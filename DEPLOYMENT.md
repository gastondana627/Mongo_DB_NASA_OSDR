# NASA OSDR Deployment Guide

## Quick Start

### 1. Check Current Setup
```bash
python startup_check.py
```

### 2. Switch Environment (if needed)
```bash
# Switch to local Neo4j
python switch_environment.py local

# Switch to production Neo4j Aura
python switch_environment.py production

# Check current configuration
python switch_environment.py status
```

### 3. Run Application
```bash
streamlit run streamlit_main_app.py
```

## Environment Setup

### Local Development

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   - The `.env` file is already configured
   - Use the environment switcher to change between local/production
   - Ensure Neo4j is running locally if using local mode

3. **Test Everything**
   ```bash
   python startup_check.py
   ```

### Production (Streamlit Cloud)

1. **Deploy to Streamlit Cloud**
   - Connect your GitHub repository
   - Set main file to `streamlit_main_app.py`

2. **Configure Secrets**
   - In Streamlit Cloud dashboard, go to Settings > Secrets
   - Copy contents from `.streamlit/secrets.toml`
   - Update with your production credentials

## Database Configuration

### MongoDB Atlas
- Production: Uses MongoDB Atlas cluster
- Connection string in `MONGO_URI`

### Neo4j
- **Local**: `bolt://localhost:7687`
- **Production**: Neo4j Aura `neo4j+s://...`

## Environment Variables

### Required for Local Development (.env)
```
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
MONGO_URI=mongodb+srv://...
OPENAI_API_KEY=sk-...
```

### Required for Production (Streamlit Secrets)
```toml
OPENAI_API_KEY = "sk-..."
MONGO_URI = "mongodb+srv://..."

[neo4j]
URI = "neo4j+s://..."
USER = "neo4j"
PASSWORD = "..."
```

## Troubleshooting

### Common Issues

1. **Neo4j Connection Failed**
   - Check if Neo4j is running locally
   - Verify credentials in `.env` or secrets
   - Ensure firewall allows connection

2. **MongoDB Connection Failed**
   - Verify MongoDB Atlas connection string
   - Check IP whitelist in MongoDB Atlas
   - Ensure network connectivity

3. **Streamlit Cloud Deployment Issues**
   - Check secrets configuration
   - Verify all required packages in `requirements.txt`
   - Check application logs in Streamlit Cloud dashboard

### Testing Commands

```bash
# Test database connections
python test_connections.py

# Run with debug output
python config.py

# Check Streamlit app locally
streamlit run streamlit_main_app.py --server.port 8501
```

## Git Management

The repository is configured to ignore:
- Virtual environments (`venv/`, `venv_nasa/`)
- Environment files (`.env`)
- Secrets (`.streamlit/secrets.toml`)
- Credentials (`gcp_credentials.json`)

Make sure to never commit sensitive information to the repository.