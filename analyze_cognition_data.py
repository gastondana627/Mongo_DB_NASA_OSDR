from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["nasa_osdr"]
collection = db["cognition_data"]

# Show sample data
print("Sample Documents:")
for doc in collection.find().limit(3):
    print(doc)

# Example: Count entries by subject
pipeline = [
    {"$group": {"_id": "$Subject", "count": {"$sum": 1}}}
]
print("\nCount by Subject:")
for result in collection.aggregate(pipeline):
    print(result)