# scraper/formatter.py (Final Production Version)

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

def get_driver():
    """Initializes and returns a Selenium WebDriver for a headless cloud environment."""
    options = ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    
    # This points to the Chrome binary installed by our Dockerfile
    # It's not strictly necessary if Chrome is on the default PATH, but it's more robust
    options.binary_location = "/usr/bin/google-chrome-stable" 
    
    service = ChromeService()
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def extract_study_data(max_pages_to_scrape=22):
    """
    Main function to orchestrate the scraping of multiple pages from the OSDR website.
    """
    driver = get_driver()
    all_studies = []
    base_url = "https://osdr.nasa.gov/bio/repo/search?q=&data_source=cgene,alsda&data_type=study&size=25"
    
    try:
        current_page_num = 0
        while current_page_num < max_pages_to_scrape:
            page_index = current_page_num
            url = f"{base_url}&page={page_index}"
            print(f"📡 Fetching data from page {page_index + 1}: {url}")
            driver.get(url)
            
            WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.card")))
            soup = BeautifulSoup(driver.page_source, "html.parser")
            study_cards = soup.select("div.card")
            
            if not study_cards:
                print(f"No more study cards found on page {page_index + 1}. Stopping.")
                break

            for card in study_cards:
                study_id = card.select_one("h5.card-title strong").text.strip() if card.select_one("h5.card-title strong") else "N/A"
                title = card.select_one("p.card-title a").text.strip() if card.select_one("p.card-title a") else "N/A"
                study_link = "https://osdr.nasa.gov" + card.select_one("p.card-title a")['href'] if card.select_one("p.card-title a") else "N/A"
                description = card.select_one("p.card-text").text.strip() if card.select_one("p.card-text") else "N/A"
                
                details = {li.text.split(":", 1)[0].strip().lower().replace(" ", "_"): [v.strip() for v in li.text.split(":", 1)[1].split(',')] if len(li.text.split(":", 1)) > 1 else [] for li in card.select("ul.list-group li.list-group-item")}

                all_studies.append({
                    "study_id": study_id, "title": title, "study_link": study_link,
                    "description": description, "image_url": "N/A",
                    "organisms": details.get("organisms", []),
                    "factors": details.get("factors", []),
                    "assay_types": details.get("assay_types", []),
                    "release_date": details.get("release_date", ["N/A"])[0]
                })

            print(f"Extracted {len(study_cards)} studies from page {page_index + 1}.")
            
            # Check for the next page button
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, "a.page-link[aria-label='Next page']")
                # A simple way to check if the button is disabled is to check if its parent `li` has the 'disabled' class
                parent_li = next_button.find_element(By.XPATH, "..")
                if "disabled" in parent_li.get_attribute("class"):
                    print("Last page reached. Stopping.")
                    break
                next_button.click()
                time.sleep(2) # Wait for the next page to load
            except:
                print("Could not find or click the 'Next page' button. Assuming last page.")
                break
                
            current_page_num += 1
            
    finally:
        print("Closing browser.")
        driver.quit()
        
    print(f"\n✅ Extraction complete. Total studies extracted: {len(all_studies)}.")
    return all_studies