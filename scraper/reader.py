# scraper/reader.py

import requests

def get_osdr_studies_html():
    url = "https://osdr.nasa.gov/bio/repo/search?q=&data_source=cgene,alsda&data_type=study"
    response = requests.get(url)
    response = requests.get(url)
    response.raise_for_status()
    return response.text