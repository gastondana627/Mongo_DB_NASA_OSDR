# streamlit_main_app.py (Definitive Version with Data Load Fix)

# === Python Standard Libraries ===
import os, sys, traceback, time, random

# === Third-Party Libraries ===
import streamlit as st
from dotenv import load_dotenv
from pymongo import MongoClient

# === Import Custom Functions ===
from scraper.formatter import extract_study_data
from scraper.utils import save_to_json, save_to_mongo
from neo4j_visualizer import (
    build_and_display_study_graph,
    find_similar_studies_by_organism,
    expand_second_level_connections
)

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

def get_random_emoji_image_path(subfolder=None, fallback_emoji="❓"):
    image_paths = get_all_emoji_image_paths(subfolder=subfolder)
    return random.choice(image_paths) if image_paths else fallback_emoji

# === Optional: Neo4j Integration ===
if 'build_and_display_study_graph' in globals():
    neo4j_enabled = True
else:
    neo4j_enabled = False

# === Streamlit Page Config ===
st.set_page_config(page_title="NASA OSDR Explorer", layout="wide", initial_sidebar_state="expanded")

# === Session State Initialization ===
if 'graph_html' not in st.session_state: st.session_state.graph_html = None
if 'scraping_in_progress' not in st.session_state: st.session_state.scraping_in_progress = False
if 'last_scrape_status_message' not in st.session_state: st.session_state.last_scrape_status_message = ""
if 'last_scrape_status_type' not in st.session_state: st.session_state.last_scrape_status_type = "info"
if 'selected_study_for_kg' not in st.session_state: st.session_state.selected_study_for_kg = None
if 'current_scrape_progress' not in st.session_state: st.session_state.current_scrape_progress = 0
if 'current_scrape_progress_text' not in st.session_state: st.session_state.current_scrape_progress_text = ""
if 'search_triggered_by_button' not in st.session_state: st.session_state.search_triggered_by_button = False
if 'app_title_emoji_left' not in st.session_state: st.session_state.app_title_emoji_left = get_random_emoji_image_path(fallback_emoji="🛰️")
if 'app_title_emoji_right' not in st.session_state: st.session_state.app_title_emoji_right = get_random_emoji_image_path(fallback_emoji="🚀")
if 'home_link_nav_icon' not in st.session_state: st.session_state.home_link_nav_icon = get_random_emoji_image_path(subfolder="home", fallback_emoji="🏠")

# === Load Environment Variables & MongoDB Setup ===
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI: st.error("❌ MONGO_URI is not set."); st.stop()

@st.cache_resource
def get_mongo_client():
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
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
    home_nav_label = "Home"
    home_nav_cols = st.columns([1, 4], gap="small")
    with home_nav_cols[0]:
        if isinstance(home_nav_icon_path, str) and (home_nav_icon_path.lower().endswith(VALID_IMAGE_EXTENSIONS) and os.path.exists(home_nav_icon_path)):
            st.image(home_nav_icon_path, width=24)
        else:
            st.markdown(f"<span style='font-size: 20px;'>{home_nav_icon_path}</span>", unsafe_allow_html=True)
    with home_nav_cols[1]:
        st.markdown(f"**{home_nav_label}**")
    st.markdown("---")
    st.header("Admin Tools")
    if st.button("🔄 Fetch OSD Metadata (Admin)", key="admin_fetch_metadata_btn_final_v3"):
        with st.spinner("Admin action... (Placeholder)"): time.sleep(1); st.info("Admin metadata fetch functionality is a placeholder.")
    st.markdown("---")
    if st.button("Clear App Cache & State", key="clear_cache_state_btn_final_v3"):
        st.cache_data.clear(); st.cache_resource.clear()
        keys_to_clear = ['scraping_in_progress', 'last_scrape_status_message', 'last_scrape_status_type', 'selected_study_for_kg', 'graph_html', 'app_title_emoji_left', 'app_title_emoji_right', 'home_link_nav_icon', 'current_scrape_progress', 'current_scrape_progress_text', 'search_triggered_by_button']
        for key in keys_to_clear:
            if key in st.session_state: del st.session_state[key]
        st.success("App cache & session state cleared."); st.rerun()

# === Main App Title ===
app_title_cols = st.columns([1, 8, 1], gap="small")
with app_title_cols[0]:
    title_emoji_left_path = st.session_state.app_title_emoji_left
    if isinstance(title_emoji_left_path, str) and (title_emoji_left_path.lower().endswith(VALID_IMAGE_EXTENSIONS) and os.path.exists(title_emoji_left_path)):
        st.image(title_emoji_left_path, width=50)
    else:
        st.markdown(f"<div style='text-align: center; font-size: 30px;'>{title_emoji_left_path}</div>", unsafe_allow_html=True)
