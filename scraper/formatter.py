from bs4 import BeautifulSoup

def extract_study_data(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    print(soup.prettify()[:1000])  # Debug: preview first 1000 characters of HTML

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

    print(f"✅ Found {len(studies)} studies.")  # Print final count after loop
    return studies