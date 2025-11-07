#!/usr/bin/env python3
"""
Researcher Analytics for OSDR Tribute System
Provides insights and analytics about the space biology research community.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, List, Any
from collections import Counter, defaultdict
import networkx as nx

class ResearcherAnalytics:
    """Analytics for the space biology research community"""
    
    def __init__(self):
        self.color_palette = px.colors.qualitative.Set3
    
    def analyze_researcher_network(self, researchers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the collaboration network of researchers"""
        
        # Create collaboration network based on shared studies
        G = nx.Graph()
        
        # Add researchers as nodes
        for researcher in researchers:
            G.add_node(
                researcher['name'],
                studies=researcher.get('studies', 0),
                affiliation=researcher.get('affiliation', 'Unknown'),
                expertise=researcher.get('expertise_areas', [])
            )
        
        # Add edges for researchers who worked on same studies
        study_to_researchers = defaultdict(list)
        
        for researcher in researchers:
            if researcher.get('study_ids'):
                for study_id in researcher['study_ids']:
                    study_to_researchers[study_id].append(researcher['name'])
        
        # Create edges between researchers who collaborated
        collaboration_count = defaultdict(int)
        
        for study_id, researcher_names in study_to_researchers.items():
            if len(researcher_names) > 1:
                for i, name1 in enumerate(researcher_names):
                    for name2 in researcher_names[i+1:]:
                        collaboration_count[(name1, name2)] += 1
        
        # Add edges with weights
        for (name1, name2), weight in collaboration_count.items():
            if weight >= 2:  # Only include researchers who collaborated on 2+ studies
                G.add_edge(name1, name2, weight=weight)
        
        return {
            'graph': G,
            'total_nodes': len(G.nodes()),
            'total_edges': len(G.edges()),
            'collaboration_pairs': len(collaboration_count),
            'density': nx.density(G) if len(G.nodes()) > 1 else 0
        }
    
    def render_researcher_overview(self, researchers: List[Dict[str, Any]]):
        """Render comprehensive researcher overview"""
        
        if not researchers:
            st.warning("No researcher data available for analysis")
            return
        
        st.subheader("👥 Space Biology Research Community Overview")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_researchers = len(researchers)
            st.metric("Total Researchers", total_researchers)
        
        with col2:
            total_contributions = sum(r.get('studies', 0) for r in researchers)
            st.metric("Total Study Contributions", total_contributions)
        
        with col3:
            affiliations = [r.get('affiliation', 'Unknown') for r in researchers if r.get('affiliation') != 'Unknown']
            unique_affiliations = len(set(affiliations))
            st.metric("Research Institutions", unique_affiliations)
        
        with col4:
            avg_contributions = total_contributions / total_researchers if total_researchers > 0 else 0
            st.metric("Avg Studies per Researcher", f"{avg_contributions:.1f}")
        
        # Research productivity distribution
        st.subheader("📊 Research Productivity Distribution")
        
        study_counts = [r.get('studies', 0) for r in researchers if r.get('studies', 0) > 0]
        
        if study_counts:
            fig = px.histogram(
                x=study_counts,
                nbins=20,
                title="Distribution of Study Contributions per Researcher",
                labels={'x': 'Number of Studies', 'y': 'Number of Researchers'}
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        # Top contributors
        st.subheader("🏆 Most Prolific Researchers")
        
        top_researchers = sorted(researchers, key=lambda x: x.get('studies', 0), reverse=True)[:15]
        
        if top_researchers:
            names = [r['name'] for r in top_researchers]
            studies = [r.get('studies', 0) for r in top_researchers]
            
            fig = px.bar(
                x=studies,
                y=names,
                orientation='h',
                title="Top 15 Researchers by Study Count",
                labels={'x': 'Number of Studies', 'y': 'Researcher'}
            )
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
    
    def render_institutional_analysis(self, researchers: List[Dict[str, Any]]):
        """Render institutional analysis"""
        
        st.subheader("🏛️ Institutional Research Landscape")
        
        # Count researchers by institution
        institution_counts = Counter()
        institution_studies = defaultdict(int)
        
        for researcher in researchers:
            affiliation = researcher.get('affiliation', 'Unknown')
            if affiliation != 'Unknown':
                institution_counts[affiliation] += 1
                institution_studies[affiliation] += researcher.get('studies', 0)
        
        if institution_counts:
            # Top institutions by researcher count
            col1, col2 = st.columns(2)
            
            with col1:
                top_institutions = institution_counts.most_common(10)
                
                institutions = [inst for inst, count in top_institutions]
                counts = [count for inst, count in top_institutions]
                
                fig = px.pie(
                    values=counts,
                    names=institutions,
                    title="Top 10 Institutions by Researcher Count"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Top institutions by total studies
                top_by_studies = sorted(
                    institution_studies.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
                
                institutions = [inst for inst, studies in top_by_studies]
                studies = [studies for inst, studies in top_by_studies]
                
                fig = px.bar(
                    x=studies,
                    y=institutions,
                    orientation='h',
                    title="Top 10 Institutions by Total Studies",
                    labels={'x': 'Total Studies', 'y': 'Institution'}
                )
                fig.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
            
            # Institutional productivity
            st.subheader("📈 Institutional Research Productivity")
            
            productivity_data = []
            for institution, researcher_count in institution_counts.most_common(15):
                total_studies = institution_studies[institution]
                avg_studies = total_studies / researcher_count
                
                productivity_data.append({
                    'Institution': institution,
                    'Researchers': researcher_count,
                    'Total Studies': total_studies,
                    'Avg Studies per Researcher': avg_studies
                })
            
            productivity_df = pd.DataFrame(productivity_data)
            
            fig = px.scatter(
                productivity_df,
                x='Researchers',
                y='Total Studies',
                size='Avg Studies per Researcher',
                hover_name='Institution',
                title="Institutional Research Output vs Team Size",
                labels={
                    'Researchers': 'Number of Researchers',
                    'Total Studies': 'Total Studies Contributed'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def render_expertise_analysis(self, researchers: List[Dict[str, Any]]):
        """Render expertise and research area analysis"""
        
        st.subheader("🧬 Research Expertise Landscape")
        
        # Collect all expertise areas
        all_expertise = []
        expertise_to_researchers = defaultdict(list)
        
        for researcher in researchers:
            if researcher.get('expertise_areas'):
                for area in researcher['expertise_areas']:
                    all_expertise.append(area)
                    expertise_to_researchers[area].append(researcher['name'])
        
        if all_expertise:
            # Top research areas
            expertise_counts = Counter(all_expertise)
            top_expertise = expertise_counts.most_common(15)
            
            col1, col2 = st.columns(2)
            
            with col1:
                areas = [area for area, count in top_expertise]
                counts = [count for area, count in top_expertise]
                
                fig = px.bar(
                    x=counts,
                    y=areas,
                    orientation='h',
                    title="Top 15 Research Areas by Researcher Count",
                    labels={'x': 'Number of Researchers', 'y': 'Research Area'}
                )
                fig.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Research area network
                st.markdown("**Research Area Connections**")
                
                # Find researchers who work in multiple areas
                multi_area_researchers = [
                    r for r in researchers 
                    if r.get('expertise_areas') and len(r['expertise_areas']) > 1
                ]
                
                if multi_area_researchers:
                    st.metric("Interdisciplinary Researchers", len(multi_area_researchers))
                    
                    # Show top interdisciplinary researchers
                    interdisciplinary = sorted(
                        multi_area_researchers,
                        key=lambda x: len(x.get('expertise_areas', [])),
                        reverse=True
                    )[:5]
                    
                    st.markdown("**Most Interdisciplinary Researchers:**")
                    for researcher in interdisciplinary:
                        areas_count = len(researcher.get('expertise_areas', []))
                        st.markdown(f"• {researcher['name']}: {areas_count} research areas")
            
            # Expertise specialization analysis
            st.subheader("🎯 Research Specialization vs Breadth")
            
            specialization_data = []
            
            for researcher in researchers:
                if researcher.get('expertise_areas'):
                    num_areas = len(researcher['expertise_areas'])
                    num_studies = researcher.get('studies', 0)
                    
                    if num_studies > 0:
                        specialization_data.append({
                            'Researcher': researcher['name'],
                            'Research Areas': num_areas,
                            'Total Studies': num_studies,
                            'Studies per Area': num_studies / num_areas,
                            'Affiliation': researcher.get('affiliation', 'Unknown')
                        })
            
            if specialization_data:
                spec_df = pd.DataFrame(specialization_data)
                
                fig = px.scatter(
                    spec_df,
                    x='Research Areas',
                    y='Total Studies',
                    size='Studies per Area',
                    color='Affiliation',
                    hover_name='Researcher',
                    title="Research Specialization: Breadth vs Depth",
                    labels={
                        'Research Areas': 'Number of Research Areas',
                        'Total Studies': 'Total Studies Contributed'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
    
    def render_collaboration_network(self, researchers: List[Dict[str, Any]]):
        """Render collaboration network analysis"""
        
        st.subheader("🤝 Research Collaboration Network")
        
        # Analyze network
        network_analysis = self.analyze_researcher_network(researchers)
        
        # Network metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Researchers", network_analysis['total_nodes'])
        
        with col2:
            st.metric("Collaborations", network_analysis['total_edges'])
        
        with col3:
            st.metric("Collaboration Pairs", network_analysis['collaboration_pairs'])
        
        with col4:
            density = network_analysis['density']
            st.metric("Network Density", f"{density:.3f}")
        
        G = network_analysis['graph']
        
        if len(G.nodes()) > 0:
            # Most connected researchers
            if len(G.edges()) > 0:
                centrality = nx.degree_centrality(G)
                top_connected = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:10]
                
                st.markdown("**Most Connected Researchers:**")
                
                for name, centrality_score in top_connected:
                    connections = G.degree(name)
                    st.markdown(f"• **{name}**: {connections} collaborations (centrality: {centrality_score:.3f})")
            
            # Research communities
            if len(G.nodes()) > 5:
                st.subheader("🌐 Research Communities")
                
                # Find connected components (research communities)
                components = list(nx.connected_components(G))
                largest_components = sorted(components, key=len, reverse=True)[:5]
                
                for i, component in enumerate(largest_components):
                    if len(component) > 2:
                        st.markdown(f"**Research Community {i+1}**: {len(component)} researchers")
                        
                        # Show sample researchers from community
                        sample_researchers = list(component)[:5]
                        for researcher in sample_researchers:
                            affiliation = G.nodes[researcher].get('affiliation', 'Unknown')
                            st.markdown(f"  - {researcher} ({affiliation})")
                        
                        if len(component) > 5:
                            st.markdown(f"  - ... and {len(component) - 5} more researchers")
    
    def render_complete_researcher_analytics(self, researchers: List[Dict[str, Any]]):
        """Render complete researcher analytics dashboard"""
        
        if not researchers:
            st.warning("No researcher data available. Please extract researchers first.")
            return
        
        st.title("👥 Space Biology Research Community Analytics")
        st.markdown(f"*Comprehensive analysis of {len(researchers)} researchers from NASA OSDR*")
        
        # Analytics tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Overview",
            "🏛️ Institutions",
            "🧬 Expertise",
            "🤝 Collaboration"
        ])
        
        with tab1:
            self.render_researcher_overview(researchers)
        
        with tab2:
            self.render_institutional_analysis(researchers)
        
        with tab3:
            self.render_expertise_analysis(researchers)
        
        with tab4:
            self.render_collaboration_network(researchers)

# Global instance
researcher_analytics = ResearcherAnalytics()