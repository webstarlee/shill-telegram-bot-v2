from pymongo import MongoClient

mongo_url = "mongodb://mongo:0vAcYlPN44ugKCNqFXNc@containers-us-west-203.railway.app:6725"
mongo_client = MongoClient(mongo_url)
mongo_db = mongo_client['shillmaster']

BOT_TOKEN="5980518310:AAH59J2CU_roxuHRfArHzq3HTuB_Dlymp-4"
LEADERBOARD_ID = "-1001894150735"