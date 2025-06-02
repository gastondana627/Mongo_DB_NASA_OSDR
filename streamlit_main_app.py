# streamlit_main_app.py

import streamlit as st
import os
import traceback
from dotenv import load_dotenv
from pymongo import MongoClient

# === Import Custom Functions ===
from scraper.formatter import extract_study_data
from scraper.utils import save_to_json, save_to_mongo
# Assuming these exist and are correctly defined in your project structure:
from save_all_metadata import save_all_metadata
from scraper.get_osds import get_all_osds
from scraper.save_osd_list import save_osd_list

# === Optional: Neo4j Integration ===
try:
    # Assuming this file exists and is correctly defined:
    from neo4j_visualizer import build_and_display_study_graph, get_graph_data # Updated import
    neo4j_enabled = True
except ImportError:
    neo4j_enabled = False
    print("Neo4j visualizer module not found or error during import.") # For server logs

# === Streamlit Page Config ===
st.set_page_config(page_title="NASA OSDR Explorer", layout="wide", initial_sidebar_state="expanded")

# === Session State Initialization ===
if 'scraping_in_progress' not in st.session_state:
    st.session_state.scraping_in_progress = False
if 'last_scrape_status_message' not in st.session_state:
    st.session_state.last_scrape_status_message = ""
if 'last_scrape_status_type' not in st.session_state: # "info", "success", "warning", "error"
    st.session_state.last_scrape_status_type = "info"
if 'selected_study_for_kg' not in st.session_state:
    st.session_state.selected_study_for_kg = None
if 'show_kg_in_tab3' not in st.session_state:
    st.session_state.show_kg_in_tab3 = False


# === Load Environment Variables ===
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    st.error("❌ MONGO_URI is not set. Please check your .env file.")
    st.stop()

# === MongoDB Setup ===
@st.cache_resource # Cache the client and db connection
def get_mongo_client():
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000) # Add timeout
        client.admin.command('ping') # Verify connection
        print("MongoDB connection successful!")
        return client
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        st.error(f"❌ MongoDB connection failed: {e}")
        return None

mongo_client = get_mongo_client()
if mongo_client:
    db = mongo_client["nasa_osdr"] # Your database name
    studies_collection = db["studies"] # Your collection name
else:
    st.error("Halting app due to MongoDB connection failure.")
    st.stop()


# === Sidebar ===
with st.sidebar:
    st.header("🚀 OSDR Explorer")
    st.page_link("streamlit_main_app.py", label="🏠 Home", icon="🏠")
    st.markdown("---")
    st.header("Admin Tools")
    if st.button("🔄 Fetch & Save OSD Metadata (Admin)", key="admin_fetch_metadata"):
        with st.spinner("Fetching OSDs and saving metadata... (Placeholder)"):
            try:
                # osds = get_all_osds()
                # save_osd_list(osds)
                # save_all_metadata(osds)
                # st.success(f"Fetched and saved metadata for {len(osds)} OSDs!")
                time.sleep(2) # Simulate work
                st.info("Admin metadata fetch functionality is a placeholder.")
            except Exception as e:
                st.error("❌ Failed to fetch/save OSD metadata.")
                st.exception(e)
    st.markdown("---")
    if st.button("Clear All Cached Data & State", key="clear_cache_button"):
        st.cache_data.clear()
        st.cache_resource.clear()
        for key in list(st.session_state.keys()): # Clear specific session state keys if needed
            if key not in ['some_persistent_state_if_any']: # Example to keep some state
                del st.session_state[key]
        st.success("Application cache and session state cleared. Please refresh if needed.")
        st.experimental_rerun()


# === Main App Title ===
st.title("🛰️ NASA OSDR | Knowledge Graph + Data Extractor 🚀")
st.markdown("Explore, extract, and visualize data from NASA's Open Science Data Repository.")

# === Tabs ===
# Initialize selected_tab in session_state if it doesn't exist
if 'selected_tab' not in st.session_state:
    st.session_state.selected_tab = "🧬 Data Extract & Store"

# Create tabs and update session state when a tab is selected
selected_tab_name = st.tabs([
    "🧬 Data Extract & Store",
    "🕸️ Knowledge Graph (Neo4j)",
    "📚 Study Explorer (MongoDB)"
])
# This part is tricky with st.tabs as it doesn't directly return the selected tab name easily to store
# For now, we'll manage tab content visibility based on button clicks in other tabs if needed.

tab_extract, tab_kg, tab_explorer = selected_tab_name


