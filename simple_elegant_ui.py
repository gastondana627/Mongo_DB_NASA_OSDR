#!/usr/bin/env python3
"""
Simple Elegant UI Components
Clean, professional components using Streamlit's native capabilities.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime

def apply_elegant_theme():
    """Apply a clean, elegant theme using minimal CSS"""
    st.markdown("""
    <style>
    /* Clean, professional styling */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #f8fafc;
    }
    
    /* Professional tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: #1e293b;
        padding: 4px;
        border-radius: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 6px;
        color: #94a3b8;
        font-weight: 500;
        padding: 8px 16px;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(45deg, #0ea5e9, #3b82f6);
        color: white !important;
    }
    
    /* Clean buttons */
    .stButton > button {
        background: linear-gradient(45deg, #0ea5e9, #3b82f6);
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: 500;
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

def create_elegant_header(title: str, subtitle: str = None):
    """Create a clean, professional header"""
    st.markdown(f"# 🚀 {title}")
    if subtitle:
        st.markdown(f"*{subtitle}*")
    st.markdown("---")

def create_status_indicators(systems: List[Dict[str, Any]]):
    """Create clean status indicators"""
    st.markdown("### System Status")
    
    for system in systems:
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            status_emoji = "🟢" if system["status"] == "Connected" else "🔴"
            st.markdown(f"**{status_emoji} {system['name']}**")
        
        with col2:
            st.markdown(f"*{system['status']}*")
        
        with col3:
            if "uptime" in system:
                st.markdown(f"*{system['uptime']}% uptime*")

def create_metrics_row(metrics: List[Dict[str, Any]]):
    """Create a clean metrics display"""
    cols = st.columns(len(metrics))
    
    for i, metric in enumerate(metrics):
        with cols[i]:
            st.metric(
                label=metric["label"],
                value=metric["value"],
                delta=metric.get("delta"),
                help=metric.get("description")
            )

def create_elegant_chart(fig, title: str = None):
    """Apply clean styling to charts"""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#f8fafc",
        title_text=title,
        title_font_size=16,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.1)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.1)")
    
    return fig

def create_info_card(title: str, content: str, icon: str = "ℹ️"):
    """Create a clean information card"""
    st.markdown(f"### {icon} {title}")
    st.markdown(content)
    st.markdown("---")

def create_data_table(df: pd.DataFrame, title: str = None):
    """Create a clean data table"""
    if title:
        st.markdown(f"### {title}")
    
    st.dataframe(df, use_container_width=True)

# Example usage functions for the main app
def render_elegant_sidebar():
    """Render a clean sidebar"""
    with st.sidebar:
        st.markdown("## 🛰️ Mission Control")
        st.markdown("*Research Platform v2.0*")
        st.markdown("---")
        
        # System status
        systems = [
            {"name": "MongoDB", "status": "Connected", "uptime": 99.9},
            {"name": "Neo4j", "status": "Connected", "uptime": 99.8}
        ]
        create_status_indicators(systems)
        
        st.markdown("---")
        st.markdown("### Tools")
        if st.button("🔄 Refresh Data"):
            st.rerun()

def render_elegant_main_content():
    """Render clean main content"""
    create_elegant_header(
        "NASA OSDR Research Platform",
        "Advanced Space Biology Data Analysis"
    )
    
    # Sample metrics
    metrics = [
        {"label": "Total Studies", "value": "1,247", "delta": "+12"},
        {"label": "System Uptime", "value": "99.9%", "delta": None},
        {"label": "Avg Citations", "value": "8.3", "delta": "+0.8"},
        {"label": "Processing Time", "value": "45 days", "delta": "-3"}
    ]
    
    create_metrics_row(metrics)
    
    st.markdown("---")
    
    # Sample chart
    fig = px.line(
        x=[1, 2, 3, 4, 5],
        y=[10, 15, 13, 17, 20],
        title="Research Trends"
    )
    fig = create_elegant_chart(fig)
    st.plotly_chart(fig, use_container_width=True)