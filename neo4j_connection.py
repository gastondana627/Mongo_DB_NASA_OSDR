# neo4j_connection.py
import os
import streamlit as st
from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_ENV_TYPE

class Neo4jConnection:
    def __init__(self):
        # Use centralized configuration
        self.uri = NEO4J_URI
        self.user = NEO4J_USER
        self.password = NEO4J_PASSWORD
        self.environment = NEO4J_ENV_TYPE
        self.driver = None
    
    def connect(self):
        """Establish connection"""
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
            return True
        except Exception as e:
            print(f"❌ Connection failed: {str(e)}")
            return False
    
    def test_connection(self):
        """Test if connection works"""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 'Connected!' as message")
                msg = result.single()[0]
                return True, msg
        except Exception as e:
            return False, str(e)
    
    def close(self):
        """Close connection"""
        if self.driver:
            self.driver.close()

# Global instance
neo4j_conn = Neo4jConnection()