# === Tab 1: Data Extraction & Store ===
with tab_extract:
    st.header("Extract Study Data from NASA OSDR")
    st.markdown("""
        Click the button below to initiate web scraping for OSDR studies.
        This will fetch study data using Selenium, save it to `data/osdr_studies.json`,
        and upsert it into the MongoDB database.
    """)
    
    total_studies_on_site = 548 
    studies_per_page = 25
    num_pages_to_scrape = (total_studies_on_site + studies_per_page - 1) // studies_per_page

    # Placeholders for dynamic messages and progress bar
    status_placeholder_tab1 = st.empty()
    progress_bar_placeholder_tab1 = st.empty()

    if st.session_state.scraping_in_progress:
        status_placeholder_tab1.info("⚙️ Scraping is currently in progress from a previous action...")
    elif st.session_state.last_scrape_status_message: # Show last status if not scraping
        if st.session_state.last_scrape_status_type == "success":
            status_placeholder_tab1.success(st.session_state.last_scrape_status_message)
        elif st.session_state.last_scrape_status_type == "warning":
            status_placeholder_tab1.warning(st.session_state.last_scrape_status_message)
        elif st.session_state.last_scrape_status_type == "error":
            status_placeholder_tab1.error(st.session_state.last_scrape_status_message)
        else:
            status_placeholder_tab1.info(st.session_state.last_scrape_status_message)
        
        if st.button("Clear Last Fetch Status", key="clear_fetch_status_tab1"):
            st.session_state.last_scrape_status_message = ""
            st.session_state.scraping_in_progress = False # Ensure this is reset
            status_placeholder_tab1.empty()
            progress_bar_placeholder_tab1.empty()
            st.experimental_rerun()


    if st.button(f"🚀 Fetch All {total_studies_on_site} OSDR Studies ({num_pages_to_scrape} Pages)", 
                 key="fetch_studies_button_main", 
                 disabled=st.session_state.scraping_in_progress):
        
        st.session_state.scraping_in_progress = True
        st.session_state.last_scrape_status_message = "" # Clear previous messages
        status_placeholder_tab1.empty() # Clear previous messages from placeholder too
        progress_bar_placeholder_tab1.empty()

        all_studies_data = []
        try:
            with progress_bar_placeholder_tab1.container():
                 progress_bar = st.progress(0, text="Starting process...")

            status_placeholder_tab1.info(f"📡 Initializing Selenium... Will attempt to scrape {num_pages_to_scrape} pages.")
            progress_bar.progress(5, text="Selenium initialized. Fetching data...")
            
            all_studies_data = extract_study_data(max_pages_to_scrape=num_pages_to_scrape)
            
            if all_studies_data:
                status_placeholder_tab1.info(f"🔍 Scraping complete. Found {len(all_studies_data)} studies. Saving to JSON...")
                progress_bar.progress(70, text=f"{len(all_studies_data)} studies scraped. Saving to JSON...")
                
                data_dir = "data"
                if not os.path.exists(data_dir):
                    os.makedirs(data_dir)
                
                json_file_path = os.path.join(data_dir, "osdr_studies.json")
                save_to_json(all_studies_data, json_file_path)
                status_placeholder_tab1.success(f"✅ {len(all_studies_data)} studies saved to {json_file_path}")
                progress_bar.progress(85, text="Saved to JSON. Saving to MongoDB...")
                
                saved_counts = save_to_mongo(all_studies_data, studies_collection) # Expects dict like {"inserted": x, "updated": y} or just a count
                
                if isinstance(saved_counts, dict):
                    msg = f"{saved_counts.get('inserted',0)} inserted, {saved_counts.get('updated',0)} updated in MongoDB."
                elif isinstance(saved_counts, int) :
                    msg = f"{saved_counts} studies effectively upserted to MongoDB."
                else:
                    msg = "Studies processed for MongoDB."

                st.session_state.last_scrape_status_message = f"✅ All tasks complete! {msg}"
                st.session_state.last_scrape_status_type = "success"
                status_placeholder_tab1.success(st.session_state.last_scrape_status_message)
                progress_bar.progress(100, text="All operations complete!")
                st.balloons()
            else:
                st.session_state.last_scrape_status_message = "⚠️ No studies were extracted after attempting all pages."
                st.session_state.last_scrape_status_type = "warning"
                status_placeholder_tab1.warning(st.session_state.last_scrape_status_message)
                progress_bar.progress(100, text="Extraction attempt finished with no results.")
        
        except Exception as e:
            st.session_state.last_scrape_status_message = f"❌ An error occurred during data extraction: {e}"
            st.session_state.last_scrape_status_type = "error"
            status_placeholder_tab1.error(st.session_state.last_scrape_status_message)
            st.text(traceback.format_exc())
            if 'progress_bar' in locals(): 
                progress_bar.progress(100, text="Error occurred.")
        finally:
            st.session_state.scraping_in_progress = False
            # No automatic rerun here, let user click "Clear Fetch Status" or another action
            # st.experimental_rerun() # Can cause loop if not careful

