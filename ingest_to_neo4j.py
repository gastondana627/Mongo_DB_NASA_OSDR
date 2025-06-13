# ingest_to_neo4j.py (v3 - Final Corrected Version)

import os
import json
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
from dotenv import load_dotenv

# --- Configuration ---
# Point directly to your sample file in the root directory
JSON_FILE_PATH = "osdr_sample.json"

# Load environment variables from .env file
load_dotenv()

class Neo4jIngestor:
    def __init__(self):
        # Get credentials from .env file
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER")
        password = os.getenv("NEO4J_PASSWORD")
        if not all([uri, user, password]):
            raise ValueError("Neo4j credentials not found in .env file. Please check your setup.")
        
        try:
            # Establish connection driver
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            # Actively verify the connection is alive
            self.driver.verify_connectivity()
            print("Successfully connected to Neo4j.")
        except ServiceUnavailable as e:
            # Provide a much better error message if the database is offline
            print(f"Connection Error: Unable to connect to Neo4j at {uri}.")
            print("Please ensure your Neo4j Desktop database is running and 'Active'.")
            raise e

    def close(self):
        if self.driver:
            self.driver.close()
            print("Neo4j connection closed.")

    def clear_database(self):
        """Clears all nodes and relationships. Useful for clean re-runs."""
        with self.driver.session() as session:
            print("Clearing existing database...")
            session.run("MATCH (n) DETACH DELETE n")
            print("Database cleared.")

    def ingest_data(self):
        """Main function to read the sample JSON and ingest it into Neo4j."""
        if not os.path.exists(JSON_FILE_PATH):
            print(f"Error: JSON file not found at '{JSON_FILE_PATH}'")
            return

        with open(JSON_FILE_PATH, 'r') as f:
            # --- THIS IS THE CORRECTED LINE ---
            # The osdr_sample.json file already contains a list, so we load it directly.
            study_data = json.load(f)

        with self.driver.session() as session:
            total_studies = len(study_data)
            print(f"Found {total_studies} study to ingest.")
            for i, study in enumerate(study_data):
                # Now 'study' is correctly a dictionary, so study.get() will work
                print(f"Ingesting study {i+1}/{total_studies}: {study.get('study_id')}")
                session.execute_write(self._create_study_graph_tx, study)

    @staticmethod
    def _create_study_graph_tx(tx, study):
        """
        This is the core Cypher query logic executed within a transaction.
        MERGE is used to prevent creating duplicate nodes on re-runs.
        """
        query = """
        MERGE (s:Study {study_id: $study_id})
        ON CREATE SET
            s.title = $title,
            s.description = $description,
            s.release_date = $release_date
        WITH s
        UNWIND $organisms AS organism_name
        MERGE (o:Organism {name: organism_name})
        MERGE (s)-[:HAS_ORGANISM]->(o)
        WITH s
        UNWIND $factors AS factor_name
        MERGE (f:Factor {name: factor_name})
        MERGE (s)-[:INVESTIGATES_FACTOR]->(f)
        WITH s
        UNWIND $assay_types AS assay_name
        MERGE (a:Assay {name: assay_name})
        MERGE (s)-[:USES_ASSAY]->(a)
        """
        tx.run(query,
            study_id=study.get('study_id'),
            title=study.get('title'),
            description=study.get('description'),
            release_date=study.get('release_date'),
            organisms=study.get('organisms', []),
            factors=study.get('factors', []),
            assay_types=study.get('assay_types', [])
        )

if __name__ == "__main__":
    ingestor = None  # Initialize ingestor to None to ensure 'finally' block works
    try:
        ingestor = Neo4jIngestor()
        ingestor.clear_database()
        ingestor.ingest_data()
        print("\nData ingestion from sample file complete!")
    except Exception as e:
        # This will now only catch errors that happen *after* a successful connection
        print(f"An operation failed: {e}")
    finally:
        if ingestor:
            ingestor.close()