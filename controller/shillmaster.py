from operator import attrgetter
from datetime import datetime
from models import Project, Pair, Leaderboard, Warn
from apis import get_token_pairs, cryptocurrency_info, hoeny_check_api
from helpers import (
    format_number_string,
    get_percent,
    user_rug_check,
    add_warn
)

async def user_shillmaster(user_id, username, chat_id, token):
    try:
        pairs = await get_token_pairs(token)
        filtered_pairs = []
        if len(pairs) > 0:
            filtered_pairs = [pair for pair in pairs if pair.base_token.address.lower() == token.lower()]

        final_filtered_pairs = []
        if len(filtered_pairs) > 0:
            for filtered_pair in filtered_pairs:
                if filtered_pair.liquidity != None:
                    final_filtered_pairs.append(filtered_pair)
                    
        pair = None
        if len(final_filtered_pairs)>0:
            pair = max(final_filtered_pairs, key=attrgetter('liquidity.usd'))

        if pair == None:
            return {"is_rug": True, "reason": "liquidity", "text": "There is no Liquidity for this Token"}
        
        if int(pair.liquidity.usd) < 100:
            text = "There is no Liquidity for "+pair.base_token.symbol+" Token"
            return {"is_rug": True, "reason": "liquidity", "text": text}

        print("Hi HI HI")
        honey_result = await hoeny_check_api(token, pair)

        print("-----------Hi HI HI---------------")
        if honey_result['is_honeypot']:
            project = {
                "username": username,
                "user_id":user_id,
                "chat_id": chat_id,
                "chain_id": pair.chain_id,
                "pair_address": pair.pair_address,
                "url":pair.url,
                "token":token,
                "token_symbol":pair.base_token.symbol,
                "marketcap":"0",
                "ath_value":"0",
                "status":"honeypot",
                "created_at": datetime.utcnow()
            }
            Project.insert_one(project)
            text = pair.base_token.symbol+" Token look like honeypot"
            return {"is_rug": True, "reason": "honeypot", "text": text}

        bot_txt = ''
        is_new = True
        marketcap_info = await cryptocurrency_info(token)
        circulating_supply = 0
        marketcap = pair.fdv
        coin_marketcap_id = None
        if marketcap_info != None:
            for key in marketcap_info:
                currency_info = marketcap_info[key]
                coin_marketcap_id=currency_info['id']
                if currency_info['self_reported_circulating_supply'] != None:
                    circulating_supply = currency_info['self_reported_circulating_supply']

        if circulating_supply != 0:
            marketcap = circulating_supply*pair.price_usd

        pair_project = Project.find_one({"username": username, "token": token})
        pair_token = Pair.find_one({"token": token})
        if pair_token != None:
            Pair.update_one({"_id": pair_token['_id']},{"$set":{"marketcap": marketcap}})
        else:
            pair_token = {
                "token":token,
                "symbol":pair.base_token.symbol,
                "chain_id": pair.chain_id,
                "pair_address": pair.pair_address,
                "url":pair.url,
                "marketcap":str(marketcap),
                "coin_market_id":coin_marketcap_id,
                "circulating_supply": "",
                "updated_at": datetime.utcnow()
            }
            Pair.insert_one(pair_token)

        if pair_project != None:
            is_new = False
            if float(marketcap)>float(pair_project['ath_value']):
                Project.update_one({"_id": pair_project['_id']},{"$set":{"ath_value": marketcap}})
            marketcap_percent = marketcap/float(pair_project['marketcap'])
            bot_txt = f"💰 <a href='{pair.url}' >{pair_project['token_symbol']}</a> Already Shared marketcap: ${format_number_string(pair_project['marketcap'])}\n"
            bot_txt += f"👉 Currently: ${format_number_string(marketcap)} ({str(round(marketcap_percent, 2))}x)\n"
            if float(marketcap)< float(pair_project['ath_value']):
                bot_txt += f"🏆 ATH: ${format_number_string(pair_project['ath_value'])} ({get_percent(pair_project['ath_value'], pair_project['marketcap'])}x)\n"
            bot_txt += "\n"
        else:
            project = {
                "username": username,
                "user_id": user_id,
                "chat_id": chat_id,
                "chain_id": pair.chain_id,
                "pair_address": pair.pair_address,
                "url": pair.url,
                "token": token,
                "token_symbol": pair.base_token.symbol,
                "marketcap": marketcap,
                "ath_value": marketcap,
                "status": "active",
                "created_at": datetime.utcnow()
            }
            Project.insert_one(project)
            bot_txt = f"🎉 @{username} shilled\n"
            bot_txt += f"👉 <code>{token}</code>\n💰 <a href='{pair.url}' >{pair.base_token.symbol}</a>- Current marketcap: ${format_number_string(marketcap)}"

        return {"is_rug": False, "text": bot_txt, "is_new": is_new}

    except:

        text="There is no liquidity for this token"
        return {"is_rug": True, "reason": "liquidity", "text": text}
    
