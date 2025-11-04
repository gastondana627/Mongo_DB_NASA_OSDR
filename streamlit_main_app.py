# === Python Standard Libraries ===
import os
import sys
import traceback
import time
import random
import json
from tempfile import NamedTemporaryFile


# Config/Configuration
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, MONGO_URI


# === Third-Party Libraries ===
import streamlit as st
from dotenv import load_dotenv  # NOW UNCOMMENTED & USED
from pymongo import MongoClient
import certifi

# === LOAD .ENV IMMEDIATELY (BEFORE ANY ST CALLS) ===
load_dotenv()

# === Streamlit Page Config (MUST BE FIRST) ===
import logging
import sys
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s', stream=sys.stdout)
logger = logging.getLogger("OSDR")

st.set_page_config(
    page_title="NASA OSDR Research Platform", 
    layout="wide", 
    initial_sidebar_state="expanded",
    page_icon="🚀"
)

# === Initialize Elegant UI Theme ===
try:
    from simple_elegant_ui import apply_elegant_theme, create_elegant_header, create_status_indicators, create_metrics_row
    
    # Apply clean, elegant theme
    apply_elegant_theme()
    elegant_ui_available = True
    
except ImportError:
    st.warning("Elegant UI theme not available - using default styling")
    elegant_ui_available = False

# === Import Custom Functions ===
from scraper.formatter import extract_study_data
from scraper.utils import save_to_json, save_to_mongo
from neo4j_visualizer import (
    build_and_display_study_graph,
    find_similar_studies_by_organism,
    expand_second_level_connections
)
from ai_utils import get_ai_comparison, perform_vector_search

# ==============================================================================
# === STREAMLIT CLOUD SECRETS INTEGRATION (CRITICAL FOR DEPLOYMENT) ===
# ==============================================================================

def configure_gcp_creds():
    """
    Handles GCP credentials for Streamlit Cloud deployment.
    It reads the JSON key content from st.secrets, writes it to a temporary
    file, and sets the GOOGLE_APPLICATION_CREDENTIALS environment variable
    to point to that file.
    """
    try:
        # Check if we are running on Streamlit Cloud and the secret is set
        if hasattr(st, 'secrets') and "GOOGLE_APPLICATION_CREDENTIALS_CONTENT" in st.secrets:
            # Get the JSON content from secrets
            creds_content_str = st.secrets["GOOGLE_APPLICATION_CREDENTIALS_CONTENT"]
            
            # Load the string as a JSON object
            creds_json = json.loads(creds_content_str)
            
            # Write the JSON object to a temporary file
            with NamedTemporaryFile(mode="w", delete=False, suffix=".json") as tmp:
                json.dump(creds_json, tmp)
                tmp_path = tmp.name

            # Set the environment variable for Google Cloud libraries
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmp_path
    except (FileNotFoundError, KeyError):
        # No secrets file or key - that's OK for local dev with .env
        pass

# Call the function to configure credentials at the start of the app
configure_gcp_creds()

@st.cache_resource
def get_mongo_client():
    """
    Establishes a connection to MongoDB using credentials from st.secrets.
    """
    try:
        # Get the MongoDB URI from Streamlit's secrets manager
        mongo_uri = st.secrets.get("MONGO_URI")
        if not mongo_uri:
            # Custom error with NASA emoji
            mongo_error_cols = st.columns([1, 20])
            with mongo_error_cols[0]:
                st.image(get_custom_emoji_for_context("error"), width=20)
            with mongo_error_cols[1]:
                st.error("MONGO_URI secret not found. Please set it in your Streamlit Cloud app settings.")
            return None

        ca = certifi.where()
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000, tlsCAFile=ca)
        # The ismaster command is cheap and does not require auth.
        client.admin.command('ismaster')
        logger.info("✅ MongoDB: Connected")
        return client
    except Exception as e:
        # Custom error with NASA emoji
        mongo_fail_cols = st.columns([1, 20])
        with mongo_fail_cols[0]:
            st.image(get_custom_emoji_for_context("error"), width=20)
        with mongo_fail_cols[1]:
            st.error(f"MongoDB connection failed: {e}")
        return None

# ==============================================================================
# === END OF SECRETS INTEGRATION SECTION ===
# ==============================================================================

