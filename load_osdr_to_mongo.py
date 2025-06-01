from pymongo import MongoClient
import json

client = MongoClient("mongodb://localhost:27017/")
db = client["nasa_osdr"]
collection = db["cognition_data"]

with open("data/nasa_cognition.json") as f:
    data = [json.loads(line) for line in f]

collection.insert_many(data)
print("Data loaded into MongoDB.")