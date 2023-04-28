from models import Advertise, Invoice
from datetime import datetime, timedelta
from config import wallet
from helpers import invoice_hash

def get_advertise():
    now_time = datetime.utcnow()
    advertise = Advertise.find_one({"start": {"$lte": now_time}, "end": {"$gte": now_time}, "paid": {"$eq": True}})

    return advertise

def new_advertise(data):
    selected_time = int(data['time'])
    selected_hours = int(data['hours'])
    today_time = datetime.utcnow().strftime('%d/%m/%Y')
    today = datetime.strptime(today_time, "%d/%m/%Y")
    start_time = today + timedelta(hours=selected_time)
    end_time = start_time + timedelta(hours=selected_hours)
    advertise = {
        "username":data['username'],
        "start":start_time,
        "end":end_time,
        "paid": False,
        "created_at": datetime.utcnow()
    }
    Advertise.insert_one(advertise)

    return advertise

def create_invoice(advertise, symbol, quantity):
    address = wallet
    hash=invoice_hash()
    invoice = {
        "username": advertise['username'],
        "hash": hash,
        "advertise_id": advertise['_id'],
        "address": address,
        "symbol": symbol,
        "quantity": quantity,
        "paid": False,
        "created_at": datetime.utcnow()
    }
    Invoice.insert_one(invoice)

    return invoice

def check_available_time():
    current_hour_str = datetime.utcnow().strftime('%d/%m/%Y %H')
    current_date_str = datetime.utcnow().strftime('%d/%m/%Y')
    current_hour = datetime.strptime(current_hour_str, "%d/%m/%Y %H")
    current_date = datetime.strptime(current_date_str, "%d/%m/%Y")
    start_time = current_hour+timedelta(hours=1)
    end_time = current_date+timedelta(hours=24)
    number_start = int(start_time.strftime('%H'))
    number_array = []
    for time_number in range(number_start, 25):
        number_array.append(time_number)

    advertises = Advertise.find({"start": { "$lte": end_time }, "end": {"$gte": start_time}, "paid": {"$eq": True}})

    db_number_array = []
    if advertises != None:
        for advertise in advertises:
            db_number_start = int(advertise['start'].strftime('%H'))
            if db_number_start == 0:
                db_number_start = 24
            delta = advertise['end']-advertise['start']
            delta_hour = delta.seconds/3600
            db_number_end = db_number_start+int(delta_hour)
            if db_number_end > 24:
                db_number_end = 25
            for time_number in range(db_number_start-1, db_number_end):
                if not time_number in db_number_array:
                    db_number_array.append(time_number)

    if len(db_number_array) > 0:
        for item in db_number_array:
            if item in number_array:
                number_array.remove(item)

    return number_array

def check_available_hour(time):
    current_date_str = datetime.utcnow().strftime('%d/%m/%Y')
    current_date = datetime.strptime(current_date_str, "%d/%m/%Y")
    end_time = current_date+timedelta(hours=time)
    advertises = Advertise.find({"start": { "$gte": end_time }, "paid": {"$eq": True}})
    origin_array = [2,4,8,12,24]
    if advertises != None:
        for advertise in advertises:
            db_number_start = int(advertise['start'].strftime('%H'))
            if int(time)+2 > db_number_start:
                if 2 in origin_array: origin_array.remove(2)
            if int(time)+4 > db_number_start:
                if 4 in origin_array: origin_array.remove(4)
            if int(time)+8 > db_number_start:
                if 8 in origin_array: origin_array.remove(8)
            if int(time)+12 > db_number_start:
                if 12 in origin_array: origin_array.remove(12)
            if int(time)+24 > db_number_start:
                if 24 in origin_array: origin_array.remove(24)

    return origin_array

def get_invoice(hash, username):
    return Invoice.find_one({"hash": hash, "username": username})

def complete_invoice(data):
    return False
    # try:
    #     invoice = Invoice.find_one({"_id": data['invoice_id']})
    #     if invoice != None:
    #         chain = "eth"
    #         if invoice['symbol'] == "BNB": chain = "bsc"
    #         params = {"chain": chain, "transaction_hash": data['transaction']}
            
    #         response = evm_api.transaction.get_transaction(api_key=api_key, params=params)
    #         transaction = response
    #         value = int(transaction['value'])
    #         final_value = value/10**18
    #         if str(transaction['to_address']).lower() == str(invoice['address']).lower() and float(invoice['quantity']) <= float(final_value):
    #             Invoice.update_one({"_id", invoice['_id']}, {"$set": {"paid": True}})
    #             return True
        
    #     return False
    # except:
    #     return False

def edit_advertise(data):
    invoice = Invoice.find_one({"_id": data['invoice_id']})
    if invoice != None:
        if invoice['paid']:
            advertise = Advertise.find_one_and_update({"_id": invoice['advertise_id']}, {"$set": {"text": data['text'], "url": data['url'], "paid": True}})
            return advertise
            
    return None
