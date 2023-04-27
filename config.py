from pymongo import MongoClient

mongo_url = "mongodb://mongo:0vAcYlPN44ugKCNqFXNc@containers-us-west-203.railway.app:6725"
mongo_client = MongoClient(mongo_url)
mongo_db = mongo_client['shillmaster']

BOT_TOKEN="6127801894:AAExOYxc_EHywwg664RmWGg2myVRThN9mL4"
LEADERBOARD = "-1001964784230"