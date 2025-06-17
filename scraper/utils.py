# scraper/utils.py
import os
import json
# No MongoDB client initialization here if it's handled by streamlit_main_app.py and passed in

def save_to_mongo(studies_list, collection_obj): # Expects collection_obj to be passed
    if not studies_list:
        print("No studies to save to MongoDB.")
        return 0 # Return count of saved/updated items
    if collection_obj is None:
        print("MongoDB collection object is None. Cannot save.")
        return 0

    print(f"Attempting to save/update {len(studies_list)} studies in MongoDB...")
    saved_count = 0
    updated_count = 0
    for study in studies_list:
        if not isinstance(study, dict):
            print(f"Skipping non-dictionary item: {study}")
            continue
        if "study_id" not in study or not study["study_id"] or study["study_id"] == "N/A":
            print(f"Skipping study due to missing or invalid 'study_id': {study.get('title', 'Unknown title')}")
            continue
        
        try:
            result = collection_obj.update_one(
                {"study_id": study["study_id"]}, 
                {"$set": study}, 
                upsert=True
            )
            if result.upserted_id is not None:
                saved_count += 1
            elif result.modified_count > 0:
                updated_count +=1
            # If no upserted_id and modified_count is 0, it means it matched but no change was made.
            # We can consider this 'processed'. If you only want to count actual inserts/updates:
            # if result.upserted_id is not None or result.modified_count > 0:
            #    processed_count +=1
        except Exception as e:
            print(f"Error saving study {study.get('study_id', 'N/A')} to MongoDB: {e}")
    
    print(f"MongoDB: {saved_count} studies inserted, {updated_count} studies updated.")
    return saved_count + updated_count

def save_to_json(data, filename):
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Data saved to {filename}")
    except Exception as e:
        print(f"Error saving data to JSON file {filename}: {e}")

        