app_title_cols[1].title("NASA OSDR Explorer", anchor=False)
with app_title_cols[2]:
    title_emoji_right_path = st.session_state.app_title_emoji_right
    if isinstance(title_emoji_right_path, str) and (title_emoji_right_path.lower().endswith(VALID_IMAGE_EXTENSIONS) and os.path.exists(title_emoji_right_path)):
        st.image(title_emoji_right_path, width=50)
    else:
        st.markdown(f"<div style='text-align: center; font-size: 30px;'>{title_emoji_right_path}</div>", unsafe_allow_html=True)
st.markdown("Extract, explore, and visualize data from NASA's Open Science Data Repository.")

# === Tabs ===
tab_names_list = ["🧬 Data Extract & Store", "🕸️ Knowledge Graph (Neo4j)", "📚 Study Explorer (MongoDB)"]
tab_extract, tab_kg, tab_explorer = st.tabs(tab_names_list)

# === Tab 1: Data Extraction & Store ===
with tab_extract:
    st.header("OSDR Study Data Extraction")
    st.markdown("Use the button below to scrape study data from the NASA OSDR website.")
    total_studies_on_site_tab1 = 550 # Updated to reflect latest scrape
    studies_per_page_tab1 = 25
    num_pages_to_scrape_tab1 = (total_studies_on_site_tab1 + studies_per_page_tab1 - 1) // studies_per_page_tab1 if total_studies_on_site_tab1 > 0 else 1
    
    status_message_area = st.empty()
    progress_area = st.empty()

    if not st.session_state.scraping_in_progress and st.session_state.last_scrape_status_message:
        if st.session_state.last_scrape_status_type == "success": status_message_area.success(st.session_state.last_scrape_status_message)
        elif st.session_state.last_scrape_status_type == "warning": status_message_area.warning(st.session_state.last_scrape_status_message)
        elif st.session_state.last_scrape_status_type == "error": status_message_area.error(st.session_state.last_scrape_status_message)
        else: status_message_area.info(st.session_state.last_scrape_status_message)
        if st.button("Clear Fetch Status", key="clear_fetch_status_tab1_button_final_v5"):
            st.session_state.last_scrape_status_message = ""; status_message_area.empty(); progress_area.empty(); st.rerun()
    elif st.session_state.scraping_in_progress:
         status_message_area.info("⚙️ Scraping is currently in progress...")
         with progress_area.container(): st.progress(st.session_state.get('current_scrape_progress', 0), text=st.session_state.get('current_scrape_progress_text', "Scraping..."))

    if st.button(f"🚀 Fetch All {total_studies_on_site_tab1} OSDR Studies ({num_pages_to_scrape_tab1} Pages)", key="fetch_studies_main_button_final_v5", disabled=st.session_state.scraping_in_progress):
        st.session_state.scraping_in_progress = True; st.session_state.last_scrape_status_message = ""
        status_message_area.empty(); progress_area.empty()
        all_studies_data = []
        try:
            with progress_area.container():
                st.session_state.current_scrape_progress = 0; st.session_state.current_scrape_progress_text = "Starting process..."
                local_progress_bar = st.progress(st.session_state.current_scrape_progress, text=st.session_state.current_scrape_progress_text)
            status_message_area.info(f"📡 Initializing Selenium... Target: {num_pages_to_scrape_tab1} pages.")
            st.session_state.current_scrape_progress = 5; st.session_state.current_scrape_progress_text = "Selenium initialized. Fetching data..."
            if local_progress_bar: local_progress_bar.progress(st.session_state.current_scrape_progress, text=st.session_state.current_scrape_progress_text)
            all_studies_data = extract_study_data(max_pages_to_scrape=num_pages_to_scrape_tab1)
            if all_studies_data:
                st.session_state.current_scrape_progress = 70; st.session_state.current_scrape_progress_text = f"{len(all_studies_data)} studies scraped. Saving JSON..."
                if local_progress_bar: local_progress_bar.progress(st.session_state.current_scrape_progress, text=st.session_state.current_scrape_progress_text)
                status_message_area.info(f"🔍 Scraping complete. Found {len(all_studies_data)} studies. Saving to JSON...")
                data_dir = "data";
                if not os.path.exists(data_dir): os.makedirs(data_dir)
                json_file_path = os.path.join(data_dir, "osdr_studies.json")
                save_to_json(all_studies_data, json_file_path)
                status_message_area.success(f"✅ All {len(all_studies_data)} studies saved to {json_file_path}")
                st.session_state.current_scrape_progress = 85; st.session_state.current_scrape_progress_text = "Saved to JSON. Saving to MongoDB..."
                if local_progress_bar: local_progress_bar.progress(st.session_state.current_scrape_progress, text=st.session_state.current_scrape_progress_text)
                
                saved_counts = save_to_mongo(all_studies_data, studies_collection)

                # --- THIS IS THE CORRECTED, ROBUST LOGIC ---
                msg_db = "Studies processed for MongoDB." # Default message
                if isinstance(saved_counts, dict):
                    # If we get a dictionary back, format a detailed message
                    msg_db = f"MongoDB: {saved_counts.get('inserted', 0)} inserted, {saved_counts.get('updated', 0)} updated."
                elif isinstance(saved_counts, int):
                    # If we get an integer back, format a simpler message
                    msg_db = f"{saved_counts} studies processed for MongoDB."
                # --- END OF FIX ---

                st.session_state.last_scrape_status_message = f"✅ All tasks complete! {msg_db}"; st.session_state.last_scrape_status_type = "success"
                status_message_area.success(st.session_state.last_scrape_status_message)
                st.session_state.current_scrape_progress = 100; st.session_state.current_scrape_progress_text = "All operations complete!"
                if local_progress_bar: local_progress_bar.progress(st.session_state.current_scrape_progress, text=st.session_state.current_scrape_progress_text)
                st.balloons()
            else:
                st.session_state.last_scrape_status_message = "⚠️ No studies were extracted."; st.session_state.last_scrape_status_type = "warning"
                status_message_area.warning(st.session_state.last_scrape_status_message)
                if 'local_progress_bar' in locals() and local_progress_bar: local_progress_bar.progress(100, text="Extraction attempt finished with no results.")
        except Exception as e_extract:
            st.session_state.last_scrape_status_message = f"❌ Error during data extraction: {e_extract}"; st.session_state.last_scrape_status_type = "error"
            status_message_area.error(st.session_state.last_scrape_status_message)
            st.text(traceback.format_exc())
            if 'local_progress_bar' in locals() and local_progress_bar is not None: local_progress_bar.progress(100, text="Error occurred.")
        finally:
            st.session_state.scraping_in_progress = False
            st.rerun()

