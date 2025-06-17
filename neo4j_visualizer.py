# neo4j_visualizer.py (Final Submission Version)

import streamlit as st
from neo4j import GraphDatabase
from pyvis.network import Network

def _build_graph_from_records(records):
    """A generic helper to build a Pyvis graph from Neo4j query results."""
    net = Network(height="720px", width="100%", notebook=True, cdn_resources='in_line', bgcolor="#222222", font_color="white")
    net.show_buttons(filter_=['physics'])
    added_nodes, study_ids_in_graph = set(), set()
    for record in records:
        for key, value in record.items():
            if isinstance(value, dict):
                node_id = value.get('study_id') or value.get('name')
                if not node_id or node_id in added_nodes: continue
                label = (record.get(f"{key}_labels") or value.get('labels', ["Unknown"]))[0]
                if label == "Study": study_ids_in_graph.add(node_id)
                net.add_node(node_id, label=node_id, title=value.get('title', node_id), size=25 if label == "Study" else 15)
                added_nodes.add(node_id)
        # Add edge processing logic here based on your query structure
        if 'start' in record and 'neighbor' in record:
             net.add_edge(record['start']['study_id'], record['neighbor']['name'])
             
    return net.generate_html(), list(study_ids_in_graph)

def run_graph_query(query: str, params: dict = None):
    """
    Runs a query against the Neo4j database using credentials from st.secrets.
    """
    driver = None
    try:
        # Accessing secrets using the correct nested structure (e.g., st.secrets.neo4j.URI)
        uri = st.secrets.neo4j.URI
        user = st.secrets.neo4j.USER
        password = st.secrets.neo4j.PASSWORD
        
        driver = GraphDatabase.driver(
            uri, 
            auth=(user, password), 
            max_connection_lifetime=360, 
            connection_timeout=30
        )
        with driver.session() as session:
            return session.run(query, parameters=params).data()
    except Exception as e:
        return [{"error": f"Neo4j Connection Error: {e}"}]
    finally:
        if driver: driver.close()

def build_and_display_study_graph(study_id: str):
    """Builds the initial graph for a single study."""
    query = "MATCH (s:Study {study_id: $study_id})-[r]-(n) RETURN properties(s) as start, properties(n) as neighbor, labels(n) as neighbor_labels"
    records = run_graph_query(query, {'study_id': study_id})
    if not records or "error" in records[0]:
        return (f"<h3>Error: {records[0].get('error') if records else 'No data found.'}</h3>", [study_id])
    return _build_graph_from_records(records)

# Placeholder for other functions if they exist
def find_similar_studies_by_organism(study_id: str): 
    # This query and logic would need to be implemented fully
    return ("<h3>Function not fully implemented.</h3>", [study_id])

def expand_second_level_connections(study_id: str):
    # This query and logic would need to be implemented fully
    return ("<h3>Function not fully implemented.</h3>", [study_id])

