# test_aura_connection.py
from neo4j import GraphDatabase

URI = "neo4j+s://5be416cb.databases.neo4j.io"
AUTH = ("neo4j", "iyODr6mTbLqK5wpj2eKE2ZUbTQbz3-DnZ6kTLiNvZPM") # <--- REPLACE WITH YOUR REAL PASSWORD

print(f"--- Attempting to connect to: {URI} ---")
try:
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        print("✅ SUCCESS! The connection to Neo4j Aura is valid.")
except Exception as e:
    print(f"❌ FAILURE: The connection failed. Error: {e}")