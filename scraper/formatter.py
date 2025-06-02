# scraper/formatter.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
from bs4 import BeautifulSoup 
import time
import os
import json

# === HELPER FUNCTIONS ===
def safe_get_text(element, by, value, default="N/A"):
    try:
        return element.find_element(by, value).text.strip()
    except NoSuchElementException:
        return default

def safe_get_attribute(element, by, value, attribute, default="N/A"):
    try:
        return element.find_element(by, value).get_attribute(attribute)
    except NoSuchElementException:
        return default

def get_text_excluding_label(parent_element, label_tag_options=('b', 'span'), label_text_options=('Highlights:',)): # Default to 'b' or 'span' for label tags
    try:
        full_html = parent_element.get_attribute('innerHTML')
        soup = BeautifulSoup(full_html, 'html.parser')
        
        for label_text_option in label_text_options: 
            for tag_name in label_tag_options: 
                labels_in_soup = soup.find_all(tag_name, string=lambda t: t and t.strip().startswith(label_text_option.strip()))
                for label_in_soup in labels_in_soup:
                    label_in_soup.extract() 
        
        remaining_text = soup.get_text(separator=' ', strip=True)
        return remaining_text if remaining_text else "N/A"
    except Exception as e:
        # print(f"Debug: Error in get_text_excluding_label - {e}") 
        return "N/A"
# === END OF HELPER FUNCTIONS ===

def wait_for_all_cards(driver, page_description_for_log="current page", wait_time=20):
    card_container_selector = "div.flex-container.margin-bot-40" 
    try:
        WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, card_container_selector))
        )
    except TimeoutException:
        print(f"❌ No study card containers ({card_container_selector}) found after {wait_time}s on {page_description_for_log}.")
        return [] 

    SCROLL_PAUSE_TIME = 0.75 
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    for _ in range(4): 
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break 
        last_height = new_height
    
    all_cards_found = []
    try:
        all_cards_found = driver.find_elements(By.CSS_SELECTOR, card_container_selector)
    except Exception as e:
        print(f"Error finding card elements on {page_description_for_log} after scroll: {e}")
    return all_cards_found


