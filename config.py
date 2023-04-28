from pymongo import MongoClient
import os
from pathlib import Path

ROOT_PATH = Path(os.path.dirname(__file__))

mongo_url = "mongodb://mongo:0vAcYlPN44ugKCNqFXNc@containers-us-west-203.railway.app:6725"
mongo_client = MongoClient(mongo_url)
mongo_db = mongo_client['shillmaster_v2']

BOT_TOKEN="5980518310:AAH59J2CU_roxuHRfArHzq3HTuB_Dlymp-4"
LEADERBOARD_ID = "-1001894150735"

wallet="0x2089b6C05D70EAB5c73721377e3Ad8993e05Ed5A"
# crypto chains
chains = {"ethereum": 1, "bsc": 56}
rpc_urls = {
    "ethereum": "https://mainnet.infura.io/v3/ea784836f0d34fd08a7484151071686d",
    "bsc": "https://polished-blissful-friday.bsc.discover.quiknode.pro/0d08b1a25f11c4e0ea1ecce9bd4fc5cf5a4caa43"
}
contract_abi_path = os.path.join(ROOT_PATH, "abis/erc20_abi.json")
with open(contract_abi_path) as contract_abi_file:
    contract_abi = contract_abi_file.read()

hoenypot_abi_path = os.path.join(ROOT_PATH, "abis/honeypot_abi.json")
with open(hoenypot_abi_path) as honeypot_abi_file:
    honeypot_abi = honeypot_abi_file.read()

honey_check_contracts = {
    "ethereum": "0xbF7B21D5529b4B019f1f7Ce5465Ff147463d604D",
    "bsc": "0x2d36BB090231DD6F327D6B4a7c08E5bED0030B3e"
}

eth_routers={
    "uniswap": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
    "shibaswap": "0x03f7724180AA6b939894B5Ca4314783B0b36b329",
    "sushiswap": "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F",
    "pancakeswap": "0xEfF92A263d31888d860bD50809A8D171709b7b1c"
}