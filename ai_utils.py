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
    """
    global _vertex_ai_initialized
    if _vertex_ai_initialized:
        return

    print("Attempting to initialize Vertex AI...")
    
    # Check if running in Streamlit's cloud environment by looking for the specific secret
    if "GOOGLE_APPLICATION_CREDENTIALS_JSON" in st.secrets:
        print("Authenticating to GCP using Streamlit Secrets...")
        try:
            creds_json_str = st.secrets["GOOGLE_APPLICATION_CREDENTIALS_JSON"] # <--- CORRECTED KEY
            creds_dict = json.loads(creds_json_str)
            credentials = service_account.Credentials.from_service_account_info(creds_dict)
            
            vertexai.init(
                project=st.secrets.get("GCP_PROJECT_ID"),
                location=st.secrets.get("GCP_LOCATION"),
                credentials=credentials
            )
            _vertex_ai_initialized = True
            print("Vertex AI initialized successfully from Streamlit Secrets.")
        except Exception as e:
            st.error(f"Authentication Error from Secrets: {e}")
    else:
        # Running in a local environment, use .env variables
        print("Authenticating to GCP using local environment variables...")
        try:
            project_id = os.getenv("GCP_PROJECT_ID")
            location = os.getenv("GCP_LOCATION")
            if not project_id or not location:
                raise ValueError("GCP_PROJECT_ID and GCP_LOCATION must be set in .env for local dev.")
            
            # The google-auth library automatically finds GOOGLE_APPLICATION_CREDENTIALS from .env
            vertexai.init(project=project_id, location=location)
            _vertex_ai_initialized = True
            print("Vertex AI initialized successfully from local environment.")
        except Exception as e:
            st.error(f"Authentication Error locally: {e}")

# --- AI-Powered Functions ---
# (The rest of your functions: get_ai_comparison, perform_vector_search, and get_ai_summary
#  remain exactly the same as you provided and are correct.)

def get_ai_comparison(study_1_details: str, study_2_details: str) -> str:
    init_vertex_ai()
    if not _vertex_ai_initialized: return "Error: Vertex AI not initialized."
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
    """Vector search with Vertex AI (primary) or OpenAI (fallback)"""
    from openai import OpenAI
    
    query_embedding = None
    embedding_source = None
    
    # Try Vertex AI first
    try:
        init_vertex_ai()
        if _vertex_ai_initialized:
            print("Using Vertex AI for embeddings...")
            model = TextEmbeddingModel.from_pretrained("text-embedding-004")
            query_embedding = model.get_embeddings([query_string])[0].values
            embedding_source = "Vertex AI"
    except Exception as e:
        print(f"Vertex AI failed: {e}. Falling back to OpenAI...")
    
    # Fallback to OpenAI if Vertex AI failed
    if query_embedding is None:
        try:
            api_key = None
            try:
                api_key = st.secrets["OPENAI_API_KEY"]
            except:
                api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return [{"error": "OpenAI API key not configured. Please add OPENAI_API_KEY to secrets."}]
            
            print("Using OpenAI for embeddings...")
            client = OpenAI(api_key=api_key)
            response = client.embeddings.create(
                input=query_string,
                model="text-embedding-3-small",
                dimensions=768
            )
            query_embedding = response.data[0].embedding
            embedding_source = "OpenAI"
        except Exception as e:
            return [{"error": f"Both Vertex AI and OpenAI failed: {e}"}]
    
    if query_embedding is None:
        return [{"error": "Failed to generate embeddings."}]
    
    # Perform vector search
    pipeline = [
        {"$vectorSearch": {
            "index": "vector_index", "path": "text_embedding",
            "queryVector": query_embedding, "numCandidates": 150, "limit": limit
        }},
        {"$project": {
            "study_id": 1, "title": 1, "description": 1, "organisms": 1, 
            "factors": 1, "study_link": 1, "score": { "$meta": "vectorSearchScore" }
        }}
    ]
    
    try:
        results = collection.aggregate(pipeline)
        results_list = list(results)
        print(f"✅ Vector search successful using {embedding_source}")
        return results_list
    except Exception as e:
        return [{"error": f"Vector search failed: {e}"}]

def get_ai_summary(question: str, search_results: list) -> str:
    init_vertex_ai()
    if not _vertex_ai_initialized: return "Error: Vertex AI not initialized."
    model = GenerativeModel("gemini-1.5-flash-001")
    context = ""
    for result in search_results[:3]:
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