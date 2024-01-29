# Openblock Labs Market Depth Request
As part of our partnership with the Starknet Foundation Grants Program, OpenBlock Labs requires participating protocols to index and graph their data.  

Much of this data is already available from different sources (on-chain, APIs), but an important data point often missing (without using roundabout methods) is the market depth for DEX analysis.

## The Request
We are requesting that participating DEXs provide a consistent solution for getting market depth data for pools. 

Ideally, this would be an on-chain contract function (preferred) or API that takes the inputs of `token0`, `token1`, `block number` or the `latest` block, and the `depth_percent` (i.e. .5%, 2%, 10%, etc) and would return the market depth for the desired pool. Instead of `token0` and `token1`, an `market_id` would work as well.

Our goal is an on-chain contract that implements an interface that everyone will create and open source.

## How this will be used
This new API or function will be used to get block-by-block market depths for all pairs within each pool, helping reduce diffrences of how this is calculated and reduce the number of necessary RPC calls used in roundabout methods. 