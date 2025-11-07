#!/usr/bin/env python3
"""
Tribute UI Components - Stunning Visual Components for Researcher Tribute
Creates NASA-grade, emotionally engaging UI for honoring space biology researchers.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List, Any, Optional
import base64
from pathlib import Path

class TributeUIComponents:
    """Stunning UI components for the researcher tribute system"""
    
    def __init__(self):
        self.nasa_colors = {
            'primary': '#0B3D91',    # NASA Blue
            'secondary': '#FC3D21',   # NASA Red
            'accent': '#FFD700',      # Gold
            'space': '#000014',       # Deep Space
            'star': '#FFFFFF',        # Star White
            'nebula': '#4B0082',      # Deep Purple
            'earth': '#6B93D6'        # Earth Blue
        }
    
    def inject_tribute_css(self):
        """Inject stunning CSS for the tribute system"""
        st.markdown("""
        <style>
        /* NASA Tribute Theme */
        .tribute-hero {
            background: linear-gradient(135deg, #0B3D91 0%, #000014 50%, #4B0082 100%);
            padding: 3rem 2rem;
            border-radius: 20px;
            margin: 2rem 0;
            position: relative;
            overflow: hidden;
            box-shadow: 0 20px 40px rgba(11, 61, 145, 0.3);
        }
        
        .tribute-hero::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="20" cy="20" r="1" fill="white" opacity="0.8"/><circle cx="80" cy="30" r="0.5" fill="white" opacity="0.6"/><circle cx="40" cy="70" r="0.8" fill="white" opacity="0.7"/><circle cx="90" cy="80" r="0.3" fill="white" opacity="0.5"/><circle cx="10" cy="90" r="0.6" fill="white" opacity="0.8"/></svg>');
            animation: twinkle 3s infinite;
        }
        
        @keyframes twinkle {
            0%, 100% { opacity: 0.8; }
            50% { opacity: 0.3; }
        }
        
        .tribute-hero h1 {
            color: white;
            font-size: 3.5rem;
            font-weight: 700;
            text-align: center;
            margin-bottom: 1rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            position: relative;
            z-index: 1;
        }
        
        .tribute-hero p {
            color: #FFD700;
            font-size: 1.3rem;
            text-align: center;
            margin-bottom: 0;
            position: relative;
            z-index: 1;
        }
        
        .researcher-card {
            background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
            border: none;
            border-radius: 15px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .researcher-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: linear-gradient(180deg, #0B3D91, #FC3D21);
        }
        
        .researcher-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(11, 61, 145, 0.2);
        }
        
        .researcher-name {
            color: #0B3D91;
            font-size: 1.4rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        
        .researcher-role {
            color: #FC3D21;
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 0.3rem;
        }
        
        .researcher-affiliation {
            color: #666;
            font-size: 0.9rem;
            margin-bottom: 1rem;
        }
        
        .stats-container {
            background: linear-gradient(135deg, #0B3D91 0%, #1e3c72 100%);
            padding: 2rem;
            border-radius: 15px;
            margin: 1rem 0;
            color: white;
        }
        
        .stat-item {
            text-align: center;
            padding: 1rem;
        }
        
        .stat-number {
            font-size: 2.5rem;
            font-weight: 700;
            color: #FFD700;
            display: block;
        }
        
        .stat-label {
            font-size: 0.9rem;
            color: #ccc;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .expertise-tag {
            display: inline-block;
            background: linear-gradient(45deg, #0B3D91, #4B0082);
            color: white;
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.8rem;
            margin: 0.2rem;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        
        .collaboration-badge {
            background: linear-gradient(45deg, #FC3D21, #FF6B35);
            color: white;
            padding: 0.2rem 0.6rem;
            border-radius: 15px;
            font-size: 0.7rem;
            font-weight: 600;
        }
        
        .tribute-section {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 2rem;
            border-radius: 15px;
            margin: 2rem 0;
            border-left: 5px solid #0B3D91;
        }
        
        .extraction-panel {
            background: linear-gradient(135deg, #0B3D91 0%, #1e3c72 100%);
            padding: 2rem;
            border-radius: 20px;
            margin: 2rem 0;
            color: white;
            text-align: center;
        }
        
        .extraction-button {
            background: linear-gradient(45deg, #FC3D21, #FF6B35);
            color: white;
            border: none;
            padding: 1rem 2rem;
            border-radius: 50px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 5px 15px rgba(252, 61, 33, 0.4);
        }
        
        .extraction-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(252, 61, 33, 0.6);
        }
        
        .progress-container {
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 1rem;
            margin: 1rem 0;
        }
        
        .institution-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            border-top: 3px solid #0B3D91;
            transition: all 0.3s ease;
        }
        
        .institution-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        }
        
        .hero-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 2rem 0;
        }
        
        .hero-stat-card {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 1.5rem;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        .hero-stat-number {
            font-size: 2.5rem;
            font-weight: 700;
            color: #FFD700;
            display: block;
        }
        
        .hero-stat-label {
            color: white;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .search-container {
            background: white;
            border-radius: 50px;
            padding: 0.5rem 1.5rem;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            margin: 1rem 0;
        }
        
        .timeline-item {
            position: relative;
            padding-left: 2rem;
            margin: 1rem 0;
        }
        
        .timeline-item::before {
            content: '';
            position: absolute;
            left: 0;
            top: 0.5rem;
            width: 12px;
            height: 12px;
            background: #0B3D91;
            border-radius: 50%;
        }
        
        .timeline-item::after {
            content: '';
            position: absolute;
            left: 5px;
            top: 1.2rem;
            width: 2px;
            height: calc(100% + 1rem);
            background: #e9ecef;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def render_tribute_hero(self, title: str, subtitle: str, stats: Dict[str, Any] = None):
        """Render stunning hero section for tribute"""
        self.inject_tribute_css()
        
        st.markdown(f"""
        <div class="tribute-hero">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if stats:
            st.markdown('<div class="hero-stats">', unsafe_allow_html=True)
            
            cols = st.columns(len(stats))
            for i, (label, value) in enumerate(stats.items()):
                with cols[i]:
                    st.markdown(f"""
                    <div class="hero-stat-card">
                        <span class="hero-stat-number">{value}</span>
                        <span class="hero-stat-label">{label}</span>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    def render_researcher_card(self, researcher: Dict[str, Any], featured: bool = False):
        """Render beautiful researcher card"""
        
        card_class = "researcher-card featured" if featured else "researcher-card"
        
        # Build expertise tags
        expertise_html = ""
        if researcher.get('expertise_areas'):
            for area in researcher['expertise_areas'][:5]:
                expertise_html += f'<span class="expertise-tag">{area}</span>'
        
        # Build collaboration badge
        collab_html = ""
        if researcher.get('studies', 0) > 10:
            collab_html = f'<span class="collaboration-badge">🏆 Top Contributor</span>'
        elif researcher.get('studies', 0) > 5:
            collab_html = f'<span class="collaboration-badge">⭐ Active Researcher</span>'
        
        st.markdown(f"""
        <div class="{card_class}">
            <div class="researcher-name">
                👨‍🔬 {researcher['name']} {collab_html}
            </div>
            <div class="researcher-role">
                {researcher.get('role', 'Researcher')}
            </div>
            <div class="researcher-affiliation">
                🏛️ {researcher.get('affiliation', 'Unknown Institution')}
            </div>
            <div style="margin: 1rem 0;">
                <strong>📊 {researcher.get('studies', 0)} OSDR Studies</strong>
            </div>
            <div>
                {expertise_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def render_extraction_panel(self, total_studies: int):
        """Render stunning extraction panel"""
        
        st.markdown(f"""
        <div class="extraction-panel">
            <h2>🚀 Discover Every Space Biology Hero</h2>
            <p>Extract and honor ALL researchers from your {total_studies} OSDR studies</p>
            <p>Build the most comprehensive space biology researcher database ever created!</p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_stats_dashboard(self, stats: Dict[str, Any]):
        """Render beautiful stats dashboard"""
        
        st.markdown('<div class="stats-container">', unsafe_allow_html=True)
        
        cols = st.columns(len(stats))
        for i, (label, value) in enumerate(stats.items()):
            with cols[i]:
                st.markdown(f"""
                <div class="stat-item">
                    <span class="stat-number">{value}</span>
                    <span class="stat-label">{label}</span>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_institution_showcase(self, institutions: List[Dict[str, Any]]):
        """Render beautiful institution showcase"""
        
        for institution in institutions:
            st.markdown(f"""
            <div class="institution-card">
                <h3 style="color: #0B3D91; margin-bottom: 0.5rem;">
                    🏛️ {institution['name']}
                </h3>
                <p style="color: #666; margin-bottom: 1rem;">
                    📍 {institution.get('location', 'Unknown')} • 
                    📅 Est. {institution.get('established', 'Unknown')}
                </p>
                <p style="margin-bottom: 1rem;">
                    {institution.get('description', 'Leading research institution')}
                </p>
                <div>
                    {' '.join([f'<span class="expertise-tag">{spec}</span>' for spec in institution.get('specialties', [])[:3]])}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    def render_search_interface(self):
        """Render beautiful search interface"""
        
        st.markdown('<div class="search-container">', unsafe_allow_html=True)
        search_term = st.text_input(
            "",
            placeholder="🔍 Search researchers by name, institution, or expertise...",
            key="researcher_search",
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        return search_term
    
    def render_progress_animation(self, progress: float, status: str):
        """Render animated progress indicator"""
        
        st.markdown(f"""
        <div class="progress-container">
            <h4 style="color: white; margin-bottom: 1rem;">🔍 {status}</h4>
            <div style="background: rgba(255,255,255,0.2); border-radius: 10px; height: 20px; overflow: hidden;">
                <div style="background: linear-gradient(45deg, #FFD700, #FFA500); height: 100%; width: {progress*100}%; transition: width 0.3s ease; border-radius: 10px;"></div>
            </div>
            <p style="color: #ccc; margin-top: 0.5rem; font-size: 0.9rem;">
                {progress*100:.1f}% Complete
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_collaboration_network_viz(self, researchers: List[Dict[str, Any]]):
        """Render stunning collaboration network visualization"""
        
        if len(researchers) < 2:
            return
        
        # Create network data
        import networkx as nx
        import plotly.graph_objects as go
        
        G = nx.Graph()
        
        # Add nodes
        for researcher in researchers[:50]:  # Limit for performance
            G.add_node(
                researcher['name'],
                studies=researcher.get('studies', 0),
                affiliation=researcher.get('affiliation', 'Unknown')
            )
        
        # Add edges based on shared expertise or high study counts
        nodes = list(G.nodes())
        for i, node1 in enumerate(nodes):
            for node2 in nodes[i+1:i+10]:  # Limit connections
                if G.nodes[node1]['studies'] > 5 and G.nodes[node2]['studies'] > 5:
                    G.add_edge(node1, node2)
        
        # Create plotly visualization
        pos = nx.spring_layout(G, k=3, iterations=50)
        
        # Edge traces
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1, color='rgba(11, 61, 145, 0.3)'),
            hoverinfo='none',
            mode='lines'
        )
        
        # Node traces
        node_x = []
        node_y = []
        node_text = []
        node_size = []
        
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(f"{node}<br>Studies: {G.nodes[node]['studies']}")
            node_size.append(max(10, G.nodes[node]['studies'] * 2))
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=[node.split()[0] for node in G.nodes()],  # First name only
            hovertext=node_text,
            textposition="middle center",
            marker=dict(
                size=node_size,
                color='#0B3D91',
                line=dict(width=2, color='white')
            )
        )
        
        fig = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(
                           title='🤝 Space Biology Research Collaboration Network',
                           titlefont_size=16,
                           showlegend=False,
                           hovermode='closest',
                           margin=dict(b=20,l=5,r=5,t=40),
                           annotations=[ dict(
                               text="Connections show research collaborations and shared expertise",
                               showarrow=False,
                               xref="paper", yref="paper",
                               x=0.005, y=-0.002,
                               xanchor='left', yanchor='bottom',
                               font=dict(color='gray', size=12)
                           )],
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           plot_bgcolor='rgba(0,0,0,0)',
                           paper_bgcolor='rgba(0,0,0,0)'
                       ))
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_tribute_message(self):
        """Render inspiring tribute message"""
        
        st.markdown("""
        <div class="tribute-section">
            <h2 style="color: #0B3D91; text-align: center; margin-bottom: 2rem;">
                🙏 A Tribute to Space Biology Heroes
            </h2>
            
            <div style="text-align: center; font-size: 1.1rem; line-height: 1.8; color: #333;">
                <p><strong>This platform is dedicated to every researcher, scientist, and visionary who dares to ask:</strong></p>
                
                <p style="font-style: italic; color: #0B3D91; font-size: 1.2rem;">
                    "How does life adapt, survive, and thrive beyond Earth?"
                </p>
                
                <div style="margin: 2rem 0; display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem;">
                    <div>
                        🚀 <strong>Risk their lives</strong><br>
                        <small>Conducting experiments in the harsh environment of space</small>
                    </div>
                    <div>
                        🔬 <strong>Dedicate their careers</strong><br>
                        <small>To advancing our understanding of life beyond Earth</small>
                    </div>
                    <div>
                        🌱 <strong>Pioneer new frontiers</strong><br>
                        <small>In astrobiology, space medicine, and space agriculture</small>
                    </div>
                    <div>
                        🤝 <strong>Collaborate globally</strong><br>
                        <small>Across nations and institutions for humanity's benefit</small>
                    </div>
                </div>
                
                <p style="font-size: 1.3rem; color: #FC3D21; font-weight: 600; margin: 2rem 0;">
                    "The exploration of space will go ahead, whether we join in it or not,<br>
                    and it is one of the great adventures of all time."<br>
                    <small style="color: #666;">— John F. Kennedy</small>
                </p>
                
                <p style="font-size: 1.1rem; color: #0B3D91;">
                    <strong>Thank you to every researcher whose work advances humanity's greatest adventure.</strong>
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Global instance
tribute_ui = TributeUIComponents()