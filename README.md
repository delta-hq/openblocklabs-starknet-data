# Openblock Labs LP Data Request
As part of our partnership with the Starknet Foundation Grants Program, OpenBlock Labs requires participating protocols to index and graph their data.  

Much of this data is already available from different sources (on-chain, APIs), but an important data point often missing (without using roundabout methods) is the market depth for DEX analysis.

## How to run
1. Run `./setup.sh` which will setup your virtual envvironment and install dependencies.
2. `python run.py`

## What to Do
1. Create or edit the file associated with your DEX in the `src` folder. Ex: `00_haiko.py`
2. The output of that file should be a json (saved in the `test` folder) with the user-level position data.
3. Add a `test_{your_dex}.py` file in the `test` folder. This is the file Your result will be tested against.
4. Add your test to the `99_tests.py` file in the `src` folder.
5. When ready, run `python run.py` which will run all the files in `src` including the tests file.

## The Request
We are requesting that participating DEXs provide a consistent solution for getting market depth data down to the pool and user level. With user-level liquidity data, Openblock Labs will be able to calculate each user's airdrop amount for each grant period, with no additional input needed from the protocol teams. This will ultimately reduce the total effort and coordination required to administer the grant program.

## Data Ingestion Process 
Over the course of the grant period, we will be collecting the necessary data at a random time each hour. (Random to prevent anyone from strategically timing and manipulating the results). This data will be used to determine the pool and user-level incentives for the period.

In order to streamline this process, we have created a GitHub repo that we would like all protocol teams to add a working solution. The GitHub repo is available here. This will allow all teams to see how we will be getting the required data.

### Required Data

| Category   | Data Requirement                                                                                                                                                                     | Method                    |
|------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------|
| All Teams  | - Volume, TVL, and Fees                                                                                                                                                              | - Flipside dashboard or API Endpoint |
| Uni v2 based | - All events that change LP token balances (mints, withdrawals, transfers) <br> - A script that can generate all LP token balances at any given block from events                           | - Contract Call or API endpoint <br> - Python script |
| Uni v3+ based | - All events that change a user's liquidity position (minting, depositing, withdrawing, transferring) <br> - Price ratio each block (or events to construct it) <br> - A script that can construct all LP positions at any given block from events | - Contract Call or API endpoint <br> - Python script |
| Lending Protocols | - Users <br> - Amount of tokens supplied <br> - Amount of tokens borrowed | - Contract Call or API endpoint <br> - Python script |

### Examples

#### LP Token Balances

This example gets the LP token balances for 10kswap.

```python
import asyncio
import json
from starknet_py.contract import Contract
from starknet_py.net.full_node_client import FullNodeClient
import requests
from starknet_py.hash.selector import get_selector_from_name
from starknet_py.net.client_models import Call
from typing import Optional, List, Tuple

node_url = "https://starknet-mainnet.public.blastapi.io"
ETH_USDC = "0x23c72abdf49dffc85ae3ede714f2168ad384cc67d08524732acea90df325"
USDC_USDT = "0x41a708cf109737a50baa6cbeb9adf0bf8d97112dc6cc80c7a458cbad35328b0"
MULTI_CALL = "0x5754af3760f3356da99aea5c3ec39ccac7783d925a19666ebbeca58ff0087f4"

async def execute_total_user_query(pair_address):
    url = "https://api.10kswap.com/transaction/addresses/"

    params = {
        "key_name": "Mint",
        "page": 1,
        "limit": 1,
        "pair_address": pair_address
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making address request:")
        return None

async def execute_addresses_query(pair_address, limit, offset):
    url = "https://api.10kswap.com/transaction/addresses/"

    params = {
        "key_name": "Mint",
        "page": offset+1 if offset==0 else int((offset / 1000) + 1),
        "limit": limit,
        "pair_address": pair_address
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making address request:")
        return None


def from_call_to_call_array(calls: List[Call]):
    call_array = []
    calldata = []
    for call in calls:
        assert len(call) == 3, "Invalid call parameters"
        entry = {
            "to": call[0],
            "selector": get_selector_from_name(call[1]),
            "data_offset": len(calldata),
            "data_len": len(call[2]),
        }
        call_array.append(entry)
        calldata.extend(call[2])
    return call_array, calldata


async def fetch_balances(
    users: List[int], contract: Contract, pair
) -> List[Tuple[int, int]]:
    # Call the 'balanceOf' function for multiple users using StarkNet multicall
    call_array, calldata = from_call_to_call_array(
        [(pair, "balanceOf", [int(user, 16)]) for user in users]
    )

    while True:
        try:
            response = await contract.functions["aggregate"].call(call_array, calldata)

            index = 0
            balances = []
            # Iterate over users
            for user in users:
                # Get balance at the current index (odd index)
                balance = response.retdata[index + 1]
                # Append user and balance to the result
                balances.append((user, balance))
                # Move to the next user's data (each user's data has size 2)
                index += 3
            return balances
        except Exception as e:
            print(f"Error fetching balances:")
            await asyncio.sleep(20)


async def process_pair(pair, batch_size, multicallContract):
    all_balances_pair = {}
    result_total_users = await execute_total_user_query(pair)
    print(result_total_users["data"]["total"])
    total_users = result_total_users["data"]["total"]

    for offset in range(0, total_users, batch_size):
        result_pair = await execute_addresses_query(pair, batch_size, offset)

        snapshots_pair = result_pair["data"]["addresses"]
        unique_users_pair = list(set(snapshot for snapshot in snapshots_pair))

        if len(unique_users_pair) == 0:
            break  # Exit the loop if there are no unique users

        balances_pair = await fetch_balances(
            unique_users_pair, multicallContract, int(pair, 16)
        )

        non_zero_balances_pair = {
            user: balance for user, balance in balances_pair if balance > 0
        }
        all_balances_pair.update(non_zero_balances_pair)

    return all_balances_pair


async def main():
    client = FullNodeClient(node_url=node_url)
    multicallContract = await Contract.from_address(address=MULTI_CALL, provider=client)

    # Set the batch size and total number of users
    batch_size = 1000

    all_balances = {}
    pairs = [ETH_USDC, USDC_USDT]

    tasks = [
        process_pair(pair, batch_size, multicallContract) for pair in pairs
    ]
    pair_results = await asyncio.gather(*tasks)

    all_balances["ETH_USDC_BALANCE"] = pair_results[0]
    all_balances["USDC_USDT_BALANCE"] = pair_results[1]

    json_filename = "./test/10kswap_balances.json"
    # json_filename = "10kswap_balances.json"
    with open(json_filename, "w") as json_file:
        json.dump(all_balances, json_file, indent=2)

    print(f"Balances saved to {json_filename}")


if __name__ == "__main__":
    asyncio.run(main())
```