from models import Advertise
from datetime import datetime, timedelta

def get_advertise():
    now_time = datetime.utcnow()
    advertise = Advertise.find_one({"start": {"$lte": now_time}, "end": {"$gte": now_time}, "paid": {"$eq": True}})

    return advertise