def extract_study_data_from_current_page(driver, current_page_num_for_log="N/A"):
    studies = []
    study_cards = wait_for_all_cards(driver, page_description_for_log=f"page {current_page_num_for_log}")

    if not study_cards:
        # wait_for_all_cards will print its own error if initial detection fails
        # This print is for if cards are found by wait_for_all_cards, but find_elements here gets none
        # print(f"⚠️ No study cards ultimately retrieved for page {current_page_num_for_log}.") 
        return []
        
    current_osd_for_error = "Unknown OSD" 

    for i, card in enumerate(study_cards):
        study_id_val, title_val = "N/A", "N/A"
        current_osd_for_error = "Unknown OSD" 
            
        try:
            title_element = card.find_element(By.CSS_SELECTOR, "p.title a") 
            title_val = title_element.text.strip()
            study_link = title_element.get_attribute("href")

            study_id_val = safe_get_text(card, By.CSS_SELECTOR, "div.accession-wrapper div.accession")
            current_osd_for_error = study_id_val 
                
            image_url = safe_get_attribute(card, By.CSS_SELECTOR, "img.type-image", "src")

            organisms, factors, assay_types, release_date, description = "N/A", "N/A", "N/A", "N/A", "N/A" # Initialize description
            try:
                mini_table = card.find_element(By.CSS_SELECTOR, "table.mat-table.searchResultTable")
                organisms = safe_get_text(mini_table, By.CSS_SELECTOR, "td.mat-column-organisms")
                factors = safe_get_text(mini_table, By.CSS_SELECTOR, "td.mat-column-factors")
                assay_types = safe_get_text(mini_table, By.CSS_SELECTOR, "td.mat-column-assays")
                release_date = safe_get_text(mini_table, By.CSS_SELECTOR, "td.mat-column-releaseDate")
                # --- DESCRIPTION IS NOW EXTRACTED FROM THE MINI-TABLE ---
                description = safe_get_text(mini_table, By.CSS_SELECTOR, "td.mat-column-description")
                if description and description.endswith("..."): 
                    description = description[:-3].strip()

            except NoSuchElementException:
                print(f"⚠️ Mini-table or a column (incl. description) not found in card {i+1} on page {current_page_num_for_log} (ID: {current_osd_for_error})")
            
            highlights = "N/A"
            try:
                # Using the structure: <div class="mt-5 ng-star-inserted"><b>Highlights: </b><span>...</span></div>
                # This XPath targets the div if its first child is a <b> starting with "Highlights:"
                highlights_container_xpath = ".//div[child::b[1][starts-with(normalize-space(.), 'Highlights:')]]"
                highlights_container_div = card.find_element(By.XPATH, highlights_container_xpath)
                highlights = get_text_excluding_label(highlights_container_div, label_tag_options=['b'], label_text_options=['Highlights:'])
                if highlights == "N/A" or not highlights.strip():
                     highlights = "N/A" # Ensure it's N/A if helper returns empty
            except NoSuchElementException:
                # This is okay if highlights are often missing. Can be made less verbose.
                # print(f"ℹ️ Highlights section not found for card {i+1} on page {current_page_num_for_log} (ID: {current_osd_for_error})")
                pass

            if study_id_val == "N/A" and title_val == "N/A":
                continue

            study_data = {
                "study_id": study_id_val, "study_link": study_link, "title": title_val, "image_url": image_url,
                "organisms": [org.strip() for org in organisms.split(',') if org.strip()] if organisms and organisms != "N/A" else [],
                "factors": [factor.strip() for factor in factors.split(',') if factor.strip()] if factors and factors != "N/A" else [],
                "assay_types": [assay.strip() for assay in assay_types.split(',') if assay.strip()] if assay_types and assay_types != "N/A" else [],
                "release_date": release_date, 
                "description": description, 
                "highlights": highlights
            }
            studies.append(study_data)
        except Exception as e_card:
            print(f"❌ Error processing content of card {i+1} on page {current_page_num_for_log} (ID: {current_osd_for_error}): {type(e_card).__name__} - {e_card}")
    return studies


