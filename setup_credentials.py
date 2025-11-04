#!/usr/bin/env python3
"""
Secure credential setup script for NASA OSDR application.
Helps users set up their credentials safely without exposing them in git.
"""

import os
import sys
from pathlib import Path
import getpass

def setup_env_file():
    """Interactive setup of .env file with secure credential input."""
    
    env_file = Path(".env")
    template_file = Path(".env.template")
    
    if not template_file.exists():
        print("❌ .env.template file not found!")
        return False
    
    print("🔐 NASA OSDR Credential Setup")
    print("=" * 50)
    print("This script will help you set up your credentials securely.")
    print("Your credentials will be stored in .env (which is git-ignored).")
    print()
    
    # Read template
    with open(template_file, 'r') as f:
        content = f.read()
    
    # Get credentials interactively
    print("📝 Please provide your credentials:")
    print()
    
    # OpenAI API Key
    openai_key = getpass.getpass("OpenAI API Key: ").strip()
    if openai_key:
        content = content.replace("your_openai_api_key_here", openai_key)
    
    # MongoDB URI
    mongo_uri = input("MongoDB Connection String: ").strip()
    if mongo_uri:
        content = content.replace("your_mongodb_connection_string_here", mongo_uri)
    
    # Neo4j Environment
    print("\nNeo4j Configuration:")
    print("1. Local (bolt://localhost:7687)")
    print("2. Neo4j Aura (cloud)")
    choice = input("Choose Neo4j environment (1 or 2): ").strip()
    
    if choice == "1":
        # Local Neo4j
        content = content.replace("NEO4J_ENV=", "NEO4J_ENV=local")
        neo4j_uri = input("Neo4j URI [bolt://localhost:7687]: ").strip() or "bolt://localhost:7687"
        neo4j_user = input("Neo4j User [neo4j]: ").strip() or "neo4j"
        neo4j_password = getpass.getpass("Neo4j Password: ").strip()
    elif choice == "2":
        # Neo4j Aura
        content = content.replace("NEO4J_ENV=", "NEO4J_ENV=production")
        neo4j_uri = input("Neo4j Aura URI (neo4j+s://...): ").strip()
        neo4j_user = input("Neo4j User [neo4j]: ").strip() or "neo4j"
        neo4j_password = getpass.getpass("Neo4j Password: ").strip()
    else:
        print("Invalid choice, skipping Neo4j setup")
        neo4j_uri = neo4j_user = neo4j_password = ""
    
    # Replace Neo4j placeholders
    if neo4j_uri:
        content = content.replace("your_neo4j_uri_here", neo4j_uri)
    if neo4j_user:
        content = content.replace("your_neo4j_user_here", neo4j_user)
    if neo4j_password:
        content = content.replace("your_neo4j_password_here", neo4j_password)
    
    # Write .env file
    with open(env_file, 'w') as f:
        f.write(content)
    
    print(f"\n✅ Credentials saved to {env_file}")
    print("🔒 This file is git-ignored and will not be committed")
    print("\n💡 Next steps:")
    print("   python startup_check.py    # Verify your setup")
    print("   streamlit run streamlit_main_app.py    # Start the app")
    
    return True

def main():
    """Main function."""
    if Path(".env").exists():
        response = input(".env file already exists. Overwrite? (y/N): ").strip().lower()
        if response != 'y':
            print("Setup cancelled.")
            return 0
    
    if setup_env_file():
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())