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
