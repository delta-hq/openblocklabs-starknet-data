import asyncio
import json
from aiohttp import ClientSession, TCPConnector
from starknet_py.contract import Contract
from starknet_py.net.full_node_client import FullNodeClient

from collections import OrderedDict


async def fetch_json(url: str, limit=10, limit_per_host=100):
    connector = TCPConnector(limit=limit, limit_per_host=limit_per_host, ssl=False)
    async with ClientSession(connector=connector, raise_for_status=True) as client:
        async with client.get(url) as response:
            data = await response.json()
    await client.close()
    return data


def nested_odict_to_dict(nested_odict):
    result = dict(nested_odict)
    for key, value in result.items():
        if isinstance(value, OrderedDict):
            result[key] = nested_odict_to_dict(value)
    return result


async def get_markets():
    url = "https://app.haiko.xyz/api/v1/markets?network=goerli"
    result = await fetch_json(url)

    return [
        {
            "market_id": item["marketId"],
            "token0": item["baseToken"]["address"],
            "token0_symbol": item["baseToken"]["symbol"],
            "token1": item["quoteToken"]["address"],
            "token1_symbol": item["quoteToken"]["symbol"],
            "width": item["width"],
            "strategy": item["strategy"]["address"],
            "swap_fee_rate": item["swapFeeRate"],
            "fee_controller": item["feeController"],
            "controller": item["controller"],
        }
        for item in result
    ]


async def main():

    CONTRACT_ADDRESS = (
        0x00BAA40F0FC9B0E069639A88C8F642D6F2E85E18332060592ACF600E46564204
    )

    ETH_USDT = 0x288d0abcfa6f2d23cd10584f502b4095d14cef132d632da876a7089c1310072

    node_url = (
        "https://starknet-testnet.blastapi.io/ca430011-493f-43f7-840f-4342481243fc"
    )

    contract = await Contract.from_address(
        address=CONTRACT_ADDRESS, provider=FullNodeClient(node_url=node_url)
    )

    results = await asyncio.gather(
        *[
            asyncio.create_task(contract.functions["depth"].call(ETH_USDT)),
            asyncio.create_task(contract.functions["curr_sqrt_price"].call(ETH_USDT)),
        ]
    )

    depth = [nested_odict_to_dict(item) for item in results[0][0]]

    with open("test/haiko.json", 'w') as file:
        json.dump(depth, file)


asyncio.run(main())
