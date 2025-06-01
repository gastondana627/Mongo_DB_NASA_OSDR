# streamlit_main_app.py

import streamlit as st
from dotenv import load_dotenv
from pymongo import MongoClient
import os

# === Load Environment Variables ===
load_dotenv()

# === Core OSDR Scraper Imports ===
from scraper.reader import get_osdr_studies_html  # UPDATED: now using web scraper
from scraper.formatter import extract_study_data
from scraper.utils import save_to_json

# === Neo4j Visualization ===
from neo4j_visualizer import get_graph_data, display_graph

# === MongoDB Setup ===
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["nasa_osdr"]
collection = db["studies"]

# === Streamlit UI Config ===
st.set_page_config(page_title="NASA OSDR Explorer", layout="wide")
st.title("🧠 NASA OSDR | Knowledge Graph + Data Extractor")

# === Sidebar Navigation ===
with st.sidebar:
    st.header("Navigation")
    st.page_link("streamlit_main_app.py", label="🏠 Home")
    # Future: Add more navigation links here

# === Main Content Tabs ===
tab1, tab2, tab3 = st.tabs([
    "🧬 Data Extract",
    "🕸️ Knowledge Graph",
    "📚 Study Explorer (MongoDB)"
])

# === Tab 1: Data Extraction ===
with tab1:
    st.subheader("🧬 Extract Study Data from NASA OSDR")
    if st.button("🚀 Fetch and Save NASA OSDR Studies"):
        st.info("Fetching data from NASA OSDR web page...")
        try:
            html_content = get_osdr_studies_html()  # New HTML-based scraping
            studies = extract_study_data(html_content)
            save_to_json(studies, "data/osdr_studies.json")
            st.success(f"✅ Saved {len(studies)} studies to data/osdr_studies.json")
        except Exception as e:
            st.error(f"❌ Error: {e}")

# === Tab 2: Neo4j Graph Visualization ===
with tab2:
    st.subheader("🕸️ Visualize Neo4j Knowledge Graph")
    if st.button("📊 Visualize Neo4j Relationships"):
        results = get_graph_data()
        display_graph(results)

# === Tab 3: MongoDB Study Explorer ===
with tab3:
    st.subheader("📚 Explore NASA OSDR Studies from MongoDB")

    organism_filter = st.text_input("🔬 Filter by Organism (e.g., Mus musculus)")
    factor_filter = st.text_input("🧪 Filter by Factor (e.g., Ionizing Radiation)")

    # Build MongoDB query
    query = {}
    if organism_filter:
        query["organisms"] = {"$regex": organism_filter, "$options": "i"}
    if factor_filter:
        query["factors"] = {"$regex": factor_filter, "$options": "i"}

    results = list(collection.find(query))
    st.write(f"🧾 {len(results)} Studies Found")

    for study in results:
        st.markdown(f"### {study.get('title', 'No Title')}")
        st.write(f"🧬 Organisms: {', '.join(study.get('organisms', []))}")
        st.write(f"⚡ Factors: {', '.join(study.get('factors', []))}")
        st.write(f"📅 Release Date: {study.get('release_date', 'N/A')}")
        st.write(f"🧪 Assay Types: {', '.join(study.get('assay_types', []))}")
        st.write(f"📖 Description: {study.get('description', '')}")
        st.markdown("---")

# === CLI Execution Only ===
def run_pipeline():
    try:
        html_content = get_osdr_studies_html()
        studies = extract_study_data(html_content)
        save_to_json(studies, "data/osdr_studies.json")
        print(f"✅ Extracted {len(studies)} studies and saved to data/osdr_studies.json")
    except Exception as e:
        print(f"❌ Error in CLI pipeline: {e}")

# Optional CLI runner
# if __name__ == "__main__":
#     run_pipeline()