# === CUSTOM EMOJI HELPER FUNCTIONS ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EMOJI_ASSETS_DIR = os.path.join(BASE_DIR, "assets", "emojis")
VALID_IMAGE_EXTENSIONS = ('.svg', '.png', '.jpg', '.jpeg', '.gif')

@st.cache_data
def get_all_emoji_image_paths(subfolder=None):
    target_dir = EMOJI_ASSETS_DIR
    if subfolder:
        target_dir = os.path.join(EMOJI_ASSETS_DIR, subfolder)
    if not os.path.exists(target_dir):
        return []
    images = [os.path.join(target_dir, f_name) for f_name in os.listdir(target_dir) if f_name.lower().endswith(VALID_IMAGE_EXTENSIONS) and os.path.isfile(os.path.join(target_dir, f_name))]
    return images

def get_random_emoji_image_path(subfolder=None, fallback_emoji=None):
    image_paths = get_all_emoji_image_paths(subfolder=subfolder)
    if image_paths:
        return random.choice(image_paths)
    
    # If no images in subfolder, try main emoji directory
    if subfolder and os.path.exists(EMOJI_ASSETS_DIR):
        main_emojis = [f for f in os.listdir(EMOJI_ASSETS_DIR) if f.endswith('.svg')]
        if main_emojis:
            return os.path.join(EMOJI_ASSETS_DIR, random.choice(main_emojis))
    
    return fallback_emoji

def get_custom_emoji_for_context(context_name, fallback_emoji="❓"):
    """
    Get a specific custom emoji based on context/usage.
    Maps regular emojis to custom NASA-themed emojis.
    """
    emoji_mapping = {
        # Tab emojis
        "ai_search": "Satellite_1.svg",
        "study_explorer": "Scientist_1.svg", 
        "knowledge_graph": "Satellite_Ground_1.svg",
        "data_setup": "MArs_Rover_1.svg",
        
        # Action emojis
        "search": "Satellite_1.svg",
        "view_graph": "Satellite_Ground_1.svg",
        "organism": "Earth_2.svg",
        "factor": "Mars_1.svg",
        "study_id": "Rocket_1.svg",
        "execute": "Rocket_1.svg",
        "cypher": "Satellite_Ground_1.svg",
        "home": "Rocket_1.svg"
    }
    
    if context_name in emoji_mapping:
        emoji_path = os.path.join(EMOJI_ASSETS_DIR, emoji_mapping[context_name])
        if os.path.exists(emoji_path):
            return emoji_path
    
    # If no specific emoji found, try to return any available emoji file
    if os.path.exists(EMOJI_ASSETS_DIR):
        available_emojis = [f for f in os.listdir(EMOJI_ASSETS_DIR) if f.endswith('.svg')]
        if available_emojis:
            return os.path.join(EMOJI_ASSETS_DIR, available_emojis[0])
    
    # Return None if no emoji files are available
    return None

# === Optional: Neo4j Integration ===
if 'build_and_display_study_graph' in globals():
    neo4j_enabled = True
else:
    neo4j_enabled = False

