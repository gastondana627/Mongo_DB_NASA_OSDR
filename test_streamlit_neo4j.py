#!/usr/bin/env python3
"""
Test Neo4j connection as it would be used in Streamlit app.
"""

import sys
import os
from neo4j import GraphDatabase

# Test the same way as streamlit_main_app.py
try:
    from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
    
    class Neo4jConnection:
        def __init__(self):
            self.uri = NEO4J_URI
            self.user = NEO4J_USER
            self.password = NEO4J_PASSWORD
            self.driver = None
            self.connected = False
        
        def connect(self):
            try:
                # For neo4j+s:// URIs, encryption is implicit, don't pass encrypted parameter
                if "neo4j+s" in self.uri or "bolt+s" in self.uri:
                    self.driver = GraphDatabase.driver(
                        self.uri,
                        auth=(self.user, self.password)
                    )
                else:
                    self.driver = GraphDatabase.driver(
                        self.uri,
                        auth=(self.user, self.password),
                        encrypted=False
                    )
                with self.driver.session() as session:
                    session.run("RETURN 1")
                self.connected = True
                return True
            except Exception as e:
                print(f"⚠️ Neo4j offline: {str(e)[:50]}")
                self.connected = False
                return False
        
        def close(self):
            if self.driver:
                self.driver.close()
    
    # Try to connect
    neo4j_conn = Neo4jConnection()
    print(f"Neo4j URI: {neo4j_conn.uri}")
    neo4j_enabled = neo4j_conn.connect()
    
    if neo4j_enabled:
        print("✅ Neo4j connection successful - Streamlit app should work!")
        print(f"   Connected: {neo4j_conn.connected}")
        print(f"   Environment: Neo4j Aura (Cloud)")
    else:
        print("❌ Neo4j connection failed - Streamlit app will show offline")
    
    neo4j_conn.close()
    
except Exception as e:
    print(f"❌ Neo4j unavailable: {str(e)[:50]}")
    neo4j_enabled = False

print(f"\nneo4j_enabled = {neo4j_enabled}")