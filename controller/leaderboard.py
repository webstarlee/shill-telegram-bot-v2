import logging
import numpy as np
import threading
from datetime import datetime, timedelta
from models import Pair, Project, Warn, Setting, Leaderboard
from config import LEADERBOARD_ID
from helpers import make_pair_array, make_coins_ids, get_time_delta, get_percent, format_number_string, convert_am_time, convert_am_str
from apis import get_pairs_by_pair_address, cryptocurrency_info_ids

def pair_marketcap_update(pair, marketcap):
    Pair.find_one_and_update({"_id": pair['_id']}, {"$set": {"marketcap": marketcap, "updated_at": datetime.utcnow()}})
    Project.update_many({"pair_address": pair['pair_address']}, {"$set": {"ath_value": marketcap}})

def update_pair_db_removed():
    Pair.update_many({"status": "removed"}, {"$set": {"broadcast": False}})

def top_ten_update(all_results, two_results, one_results):
    user_name_array = []
    for all_result in all_results:
        if not all_result['username'] in user_name_array:
                user_name_array.append(all_result['username'])
    
    for two_result in two_results:
        if not two_result['username'] in user_name_array:
                user_name_array.append(two_result['username'])
    
    for one_result in one_results:
        if not one_result['username'] in user_name_array:
                user_name_array.append(one_result['username'])
    
    setting = Setting.find_one({"master": "master"})
    if setting != None:
        Setting.find_one_and_update({"_id": setting['_id']}, {"$set": {"top_ten_users": user_name_array}})
    else:
        setting = {
            "master": "master",
            "top_ten_users": user_name_array
        }
        Setting.insert_one(setting)

def user_rug_check(pair):
    logging.info("Rug check function working")
    projects = Project.find({"pair_address": pair['pair_address']})
    if projects != None:
        for project in projects:
            logging.info(f"Project status to remove for {project['_id']}")
            Project.find_one_and_update({"_id": project['_id']}, {"$set": {"status": "removed"}})
            current_time = datetime.utcnow()
            delta = get_time_delta(current_time, project['created_at'])
            if delta <= 30:
                warn_user = Warn.find_one({"username": project['username']})
                if warn_user != None:
                    current_count = warn_user['count']
                    current_count = int(current_count)+1
                    Warn.update_one({"_id": warn_user['_id']}, {"$set": {"count": current_count}})
                else:
                    warn_user =  {
                        "username": project['username'],
                        "user_id":project['user_id'],
                        "chat_id": project['chat_id'],
                        "count": 1
                    }
                    Warn.insert_one(warn_user)
                    logging.info(f"Insert warnning for {project['username']}")

    Pair.find_one_and_update({"_id": pair['_id']}, {"$set" : {"status": "removed", "removed_at": datetime.utcnow(), "broadcast": True}})

def leaderboard_db_update(leaderboard, text):
    Leaderboard.find_one_and_update({"_id": leaderboard['_id']}, {"$set": {"text": text}})

def update_leaderboard_message_id(id, message_id):
    print(f"message_id: {message_id}")
    print(f"ID: {id}")
    Leaderboard.find_one_and_update({"_id": id}, {"$set": {"message_id": message_id}})