# === Tab 2: Knowledge Graph (Neo4j) ===
with tab_kg:
    st.header("Explore Study Relationships (Neo4j)")
    if not neo4j_enabled:
        st.error("❌ Neo4j functionality is currently unavailable (neo4j_visualizer module not found or error).")
    else:
        st.markdown("Visualize connections for a selected study from the 'Study Explorer' tab or view a general graph.")
        
        if st.session_state.selected_study_for_kg:
            st.subheader(f"Knowledge Graph for Study: {st.session_state.selected_study_for_kg}")
            with st.spinner(f"Generating graph for {st.session_state.selected_study_for_kg}..."):
                try:
                    # This function needs to be implemented in neo4j_visualizer.py
                    # It should query Neo4j for the subgraph of selected_study_for_kg
                    # and return the HTML for the pyvis graph.
                    html_graph = build_and_display_study_graph(st.session_state.selected_study_for_kg) 
                    if html_graph:
                        st.components.v1.html(html_graph, height=650, scrolling=True)
                    else:
                        st.warning(f"Could not generate or display graph for {st.session_state.selected_study_for_kg}.")
                except Exception as e_kg_study:
                    st.error(f"Error generating study-specific graph: {e_kg_study}")
                    st.text(traceback.format_exc())
            
            if st.button("Clear Study Graph", key="clear_study_kg"):
                st.session_state.selected_study_for_kg = None
                st.experimental_rerun()
        else:
            st.info("Select '👁️ View Knowledge Graph' for a study in the 'Study Explorer' tab to see its specific connections.")
            if st.button("📊 Visualize General Neo4j Relationships", key="general_kg_button"):
                with st.spinner("Fetching general graph data and rendering visualization..."):
                    try:
                        graph_data_results = get_graph_data() 
                        if graph_data_results:
                            # display_graph needs to be adapted to take general data and render it
                            # For now, let's assume it also produces HTML similar to build_and_display_study_graph
                            general_html_graph = display_graph(graph_data_results) # You might need to adapt display_graph
                            if general_html_graph:
                                st.components.v1.html(general_html_graph, height=650, scrolling=True)
                                st.success("✅ General graph displayed.")
                            else:
                                st.warning("⚠️ Could not display general graph.")
                        else:
                            st.warning("⚠️ No general graph data returned from Neo4j.")
                    except Exception as e_kg_general:
                        st.error(f"❌ Error visualizing general Neo4j graph: {e_kg_general}")
                        st.text(traceback.format_exc())

