# update_mongo_with_embeddings.py (Corrected with SSL Fix)

import json
import os
from pymongo import MongoClient
from dotenv import load_dotenv
import certifi # <-- ADDED FOR THE SSL FIX

def update_mongo_with_vectors():
    """
    Loads studies with embeddings from a JSON file and updates the
    corresponding documents in MongoDB with the new vector field.
    """
    load_dotenv()
    MONGO_URI = os.getenv("MONGO_URI")
    if not MONGO_URI:
        print("ERROR: MONGO_URI not found in .env file.")
        return

    print("Connecting to MongoDB...")
    try:
        # --- THIS IS THE CORRECTED CONNECTION LOGIC ---
        ca = certifi.where()
        client = MongoClient(MONGO_URI, tlsCAFile=ca)
        db = client["nasa_osdr"]
        studies_collection = db["studies"]
        # Ping the server to confirm a successful connection
        client.admin.command('ping')
        print("Connection successful.")
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return


    input_file = "data/osdr_studies_with_embeddings.json"
    print(f"Loading data from {input_file}...")
    try:
        with open(input_file, 'r') as f:
            studies_with_embeddings = json.load(f)
        print(f"Loaded {len(studies_with_embeddings)} studies with embeddings.")
    except FileNotFoundError:
        print(f"ERROR: {input_file} not found. Please run generate_embeddings.py first.")
        return

    updated_count = 0
    print("Beginning update process...")
    for study in studies_with_embeddings:
        study_id = study.get('study_id')
        embedding = study.get('text_embedding')

        if not study_id or not embedding:
            continue

        result = studies_collection.update_one(
            {'study_id': study_id},
            {'$set': {'text_embedding': embedding}}
        )
        if result.modified_count > 0:
            updated_count += 1
            # This print statement can be noisy for 550 documents, so let's show progress differently
            if updated_count % 50 == 0:
                 print(f"Updated {updated_count} documents so far...")


    print(f"\nUpdate complete. Successfully updated {updated_count} documents in MongoDB.")

if __name__ == "__main__":
    update_mongo_with_vectors()