async def token_update():
    pairs_cursor = Pair.find({"status": "active"})
    pairs = list(pairs_cursor)

    pairs_chunks = make_pair_array(pairs)
    pair_mcoin_ids = make_coins_ids(pairs)

    eth_pairs_chunks = pairs_chunks['eth']
    bsc_pairs_chunks = pairs_chunks['bsc']
    
    marketcap_results = []
    for mcoin_ids in pair_mcoin_ids:
        cap_result = await cryptocurrency_info_ids(mcoin_ids)
        if cap_result != None:
            for single_key in cap_result:
                marketcap_results.append(cap_result[single_key])
    
    all_pair_results = []
    for eth_pair_chunk in eth_pairs_chunks:
        results = await get_pairs_by_pair_address("ethereum", eth_pair_chunk)
        for single_result in results:
            all_pair_results.append(single_result)
    
    for bsc_pair_chunk in bsc_pairs_chunks:
        results = await get_pairs_by_pair_address("bsc", bsc_pair_chunk)
        for single_result in results:
            all_pair_results.append(single_result)

    for pair in pairs:
        liquidities = [single_result for single_result in all_pair_results if single_result.pair_address.lower() == pair['pair_address'].lower()]
        market_info = [single_cap for single_cap in marketcap_results if single_cap['id'] == pair['coin_market_id']]
        exist_pair = None
        if len(liquidities)>0:
            exist_pair = liquidities[0]
        else:
            check_again = await get_pairs_by_pair_address(pair['chain_id'], [pair['pair_address']])
            if len(check_again)>0:
                exist_pair = check_again[0]
        
        if exist_pair != None and exist_pair.liquidity.usd>100:
            now_marketcap = exist_pair.fdv
            circulating_supply = None
            if len(market_info)>0:
                circulating_supply = market_info[0]['self_reported_circulating_supply']
            
            if circulating_supply != None:
                now_marketcap = circulating_supply*exist_pair.price_usd
            
            logging.info(f"updated token marketcap: {pair['token']} => {now_marketcap}")
            db_insert = threading.Thread(target=pair_marketcap_update, args=(pair, now_marketcap,))
            db_insert.start()
        else:
            rug_check = threading.Thread(target=user_rug_check, args=(pair,))
            rug_check.start()

    logging.info("Completed")
    return True

def get_broadcasts():
    projects_cursor = Project.find({"status": "active"}).sort("created_at", -1)
    projects = list(projects_cursor)

    two_week_projects = []
    one_week_projects = []
    current_time = datetime.utcnow()
    for project in projects:
        delta = get_time_delta(current_time, project['created_at'])
        if delta <= 20160:
            two_week_projects.append(project)
            if delta <= 10080:
                one_week_projects.append(project)
            
    all_results = calculate_order(projects)
    two_results = calculate_order(two_week_projects)
    one_results = calculate_order(one_week_projects)

    db_insert = threading.Thread(target=top_ten_update, args=(all_results, two_results, one_results,))
    db_insert.start()

    now_text = f"<code>UTC:{datetime.utcnow().strftime('%d/%m/%y')} {convert_am_time(datetime.utcnow().strftime('%H'))}:{datetime.utcnow().strftime('%M')} {convert_am_str(datetime.utcnow().strftime('%H'))}</code>"
    all_text = f"TOP 10 SHILLERS OF ALL TIME\n\n{broadcast_text(all_results)}{now_text}"
    two_text = f"TOP 10 SHILLERS PAST 2 WEEKS\n\n{broadcast_text(two_results)}{now_text}"
    one_text = f"TOP 10 SHILLERS PAST WEEK\n\n{broadcast_text(one_results)}{now_text}"

    search_data = [
        {"type": "all", "text": all_text},
        {"type": "two", "text": two_text},
        {"type": "one", "text": one_text},
    ]
    broadcast_data = []
    for single_leader_data in search_data:
        leaderboard = Leaderboard.find_one({"type": single_leader_data['type']})
        if leaderboard != None:
            leaderboard_item = {
                "_id": leaderboard['_id'],
                "type": single_leader_data['type'],
                "chat_id": LEADERBOARD_ID,
                "message_id": leaderboard['message_id'],
                "text": single_leader_data['text']
            }
            broadcast_data.append(leaderboard_item)
            leaderboard_update = threading.Thread(target=leaderboard_db_update, args=(leaderboard, single_leader_data['text'],))
            leaderboard_update.start()
        else:
            leaderboard = {
                "type": single_leader_data['type'],
                "chat_id": LEADERBOARD_ID,
                "message_id": "",
                "text": single_leader_data['text']
            }
            Leaderboard.insert_one(leaderboard)
            broadcast_data.append(leaderboard)

    return broadcast_data

