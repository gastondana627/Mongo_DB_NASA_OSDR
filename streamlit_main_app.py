# streamlit_main_app.py

import streamlit as st
import os
import traceback
from dotenv import load_dotenv
from pymongo import MongoClient
import sys 
import time # Added for placeholder simulation

# === Import Custom Functions ===
from scraper.formatter import extract_study_data
from scraper.utils import save_to_json, save_to_mongo
# Assuming these exist and are correctly defined in your project structure:
# from save_all_metadata import save_all_metadata # Placeholder
# from scraper.get_osds import get_all_osds       # Placeholder
# from scraper.save_osd_list import save_osd_list # Placeholder

# === Optional: Neo4j Integration ===
try:
    from neo4j_visualizer import build_and_display_study_graph, get_graph_data 
    neo4j_enabled = True
except ImportError:
    neo4j_enabled = False
    print("Neo4j visualizer module not found or error during import.")

# === Streamlit Page Config ===
st.set_page_config(page_title="NASA OSDR Explorer", layout="wide", initial_sidebar_state="expanded")

# === Session State Initialization ===
# (Session state initializations as in the previous full snippet you have - no changes needed here)
if 'scraping_in_progress' not in st.session_state:
    st.session_state.scraping_in_progress = False
if 'last_scrape_status_message' not in st.session_state:
    st.session_state.last_scrape_status_message = ""
if 'last_scrape_status_type' not in st.session_state: 
    st.session_state.last_scrape_status_type = "info"
if 'selected_study_for_kg' not in st.session_state:
    st.session_state.selected_study_for_kg = None


# === Load Environment Variables ===
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    st.error("❌ MONGO_URI is not set. Please check your .env file.")
    st.stop()

# === MongoDB Setup ===
@st.cache_resource 
def get_mongo_client():
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000) 
        client.admin.command('ping') 
        print("MongoDB connection successful!")
        return client
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        st.error(f"❌ MongoDB connection failed: {e}")
        return None

mongo_client = get_mongo_client()
if mongo_client:
    db = mongo_client["nasa_osdr"] 
    studies_collection = db["studies"] 
else:
    st.error("Halting app due to MongoDB connection failure.")
    st.stop()


# === Sidebar ===
with st.sidebar:
    st.header("🚀 OSDR Explorer")
    # Streamlit often creates a default link to the main app file.
    # If you have a multi-page app structure (e.g., using a 'pages/' directory),
    # st.page_link would be used for those. For a single file app, this might be redundant
    # or you can just use st.markdown for a home-like button if needed.
    # Let's simplify if this is the main page:
    st.markdown("#### 🏠 Home") # Simpler home indicator if it's the main page
    # If you later add a pages/ directory for a multi-page app:
    # st.page_link("streamlit_main_app.py", label="🏠 Home Base", icon="🏠")
    st.markdown("---")
    st.header("Admin Tools")
    if st.button("🔄 Fetch & Save OSD Metadata (Admin)", key="admin_fetch_metadata"):
        with st.spinner("Admin action: Fetching OSDs and saving metadata... (Placeholder)"):
            try:
                # --- THIS SECTION REQUIRES YOUR ACTUAL IMPLEMENTATION ---
                # For now, it will show the placeholder message.
                # Example:
                # if 'get_all_osds' in globals() and 'save_osd_list' in globals() and 'save_all_metadata' in globals():
                #     osds = get_all_osds()
                #     save_osd_list(osds)
                #     save_all_metadata(osds)
                #     st.success(f"Fetched and saved metadata for {len(osds)} OSDs!")
                # else:
                #     st.warning("Admin metadata functions (get_all_osds, etc.) are not fully imported or defined.")
                time.sleep(1) # Simulate work
                st.info("This Admin metadata fetch functionality is a placeholder and needs to be implemented.")
                # --- END OF SECTION REQUIRING IMPLEMENTATION ---
            except Exception as e:
                st.error(f"❌ Failed to execute admin metadata task: {e}")
                # st.exception(e) # Use this for more detailed error in Streamlit UI
    st.markdown("---")
    if st.button("Clear App Cache & State", key="clear_cache_button"): # Renamed slightly
        st.cache_data.clear()
        st.cache_resource.clear()
        keys_to_clear = ['scraping_in_progress', 'last_scrape_status_message', 
                         'last_scrape_status_type', 'selected_study_for_kg']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.success("Application cache and session state relevant to scraping/KG view have been cleared. Consider refreshing the page.")
        # st.experimental_rerun() # Use with caution, can cause loops if state isn't managed carefully

