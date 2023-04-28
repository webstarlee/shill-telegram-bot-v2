import random
import string
import time
import maya
import datetime
from web3 import Web3
from models import Ban, Warn, Project

def start_text():
    text = " ShillMasterBot Commands: \n\n"
    text += "<em>/shillcontract_address</em> : Add a project recommendation by providing its contract address; the bot tracks the project's performance since your suggestion.\n\n"
    text += "<em>/shillmaster@Username</em> : View the recommendation history and performance metrics of a specific user.\n\n"
    text += "<em>/remove_warning@Username</em> : Revoke a user's rug-shilling warning; two warnings result in an automatic group ban.\n\n"
    text += "<em>/unban@Username</em> : Unban the user who shilled two rugs.\n\n"
    text += "<em>/advertise</em> : Book advertising for your project to be displayed under the leaderboards."

    return text

def get_time_delta(time_one, time_two):
    cal_time_one = datetime.datetime.utcnow()
    cal_time_two = datetime.datetime.utcnow()
    if isinstance(time_one, datetime.date):
        cal_time_one = time_one
    else:
        cal_time_one_datetime = maya.parse(time_one).datetime()
        cal_time_one_date = cal_time_one_datetime.date()
        cal_time_one_time = cal_time_one_datetime.time()
        cal_time_one_time = str(cal_time_one_time).split('.')[0]
        cal_time_one_str = str(cal_time_one_date)+" "+str(cal_time_one_time)
        cal_time_one = datetime.datetime.strptime(cal_time_one_str, '%Y-%m-%d %H:%M:%S')
    
    if isinstance(time_two, datetime.date):
        cal_time_two = time_two
    else:
        cal_time_two_datetime = maya.parse(time_two).datetime()
        cal_time_two_date = cal_time_two_datetime.date()
        cal_time_two_time = cal_time_two_datetime.time()
        cal_time_two_time = str(cal_time_two_time).split('.')[0]
        cal_time_two_str = str(cal_time_two_date)+" "+str(cal_time_two_time)
        cal_time_two = datetime.datetime.strptime(cal_time_two_str, '%Y-%m-%d %H:%M:%S')

    delta = cal_time_two-cal_time_one
    delta_min = delta.seconds/60
    return delta_min

def make_pair_array(pairs):
    eth_pairs_array = []
    bsc_pairs_array = []
    for pair in pairs:
        if pair['chain_id'] == "ethereum":
            exist = [eth_pair for eth_pair in eth_pairs_array if eth_pair['token'].lower() == pair['token'].lower()]
            if len(exist) == 0:
                eth_pairs_array.append(pair)
        elif pair['chain_id'] == "bsc":
            exist = [bsc_pair for bsc_pair in bsc_pairs_array if bsc_pair['token'].lower() == pair['token'].lower()]
            if len(exist) == 0:
                bsc_pairs_array.append(pair)
    
    eth_pairs_chunks = []
    eth_pair_addresses = []
    eth_count = len(eth_pairs_array)
    for index, eth_pair in enumerate(eth_pairs_array):
        _index = index+1
        if _index%30 == 0:
            eth_pairs_chunks.append(eth_pair_addresses)
            eth_pair_addresses = []
        elif _index == eth_count:
            eth_pairs_chunks.append(eth_pair_addresses)
        else:
            eth_pair_addresses.append(eth_pair['pair_address'])
    
    bsc_pairs_chunks = []
    bsc_pair_addresses = []
    bsc_count = len(bsc_pairs_array)
    for index, bsc_pair in enumerate(bsc_pairs_array):
        _index = index+1
        if _index%30 == 0:
            bsc_pairs_chunks.append(bsc_pair_addresses)
            bsc_pair_addresses = []
        elif _index == bsc_count:
            bsc_pairs_chunks.append(bsc_pair_addresses)
        else:
            bsc_pair_addresses.append(bsc_pair['pair_address'])

    return {"eth": eth_pairs_chunks, "bsc": bsc_pairs_chunks}

