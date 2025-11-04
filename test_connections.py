#!/usr/bin/env python3
"""
Test script to verify database connections and configuration.
"""

import sys
import os
from pymongo import MongoClient
from neo4j import GraphDatabase
import certifi

# Add current directory to path to import config
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import MONGO_URI, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, IS_LOCAL

def test_mongodb_connection():
    """Test MongoDB connection."""
    print("Testing MongoDB connection...")
    try:
        if not MONGO_URI:
            print("❌ MongoDB URI not configured")
            return False
            
        client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
        # Test connection
        client.admin.command('ping')
        print(f"✅ MongoDB connection successful")
        
        # List databases
        dbs = client.list_database_names()
        print(f"   Available databases: {dbs}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False

def test_neo4j_connection():
    """Test Neo4j connection."""
    print("Testing Neo4j connection...")
    try:
        if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
            print("❌ Neo4j credentials not configured")
            return False
            
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        
        # Test connection
        with driver.session() as session:
            result = session.run("RETURN 'Hello Neo4j' as message")
            record = result.single()
            print(f"✅ Neo4j connection successful: {record['message']}")
            
        driver.close()
        return True
        
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        return False

def main():
    """Run all connection tests."""
    print("=" * 60)
    print("NASA OSDR Database Connection Test")
    print("=" * 60)
    print(f"Environment: {'Local Development' if IS_LOCAL else 'Production'}")
    print()
    
    # Test connections
    mongo_ok = test_mongodb_connection()
    print()
    neo4j_ok = test_neo4j_connection()
    print()
    
    # Summary
    print("=" * 60)
    print("Connection Test Summary:")
    print(f"MongoDB: {'✅ OK' if mongo_ok else '❌ FAILED'}")
    print(f"Neo4j:   {'✅ OK' if neo4j_ok else '❌ FAILED'}")
    
    if mongo_ok and neo4j_ok:
        print("\n🎉 All connections successful!")
        return 0
    else:
        print("\n⚠️  Some connections failed. Check your configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())