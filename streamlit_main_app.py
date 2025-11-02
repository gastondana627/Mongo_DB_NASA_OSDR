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


import streamlit as st

# Custom CSS for sleek UI
st.markdown("""
<style>
:root {
    --accent: #00D9FF;
    --bg-dark: #0E1117;
}

h1, h2, h3 {
    font-family: 'IBM Plex Mono', 'Courier New', monospace;
    letter-spacing: 0.03em;
}

button {
    border-radius: 4px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 500 !important;
}

[data-testid="stExpander"] {
    border-radius: 6px !important;
}

.stTabs [data-baseweb="tab-list"] button {
    font-family: 'IBM Plex Mono', monospace;
    letter-spacing: 0.02em;
    border-bottom: 2px solid transparent;
}

.stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
    border-bottom-color: #00D9FF !important;
    color: #00D9FF !important;
}
</style>
""", unsafe_allow_html=True)

from dotenv import load_dotenv  # NOW UNCOMMENTED & USED
from pymongo import MongoClient
import certifi

# === LOAD .ENV IMMEDIATELY (BEFORE ANY ST CALLS) ===
load_dotenv()

# === Streamlit Page Config (MUST BE FIRST) ===
st.set_page_config(page_title="NASA OSDR Explorer", layout="wide", initial_sidebar_state="expanded")

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
        print("MongoDB connection successful!")
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
if 'cypher_editor' not in st.session_state: st.session_state['cypher_editor'] = {}
for key in ['graph_html', 'last_scrape_status_message', 'ai_comparison_text', 'selected_study_for_kg', 'mongo_query']:
    if key not in st.session_state: st.session_state[key] = None
for key in ['kg_study_ids', 'ai_search_results']:
    if key not in st.session_state: st.session_state[key] = []
for key in ['scraping_in_progress', 'search_triggered']:
    if key not in st.session_state: st.session_state[key] = False
if 'last_scrape_status_type' not in st.session_state: st.session_state['last_scrape_status_type'] = 'info'
if 'app_title_emoji_left' not in st.session_state: st.session_state.app_title_emoji_left = get_random_emoji_image_path()
if 'app_title_emoji_right' not in st.session_state: st.session_state.app_title_emoji_right = get_random_emoji_image_path()
if 'home_link_nav_icon' not in st.session_state: st.session_state.home_link_nav_icon = get_custom_emoji_for_context("home")

# === Enhanced Session Management Initialization (SURGICAL FIX #1: Defensive Loading) ===
try:
    from session_manager import session_manager
    # Restore previous session if available - but don't fail if it doesn't exist
    if 'cypher_session_restored' not in st.session_state:
        try:
            session_info = session_manager.restore_session()
        except KeyError:
            # Session state key doesn't exist yet - that's OK, first run
            pass
        st.session_state.cypher_session_restored = True
except ImportError:
    # session_manager module doesn't exist - continue without it
    pass

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
            self.uri = os.getenv("NEO4J_LOCAL_URI", "bolt://localhost:7687")
            self.user = os.getenv("NEO4J_LOCAL_USER", "neo4j")
            self.password = os.getenv("NEO4J_LOCAL_PASSWORD", "")
            self.driver = None
            self.connected = False
        
        def connect(self):
            try:
                self.driver = GraphDatabase.driver(
                    self.uri,
                    auth=(self.user, self.password),
                    encrypted="neo4j+s" in self.uri
                )
                with self.driver.session() as session:
                    session.run("RETURN 1")
                self.connected = True
                return True
            except Exception as e:
                print(f"⚡ Neo4j offline: {str(e)[:50]}")
                self.connected = False
                return False
        
        def close(self):
            if self.driver:
                self.driver.close()
    
    # Try to connect
    neo4j_conn = Neo4jConnection()
    print(f"→ Neo4j URI = {neo4j_conn.uri}")
    neo4j_enabled = neo4j_conn.connect()
    
except Exception as e:
    # Neo4j not available - continue without it
    print(f"ℹ️ Neo4j unavailable: {str(e)[:50]}")
    neo4j_enabled = False

