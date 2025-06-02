# scraper/formatter.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
from bs4 import BeautifulSoup # Added for the new helper
import time
import os
import json

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

def get_text_excluding_label(parent_element, label_tag_options=('span', 'b'), label_text_options=('Description:', 'Highlights:')):
    # This function attempts to get all text from parent_element, excluding a specific label.
    # It's designed for cases where the label (e.g., <b>Description:</b>) is a sibling to other text nodes or simple spans.
    try:
        full_html = parent_element.get_attribute('innerHTML')
        soup = BeautifulSoup(full_html, 'html.parser')
        
        label_found_and_removed = False
        for label_text_option in label_text_options: # e.g., "Description:"
            for tag_name in label_tag_options: # e.g., 'b' or 'span'
                # Find all occurrences of the label tag that contain the label_text_option
                # We are looking for tags whose direct string or stripped text content equals the label.
                # Using a lambda for string matching to be more precise with stripped text.
                labels_in_soup = soup.find_all(tag_name, string=lambda t: t and t.strip() == label_text_option)
                for label_in_soup in labels_in_soup:
                    label_in_soup.extract() # Remove the found label tag
                    label_found_and_removed = True
        
        # Get the remaining text, join parts with spaces, and strip leading/trailing whitespace.
        remaining_text = soup.get_text(separator=' ', strip=True)
        return remaining_text if remaining_text else "N/A"
        
    except Exception as e:
        # print(f"Error in get_text_excluding_label for element HTML: {parent_element.get_attribute('outerHTML')}, Error: {e}") # Debug this function
        return "N/A"


def wait_for_all_cards(driver, wait_time=30):
    card_container_selector = "div.flex-container.margin-bot-40" 
    
    # print(f"⏳ Waiting for study cards ({card_container_selector}) to load...")
    try:
        WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, card_container_selector))
        )
        # print("✅ At least one study card container detected.")
    except TimeoutException:
        print(f"❌ No study card containers ({card_container_selector}) found after {wait_time} seconds on current page.")
        # driver.save_screenshot("debug_screenshot_cards_not_found.png") # Less critical if pagination is working
        # with open("debug_html_cards_not_found.html", "w", encoding="utf-8") as f:
        #     f.write(driver.page_source)
        return [] # Return empty if no cards, page might be empty

    # print("⏳ Scrolling and waiting for all study cards to render on current page...")
    SCROLL_PAUSE_TIME = 1.5 # Can be shorter if not expecting many lazy-loaded items per scroll
    last_height = driver.execute_script("return document.body.scrollHeight")
    consecutive_no_change = 0
    max_consecutive_no_change = 2 

    # Perform a few scrolls to ensure all content on the page is loaded
    for _ in range(3): # Scroll 3 times to be reasonably sure
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            consecutive_no_change +=1
            if consecutive_no_change >= max_consecutive_no_change:
                # print("📜 Scroll height reached the end for this page.") # Less verbose
                break
        else:
            consecutive_no_change = 0 
        last_height = new_height
    
    all_cards_found = []
    try:
        # After scrolling, get all card elements
        all_cards_found = driver.find_elements(By.CSS_SELECTOR, card_container_selector)
        # print(f"✅ {len(all_cards_found)} study card containers detected on current page after scroll.")
    except Exception as e:
        print(f"Error finding card elements after scroll: {e}")
            
    return all_cards_found


def extract_study_data_from_current_page(driver):
    studies = []
    study_cards = wait_for_all_cards(driver) # This now handles waiting & scrolling for current page

    if not study_cards:
        # print("⚠️ No study cards found on current page by wait_for_all_cards.") # wait_for_all_cards will print its own error
        return []
        
    # print(f"Extracting data from {len(study_cards)} detected cards on current page...")
    current_osd_for_error = "Unknown OSD" 

    for i, card in enumerate(study_cards):
        study_id_val = "N/A" 
        title_val = "N/A"
        current_osd_for_error = "Unknown OSD" 
            
        try:
            title_element = card.find_element(By.CSS_SELECTOR, "p.title a") 
            title_val = title_element.text.strip()
            study_link = title_element.get_attribute("href")

            study_id_val = safe_get_text(card, By.CSS_SELECTOR, "div.accession-wrapper div.accession")
            current_osd_for_error = study_id_val 
                
            image_url = safe_get_attribute(card, By.CSS_SELECTOR, "img.type-image", "src")

            organisms, factors, assay_types, release_date = "N/A", "N/A", "N/A", "N/A"
            try:
                mini_table = card.find_element(By.CSS_SELECTOR, "table.mat-table.searchResultTable")
                organisms = safe_get_text(mini_table, By.CSS_SELECTOR, "td.mat-column-organisms")
                factors = safe_get_text(mini_table, By.CSS_SELECTOR, "td.mat-column-factors")
                assay_types = safe_get_text(mini_table, By.CSS_SELECTOR, "td.mat-column-assays")
                release_date = safe_get_text(mini_table, By.CSS_SELECTOR, "td.mat-column-releaseDate")
            except NoSuchElementException:
                print(f"⚠️ Mini-table not found in card {i+1} (Study ID: {current_osd_for_error})")

            description = "N/A"
            try:
                # XPATH NEEDS VERIFICATION - finds a div containing a b or span tag with "Description:"
                desc_container_xpath = ".//div[.//(*[self::b or self::span][normalize-space(starts-with(., 'Description:'))])]"
                description_container_div = card.find_element(By.XPATH, desc_container_xpath)
                description = get_text_excluding_label(description_container_div, label_text_options=['Description:'])
                if description == "N/A": # If helper returned N/A (e.g. an error in helper)
                    print(f"⚠️ Description (via helper) not extracted for card {i+1} (Study ID: {current_osd_for_error})")
            except NoSuchElementException:
                # This means the container div itself was not found by the XPath
                print(f"⚠️ Description container div not found for card {i+1} (Study ID: {current_osd_for_error})")
            
            highlights = "N/A"
            try:
                # XPATH NEEDS VERIFICATION - finds a div containing a b or span tag with "Highlights:"
                highlights_container_xpath = ".//div[.//(*[self::b or self::span][normalize-space(starts-with(., 'Highlights:'))])]"
                highlights_container_div = card.find_element(By.XPATH, highlights_container_xpath)
                highlights = get_text_excluding_label(highlights_container_div, label_text_options=['Highlights:'])
                if highlights == "N/A":
                     print(f"⚠️ Highlights (via helper) not extracted for card {i+1} (Study ID: {current_osd_for_error})")
            except NoSuchElementException:
                print(f"⚠️ Highlights container div not found for card {i+1} (Study ID: {current_osd_for_error})")

            if study_id_val == "N/A" and title_val == "N/A":
                # print(f"⚠️ Skipping card {i+1} as it seems empty or malformed.") # Less verbose
                continue

            study_data = {
                "study_id": study_id_val, "study_link": study_link, "title": title_val, "image_url": image_url,
                "organisms": [org.strip() for org in organisms.split(',') if org.strip()] if organisms and organisms != "N/A" else [],
                "factors": [factor.strip() for factor in factors.split(',') if factor.strip()] if factors and factors != "N/A" else [],
                "assay_types": [assay.strip() for assay in assay_types.split(',') if assay.strip()] if assay_types and assay_types != "N/A" else [],
                "release_date": release_date, "description": description, "highlights": highlights
            }
            studies.append(study_data)
        except Exception as e_card:
            print(f"❌ Error processing content of study card {i+1} (Study ID: {current_osd_for_error}): {e_card}")
    
    # print(f"✅ Extracted {len(studies)} studies from this page.") # Less verbose
    return studies


