import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =============================================================================
# Environment Detection
# =============================================================================
# Detect if running locally or on Streamlit Cloud
IS_LOCAL = not os.path.exists("/mount/src")

# =============================================================================
# Configuration Loading
# =============================================================================

def get_config_value(key, default=None, secrets_key=None):
    """
    Get configuration value from environment or Streamlit secrets.
    
    Args:
        key: Environment variable key
        default: Default value if not found
        secrets_key: Alternative key for Streamlit secrets (if different from key)
    
    Returns:
        Configuration value
    """
    if IS_LOCAL:
        return os.getenv(key, default)
    else:
        # Use secrets_key if provided, otherwise use key
        secret_key = secrets_key or key
        try:
            if "." in secret_key:
                # Handle nested secrets like "neo4j.URI"
                parts = secret_key.split(".")
                value = st.secrets
                for part in parts:
                    value = value[part]
                return value
            else:
                return st.secrets.get(secret_key, default)
        except (KeyError, AttributeError):
            return default

# =============================================================================
# Database Configuration
# =============================================================================

# MongoDB Configuration
MONGO_URI = get_config_value("MONGO_URI", "mongodb://localhost:27017/osdr")

# Neo4j Configuration - Auto-detect environment and fallback gracefully
def get_neo4j_config():
    """Get Neo4j configuration with automatic environment detection and fallback."""
    
    # Check for manual environment override
    neo4j_env = get_config_value("NEO4J_ENV", "").lower()
    
    # If running on Streamlit Cloud, try secrets first (unless forced to local)
    if not IS_LOCAL and neo4j_env != "local":
        try:
            uri = get_config_value("NEO4J_URI", secrets_key="neo4j.URI")
            user = get_config_value("NEO4J_USER", secrets_key="neo4j.USER") 
            password = get_config_value("NEO4J_PASSWORD", secrets_key="neo4j.PASSWORD")
            
            if all([uri, user, password]):
                return uri, user, password, "Production (Streamlit Cloud)"
        except:
            pass
    
    # Try environment variables (from .env or system)
    uri = get_config_value("NEO4J_URI")
    user = get_config_value("NEO4J_USER") 
    password = get_config_value("NEO4J_PASSWORD")
    
    if all([uri, user, password]):
        # Determine environment type based on URI
        if "bolt://localhost" in uri or "127.0.0.1" in uri:
            env_type = "Local Development"
        elif "neo4j+s://" in uri:
            env_type = "Neo4j Aura (Cloud)"
        else:
            env_type = "Custom Neo4j"
        
        return uri, user, password, env_type
    
    # Fallback to local defaults
    return "bolt://localhost:7687", "neo4j", "Gas121212", "Local Default"

NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_ENV_TYPE = get_neo4j_config()

# =============================================================================
# API Keys
# =============================================================================

# OpenAI API Key
OPENAI_API_KEY = get_config_value("OPENAI_API_KEY")

# =============================================================================
# Google Cloud Configuration
# =============================================================================

# GCP Credentials
GOOGLE_APPLICATION_CREDENTIALS = get_config_value("GOOGLE_APPLICATION_CREDENTIALS", "gcp_credentials.json")
GCP_PROJECT_ID = get_config_value("GCP_PROJECT_ID", "nasa-osdr-mongo")
GCP_LOCATION = get_config_value("GCP_LOCATION", "us-central1")

# =============================================================================
# Debug Information
# =============================================================================

if __name__ == "__main__":
    print(f"Environment Detection: {'Local' if IS_LOCAL else 'Production'}")
    print(f"Neo4j Environment: {NEO4J_ENV_TYPE}")
    print(f"MongoDB URI: {MONGO_URI[:50]}..." if MONGO_URI else "MongoDB URI: Not set")
    print(f"Neo4j URI: {NEO4J_URI}")
    print(f"Neo4j User: {NEO4J_USER}")
    print(f"OpenAI API Key: {'Set' if OPENAI_API_KEY else 'Not set'}")
    print(f"GCP Project: {GCP_PROJECT_ID}")
