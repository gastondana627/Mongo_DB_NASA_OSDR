
# NASA OSDR AI Explorer

## 🚀 Project Overview

The **NASA OSDR AI Explorer** is a cloud-native web application designed to unlock novel insights from NASA's Open Science Data Repository (OSDR). The project addresses the challenge of navigating vast and complex scientific datasets by transforming flat research data into an intuitive, multi-faceted exploration tool. It leverages a sophisticated architecture combining multiple databases, a containerized deployment, and a powerful AI-driven search and analysis engine built on Google Cloud's Vertex AI.

The application allows users to find data through traditional keyword filters or through a powerful **AI-powered semantic search**, which understands natural language questions. It provides a unique **knowledge graph visualization** using Neo4j to visually map the intricate relationships between studies, organisms, and research factors. Furthermore, users can select related studies from the graph and receive an **AI-generated summary** comparing their similarities and differences, powered by Google's Gemini model.

**Live Deployed Application:** 

## ✨ Core Features

* **AI Semantic Search:** Ask complex, natural language questions (e.g., *"What do we know about muscle atrophy in rodents during spaceflight?"*) and receive conceptually relevant studies, sorted by relevance.
* **Interactive Knowledge Graph:** Select any study to instantly visualize its connections to organisms, experimental factors, and assay types in a dynamic, explorable graph.
* **AI-Powered Comparison:** Select two related studies from the knowledge graph and receive an instant, AI-generated summary explaining their scientific relationship, similarities, and differences.
* **Cloud-Native & Deployed:** The entire application is containerized with Docker and deployed on **Google Cloud Run**, making it publicly accessible, scalable, and secure.
* **Multi-Database Architecture:** Utilizes MongoDB Atlas for robust data storage and Neo4j AuraDB for high-performance graph relationship queries.

## 🛠️ Tech Stack

* **Programming Language:** Python
* **Web Application Framework:** Streamlit
* **AI & Machine Learning:** Google Cloud Vertex AI (Embeddings API & Gemini 1.5 Flash)
* **Deployment:** Docker, Google Cloud Run, Google Artifact Registry
* **Databases:**
    * **MongoDB Atlas** (with Vector Search) for primary data and vector storage.
    * **Neo4j AuraDB** for graph data modeling and visualization.
* **Security:** Google Secret Manager for secure credential handling.
* **DevOps:** Git & GitLab for source code management.

## ⚙️ Cloud Architecture

The application is fully cloud-native, leveraging a modern, scalable architecture:
1.  A **Python scraper** using Selenium extracts data from the NASA OSDR.
2.  The data is processed by a script using the **Vertex AI Embeddings API** to generate semantic vectors.
3.  The enriched data is stored in **MongoDB Atlas** and indexed for vector search. Relational data is loaded into **Neo4j AuraDB**.
4.  The Streamlit application is containerized using **Docker** and its image is stored in **Google Artifact Registry**.
5.  The container is deployed as a service on **Google Cloud Run**, which automatically handles scaling and traffic.
6.  The deployed service securely accesses database credentials and API keys at runtime from **Google Secret Manager**.

## ▶️ How to Run the Application

### Admin / Developer Setup (Local)

This covers the complete process of setting up the project from scratch on a local machine.

1.  **Prerequisites:** Ensure you have Python 3.10+, Git, Docker Desktop, and the `gcloud` CLI installed and authenticated.
2.  **Clone Repository:**
    ```bash
    git clone [Your-GitLab-Repo-URL]
    cd [Your-Repo-Name]
    ```
3.  **Setup Environment:**
    * Create and activate a Python virtual environment:
        ```bash
        python3 -m venv venv
        source venv/bin/activate  # On Windows: venv\Scripts\activate
        ```
    * Install all required libraries:
        ```bash
        pip install -r requirements.txt
        ```
4.  **Configure Credentials:**
    * Create a `.env` file in the root directory.
    * Add your cloud `MONGO_URI`, `NEO4J_URI`, `NEO4J_USER`, and `NEO4J_PASSWORD` to this file.
    * Place your `gcp_credentials.json` file in the root directory.
5.  **Start Databases:**
    * Ensure your MongoDB Atlas and Neo4j AuraDB clusters are active.
