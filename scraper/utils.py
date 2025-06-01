# scraper/utils.py
import json
import os

def save_to_json(data, filename="data/osdr_studies.json"):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)