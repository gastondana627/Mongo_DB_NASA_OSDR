# loading_animations.py

import streamlit as st
import time
from typing import Optional, Dict, Any
import json

class LoadingAnimations:
    """Enhanced loading animations for NASA OSDR Research Platform"""
    
    def __init__(self):
        self.nasa_emojis = ["🚀", "🛰️", "🌌", "⭐", "🌍", "🔬", "📡", "🧬"]
        self.loading_messages = [
            "Connecting to Neo4j database...",
            "Querying knowledge graph...",
            "Processing study relationships...",
            "Building visualization...",
            "Optimizing graph layout...",
            "Loading complete!"
        ]
    
    def show_node_lock_animation(self, study_id: str, duration: float = 3.0):
        """Show animated loading sequence for node locking"""
        
        # Create placeholder for animation
        animation_placeholder = st.empty()
        progress_placeholder = st.empty()
        
        # Animation sequence
        steps = [
            {"message": f"🔒 Locking study {study_id}...", "progress": 0.2},
            {"message": "📡 Connecting to knowledge graph...", "progress": 0.4},
            {"message": "🔍 Querying relationships...", "progress": 0.6},
            {"message": "🎯 Building visualization...", "progress": 0.8},
            {"message": "✅ Lock complete!", "progress": 1.0}
        ]
        
        step_duration = duration / len(steps)
        
        for i, step in enumerate(steps):
            with animation_placeholder.container():
                # Create animated header
                cols = st.columns([1, 10])
                with cols[0]:
                    # Rotating emoji animation
                    emoji_idx = i % len(self.nasa_emojis)
                    st.markdown(f"## {self.nasa_emojis[emoji_idx]}")
                with cols[1]:
                    st.markdown(f"### {step['message']}")
            
            # Progress bar
            with progress_placeholder.container():
                st.progress(step['progress'])
                if i < len(steps) - 1:  # Don't sleep on the last step
                    time.sleep(step_duration)
        
        # Clear animation after completion
        time.sleep(0.5)
        animation_placeholder.empty()
        progress_placeholder.empty()
    
    def show_query_execution_animation(self, query: str, duration: float = 2.0):
        """Show animated loading for query execution"""
        
        animation_placeholder = st.empty()
        
        steps = [
            "🔍 Parsing Cypher query...",
            "📊 Executing against Neo4j...",
            "🎨 Formatting results...",
            "✅ Query complete!"
        ]
        
        step_duration = duration / len(steps)
        
        for i, message in enumerate(steps):
            with animation_placeholder.container():
                cols = st.columns([1, 10])
                with cols[0]:
                    emoji_idx = i % len(self.nasa_emojis)
                    st.markdown(f"## {self.nasa_emojis[emoji_idx]}")
                with cols[1]:
                    st.markdown(f"### {message}")
                
                # Show query preview on first step
                if i == 0:
                    with st.expander("Query Preview", expanded=False):
                        st.code(query[:200] + "..." if len(query) > 200 else query, language="sql")
            
            if i < len(steps) - 1:
                time.sleep(step_duration)
        
        time.sleep(0.3)
        animation_placeholder.empty()
    
    def show_spinner_with_messages(self, messages: list, duration_per_message: float = 1.0):
        """Show spinner with rotating messages"""
        
        for message in messages:
            with st.spinner(message):
                time.sleep(duration_per_message)
    
    def create_pulsing_lock_indicator(self, study_id: str):
        """Create a pulsing lock indicator for locked nodes"""
        
        # CSS for pulsing animation
        pulsing_css = """
        <style>
        .pulsing-lock {
            animation: pulse 2s infinite;
            display: inline-block;
        }
        
        @keyframes pulse {
            0% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.7; transform: scale(1.1); }
            100% { opacity: 1; transform: scale(1); }
        }
        
        .lock-container {
            background: linear-gradient(135deg, #1f4e79, #2d5aa0);
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            border-left: 5px solid #4CAF50;
        }
        </style>
        """
        
        # HTML for pulsing lock
        lock_html = f"""
        {pulsing_css}
        <div class="lock-container">
            <span class="pulsing-lock">🔒</span>
            <strong style="color: #4CAF50; margin-left: 10px;">
                LOCKED NODE: {study_id}
            </strong>
        </div>
        """
        
        st.markdown(lock_html, unsafe_allow_html=True)
    
    def show_success_animation(self, message: str, duration: float = 2.0):
        """Show success animation with celebration emojis (non-blocking)"""
        
        # Use Streamlit's built-in balloons for celebration
        st.balloons()
        
        # Show immediate success message
        st.success(f"✅ {message}")
        
        # Optional: Add some visual flair with CSS
        success_css = """
        <style>
        .success-pulse {
            animation: successPulse 1s ease-in-out;
        }
        
        @keyframes successPulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        </style>
        """
        st.markdown(success_css, unsafe_allow_html=True)
    
    def create_loading_overlay(self, message: str = "Loading..."):
        """Create a loading overlay that covers the content"""
        
        overlay_css = """
        <style>
        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
            color: white;
            font-size: 24px;
        }
        
        .loading-spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #3498db;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin-right: 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* Prevent page greying out during Streamlit rerun */
        .stApp > div[data-testid="stAppViewContainer"] {
            background-color: transparent !important;
        }
        
        /* Smooth transitions for better UX */
        .stButton > button {
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        
        /* Loading state improvements */
        .stSpinner {
            background: rgba(255, 255, 255, 0.9) !important;
            border-radius: 10px !important;
            padding: 20px !important;
        }
        </style>
        """
        
        overlay_html = f"""
        {overlay_css}
        <div class="loading-overlay">
            <div class="loading-spinner"></div>
            <div>{message}</div>
        </div>
        """
        
        return st.markdown(overlay_html, unsafe_allow_html=True)
    
    def apply_smooth_ui_css(self):
        """Apply CSS to prevent page greying and improve transitions"""
        
        smooth_css = """
        <style>
        /* Prevent Streamlit's default greying during rerun */
        .stApp {
            background-color: var(--background-color) !important;
        }
        
        .stApp > div[data-testid="stAppViewContainer"] {
            background-color: transparent !important;
        }
        
        /* Smooth button transitions */
        .stButton > button {
            transition: all 0.2s ease-in-out;
            border-radius: 8px;
        }
        
        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        /* Loading spinner improvements */
        .stSpinner > div {
            border-color: #4CAF50 transparent transparent transparent !important;
        }
        
        /* Success message animations */
        .stSuccess {
            animation: slideIn 0.3s ease-out;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        /* Prevent flash of unstyled content */
        .stMarkdown {
            transition: opacity 0.2s ease-in-out;
        }
        </style>
        """
        
        st.markdown(smooth_css, unsafe_allow_html=True)
    
    def show_node_click_feedback(self, node_type: str, node_name: str):
        """Show feedback when a node is clicked (non-blocking)"""
        
        # Show immediate feedback without blocking
        st.info(f"🎯 **Node Clicked**: {node_type} - {node_name}")
        st.caption("Generating contextual queries...")
        
        return True

# Global instance for the application
loading_animations = LoadingAnimations()