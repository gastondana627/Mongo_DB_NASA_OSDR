# NASA OSDR Data Extractor & Knowledge Graph Explorer

## 🚀 Project Overview

This project is a Python-based application designed to extract research study data from the NASA Open Science Data Repository (OSDR), store it, and provide tools for exploration and (planned) knowledge graph visualization. It utilizes Selenium for web scraping, MongoDB for data persistence, and Streamlit for the user interface. The eventual goal is to build a knowledge graph using Neo4j to uncover relationships within the OSDR data.

**Current Status:** Successfully scrapes approximately 548 studies across ~22 pages from the NASA OSDR website, extracting detailed information for each study. Data is saved to a local JSON file and upserted into a MongoDB database. The Streamlit application allows users to trigger the data extraction process and explore the stored MongoDB data with basic filters.

## ✨ Features Implemented

* **Web Scraping:**
    * Uses Selenium and ChromeDriver to navigate the dynamic NASA OSDR website.
    * Implements multi-page pagination by interacting with "Next page" elements.
    * Extracts key data fields per study: Study ID, Title, Study Link, Image URL, Organisms, Factors, Assay Types, Release Date, Description, and Highlights.
* **Data Storage:**
    * Saves all extracted study data into a structured JSON file (`data/osdr_studies.json`).
    * Upserts (updates or inserts) study data into a MongoDB collection (`nasa_osdr.studies`), using `study_id` as the unique identifier.
* **Streamlit Web Application:**
    * **Data Extract & Store Tab:** Allows users to initiate the full data scraping process with UI feedback (progress messages, status updates using `st.empty()`).
    * **Study Explorer (MongoDB) Tab:** Enables users to browse and filter the studies stored in MongoDB by Organism, Factor, or Study ID. Displays detailed information for each study in an expandable view.
    * **Knowledge Graph (Neo4j) Tab (Placeholder):** UI elements and session state logic are in place to eventually display study-specific knowledge graphs and general graph overviews from a Neo4j database.
* **Environment Configuration:** Uses a `.env` file for managing sensitive information like the MongoDB URI.

## 🛠️ Tech Stack

* **Programming Language:** Python 3.12 (or your version)
* **Web Scraping:** Selenium, ChromeDriver
* **HTML Parsing (Helper):** BeautifulSoup4
* **Web Application Framework:** Streamlit
* **Database:** MongoDB (using Pymongo driver)
* **Planned Graph Database:** Neo4j (using `neo4j-driver`)
* **Environment Management:** `python-dotenv`
* **Standard Libraries:** `os`, `json`, `time`, `sys`, `traceback`

## ⚙️ Setup and Installation

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/](https://github.com/)[your-github-username]/[your-repo-name].git
    cd [your-repo-name]
    ```
2.  **Create a Python Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install Dependencies:**
    Create a `requirements.txt` file (see contents below) and run:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Install ChromeDriver:**
    * Download the ChromeDriver executable that matches your installed Google Chrome browser version from [https://chromedriver.chromium.org/downloads](https://chromedriver.chromium.org/downloads).
    * Ensure ChromeDriver is in your system's PATH or place it in the project's root directory (the script currently expects it to be in PATH).
5.  **Setup MongoDB:**
    * Install MongoDB Community Server from [https://www.mongodb.com/try/download/community](https://www.mongodb.com/try/download/community) or use Docker.
    * Ensure your MongoDB server is running (usually on `localhost:27017`).
6.  **Create `.env` File:**
    * In the project's root directory, create a file named `.env`.
    * Add your MongoDB connection URI:
        ```
        MONGO_URI="mongodb://localhost:27017/"
        ```
        (Adjust if your MongoDB setup is different).
7.  **(Future) Setup Neo4j:**
    * Install Neo4j Desktop or Server from [https://neo4j.com/download/](https://neo4j.com/download/).
    * Ensure the Neo4j server is running.
    * You will need to configure connection details (URI, user, password) likely in your `.env` file or directly in the Neo4j connection script for the knowledge graph features.

## ▶️ How to Run

1.  **Start your MongoDB server** if it's not already running.
2.  **(Future) Start your Neo4j server** if you are working on the knowledge graph features.
3.  **Activate your Python virtual environment:**
    ```bash
    source venv/bin/activate  # Or venv\Scripts\activate on Windows
    ```
4.  **Run the Streamlit Application:**
    ```bash
    streamlit run streamlit_main_app.py
    ```
    The application should open in your web browser.

5.  **Using the Application:**
    * **Data Extract & Store Tab:** Click the "Fetch All OSDR Studies" button to begin scraping. Monitor the progress in the UI and terminal.
    * **Study Explorer (MongoDB) Tab:** Use the filter inputs (Organism, Factor, Study ID) to search and explore the studies stored in MongoDB. Click on a study to expand its details.
    * **Knowledge Graph (Neo4j) Tab:** (Placeholder) Will display graph visualizations once implemented.

## 📂 Project Structure (Simplified)
MONGO_DB_NASA_OSDR/
├── scraper/
│   ├── init.py
│   ├── formatter.py        # Main Selenium web scraping logic
│   ├── utils.py            # Utility functions (save_to_json, save_to_mongo)
│   ├── get_osds.py         # (User-defined placeholder for OSD list logic)
│   └── save_osd_list.py    # (User-defined placeholder)
├── data/
│   └── osdr_studies.json   # Output of the scraper
├── streamlit_main_app.py   # Main Streamlit application file
├── neo4j_visualizer.py     # (Planned: for Neo4j functions)
├── save_all_metadata.py    # (User-defined placeholder)
├── .env                    # Local environment variables (MONGO_URI, etc. - NOT COMMITTED)
├── .gitignore              # Specifies intentionally untracked files (e.g., .env, pycache)
└── README.md               # This file
└── requirements.txt        # Python dependencies






## ⏭️ Next Steps / Future Work

* **Refine "Highlights" Parsing:** Ensure consistent extraction if HTML structure varies.
* **Robust "Next Page" Button Detection:** Further verify and solidify the selector and disabled state check for the paginator's "Next Page" button.
* **"Invalid Session ID" Error:** Monitor and troubleshoot if it reappears during very long scraping sessions.
* **Full Neo4j Integration:**
    * Design and implement the graph data model.
    * Develop scripts to ingest data from MongoDB/JSON into Neo4j.
    * Implement Cypher queries for fetching graph data.
    * Visualize the graphs in the Streamlit application.
* **Enhanced UI/UX:** Add more advanced filtering, sorting, and data visualization options in the Streamlit app.
* **Error Handling & Logging:** Implement more comprehensive error handling and logging throughout the application.
* **Deployment:** Explore options for deploying the Streamlit application (e.g., Streamlit Community Cloud).

## 📄 License

(MIT License)

---
This project was developed by Gaston D./GASTONDANA627