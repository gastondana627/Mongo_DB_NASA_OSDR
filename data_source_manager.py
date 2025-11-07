#!/usr/bin/env python3
"""
Data Source Manager for NASA OSDR Platform
Tracks and manages real vs. demo data sources with clear labeling.
"""

import streamlit as st
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

@dataclass
class DataSource:
    """Information about a data source"""
    name: str
    source_type: str  # "real", "demo", "api", "simulated"
    description: str
    last_updated: Optional[datetime] = None
    status: str = "unknown"  # "connected", "offline", "error"
    accuracy: str = "unknown"  # "real-time", "cached", "demo", "estimated"

class DataSourceManager:
    """Manages and tracks data sources for transparency"""
    
    def __init__(self):
        self.sources = self._initialize_sources()
    
    def _initialize_sources(self) -> Dict[str, DataSource]:
        """Initialize known data sources"""
        return {
            "osdr_studies": DataSource(
                name="OSDR Studies Database",
                source_type="real",
                description="Your actual NASA OSDR study metadata from MongoDB",
                accuracy="real-time"
            ),
            "neo4j_relationships": DataSource(
                name="Knowledge Graph",
                source_type="real", 
                description="Your actual study relationships in Neo4j",
                accuracy="real-time"
            ),
            "iss_position": DataSource(
                name="ISS Position",
                source_type="api",
                description="Real-time ISS location from NASA Open Notify API",
                accuracy="real-time"
            ),
            "iss_crew": DataSource(
                name="ISS Crew",
                source_type="api",
                description="Current astronauts from NASA Open Notify API",
                accuracy="real-time"
            ),
            "research_analytics": DataSource(
                name="Research Analytics",
                source_type="real",
                description="Real analytics from your OSDR database - no demo data",
                accuracy="real-time"
            ),
            "researcher_profiles": DataSource(
                name="Researcher Profiles",
                source_type="real",
                description="Real principal investigators extracted from OSDR studies",
                accuracy="real-time"
            ),

        }
    
    def update_source_status(self, source_id: str, status: str, last_updated: datetime = None):
        """Update the status of a data source"""
        if source_id in self.sources:
            self.sources[source_id].status = status
            if last_updated:
                self.sources[source_id].last_updated = last_updated
    
    def get_source_info(self, source_id: str) -> Optional[DataSource]:
        """Get information about a specific data source"""
        return self.sources.get(source_id)
    
    def render_data_source_panel(self):
        """Render a panel showing all data sources and their status"""
        st.markdown("### 📊 Data Sources")
        
        # Group by type
        real_sources = [s for s in self.sources.values() if s.source_type == "real"]
        api_sources = [s for s in self.sources.values() if s.source_type == "api"]
        demo_sources = [s for s in self.sources.values() if s.source_type in ["demo", "simulated"]]
        
        # Real data sources
        if real_sources:
            st.markdown("**🟢 Real Data (Your OSDR Database)**")
            for source in real_sources:
                status_emoji = "🟢" if source.status == "connected" else "🔴" if source.status == "offline" else "🟡"
                st.markdown(f"- {status_emoji} **{source.name}**: {source.description}")
        
        # API data sources  
        if api_sources:
            st.markdown("**🔵 Live APIs (External)**")
            for source in api_sources:
                status_emoji = "🟢" if source.status == "connected" else "🔴" if source.status == "offline" else "🟡"
                st.markdown(f"- {status_emoji} **{source.name}**: {source.description}")
        
        # Demo/simulated sources
        if demo_sources:
            st.markdown("**🟡 Demo/Simulated Data**")
            for source in demo_sources:
                st.markdown(f"- 📋 **{source.name}**: {source.description}")
    
    def add_data_accuracy_note(self, source_id: str, component_name: str = None):
        """Add a clear note about data accuracy for a component"""
        source = self.get_source_info(source_id)
        if not source:
            return
        
        component_text = f" for {component_name}" if component_name else ""
        
        if source.source_type == "real":
            st.success(f"📊 **Live Data**: Using real data from your OSDR database{component_text}")
        elif source.source_type == "api":
            st.info(f"📡 **Real-time API**: Live data from external source{component_text}")
        elif source.source_type in ["demo", "simulated"]:
            st.warning(f"📋 **Demo Data**: Simulated data for demonstration{component_text}")
    
    def get_real_osdr_metrics(self) -> Dict[str, Any]:
        """Get real metrics from OSDR database"""
        try:
            from config import MONGO_URI
            from pymongo import MongoClient
            import certifi
            
            client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
            db = client.nasa_osdr
            studies_collection = db.studies
            
            # Get real counts
            total_studies = studies_collection.count_documents({})
            
            # Get organism distribution
            organism_pipeline = [
                {"$group": {"_id": "$organism", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 5}
            ]
            top_organisms = list(studies_collection.aggregate(organism_pipeline))
            
            # Get factor distribution  
            factor_pipeline = [
                {"$group": {"_id": "$factor", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 5}
            ]
            top_factors = list(studies_collection.aggregate(factor_pipeline))
            
            self.update_source_status("osdr_studies", "connected", datetime.now())
            
            return {
                "total_studies": total_studies,
                "top_organisms": top_organisms,
                "top_factors": top_factors,
                "data_source": "real",
                "last_updated": datetime.now()
            }
            
        except Exception as e:
            self.update_source_status("osdr_studies", "error")
            return {
                "total_studies": 0,
                "top_organisms": [],
                "top_factors": [],
                "data_source": "error",
                "error": str(e)
            }
    
    def create_accuracy_legend(self):
        """Create a legend explaining data accuracy indicators"""
        st.markdown("### 📋 Data Accuracy Legend")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**🟢 Real Data**")
            st.markdown("- Your actual OSDR studies")
            st.markdown("- Live database connections")
            st.markdown("- Real-time accuracy")
        
        with col2:
            st.markdown("**🔵 Live APIs**") 
            st.markdown("- External real-time data")
            st.markdown("- NASA/space agency APIs")
            st.markdown("- Updated automatically")
        
        with col3:
            st.markdown("**🟡 Demo Data**")
            st.markdown("- Simulated for demonstration")
            st.markdown("- Realistic but not real")
            st.markdown("- Will be replaced with real data")

# Global instance
data_source_manager = DataSourceManager()