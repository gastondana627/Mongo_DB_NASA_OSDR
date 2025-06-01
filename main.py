# main.py

import streamlit as st

# === Core OSDR Scraper Imports ===
from scraper.reader import get_osdr_studies_html
from scraper.formatter import extract_study_data
from scraper.utils import save_to_json

# === Neo4j Visualization ===
from neo4j_visualizer import get_graph_data, display_graph

# === Streamlit UI Config ===
st.set_page_config(page_title="NASA OSDR Explorer", layout="wide")
st.title("🧠 NASA OSDR | Knowledge Graph + Data Extractor")

# === Sidebar Navigation ===
with st.sidebar:
    st.header("Navigation")
    st.page_link("main.py", label="🏠 Home")
    # Future additions: Docs, MongoDB, About, etc.

# === Main Content Tabs ===
tab1, tab2 = st.tabs(["🧬 Data Extract", "🕸️ Knowledge Graph"])

with tab1:
    st.subheader("🧬 Extract Study Data from NASA OSDR")
    if st.button("🚀 Run NASA OSDR Data Extraction Pipeline"):
        html_content = get_osdr_studies_html()
        structured_data = extract_study_data(html_content)
        save_to_json(structured_data, "osdr_sample.json")
        st.success(f"✅ Extracted {len(structured_data)} studies and saved to osdr_sample.json")

with tab2:
    st.subheader("🕸️ Visualize Neo4j Knowledge Graph")
    if st.button("📊 Visualize Neo4j Relationships"):
        results = get_graph_data()
        display_graph(results)

# === CLI Execution Only ===
def run_pipeline():
    html_content = get_osdr_studies_html()
    structured_data = extract_study_data(html_content)
    save_to_json(structured_data, "osdr_sample.json")
    print(f"Extracted {len(structured_data)} studies and saved to osdr_sample.json")

if __name__ == "__main__":
    run_pipeline()