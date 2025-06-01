# scraper/get_osd_metadata.py

import requests

def get_metadata_for_osd(accession):
    """
    Fetch metadata for a given OSD accession.
    You can modify this to scrape or call an API as needed.
    """
    try:
        url = f"https://www.ncbi.nlm.nih.gov/research/osd/api/osd/{accession}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch metadata for {accession}. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Exception while fetching metadata for {accession}: {e}")
        return None