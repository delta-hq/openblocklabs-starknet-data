import asyncio
import json
from starknet_py.contract import Contract
from starknet_py.net.full_node_client import FullNodeClient
import requests
from starknet_py.hash.selector import get_selector_from_name
from starknet_py.net.client_models import Call
from typing import Optional, List, Tuple

node_url = "https://starknet-mainnet.public.blastapi.io"
ETH_USDC = "0x30615bec9c1506bfac97d9dbd3c546307987d467a7f95d5533c2e861eb81f3f"
USDC_USDT = "0x601f72228f73704e827de5bcd8dadaad52c652bb1e42bf492d90bbe22df2cec"
MULTI_CALL = "0x5754af3760f3356da99aea5c3ec39ccac7783d925a19666ebbeca58ff0087f4"


async def execute_graphql_query(pair_address, limit, offset):
    url = "https://api.sithswap.info/"

    query = f"""
    {{
        liquiditypositionsnapshots(first:  {limit},skip: {offset}, where:{{pair_in:"{pair_address}"}}) {{
            user
        }}
    }}
    """
    headers = {"Content-Type": "application/json"}
    payload = {"query": query}
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making GraphQL request:")
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


async def process_pair(pair, batch_size, total_users, multicallContract):
    all_balances_pair = {}
    for offset in range(0, total_users, batch_size):
        result_pair = await execute_graphql_query(pair, batch_size, offset)

        snapshots_pair = result_pair["data"]["liquiditypositionsnapshots"]
        unique_users_pair = list(set(snapshot["user"] for snapshot in snapshots_pair))

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
    total_users = 100000

    all_balances = {}
    pairs = [ETH_USDC, USDC_USDT]

    tasks = [
        process_pair(pair, batch_size, total_users, multicallContract) for pair in pairs
    ]
    pair_results = await asyncio.gather(*tasks)

    all_balances["ETH_USDC_BALANCE"] = pair_results[0]
    all_balances["USDC_USDT_BALANCE"] = pair_results[1]

    json_filename = "./test/sithswap_balances.json"
    # json_filename = "sithswap_balances.json"
    with open(json_filename, "w") as json_file:
        json.dump(all_balances, json_file, indent=2)

    print(f"Balances saved to {json_filename}")


if __name__ == "__main__":
    asyncio.run(main())