def extract_study_data(max_pages_to_scrape=22): # Default to 22 pages (550 studies)
    options = Options()
    # options.add_argument("--headless") # Keep it headed to observe browser behavior
    options.add_argument("--window-size=1920,1200")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--log-level=1") 

    driver = webdriver.Chrome(options=options)
    all_extracted_studies = []
    
    current_page_num_actual = 0 
    base_url = "https://osdr.nasa.gov/bio/repo/search?q=&data_source=cgene,alsda&data_type=study&size=25"

    try:
        initial_url = f"{base_url}&page={current_page_num_actual}"
        print(f"📡 Fetching data from initial page {current_page_num_actual + 1}: {initial_url}")
        driver.get(initial_url)
        time.sleep(2) 

        for i in range(max_pages_to_scrape): # This loop controls how many pages we ATTEMPT to scrape
            page_desc = f"page {current_page_num_actual + 1}"
            print(f"--- Processing {page_desc} ---")
            
            page_studies = extract_study_data_from_current_page(driver, current_page_num_for_log=(current_page_num_actual + 1))
            
            if not page_studies:
                # If no studies found on the current page (could be first or subsequent)
                print(f"No studies extracted from {page_desc}. Checking if page is truly empty or end of results.")
                # Check if there are any card containers at all on this page
                if not driver.find_elements(By.CSS_SELECTOR, "div.flex-container.margin-bot-40"):
                    print(f"{page_desc} appears to be genuinely empty of cards. Stopping pagination.")
                    break 
                # If card containers were found by wait_for_all_cards but extract_study_data_from_current_page returned [],
                # it means parsing failed for all of them on this page.
                # This might indicate the end or a page with a different structure.
                print(f"Although card containers might have been detected on {page_desc}, no data was extracted. Assuming end or issue.")
                break
            
            all_extracted_studies.extend(page_studies)
            print(f"Extracted {len(page_studies)} from {page_desc}. Total studies so far: {len(all_extracted_studies)}")

            if i >= max_pages_to_scrape - 1: # Check if we've hit the loop's limit
                print(f"Reached max_pages_to_scrape ({max_pages_to_scrape}). Stopping.")
                break

            # --- "Next Page" button logic ---
            try:
                # ***** YOU MUST INSPECT AND PROVIDE THE CORRECT SELECTOR AND DISABLED MECHANISM *****
                next_button_selector = "button.mat-paginator-navigation-next" # Current guess - VERIFY!
                # Alternative using aria-label if more reliable:
                # next_button_selector = "button[aria-label='Next page']" 
                
                next_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, next_button_selector))
                )
                
                button_classes = next_button.get_attribute("class") or "" 
                is_disabled = next_button.get_attribute("disabled") == "true" or \
                              "mat-button-disabled" in button_classes.split() # VERIFY 'mat-button-disabled'
                
                if is_disabled:
                    print(f"⏹️ Next page button is present but disabled on {page_desc}. Reached the last page of results.")
                    break
                
                print(f"Attempting to click 'Next page' button to go from {page_desc}...")
                driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", next_button)
                time.sleep(0.5) 
                WebDriverWait(driver, 5).until(EC.element_to_be_clickable(next_button)).click()
                
                current_page_num_actual += 1 
                print(f"Successfully clicked 'Next'. Waiting for new page content (now page {current_page_num_actual + 1})...")
                time.sleep(3.5) # Longer pause for next page to fully load/render after click

            except TimeoutException: 
                print(f"ℹ️ Next page button not found (Timeout) after {page_desc}. Assuming it's the last page.")
                break 
            except NoSuchElementException:
                print(f"ℹ️ Next page button not found (NoSuchElement) after {page_desc}. Assuming it's the last page.")
                break
            except Exception as e_paginator:
                print(f"⚠️ Error clicking 'Next page' button or checking paginator after {page_desc}: {e_paginator}. Stopping pagination.")
                break 
        # --- End of "Next Page" button logic ---

        print(f"\n✅ Extraction complete. Total studies extracted: {len(all_extracted_studies)}.")
        return all_extracted_studies

    except Exception as e_main: 
        print(f"❌ An critical error occurred during the multi-page extraction process: {e_main}")
        try:
            driver.save_screenshot("debug_screenshot_critical_error.png")
            with open("debug_html_critical_error.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
        except Exception as e_debug_save:
            print(f"Could not save debug files during critical error: {e_debug_save}")
        import traceback
        traceback.print_exc()
        return all_extracted_studies 
    finally:
        print("Closing browser.")
        if 'driver' in locals() and driver is not None:
            driver.quit()

if __name__ == '__main__':
    print("Running formatter.py directly for testing...")
    # Test with a specific number of pages
    extracted_studies = extract_study_data(max_pages_to_scrape=2) # Default to 2 pages for CLI test
    if extracted_studies:
        print(f"\n--- Successfully Extracted {len(extracted_studies)} Studies ---")
        if extracted_studies: 
            print("\n--- First Study Example ---")
            for key, value in extracted_studies[0].items(): 
                print(f"  {key}: {value}")
        
        output_dir = os.path.join(os.path.dirname(__file__), "..", "data") 
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except OSError as e_dir: 
                print(f"Error creating directory {output_dir}: {e_dir}")
                output_dir = "." 
        
        test_file_path = os.path.join(output_dir, "formatter_test_output.json")
        try:
            with open(test_file_path, "w") as f_json: 
                json.dump(extracted_studies, f_json, indent=4)
            print(f"\nTest output saved to: {test_file_path}")
        except IOError as e_io: 
            print(f"Error writing test output to {test_file_path}: {e_io}")
    else:
        print("No studies extracted during the test run.")