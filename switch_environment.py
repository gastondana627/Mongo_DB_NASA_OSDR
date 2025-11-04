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
        lines = f.readlines()
    
    # Configuration options
    local_config = [
        "NEO4J_URI=bolt://localhost:7687\n",
        "NEO4J_USER=neo4j\n", 
        "NEO4J_PASSWORD=Gas121212\n"
    ]
    
    aura_config = [
        "NEO4J_URI=neo4j+s://befd9937.databases.neo4j.io:7687\n",
        "NEO4J_USER=neo4j\n",
        "NEO4J_PASSWORD=n80rOEUo3DEHIOQkg3VZo4zUT5_cCZy_ioY_jVIZYKY\n"
    ]
    
    # Update lines
    new_lines = []
    config_to_use = local_config if use_local else aura_config
    config_index = 0
    
    for line in lines:
        if line.startswith("NEO4J_URI=") or line.startswith("NEO4J_USER=") or line.startswith("NEO4J_PASSWORD="):
            if config_index < len(config_to_use):
                new_lines.append(config_to_use[config_index])
                config_index += 1
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    
    # Write updated content
    with open(env_file, 'w') as f:
        f.writelines(new_lines)
    
    env_type = "Local Development" if use_local else "Neo4j Aura (Production)"
    print(f"✅ Environment switched to: {env_type}")
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