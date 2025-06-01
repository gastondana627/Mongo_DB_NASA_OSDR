import json
import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the API key securely
api_key = os.getenv("NASA_API_KEY")

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["nasa_osdr"]
collection = db["osdr_data"]

# Load JSON data
with open("osdr_sample.json", "r") as f:
    data = json.load(f)

# Optional: Inject the API key into each document if needed
for doc in data:
    doc["api_key_used"] = api_key  # Optional — comment out if not desired

# Insert into MongoDB
collection.insert_many(data)

print("✅ Data inserted into MongoDB with API key tagging (optional)!")