def calculate_order(projects):
    user_lists = []
    for project in projects:
        exist_list = [user_list for user_list in user_lists if user_list['username'] == project['username']]
        if len(exist_list)>0:
            count = int(exist_list[0]['count'])+1
            total_percent = float(exist_list[0]['total_percent'])+get_percent(project['ath_value'], project['marketcap'])
            origin_percent = float(exist_list[0]['project']['ath_value'])/float(exist_list[0]['project']['marketcap'])
            new_percent = float(project['ath_value'])/float(project['marketcap'])
            if new_percent > origin_percent:
                exist_list[0]['project'] = project
            exist_list[0]['count'] = count
            exist_list[0]['total_percent'] = total_percent
            exist_list[0]['average_percent'] = total_percent/count
        else:
            new_list = {
                "username": project['username'],
                "project": project,
                "count": 1,
                "total_percent": get_percent(project['ath_value'], project['marketcap']),
                "average_percent": get_percent(project['ath_value'], project['marketcap'])
            }
            user_lists.append(new_list)

    results = sorted(user_lists, key=lambda d: d['average_percent'], reverse=True)

    results = np.array(results)
    final_result = results[0:10]

    return final_result

def broadcast_text(results):
    result_text=""
    index = 1
    for result in results:
        current_marketcap = result['project']['marketcap']
        pair = Pair.find_one({"token": result['project']['token']})
        if pair != None:
            current_marketcap = pair['marketcap']
        result_text += f"#{str(index)}: @{result['username']} Total {str(round(result['average_percent'], 2))}x.\n"
        result_text += f"👉 <a href='{result['project']['url']}'>{result['project']['token_symbol']}</a> Shared marketcap: ${format_number_string(result['project']['marketcap'])}\n"
        result_text += f"💰 Currently: ${format_number_string(current_marketcap)} ({round(float(current_marketcap)/float(result['project']['marketcap']), 2)}x)\n"
        if float(current_marketcap)<float(result['project']['ath_value']):
            result_text += f"🏆 ATH: ${format_number_string(result['project']['ath_value'])} ({get_percent(result['project']['ath_value'], result['project']['marketcap'])}x)\n"
        result_text += "\n"
        index +=1

    return result_text

def get_removed_pairs():
    pair_cursor = Pair.find({"status": "removed", "broadcast": True})
    removed_pairs = list(pair_cursor)
    removed_pair_details = []
    if len(removed_pairs)>0:
        for removed_pair in removed_pairs:
            project_cursor = Project.find({"pair_address": removed_pair['pair_address']})
            projects = list(project_cursor)
            shilled_usernames = []
            if len(projects) > 0:
                for project in projects:
                    if not project['username'] in shilled_usernames:
                        shilled_usernames.append(project['username'])
            
            single_removed_pair = {
                "token": removed_pair['token'],
                "symbol": removed_pair['symbol'],
                "url": removed_pair['url'],
                "users": shilled_usernames
            }
            exist = [removed_pair_detail for removed_pair_detail in removed_pair_details if removed_pair_detail['token'] == single_removed_pair['token']]
            if len(exist) == 0:
                removed_pair_details.append(single_removed_pair)
    
    removed_pairs_details_text = []
    if len(removed_pair_details)> 0:
        for removed_pair_detail in removed_pair_details:
            text = f"<a href='{removed_pair_detail['url']}' >{removed_pair_detail['symbol']}</a> Liquidity removed\n"
            text += f"❌ <code>{removed_pair_detail['token']}</code>\n"
            if len(removed_pair_detail['users'])>0:
                text += "\nShilled by: "
                for black_username in removed_pair_detail['users']:
                    text += "@"+black_username+", "
            removed_pairs_details_text.append(text)
    
    pair_db_clear = threading.Thread(target=update_pair_db_removed)
    pair_db_clear.start()
    return removed_pairs_details_text

def get_leaderboard():
    leaderboard = Leaderboard.find_one({"type": "all"})
    text = ""
    if leaderboard != None:
        text = leaderboard['text']
    
    return text