# === Tab 2: Knowledge Graph (Neo4j) ===
with tab_kg:
    st.header("Study Knowledge Graph (Neo4j)")
    if not neo4j_enabled:
        st.error("❌ Neo4j features currently disabled.")
    else:
        st.markdown("Visualize connections for a study selected from the 'Study Explorer' tab.")
        selected_study_id = st.session_state.get('selected_study_for_kg')
        if selected_study_id:
            if st.session_state.graph_html is None:
                with st.spinner(f"Generating base graph for {selected_study_id}..."):
                    st.session_state.graph_html = build_and_display_study_graph(selected_study_id)
            st.subheader(f"Displaying Knowledge Graph for Study ID: {selected_study_id}")
            if st.session_state.graph_html:
                st.components.v1.html(st.session_state.graph_html, height=750, scrolling=True)
            st.markdown("---")
            st.subheader("Interactive Queries")
            st.caption("Run new queries to expand the graph and discover more connections.")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Find Similar Studies (by Organism)"):
                    with st.spinner("Querying for similar studies..."):
                        st.session_state.graph_html = find_similar_studies_by_organism(selected_study_id)
                    st.rerun()
            with col2:
                if st.button("Expand 2nd-Level Connections"):
                    with st.spinner("Querying for expanded connections..."):
                        st.session_state.graph_html = expand_second_level_connections(selected_study_id)
                    st.rerun()
            with col3:
                 if st.button("Reset to Default Graph"):
                    with st.spinner("Resetting graph..."):
                        st.session_state.graph_html = build_and_display_study_graph(selected_study_id)
                    st.rerun()
            st.markdown("---")
            st.subheader("🤖 AI-Powered Analysis")
            if st.button("Compare Studies with AI (Placeholder)"):
                st.info("AI analysis feature coming soon! This will use Google's Vertex AI to explain the relationships found in the graph.")
            st.markdown("---")
            if st.button("Clear Graph View / Select Another Study", key="clear_kg_view_button"):
                st.session_state.selected_study_for_kg = None
                st.session_state.graph_html = None
                st.rerun()
        else:
            st.info("To view a specific study's graph, please go to the 'Study Explorer (MongoDB)' tab and select one.")

