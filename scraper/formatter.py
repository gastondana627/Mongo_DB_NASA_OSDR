from bs4 import BeautifulSoup

def extract_study_data(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    studies = []

    # Adjust these selectors based on actual structure
    study_cards = soup.find_all("div", class_="result-item")  # Or whatever the study card uses
    for card in study_cards:
        title = card.find("h4").get_text(strip=True)
        desc = card.find("p").get_text(strip=True)

        studies.append({
            "title": title,
            "description": desc,
            # Add more fields here if visible
        })

    return studies