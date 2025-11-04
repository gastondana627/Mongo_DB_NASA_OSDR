#!/usr/bin/env python3
"""
Real-Time Data Manager for NASA OSDR
Integrates live data feeds and provides real-time monitoring capabilities.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
from typing import Dict, List, Optional, Any
import asyncio
import json
from dataclasses import dataclass
import time

@dataclass
class DataFeed:
    """Configuration for a real-time data feed"""
    name: str
    source: str
    endpoint: str
    update_frequency: int  # seconds
    data_type: str
    description: str
    active: bool = True

class RealTimeDataManager:
    """Manages real-time data integration and monitoring"""
    
    def __init__(self):
        self.data_feeds = self._initialize_data_feeds()
        self.cache_duration = 300  # 5 minutes cache
    
    def _initialize_data_feeds(self) -> List[DataFeed]:
        """Initialize available real-time data feeds"""
        return [
            DataFeed(
                name="ISS Current Location",
                source="Open Notify API",
                endpoint="http://api.open-notify.org/iss-now.json",
                update_frequency=60,
                data_type="location",
                description="Real-time International Space Station position"
            ),
            DataFeed(
                name="ISS Crew",
                source="Open Notify API", 
                endpoint="http://api.open-notify.org/astros.json",
                update_frequency=3600,
                data_type="crew",
                description="Current astronauts aboard the ISS"
            ),
            DataFeed(
                name="Space Weather",
                source="NOAA Space Weather",
                endpoint="https://services.swpc.noaa.gov/products/summary/solar-wind-speed.json",
                update_frequency=900,
                data_type="space_weather",
                description="Current space weather conditions"
            ),
            DataFeed(
                name="NASA GeneLab Data Releases",
                source="NASA GeneLab API",
                endpoint="https://genelab-data.ndc.nasa.gov/genelab/data/search",
                update_frequency=86400,
                data_type="datasets",
                description="Latest GeneLab dataset releases"
            )
        ]
    
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def fetch_iss_location(_self) -> Optional[Dict[str, Any]]:
        """Fetch current ISS location"""
        try:
            response = requests.get("http://api.open-notify.org/iss-now.json", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    "timestamp": datetime.fromtimestamp(data["timestamp"]),
                    "latitude": float(data["iss_position"]["latitude"]),
                    "longitude": float(data["iss_position"]["longitude"])
                }
        except Exception as e:
            st.error(f"Failed to fetch ISS location: {e}")
        return None
    
    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def fetch_iss_crew(_self) -> Optional[List[Dict[str, str]]]:
        """Fetch current ISS crew"""
        try:
            response = requests.get("http://api.open-notify.org/astros.json", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [
                    {"name": person["name"], "craft": person["craft"]}
                    for person in data["people"]
                    if person["craft"] == "ISS"
                ]
        except Exception as e:
            st.error(f"Failed to fetch ISS crew: {e}")
        return None
    
    def render_iss_tracker(self):
        """Render real-time ISS tracking dashboard"""
        st.subheader("🛰️ International Space Station - Live Tracker")
        
        # Fetch current ISS data
        iss_location = self.fetch_iss_location()
        iss_crew = self.fetch_iss_crew()
        
        if iss_location:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Create ISS location map
                fig = go.Figure()
                
                # Add ISS current position
                fig.add_trace(go.Scattermapbox(
                    lat=[iss_location["latitude"]],
                    lon=[iss_location["longitude"]],
                    mode='markers',
                    marker=dict(size=15, color='red'),
                    text=f"ISS Current Position<br>Lat: {iss_location['latitude']:.2f}<br>Lon: {iss_location['longitude']:.2f}",
                    name="ISS"
                ))
                
                fig.update_layout(
                    mapbox=dict(
                        style="open-street-map",
                        center=dict(lat=iss_location["latitude"], lon=iss_location["longitude"]),
                        zoom=2
                    ),
                    height=400,
                    margin=dict(l=0, r=0, t=0, b=0)
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # ISS Information Panel
                st.metric("Latitude", f"{iss_location['latitude']:.4f}°")
                st.metric("Longitude", f"{iss_location['longitude']:.4f}°")
                st.metric("Last Updated", iss_location["timestamp"].strftime("%H:%M:%S UTC"))
                
                # Current crew
                if iss_crew:
                    st.write("**Current Crew:**")
                    for crew_member in iss_crew:
                        st.write(f"👨‍🚀 {crew_member['name']}")
                
                # Auto-refresh toggle
                if st.checkbox("Auto-refresh (60s)", key="iss_auto_refresh"):
                    time.sleep(1)
                    st.rerun()
    
    def render_space_weather_monitor(self):
        """Render space weather monitoring dashboard"""
        st.subheader("☀️ Space Weather Monitor")
        
        # Simulated space weather data (replace with real API)
        current_time = datetime.now()
        
        # Create sample space weather metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Solar Wind Speed",
                "425 km/s",
                delta="12 km/s",
                help="Current solar wind velocity"
            )
        
        with col2:
            st.metric(
                "Proton Density", 
                "8.2 p/cm³",
                delta="-1.1 p/cm³",
                help="Solar wind proton density"
            )
        
        with col3:
            st.metric(
                "Magnetic Field",
                "6.8 nT",
                delta="2.1 nT", 
                help="Interplanetary magnetic field strength"
            )
        
        with col4:
            st.metric(
                "Kp Index",
                "2.3",
                delta="-0.7",
                help="Geomagnetic activity index"
            )
        
        # Space weather impact on research
        st.info("""
        **Research Impact:** Current space weather conditions are within normal ranges. 
        Radiation exposure levels are suitable for biological experiments aboard the ISS.
        """)
    
    def render_dataset_activity_monitor(self):
        """Render dataset activity and new releases monitor"""
        st.subheader("📊 Dataset Activity Monitor")
        
        # Simulated recent dataset activity
        recent_activity = [
            {
                "dataset_id": "GLDS-394",
                "title": "Transcriptomic analysis of mouse liver after 30-day spaceflight",
                "status": "Processing",
                "last_updated": datetime.now() - timedelta(hours=2),
                "organism": "Mus musculus"
            },
            {
                "dataset_id": "GLDS-395", 
                "title": "Proteomic changes in Arabidopsis seedlings under microgravity",
                "status": "Available",
                "last_updated": datetime.now() - timedelta(days=1),
                "organism": "Arabidopsis thaliana"
            },
            {
                "dataset_id": "GLDS-396",
                "title": "Metabolomic profiling of human muscle tissue post-flight",
                "status": "Quality Control",
                "last_updated": datetime.now() - timedelta(days=3),
                "organism": "Homo sapiens"
            }
        ]
        
        # Display as interactive table
        df = pd.DataFrame(recent_activity)
        df["last_updated"] = df["last_updated"].dt.strftime("%Y-%m-%d %H:%M")
        
        st.dataframe(
            df,
            column_config={
                "dataset_id": "Dataset ID",
                "title": "Title", 
                "status": st.column_config.SelectboxColumn(
                    "Status",
                    options=["Processing", "Available", "Quality Control", "Under Review"]
                ),
                "last_updated": "Last Updated",
                "organism": "Organism"
            },
            hide_index=True,
            use_container_width=True
        )
    
    def render_research_alerts(self):
        """Render research alerts and notifications"""
        st.subheader("🔔 Research Alerts")
        
        alerts = [
            {
                "type": "info",
                "title": "New ISS Experiment Scheduled",
                "message": "Tissue Chips in Space experiment launching next month",
                "timestamp": datetime.now() - timedelta(hours=1)
            },
            {
                "type": "warning", 
                "title": "Space Weather Advisory",
                "message": "Elevated solar activity expected this week - may affect radiation studies",
                "timestamp": datetime.now() - timedelta(hours=6)
            },
            {
                "type": "success",
                "title": "Dataset Release",
                "message": "GLDS-393 RNA-seq data now available for download",
                "timestamp": datetime.now() - timedelta(days=1)
            }
        ]
        
        for alert in alerts:
            if alert["type"] == "info":
                st.info(f"**{alert['title']}** - {alert['message']}")
            elif alert["type"] == "warning":
                st.warning(f"**{alert['title']}** - {alert['message']}")
            elif alert["type"] == "success":
                st.success(f"**{alert['title']}** - {alert['message']}")
    
    def render_experiment_timeline(self):
        """Render timeline of ongoing and upcoming experiments"""
        st.subheader("📅 Experiment Timeline")
        
        # Sample experiment timeline data
        experiments = [
            {"name": "Tissue Chips in Space", "start": "2024-12-01", "end": "2025-02-28", "status": "Upcoming"},
            {"name": "Plant Habitat-03", "start": "2024-10-15", "end": "2024-12-15", "status": "Active"},
            {"name": "Cardinal Muscle", "start": "2024-09-01", "end": "2024-11-30", "status": "Active"},
            {"name": "Food Physiology", "start": "2024-08-01", "end": "2024-10-31", "status": "Completed"}
        ]
        
        # Create Gantt chart
        df_timeline = pd.DataFrame(experiments)
        df_timeline["start"] = pd.to_datetime(df_timeline["start"])
        df_timeline["end"] = pd.to_datetime(df_timeline["end"])
        
        fig = px.timeline(
            df_timeline,
            x_start="start",
            x_end="end", 
            y="name",
            color="status",
            title="ISS Experiment Timeline"
        )
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    def render_complete_dashboard(self):
        """Render the complete real-time data dashboard"""
        st.title("🌍 Real-Time Space Research Dashboard")
        
        # Main dashboard tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "🛰️ ISS Tracker", 
            "☀️ Space Weather", 
            "📊 Dataset Activity",
            "📅 Experiment Timeline"
        ])
        
        with tab1:
            self.render_iss_tracker()
        
        with tab2:
            col1, col2 = st.columns([1, 1])
            with col1:
                self.render_space_weather_monitor()
            with col2:
                self.render_research_alerts()
        
        with tab3:
            self.render_dataset_activity_monitor()
        
        with tab4:
            self.render_experiment_timeline()

# Global instance
realtime_manager = RealTimeDataManager()