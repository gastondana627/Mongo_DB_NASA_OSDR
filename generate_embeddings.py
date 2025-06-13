# generate_embeddings.py

import json
import os
import time
from google.api_core.exceptions import ResourceExhausted
from vertexai.language_models import TextEmbeddingModel

# --- CONFIGURATION ---
# IMPORTANT: Replace these with your actual GCP project details.
PROJECT_ID = "nasa-osdr-mongo"
LOCATION = "us-central1"


INPUT_JSON_PATH = "data/osdr_studies.json"
OUTPUT_JSON_PATH = "data/osdr_studies_with_embeddings.json"
# --- END CONFIGURATION ---


def generate_embeddings():
    """
    Reads study data, generates text embeddings using Vertex AI,
    and saves the enriched data to a new JSON file.
    """
    print(f"Initializing Vertex AI for project '{PROJECT_ID}' in '{LOCATION}'...")
    model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")
    print("TextEmbeddingModel loaded.")

    print(f"Loading studies from {INPUT_JSON_PATH}...")
    with open(INPUT_JSON_PATH, 'r') as f:
        studies = json.load(f)
    print(f"Loaded {len(studies)} studies.")

    studies_with_embeddings = []
    
    # Vertex AI has a rate limit (e.g., 60 requests per minute).
    # We process in batches to respect this limit.
    batch_size = 5
    
    for i in range(0, len(studies), batch_size):
        batch = studies[i:i + batch_size]
        
        # Create a list of text content to send to the API
        content_batch = []
        for study in batch:
            # Combine relevant text fields for a richer embedding
            title = study.get('title', '')
            description = study.get('description', '')
            factors = ', '.join(study.get('factors', []))
            combined_text = f"Title: {title}\nDescription: {description}\nFactors: {factors}"
            content_batch.append(combined_text)
        
        try:
            print(f"Processing batch {i//batch_size + 1}/{(len(studies) + batch_size - 1)//batch_size}... (Studies {i+1} to {i+len(batch)})")
            # Get embeddings for the entire batch in one API call
            embeddings = model.get_embeddings(content_batch)
            
            # Add the embedding vector to each study object in the batch
            for study, embedding in zip(batch, embeddings):
                study['text_embedding'] = embedding.values
                studies_with_embeddings.append(study)
            
            # Wait for a second to respect rate limits
            time.sleep(1)

        except ResourceExhausted as e:
            print(f"Rate limit hit. Waiting for 60 seconds before retrying. Error: {e}")
            time.sleep(60)
            # You might want to add more robust retry logic here in a real application
            continue
        except Exception as e:
            print(f"An error occurred during embedding generation: {e}")
            continue

    print(f"\nSuccessfully generated embeddings for {len(studies_with_embeddings)} studies.")

    # Save the enriched data to a new file
    print(f"Saving enriched data to {OUTPUT_JSON_PATH}...")
    with open(OUTPUT_JSON_PATH, 'w') as f:
        json.dump(studies_with_embeddings, f, indent=2)
    print("Save complete.")

if __name__ == "__main__":
    # This requires authentication. Run the 'export' command in your terminal first.
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        print("ERROR: The GOOGLE_APPLICATION_CREDENTIALS environment variable is not set.")
        print("Please run the following command in your terminal before executing this script:")
        print('export GOOGLE_APPLICATION_CREDENTIALS="gcp_credentials.json"')
    else:
        generate_embeddings()