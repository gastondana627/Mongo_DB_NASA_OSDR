
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

This plan lets you finalize the local testing phase robustly and advance confidently to production deployment when ready.

You're almost through infrastructure obstacles, fresh progress will come now.

🚀




---
This project was developed by Gaston D. / GASTONDANA627 for the **AI in Action Hackathon by Google Cloud and MongoDB**.