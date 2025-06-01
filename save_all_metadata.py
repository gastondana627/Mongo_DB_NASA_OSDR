# save_all_metadata.py
# save_all_metadata.py

import os
import json
from scraper.get_osd_metadata import get_metadata_for_osd

def save_all_metadata(osd_list, output_folder="osd_metadata"):
    os.makedirs(output_folder, exist_ok=True)
    for accession in osd_list:
        metadata = get_metadata_for_osd(accession)
        if metadata:
            with open(f"{output_folder}/{accession}.json", "w") as f:
                json.dump(metadata, f, indent=2)
            print(f"Saved metadata for {accession}")
        else:
            print(f"Skipped {accession} (no metadata)")