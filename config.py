import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Better environment detection
IS_LOCAL = not os.path.exists("/mount/src")  # Streamlit Cloud = /mount/src exists
# OR detect via Streamlit's internal
try:
    IS_LOCAL = not st.get_option("logger.level")  # Will error in local
except:
    IS_LOCAL = True

# MongoDB
MONGO_URI = os.getenv("MONGO_URI")

# Neo4j
if IS_LOCAL:
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
else:
    # Production: st.secrets
    try:
        NEO4J_URI = st.secrets["NEO4J_URI"]
        NEO4J_USER = st.secrets.get("NEO4J_USER", "neo4j")
        NEO4J_PASSWORD = st.secrets["NEO4J_PASSWORD"]
    except:
        NEO4J_URI = None
        NEO4J_USER = None
        NEO4J_PASSWORD = None

print(f"🔧 Running in {'LOCAL' if IS_LOCAL else 'PRODUCTION'} mode")
print(f"[OSDR] Neo4j: {NEO4J_URI}")
