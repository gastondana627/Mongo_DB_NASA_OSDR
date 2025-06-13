# streamlit_main_app.py (Definitive, Fully Corrected Version)

# === Python Standard Libraries ===
import os, sys, traceback, time, random

# === Third-Party Libraries ===
import streamlit as st
from dotenv import load_dotenv
from pymongo import MongoClient
import certifi

# === Import Custom Functions ===
from scraper.formatter import extract_study_data
from scraper.utils import save_to_json, save_to_mongo
from neo4j_visualizer import build_and_display_study_graph, find_similar_studies_by_organism, expand_second_level_connections
# from ai_utils import get_ai_comparison # Uncomment when ready

# === CUSTOM EMOJI HELPER FUNCTIONS ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EMOJI_ASSETS_DIR = os.path.join(BASE_DIR, "assets", "emojis")
VALID_IMAGE_EXTENSIONS = ('.svg', '.png', '.jpg', '.jpeg', '.gif')
@st.cache_data
def get_all_emoji_image_paths(subfolder=None):
    target_dir = EMOJI_ASSETS_DIR
    if subfolder: target_dir = os.path.join(EMOJI_ASSETS_DIR, subfolder)
    if not os.path.exists(target_dir): return []
    return [os.path.join(target_dir, f) for f in os.listdir(target_dir) if f.lower().endswith(VALID_IMAGE_EXTENSIONS) and os.path.isfile(os.path.join(target_dir, f))]
def get_random_emoji_image_path(subfolder=None, fallback_emoji="❓"):
    paths = get_all_emoji_image_paths(subfolder=subfolder)
    return random.choice(paths) if paths else fallback_emoji

# === Optional: Neo4j Integration ===
if 'build_and_display_study_graph' in globals(): neo4j_enabled = True
else: neo4j_enabled = False

# === Streamlit Page Config ===
st.set_page_config(page_title="NASA OSDR Explorer", layout="wide", initial_sidebar_state="expanded")

# === Session State Initialization ===
if 'graph_html' not in st.session_state: st.session_state.graph_html = None
if 'kg_study_ids' not in st.session_state: st.session_state.kg_study_ids = []
if 'ai_comparison_text' not in st.session_state: st.session_state.ai_comparison_text = None
if 'scraping_in_progress' not in st.session_state: st.session_state.scraping_in_progress = False
if 'last_scrape_status_message' not in st.session_state: st.session_state.last_scrape_status_message = ""
if 'selected_study_for_kg' not in st.session_state: st.session_state.selected_study_for_kg = None
if 'app_title_emoji_left' not in st.session_state: st.session_state.app_title_emoji_left = get_random_emoji_image_path()
if 'app_title_emoji_right' not in st.session_state: st.session_state.app_title_emoji_right = get_random_emoji_image_path()
if 'home_link_nav_icon' not in st.session_state: st.session_state.home_link_nav_icon = get_random_emoji_image_path(subfolder="home", fallback_emoji="🏠")

# === Load Environment Variables & MongoDB Setup ===
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI: st.error("❌ MONGO_URI not set."); st.stop()
@st.cache_resource
def get_mongo_client():
    try:
        ca = certifi.where(); client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000, tlsCAFile=ca)
        client.admin.command('ping'); print("MongoDB connection successful!")
        return client
    except Exception as e:
        st.error(f"❌ MongoDB connection failed: {e}"); return None
mongo_client = get_mongo_client()
if mongo_client:
    db = mongo_client["nasa_osdr"]; studies_collection = db["studies"]
else:
    st.error("Halting app due to MongoDB connection failure."); st.stop()

# === Sidebar ===
with st.sidebar:
    st.header("OSDR Explorer")
    home_nav_icon_path = st.session_state.home_link_nav_icon
    st.image(home_nav_icon_path, width=28)
    st.markdown("---")
    st.header("Admin Tools")
    if st.button("Clear App Cache & State", key="clear_cache_state_btn"):
        st.cache_data.clear(); st.cache_resource.clear()
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.success("App cache & session state cleared."); st.rerun()

# === Main App Title ===
app_title_cols = st.columns([1, 8, 1], gap="small")
with app_title_cols[0]: st.image(st.session_state.app_title_emoji_left, width=50)
app_title_cols[1].title("NASA OSDR Explorer", anchor=False)
with app_title_cols[2]: st.image(st.session_state.app_title_emoji_right, width=50)
st.markdown("Extract, explore, and visualize data from NASA's Open Science Data Repository.")

# === Tabs ===
tab_extract, tab_kg, tab_explorer = st.tabs(["🧬 Data Extract & Store", "🕸️ Knowledge Graph (Neo4j)", "📚 Study Explorer (MongoDB)"])

# === Tab 1: Data Extraction & Store ===
with tab_extract:
    st.header("OSDR Data Status")
    try:
        studies_count = studies_collection.count_documents({})
        if studies_count > 0:
            st.success(f"✅ Your MongoDB database is populated with **{studies_count}** studies.")
            st.info("You are ready to explore the data. To re-scrape, use the button below.")
            if st.button("🔄 Re-fetch All Data (will overwrite existing data)"):
                st.session_state.scraping_in_progress = True; st.rerun()
        else:
            st.warning("Your database is empty."); st.markdown("Use the button below to scrape study data from the NASA OSDR website.")
            if st.button(f"🚀 Fetch All OSDR Studies"):
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
                        st.session_state.last_scrape_status_message = f"✅ Success! Scraped {len(all_studies_data)} studies. {msg}"
                        st.session_state.last_scrape_status_type = "success"
                except Exception as e:
                    st.session_state.last_scrape_status_message = f"❌ Error: {e}"; st.session_state.last_scrape_status_type = "error"
                finally:
                    st.session_state.scraping_in_progress = False; st.rerun()
    except Exception as e: st.error(f"❌ An error occurred while checking the database status: {e}")

