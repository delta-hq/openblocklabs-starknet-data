import json
import requests
import re
import math
import pandas as pd

contracts = [
    "0x49d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7",  # ETH
    "0xda114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3",  # DAI
    "0x3fe2b97c1fd336e750087d68b9b867997fd64a2661ff3ca5a7c771641e8e7ac",  # wBTC
    "0x68f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8",  # USDT
    "0x42b8f0484674ca266ac5d08e4ac6a3fe65bd3129795def2dca5c34ecc5f96d2",  # wstETH
    "0x124aeb495b947201f5fac96fd1138e326ad86195b98df6dec9009158a533b49",  # LORDS
    "0x319111a5037cbec2b3e638cc34a3474e2d2608299f3e62866e9cc683208c610",  # rETH
    "0x70a76fd48ca0ef910631754d77dd822147fe98a569b826ec85e3c33fde586ac",  # LUSD
]

starknet_api_key = "Vywi-dTCuV0MyoorAtAZF8xGbC0LNSCP"

url = f"https://starknet-mainnet.g.alchemy.com/v2/{starknet_api_key}"
headers = {
    "accept": "application/json",
    "content-type": "application/json",
}

depth_list = [0.02, 0.05, 0.1, 0.2]

ekubo_api_url = "https://mainnet-api.ekubo.org/pools"
ekubo_response = requests.get(ekubo_api_url)
df = pd.DataFrame(ekubo_response.json())

all_depths = []
for index, row in df.iterrows():
    print("\n")
    # Access individual columns using column names
    token0 = row["token0"]
    token1 = row["token1"]
    fee = row["fee"]
    tick_spacing = hex(row["tick_spacing"])
    extension = row["extension"]
    print(
        f"token0: {token0},token1: {token1},fee: {fee},tick_spacing: {tick_spacing},extension: {extension}"
    )

    for i in depth_list:
        sqrt_perc = math.floor((math.sqrt(1 + i) - 1) * 2**128)
        hex_sqrt_perc = hex(sqrt_perc)

        data = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "starknet_call",
            "params": [
                {
                    "contract_address": "0x0048de1849643ee73f24c61e39312d24f98bd3bef7b112b63b861d423a6f1dce",
                    "calldata": [
                        token0,
                        token1,
                        fee,
                        tick_spacing,
                        extension,
                        hex_sqrt_perc,
                    ],
                    "entry_point_selector": "0x03a0f2479a5d4bd47d577a0afc13c861825a103113a848ec6a7aa08837bcc070",
                },
                {
                    "block_number": 522965
                },  # we can use this if we need to go by specific blocks
                # "latest",
            ],
        }

        # getting error message here is normal, need to get the amount for token0 and token1 in the error
        try:
            response = requests.post(url, headers=headers, json=data)
            error_message = response.json()["error"]["data"]
            revert_error = error_message.get("revert_error", "")

            matches = re.search(

                ########################
                #### FIX REGEX HERE ####
                ########################

                r"3f532df6e73f94d604f4eb8c661635595c91adc1d387931451eacd418cfbd14,\s*(0x[a-fA-F0-9]*)\s*(?:\('.*'\))?,\s*(0x[a-fA-F0-9]*)",

                ########################
                ########################
                ########################

                revert_error,
            )
            
            if matches and matches is not None:
                token0_liquidity = matches.group(1)
                token1_liquidity = matches.group(2)
            else:
                token0_liquidity = "0x0"
                token1_liquidity = "0x0"

            amount_of_token0 = int(token0_liquidity, 16)
            amount_of_token1 = int(token1_liquidity, 16)

            all_depths.append(
                {
                    "depth": i,
                    "token0": token0,
                    "token1": token1,
                    "token0_amount": amount_of_token0,
                    "token1_amount": amount_of_token1,
                }
            )

            if amount_of_token0 == 0 and amount_of_token1 == 0:
                print(f"depth: {i * 100}%, error: no liquidity")
            else:
                print(
                    f"depth: {i * 100}% amount of token0: {amount_of_token0} , amount of token1: {amount_of_token1}"
                )

        except Exception as e:
            print(e)


with open("test/ekubo.json", 'w') as file:
    json.dump(all_depths, file)