# === Main App Title ===
# (Title and markdown as before - no changes needed here)
st.title("🛰️ NASA OSDR | Knowledge Graph + Data Extractor 🚀")
st.markdown("Explore, extract, and visualize data from NASA's Open Science Data Repository.")

# === Tabs ===
# (Tab definitions as before - no changes needed here)
tab_names = [
    "🧬 Data Extract & Store",
    "🕸️ Knowledge Graph (Neo4j)",
    "📚 Study Explorer (MongoDB)"
]
tab_extract, tab_kg, tab_explorer = st.tabs(tab_names)


# === Tab 1: Data Extraction & Store ===
# (This section with st.empty() and progress bar logic is the one I provided in the previous response,
#  and should be used as is from that response - no new changes here beyond what was already given for st.empty)
with tab_extract:
    st.header("Extract Study Data from NASA OSDR")
    st.markdown("""
        Click the button below to initiate web scraping for OSDR studies.
        This will fetch study data using Selenium, save it to `data/osdr_studies.json`,
        and upsert it into the MongoDB database.
    """)
    
    total_studies_on_site = 548 
    studies_per_page = 25
    # Calculate num_pages_to_scrape more safely
    num_pages_to_scrape = (total_studies_on_site + studies_per_page - 1) // studies_per_page if total_studies_on_site > 0 else 1

    status_placeholder_tab1 = st.empty()
    progress_bar_placeholder_tab1 = st.empty()

    if not st.session_state.scraping_in_progress and st.session_state.last_scrape_status_message:
        if st.session_state.last_scrape_status_type == "success":
            status_placeholder_tab1.success(st.session_state.last_scrape_status_message)
        # ... (other status types as in previous full snippet) ...
        elif st.session_state.last_scrape_status_type == "warning":
            status_placeholder_tab1.warning(st.session_state.last_scrape_status_message)
        elif st.session_state.last_scrape_status_type == "error":
            status_placeholder_tab1.error(st.session_state.last_scrape_status_message)
        else:
            status_placeholder_tab1.info(st.session_state.last_scrape_status_message)

        if st.button("Clear Fetch Status", key="clear_fetch_status_tab1_button_v2"): # Ensure unique key
            st.session_state.last_scrape_status_message = ""
            status_placeholder_tab1.empty()
            progress_bar_placeholder_tab1.empty()
            st.experimental_rerun()
    elif st.session_state.scraping_in_progress:
         status_placeholder_tab1.info("⚙️ Scraping is currently in progress...")


    if st.button(f"🚀 Fetch All {total_studies_on_site} OSDR Studies ({num_pages_to_scrape} Pages)", 
                 key="fetch_studies_button_main_v2",  # Ensure unique key
                 disabled=st.session_state.scraping_in_progress):
        
        st.session_state.scraping_in_progress = True
        st.session_state.last_scrape_status_message = "" 
        status_placeholder_tab1.empty() 
        progress_bar_placeholder_tab1.empty()
        current_progress_bar = None # Initialize

        all_studies_data = []
        try:
            with progress_bar_placeholder_tab1.container():
                 current_progress_bar = st.progress(0, text="Starting process...")

            status_placeholder_tab1.info(f"📡 Initializing Selenium... Will attempt to scrape {num_pages_to_scrape} pages.")
            if current_progress_bar: current_progress_bar.progress(5, text="Selenium initialized. Fetching data...")
            
            all_studies_data = extract_study_data(max_pages_to_scrape=num_pages_to_scrape)
            
            if all_studies_data:
                status_placeholder_tab1.info(f"🔍 Scraping complete. Found {len(all_studies_data)} studies. Preparing to save...")
                if current_progress_bar: current_progress_bar.progress(70, text=f"{len(all_studies_data)} studies scraped. Saving to JSON...")
                
                data_dir = "data"
                if not os.path.exists(data_dir):
                    os.makedirs(data_dir)
                
                json_file_path = os.path.join(data_dir, "osdr_studies.json")
                save_to_json(all_studies_data, json_file_path) 
                status_placeholder_tab1.success(f"✅ All {len(all_studies_data)} studies saved to {json_file_path}")
                if current_progress_bar: current_progress_bar.progress(85, text="Saved to JSON. Saving to MongoDB...")
                
                # Ensure studies_collection is the correct MongoDB collection object
                saved_counts_details = save_to_mongo(all_studies_data, studies_collection) 
                
                msg = "Studies processed for MongoDB." 
                if isinstance(saved_counts_details, dict): # If save_to_mongo returns a dict
                    msg = f"MongoDB: {saved_counts_details.get('inserted',0)} inserted, {saved_counts_details.get('updated',0)} updated."
                elif isinstance(saved_counts_details, int) : 
                    msg = f"{saved_counts_details} studies effectively upserted/processed for MongoDB."

                st.session_state.last_scrape_status_message = f"✅ All tasks complete! {msg}"
                st.session_state.last_scrape_status_type = "success"
                status_placeholder_tab1.success(st.session_state.last_scrape_status_message)
                if current_progress_bar: current_progress_bar.progress(100, text="All operations complete!")
                st.balloons()
            else:
                st.session_state.last_scrape_status_message = "⚠️ No studies were extracted after attempting all pages."
                st.session_state.last_scrape_status_type = "warning"
                status_placeholder_tab1.warning(st.session_state.last_scrape_status_message)
                if current_progress_bar: current_progress_bar.progress(100, text="Extraction attempt finished with no results.")
        
        except Exception as e:
            st.session_state.last_scrape_status_message = f"❌ An error occurred during data extraction: {e}"
            st.session_state.last_scrape_status_type = "error"
            status_placeholder_tab1.error(st.session_state.last_scrape_status_message)
            st.text(traceback.format_exc())
            if 'current_progress_bar' in locals() and current_progress_bar is not None: 
                current_progress_bar.progress(100, text="Error occurred.")
        finally:
            st.session_state.scraping_in_progress = False
            st.experimental_rerun() # Rerun to update UI state after scraping finishes or errors


