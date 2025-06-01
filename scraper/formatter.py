from bs4 import BeautifulSoup

def extract_study_data(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    studies = []

    # Select all <a> tags inside <p> tags with links to study pages
    anchors = soup.select("p > a[href^='/bio/repo/data/studies/']")

    for a in anchors:
        title = a.get_text(strip=True)
        link = a["href"]

        studies.append({
            "title": title,
            "link": f"https://osdr.nasa.gov{link}"
        })

    return studies