6.  **Run the Full Data Pipeline:**
    * **Step A (Scrape & Load MongoDB):** Launch the Streamlit app (`streamlit run streamlit_main_app.py`). Go to the "Data & Setup" tab and click the "Fetch All... Studies" button. Wait for it to complete.
    * **Step B (Load Neo4j):** Run the ingestion script from your terminal: `python3 ingest_to_neo4j.py`.
    * **Step C (Generate AI Embeddings):** Run the embedding script: `python3 generate_embeddings.py`.
    * **Step D (Update MongoDB with Embeddings):** Run the update script: `python3 update_mongo_with_embeddings.py`.
7.  **Run the Application Locally:**
    * Launch the fully populated application: `streamlit run streamlit_main_app.py`.

### End-User Experience (Live Deployed App)

1.  **Access the App:** Open a web browser and navigate to the public URL provided by Google Cloud Run.
2.  **Explore the Tabs:**
    * **🤖 AI Semantic Search:** The primary way to interact with the data. Ask a natural language question to find the most relevant studies.
    * **📚 Study Explorer (Keyword):** A tool for precise, keyword-based searches.
    * **🕸️ Knowledge Graph:** A visual exploration tool. Select a study from one of the search tabs to view its connections here. Use the interactive buttons to discover new relationships.

## 📂 Project Structure

```
[Your-Repo-Name]/
├── scraper/              # Contains all web scraping logic
├── assets/               # UI images and icons
├── data/                 # Output for scraped JSON files
├── ai_utils.py           # Functions for calling Google Vertex AI APIs
├── neo4j_visualizer.py   # Functions for building Neo4j graphs
├── ingest_to_neo4j.py    # Script to populate the Neo4j database
├── generate_embeddings.py# Script to generate AI embeddings
├── update_mongo_with_embeddings.py # Script to update MongoDB with vectors
├── streamlit_main_app.py # The main Streamlit application file
├── Dockerfile            # The recipe to build the production container
├── requirements.txt      # Python dependencies
└── .env                  # Local environment variables (NOT COMMITTED)
```

## ⏭️ Future Work

* **CI/CD Pipeline:** Implement a full CI/CD pipeline using GitLab to automatically build, test, and deploy the application on every push to the main branch.
* **User Accounts:** Integrate Firebase Authentication to allow users to save their research sessions, favorite studies, and store AI-generated insights.
* **Advanced Analytics:** Use Google BigQuery and Looker Studio to create and embed high-level dashboards analyzing trends across the entire dataset.



## 🧰 Local Database Restore

To restore the Neo4j database locally from a `.backup` file:

1. Stop Neo4j Desktop instance.
2. Run the restore command:

"/path/to/neo4j-admin" database restore neo4j
--from-path=/path/to/neo4j-backup.backup
--overwrite-destination

text

3. Start Neo4j Desktop instance.
4. Verify with Cypher query:

MATCH (n) RETURN count(n);

text

5. Add your MongoDB and Neo4j connection details to a `secrets.toml` file in `.streamlit` directory:

[neo4j]
uri = "bolt://localhost:7687"
user = "neo4j"
password = "your_password"

[mongodb]
uri = "your_mongodb_uri"

text

## 🐳 Docker Configuration for Local and Production

Use environment variables to switch between local and cloud Neo4j instances. In your Docker setup and Streamlit app:

- Read environment variables for Neo4j URI, user, and password.
- Default to local values if none provided.
- Update your deployment pipeline to set correct env vars for production.

---

Localhost vs. Production Configuration
Environment Overview

The application supports two distinct operating modes: local development and cloud production. Each mode requires specific configuration and behaves differently based on available services.

Component | Localhost | Production (Cloud Run)
MongoDB | Cloud Atlas (remote) | Cloud Atlas (remote)
Neo4j | Docker Desktop (local:7687) | Unavailable (offline)
Vertex AI | GCP credentials required | GCP credentials via Secret Manager
OpenAI | API key from .env | API key via Streamlit Secrets
Vector Search | MongoDB Atlas vector index | MongoDB Atlas vector index
AI Search Mode | Vertex AI > OpenAI > MongoDB | OpenAI > MongoDB fallback

Localhost Setup

Purpose: Full-featured development environment with all services accessible.

Prerequisites:

Python 3.10+, Git, Docker Desktop installed

Clone and setup:
git clone https://github.com/gastondana627/Mongo_DB_NASA_OSDR.git
cd Mongo_DB_NASA_OSDR
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

