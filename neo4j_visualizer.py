# neo4j_visualizer.py (Final Submission Version)

import streamlit as st
from neo4j import GraphDatabase
from pyvis.network import Network

# In neo4j_visualizer.py

# In neo4j_visualizer.py

def _build_graph_from_records(records):
    """Builds a Pyvis graph from the Neo4j query results."""
    net = Network(height="750px", width="100%", notebook=True, cdn_resources='in_line', bgcolor="#1E1E1E", font_color="#FFFFFF", directed=True)
    net.set_options("""
    var options = {
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -40000,
          "centralGravity": 0.15,
          "springLength": 170
        },
        "minVelocity": 0.75
      }
    }
    """)

    added_nodes = set()

    for record in records:
        start_node_props = record.get('start')
        neighbor_node_props = record.get('neighbor')

        # Add the main study node
        if start_node_props and start_node_props.get('study_id') not in added_nodes:
            node_id = start_node_props['study_id']
            net.add_node(node_id, label=node_id, title=start_node_props.get('title', node_id), color="#0083FF", size=30, group="Study")
            added_nodes.add(node_id)

        # Add the neighboring node
        if neighbor_node_props:
            neighbor_labels = record.get('neighbor_labels', ['Unknown'])
            node_group = neighbor_labels[0] if neighbor_labels else "Unknown"
            node_id = neighbor_node_props.get('name')

            if node_id and node_id not in added_nodes:
                color_map = {"Organism": "#FF6C00", "Factor": "#C600FF", "Assay": "#00D95A"}
                net.add_node(node_id, label=node_id, title=node_id, group=node_group, color=color_map.get(node_group, "#CCCCCC"), size=15)
                added_nodes.add(node_id)

            # Add the edge connecting the study to its neighbor
            if start_node_props and start_node_props.get('study_id') and node_id:
                net.add_edge(start_node_props['study_id'], node_id)

    return net.generate_html(), list(added_nodes) # Return list of nodes in graph



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

