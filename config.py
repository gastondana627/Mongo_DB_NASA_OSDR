import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Detect environment: True if local (no /mount/src), False if cloud
IS_LOCAL = not os.path.exists("/mount/src")

if IS_LOCAL:
    # Local: Use .env or Docker defaults
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")  # Your Docker password
    # Set local env var for backward compatibility
    os.environ["NEO4J_LOCAL_URI"] = NEO4J_URI
else:
    # Production: Force secrets (no local fallback)
    try:
        NEO4J_URI = st.secrets["NEO4J_URI"]
        NEO4J_USER = st.secrets["NEO4J_USER"]
        NEO4J_PASSWORD = st.secrets["NEO4J_PASSWORD"]
        # Override any local env
        os.environ["NEO4J_LOCAL_URI"] = NEO4J_URI
        print(f"[OSDR] Production Neo4j URI forced: {NEO4J_URI}")  # Debug log
    except KeyError as e:
        st.error(f"Missing secret: {e}")
        NEO4J_URI = None
        NEO4J_USER = None
        NEO4J_PASSWORD = None

# MongoDB (unchanged, works everywhere)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/osdr")
if not IS_LOCAL:
    MONGO_URI = st.secrets.get("MONGO_URI", MONGO_URI)

# OpenAI: Ensure no proxies passed
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") if IS_LOCAL else st.secrets.get("OPENAI_API_KEY")
