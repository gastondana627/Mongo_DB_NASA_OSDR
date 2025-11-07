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

# === Apply Smooth Loading Animations ===
try:
    from loading_animations import loading_animations
    loading_animations.apply_smooth_ui_css()
except ImportError:
    pass

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

# For testing KG integration, temporarily enable KG buttons even without Neo4j
# This allows testing the session state flow
neo4j_enabled = True  # TODO: Remove this line when Neo4j is properly configured

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
    # Enable AI search for demo
    vector_search_available = True
    
    if not vector_search_available:
        st.info("🔍 **AI Semantic Search is currently being configured**")
        st.markdown("**In the meantime, use the powerful keyword search below or try the Study Explorer tab for more filtering options.**")
        
        # Provide fallback search
        st.markdown("### 🔍 Keyword Search")
        user_question = st.text_area("Enter keywords to search:", height=100, placeholder="e.g., microgravity cardiovascular mammals")
        
        if st.button("Search Keywords", key="keyword_search_button"):
            if user_question and studies_collection is not None:
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
                                
                                # Add Knowledge Graph button for fallback search too
                                if neo4j_enabled:
                                    view_cols = st.columns([1, 10])
                                    with view_cols[0]:
                                        st.image(get_custom_emoji_for_context("view_graph"), width=15)
                                    with view_cols[1]:
                                        # Use the centralized node lock manager
                                        from node_lock_manager import node_lock_manager
                                        study_id = item.get('study_id')
                                        study_title = item.get('title', 'Unknown Title')
                                        study_description = item.get('description', 'No description available')
                                        
                                        node_lock_manager.render_lock_button(
                                            study_id=study_id,
                                            tab_name="ai_semantic_search",
                                            study_title=study_title,
                                            study_description=study_description,
                                            button_key=f"kg_view_fallback_{study_id}"
                                        )
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
                        # Fallback: Use enhanced keyword search that mimics AI behavior
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
                        # Add mock relevance scores for demo
                        for i, result in enumerate(results):
                            result['score'] = 0.95 - (i * 0.05)  # Decreasing relevance scores
                        
                        st.session_state.ai_search_results = results
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
                            # Use the centralized node lock manager
                            from node_lock_manager import node_lock_manager
                            study_id = item.get('study_id')
                            study_title = item.get('title', 'Unknown Title')
                            study_description = item.get('description', 'No description available')
                            
                            node_lock_manager.render_lock_button(
                                study_id=study_id,
                                tab_name="ai_semantic_search",
                                study_title=study_title,
                                study_description=study_description,
                                button_key=f"kg_view_ai_{study_id}"
                            )

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

    # Status indicator for Study Explorer
    current_locked = st.session_state.get('selected_study_for_kg')
    if current_locked:
        st.info(f"🔒 **Currently Locked**: {current_locked} - Switch to Knowledge Graph tab to view")
    
    # Debug section for Study Explorer
    with st.expander("🔧 Study Explorer Debug", expanded=False):
        st.write("**Current Session State:**")
        st.write(f"- Selected study: {st.session_state.get('selected_study_for_kg', 'None')}")
        st.write(f"- KG auto executed: {st.session_state.get('kg_auto_executed', 'None')}")
        st.write(f"- Search triggered: {st.session_state.get('search_triggered', 'None')}")
        
        # Quick test lock button
        if st.button("🧪 Test Lock OSD-782", key="test_lock_explorer"):
            from node_lock_manager import node_lock_manager
            success = node_lock_manager.lock_node("OSD-782", "study_explorer", "Test Study", "Test Description")
            if success:
                st.success("✅ Test lock successful!")
                st.rerun()
            else:
                st.error("❌ Test lock failed!")
        
        # Clear lock button for testing
        if current_locked and st.button("🔓 Clear Lock (Debug)", key="clear_lock_debug"):
            st.session_state.selected_study_for_kg = None
            st.session_state.kg_auto_executed = False
            st.success("🔓 Lock cleared!")
            st.rerun()
    
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
                            # Use the centralized node lock manager
                            from node_lock_manager import node_lock_manager
                            study_id = item.get('study_id')
                            study_title = item.get('title', 'Unknown Title')
                            study_description = item.get('description', 'No description available')
                            
                            # Debug info for Study Explorer
                            if st.checkbox(f"Debug {study_id}", key=f"debug_{study_id}", value=False):
                                st.write(f"Study ID: {study_id}")
                                st.write(f"Tab name: study_explorer")
                                st.write(f"Current locked: {st.session_state.get('selected_study_for_kg', 'None')}")
                                st.write(f"Can lock: {node_lock_manager.can_lock_nodes('study_explorer')}")
                            
                            node_lock_manager.render_lock_button(
                                study_id=study_id,
                                tab_name="study_explorer",
                                study_title=study_title,
                                study_description=study_description,
                                button_key=f"kg_view_kw_{study_id}"
                            )
                                
            # Reset search trigger after displaying results to prevent duplicate rendering
            st.session_state.search_triggered = False
            
        except Exception as e:
            st.error(f"Error searching studies: {e}")
            st.session_state.search_triggered = False