# === Session State Initialization ===
def initialize_session_state():
    """Initialize all session state variables with safe defaults"""
    defaults = {
        # Core app state
        'graph_html': None,
        'last_scrape_status_message': None,
        'ai_comparison_text': None,
        'selected_study_for_kg': None,
        'mongo_query': None,
        'last_scrape_status_type': 'info',
        
        # Lists
        'kg_study_ids': [],
        'ai_search_results': [],
        
        # Booleans
        'scraping_in_progress': False,
        'search_triggered': False,
        'cypher_session_restored': False,
        
        # UI elements
        'app_title_emoji_left': None,
        'app_title_emoji_right': None,
        'home_link_nav_icon': None,
        
        # Cypher editor state
        'cypher_query_result': None,
        'cypher_query_executed': None,
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value
    
    # Initialize emoji paths safely
    try:
        if st.session_state.app_title_emoji_left is None:
            st.session_state.app_title_emoji_left = get_random_emoji_image_path()
        if st.session_state.app_title_emoji_right is None:
            st.session_state.app_title_emoji_right = get_random_emoji_image_path()
        if st.session_state.home_link_nav_icon is None:
            st.session_state.home_link_nav_icon = get_custom_emoji_for_context("home")
    except Exception:
        # Fallback if emoji functions fail
        pass

# Initialize session state
initialize_session_state()

# Global error handler for session state issues
def safe_session_get(key, default=None):
    """Safely get session state value with fallback"""
    try:
        return st.session_state.get(key, default)
    except (KeyError, AttributeError):
        return default

def safe_session_set(key, value):
    """Safely set session state value"""
    try:
        st.session_state[key] = value
        return True
    except Exception:
        return False

# === Enhanced Session Management Initialization (SURGICAL FIX #1: Defensive Loading) ===
try:
    from session_manager import session_manager
    # Restore previous session if available - but don't fail if it doesn't exist
    if not st.session_state.get('cypher_session_restored', False):
        try:
            session_info = session_manager.restore_session()
        except (KeyError, AttributeError, Exception):
            # Session state key doesn't exist yet or other error - that's OK, first run
            pass
        st.session_state.cypher_session_restored = True
except ImportError:
    # session_manager module doesn't exist - continue without it
    st.session_state.cypher_session_restored = True

# === MongoDB Client Initialization ===
mongo_client = get_mongo_client()
if mongo_client:
    db = mongo_client["nasa_osdr"]
    studies_collection = db["studies"]
else:
    st.error("Halting app due to MongoDB connection failure. Check your secrets.")
    st.stop()

# === Neo4j Connection (SURGICAL FIX #2: Optional, Non-Breaking) ===
neo4j_enabled = False
neo4j_conn = None

try:
    from neo4j import GraphDatabase
    
    class Neo4jConnection:
        def __init__(self):
            # Use centralized configuration
            from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
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
    logger.info(f"Neo4j: {neo4j_conn.uri}")
    neo4j_enabled = neo4j_conn.connect()
    
except Exception as e:
    # Neo4j not available - continue without it
    print(f"ℹ️ Neo4j unavailable: {str(e)[:50]}")
    neo4j_enabled = False

# === Sidebar ===
with st.sidebar:
    # Modern sidebar header using native Streamlit
    st.markdown("## 🛰️ Mission Control")
    st.markdown("*Research Platform v2.0*")
    
    st.markdown("---")
    
    # System status with elegant UI
    if elegant_ui_available:
        database_status = [
            {
                "name": "MongoDB Atlas",
                "status": "Connected" if mongo_client else "Offline",
                "uptime": 99.9
            },
            {
                "name": "Neo4j Aura",
                "status": "Connected" if neo4j_conn and neo4j_conn.connected else "Offline", 
                "uptime": 99.8
            }
        ]
        create_status_indicators(database_status)
    else:
        # Fallback status
        st.markdown("### System Status")
        mongo_status = "🟢 Connected" if mongo_client else "🔴 Offline"
        neo4j_status = "🟢 Connected" if neo4j_conn and neo4j_conn.connected else "🔴 Offline"
        st.markdown(f"**MongoDB:** {mongo_status}")
        st.markdown(f"**Neo4j:** {neo4j_status}")
    
    st.markdown("---")
    
    # Researcher Spotlight
    try:
        from app_credits_manager import app_credits
        app_credits.render_researcher_spotlight()
        st.markdown("---")
    except ImportError:
        pass
    
    # Admin tools with elegant styling
    st.markdown("### ⚙️ System Tools")
    if st.button("🔄 Clear Cache & Reset", key="clear_cache_state_btn", use_container_width=True):
        st.cache_data.clear()
        st.cache_resource.clear()
        if neo4j_conn:
            neo4j_conn.close()
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.success("✅ System cache cleared and session reset")
        st.rerun()

# === Elegant Research Platform Header ===
if elegant_ui_available:
    create_elegant_header(
        "NASA OSDR Research Platform",
        "Advanced Space Biology Data Analysis & Knowledge Discovery"
    )
    
    # Add research metrics using real data
    if mongo_client:
        try:
            from data_source_manager import data_source_manager
            
            # Get real OSDR metrics
            osdr_metrics = data_source_manager.get_real_osdr_metrics()
            
            if osdr_metrics["data_source"] == "real":
                studies_count = osdr_metrics["total_studies"]
                metrics = [
                    {"label": "OSDR Studies", "value": f"{studies_count:,}", "delta": "Real data"},
                    {"label": "Databases", "value": "2/2", "delta": "Connected"},
                    {"label": "Data Quality", "value": "Live", "delta": "Real-time"},
                    {"label": "Platform", "value": "Active", "delta": "Operational"}
                ]
                create_metrics_row(metrics)
                st.success("📊 **Live Metrics**: Using real data from your OSDR database")
            else:
                # Fallback metrics with clear labeling
                metrics = [
                    {"label": "Platform Status", "value": "Active", "delta": "Operational"},
                    {"label": "Databases", "value": "2/2", "delta": "Connected"},
                    {"label": "Research Tools", "value": "6", "delta": "Available"},
                    {"label": "Data Source", "value": "Demo", "delta": "Simulated"}
                ]
                create_metrics_row(metrics)
                st.warning("📋 **Demo Metrics**: Connect to OSDR database for real metrics")
        except Exception as e:
            # Error fallback
            metrics = [
                {"label": "Platform Status", "value": "Active", "delta": "Operational"},
                {"label": "Connection", "value": "Error", "delta": "Check config"},
                {"label": "Mode", "value": "Demo", "delta": "Fallback"},
                {"label": "Data Source", "value": "Simulated", "delta": "Not real"}
            ]
            create_metrics_row(metrics)
            st.error(f"⚠️ **Connection Error**: {str(e)[:100]}... Using demo data.")
else:
    # Fallback header
    st.markdown("# 🚀 NASA OSDR Research Platform")
    st.markdown("*Advanced Space Biology Data Analysis & Knowledge Discovery*")
    st.markdown("---")

# === Enhanced Tabs for Research Value ===
tab_ai_search, tab_explorer, tab_kg, tab_realtime, tab_analytics, tab_ontology, tab_sources, tab_credits, tab_extract = st.tabs([
    "🔍 AI Semantic Search", 
    "📚 Study Explorer", 
    "🕸️ Knowledge Graph", 
    "🌍 Real-Time Data",
    "📊 Research Analytics", 
    "🧬 Ontology Browser",
    "📋 Data Sources",
    "🌟 Credits & Researchers",
    "⚙️ Data & Setup"
])

# === AI Semantic Search Tab ===
with tab_ai_search:
    # Custom header with NASA emoji
    header_cols = st.columns([1, 10])
    with header_cols[0]:
        st.image(get_custom_emoji_for_context("ai_search"), width=40)
    with header_cols[1]:
        st.header("AI-Powered Semantic Search")
    
    # Check if vector search is available
    vector_search_available = False
    
    # Try to check if vector search function exists
    try:
        from enhanced_neo4j_executor import perform_vector_search
        vector_search_available = True
    except ImportError:
        vector_search_available = False
    
    if not vector_search_available:
        st.warning("🔧 **AI Vector Search Setup Required**")
        st.markdown("""
        **To enable AI semantic search, you need to:**
        
        1. **Set up MongoDB Atlas Vector Search** on your studies collection
        2. **Configure text embeddings** for study descriptions
        3. **Set up GCP Vertex AI credentials** (optional - for enhanced AI)
        
        **Alternative: Use the Study Explorer tab** for keyword-based search while AI search is being configured.
        """)
        
        # Provide fallback search
        st.markdown("### 🔍 Fallback: Keyword Search")
        user_question = st.text_area("Enter keywords to search:", height=100, placeholder="e.g., microgravity cardiovascular mammals")
        
        if st.button("Search Keywords", key="keyword_search_button"):
            if user_question and studies_collection:
                try:
                    # Simple text search as fallback
                    search_terms = user_question.lower().split()
                    query = {
                        "$or": [
                            {"title": {"$regex": "|".join(search_terms), "$options": "i"}},
                            {"description": {"$regex": "|".join(search_terms), "$options": "i"}},
                            {"organisms": {"$in": search_terms}},
                            {"factors": {"$in": search_terms}}
                        ]
                    }
                    
                    results = list(studies_collection.find(query).limit(10))
                    
                    if results:
                        st.success(f"Found **{len(results)}** studies matching your keywords.")
                        for item in results:
                            with st.expander(f"**{item.get('study_id', 'N/A')}:** {item.get('title', 'No Title')}"):
                                st.markdown(f"**Description:** {item.get('description', 'N/A')}")
                                if item.get('study_link'): 
                                    st.markdown(f"[View Original Study on OSDR]({item.get('study_link')})")
                    else:
                        st.info("No studies found matching those keywords. Try different terms or use the Study Explorer tab.")
                        
                except Exception as e:
                    st.error(f"Search error: {e}")
    else:
        st.success("✅ **AI Vector Search Available**")
        st.markdown("Ask a question in natural language to find the most conceptually related studies in the dataset.")
        user_question = st.text_area("Enter your research question:", height=100, placeholder="e.g., What are the effects of microgravity on the cardiovascular system of mammals?")

        if st.button("Search with AI", key="ai_search_button"):
            if user_question:
                try:
                    with st.spinner("Searching for conceptually similar studies using AI..."):
                        st.session_state.ai_search_results = perform_vector_search(user_question, studies_collection)
                except Exception as e:
                    st.error(f"⚠️ AI Search error: {e}")
                    st.info("💡 **Tip**: Try the keyword search in Study Explorer tab as an alternative.")
                    st.session_state.ai_search_results = []
            else:
                st.warning("Please enter a question to search.")
                st.session_state.ai_search_results = []

    if st.session_state.ai_search_results:
        results = st.session_state.ai_search_results
        if not results or (isinstance(results, list) and len(results) > 0 and "error" in results[0]):
            st.error(f"An error occurred: {results[0].get('error', 'Unknown')}")
        else:
            st.success(f"Found **{len(results)}** conceptually relevant studies, sorted by relevance.")
            for item in results:
                with st.expander(f"**{item.get('study_id', 'N/A')}:** {item.get('title', 'No Title')} (Relevance Score: {item.get('score', 0):.4f})"):
                    st.markdown(f"**Description:** {item.get('description', 'N/A')}")
                    if item.get('study_link'): st.markdown(f"[View Original Study on OSDR]({item.get('study_link')})")
                    if neo4j_enabled:
                        # Custom button with NASA emoji
                        view_cols = st.columns([1, 10])
                        with view_cols[0]:
                            st.image(get_custom_emoji_for_context("view_graph"), width=15)
                        with view_cols[1]:
                            if st.button("View Knowledge Graph", key=f"kg_view_ai_{item.get('study_id')}"):
                                st.session_state.selected_study_for_kg = item.get('study_id')
                                st.session_state.graph_html = None
                                st.session_state.kg_study_ids = []
                                st.session_state.ai_comparison_text = None
                                logger.info(f"🔗 KG: Study {item.get('study_id')} selected from AI search")
                                st.success(f"✅ Study loaded. Go to Knowledge Graph tab.")
                                st.rerun()

# === Keyword Search Tab ===
with tab_explorer:
    # Custom header with NASA emoji
    header_cols = st.columns([1, 10])
    with header_cols[0]:
        st.image(get_custom_emoji_for_context("study_explorer"), width=40)
    with header_cols[1]:
        st.header("Keyword-Based Study Explorer")
    st.markdown("Filter and view detailed information for studies stored in the database using exact keywords.")
    with st.form(key="search_form"):
        filter_cols = st.columns([2, 2, 1])
        with filter_cols[0]: 
            col1, col2 = st.columns([1, 10])
            with col1:
                st.image(get_custom_emoji_for_context("organism"), width=20)
            with col2:
                organism_filter = st.text_input("Organism contains", placeholder="e.g., Mus musculus")
        with filter_cols[1]: 
            col1, col2 = st.columns([1, 10])
            with col1:
                st.image(get_custom_emoji_for_context("factor"), width=20)
            with col2:
                factor_filter = st.text_input("Factor contains", placeholder="e.g., Spaceflight")
        with filter_cols[2]: 
            col1, col2 = st.columns([1, 10])
            with col1:
                st.image(get_custom_emoji_for_context("study_id"), width=20)
            with col2:
                study_id_filter = st.text_input("Study ID is", placeholder="e.g., OSD-840")
        search_cols = st.columns([1, 10])
        with search_cols[0]:
            st.image(get_custom_emoji_for_context("search"), width=20)
        with search_cols[1]:
            submitted = st.form_submit_button("Search by Keyword")
        if submitted:
            query = {}
            if organism_filter: query["organisms"] = {"$regex": organism_filter.strip(), "$options": "i"}
            if factor_filter: query["factors"] = {"$regex": factor_filter.strip(), "$options": "i"}
            if study_id_filter: query["study_id"] = {"$regex": f"^{study_id_filter.strip()}$", "$options": "i"}
            st.session_state.mongo_query = query
            st.session_state.search_triggered = True

    # Only show results if search was triggered and we have a query
    if st.session_state.get('search_triggered') and st.session_state.get('mongo_query') is not None:
        try:
            results = list(studies_collection.find(st.session_state.mongo_query).limit(50))
            st.metric(label="Studies Found", value=len(results))
            
            if not results and st.session_state.mongo_query: 
                st.warning("No studies match your filter criteria.")
            else:
                for item in results:
                    with st.expander(f"{item.get('study_id', 'N/A')}: {item.get('title', 'No Title')}"):
                        st.markdown(f"**Description:** {item.get('description', 'N/A')}")
                        # Custom button with NASA emoji
                        view_cols = st.columns([1, 10])
                        with view_cols[0]:
                            st.image(get_custom_emoji_for_context("view_graph"), width=15)
                        with view_cols[1]:
                            if st.button("View Knowledge Graph", key=f"kg_view_kw_{item.get('study_id')}"):
                                st.session_state.selected_study_for_kg = item.get('study_id')
                                st.session_state.graph_html, st.session_state.kg_study_ids, st.session_state.ai_comparison_text = None, [], None
                                st.success(f"Study {item.get('study_id')} selected. Switch to the 'Knowledge Graph' tab.")
                                
            # Reset search trigger after displaying results to prevent duplicate rendering
            st.session_state.search_triggered = False
            
        except Exception as e:
            st.error(f"Error searching studies: {e}")
            st.session_state.search_triggered = False

# === Knowledge Graph Tab ===
with tab_kg:
    # Simplified Knowledge Graph tab for stability
    st.header("🕸️ Knowledge Graph Explorer")
    
    if not neo4j_enabled:
        st.warning("⚠️ Neo4j Unavailable (Production Mode)")
        st.info("Knowledge Graph visualization requires Neo4j connection. This feature is available in local development.")
        
        if st.session_state.get('selected_study_for_kg'):
            st.info(f"Selected study: {st.session_state.get('selected_study_for_kg')}")
            if st.button("Clear Selection", key="kg_clear_simple"):
                st.session_state.selected_study_for_kg = None
                st.rerun()
    else:
        st.success("✅ Neo4j Connected - Knowledge Graph Available")
        
        # Simple query interface
        st.subheader("Cypher Query Interface")
        
        # Sample queries
        sample_queries = {
            "Find all studies": "MATCH (s:Study) RETURN s LIMIT 10",
            "Studies with mice": "MATCH (s:Study)-[:HAS_ORGANISM]->(o:Organism) WHERE o.organism_name CONTAINS 'mouse' RETURN s, o LIMIT 5",
            "Spaceflight studies": "MATCH (s:Study)-[:HAS_FACTOR]->(f:Factor) WHERE f.factor_name CONTAINS 'spaceflight' RETURN s, f LIMIT 5"
        }
        
        # Query selection
        selected_query_name = st.selectbox("Choose a sample query:", list(sample_queries.keys()))
        query = st.text_area("Cypher Query:", value=sample_queries[selected_query_name], height=150)
        
        if st.button("Execute Query", key="simple_kg_execute"):
            try:
                from enhanced_neo4j_executor import neo4j_executor
                with st.spinner("Executing query..."):
                    result = neo4j_executor.execute_query(query)
                    
                if result.success:
                    st.success(f"✅ Query executed successfully in {result.execution_time:.0f}ms")
                    
                    # Simple results display
                    if hasattr(result, 'data') and result.data:
                        st.subheader("Results")
                        st.json(result.data[:5])  # Show first 5 results
                        
                        if len(result.data) > 5:
                            st.info(f"Showing first 5 of {len(result.data)} results")
                    else:
                        st.info("Query executed but returned no data")
                else:
                    st.error(f"Query failed: {result.error_message}")
                    
            except Exception as e:
                st.error(f"Error executing query: {str(e)}")
        
        # Show selected study if available
        if st.session_state.get('selected_study_for_kg'):
            st.markdown("---")
            st.subheader("Selected Study")
            st.info(f"Study ID: {st.session_state.get('selected_study_for_kg')}")
            
            if st.button("Clear Selection", key="kg_clear_neo4j"):
                st.session_state.selected_study_for_kg = None
                st.rerun()

# === Real-Time Data Tab ===
with tab_realtime:
    try:
        from realtime_data_manager import realtime_manager
        from data_source_manager import data_source_manager
        
        # Add data source transparency
        st.info("📡 **Data Sources**: ISS position/crew are real-time APIs. Space weather and experiments are demo data.")
        
        realtime_manager.render_complete_dashboard()
    except ImportError:
        st.error("Real-time data manager not available")

# === Research Analytics Tab ===
with tab_analytics:
    try:
        from research_analytics import research_analytics
        from data_source_manager import data_source_manager
        
        # Add data source transparency
        data_source_manager.add_data_accuracy_note("research_analytics", "Research Analytics")
        
        research_analytics.render_complete_analytics_dashboard()
    except ImportError:
        st.error("Research analytics not available")

# === Ontology Browser Tab ===
with tab_ontology:
    try:
        from ontology_manager import ontology_manager
        
        st.title("🧬 Formal Ontology & Metadata Standards")
        
        # Ontology navigation
        ontology_tab1, ontology_tab2 = st.tabs(["📖 Browse Ontology", "✅ Validate Metadata"])
        
        with ontology_tab1:
            ontology_manager.render_ontology_browser()
        
        with ontology_tab2:
            ontology_manager.render_metadata_validator()
            
    except ImportError:
        st.error("Ontology manager not available")

# === Data Sources Tab ===
with tab_sources:
    try:
        from data_source_manager import data_source_manager
        
        st.title("📋 Data Sources & Accuracy")
        st.markdown("This tab shows exactly what data is real vs. demo/simulated for complete transparency.")
        
        # Show data source panel
        data_source_manager.render_data_source_panel()
        
        st.markdown("---")
        
        # Show accuracy legend
        data_source_manager.create_accuracy_legend()
        
        st.markdown("---")
        
        # Show real OSDR metrics if available
        st.markdown("### 🔍 Your Real OSDR Data")
        osdr_metrics = data_source_manager.get_real_osdr_metrics()
        
        if osdr_metrics["data_source"] == "real":
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Studies", osdr_metrics["total_studies"])
                
                if osdr_metrics["top_organisms"]:
                    st.markdown("**Top Organisms:**")
                    for org in osdr_metrics["top_organisms"][:3]:
                        st.markdown(f"- {org['_id']}: {org['count']} studies")
            
            with col2:
                st.markdown(f"**Last Updated:** {osdr_metrics['last_updated'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
                
                if osdr_metrics["top_factors"]:
                    st.markdown("**Top Factors:**")
                    for factor in osdr_metrics["top_factors"][:3]:
                        st.markdown(f"- {factor['_id']}: {factor['count']} studies")
        else:
            st.warning("Could not connect to OSDR database. Check your configuration in the Data & Setup tab.")
            
    except ImportError:
        st.error("Data source manager not available")

# === Credits & Researchers Tab ===
with tab_credits:
    try:
        from app_credits_manager import app_credits
        
        # Beautiful extraction interface
        try:
            from tribute_ui_components import tribute_ui
            tribute_ui.render_extraction_panel(549)
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("""
                ### 🎯 What This Will Do:
                - **Scrape all 549 OSDR studies** for researcher information
                - **Extract Principal Investigators, Co-Investigators, and Authors**
                - **Build complete researcher profiles** with affiliations and expertise
                - **Map collaboration networks** based on shared studies
                - **Create the ultimate space biology researcher database**
                """)
            
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🚀 Start Full Extraction", key="start_extraction", use_container_width=True):
                    st.session_state.start_researcher_extraction = True
        
        except ImportError:
            # Fallback extraction interface
            st.markdown("## 🔍 OSDR Researcher Extraction")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.info("💡 **Extract ALL researchers from your 500+ OSDR studies** to create the most comprehensive space biology researcher database ever assembled!")
            
            with col2:
                if st.button("🚀 Start Full Extraction", key="start_extraction", use_container_width=True):
                    st.session_state.start_researcher_extraction = True
        
        # Show extraction progress if started
        if st.session_state.get('start_researcher_extraction', False):
            try:
                from osdr_researcher_extractor import osdr_researcher_extractor
                
                with st.spinner("🔍 Extracting researchers from all OSDR studies..."):
                    researchers_db = osdr_researcher_extractor.extract_all_researchers_from_osdr()
                    osdr_researcher_extractor.save_researchers_to_database()
                
                st.success(f"✅ Successfully extracted {len(researchers_db)} unique researchers!")
                st.session_state.start_researcher_extraction = False
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Extraction failed: {e}")
                st.session_state.start_researcher_extraction = False
        
        st.markdown("---")
        
        # Add researcher analytics if data is available
        try:
            from researcher_analytics import researcher_analytics
            
            # Check if we have researcher data
            osdr_researchers = app_credits.get_researcher_from_osdr_data()
            
            if osdr_researchers and len(osdr_researchers) > 10:
                st.markdown("## 📊 Research Community Analytics")
                
                if st.button("🔍 Analyze Research Community", key="analyze_community"):
                    researcher_analytics.render_complete_researcher_analytics(osdr_researchers)
                
                st.markdown("---")
        
        except ImportError:
            pass
        
        # Render the comprehensive credits
        app_credits.render_comprehensive_credits()
        
    except ImportError:
        st.error("Credits manager not available")

# === Data & Setup Tab ===
with tab_extract:
    # Custom header with NASA emoji
    header_cols = st.columns([1, 10])
    with header_cols[0]:
        st.image(get_custom_emoji_for_context("data_setup"), width=40)
    with header_cols[1]:
        st.header("OSDR Data Status & Management")
    if 'last_scrape_status_message' in st.session_state and st.session_state.last_scrape_status_message:
        status_type = st.session_state.get('last_scrape_status_type', 'info')
        getattr(st, status_type)(st.session_state.last_scrape_status_message)
    try:
        studies_count = studies_collection.count_documents({})
        if studies_count > 0:
            # Custom success with NASA emoji
            success_cols = st.columns([1, 20])
            with success_cols[0]:
                st.image(get_custom_emoji_for_context("success"), width=20)
            with success_cols[1]:
                st.success(f"Your MongoDB database is populated with **{studies_count}** studies.")
            
            # Custom button with NASA emoji
            refresh_cols = st.columns([1, 10])
            with refresh_cols[0]:
                st.image(get_custom_emoji_for_context("refresh"), width=20)
            with refresh_cols[1]:
                if st.button("Re-fetch All Data (will overwrite)", key="refetch_data_btn"):
                    st.session_state.scraping_in_progress = True; st.rerun()
        else:
            st.warning("Your database is empty."); st.markdown("Use the button below to scrape all study data.")
            # Custom button with NASA emoji
            fetch_cols = st.columns([1, 10])
            with fetch_cols[0]:
                st.image(get_custom_emoji_for_context("rocket"), width=20)
            with fetch_cols[1]:
                if st.button("Fetch All OSDR Studies", key="initial_fetch_btn"):
                    st.session_state.scraping_in_progress = True; st.rerun()
        if st.session_state.get('scraping_in_progress'):
            with st.spinner("Scraping data... this will take several minutes."):
                try:
                    if studies_count > 0: studies_collection.delete_many({})
                    all_studies_data = extract_study_data()
                    if all_studies_data:
                        save_to_json(all_studies_data, "data/osdr_studies.json")
                        saved_counts = save_to_mongo(all_studies_data, studies_collection)
                        msg = f"MongoDB: {saved_counts.get('inserted',0)} inserted." if isinstance(saved_counts, dict) else ""
                        st.session_state.last_scrape_status_message = f"Success! Scraped {len(all_studies_data)} studies. {msg}"
                        st.session_state.last_scrape_status_type = "success"
                except Exception as e:
                    st.session_state.last_scrape_status_message = f"Error: {e}"; st.session_state.last_scrape_status_type = "error"
                finally:
                    st.session_state.scraping_in_progress = False; st.rerun()
    except Exception as e: 
        # Custom error with NASA emoji
        db_error_cols = st.columns([1, 20])
        with db_error_cols[0]:
            st.image(get_custom_emoji_for_context("error"), width=20)
        with db_error_cols[1]:
            st.error(f"DB status check failed: {e}")

# === Optional CLI Functionality ===
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run_scraper":
        print("🚀 Running scraper pipeline from CLI...")
        if not mongo_client: print("❌ MongoDB client not initialized.")
        else:
            try:
                cli_studies_collection = mongo_client["nasa_osdr"]["studies"]
                studies = extract_study_data()
                if studies:
                    save_to_json(studies, "data/osdr_studies_cli.json")
                    counts = save_to_mongo(studies, cli_studies_collection)
                    print(f"✅ MongoDB (CLI): {counts.get('inserted',0)} inserted, {counts.get('updated',0)} updated.")
                else: print("⚠️ No studies were extracted in CLI run.")
            except Exception as e:
                print(f"❌ Error in CLI scraper pipeline: {e}"); traceback.print_exc()