Create .env file with local credentials:
MONGO_URI=mongodb+srv://USERNAME:PASSWORD@nasa-osdr-mongodb.gd5tnsw.mongodb.net/?retryWrites=truemongodb+srv://nasa_user:NasaUser100!!@nasa-osdr-mongodb.gd5tnsw.mongodb.net/?retryWrites=true&w=majority&appName=NASA-OSDR-MongoDBw=majority
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_local_neo4j_password
GCP_PROJECT_ID=nasa-osdr-mongo
GCP_LOCATION=us-central1
OPENAI_API_KEY=sk-proj-your-key-here

Running Locally:

Start Neo4j Docker container:
docker run -d --name neo4j-local -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/your_password neo4j:latest

Launch Streamlit:
streamlit run streamlit_main_app.py

App runs at http://localhost:8501

What Works Locally:

✅ AI Semantic Search: Vertex AI (if GCP creds available) > OpenAI > MongoDB fallback
✅ Study Explorer: Full keyword search with MongoDB
✅ Knowledge Graph: Full Neo4j visualization with study relationships
✅ Data & Setup: Scrape and populate MongoDB + Neo4j

Localhost Logs:

✅ MongoDB: Connected
Neo4j: bolt://localhost:7687
Using Vertex AI for embeddings...
Using OpenAI for embeddings...
Using localhost fallback: returning sample results...

Production Setup (Streamlit Cloud)

Purpose: Public-facing cloud application with managed infrastructure.

Prerequisites:

Streamlit Cloud account (free tier at streamlit.io)

GitHub repository with code pushed to main branch

Secrets configured in Streamlit Cloud dashboard

Configuration:

Navigate to astroarchive.streamlit.app > Settings (gear icon) > Secrets and add:

OPENAI_API_KEY = "sk-proj-your-key-here"
GCP_PROJECT_ID = "nasa-osdr-mongo"
GCP_LOCATION = "us-central1"
MONGO_URI = "mongodb+srv://USERNAME:PASSWORD@nasa-osdr-mongodb.gd5tnsw.mongodb.net/?retryWrites=truemongodb+srv://nasa_user:NasaUser100!!@nasa-osdr-mongodb.gd5tnsw.mongodb.net/..."w=majority

What Works in Production:

✅ AI Semantic Search: OpenAI API > MongoDB fallback
✅ Study Explorer: Full keyword search with MongoDB
⚠️ Knowledge Graph: Shows "Neo4j features disabled" (expected—Neo4j unreachable from cloud)
✅ Data & Setup: Read-only (no scraping from production)

What Doesn't Work in Production:

❌ Knowledge Graph Rendering: Neo4j is local-only, unreachable from Cloud Run
❌ Vertex AI: Falls back to OpenAI automatically
❌ Local Data Scraping: No write access to production sources

Production Logs:

🔧 Running in LOCAL mode
✅ MongoDB: Connected
Neo4j: bolt://localhost:7687
⚠️ Neo4j offline: Couldn't connect to localhost:7687
Using OpenAI for embeddings...

Decision Tree: Which Environment?

Use LOCALHOST if you want to:

Develop new features

Test Neo4j graph relationships

Populate databases from scratch

Debug AI search pipelines

Work offline with cached data

Use PRODUCTION if you want to:

Share the app publicly

Access via stable URL (astroarchive.streamlit.app)

Leverage MongoDB vector search at scale

Demo AI semantic search (OpenAI mode)

Run without local infrastructure

Common Issues & Fixes

"Neo4j offline" in Production (Expected)

Neo4j is not accessible from Cloud Run. Knowledge Graph shows disabled warning. This is intentional.

Fix: Deploy cloud-hosted Neo4j (Neo4j AuraDB) if KG needed in production.

"OpenAI API key not configured" in Production

Fix: Add OPENAI_API_KEY to Streamlit Cloud Secrets (see Configuration above).

"GCP_PROJECT_ID and GCP_LOCATION" error in Production

Fix: Optional. Only needed for Vertex AI. Add both to Secrets or leave empty for OpenAI fallback.

AI Search returns "No studies in database" in Production

Fix: Ensure MongoDB Atlas vector index is created. Run locally:
python3 generate_embeddings.py
python3 update_mongo_with_embeddings.py

Deployment Workflow

Local Development
↓
git push origin main
↓
GitHub > Streamlit Cloud Auto-Deploy
↓
Production Live (astroarchive.streamlit.app)
↓
Changes live in 1-2 minutes

No manual deployment needed—Streamlit Cloud auto-rebuilds on every push to main.
🚀




---
This project was developed by Gaston D. / GASTONDANA627 for the **AI in Action Hackathon by Google Cloud and MongoDB**.