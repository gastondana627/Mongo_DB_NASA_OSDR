import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Auto-detect environment
IS_LOCAL = os.getenv("STREAMLIT_RUNTIME_ENV", "").lower() != "cloud"

# MongoDB (same for both)
MONGO_URI = os.getenv("MONGO_URI")

# Neo4j - local vs production
if IS_LOCAL:
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
else:
    # Production: read from Streamlit Secrets
    NEO4J_URI = st.secrets.get("NEO4J_URI")
    NEO4J_USER = st.secrets.get("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = st.secrets.get("NEO4J_PASSWORD")

print(f"🔧 Running in {'LOCAL' if IS_LOCAL else 'PRODUCTION'} mode")
print(f"[OSDR] Neo4j: {NEO4J_URI}")
