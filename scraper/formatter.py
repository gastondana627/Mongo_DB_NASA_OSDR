from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import os

def wait_for_all_cards(driver, wait_time=30):
    print("⏳ Scrolling and waiting for studies to render...")
    SCROLL_PAUSE_TIME = 2
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    try:
        WebDriverWait(driver, wait_time).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".card"))
        )
        print("✅ Study cards detected.")
    except Exception as e:
        print("❌ Cards not found even after scroll:", e)

    return driver.find_elements(By.CSS_SELECTOR, ".card")


def extract_study_data():
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)

    try:
        url = "https://osdr.nasa.gov/bio/repo/search?q=&data_source=cgene,alsda&data_type=study&size=100"
        print("📡 Fetching data from NASA OSDR web page using Selenium...")
        driver.get(url)

        time.sleep(5)  # Let Angular render initial content

        rows = wait_for_all_cards(driver)

        # Save screenshot and HTML for inspection
        driver.save_screenshot("debug_screenshot.png")
        with open("debug.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)

        # Dump unique classes to help with debugging
        soup = BeautifulSoup(driver.page_source, "html.parser")
        all_classes = set()
        for tag in soup.find_all(True):
            class_attr = tag.get("class")
            if class_attr:
                all_classes.update(class_attr)
        print("📦 Unique classes found in page:", sorted(all_classes))

        if not rows:
            print("⚠️ No studies were found.")
            return []

        studies = []
        for row in rows:
            try:
                title = row.find_element(By.CSS_SELECTOR, ".title").text.strip()
                description = row.find_element(By.CSS_SELECTOR, ".description").text.strip()
                link = row.find_element(By.TAG_NAME, "a").get_attribute("href")

                studies.append({
                    "title": title,
                    "description": description,
                    "link": link
                })
            except Exception as e:
                print(f"❌ Error parsing study row: {e}")

        return studies

    except Exception as e:
        print("❌ Error during extraction:", e)
        return []

    finally:
        driver.quit()