# === Sidebar ===
with st.sidebar:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h2 style='text-align: center;'>OSDR Explorer</h2>", unsafe_allow_html=True)
        if st.session_state.home_link_nav_icon and os.path.exists(st.session_state.home_link_nav_icon):
            st.image(st.session_state.home_link_nav_icon, width=76, use_container_width=False)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h3 style='text-align: center;'>Admin Tools</h3>", unsafe_allow_html=True)
    
    if st.button("Clear App Cache & State", key="clear_cache_state_btn", use_container_width=True):
        st.cache_data.clear()
        st.cache_resource.clear()
        if neo4j_conn:
            neo4j_conn.close()
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.success("App cache & session state cleared.")
        st.rerun()
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h3 style='text-align: center;'>Database Status</h3>", unsafe_allow_html=True)
    
    if neo4j_enabled and neo4j_conn and neo4j_conn.connected:
        st.success("✅ Neo4j: Connected")
    else:
        st.info("⚡ Neo4j: Offline (optional)")

# === Main App Title ===
app_title_cols = st.columns([1, 8, 1], gap="small")
with app_title_cols[0]:
    if st.session_state.app_title_emoji_left and os.path.exists(st.session_state.app_title_emoji_left):
        st.image(st.session_state.app_title_emoji_left, width=80, use_container_width=False)
app_title_cols[1].title("NASA OSDR Explorer", anchor=False)
with app_title_cols[2]:
    if st.session_state.app_title_emoji_right and os.path.exists(st.session_state.app_title_emoji_right):
        st.image(st.session_state.app_title_emoji_right, width=80, use_container_width=False)
st.markdown("Extract, explore, and visualize data from NASA's Open Science Data Repository.")

# === Tabs ===
tab_ai_search, tab_explorer, tab_kg, tab_extract = st.tabs(["AI Semantic Search", "Study Explorer", "Knowledge Graph", "Data & Setup"])

# === AI Semantic Search Tab (DISABLED - GCP permissions pending) ===
with tab_ai_search:
    st.header("AI-Powered Semantic Search")
    st.markdown("Ask a question in natural language to find the most conceptually related studies in the dataset.")
    user_question = st.text_area("Enter your research question:", height=100, placeholder="e.g., What are the effects of microgravity on the cardiovascular system of mammals?")

    if st.button("Search with AI", key="ai_search_button"):
        if user_question:
            try:
                with st.spinner("Searching for conceptually similar studies using Vertex AI and MongoDB..."):
                    st.session_state.ai_search_results = perform_vector_search(user_question, studies_collection)
            except Exception as e:
                st.error(f"⚡ AI Search error: {str(e)}")
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
                                st.session_state.graph_html, st.session_state.kg_study_ids, st.session_state.ai_comparison_text = None, [], None
                                st.success(f"Study {item.get('study_id')} selected. Switch to the 'Knowledge Graph' tab to view.")

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

    if st.session_state.get('search_triggered') and 'mongo_query' in st.session_state:
        results = list(studies_collection.find(st.session_state.mongo_query).limit(50))
        st.metric(label="Studies Found", value=len(results))
        if not results and st.session_state.mongo_query: st.warning("No studies match your filter criteria.")
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

# === Knowledge Graph Tab ===
with tab_kg:
    st.subheader("Cypher Query Interface")
    
    # Query editor
    current_query = st.text_area("Enter Cypher Query:", height=150, placeholder="MATCH (n) RETURN n LIMIT 10")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Execute Query"):
            with st.spinner("Executing..."):
                try:
                    result = neo4j_executor.execute_query(current_query)
                    if result.success:
                        st.session_state.cypher_query_result = result
                        st.success(f"Query executed in {result.execution_time:.0f}ms")
                        if result.data:
                            st.json(result.data[:10])  # Show first 10 results
                    else:
                        st.error(f"Query error: {result.error_message}")
                except Exception as e:
                    st.error(f"Execution error: {str(e)}")
    
    with col2:
        if st.button("Clear Results"):
            st.session_state.cypher_query_result = None
            st.rerun()
    
    with col3:
        if st.button("Sample Query"):
            st.session_state.current_query = "MATCH (s:Study) RETURN s LIMIT 10"
            st.rerun()

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
                else: print("⚡ No studies were extracted in CLI run.")
            except Exception as e:
                print(f"❌ Error in CLI scraper pipeline: {e}"); traceback.print_exc()
