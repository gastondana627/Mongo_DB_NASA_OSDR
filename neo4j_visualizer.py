# neo4j_visualizer.py
from neo4j import GraphDatabase
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "your_password"))

def get_graph_data():
    query = """
    MATCH (n)-[r]->(m)
    RETURN n.name AS source, type(r) AS relation, m.name AS target
    LIMIT 50
    """
    with driver.session() as session:
        results = session.run(query)
        return [record.data() for record in results]

def display_graph(results):
    G = nx.DiGraph()
    for record in results:
        G.add_edge(record["source"], record["target"], label=record["relation"])
    
    net = Network(height="600px", width="100%", directed=True)
    net.from_nx(G)
    net.show("graph.html")
    components.html(open("graph.html", "r", encoding="utf-8").read(), height=620)