async def get_user_shillmaster(user):
    return_txt = "❗ There is not any shill yet for @"+user
    username = user.replace("@", "")
    user_shills = Project.find({"username": username}).sort("created_at", -1).limit(5)
    if user_shills != None:
        return_txt = "📊 Shillmaster stats for @"+user+" 📊\n\n"
        for project in user_shills:
            if project['status'] == "active":
                return_txt += "💰 <a href='"+project['url']+"' >"+project['token_symbol']+"</a> Shared marketcap: $"+format_number_string(project['marketcap'])+"\n"
                current_info = await current_status(project)
                
                if current_info['is_liquidity']:
                    if float(current_info['marketcap'])>float(project['ath_value']):
                        Project.update_one({"_id": project['_id']}, {"$set":{"ath_value": current_info['marketcap']}})
                    return_txt += f"👉 Currently: ${format_number_string(current_info['marketcap'])} ({str(round(current_info['percent'], 2))}x)\n"
                    if float(current_info['marketcap'])< float(project['ath_value']):
                        return_txt += f"🏆 ATH: ${format_number_string(project['ath_value'])} ({get_percent(project['ath_value'], project['marketcap'])}x)\n"
                    return_txt += "\n"
                else:
                    is_warn = current_info['is_warn']
                    if is_warn:
                        add_warn(username, project['user_id'], project['chat_id'])
                    return_txt += "👉 Currently: LIQUIDITY REMOVED\n\n"
            
            if project['status'] == "removed":
                return_txt += f"💰 <a href='{project['url']}' >{project['token_symbol']}</a> Shared marketcap: ${format_number_string(project['marketcap'])}\n"
                return_txt += "⚠️ Currently: LIQUIDITY REMOVED\n\n"
                return_txt += f"🏆 ATH: ${format_number_string(project['ath_value'])} ({get_percent(project['ath_value'], project['marketcap'])}x)\n\n"
            
            if project['status'] == "no_liquidity":
                return_txt += f"💰 <a href='{project['url']}' >{project['token_symbol']}</a> has no Liquidity\n"
                return_txt += "⚠️ Got Warn with this token\n\n"
            
            if project['status'] == "honeypot":
                return_txt += f"💰 <a href='{project['url']}' >{project['token_symbol']}</a> look like Honeypot\n"
                return_txt += "⚠️ Got Warn with this token\n\n"

    return return_txt

async def current_status(project):
    try:
        pairs = await get_token_pairs(project['token'])
        filtered_pairs = []
        if len(pairs) > 0:
            filtered_pairs = [pair for pair in pairs if pair.url.lower() == project['url'].lower()]
        
        pair = None
        if len(filtered_pairs)>0:
            pair = max(filtered_pairs, key=attrgetter('liquidity.usd'))

        if pair == None:
            is_warn = user_rug_check(project, 'removed')
            return {"is_liquidity": False, "is_warn": is_warn}
        
        if pair.liquidity.usd <= 100:
            is_warn = user_rug_check(project, 'removed')
            return {"is_liquidity": False, "is_warn": is_warn}
        
        marketcap_info = await cryptocurrency_info(project['token'])
        circulating_supply = 0
        marketcap = pair.fdv
        if marketcap_info != None:
            for key in marketcap_info:
                currency_info = marketcap_info[key]
                if currency_info['self_reported_circulating_supply'] != None:
                    circulating_supply = currency_info['self_reported_circulating_supply']
        if circulating_supply != 0:
            marketcap = circulating_supply*pair.price_usd

        print(project['token'], ": ",circulating_supply)
        marketcap_percent = marketcap/float(project['marketcap'])
        return {"is_liquidity": True, "marketcap": marketcap, "percent": marketcap_percent}
    except:
        return {"is_liquidity":False, "is_warn": False}