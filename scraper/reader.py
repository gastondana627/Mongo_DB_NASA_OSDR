# scraper/reader.py

#from scraper.formatter import extract_study_data
#import json
#import os

#def fetch_and_save_osdr_studies():
#    print("📡 Fetching data from NASA OSDR web page...\n")
#    studies = extract_study_data()  # now uses Selenium internally

    # Save the studies to a local JSON file
#    os.makedirs("data", exist_ok=True)
#    with open("data/osdr_studies.json", "w") as f:
#        json.dump(studies, f, indent=2)

#    print(f"\n✅ Saved {len(studies)} studies to data/osdr_studies.json")