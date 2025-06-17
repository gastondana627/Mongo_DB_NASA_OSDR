# neo4j_visualizer.py (Definitive Upgraded & Corrected Version for Streamlit Cloud)

import streamlit as st
from neo4j import GraphDatabase
from pyvis.network import Network

# The old os.getenv and load_dotenv lines are removed as we will get secrets from st.secrets

def _build_graph_from_records(records):
    """A generic helper to build a Pyvis graph from Neo4j query results."""
    net = Network(height="720px", width="100%", notebook=True, cdn_resources='in_line', bgcolor="#222222", font_color="white")
    net.show_buttons(filter_=['physics'])
    color_map = {"Study": "#4287f5", "Organism": "#32a852", "Factor": "#d4a017", "Assay": "#ad343e", "Unknown": "#999999"}
    added_nodes = set()
    study_ids_in_graph = set()

    for record in records:
        # Process all nodes in the record first
        for key, value in record.items():
            if isinstance(value, dict): # Check if the item is a node's property dictionary
                node_id = value.get('study_id') or value.get('name')
                if not node_id or node_id in added_nodes:
                    continue
                
                label_key = f"{key}_labels"
                node_labels = record.get(label_key, value.get('labels', []))
                label = node_labels[0] if node_labels else "Unknown"

                if label == "Study":
                    study_ids_in_graph.add(node_id)
                
                title = value.get('title') or node_id
                size = 25 if label == "Study" else 15
                net.add_node(node_id, label=node_id, title=title, color=color_map.get(label, "#ffffff"), size=size)
                added_nodes.add(node_id)
        
        # Process edges based on common query patterns
        if 'start' in record and 'organism' in record and 'similar' in record:
            net.add_edge(record['start']['study_id'], record['organism']['name'], color="#32a852")
            net.add_edge(record['similar']['study_id'], record['organism']['name'], color="#32a852")
        elif 'study_props' in record and 'neighbor_props' in record:
            net.add_edge(record['study_props']['study_id'], record['neighbor_props']['name'])
        elif 'neighbor' in record and 'second_level' in record and 'start' in record:
             net.add_edge(record['start']['study_id'], record['neighbor']['name'])
             net.add_edge(record['neighbor']['name'], record['second_level'].get('name') or record['second_level'].get('study_id'))

    return net.generate_html(), list(study_ids_in_graph)

def run_graph_query(query: str, params: dict = None):
    """
    A generic function to securely run any query and return its data.
    This version reads credentials directly from Streamlit's secrets manager.
    """
    driver = None
    try:
        # Get credentials from Streamlit secrets instead of .env file
        uri = st.secrets["NEO4J_URI"]
        user = st.secrets["NEO4J_USER"]
        password = st.secrets["NEO4J_PASSWORD"]

        # Establish connection with the retrieved secrets
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        with driver.session() as session:
            return session.run(query, parameters=params).data()
    except Exception as e:
        # Return a more specific error message if secrets are missing
        if "AttributeError" in str(e) or "KeyError" in str(e):
             return [{"error": "Neo4j credentials not found in Streamlit Secrets. Please check your deployment settings."}]
        return [{"error": f"An unexpected error occurred connecting to Neo4j: {e}"}]
    finally:
        if driver: driver.close()

def build_and_display_study_graph(study_id: str):
    """Builds the initial, simple graph for a single study."""
    query = "MATCH (study:Study {study_id: $study_id})-[r]-(neighbor) RETURN properties(study) as study_props, labels(neighbor) as neighbor_labels, properties(neighbor) as neighbor_props"
    records = run_graph_query(query, {'study_id': study_id})
    if not records or ("error" in records[0] and records[0].get("error")):
        error_message = records[0].get("error") if records else f"No graph data found for study {study_id}."
        return (f"<h3>{error_message}</h3>", [])
    return _build_graph_from_records(records)

def find_similar_studies_by_organism(study_id: str):
    """Finds other studies that share the same organism(s)."""
    query = "MATCH (start:Study {study_id: $study_id})-[:HAS_ORGANISM]->(o:Organism)<-[:HAS_ORGANISM]-(similar:Study) WHERE start <> similar RETURN properties(start) as start, properties(o) as organism, properties(similar) as similar, labels(o) as organism_labels LIMIT 1"
    records = run_graph_query(query, {'study_id': study_id})
    if not records or ("error" in records[0] and records[0].get("error")):
        error_message = records[0].get("error") if records else "No other studies found sharing the same organism."
        # Still return the base graph if no similar studies are found
        base_html, _ = build_and_display_study_graph(study_id)
        return (f"{base_html}<h3>{error_message}</h3>", [study_id])
    return _build_graph_from_records(records)

def expand_second_level_connections(study_id: str):
    """Expands the graph to show connections of connections. This is now fully implemented."""
    query = """
    MATCH (start:Study {study_id: $study_id})-[r1]-(neighbor)-[r2]-(second_level)
    WHERE elementId(start) <> elementId(second_level) AND NOT (start)--(second_level)
    RETURN properties(start) as start, 
           properties(neighbor) as neighbor, labels(neighbor) as neighbor_labels,
           properties(second_level) as second_level, labels(second_level) as second_level_labels
    LIMIT 20
    """
    records = run_graph_query(query, {'study_id': study_id})
    if not records or ("error" in records[0] and records[0].get("error")):
        error_message = records[0].get("error") if records else "No second-level connections found."
        return (f"<h3>{error_message}</h3>", [study_id])
    return _build_graph_from_records(records)