def make_coins_ids(pairs):
    coin_ids = []
    for pair in pairs:
        if pair['coin_market_id'] != "" and not pair['coin_market_id'] in coin_ids:
            if isinstance(pair['coin_market_id'], int):
                coin_ids.append(pair['coin_market_id'])
    ids_count = len(coin_ids)
    chunk = []
    chunk_array = []
    for index, id in enumerate(coin_ids):
        _index = index+1
        if _index%5 == 0:
            chunk_array.append(chunk)
            chunk = []
        elif _index == ids_count:
            chunk_array.append(chunk)
        else:
            chunk.append(id)
    return chunk_array

def get_params(origin_text, command):
    param = origin_text.replace(command, "")
    param = param.replace("@", "")
    param = param.strip()
    return param

def get_percent(first, second):
    first = float(first)
    second = float(second)
    percent = first/second
    return round(percent, 2)

def format_number_string(number):
    number = float(number)
    final_number = "{:,}".format(int(number))
    return str(final_number)

def convert_am_str(item):
    item = int(item)
    status = "AM"
    if item == 12:
        status = "PM"
    elif item > 12:
        status = "PM"
    return str(status)

def convert_am_time(item):
    item = int(item)
    time_numner = item
    if item == 0:
        time_numner = 12
    elif item == 24:
        time_numner = 12
    elif item > 12:
        time_numner = item-12
    return str(time_numner)

def get_baned_user(username):
    return Ban.find_one({'username': username})

def add_ban_user(user):
    ban_user = Ban.find_one({"username": user['username']})
    if ban_user == None:
        ban_user = {
            "username": user['username'],
            "user_id": user['user_id'],
            "chat_id": user['chat_id'],
        }
        Ban.insert_one(ban_user)

def remove_ban_user(user):
    Ban.find_one_and_delete({'username': user['username']})

def add_warn(username, user_id, chat_id):
    warn_user = Warn.find_one({"username": username})
    if warn_user != None:
        current_count = warn_user['count']
        current_count = int(current_count)+1
        Warn.update_one({"_id": warn_user['_id']}, {"$set": {"count": current_count}})
    else:
        warn_user =  {
            "username": username,
            "user_id":user_id,
            "chat_id": chat_id,
            "count": 1
        }
        Warn.insert_one(warn_user)
    
    return Warn.find_one({"username": username})

def remove_warn(username):
    warn_user = Warn.find_one({'username': username})
    text = ""
    if warn_user != None:
        Warn.find_one_and_delete({"_id": warn_user['_id']})
        text = "Warning removed from @"+username+" ✅"
    else:
        text = "Warning removed from @"+username+" ✅"
    
    return text

def to_check_some(token):
    token_checksum_address = Web3.to_checksum_address(token)

    return token_checksum_address

def user_rug_check(project, reason):
    pair_project = Project.find_one({"_id": project['_id']})
    is_warn = False
    if pair_project != None:
        print("project rug check for: ", pair_project["created_at"])
        Project.update_one({"_id": project['_id']}, {"$set":{"status": reason}})
        current_time = datetime.utcnow()
        delta = get_time_delta(current_time, pair_project['created_at'])
        if delta <= 30:
            is_warn = True
    
    return is_warn

def get_user_warn(username):
    return Warn.find_one({"username": username})

def invoice_hash():
    chars = string.ascii_uppercase+string.digits
    stamp = time.time()
    hash = ''.join(random.choice(chars) for _ in range(16))
    result = str(hash)+str(stamp)
    return result

def convert_am_pm(item):
    item = int(item)
    time_numner = item
    status = "AM"
    if item == 0:
        time_numner = 12
    elif item == 12:
        status = "PM"
    elif item == 24:
        time_numner = 12
    elif item > 12:
        time_numner = item-12
        status = "PM"
    result_time = str(time_numner)+str(status)
    return result_time
