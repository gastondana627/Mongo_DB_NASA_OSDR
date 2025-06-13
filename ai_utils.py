# ai_utils.py

import os
import vertexai
from vertexai.generative_models import GenerativeModel, Part

# --- CONFIGURATION ---
PROJECT_ID = "nasa-osdr-mongo"  # Your GCP Project ID
LOCATION = "us-central1"        # The GCP region

def get_ai_comparison(study_1_details: str, study_2_details: str) -> str:
    """
    Uses the Gemini AI model to generate a comparison between two studies.

    Args:
        study_1_details: A string containing the details of the first study.
        study_2_details: A string containing the details of the second study.

    Returns:
        A string containing the AI-generated comparison.
    """
    print("Initializing Vertex AI for generative model...")
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    # Load the Gemini 1.5 Flash model, which is fast and powerful
    model = GenerativeModel("gemini-1.5-flash-001")
    print("Gemini 1.5 Flash model loaded.")

    # This is the prompt that instructs the AI on how to behave
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