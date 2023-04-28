import json
import logging
from datetime import datetime, timedelta
from models import Pair, Project, Warn, Setting, Leaderboard
from apis import cryptocurrency_info

def database_to_json():
    projects_cursor = Project.find()
    projects = list(projects_cursor)
    with open("projects.json", "a") as outfile:
            outfile.write("[")
    for project in projects:
        single_project={
            "username": project['username'],
            "user_id": project['user_id'],
            "chat_id": project['chat_id'],
            "chain_id": project['chain_id'],
            "pair_address": project['pair_address'],
            "url": project['url'],
            "token": project['token'],
            "token_symbol": project['token_symbol'],
            "marketcap": project['marketcap'],
            "ath_value": project['ath_value'],
            "status": project['status'],
            "created_at": str(project['created_at']),
        }
        json_object = json.dumps(single_project, indent=4)
        with open("projects.json", "a") as outfile:
            outfile.write(json_object+",")
    
    with open("projects.json", "a") as outfile:
            outfile.write("]")


def json_to_database():
    f = open('projects.json')
    data = json.load(f)
    for i in data:
        created_at = i['created_at'].split(".")[0]
        create_at_time = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
        project_data = {
            "username": i['username'],
            "user_id": i['user_id'],
            "chat_id": i['chat_id'],
            "chain_id": i['chain_id'],
            "pair_address": i['pair_address'],
            "url": i['url'],
            "token": i['token'],
            "token_symbol": i['token_symbol'],
            "marketcap": i['marketcap'],
            "ath_value": i['ath_value'],
            "status": i['status'],
            "created_at": create_at_time,
        }
        Project.insert_one(project_data)

    f.close()

def project_to_pair():
    project_cursor = Project.find()
    projects = list(project_cursor)

    unique_pair_list = []
    for project in projects:
        exist = [unique_pair for unique_pair in unique_pair_list if unique_pair['pair_address'] == project['pair_address']]
        if len(exist)==0:
            unique_pair_list.append(project)
    
    for unique_pair in unique_pair_list:
        logging.info(f"insert db: {unique_pair['token']}")
        single_pair={
            "token": unique_pair['token'],
            "symbol": unique_pair['token_symbol'],
            "chain_id": unique_pair['chain_id'],
            "pair_address": unique_pair['pair_address'],
            "url": unique_pair['url'],
            "marketcap": unique_pair['marketcap'],
            "coin_market_id": "",
            "circulating_supply": "",
            "updated_at": datetime.utcnow()
        }
        Pair.insert_one(single_pair)

async def get_coin_id():
    pair_cursor = Pair.find()
    pairs = list(pair_cursor)
    for pair in pairs:
        coin_info = await cryptocurrency_info(pair['token'])
        coin_marketcap_id = ""
        circulating_supply = ""
        if coin_info != None:
            for key in coin_info:
                currency_info = coin_info[key]
                coin_marketcap_id=currency_info['id']
                if currency_info['self_reported_circulating_supply'] != None:
                    circulating_supply = currency_info['self_reported_circulating_supply']
        if coin_marketcap_id != "":
            logging.info(f"Update pair for : {pair['_id']}")
            Pair.find_one_and_update({"_id": pair['_id']}, {"$set": {"coin_market_id": coin_marketcap_id, "circulating_supply": circulating_supply}})

def pair_update_status():
    pair_cursor = Pair.find()
    pairs = list(pair_cursor)
    for pair in pairs:
        logging.info(f"Update pair for : {pair['_id']}")
        Pair.find_one_and_update({"_id": pair['_id']}, {"$set": {"status": "active"}})
    
    logging.info("Done")