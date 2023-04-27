import json
import aiohttp
from models.tokenPair import TokenPair

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