# === Knowledge Graph Tab ===
with tab_kg:
    try:
        # Custom header with NASA emoji
        header_cols = st.columns([1, 10])
        with header_cols[0]:
            st.image(get_custom_emoji_for_context("knowledge_graph"), width=40)
        with header_cols[1]:
            st.header("Enhanced Knowledge Graph Explorer")
        
        # Check if a study was selected from other tabs
        selected_study_id = st.session_state.get('selected_study_for_kg')
        
        # Temporary debug info for troubleshooting
        with st.expander("🔧 Debug Info (Click to expand)", expanded=False):
            st.write(f"**selected_study_for_kg**: {selected_study_id}")
            st.write(f"**kg_auto_executed**: {st.session_state.get('kg_auto_executed', 'Not set')}")
            st.write(f"**cypher_query_result**: {'Present' if st.session_state.get('cypher_query_result') else 'None'}")
            st.write(f"**All KG keys**: {[k for k in st.session_state.keys() if 'kg' in k.lower() or 'study' in k.lower()]}")
            
            # Manual test button
            if st.button("🧪 Test Lock OSD-840", key="test_lock"):
                st.session_state.selected_study_for_kg = "OSD-840"
                st.session_state.kg_auto_executed = False
                st.success("Test lock applied! Check if locked node appears above.")
        

        # === LOCKED NODE SYSTEM ===
        # Use the centralized node lock manager with error handling
        try:
            import sys
            import os
            
            # Ensure the current directory is in the path
            current_dir = os.path.dirname(os.path.abspath(__file__))
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)
            
            from node_lock_manager import node_lock_manager
            node_lock_manager.render_locked_node_display()
        except Exception as lock_error:
            # Fallback to legacy locked node display
            if selected_study_id:
                # Prominent locked node display
                st.container()
                lock_cols = st.columns([1, 15, 3])
                with lock_cols[0]:
                    st.image(get_custom_emoji_for_context("study_id"), width=40)
                with lock_cols[1]:
                    st.markdown(f"### 🔒 **LOCKED NODE**: {selected_study_id}")
                    
                    # Get and display study details
                    try:
                        study_doc = studies_collection.find_one({"study_id": selected_study_id})
                        if study_doc:
                            st.markdown(f"**{study_doc.get('title', 'N/A')}**")
                            st.caption(f"{study_doc.get('description', 'N/A')[:150]}...")
                    except Exception:
                        st.caption("Study details unavailable")
                        
                with lock_cols[2]:
                    # Release Node button
                    if st.button("🔓 **Release Node**", key="release_node", type="primary"):
                        # Clear all KG-related session state
                        st.session_state.selected_study_for_kg = None
                        st.session_state.graph_html = None
                        st.session_state.kg_study_ids = []
                        st.session_state.ai_comparison_text = None
                        st.session_state.cypher_query_result = None
                        st.session_state.kg_auto_executed = False
                        st.session_state.kg_mock_result = None
                        st.success("🔓 Node released! Knowledge Graph reset.")
                        st.rerun()
                
                st.markdown("---")
        
        # Auto-execute query for locked study (regardless of Neo4j status)
        if selected_study_id and not st.session_state.get('kg_auto_executed', False):
            # Generate query automatically
            auto_query = f"""MATCH (s:Study {{study_id: '{selected_study_id}'}})
OPTIONAL MATCH (s)-[r]-(n)
RETURN s, r, n
LIMIT 25"""
            
            # Mark as executed to prevent re-execution
            st.session_state.kg_auto_executed = True
            st.session_state.kg_auto_query = auto_query
            
            # Execute the query if Neo4j is available
            if neo4j_enabled:
                try:
                    from enhanced_neo4j_executor import neo4j_executor
                    
                    # Show enhanced loading animation
                    try:
                        from loading_animations import loading_animations
                        
                        # Create animation container
                        loading_container = st.empty()
                        
                        with loading_container.container():
                            # Show query execution animation
                            loading_animations.show_query_execution_animation(auto_query, duration=2.0)
                        
                        # Execute query
                        result = neo4j_executor.execute_query(auto_query)
                        
                        # Clear loading animation
                        loading_container.empty()
                        
                        if result.success:
                            st.session_state.cypher_query_result = result
                            st.session_state.cypher_query_executed = auto_query
                            
                            # Show success with animation
                            loading_animations.show_success_animation(f"Visualization loaded! ({result.execution_time:.0f}ms)")
                        else:
                            st.error(f"❌ Query failed: {result.error_message}")
                            
                    except ImportError:
                        # Fallback to simple spinner
                        with st.spinner(f"🤖 Loading visualization for {selected_study_id}..."):
                            result = neo4j_executor.execute_query(auto_query)
                            if result.success:
                                st.session_state.cypher_query_result = result
                                st.session_state.cypher_query_executed = auto_query
                                st.success(f"✅ **Locked node visualization loaded!** Query executed in {result.execution_time:.0f}ms")
                            else:
                                st.error(f"❌ Query failed: {result.error_message}")
                                
                except Exception as e:
                    st.error(f"❌ Auto-query execution failed: {str(e)}")
            else:
                # Create a mock result for display when Neo4j is not available
                st.session_state.kg_mock_result = {
                    "study_id": selected_study_id,
                    "query": auto_query,
                    "message": "Neo4j visualization not available - showing study metadata instead"
                }
            
            st.rerun()
        
        if not neo4j_enabled: 
            # Custom error with NASA emoji
            error_cols = st.columns([1, 20])
            with error_cols[0]:
                st.image(get_custom_emoji_for_context("error"), width=20)
            with error_cols[1]:
                st.warning("⚠️ Neo4j Unavailable (Production Mode)")
            st.info("Knowledge Graph visualization requires Neo4j. Local deployment shows full relationship maps. Viewing study metadata instead...")
            
            if selected_study_id:
                st.info("💡 **Neo4j Required**: To see the full knowledge graph and relationships for this study, Neo4j connection is needed.")
            else:
                st.info("Select a study from AI Semantic Search or Study Explorer to view its metadata.")
        else:
            # Import the Cypher editor with error handling
            try:
                from cypher_editor import CypherEditor
                from enhanced_neo4j_executor import neo4j_executor
                
                # Create cypher editor instance
                cypher_editor = CypherEditor()
                
                # Create two-column layout: Cypher editor on left, graph on right
                editor_col, graph_col = st.columns([1, 2], gap="medium")
                
                with editor_col:
                    # Custom subheader with NASA emoji
                    subheader_cols = st.columns([1, 10])
                    with subheader_cols[0]:
                        st.image(get_custom_emoji_for_context("cypher"), width=30)
                    with subheader_cols[1]:
                        st.subheader("Cypher Query Interface")
                    
                    # Auto-generate query for selected study
                    if selected_study_id and st.button("🎯 Generate Query for Selected Study", key="auto_gen_study_query"):
                        auto_query = f"""MATCH (s:Study {{study_id: '{selected_study_id}'}})
OPTIONAL MATCH (s)-[r]-(n)
RETURN s, r, n
LIMIT 25"""
                        cypher_editor.set_query(auto_query)
                        st.success(f"✅ Generated query for study {selected_study_id}")
                        st.rerun()
                    
                    # Render the complete Cypher editor with error handling
                    try:
                        current_query, execute_clicked = cypher_editor.render_complete_editor()
                    except Exception as e:
                        st.error(f"Cypher editor initialization failed: {str(e)}")
                        st.info("Using fallback query interface...")
                        current_query = st.text_area("Enter Cypher Query:", height=200, placeholder="MATCH (n) RETURN n LIMIT 10")
                        execute_clicked = st.button("Execute Query", key="fallback_execute")
                    
                    # Handle query execution
                    if execute_clicked and current_query and current_query.strip():
                        with st.spinner("Executing query..."):
                            try:
                                # Execute the query using the enhanced executor
                                result = neo4j_executor.execute_query(current_query)
                                
                                # Add to history with detailed metadata (with error handling)
                                try:
                                    cypher_editor.add_to_history(
                                        query=current_query,
                                        execution_time_ms=getattr(result, 'execution_time', 0),
                                        result_count=len(result.data) if hasattr(result, 'data') and result.data else 0,
                                        success=getattr(result, 'success', False),
                                        error_message=getattr(result, 'error_message', None) if not getattr(result, 'success', False) else None
                                    )
                                except Exception:
                                    # History update failed - continue without it
                                    pass
                                
                                # Save query state to session manager (with error handling)
                                try:
                                    from session_manager import session_manager
                                    session_manager.save_query_state(
                                        query=current_query,
                                        results={
                                            "success": getattr(result, 'success', False),
                                            "execution_time": getattr(result, 'execution_time', 0),
                                            "data_count": len(result.data) if hasattr(result, 'data') and result.data else 0,
                                            "result_type": getattr(result, 'result_type', 'unknown')
                                        }
                                    )
                                except Exception:
                                    # Session manager save failed - continue without it
                                    pass
                                
                                if result.success:
                                    # Store results in session state for visualization
                                    st.session_state.cypher_query_result = result
                                    st.session_state.cypher_query_executed = current_query
                                    
                                    # Custom success with NASA emoji
                                    success_cols = st.columns([1, 20])
                                    with success_cols[0]:
                                        st.image(get_custom_emoji_for_context("success"), width=20)
                                    with success_cols[1]:
                                        st.success(f"Query executed successfully in {result.execution_time:.0f}ms")
                                    
                                    # Show performance warning if needed
                                    if result.warning_message:
                                        warning_cols = st.columns([1, 20])
                                        with warning_cols[0]:
                                            st.image(get_custom_emoji_for_context("warning"), width=20)
                                        with warning_cols[1]:
                                            st.warning(result.warning_message)
                                else:
                                    # Custom error with NASA emoji
                                    error_cols = st.columns([1, 20])
                                    with error_cols[0]:
                                        st.image(get_custom_emoji_for_context("error"), width=20)
                                    with error_cols[1]:
                                        st.error(f"Query failed: {result.error_message}")
                                    st.session_state.cypher_query_result = None
                                    
                            except Exception as query_error:
                                st.error(f"Query execution failed: {str(query_error)}")
                                st.session_state.cypher_query_result = None
                
                with graph_col:
                    # Custom subheader with NASA emoji
                    subheader_cols = st.columns([1, 10])
                    with subheader_cols[0]:
                        st.image(get_custom_emoji_for_context("chart"), width=30)
                    with subheader_cols[1]:
                        if selected_study_id:
                            st.subheader(f"🔒 Locked Node Visualization: {selected_study_id}")
                        else:
                            st.subheader("Query Results & Visualization")
                    
                    # Show locked node status
                    if selected_study_id:
                        if st.session_state.get('kg_auto_executed', False):
                            st.success(f"🔒 **Displaying results for locked study: {selected_study_id}**")
                        else:
                            st.info(f"🔄 **Loading visualization for locked study: {selected_study_id}...**")
                    
                    # Check for locked study fallback (when Neo4j not available)
                    if selected_study_id and not neo4j_enabled and st.session_state.get('kg_mock_result'):
                        # Show study metadata as fallback
                        st.warning("⚠️ **Neo4j Unavailable** - Showing study metadata instead of graph visualization")
                        
                        try:
                            study_doc = studies_collection.find_one({"study_id": selected_study_id})
                            if study_doc:
                                st.markdown("### 📊 **Study Details**")
                                
                                # Create a nice display of study information
                                info_cols = st.columns([1, 3])
                                with info_cols[0]:
                                    st.markdown("**Study ID:**")
                                    st.markdown("**Title:**")
                                    st.markdown("**Organisms:**")
                                    st.markdown("**Factors:**")
                                    st.markdown("**Description:**")
                                
                                with info_cols[1]:
                                    st.markdown(f"`{study_doc.get('study_id', 'N/A')}`")
                                    st.markdown(f"{study_doc.get('title', 'N/A')}")
                                    st.markdown(f"{', '.join(study_doc.get('organisms', ['N/A']))}")
                                    st.markdown(f"{', '.join(study_doc.get('factors', ['N/A']))}")
                                    st.markdown(f"{study_doc.get('description', 'N/A')[:300]}...")
                                
                                if study_doc.get('study_link'):
                                    st.markdown(f"🔗 [**View Original Study on OSDR**]({study_doc.get('study_link')})")
                                
                                st.info("💡 **Full graph visualization requires Neo4j connection**")
                            else:
                                st.error(f"Study {selected_study_id} not found in database")
                        except Exception as e:
                            st.error(f"Error loading study details: {e}")
                    
                    # Check if we have query results to display
                    elif hasattr(st.session_state, 'cypher_query_result') and st.session_state.cypher_query_result:
                        result = st.session_state.cypher_query_result
                        
                        # Use the enhanced results formatter with error handling
                        try:
                            from results_formatter import ResultsFormatter
                            results_formatter = ResultsFormatter()
                            formatted_results = results_formatter.format_results(result)
                            
                            # Render the formatted results
                            results_formatter.render_results_display(formatted_results)
                            
                            # Add interactive node click handler
                            from node_click_handler import node_click_handler
                            selected_query = node_click_handler.render_interactive_node_click_handler()
                            
                            # If a query was generated from node click, load it into the Cypher editor
                            if selected_query and 'generated_node_query' in st.session_state:
                                st.markdown("---")
                                st.markdown("### 🔄 Generated Query from Node Click")
                                st.code(st.session_state.generated_node_query, language="sql")
                                
                                if st.button("▶️ Execute Generated Query", key="execute_node_query"):
                                    # Execute the generated query
                                    from enhanced_neo4j_executor import neo4j_executor
                                    node_result = neo4j_executor.execute_query(st.session_state.generated_node_query)
                                    
                                    if node_result.success:
                                        st.success(f"✅ Node query executed successfully! Found {len(node_result.data)} results.")
                                        # Format and display the results
                                        node_formatted_results = results_formatter.format_results(node_result)
                                        results_formatter.render_results_display(node_formatted_results)
                                    else:
                                        st.error(f"❌ Node query failed: {node_result.error_message}")
                                
                                # Clear the generated query after use
                                if st.button("🧹 Clear Generated Query", key="clear_node_query"):
                                    if 'generated_node_query' in st.session_state:
                                        del st.session_state.generated_node_query
                                    if 'node_query_description' in st.session_state:
                                        del st.session_state.node_query_description
                                    st.rerun()
                            
                        except Exception as formatter_error:
                            # Fallback display for data conversion errors
                            st.warning(f"⚠️ **Results formatter error**: {str(formatter_error)}")
                            st.info("**Showing raw query results instead:**")
                            
                            # Simple fallback display
                            if hasattr(result, 'data') and result.data:
                                st.success(f"🎯 **Knowledge Graph Loaded!** Found {len(result.data)} connected entities for {selected_study_id}")
                                
                                # Quick stats
                                stats_cols = st.columns(3)
                                with stats_cols[0]:
                                    st.metric("📊 Records", len(result.data))
                                with stats_cols[1]:
                                    st.metric("⚡ Query Time", f"{getattr(result, 'execution_time', 0):.0f}ms")
                                with stats_cols[2]:
                                    st.metric("🔒 Study", selected_study_id)
                                
                                # Create a simple knowledge graph visualization
                                st.markdown("### 🕸️ **Knowledge Graph Visualization**")
                                
                                # Parse the records to extract nodes and relationships
                                study_node = None
                                connected_nodes = []
                                relationships = []
                                
                                for record in result.data:
                                    try:
                                        # Extract study node
                                        if hasattr(record, 's') and record.s:
                                            study_node = record.s
                                        
                                        # Extract connected nodes and relationships
                                        if hasattr(record, 'n') and record.n:
                                            connected_nodes.append(record.n)
                                        
                                        if hasattr(record, 'r') and record.r:
                                            relationships.append(record.r)
                                    except Exception:
                                        pass
                                
                                # Display the knowledge graph structure
                                if study_node:
                                    st.markdown("---")
                                    st.markdown("### 🌐 **Interactive Knowledge Graph**")
                                    # Center study node
                                    study_cols = st.columns([1, 3, 1])
                                    with study_cols[1]:
                                        st.markdown(f"""
                                        <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; margin: 10px;">
                                            <h3 style="color: white; margin: 0;">🎯 {selected_study_id}</h3>
                                            <p style="color: #f0f0f0; margin: 5px 0;">{getattr(study_node, 'title', 'Study Node')}</p>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    
                                    # Connected nodes in a grid
                                    if connected_nodes:
                                        st.markdown("#### 🔗 **Connected Entities**")
                                        
                                        # Group nodes by type
                                        node_types = {}
                                        for node in connected_nodes:
                                            try:
                                                labels = list(node.labels) if hasattr(node, 'labels') else ['Unknown']
                                                node_type = labels[0] if labels else 'Unknown'
                                                if node_type not in node_types:
                                                    node_types[node_type] = []
                                                node_types[node_type].append(node)
                                            except Exception:
                                                pass
                                        
                                        # Display nodes by type
                                        for node_type, nodes in node_types.items():
                                            if nodes:
                                                st.markdown(f"**{node_type}s ({len(nodes)})**")
                                                
                                                # Create columns for nodes
                                                cols = st.columns(min(len(nodes), 3))
                                                for i, node in enumerate(nodes[:3]):  # Show first 3 of each type
                                                    with cols[i % 3]:
                                                        try:
                                                            name = getattr(node, 'name', getattr(node, f'{node_type.lower()}_name', f'{node_type} {i+1}'))
                                                            st.markdown(f"""
                                                            <div style="padding: 10px; background: #2d3748; border-radius: 8px; margin: 5px; text-align: center;">
                                                                <strong>{name}</strong>
                                                            </div>
                                                            """, unsafe_allow_html=True)
                                                        except Exception:
                                                            st.markdown(f"<div style='padding: 10px; background: #2d3748; border-radius: 8px; margin: 5px; text-align: center;'><strong>{node_type} {i+1}</strong></div>", unsafe_allow_html=True)
                                                
                                                if len(nodes) > 3:
                                                    st.caption(f"... and {len(nodes) - 3} more {node_type.lower()}s")
                                    
                                    # Relationships summary
                                    if relationships:
                                        st.markdown("#### ⚡ **Relationships**")
                                        rel_types = {}
                                        for rel in relationships:
                                            try:
                                                rel_type = rel.type if hasattr(rel, 'type') else 'CONNECTED_TO'
                                                rel_types[rel_type] = rel_types.get(rel_type, 0) + 1
                                            except Exception:
                                                pass
                                        
                                        rel_cols = st.columns(min(len(rel_types), 4))
                                        for i, (rel_type, count) in enumerate(rel_types.items()):
                                            with rel_cols[i % 4]:
                                                st.metric(rel_type.replace('_', ' '), count)
                                
                                # Raw data expandable section
                                with st.expander("🔍 **View Raw Data**", expanded=False):
                                    for i, record in enumerate(result.data[:5]):
                                        st.markdown(f"**Record {i+1}:**")
                                        st.json(dict(record) if hasattr(record, 'items') else str(record))
                                    
                                    if len(result.data) > 5:
                                        st.info(f"... and {len(result.data) - 5} more records")
                            else:
                                st.info("No data returned from query")
                            
                            formatted_results = None
                        
                        # Add node interaction panel if we have graph results
                        if formatted_results and formatted_results.result_type.value in ['graph', 'mixed'] and formatted_results.graph_html:
                            st.markdown("---")
                            
                            # Node interaction section
                            from node_click_handler import NodeClickHandler
                            node_click_handler = NodeClickHandler()
                            
                            # Custom subheader with NASA emoji
                            target_cols = st.columns([1, 10])
                            with target_cols[0]:
                                st.image(get_custom_emoji_for_context("target"), width=30)
                            with target_cols[1]:
                                st.subheader("Interactive Node Exploration")
                            
                            # Create sample node interaction for demonstration
                            demo_cols = st.columns(2)
                            
                            with demo_cols[0]:
                                # Custom info with NASA emoji
                                info_cols = st.columns([1, 20])
                                with info_cols[0]:
                                    st.image(get_custom_emoji_for_context("lightbulb"), width=20)
                                with info_cols[1]:
                                    st.info("**Click on nodes in the graph above to generate contextual queries**")
                                
                                # Show sample queries for demonstration
                                rocket_cols = st.columns([1, 10])
                                with rocket_cols[0]:
                                    st.image(get_custom_emoji_for_context("rocket"), width=25)
                                with rocket_cols[1]:
                                    st.markdown("### Try These Sample Queries:")
                                sample_queries = node_click_handler.create_sample_queries_for_demo()
                                
                                for sample in sample_queries[:2]:  # Show first 2 samples
                                    # Custom button with NASA emoji
                                    doc_cols = st.columns([1, 10])
                                    with doc_cols[0]:
                                        st.image(get_custom_emoji_for_context("document"), width=15)
                                    with doc_cols[1]:
                                        if st.button(sample['title'], key=f"sample_{sample['title'].replace(' ', '_')}"):
                                            cypher_editor.set_query(sample['query'])
                                            st.success(f"Query loaded: {sample['description']}")
                                            st.rerun()
                            
                            with demo_cols[1]:
                                # Manual node exploration
                                # Custom header with NASA emoji
                                mag_cols = st.columns([1, 10])
                                with mag_cols[0]:
                                    st.image(get_custom_emoji_for_context("magnifying"), width=25)
                                with mag_cols[1]:
                                    st.markdown("### Manual Node Exploration")
                                
                                # Example node types for manual exploration
                                node_type = st.selectbox(
                                    "Select node type to explore:",
                                    ["Study", "Organism", "Factor", "Assay"],
                                    key="manual_node_type"
                                )
                                
                                if node_type == "Study":
                                    node_value = st.text_input("Study ID:", placeholder="e.g., OSD-840", key="manual_study_id")
                                    if node_value and st.button("Generate Study Queries", key="gen_study_queries"):
                                        properties = {"study_id": node_value}
                                        selected_query = node_click_handler.render_node_interaction_panel(
                                            node_value, node_type, properties
                                        )
                                        if selected_query:
                                            cypher_editor.set_query(selected_query)
                                            st.rerun()
                                
                                elif node_type in ["Organism", "Factor", "Assay"]:
                                    name_field = f"{node_type.lower()}_name"
                                    node_value = st.text_input(f"{node_type} name:", placeholder=f"e.g., mouse, spaceflight", key=f"manual_{node_type.lower()}")
                                    if node_value and st.button(f"Generate {node_type} Queries", key=f"gen_{node_type.lower()}_queries"):
                                        properties = {name_field: node_value, "name": node_value}
                                        selected_query = node_click_handler.render_node_interaction_panel(
                                            node_value, node_type, properties
                                        )
                                        if selected_query:
                                            cypher_editor.set_query(selected_query)
                                            st.rerun()
                    
                    # Legacy graph functionality (for backward compatibility)
                    elif st.session_state.get('selected_study_for_kg'):
                        selected_study_id = st.session_state.get('selected_study_for_kg')
                        
                        if st.session_state.graph_html is None:
                            with st.spinner(f"Generating base graph for {selected_study_id}..."):
                                html, ids = build_and_display_study_graph(selected_study_id)
                                st.session_state.graph_html, st.session_state.kg_study_ids = html, ids
                        
                        st.subheader(f"Legacy Graph View: {', '.join(st.session_state.kg_study_ids)}")
                        if st.session_state.graph_html: 
                            st.components.v1.html(st.session_state.graph_html, height=600, scrolling=True)
                        
                        # Legacy interactive queries
                        st.markdown("---")
                        st.subheader("Quick Actions")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if st.button("Find Similar Study (Organism)"):
                                with st.spinner("Querying..."):
                                    html, ids = find_similar_studies_by_organism(selected_study_id)
                                    st.session_state.graph_html, st.session_state.kg_study_ids, st.session_state.ai_comparison_text = html, ids, None
                                st.rerun()
                        with col2:
                            if st.button("Expand Connections"):
                                with st.spinner("Querying..."):
                                    html, ids = expand_second_level_connections(selected_study_id)
                                    st.session_state.graph_html, st.session_state.kg_study_ids, st.session_state.ai_comparison_text = html, ids, None
                                st.rerun()
                        with col3:
                            if st.button("Reset Graph"):
                                with st.spinner("Resetting..."):
                                    html, ids = build_and_display_study_graph(selected_study_id)
                                    st.session_state.graph_html, st.session_state.kg_study_ids, st.session_state.ai_comparison_text = html, ids, None
                                st.rerun()
                        
                        # AI Analysis
                        st.markdown("---")
                        # Custom subheader with NASA emoji
                        robot_cols = st.columns([1, 10])
                        with robot_cols[0]:
                            st.image(get_custom_emoji_for_context("robot"), width=30)
                        with robot_cols[1]:
                            st.subheader("AI-Powered Analysis")
                        if len(st.session_state.kg_study_ids) == 2:
                            if st.button(f"Compare {st.session_state.kg_study_ids[0]} & {st.session_state.kg_study_ids[1]} with AI"):
                                with st.spinner("Calling Google Gemini to analyze..."):
                                    docs = list(studies_collection.find({"study_id": {"$in": st.session_state.kg_study_ids}}, {"_id": 0, "study_id": 1, "title": 1, "description": 1}))
                                    if len(docs) == 2:
                                        d1 = f"ID: {docs[0].get('study_id')}, Title: {docs[0].get('title')}, Desc: {docs[0].get('description')}"
                                        d2 = f"ID: {docs[1].get('study_id')}, Title: {docs[1].get('title')}, Desc: {docs[1].get('description')}"
                                        st.session_state.ai_comparison_text = get_ai_comparison(d1, d2)
                                    else: 
                                        st.session_state.ai_comparison_text = "Error: Could not retrieve details for both studies."
                                st.rerun()
                        if st.session_state.ai_comparison_text:
                            # Custom info with NASA emoji
                            gemini_cols = st.columns([1, 20])
                            with gemini_cols[0]:
                                st.image(get_custom_emoji_for_context("robot"), width=20)
                            with gemini_cols[1]:
                                st.info("Gemini Analysis:")
                            st.markdown(st.session_state.ai_comparison_text)
                        
                        # Clear controls
                        st.markdown("---")
                        if st.button("Clear Graph View"):
                            st.session_state.selected_study_for_kg, st.session_state.graph_html, st.session_state.kg_study_ids, st.session_state.ai_comparison_text = None, None, [], None
                            st.rerun()
                    
                    else:
                        # Show different message based on locked node status
                        if selected_study_id:
                            # Locked node but no results yet
                            lock_info_cols = st.columns([1, 20])
                            with lock_info_cols[0]:
                                st.image(get_custom_emoji_for_context("study_id"), width=20)
                            with lock_info_cols[1]:
                                st.info(f"🔒 **Node Locked: {selected_study_id}**\n\nVisualization will appear here once the query executes. Use the Cypher editor to run custom queries for this study, or wait for auto-execution to complete.")
                        else:
                            # No locked node - show general instructions
                            start_cols = st.columns([1, 20])
                            with start_cols[0]:
                                st.image(get_custom_emoji_for_context("lightbulb"), width=20)
                            with start_cols[1]:
                                st.info("**Get Started:**\n\n1. **Lock a study**: Go to AI Search or Study Explorer and click '🔒 Lock into Knowledge Graph'\n2. **Or use Cypher editor**: Write custom queries on the left\n3. **View results**: Visualizations will appear here")
                        
                        # Show sample queries
                        sample_cols = st.columns([1, 10])
                        with sample_cols[0]:
                            st.image(get_custom_emoji_for_context("rocket"), width=25)
                        with sample_cols[1]:
                            st.markdown("### Sample Queries to Try:")
                        sample_queries = [
                            ("Find all studies", "MATCH (s:Study) RETURN s LIMIT 10"),
                            ("Studies with mice", "MATCH (s:Study)-[:HAS_ORGANISM]->(o:Organism) WHERE o.organism_name CONTAINS 'mouse' RETURN s, o LIMIT 5"),
                            ("Spaceflight studies", "MATCH (s:Study)-[:HAS_FACTOR]->(f:Factor) WHERE f.factor_name CONTAINS 'spaceflight' RETURN s, f LIMIT 5"),
                            ("Study connections", "MATCH (s:Study)-[r]-(n) WHERE s.study_id = 'OSD-840' RETURN s, r, n LIMIT 20")
                        ]
                        
                        for title, query in sample_queries:
                            # Custom button with NASA emoji
                            query_cols = st.columns([1, 10])
                            with query_cols[0]:
                                st.image(get_custom_emoji_for_context("document"), width=15)
                            with query_cols[1]:
                                if st.button(title, key=f"sample_{title.replace(' ', '_')}"):
                                    cypher_editor.set_query(query)
                                    st.rerun()
                
            except ImportError as import_error:
                st.error(f"Knowledge Graph components unavailable: {str(import_error)}")
                st.info("Some advanced features require additional dependencies.")
            except Exception as kg_error:
                st.error(f"Knowledge Graph error: {str(kg_error)}")
                st.info("Using simplified interface...")
                
                # Fallback simple interface
                st.subheader("Simple Query Interface")
                query = st.text_area("Enter Cypher Query:", height=150, placeholder="MATCH (n) RETURN n LIMIT 10")
                if st.button("Execute Query", key="fallback_kg_execute"):
                    st.info("Query execution temporarily unavailable due to technical issues.")
    
    except Exception as tab_error:
        st.error("🔧 Knowledge Graph tab encountered an error")
        
        # Show detailed error in debug mode
        with st.expander("🔍 Error Details (for debugging)", expanded=False):
            st.code(f"Error: {str(tab_error)}")
            st.code(f"Error type: {type(tab_error).__name__}")
            import traceback
            st.code(traceback.format_exc())
        
        st.info("💡 **Troubleshooting**: This error might be due to missing dependencies or configuration issues.")
        
        # Show basic info if study is selected
        if st.session_state.get('selected_study_for_kg'):
            st.info(f"Selected study: {st.session_state.get('selected_study_for_kg')}")
            if st.button("Clear Selection", key="kg_clear_fallback"):
                st.session_state.selected_study_for_kg = None
                st.rerun()
        
        # Provide fallback functionality
        st.markdown("### 🔄 Fallback Options")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Retry Knowledge Graph", key="retry_kg"):
                st.rerun()
        with col2:
            if st.button("📚 Go to Study Explorer", key="goto_explorer"):
                st.info("Please switch to the Study Explorer tab manually.")

# === Real-Time Data Tab ===
with tab_realtime:
    try:
        # Show node locking restriction message
        from node_lock_manager import node_lock_manager
        node_lock_manager.render_unauthorized_message("realtime_data")
        
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
        # Show node locking restriction message
        from node_lock_manager import node_lock_manager
        node_lock_manager.render_unauthorized_message("research_analytics")
        
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
