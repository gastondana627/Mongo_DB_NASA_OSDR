# neo4j_visualizer.py (Final Version with Deprecation Fix)

import os
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
from dotenv import load_dotenv
from pyvis.network import Network
import html

load_dotenv()

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")

def _build_graph_from_records(records):
    net = Network(height="720px", width="100%", notebook=True, cdn_resources='in_line', bgcolor="#222222", font_color="white")
    net.show_buttons(filter_=['physics'])
    color_map = {"Study": "#4287f5", "Organism": "#32a852", "Factor": "#d4a017", "Assay": "#ad343e"}
    added_nodes = set()
    for record in records:
        for key, value in record.items():
            if isinstance(value, dict):
                node_id = value.get('study_id') or value.get('name')
                if not node_id or node_id in added_nodes: continue
                label_key = f"{key}_labels"
                labels = record.get(label_key, value.get('labels', []))
                label = labels[0] if labels else "Unknown"
                title = value.get('title') or node_id
                size = 25 if label == "Study" else 15
                net.add_node(node_id, label=node_id, title=title, color=color_map.get(label, "#ffffff"), size=size)
                added_nodes.add(node_id)
        if 'start' in record and 'organism' in record and 'similar' in record:
            net.add_edge(record['start']['study_id'], record['organism']['name'])
            net.add_edge(record['similar']['study_id'], record['organism']['name'])
        elif 'study_props' in record and 'neighbor_props' in record:
            net.add_edge(record['study_props']['study_id'], record['neighbor_props']['name'])
        elif 'neighbor' in record and 'second_level' in record:
             net.add_edge(record['start']['study_id'], record['neighbor']['name'])
             net.add_edge(record['neighbor']['name'], record['second_level'].get('name') or record['second_level'].get('study_id'))
    return net.generate_html()

def run_graph_query(query: str, params: dict = None):
    driver = None
    try:
        driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
        driver.verify_connectivity()
        with driver.session() as session:
            results = session.run(query, parameters=params)
            return results.data()
    except ServiceUnavailable:
        return [{"error": "Connection Error: Could not connect to the Neo4j database."}]
    except Exception as e:
        return [{"error": f"An unexpected error occurred: {e}"}]
    finally:
        if driver is not None: driver.close()

def build_and_display_study_graph(study_id: str):
    query = """
    MATCH (study:Study {study_id: $study_id})-[r]-(neighbor)
    RETURN properties(study) as study_props, labels(neighbor) as neighbor_labels, properties(neighbor) as neighbor_props
    """
    records = run_graph_query(query, {'study_id': study_id})
    if not records: return f"<h3>No graph data found for study ID: {study_id}.</h3><p>Please ensure the full dataset has been ingested.</p>"
    if "error" in records[0]: return f"<h3>{records[0]['error']}</h3>"
    return _build_graph_from_records(records)

def find_similar_studies_by_organism(study_id: str):
    query = """
    MATCH (start:Study {study_id: $study_id})-[:HAS_ORGANISM]->(organism:Organism)<-[:HAS_ORGANISM]-(similar:Study)
    WHERE start <> similar
    RETURN properties(start) as start, properties(organism) as organism, properties(similar) as similar
    LIMIT 10
    """
    records = run_graph_query(query, {'study_id': study_id})
    if not records: return "<h3>No other studies found sharing the same organism. Try another starting study.</h3>"
    if "error" in records[0]: return f"<h3>{records[0]['error']}</h3>"
    return _build_graph_from_records(records)

def expand_second_level_connections(study_id: str):
    # THIS QUERY IS NOW FIXED WITH elementId()
    query = """
    MATCH (start:Study {study_id: $study_id})-[r1]-(neighbor)-[r2]-(second_level)
    WHERE elementId(start) < elementId(second_level) AND NOT (start)--(second_level)
    RETURN properties(start) as start, 
           properties(neighbor) as neighbor, labels(neighbor) as neighbor_labels,
           properties(second_level) as second_level, labels(second_level) as second_level_labels
    LIMIT 25
    """
    records = run_graph_query(query, {'study_id': study_id})
    if not records: return "<h3>No second-level connections found.</h3>"
    if "error" in records[0]: return f"<h3>{records[0]['error']}</h3>"
    return _build_graph_from_records(records)

