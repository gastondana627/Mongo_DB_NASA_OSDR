#!/usr/bin/env python3
"""
Startup check script for NASA OSDR application.
Verifies configuration and connections before running the app.
"""

import sys
import os
from config import (
    IS_LOCAL, NEO4J_URI, NEO4J_USER, NEO4J_ENV_TYPE, 
    MONGO_URI, OPENAI_API_KEY
)

def check_configuration():
    """Check if all required configuration is present."""
    print("🔍 Checking Configuration...")
    
    issues = []
    
    # Check Neo4j config
    if not NEO4J_URI:
        issues.append("❌ NEO4J_URI not set")
    if not NEO4J_USER:
        issues.append("❌ NEO4J_USER not set")
    
    # Check MongoDB config
    if not MONGO_URI:
        issues.append("❌ MONGO_URI not set")
    
    # Check OpenAI config
    if not OPENAI_API_KEY:
        issues.append("❌ OPENAI_API_KEY not set")
    
    if issues:
        print("\n".join(issues))
        return False
    
    print("✅ All configuration variables are set")
    return True

def show_environment_info():
    """Show current environment information."""
    print("\n📋 Environment Information:")
    print(f"   Runtime Environment: {'Local Development' if IS_LOCAL else 'Production (Streamlit Cloud)'}")
    print(f"   Neo4j Environment: {NEO4J_ENV_TYPE}")
    print(f"   Neo4j URI: {NEO4J_URI}")
    print(f"   MongoDB: {'Configured' if MONGO_URI else 'Not configured'}")
    print(f"   OpenAI API: {'Configured' if OPENAI_API_KEY else 'Not configured'}")

def test_connections():
    """Test database connections."""
    print("\n🔗 Testing Connections...")
    
    # Test MongoDB
    try:
        from pymongo import MongoClient
        import certifi
        
        client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
        client.admin.command('ping')
        print("✅ MongoDB connection successful")
        client.close()
        mongo_ok = True
    except Exception as e:
        print(f"❌ MongoDB connection failed: {str(e)[:100]}")
        mongo_ok = False
    
    # Test Neo4j
    try:
        from neo4j import GraphDatabase
        
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, os.getenv('NEO4J_PASSWORD')))
        with driver.session() as session:
            session.run("RETURN 1")
        print("✅ Neo4j connection successful")
        driver.close()
        neo4j_ok = True
    except Exception as e:
        print(f"❌ Neo4j connection failed: {str(e)[:100]}")
        neo4j_ok = False
    
    return mongo_ok and neo4j_ok

def main():
    """Main startup check."""
    print("=" * 60)
    print("🚀 NASA OSDR Application Startup Check")
    print("=" * 60)
    
    # Check configuration
    config_ok = check_configuration()
    
    # Show environment info
    show_environment_info()
    
    # Test connections if config is OK
    if config_ok:
        connections_ok = test_connections()
    else:
        connections_ok = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Startup Check Summary:")
    print(f"   Configuration: {'✅ OK' if config_ok else '❌ Issues found'}")
    print(f"   Connections: {'✅ OK' if connections_ok else '❌ Issues found'}")
    
    if config_ok and connections_ok:
        print("\n🎉 All checks passed! Ready to start the application.")
        print("\n💡 To start the app, run:")
        print("   streamlit run streamlit_main_app.py")
        return 0
    else:
        print("\n⚠️  Issues found. Please fix configuration before starting the app.")
        print("\n💡 Helpful commands:")
        print("   python switch_environment.py status    # Check current config")
        print("   python switch_environment.py local     # Switch to local Neo4j")
        print("   python switch_environment.py production # Switch to Aura Neo4j")
        return 1

if __name__ == "__main__":
    sys.exit(main())