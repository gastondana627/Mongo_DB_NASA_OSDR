# streamlit_main_app.py

import streamlit as st
import os
import traceback
from dotenv import load_dotenv
from pymongo import MongoClient

# === Import Custom Functions ===
from scraper.formatter import extract_study_data
from scraper.utils import save_to_json, save_to_mongo
from save_all_metadata import save_all_metadata
from scraper.get_osds import get_all_osds
from scraper.save_osd_list import save_osd_list

# === Optional: Neo4j Integration ===
try:
    from neo4j_visualizer import get_graph_data, display_graph
    neo4j_enabled = True
except ImportError:
    neo4j_enabled = False

# === Streamlit Page Config ===
st.set_page_config(page_title="NASA OSDR Explorer", layout="wide")
st.write("✅ set_page_config successful")

# === Load Environment Variables ===
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    st.error("❌ MONGO_URI is not set. Please check your .env file.")
    st.stop()

# === MongoDB Setup ===
client = MongoClient(MONGO_URI)
db = client["nasa_osdr"]
collection = db["studies"]

# === Sidebar Action for Manual Data Pull ===
st.sidebar.header("Admin Tools")
if st.sidebar.button("🔄 Fetch & Save OSD Metadata"):
    with st.spinner("Fetching OSDs and saving metadata..."):
        try:
            osds = get_all_osds()
            save_osd_list(osds)
            save_all_metadata(osds)
            st.success(f"Fetched and saved metadata for {len(osds)} OSDs!")
        except Exception as e:
            st.error("❌ Failed to fetch/save metadata.")
            st.exception(e)

# === Sidebar Navigation ===
with st.sidebar:
    st.header("Navigation")
    st.page_link("streamlit_main_app.py", label="🏠 Home", icon="🏠")

# === Main App Title ===
st.title("🧠 NASA OSDR | Knowledge Graph + Data Extractor")

# === Tabs ===
tab1, tab2, tab3 = st.tabs([
    "🧬 Data Extract",
    "🕸️ Knowledge Graph",
    "📚 Study Explorer (MongoDB)"
])

# === Tab 1: Data Extraction ===
with tab1:
    st.subheader("🧬 Extract Study Data from NASA OSDR")
    if st.button("🚀 Fetch and Save NASA OSDR Studies"):
        st.info("Fetching data from NASA OSDR web page using Selenium...")
        try:
            studies = extract_study_data()
            if studies:
                save_to_json(studies, "data/osdr_studies.json")
                save_to_mongo(studies)
                st.success(f"✅ Saved {len(studies)} studies to JSON and MongoDB")
            else:
                st.warning("⚠️ No studies were found.")
        except Exception as e:
            st.error(f"❌ Error: {e}")
            st.text(traceback.format_exc())

# === Tab 2: Neo4j Graph Visualization ===
with tab2:
    st.subheader("🕸️ Visualize Neo4j Knowledge Graph")
    if not neo4j_enabled:
        st.error("❌ Neo4j functionality is currently unavailable.")
    else:
        if st.button("📊 Visualize Neo4j Relationships"):
            try:
                results = get_graph_data()
                display_graph(results)
            except Exception as e:
                st.error(f"❌ Error: {e}")
                st.text(traceback.format_exc())

# === Tab 3: MongoDB Study Explorer ===
with tab3:
    st.subheader("📚 Explore NASA OSDR Studies from MongoDB")

    organism_filter = st.text_input("🔬 Filter by Organism (e.g., Mus musculus)")
    factor_filter = st.text_input("🧪 Filter by Factor (e.g., Ionizing Radiation)")

    query = {}
    if organism_filter:
        query["organisms"] = {"$regex": organism_filter, "$options": "i"}
    if factor_filter:
        query["factors"] = {"$regex": factor_filter, "$options": "i"}

    try:
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
    except Exception as e:
        st.error(f"❌ MongoDB query failed: {e}")
        st.text(traceback.format_exc())

# === Optional CLI Functionality ===
def run_pipeline():
    try:
        studies = extract_study_data()
        save_to_json(studies, "data/osdr_studies.json")
        save_to_mongo(studies)
        print(f"✅ Extracted {len(studies)} studies and saved to JSON and MongoDB")
    except Exception as e:
        print(f"❌ Error in CLI pipeline: {e}")
        traceback.print_exc()