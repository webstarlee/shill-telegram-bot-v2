import json
import aiohttp
from models.tokenPair import TokenPair
from web3 import Web3
from config import chains, ROOT_PATH, rpc_urls, contract_abi, honeypot_abi, honey_check_contracts, eth_routers

headers = {
        'Accepts': 'application/json',
        'Accept-Encoding': 'deflate, gzip',
        'X-CMC_PRO_API_KEY': "8d44a2eb-52eb-4718-8bed-5b21a1eb5747"
    }

async def get_pairs_by_pair_address(chain, addresses):
    try:
        stringed_addresses = ','.join([str(elem) for elem in addresses])
        dex_url = "https://api.dexscreener.com/latest/dex/pairs/"+chain+"/"+stringed_addresses
        async with aiohttp.ClientSession() as session:
            async with session.get(dex_url) as response:
                result = await response.text()
                result_array = json.loads(result)

                return [TokenPair.parse_obj(pair) for pair in result_array["pairs"]]
    except:
        return []

async def cryptocurrency_info_ids(ids):
    try:
        ids = ','.join([str(elem) for elem in ids])
        coinmarketcap_url = "https://pro-api.coinmarketcap.com/v2/cryptocurrency/info?id="+ids
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(coinmarketcap_url) as response:
                result = await response.text()
                result_array = json.loads(result)
                return result_array['data']
    except:
        return None
    
async def get_token_pairs(token):
    try:
        dex_url = "https://api.dexscreener.io/latest/dex/tokens/"+token
        async with aiohttp.ClientSession() as session:
            async with session.get(dex_url) as response:
                result = await response.text()
                result_array = json.loads(result)

                return [TokenPair.parse_obj(pair) for pair in result_array["pairs"]]
    except:
        return []

async def cryptocurrency_info(token):
    try:
        coinmarketcap_url = "https://pro-api.coinmarketcap.com/v2/cryptocurrency/info?address="+token
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(coinmarketcap_url) as response:
                result = await response.text()
                result_array = json.loads(result)
                return result_array['data']
    except:
        return None

async def hoeny_check_api(token, pair):
    print("honey check start")
    target_token_address = Web3.to_checksum_address(token)
    from_address = Web3.to_checksum_address("0xE556B7494C8809d66494CD23C48bff02e4391dCB")
    router_address = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
    if pair.labels != None and ("v3" in pair.labels or "V3" in pair.labels):
        print("V3")
        return {"is_honeypot": False, "reason": "v3"}
    
    if pair.chain_id == "bsc":
        print("router: ", pair.dex_id)
        router_address = "0x10ED43C718714eb63d5aA57B78B54704E256024E"
    else:
        print("router: ", pair.dex_id)
        router_address = eth_routers[pair.dex_id]

    final_router = Web3.to_checksum_address(router_address)
    honey_contract_address = Web3.to_checksum_address(honey_check_contracts[pair.chain_id])
    rpc_url = rpc_urls[pair.chain_id]
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    contract = web3.eth.contract(address=honey_contract_address, abi=honeypot_abi)
    buy_path = []
    if pair.chain_id == "bsc":
        if pair.quote_token.symbol == "WBNB":
            buy_path.append(Web3.to_checksum_address(pair.quote_token.address))
            buy_path.append(target_token_address)
        else:
            buy_path.append(Web3.to_checksum_address("0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"))
            buy_path.append(Web3.to_checksum_address(pair.quote_token.address))
            buy_path.append(target_token_address)
    else:
        if pair.quote_token.symbol == "WETH":
            buy_path.append(Web3.to_checksum_address(pair.quote_token.address))
            buy_path.append(target_token_address)
        else:
            buy_path.append(Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"))
            buy_path.append(Web3.to_checksum_address(pair.quote_token.address))
            buy_path.append(target_token_address)
    
    sell_path = list(reversed(buy_path))
    print("buy path: ", buy_path)
    print("sell path: ", sell_path)
    try:
        response = contract.functions.honeyCheck(target_token_address, buy_path, sell_path, final_router).call({'from': from_address, 'value': 10000000000000000})
        print(response)
        return {"is_honeypot": False, "reason": "pass"}
    except:
        print("Honeypot !!!!")
        return {"is_honeypot": True, "reason": "fail"}