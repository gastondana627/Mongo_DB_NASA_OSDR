# scraper/utils.py
import json
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# JSON saving
def save_to_json(data, filename="data/osdr_studies.json"):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

# MongoDB saving
MONGO_URI = os.getenv("MONGO_URI")  # Your MongoDB connection string
client = MongoClient(MONGO_URI)
db = client["nasa_osdr"]
collection = db["studies"]

def save_to_mongo(studies):
    for study in studies:
        collection.update_one(
            {"study_id": study["study_id"]},  # Match existing
            {"$set": study},                  # Insert or update
            upsert=True
        )