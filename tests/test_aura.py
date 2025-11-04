import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()
uri = os.getenv("NEO4J_URI")
user = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(uri, auth=(user, password))  # No legacy config

try:
    driver.verify_connectivity()
    with driver.session() as session:
        result = session.run("RETURN 'Aura test successful'")
        print(result.single()["'Aura test successful'"])
    print("Full connection and query OK")
except Exception as e:
    print(f"Error: {e}")
finally:
    driver.close()
