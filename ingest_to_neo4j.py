# ingest_to_neo4j.py (Definitive Version)
import os
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv

JSON_FILE_PATH = "data/osdr_studies.json"
load_dotenv()

class Neo4jIngestor:
    def __init__(self):
        uri = os.getenv("NEO4J_URI"); user = os.getenv("NEO4J_USER"); password = os.getenv("NEO4J_PASSWORD")
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.driver.verify_connectivity()
            print("Successfully connected to Neo4j.")
        except Exception as e:
            print(f"Connection Error. Please ensure Neo4j is running and credentials in .env are correct. Error: {e}")
            raise

    def close(self):
        if self.driver: self.driver.close(); print("Neo4j connection closed.")

    def clear_database(self):
        with self.driver.session() as session:
            print("Clearing existing database..."); session.run("MATCH (n) DETACH DELETE n"); print("Database cleared.")

    def ingest_data(self):
        if not os.path.exists(JSON_FILE_PATH):
            print(f"Error: '{JSON_FILE_PATH}' not found. Please run the scraper in the main app first."); return
        with open(JSON_FILE_PATH, 'r') as f: study_data = json.load(f)
        with self.driver.session() as session:
            total = len(study_data); print(f"Found {total} studies to ingest.")
            for i, study in enumerate(study_data):
                print(f"Ingesting study {i+1}/{total}: {study.get('study_id')}")
                # The **study syntax unpacks the dictionary to match the query parameters
                session.execute_write(self._create_study_graph_tx, **study)

    @staticmethod
    def _create_study_graph_tx(tx, **study):
        query = """
        MERGE (s:Study {study_id: $study_id})
        ON CREATE SET s.title = $title, s.description = $description, s.release_date = $release_date
        WITH s
        UNWIND $organisms AS organism_name MERGE (o:Organism {name: organism_name}) MERGE (s)-[:HAS_ORGANISM]->(o)
        WITH s
        UNWIND $factors AS factor_name MERGE (f:Factor {name: factor_name}) MERGE (s)-[:INVESTIGATES_FACTOR]->(f)
        WITH s
        UNWIND $assay_types AS assay_name MERGE (a:Assay {name: assay_name}) MERGE (s)-[:USES_ASSAY]->(a)
        """
        tx.run(query, **study)

if __name__ == "__main__":
    ingestor = None
    try:
        ingestor = Neo4jIngestor()
        ingestor.clear_database()
        ingestor.ingest_data()
        print("\nData ingestion complete!")
    except Exception:
        print(f"An operation failed.")
    finally:
        if ingestor: ingestor.close()