def extract_study_data(max_pages_to_scrape=23): # Default to attempt all ~548 studies (22-23 pages)
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1200") # Slightly taller window
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--log-level=0") # Reduce Selenium's own logging verbosity

    driver = webdriver.Chrome(options=options)
    all_extracted_studies = []
    base_url = "https://osdr.nasa.gov/bio/repo/search?q=&data_source=cgene,alsda&data_type=study&size=25"

    try:
        for page_num in range(max_pages_to_scrape): 
            current_url = f"{base_url}&page={page_num}"
            print(f"📡 Fetching data from page {page_num + 1}/{max_pages_to_scrape}: {current_url}")
            driver.get(current_url)
            
            page_studies = extract_study_data_from_current_page(driver) # This now includes wait_for_all_cards
            
            if not page_studies and page_num > 0 : # If not the first page and no studies, likely end.
                print(f"No studies extracted from page {page_num + 1}. Assuming end of results.")
                break 
            
            all_extracted_studies.extend(page_studies)
            print(f"Extracted {len(page_studies)} from page {page_num + 1}. Total studies so far: {len(all_extracted_studies)}")

            # Robust "Next Page" button check
            try:
                # **YOU MUST VERIFY THIS SELECTOR AND THE DISABLED MECHANISM**
                # Common selectors for Angular Material paginator next button:
                # 1. By specific class and not having disabled attribute/class
                #    next_button_selector = "button.mat-paginator-navigation-next:not([disabled]):not(.mat-button-disabled)"
                # 2. By aria-label
                next_button_selector_aria = "button[aria-label='Next page']"
                
                next_button = WebDriverWait(driver, 7).until( # Wait a bit for paginator to be interactable
                    EC.presence_of_element_located((By.CSS_SELECTOR, next_button_selector_aria))
                )
                
                # Check if disabled (common ways)
                is_disabled = next_button.get_attribute("disabled") == "true" or \
                              "mat-button-disabled" in next_button.get_attribute("class").split()
                
                if is_disabled:
                    print("⏹️ Next page button is present but disabled. Reached the last page of results.")
                    break
                if page_num == max_pages_to_scrape - 1: # If it's the last page we intend to scrape
                    print(f"Reached max_pages_to_scrape ({max_pages_to_scrape}). Stopping.")
                    break

                # Scroll to button and click (attempting to handle potential interceptions)
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                    time.sleep(0.5) # Short pause for scrolling
                    WebDriverWait(driver, 5).until(EC.element_to_be_clickable(next_button)).click()
                except ElementClickInterceptedException:
                    print("Click intercepted, trying JavaScript click on next page button...")
                    driver.execute_script("arguments[0].click();", next_button)
                
                # print(f"Navigated to page {page_num + 2}") # Less verbose
                time.sleep(2) # Pause after click for next page to start loading

            except TimeoutException: 
                print("ℹ️ Next page button not found (Timeout after 7s). Assuming it's the last page.")
                break 
            except NoSuchElementException:
                print("ℹ️ Next page button not found (NoSuchElement). Assuming it's the last page.")
                break
            except Exception as e_paginator:
                print(f"⚠️ Error interacting with paginator: {e_paginator}. Stopping pagination.")
                break 

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
    # Test with a smaller number of pages (e.g., 3 pages)
    extracted_studies = extract_study_data(max_pages_to_scrape=3) 
    if extracted_studies:
        print(f"\n--- Successfully Extracted {len(extracted_studies)} Studies ---")
        # If you want to see the data for the first study:
        # if extracted_studies:
        #     print("\n--- First Study Example ---")
        #     for key, value in extracted_studies[0].items(): 
        #         print(f"  {key}: {value}")
        
        output_dir = os.path.join(os.path.dirname(__file__), "..", "data") # Assumes 'data' is one level up from 'scraper'
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
                print(f"Created directory: {output_dir}")
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