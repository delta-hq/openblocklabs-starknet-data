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

We also need a snapshot of LP token holders for Uni v2 protocols.

Ideally, this would be an on-chain contract function (preferred). The [Haiko example](#example-haiko) below shows pool-level data sufficient to determine the grant to each pool. We would like the data in this format, but broken out by user address so that it can be used to determine the user-level grant amount.

If not possible, please provide an api endpoint.
   
Our goal is an on-chain contract that implements an interface that everyone will create and open source.

### Data Requirements v3
1. Market Depth at pool and user level.

### Data Requirements v2
1. Snapshot of all LP token holders.

## How this will be used
This new API or function will be used to take periodic snapshots of all user positions within each pool, in addition to the current price. This will be used to calculate the average liquidity contributed by each user, weighted by its distance from the current market price. This metric will be used to determine the user's share of incentives.

This repo is designed to give you a way to PR a version of the `haiko.py` file for your DEX and write a test that gives a similar result.

## Example: Haiko

Haiko has written a contract function `depth` (currently on testnet) available here: [https://testnet.starkscan.co/contract/0xbaa40f0fc9b0e069639a88c8f642d6f2e85e18332060592acf600e46564204#read-write-contract](https://testnet.starkscan.co/contract/0xbaa40f0fc9b0e069639a88c8f642d6f2e85e18332060592acf600e46564204#read-write-contract)

Which returns a response we can use to get market depths for pairs. This is a first draft, but two additional pieces of information will ultimately be needed: the current price (ideally included in the response rather than in a separate call) and the corresponding addresses of each user providing liquidity.

`limits` are similar to Uniswap V3 `ticks`. Documentation explaining limits on Haiko: [https://haiko-docs.gitbook.io/docs/developers/advanced-concepts/limits](https://haiko-docs.gitbook.io/docs/developers/advanced-concepts/limits)

```json
[
    [
        {
            "name": "limit",
            "type": "core::integer::u32",
            "value": "8626740"
        },
        {
            "name": "price",
            "type": "core::integer::u256",
            "value": "13409907618269814412629275245516"
        },
        {
            "name": "liquidity_delta",
            "type": "amm::types::i128::i128",
            "value": [
                {
                    "name": "val",
                    "type": "core::integer::u128",
                    "value": "41297276145384522878738"
                },
                {
                    "name": "sign",
                    "type": "core::bool",
                    "value": "0"
                }
            ]
        }
    ],
    [
        {
            "name": "limit",
            "type": "core::integer::u32",
            "value": "8646740"
        },
        {
            "name": "price",
            "type": "core::integer::u256",
            "value": "16378881772847054732583964069663"
        },
        {
            "name": "liquidity_delta",
            "type": "amm::types::i128::i128",
            "value": [
                {
                    "name": "val",
                    "type": "core::integer::u128",
                    "value": "41297276145384522878738"
                },
                {
                    "name": "sign",
                    "type": "core::bool",
                    "value": "1"
                }
            ]
        }
    ]
```

Ultimately, we want this data separated out by user, adding an additional `lp_address` parameter with each `liquidity_delta`.

## Testing Code

Here is a script for testing the functionality of the `depth` function. This specific example is for Haiko's implementation:

```python
import asyncio
import json
from starknet_py.contract import Contract
from starknet_py.net.full_node_client import FullNodeClient

from collections import OrderedDict


def nested_odict_to_dict(nested_odict):
    result = dict(nested_odict)
    for key, value in result.items():
        if isinstance(value, OrderedDict):
            result[key] = nested_odict_to_dict(value)
    return result


async def main():

    CONTRACT_ADDRESS = (
        0x00BAA40F0FC9B0E069639A88C8F642D6F2E85E18332060592ACF600E46564204  # Haiko
    )

    ETH_USDT = (
        0x288D0ABCFA6F2D23CD10584F502B4095D14CEF132D632DA876A7089C1310072  # market_id
    )

    node_url = "<Insert Node Url>"

    contract = await Contract.from_address(
        address=CONTRACT_ADDRESS, provider=FullNodeClient(node_url=node_url)
    )

    value = await contract.functions["depth"].call(ETH_USDT)

    value_json = [nested_odict_to_dict(item) for item in value[0]]

    print(json.dumps(value_json, indent=4))


asyncio.run(main())

```