# === Tab 2: Knowledge Graph (Neo4j) ===
# (This section with st.session_state.selected_study_for_kg is from the previous full snippet - no new changes here)
with tab_kg:
    st.header("Explore Study Relationships (Neo4j)")
    if not neo4j_enabled:
        st.error("❌ Neo4j functionality is currently unavailable (neo4j_visualizer module not found or error).")
    else:
        st.markdown("Visualize connections for a selected study or view a general graph.")
        
        selected_study_id_kg = st.session_state.get('selected_study_for_kg') # Use .get for safety

        if selected_study_id_kg:
            st.subheader(f"Knowledge Graph for Study: {selected_study_id_kg}")
            with st.spinner(f"Generating graph for {selected_study_id_kg}..."):
                try:
                    # This function needs to be fully implemented in neo4j_visualizer.py
                    html_graph = build_and_display_study_graph(selected_study_id_kg) 
                    if html_graph:
                        st.components.v1.html(html_graph, height=650, scrolling=True)
                    else:
                        st.warning(f"Could not generate or display graph for {selected_study_id_kg}.")
                except NameError: 
                    st.error("Neo4j graph generation function (build_and_display_study_graph) is not available.")
                except Exception as e_kg_study:
                    st.error(f"Error generating study-specific graph: {e_kg_study}")
                    st.text(traceback.format_exc())
            
            if st.button("Clear Study Graph View", key="clear_study_kg_button_tab2"): # Unique key
                st.session_state.selected_study_for_kg = None
                st.experimental_rerun()
        else:
            st.info("Select '👁️ View Study Knowledge Graph' for a study in the 'Study Explorer' tab to see its specific connections here.")
            # Placeholder for general graph visualization
            # if st.button("📊 Visualize General Neo4j Relationships", key="general_kg_button_tab2_v2"): # Unique key
            #     st.info("General graph visualization to be implemented.")


