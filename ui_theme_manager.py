#!/usr/bin/env python3
"""
Modern UI Theme Manager for NASA OSDR Research Platform
Creates an elegant, research-grade interface matching space biology research standards.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, Optional
import base64
from pathlib import Path

class ResearchUITheme:
    """Modern, elegant UI theme for space biology research"""
    
    def __init__(self):
        self.colors = {
            # Primary NASA/Space theme
            "primary_blue": "#0B3D91",      # NASA Blue
            "secondary_blue": "#1E88E5",    # Lighter blue
            "accent_orange": "#FF6B35",     # NASA Orange/Mars
            "deep_space": "#0A0E27",        # Deep space background
            "cosmic_purple": "#6366F1",     # Cosmic accent
            
            # Research interface colors
            "success_green": "#10B981",     # Success states
            "warning_amber": "#F59E0B",     # Warnings
            "error_red": "#EF4444",         # Errors
            "info_cyan": "#06B6D4",         # Information
            
            # Neutral palette
            "text_primary": "#F8FAFC",      # Primary text (light)
            "text_secondary": "#CBD5E1",    # Secondary text
            "text_muted": "#94A3B8",        # Muted text
            "surface_dark": "#1E293B",      # Dark surfaces
            "surface_medium": "#334155",    # Medium surfaces
            "surface_light": "#475569",     # Light surfaces
            
            # Data visualization
            "data_blue": "#3B82F6",
            "data_green": "#22C55E", 
            "data_purple": "#8B5CF6",
            "data_pink": "#EC4899",
            "data_yellow": "#EAB308",
            "data_teal": "#14B8A6"
        }
        
        self.fonts = {
            "primary": "Inter, -apple-system, BlinkMacSystemFont, sans-serif",
            "monospace": "'JetBrains Mono', 'Fira Code', Consolas, monospace",
            "display": "'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif"
        }
    
    def inject_custom_css(self):
        """Inject simplified, modern CSS styling that works reliably with Streamlit"""
        css = """
        <style>
        /* Import modern fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Main app background */
        .stApp {
            background: linear-gradient(135deg, #0A0E27 0%, #1a1a2e 50%, #1E293B 100%);
            color: #F8FAFC;
            font-family: 'Inter', sans-serif;
        }
        
        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background: #1E293B;
            padding: 8px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .stTabs [data-baseweb="tab"] {
            background: transparent;
            border-radius: 8px;
            color: #CBD5E1;
            font-weight: 500;
            padding: 12px 20px;
            transition: all 0.3s ease;
            border: 1px solid transparent;
        }
        
        .stTabs [data-baseweb="tab"]:hover {
            background: rgba(255, 255, 255, 0.05);
            color: #F8FAFC;
        }
        
        .stTabs [aria-selected="true"] {
            background: linear-gradient(45deg, #0B3D91, #1E88E5);
            color: white !important;
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 4px 16px rgba(11, 61, 145, 0.4);
        }
        
        /* Button styling */
        .stButton > button {
            background: linear-gradient(45deg, #0B3D91, #1E88E5);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.75rem 1.5rem;
            font-weight: 500;
            transition: all 0.3s ease;
            box-shadow: 0 4px 16px rgba(11, 61, 145, 0.3);
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(11, 61, 145, 0.4);
        }
        
        /* Metric styling */
        .stMetric {
            background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
            border-radius: 12px;
            padding: 1rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)
    
    def create_header(self, title: str, subtitle: str = None, icon: str = "🚀"):
        """Create an elegant header section"""
        header_html = f"""
        <div class="main-header fade-in-up">
            <h1>{icon} {title}</h1>
            {f'<div class="subtitle">{subtitle}</div>' if subtitle else ''}
        </div>
        """
        st.markdown(header_html, unsafe_allow_html=True)
    
    def create_metric_card(self, title: str, value: str, delta: str = None, help_text: str = None):
        """Create an elegant metric card"""
        delta_html = ""
        if delta:
            delta_color = "var(--success-green)" if not delta.startswith("-") else "var(--error-red)"
            delta_html = f'<div style="color: {delta_color}; font-size: 0.9rem; margin-top: 0.5rem;">{delta}</div>'
        
        card_html = f"""
        <div class="metric-card">
            <div class="metric-value">{value}</div>
            <div class="metric-label">{title}</div>
            {delta_html}
        </div>
        """
        return st.markdown(card_html, unsafe_allow_html=True)
    
    def create_research_card(self, content: str, title: str = None):
        """Create a research-themed content card"""
        title_html = f"<h3 style='margin-top: 0; color: var(--text-primary);'>{title}</h3>" if title else ""
        card_html = f"""
        <div class="research-card fade-in-up">
            {title_html}
            {content}
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)
    
    def get_plotly_theme(self) -> Dict[str, Any]:
        """Get Plotly theme configuration for consistent styling"""
        return {
            "layout": {
                "paper_bgcolor": self.colors["surface_dark"],
                "plot_bgcolor": self.colors["deep_space"],
                "font": {
                    "family": self.fonts["primary"],
                    "color": self.colors["text_primary"]
                },
                "colorway": [
                    self.colors["data_blue"],
                    self.colors["data_green"], 
                    self.colors["data_purple"],
                    self.colors["data_pink"],
                    self.colors["data_yellow"],
                    self.colors["data_teal"]
                ],
                "xaxis": {
                    "gridcolor": "rgba(255, 255, 255, 0.1)",
                    "linecolor": "rgba(255, 255, 255, 0.2)",
                    "tickcolor": "rgba(255, 255, 255, 0.2)"
                },
                "yaxis": {
                    "gridcolor": "rgba(255, 255, 255, 0.1)",
                    "linecolor": "rgba(255, 255, 255, 0.2)",
                    "tickcolor": "rgba(255, 255, 255, 0.2)"
                }
            }
        }
    
    def create_status_indicator(self, status: str, label: str):
        """Create a modern status indicator"""
        status_colors = {
            "online": self.colors["success_green"],
            "offline": self.colors["error_red"],
            "warning": self.colors["warning_amber"],
            "info": self.colors["info_cyan"]
        }
        
        color = status_colors.get(status, self.colors["text_muted"])
        
        indicator_html = f"""
        <div style="display: flex; align-items: center; gap: 8px; margin: 8px 0;">
            <div style="width: 8px; height: 8px; border-radius: 50%; background: {color}; 
                        box-shadow: 0 0 8px {color}40;"></div>
            <span style="color: var(--text-secondary); font-size: 0.9rem;">{label}</span>
        </div>
        """
        st.markdown(indicator_html, unsafe_allow_html=True)

# Global theme instance
ui_theme = ResearchUITheme()