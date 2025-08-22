
# test_neo4j.py
from neo4j import GraphDatabase

# --- PASTE YOUR CREDENTIALS DIRECTLY HERE ---
NEO4J_URI="__"
NEO4J_USER="neo4j"
NEO4J_PASSWORD="__"

# ---------------------------------------------

print(f"Attempting to connect to: {uri}")
try:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    driver.verify_connectivity()
    print("✅ Success! Connection is valid.")
    driver.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
