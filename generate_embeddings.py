# generate_embeddings.py (Using the latest standard model)

import json
import os
import time
from google.api_core.exceptions import ResourceExhausted
import vertexai
from vertexai.language_models import TextEmbeddingModel

# --- CONFIGURATION ---
PROJECT_ID = "nasa-osdr-mongo"  # Your GCP Project ID
LOCATION = "us-central1"        # The GCP region

INPUT_JSON_PATH = "data/osdr_studies.json"
OUTPUT_JSON_PATH = "data/osdr_studies_with_embeddings.json"
# --- END CONFIGURATION ---


def generate_embeddings():
    """
    Reads study data, generates text embeddings using Vertex AI,
    and saves the enriched data to a new JSON file.
    """
    print(f"Initializing Vertex AI for project '{PROJECT_ID}' in '{LOCATION}'...")
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    
    # --- THIS IS THE CORRECTED, MODERN MODEL NAME ---
    model = TextEmbeddingModel.from_pretrained("text-embedding-004")
    print("TextEmbeddingModel loaded successfully.")

    print(f"Loading studies from {INPUT_JSON_PATH}...")
    try:
        with open(INPUT_JSON_PATH, 'r') as f:
            studies = json.load(f)
        print(f"Loaded {len(studies)} studies.")
    except FileNotFoundError:
        print(f"ERROR: Input file not found at '{INPUT_JSON_PATH}'.")
        print("Please run the data scraping process from the main app first.")
        return

    studies_with_embeddings = []
    
    # Vertex AI has a rate limit. We process in batches to respect this.
    batch_size = 5
    
    for i in range(0, len(studies), batch_size):
        batch = studies[i:i + batch_size]
        
        content_batch = []
        for study in batch:
            title = study.get('title', '')
            description = study.get('description', '')
            factors = ', '.join(study.get('factors', []))
            combined_text = f"Title: {title}\nDescription: {description}\nFactors: {factors}"
            content_batch.append(combined_text)
        
        try:
            print(f"Processing batch {i//batch_size + 1}/{(len(studies) + batch_size - 1)//batch_size}... (Studies {i+1} to {i+len(batch)})")
            embeddings = model.get_embeddings(content_batch)
            
            for study, embedding in zip(batch, embeddings):
                study['text_embedding'] = embedding.values
                studies_with_embeddings.append(study)
            
            time.sleep(1) # Wait 1 second between batches to be safe with rate limits

        except ResourceExhausted as e:
            print(f"Rate limit hit. Waiting for 60 seconds before retrying. Error: {e}")
            time.sleep(60)
            continue
        except Exception as e:
            print(f"An error occurred during embedding generation for batch {i//batch_size + 1}: {e}")
            continue

    print(f"\nSuccessfully generated embeddings for {len(studies_with_embeddings)} studies.")

    print(f"Saving enriched data to {OUTPUT_JSON_PATH}...")
    with open(OUTPUT_JSON_PATH, 'w') as f:
        json.dump(studies_with_embeddings, f, indent=2)
    print("Save complete.")

if __name__ == "__main__":
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        print("ERROR: The GOOGLE_APPLICATION_CREDENTIALS environment variable is not set.")
        print("Please run the following command in your terminal before executing this script:")
        print('export GOOGLE_APPLICATION_CREDENTIALS="gcp_credentials.json"')
    else:
        generate_embeddings()