# === Tab 3: Study Explorer (MongoDB) ===
# (This section with the "View Study Knowledge Graph" button is from the previous full snippet - no new changes here)
with tab_explorer:
    st.header("Explore NASA OSDR Studies from MongoDB")
    st.markdown("Filter and view studies stored in the MongoDB database.")

    # Use columns for filter inputs
    filter_col1, filter_col2, filter_col3 = st.columns([2,2,1])
    with filter_col1:
        organism_filter_input_exp = st.text_input("🔬 Filter by Organism", key="mongo_org_filter_explorer_input_v2", placeholder="e.g., Mus musculus")
    with filter_col2:
        factor_filter_input_exp = st.text_input("🧪 Filter by Factor", key="mongo_factor_filter_explorer_input_v2", placeholder="e.g., Spaceflight")
    with filter_col3: # Column for Study ID filter
        study_id_filter_input_exp = st.text_input("🆔 Filter by Study ID", key="mongo_study_id_filter_explorer_input_v2", placeholder="e.g., OSD-840")

    # Build query
    mongo_query_explorer_exp = {}
    if organism_filter_input_exp:
        mongo_query_explorer_exp["organisms"] = {"$regex": organism_filter_input_exp.strip(), "$options": "i"}
    if factor_filter_input_exp:
        mongo_query_explorer_exp["factors"] = {"$regex": factor_filter_input_exp.strip(), "$options": "i"}
    if study_id_filter_input_exp:
        # For Study ID, usually an exact match is better unless user expects partial
        mongo_query_explorer_exp["study_id"] = {"$regex": f"^{study_id_filter_input_exp.strip()}$", "$options": "i"} # Exact match, case insensitive


    if st.button("🔍 Search Studies in MongoDB", key="mongo_db_search_button_explorer_v2") or any(mongo_query_explorer_exp.values()):
        try:
            results_explorer = list(studies_collection.find(mongo_query_explorer_exp).limit(50)) # Limit for display
            st.metric(label="Studies Found", value=len(results_explorer))

            if not results_explorer:
                st.info("No studies match your current filter criteria in MongoDB.")
            else:
                for study_item_exp in results_explorer: 
                    expander_title = f"{study_item_exp.get('study_id', 'N/A')}: {study_item_exp.get('title', 'No Title')}"
                    with st.expander(expander_title):
                        # ... (study details display as before) ...
                        st.markdown(f"**Study ID:** {study_item_exp.get('study_id', 'N/A')}")
                        if study_item_exp.get('study_link'):
                            st.markdown(f"[View Study on OSDR]({study_item_exp.get('study_link')})")
                        
                        col_details1_exp, col_details2_exp = st.columns(2)
                        with col_details1_exp:
                            st.markdown(f"**Organisms:** {', '.join(study_item_exp.get('organisms', [])) if study_item_exp.get('organisms') else 'N/A'}")
                            st.markdown(f"**Factors:** {', '.join(study_item_exp.get('factors', [])) if study_item_exp.get('factors') else 'N/A'}")
                            st.markdown(f"**Assay Types:** {', '.join(study_item_exp.get('assay_types', [])) if study_item_exp.get('assay_types') else 'N/A'}")
                            st.markdown(f"**Release Date:** {study_item_exp.get('release_date', 'N/A')}")
                        
                        with col_details2_exp:
                            if study_item_exp.get('image_url') and "no-image-icon" not in study_item_exp.get('image_url'):
                                st.image(study_item_exp.get('image_url'), width=100, caption="Study Image")
                            else:
                                st.caption("No image available")
                        
                        st.markdown(f"**Description:** {study_item_exp.get('description', 'N/A')}")
                        st.markdown(f"**Highlights:** {study_item_exp.get('highlights', 'N/A')}")

                        if neo4j_enabled:
                            if st.button("👁️ View Study Knowledge Graph", key=f"kg_button_tab3_{study_item_exp.get('study_id')}_v2"): # Unique key
                                st.session_state.selected_study_for_kg = study_item_exp.get('study_id')
                                st.info(f"Knowledge graph for {st.session_state.selected_study_for_kg} can be viewed in the 'Knowledge Graph (Neo4j)' tab. Please navigate there.")
                                # st.experimental_rerun() # To potentially auto-switch or update UI if needed
                                
        except Exception as e:
            st.error(f"❌ MongoDB query failed: {e}")
            st.text(traceback.format_exc())
    else:
        st.info("Enter filter criteria or click search to view studies in MongoDB.")


# === Optional CLI Functionality (If you want to run scraper without Streamlit) ===
# (CLI part as before - no changes needed here from the previous full snippet)
if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "run_scraper":
    print("🚀 Running scraper pipeline from CLI...")
    if not mongo_client: # Check if mongo_client was initialized
        print("❌ MongoDB client not initialized for CLI run. Check MONGO_URI or connection.")
    else:
        cli_studies_collection = studies_collection # Use the collection from the main script scope
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
                
                saved_cli_counts_details = save_to_mongo(studies_cli, cli_studies_collection)
                
                msg_cli = "Studies processed for MongoDB from CLI."
                if isinstance(saved_cli_counts_details, dict):
                    msg_cli = f"MongoDB (CLI): {saved_cli_counts_details.get('inserted',0)} inserted, {saved_cli_counts_details.get('updated',0)} updated."
                elif isinstance(saved_cli_counts_details, int) :
                    msg_cli = f"{saved_cli_counts_details} studies effectively upserted to MongoDB from CLI run."
                print(f"✅ {msg_cli}")
            else:
                print("⚠️ No studies were extracted in CLI run.")
        except Exception as e_cli:
            print(f"❌ Error in CLI scraper pipeline: {e_cli}")
            traceback.print_exc()