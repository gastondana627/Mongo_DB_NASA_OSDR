# test_aura_connection.py
from neo4j import GraphDatabase

URI = "__"
AUTH = ("neo4j", "___") # <--- REPLACE WITH YOUR REAL PASSWORD

print(f"--- Attempting to connect to: {URI} ---")
try:
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        print("✅ SUCCESS! The connection to Neo4j Aura is valid.")
except Exception as e:
    print(f"❌ FAILURE: The connection failed. Error: {e}")