# === Tab 3: Study Explorer (MongoDB) ===
with tab_explorer:
    st.header("Explore Studies in MongoDB")
    st.markdown("Filter and view detailed information for studies stored in the database.")
    filter_cols = st.columns([2, 2, 1])
    with filter_cols[0]: organism_filter_val = st.text_input("🔬 Organism contains", key="mongo_org_filter_val_final_v5", placeholder="e.g., Mus musculus")
    with filter_cols[1]: factor_filter_val = st.text_input("🧪 Factor contains", key="mongo_factor_filter_val_final_v5", placeholder="e.g., Spaceflight")
    with filter_cols[2]: study_id_filter_val = st.text_input("🆔 Study ID is", key="mongo_study_id_filter_val_final_v5", placeholder="e.g., OSD-840")
    query_mongo_explorer = {}
    if organism_filter_val: query_mongo_explorer["organisms"] = {"$regex": organism_filter_val.strip(), "$options": "i"}
    if factor_filter_val: query_mongo_explorer["factors"] = {"$regex": factor_filter_val.strip(), "$options": "i"}
    if study_id_filter_val: query_mongo_explorer["study_id"] = {"$regex": f"^{study_id_filter_val.strip()}$", "$options": "i"}
    if st.button("🔍 Search Studies", key="search_mongo_button_explorer_final_v5") or (query_mongo_explorer and not st.session_state.get('search_triggered_by_button', False)):
        st.session_state.search_triggered_by_button = True
        try:
            if not query_mongo_explorer:
                 st.info("Please enter filter criteria to search.")
            else:
                results_mongo_explorer = list(studies_collection.find(query_mongo_explorer).limit(50))
                st.metric(label="Studies Found", value=len(results_mongo_explorer))
                if not results_mongo_explorer: st.warning("No studies match your filter criteria.")
                else:
                    for item_study in results_mongo_explorer:
                        exp_title = f"{item_study.get('study_id', 'N/A')}: {item_study.get('title', 'No Title')}"
                        with st.expander(exp_title):
                            st.markdown(f"**Study ID:** {item_study.get('study_id', 'N/A')}")
                            if item_study.get('study_link'): st.markdown(f"[View Original Study on OSDR]({item_study.get('study_link')})")
                            exp_col1, exp_col2 = st.columns([3,1])
                            with exp_col1:
                                st.markdown(f"**Organisms:** {', '.join(item_study.get('organisms', [])) if item_study.get('organisms') else 'N/A'}")
                                st.markdown(f"**Factors:** {', '.join(item_study.get('factors', [])) if item_study.get('factors') else 'N/A'}")
                                st.markdown(f"**Assay Types:** {', '.join(item_study.get('assay_types', [])) if item_study.get('assay_types') else 'N/A'}")
                                st.markdown(f"**Release Date:** {item_study.get('release_date', 'N/A')}")
                            with exp_col2:
                                if item_study.get('image_url') and "no-image-icon" not in item_study.get('image_url'):
                                    st.image(item_study.get('image_url'), width=120, caption="Study Image")
                                else: st.caption("No image")
                            st.markdown(f"**Description:** {item_study.get('description', 'N/A')}")
                            st.markdown(f"**Highlights:** {item_study.get('highlights', 'N/A')}")
                            if neo4j_enabled:
                                if st.button("👁️ View Study Knowledge Graph", key=f"kg_view_button_tab3_{item_study.get('study_id')}_final_v5"):
                                    st.session_state.selected_study_for_kg = item_study.get('study_id')
                                    st.session_state.graph_html = None
                                    st.success(f"Study {st.session_state.selected_study_for_kg} selected. View in 'Knowledge Graph (Neo4j)' tab.")
        except Exception as e_mongo_explore:
            st.error(f"❌ MongoDB query failed: {e_mongo_explore}"); st.text(traceback.format_exc())
    elif not query_mongo_explorer:
        st.info("Enter filter criteria and click 'Search Studies' to explore the MongoDB data.")
    if 'search_triggered_by_button' in st.session_state : st.session_state.search_triggered_by_button = False

# === Optional CLI Functionality ===
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run_scraper":
        print("🚀 Running scraper pipeline from CLI...")
        if not mongo_client: print("❌ MongoDB client not initialized for CLI run.")
        else:
            cli_studies_collection_ref = studies_collection
            try:
                # ... CLI logic as before
                pass
            except Exception as e_cli_run:
                print(f"❌ Error in CLI scraper pipeline: {e_cli_run}"); traceback.print_exc()


