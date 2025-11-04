#!/usr/bin/env python3
"""
Environment switcher for NASA OSDR application.
Easily switch between local and production Neo4j configurations.
"""

import os
import sys
from pathlib import Path

def update_env_file(use_local=True):
    """Update .env file to use local or production Neo4j configuration."""
    
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found!")
        return False
    
    # Read current content
    with open(env_file, 'r') as f:
        content = f.read()
    
    if use_local:
        # Switch to local configuration
        new_content = content.replace(
            'NEO4J_ENV=production', 'NEO4J_ENV=local'
        ).replace(
            'NEO4J_ENV=', 'NEO4J_ENV=local'
        )
        env_type = "Local Development"
    else:
        # Switch to production configuration  
        new_content = content.replace(
            'NEO4J_ENV=local', 'NEO4J_ENV=production'
        ).replace(
            'NEO4J_ENV=', 'NEO4J_ENV=production'
        )
        env_type = "Neo4j Aura (Production)"
    
    # Write updated content
    with open(env_file, 'w') as f:
        f.write(new_content)
    
    print(f"✅ Environment switched to: {env_type}")
    print("⚠️  Make sure your credentials are properly set in .env file")
    return True

def show_current_config():
    """Show current configuration."""
    from config import NEO4J_URI, NEO4J_USER, NEO4J_ENV_TYPE
    print(f"Current Configuration:")
    print(f"  Environment: {NEO4J_ENV_TYPE}")
    print(f"  Neo4j URI: {NEO4J_URI}")
    print(f"  Neo4j User: {NEO4J_USER}")

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python switch_environment.py [local|production|status]")
        print()
        print("Commands:")
        print("  local      - Switch to local Neo4j (bolt://localhost:7687)")
        print("  production - Switch to Neo4j Aura (cloud)")
        print("  status     - Show current configuration")
        return 1
    
    command = sys.argv[1].lower()
    
    if command == "status":
        show_current_config()
    elif command == "local":
        if update_env_file(use_local=True):
            print("\n🔄 Restart your Streamlit app to apply changes")
    elif command == "production":
        if update_env_file(use_local=False):
            print("\n🔄 Restart your Streamlit app to apply changes")
    else:
        print(f"❌ Unknown command: {command}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())