# neo4j_connection.py
import os
import streamlit as st
from neo4j import GraphDatabase

class Neo4jConnection:
    def __init__(self):
        env = self._get_env_var("NEO4J_ENV", "local")
        
        if env == "local":
            self.uri = self._get_env_var("NEO4J_LOCAL_URI")
            self.user = self._get_env_var("NEO4J_LOCAL_USER")
            self.password = self._get_env_var("NEO4J_LOCAL_PASSWORD")
            self.environment = "LOCAL (Desktop)"
        else:
            self.uri = self._get_env_var("NEO4J_CLOUD_URI")
            self.user = self._get_env_var("NEO4J_CLOUD_USER")
            self.password = self._get_env_var("NEO4J_CLOUD_PASSWORD")
            self.environment = "CLOUD (Aura)"
        
        self.driver = None
    
    def _get_env_var(self, key, default=None):
        """Get from Streamlit secrets or OS env"""
        try:
            if hasattr(st, 'secrets') and key in st.secrets:
                return st.secrets[key]
        except:
            pass
        return os.getenv(key, default)
    
    def connect(self):
        """Establish connection"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                encrypted=True if "neo4j+s" in self.uri else False
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
