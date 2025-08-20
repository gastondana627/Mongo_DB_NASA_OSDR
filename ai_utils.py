# ai_utils.py

import streamlit as st
import os
import vertexai
import json
from vertexai.generative_models import GenerativeModel
from vertexai.language_models import TextEmbeddingModel
from google.oauth2 import service_account

# --- Centralized Vertex AI Initialization ---
_vertex_ai_initialized = False

def init_vertex_ai():
    """
    Initializes Vertex AI with credentials, handling both local and Streamlit Cloud environments.
    This function should be called once before any Vertex AI operations.
    """
    global _vertex_ai_initialized
    if _vertex_ai_initialized:
        return

    print("Attempting to initialize Vertex AI...")
    
    # Check if running in Streamlit's cloud environment
    if "GCP_PROJECT_ID" in st.secrets:
        print("Authenticating to GCP using Streamlit Secrets...")
        try:
            # Get credentials from Streamlit's secrets
            creds_json_str = st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"]
            creds_dict = json.loads(creds_json_str)
            credentials = service_account.Credentials.from_service_account_info(creds_dict)
            
            vertexai.init(
                project=st.secrets["GCP_PROJECT_ID"],
                location=st.secrets["GCP_LOCATION"],
                credentials=credentials
            )
            _vertex_ai_initialized = True
            print("Vertex AI initialized successfully from Streamlit Secrets.")
        except Exception as e:
            print(f"!!!!!!!! ERROR: Failed to initialize Vertex AI from Streamlit Secrets: {e}")
            st.error(f"Authentication Error: Could not initialize Vertex AI. Please check your Streamlit Secrets configuration. Details: {e}")
    else:
        # Running in a local environment, use .env variables
        print("Authenticating to GCP using local environment variables...")
        try:
            # For local, ensure GOOGLE_APPLICATION_CREDENTIALS points to your .json file in .env
            # And GCP_PROJECT_ID/GCP_LOCATION are also in your .env
            project_id = os.getenv("GCP_PROJECT_ID")
            location = os.getenv("GCP_LOCATION")
            if not project_id or not location:
                raise ValueError("GCP_PROJECT_ID and GCP_LOCATION must be set in your .env file for local development.")
            
            vertexai.init(project=project_id, location=location)
            _vertex_ai_initialized = True
            print("Vertex AI initialized successfully from local environment.")
        except Exception as e:
            print(f"!!!!!!!! ERROR: Failed to initialize Vertex AI locally: {e}")
            st.error(f"Authentication Error: Could not initialize Vertex AI locally. Ensure your .env file and ADC are configured correctly. Details: {e}")

# --- AI-Powered Functions ---

def get_ai_comparison(study_1_details: str, study_2_details: str) -> str:
    """Uses Gemini to generate a comparison between two studies."""
    init_vertex_ai() # Ensure Vertex AI is initialized
    
    if not _vertex_ai_initialized:
        return "Error: Vertex AI not initialized. Cannot perform comparison."
        
    model = GenerativeModel("gemini-1.5-flash-001")
    prompt = f"""
    You are a helpful NASA science assistant. Compare two scientific studies based on the provided details. Focus on their similarities and differences in methodology, organisms studied, and key factors investigated.

    STUDY 1: {study_1_details}
    ---
    STUDY 2: {study_2_details}
    ---
    Please provide your analysis in a concise paragraph.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error contacting Gemini for comparison: {e}"

def perform_vector_search(query_string: str, collection, limit=10):
    """Performs a vector search on the MongoDB collection."""
    init_vertex_ai() # Ensure Vertex AI is initialized
    
    if not _vertex_ai_initialized:
        return [{"error": "Vertex AI not initialized. Cannot perform vector search."}]
        
    model = TextEmbeddingModel.from_pretrained("text-embedding-004")
    query_embedding = model.get_embeddings([query_string])[0].values
    
    pipeline = [
        {"$vectorSearch": {
            "index": "vector_index", # Ensure this index exists in your MongoDB Atlas collection
            "path": "text_embedding", # The field containing the vectors
            "queryVector": query_embedding,
            "numCandidates": 150,
            "limit": limit
        }},
        {"$project": {
            "study_id": 1, "title": 1, "description": 1,
            "organisms": 1, "factors": 1, "study_link": 1,
            "score": { "$meta": "vectorSearchScore" }
        }}
    ]
    try:
        results = collection.aggregate(pipeline)
        return list(results)
    except Exception as e:
        print(f"An error occurred during vector search: {e}")
        return [{"error": f"Vector search failed: {e}"}]

def get_ai_summary(question: str, search_results: list) -> str:
    """Generates a 1-2 sentence summary from search results using Gemini."""
    init_vertex_ai() # Ensure Vertex AI is initialized
    
    if not _vertex_ai_initialized:
        return "Error: Vertex AI not initialized. Cannot generate summary."
        
    model = GenerativeModel("gemini-1.5-flash-001")
    
    # Create a concise context from the top results for the prompt
    context = ""
    for result in search_results[:3]: # Use top 3 results for context
        context += f"Title: {result.get('title', 'N/A')}\\nDescription: {result.get('description', 'N/A')}\\n\\n"

    prompt = f"""
    Based on the following search results for the user's question, provide a concise 1-2 sentence summary of the key findings or themes.

    User's Question: "{question}"
    Search Results Context:
    {context}
    Summary:
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error contacting Gemini for summary: {e}"



