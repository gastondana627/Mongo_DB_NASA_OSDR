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
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h2 style='text-align: center;'>OSDR Explorer</h2>", unsafe_allow_html=True)
        if st.session_state.home_link_nav_icon and os.path.exists(st.session_state.home_link_nav_icon):
            st.image(st.session_state.home_link_nav_icon, width=76)
    
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
    
    if neo4j_conn and neo4j_conn.connected:
        st.success("✅ Neo4j: Connected")
    else:
        st.info("⚠️ Neo4j: Offline (optional)")

# === Main App Title ===
app_title_cols = st.columns([1, 8, 1], gap="small")
with app_title_cols[0]:
    if st.session_state.app_title_emoji_left and os.path.exists(st.session_state.app_title_emoji_left):
        st.image(st.session_state.app_title_emoji_left, width=80)
app_title_cols[1].title("NASA OSDR Explorer", anchor=False)
with app_title_cols[2]:
    if st.session_state.app_title_emoji_right and os.path.exists(st.session_state.app_title_emoji_right):
        st.image(st.session_state.app_title_emoji_right, width=80)
st.markdown("Extract, explore, and visualize data from NASA's Open Science Data Repository.")

# === Enhanced Tabs for Research Value ===
tab_ai_search, tab_explorer, tab_kg, tab_realtime, tab_analytics, tab_ontology, tab_extract = st.tabs([
    "🔍 AI Semantic Search", 
    "📚 Study Explorer", 
    "🕸️ Knowledge Graph", 
    "🌍 Real-Time Data",
    "📊 Research Analytics", 
    "🧬 Ontology Browser",
    "⚙️ Data & Setup"
])

# === AI Semantic Search Tab (DISABLED - GCP permissions pending) ===
with tab_ai_search:
    st.info("ℹ️ **AI Vector Search Status**: Vector index setup in progress. The search functionality will be available once MongoDB Atlas vector search is configured.")
    # Custom header with NASA emoji
    header_cols = st.columns([1, 10])
    with header_cols[0]:
        st.image(get_custom_emoji_for_context("ai_search"), width=40)
    with header_cols[1]:
        st.header("AI-Powered Semantic Search")
    st.markdown("Ask a question in natural language to find the most conceptually related studies in the dataset.")
    user_question = st.text_area("Enter your research question:", height=100, placeholder="e.g., What are the effects of microgravity on the cardiovascular system of mammals?")

    if st.button("Search with AI", key="ai_search_button"):
        if user_question:
            try:
                with st.spinner("Searching for conceptually similar studies using Vertex AI and MongoDB..."):
                    st.session_state.ai_search_results = perform_vector_search(user_question, studies_collection)
            except Exception as e:
                st.error("⚠️ AI Search unavailable. GCP Vertex AI permissions are being updated. Try again in 5 minutes.")
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
    # Custom header with NASA emoji
    header_cols = st.columns([1, 10])
    with header_cols[0]:
        st.image(get_custom_emoji_for_context("knowledge_graph"), width=40)
    with header_cols[1]:
        st.header("Enhanced Knowledge Graph Explorer")
    if not neo4j_enabled: 
        # Custom error with NASA emoji
        error_cols = st.columns([1, 20])
        with error_cols[0]:
            st.image(get_custom_emoji_for_context("error"), width=20)
        with error_cols[1]:
            st.warning("⚠️ Neo4j Unavailable (Production Mode)")
        st.info("Knowledge Graph visualization requires Neo4j. Local deployment shows full relationship maps. Viewing study metadata instead...")
        
        if "selected_study" in st.session_state and st.session_state["selected_study"]:
            study = st.session_state["selected_study"]
            st.subheader(f"Study: {study.get('study_id', 'Unknown')}")
            st.write(f"**Title:** {study.get('title', 'N/A')}")
            st.write(f"**Description:** {study.get('description', 'N/A')[:500]}")
            st.caption("⚠️ Relationships unavailable without Neo4j")
        else:
            st.info("Select a study from AI Semantic Search or Study Explorer to view its metadata.")
    else:
        # Import the Cypher editor
        from cypher_editor import cypher_editor
        from enhanced_neo4j_executor import neo4j_executor
        
        # Create two-column layout: Cypher editor on left, graph on right
        editor_col, graph_col = st.columns([1, 2], gap="medium")
        
        with editor_col:
            # Custom subheader with NASA emoji
            subheader_cols = st.columns([1, 10])
            with subheader_cols[0]:
                st.image(get_custom_emoji_for_context("cypher"), width=30)
            with subheader_cols[1]:
                st.subheader("Cypher Query Interface")
            
            # Render the complete Cypher editor
            current_query, execute_clicked = cypher_editor.render_complete_editor()
            
            # Handle query execution
            if execute_clicked and current_query.strip():
                with st.spinner("Executing query..."):
                    # Execute the query using the enhanced executor
                    result = neo4j_executor.execute_query(current_query)
                    
                    # Add to history with detailed metadata
                    cypher_editor.add_to_history(
                        query=current_query,
                        execution_time_ms=result.execution_time,
                        result_count=len(result.data) if result.data else 0,
                        success=result.success,
                        error_message=result.error_message if not result.success else None
                    )
                    
                    # Save query state to session manager
                    from session_manager import session_manager
                    session_manager.save_query_state(
                        query=current_query,
                        results={
                            "success": result.success,
                            "execution_time": result.execution_time,
                            "data_count": len(result.data) if result.data else 0,
                            "result_type": getattr(result, 'result_type', 'unknown')
                        }
                    )
                    
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
        
        with graph_col:
            # Custom subheader with NASA emoji
            subheader_cols = st.columns([1, 10])
            with subheader_cols[0]:
                st.image(get_custom_emoji_for_context("chart"), width=30)
            with subheader_cols[1]:
                st.subheader("Query Results & Visualization")
            
            # Check if we have query results to display
            if hasattr(st.session_state, 'cypher_query_result') and st.session_state.cypher_query_result:
                result = st.session_state.cypher_query_result
                
                # Use the enhanced results formatter
                from results_formatter import results_formatter
                formatted_results = results_formatter.format_results(result)
                
                # Render the formatted results
                results_formatter.render_results_display(formatted_results)
                
                # Add node interaction panel if we have graph results
                if formatted_results.result_type.value in ['graph', 'mixed'] and formatted_results.graph_html:
                    st.markdown("---")
                    
                    # Node interaction section
                    from node_click_handler import node_click_handler
                    
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
                            else: st.session_state.ai_comparison_text = "Error: Could not retrieve details for both studies."
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
                # Custom info with NASA emoji
                start_cols = st.columns([1, 20])
                with start_cols[0]:
                    st.image(get_custom_emoji_for_context("lightbulb"), width=20)
                with start_cols[1]:
                    st.info("**Get Started:**\n\n1. Use the Cypher editor on the left to write custom queries\n2. Or find a study using the search tabs and select 'View Knowledge Graph'\n3. Click 'Execute Query' to see results here")
                
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

# === Real-Time Data Tab ===
with tab_realtime:
    try:
        from realtime_data_manager import realtime_manager
        realtime_manager.render_complete_dashboard()
    except ImportError:
        st.error("Real-time data manager not available")

# === Research Analytics Tab ===
with tab_analytics:
    try:
        from research_analytics import research_analytics
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