# === Tab 2: Knowledge Graph (Neo4j) ===
with tab_kg:
    st.header("Study Knowledge Graph (Neo4j)")
    if not neo4j_enabled: st.error("❌ Neo4j features currently disabled.")
    else:
        selected_study_id = st.session_state.get('selected_study_for_kg')
        if selected_study_id:
            if st.session_state.graph_html is None:
                with st.spinner(f"Generating base graph for {selected_study_id}..."):
                    html, ids = build_and_display_study_graph(selected_study_id)
                    st.session_state.graph_html, st.session_state.kg_study_ids = html, ids
            st.subheader(f"Displaying Knowledge Graph for: {', '.join(st.session_state.kg_study_ids)}")
            st.components.v1.html(st.session_state.graph_html, height=750, scrolling=True)
            st.markdown("---"); st.subheader("Interactive Queries")
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
            st.markdown("---"); st.subheader("🤖 AI-Powered Analysis")
            if len(st.session_state.kg_study_ids) == 2:
                if st.button(f"Compare {st.session_state.kg_study_ids[0]} & {st.session_state.kg_study_ids[1]} with AI"):
                    st.info("This feature is coming soon! It will use Google's Vertex AI.")
            if st.session_state.ai_comparison_text: st.info(st.session_state.ai_comparison_text)
            st.markdown("---")
            if st.button("Clear Graph View"):
                st.session_state.selected_study_for_kg, st.session_state.graph_html = None, None
                st.session_state.kg_study_ids, st.session_state.ai_comparison_text = [], None
                st.rerun()
        else:
            st.info("To view a graph, select a study in the 'Study Explorer (MongoDB)' tab.")

# === Tab 3: Study Explorer (MongoDB) ===
with tab_explorer:
    st.header("Explore Studies in MongoDB")
    st.markdown("Filter and view detailed information for studies stored in the database.")
    filter_cols = st.columns([2, 2, 1])
    with filter_cols[0]: organism_filter_val = st.text_input("🔬 Organism contains", key="mongo_org_filter", placeholder="e.g., Mus musculus")
    with filter_cols[1]: factor_filter_val = st.text_input("🧪 Factor contains", key="mongo_factor_filter", placeholder="e.g., Spaceflight")
    with filter_cols[2]: study_id_filter_val = st.text_input("🆔 Study ID is", key="mongo_study_id_filter", placeholder="e.g., OSD-840")
    if st.button("🔍 Search Studies", key="search_mongo_button"):
        query = {}
        if organism_filter_val: query["organisms"] = {"$regex": organism_filter_val.strip(), "$options": "i"}
        if factor_filter_val: query["factors"] = {"$regex": factor_filter_val.strip(), "$options": "i"}
        if study_id_filter_val: query["study_id"] = {"$regex": f"^{study_id_filter_val.strip()}$", "$options": "i"}
        st.session_state.mongo_query = query
        st.rerun()
    if 'mongo_query' in st.session_state:
        try:
            results = list(studies_collection.find(st.session_state.mongo_query).limit(50))
            st.metric(label="Studies Found", value=len(results))
            if not results and st.session_state.mongo_query: st.warning("No studies match your filter criteria.")
            for item_study in results:
                with st.expander(f"{item_study.get('study_id', 'N/A')}: {item_study.get('title', 'No Title')}"):
                    st.markdown(f"**Study ID:** {item_study.get('study_id', 'N/A')}")
                    if item_study.get('study_link'): st.markdown(f"[View Original Study on OSDR]({item_study.get('study_link')})")
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**Organisms:** {', '.join(item_study.get('organisms', []))}")
                        st.markdown(f"**Factors:** {', '.join(item_study.get('factors', []))}")
                    with col2:
                        if item_study.get('image_url') and "no-image-icon" not in item_study.get('image_url'):
                            st.image(item_study.get('image_url'), width=120)
                    if neo4j_enabled:
                        if st.button("👁️ View Study Knowledge Graph", key=f"kg_view_button_{item_study.get('study_id')}"):
                            st.session_state.selected_study_for_kg = item_study.get('study_id'); st.session_state.graph_html = None
                            st.success(f"Study {item_study.get('study_id')} selected. View in 'Knowledge Graph (Neo4j)' tab.")
        except Exception as e: st.error(f"❌ MongoDB query failed: {e}")


# === Optional CLI Functionality ===
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run_scraper":
        print("🚀 Running scraper pipeline from CLI...")
        if not mongo_client: print("❌ MongoDB client not initialized.")
        else:
            try:
                cli_studies_collection = mongo_client["nasa_osdr"]["studies"]
                num_pages = (550 + 24) // 25
                studies = extract_study_data(max_pages_to_scrape=num_pages)
                if studies:
                    save_to_json(studies, "data/osdr_studies_cli.json")
                    print(f"✅ Saved {len(studies)} studies to JSON.")
                    counts = save_to_mongo(studies, cli_studies_collection)
                    print(f"✅ MongoDB (CLI): {counts.get('inserted',0)} inserted, {counts.get('updated',0)} updated.")
                else:
                    print("⚠️ No studies were extracted in CLI run.")
            except Exception as e:
                print(f"❌ Error in CLI scraper pipeline: {e}"); traceback.print_exc()


