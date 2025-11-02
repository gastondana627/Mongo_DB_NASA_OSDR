import os
from dotenv import load_dotenv

load_dotenv()

# Auto-detect environment
IS_LOCAL = os.getenv("STREAMLIT_RUNTIME_ENV", "").lower() != "cloud"

# MongoDB (same for both)
MONGO_URI = os.getenv("MONGO_URI")

# Neo4j - local vs production
if IS_LOCAL:
    NEO4J_URI = os.getenv("NEO4J_LOCAL_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_LOCAL_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_LOCAL_PASSWORD", "")
else:
    NEO4J_URI = os.getenv("NEO4J_AURA_URI")
    NEO4J_USER = os.getenv("NEO4J_AURA_USER")
    NEO4J_PASSWORD = os.getenv("NEO4J_AURA_PASSWORD")

print(f"🔧 Running in {'LOCAL' if IS_LOCAL else 'PRODUCTION'} mode")