# === Tab 3: Study Explorer (MongoDB) ===
with tab_explorer:
    st.header("Explore NASA OSDR Studies from MongoDB")
    st.markdown("Filter and view studies stored in the MongoDB database.")

    col1_filter, col2_filter = st.columns(2)
    with col1_filter:
        organism_filter_input = st.text_input("🔬 Filter by Organism", key="mongo_org_filter_explorer", placeholder="e.g., Mus musculus")
    with col2_filter:
        factor_filter_input = st.text_input("🧪 Filter by Factor", key="mongo_factor_filter_explorer", placeholder="e.g., Spaceflight")

    study_id_filter_input = st.text_input("🆔 Filter by Study ID (OSD-XXX)", key="mongo_study_id_filter_explorer")

    mongo_query_explorer = {}
    if organism_filter_input:
        mongo_query_explorer["organisms"] = {"$regex": organism_filter_input.strip(), "$options": "i"}
    if factor_filter_input:
        mongo_query_explorer["factors"] = {"$regex": factor_filter_input.strip(), "$options": "i"}
    if study_id_filter_input:
        mongo_query_explorer["study_id"] = {"$regex": study_id_filter_input.strip(), "$options": "i"}

    # Display results dynamically or with a button
    # For simplicity, results update as filters change if any filter is active.
    # You might prefer an explicit search button for performance with large datasets.
    
    if mongo_query_explorer: # Only query if there's at least one filter criteria
        try:
            results_explorer = list(studies_collection.find(mongo_query_explorer).limit(50)) # Limit results
            st.metric(label="Studies Found", value=len(results_explorer))

            if not results_explorer:
                st.info("No studies match your current filter criteria in MongoDB.")
            else:
                for study_item in results_explorer:
                    expander_title = f"{study_item.get('study_id', 'N/A')}: {study_item.get('title', 'No Title')}"
                    with st.expander(expander_title):
                        st.markdown(f"**Study ID:** {study_item.get('study_id', 'N/A')}")
                        if study_item.get('study_link'):
                            st.markdown(f"[View Study on OSDR]({study_item.get('study_link')})")
                        
                        # Display data in columns for better layout
                        col_details1, col_details2 = st.columns(2)
                        with col_details1:
                            st.markdown(f"**Organisms:** {', '.join(study_item.get('organisms', [])) if study_item.get('organisms') else 'N/A'}")
                            st.markdown(f"**Factors:** {', '.join(study_item.get('factors', [])) if study_item.get('factors') else 'N/A'}")
                            st.markdown(f"**Assay Types:** {', '.join(study_item.get('assay_types', [])) if study_item.get('assay_types') else 'N/A'}")
                            st.markdown(f"**Release Date:** {study_item.get('release_date', 'N/A')}")
                        
                        with col_details2:
                            if study_item.get('image_url') and "no-image-icon" not in study_item.get('image_url'):
                                st.image(study_item.get('image_url'), width=100, caption="Study Image")
                            else:
                                st.caption("No image available")
                        
                        st.markdown(f"**Description:** {study_item.get('description', 'N/A')}")
                        st.markdown(f"**Highlights:** {study_item.get('highlights', 'N/A')}")
                        
                        if neo4j_enabled:
                            if st.button("👁️ View Study Knowledge Graph", key=f"kg_button_{study_item.get('study_id')}"):
                                st.session_state.selected_study_for_kg = study_item.get('study_id')
                                st.session_state.show_kg_in_tab3 = False # Ensure it shows in Tab 2
                                # st.experimental_set_query_params(tab="Knowledge Graph (Neo4j)") # This is not standard for st.tabs
                                st.info(f"Knowledge graph for {st.session_state.selected_study_for_kg} will be shown in the 'Knowledge Graph (Neo4j)' tab. Please navigate there.")
                                # A more direct way to switch tabs isn't built-in, user has to click.
                                # Consider displaying graph in an st.dialog or st.expander here if preferred for "in-place" view.
                                
        except Exception as e:
            st.error(f"❌ MongoDB query failed: {e}")
            st.text(traceback.format_exc())
    else:
        st.info("Enter filter criteria to search studies in MongoDB.")


# === Optional CLI Functionality ===
if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "run_scraper":
    print("🚀 Running scraper pipeline from CLI...")
    # ... (CLI logic as before, ensure mongo_client is available or re-init for CLI if needed) ...
    if mongo_client:
        cli_db = mongo_client["nasa_osdr"]
        cli_collection = cli_db["studies"]
        try:
            num_pages_cli = (548 + 25 - 1) // 25 
            studies_cli = extract_study_data(max_pages_to_scrape=num_pages_cli) 
            if studies_cli:
                data_dir_cli = "data"
                if not os.path.exists(data_dir_cli):
                    os.makedirs(data_dir_cli)
                json_file_path_cli = os.path.join(data_dir_cli, "osdr_studies_cli_output.json")
                save_to_json(studies_cli, json_file_path_cli)
                print(f"✅ Saved {len(studies_cli)} studies to {json_file_path_cli}")
                
                saved_cli_counts = save_to_mongo(studies_cli, cli_collection)
                if isinstance(saved_cli_counts, dict):
                    print(f"✅ MongoDB: {saved_cli_counts.get('inserted',0)} inserted, {saved_cli_counts.get('updated',0)} updated from CLI.")
                elif isinstance(saved_cli_counts, int):
                     print(f"✅ {saved_cli_counts} studies effectively upserted to MongoDB from CLI run.")
                else:
                    print("✅ Studies processed for MongoDB from CLI run.")
            else:
                print("⚠️ No studies were extracted in CLI run.")
        except Exception as e_cli:
            print(f"❌ Error in CLI scraper pipeline: {e_cli}")
            traceback.print_exc()
    else:
        print("MongoDB client not available for CLI run.")