#!/usr/bin/env python3
"""
Modern Research UI Components
Elegant, professional components designed for space biology research.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime
import numpy as np

class ResearchComponents:
    """Modern UI components for research applications"""
    
    def __init__(self, theme):
        self.theme = theme
    
    def research_dashboard_header(self, title: str, mission_status: str = "Active", 
                                last_updated: datetime = None):
        """Create a mission control style header using Streamlit native components"""
        if last_updated is None:
            last_updated = datetime.now()
        
        # Use Streamlit columns for layout instead of complex HTML
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"# 🚀 {title}")
            st.markdown("*NASA Open Science Data Repository • Advanced Research Platform*")
        
        with col2:
            status_emoji = "🟢" if mission_status == "Active" else "🟡" if mission_status == "Standby" else "🔴"
            st.markdown(f"**{status_emoji} System {mission_status}**")
            st.markdown(f"*Last Updated: {last_updated.strftime('%H:%M:%S UTC')}*")
        
        st.markdown("---")
    
    def research_metrics_grid(self, metrics: List[Dict[str, Any]]):
        """Create a grid of research metrics using Streamlit native components"""
        cols = st.columns(len(metrics))
        
        for i, metric in enumerate(metrics):
            with cols[i]:
                # Use Streamlit's metric component for better rendering
                delta_value = metric.get("delta")
                
                # Format delta with trend indicators
                if delta_value and metric.get("trend"):
                    if metric["trend"] == "up":
                        delta_display = f"↗ {delta_value}"
                    elif metric["trend"] == "down":
                        delta_display = f"↘ {delta_value}"
                    else:
                        delta_display = f"→ {delta_value}"
                else:
                    delta_display = delta_value
                
                st.metric(
                    label=metric['label'],
                    value=metric['value'],
                    delta=delta_display,
                    help=metric.get('description')
                )
    
    def research_status_panel(self, databases: List[Dict[str, Any]]):
        """Create a modern database status panel using Streamlit native components"""
        st.markdown("### 🔗 System Status")
        
        for db in databases:
            # Use Streamlit's native components instead of complex HTML
            status_emoji = "🟢" if db["status"] == "Connected" else "🔴"
            
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**{status_emoji} {db['name']}**")
                    st.markdown(f"*{db['type']} • {db.get('location', 'Cloud')}*")
                    if db.get("description"):
                        st.markdown(f"_{db['description']}_")
                
                with col2:
                    st.markdown(f"**{db['status']}**")
                    uptime = db.get("uptime", 99.9)
                    st.markdown(f"*{uptime}% uptime*")
                
                st.markdown("---")
    
    def create_elegant_chart(self, fig, title: str = None):
        """Apply elegant styling to Plotly charts"""
        # Apply theme
        fig.update_layout(
            **self.theme.get_plotly_theme()["layout"],
            title={
                "text": title,
                "font": {"size": 18, "family": "Space Grotesk"},
                "x": 0.02
            } if title else None,
            margin=dict(l=20, r=20, t=40, b=20),
            height=400
        )
        
        # Add subtle animations
        fig.update_traces(
            hovertemplate="<b>%{x}</b><br>%{y}<extra></extra>",
            hoverlabel=dict(
                bgcolor="rgba(30, 41, 59, 0.9)",
                bordercolor="rgba(255, 255, 255, 0.2)",
                font_color="white"
            )
        )
        
        return fig
    
    def research_data_table(self, df: pd.DataFrame, title: str = None):
        """Create an elegant data table for research data"""
        if title:
            st.markdown(f"### {title}")
        
        # Style the dataframe
        styled_df = df.style.set_table_styles([
            {
                'selector': 'thead th',
                'props': [
                    ('background-color', '#1E293B'),
                    ('color', '#F8FAFC'),
                    ('font-weight', '600'),
                    ('border', '1px solid rgba(255, 255, 255, 0.1)'),
                    ('padding', '12px')
                ]
            },
            {
                'selector': 'tbody td',
                'props': [
                    ('background-color', '#334155'),
                    ('color', '#CBD5E1'),
                    ('border', '1px solid rgba(255, 255, 255, 0.1)'),
                    ('padding', '10px')
                ]
            },
            {
                'selector': 'tbody tr:hover',
                'props': [
                    ('background-color', '#475569'),
                ]
            }
        ])
        
        st.dataframe(styled_df, use_container_width=True)
    
    def query_editor_panel(self, query: str = "", language: str = "cypher"):
        """Create an elegant query editor panel"""
        editor_html = f"""
        <div style="
            background: linear-gradient(145deg, #0A0E27, #1E293B);
            border-radius: 12px;
            padding: 1rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
            margin-bottom: 1rem;
        ">
            <div style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 1rem;
                padding-bottom: 0.5rem;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            ">
                <h4 style="
                    color: #F8FAFC;
                    margin: 0;
                    font-family: 'Space Grotesk', sans-serif;
                    font-weight: 500;
                ">⚡ Query Editor</h4>
                
                <div style="
                    background: #334155;
                    padding: 4px 8px;
                    border-radius: 6px;
                    font-size: 0.8rem;
                    color: #94A3B8;
                    font-family: 'JetBrains Mono', monospace;
                ">{language.upper()}</div>
            </div>
        </div>
        """
        st.markdown(editor_html, unsafe_allow_html=True)
    
    def research_alert(self, message: str, alert_type: str = "info", icon: str = None):
        """Create elegant research alerts"""
        colors = {
            "success": {"bg": "rgba(16, 185, 129, 0.1)", "border": "#10B981", "icon": "✅"},
            "error": {"bg": "rgba(239, 68, 68, 0.1)", "border": "#EF4444", "icon": "❌"},
            "warning": {"bg": "rgba(245, 158, 11, 0.1)", "border": "#F59E0B", "icon": "⚠️"},
            "info": {"bg": "rgba(6, 182, 212, 0.1)", "border": "#06B6D4", "icon": "ℹ️"}
        }
        
        style = colors.get(alert_type, colors["info"])
        display_icon = icon or style["icon"]
        
        alert_html = f"""
        <div style="
            background: {style['bg']};
            border-left: 4px solid {style['border']};
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
            display: flex;
            align-items: center;
            gap: 12px;
        ">
            <span style="font-size: 1.2rem;">{display_icon}</span>
            <div style="color: #F8FAFC; flex: 1;">{message}</div>
        </div>
        """
        st.markdown(alert_html, unsafe_allow_html=True)
    
    def loading_animation(self, message: str = "Processing..."):
        """Create an elegant loading animation"""
        loading_html = f"""
        <div style="
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 2rem;
            gap: 1rem;
        ">
            <div style="
                border: 3px solid rgba(255, 255, 255, 0.1);
                border-top: 3px solid #1E88E5;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
            "></div>
            <div style="
                color: #CBD5E1;
                font-size: 0.9rem;
                font-weight: 500;
            ">{message}</div>
        </div>
        
        <style>
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        </style>
        """
        return st.markdown(loading_html, unsafe_allow_html=True)

# Global components instance
research_ui = None  # Will be initialized with theme