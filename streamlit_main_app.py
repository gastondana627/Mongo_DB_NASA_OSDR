import streamlit as st
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["nasa_osdr"]
collection = db["studies"]

st.title("🚀 NASA OSDR Study Explorer")

# Search and filter UI
organism_filter = st.text_input("🔬 Filter by Organism (e.g., Mus musculus)")
factor_filter = st.text_input("🧪 Filter by Factor (e.g., Ionizing Radiation)")

# Query MongoDB
query = {}
if organism_filter:
    query["organisms"] = {"$regex": organism_filter, "$options": "i"}
if factor_filter:
    query["factors"] = {"$regex": factor_filter, "$options": "i"}

results = list(collection.find(query))

st.subheader(f"🧾 {len(results)} Studies Found")

for study in results:
    st.markdown(f"### {study.get('title', 'No Title')}")
    st.write(f"🧬 Organisms: {', '.join(study.get('organisms', []))}")
    st.write(f"⚡ Factors: {', '.join(study.get('factors', []))}")
    st.write(f"📅 Release Date: {study.get('release_date', 'N/A')}")
    st.write(f"🧪 Assay Types: {', '.join(study.get('assay_types', []))}")
    st.write(f"📖 Description: {study.get('description', '')}")
    st.markdown("---")