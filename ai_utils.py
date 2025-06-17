import os
import vertexai
from vertexai.generative_models import GenerativeModel
from vertexai.language_models import TextEmbeddingModel
from pymongo import MongoClient

# --- CONFIGURATION ---
if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./gcp_credentials.json"

PROJECT_ID = "nasa-osdr-mongo"  # Your GCP Project ID
LOCATION = "us-central1"        # The GCP region

# --- GENERATIVE COMPARISON FUNCTION ---
def get_ai_comparison(study_1_details: str, study_2_details: str) -> str:
    """
    Uses the Gemini AI model to generate a comparison between two studies.
    """
    print("Initializing Vertex AI for generative model...")
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    model = GenerativeModel("gemini-1.5-flash-001")
    print("Gemini 1.5 Flash model loaded.")

    prompt = f"""
    You are a helpful NASA science assistant. Your task is to compare two scientific studies and provide a brief, insightful summary of their relationship. Focus on their similarities and differences in terms of the factors they investigate and the organisms they use.

    Here is the data for the two studies:

    ---
    STUDY 1:
    {study_1_details}
    ---
    STUDY 2:
    {study_2_details}
    ---

    Please provide your analysis in a concise paragraph.
    """

    try:
        print("Sending request to Gemini API...")
        response = model.generate_content(prompt)
        print("Received response from Gemini API.")
        return response.text
    except Exception as e:
        error_message = f"An error occurred while contacting the AI model: {e}"
        print(error_message)
        return error_message

# --- VECTOR SEARCH FUNCTION ---
def perform_vector_search(query_string: str, collection, limit=10):
    """
    Performs a vector search on the MongoDB collection.
    """
    print("Initializing Vertex AI for embedding the search query...")
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    model = TextEmbeddingModel.from_pretrained("text-embedding-004")
    print(f"Generating embedding for query: '{query_string}'")

    # 1. Get the vector embedding for the user's query
    query_embedding = model.get_embeddings([query_string])[0].values

    # 2. Define the MongoDB Vector Search aggregation pipeline
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "text_embedding",
                "queryVector": query_embedding,
                "numCandidates": 200,
                "limit": limit
            }
        },
        {
            "$project": {
                "study_id": 1, "title": 1, "description": 1,
                "organisms": 1, "factors": 1, "study_link": 1,
                "score": { "$meta": "vectorSearchScore" }
            }
        }
    ]

    print("Executing vector search query in MongoDB...")
    try:
        results = collection.aggregate(pipeline)
        return list(results)
    except Exception as e:
        print(f"An error occurred during vector search: {e}")
        return [{"error": str(e)}]

# --- TEST HARNESS ---
if __name__ == "__main__":
    # Test Gemini comparison
    print("\n--- GEMINI COMPARISON TEST ---")
    comparison = get_ai_comparison("Study on mouse genetics", "Experiment on fruit fly behavior")
    print(comparison)

    # Optional: test MongoDB vector search
    print("\n--- VECTOR SEARCH TEST ---")
    try:
        client = MongoClient("mongodb://localhost:27017")  # or use your MongoDB URI
        db = client["nasa_osdr"]
        collection = db["studies"]
        query = "Effects of microgravity on cognitive performance"
        results = perform_vector_search(query, collection)
        for r in results:
            print(r)
    except Exception as db_error:
        print(f"Database connection failed: {db_error}")
