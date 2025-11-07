#!/usr/bin/env python3
"""
Advanced Research Analytics for NASA OSDR
Provides sophisticated analytics and insights for space biology research.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import networkx as nx
from datetime import datetime, timedelta
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import scipy.stats as stats

@dataclass
class ResearchMetric:
    """Research performance metric"""
    name: str
    value: float
    unit: str
    trend: str  # "up", "down", "stable"
    description: str
    benchmark: Optional[float] = None

class ResearchAnalytics:
    """Advanced analytics for space biology research"""
    
    def __init__(self):
        self.color_palette = px.colors.qualitative.Set3
    
    def get_real_research_data(self) -> pd.DataFrame:
        """Get real research data from MongoDB OSDR database - NO DEMO DATA"""
        try:
            from config import MONGO_URI
            from pymongo import MongoClient
            import certifi
            
            # Connect to real database
            client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
            db = client.nasa_osdr
            collection = db.studies
            
            # Get real studies data with all available fields
            studies = list(collection.find({}, {
                "study_id": 1,
                "title": 1, 
                "organism": 1,
                "factor": 1,
                "assay_type": 1,
                "description": 1,
                "publication_date": 1,
                "sample_count": 1,
                "data_files": 1,
                "_id": 0
            }))
            
            if studies:
                df = pd.DataFrame(studies)
                
                # Only use real data - no simulated fields
                # If fields don't exist in real data, don't add them
                if "publication_date" not in df.columns:
                    st.warning("⚠️ Publication dates not available in OSDR data")
                if "sample_count" not in df.columns:
                    st.warning("⚠️ Sample counts not available in OSDR data")
                
                return df
            else:
                st.error("❌ No studies found in OSDR database")
                return pd.DataFrame()  # Return empty DataFrame instead of demo data
                
        except Exception as e:
            st.error(f"❌ Could not connect to OSDR database: {e}")
            st.info("🔧 Please check your MongoDB connection in config.py")
            return pd.DataFrame()  # Return empty DataFrame instead of demo data
    
    def get_real_osdr_statistics(self) -> Dict[str, Any]:
        """Get real statistics from OSDR database - NO SIMULATED DATA"""
        try:
            from config import MONGO_URI
            from pymongo import MongoClient
            import certifi
            
            client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
            db = client.nasa_osdr
            collection = db.studies
            
            # Real aggregation queries
            stats = {}
            
            # Total studies
            stats["total_studies"] = collection.count_documents({})
            
            # Organism distribution
            organism_pipeline = [
                {"$group": {"_id": "$organism", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            stats["organisms"] = list(collection.aggregate(organism_pipeline))
            
            # Factor distribution
            factor_pipeline = [
                {"$group": {"_id": "$factor", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            stats["factors"] = list(collection.aggregate(factor_pipeline))
            
            # Assay type distribution
            assay_pipeline = [
                {"$group": {"_id": "$assay_type", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            stats["assay_types"] = list(collection.aggregate(assay_pipeline))
            
            return stats
            
        except Exception as e:
            st.error(f"❌ Could not get OSDR statistics: {e}")
            return {}
    
    def calculate_real_research_metrics(self, stats: Dict[str, Any]) -> List[ResearchMetric]:
        """Calculate metrics from real OSDR data only"""
        metrics = []
        
        if not stats:
            return metrics
        
        # Total studies in database
        if "total_studies" in stats:
            metrics.append(ResearchMetric(
                name="Total OSDR Studies",
                value=float(stats["total_studies"]),
                unit="studies",
                trend="stable",
                description="Total studies in NASA OSDR database"
            ))
        
        # Organism diversity
        if "organisms" in stats and stats["organisms"]:
            organism_count = len(stats["organisms"])
            metrics.append(ResearchMetric(
                name="Organism Types",
                value=float(organism_count),
                unit="species",
                trend="stable", 
                description="Number of different organisms studied"
            ))
        
        # Factor diversity
        if "factors" in stats and stats["factors"]:
            factor_count = len(stats["factors"])
            metrics.append(ResearchMetric(
                name="Research Factors",
                value=float(factor_count),
                unit="factors",
                trend="stable",
                description="Number of different space factors studied"
            ))
        
        # Assay diversity
        if "assay_types" in stats and stats["assay_types"]:
            assay_count = len(stats["assay_types"])
            metrics.append(ResearchMetric(
                name="Assay Types",
                value=float(assay_count),
                unit="assays",
                trend="stable",
                description="Number of different assay types used"
            ))
        
        return metrics
    
    def render_research_overview_dashboard(self):
        """Render research overview using REAL OSDR data only"""
        st.subheader("📊 OSDR Research Analytics - Real Data Only")
        
        # Get real statistics from OSDR database
        stats = self.get_real_osdr_statistics()
        
        if not stats:
            st.error("❌ Unable to connect to OSDR database")
            st.info("🔧 Please check your MongoDB connection settings")
            return
        
        # Show data source confirmation
        st.success("✅ **Live OSDR Data**: All analytics based on your actual NASA OSDR database")
        
        # Calculate real metrics
        metrics = self.calculate_real_research_metrics(stats)
        
        if metrics:
            # Key metrics row
            cols = st.columns(len(metrics))
            for i, metric in enumerate(metrics):
                with cols[i]:
                    st.metric(
                        label=metric.name,
                        value=f"{metric.value:.0f} {metric.unit}",
                        help=metric.description
                    )
        
        # Real data visualizations
        st.subheader("📈 OSDR Database Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Organism distribution from real data
            if "organisms" in stats and stats["organisms"]:
                organism_data = pd.DataFrame(stats["organisms"])
                organism_data.columns = ["Organism", "Study Count"]
                
                fig = px.bar(
                    organism_data.head(10),
                    x="Study Count",
                    y="Organism",
                    orientation="h",
                    title="Top 10 Organisms in OSDR",
                    labels={"Study Count": "Number of Studies"}
                )
                fig.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Factor distribution from real data
            if "factors" in stats and stats["factors"]:
                factor_data = pd.DataFrame(stats["factors"])
                factor_data.columns = ["Factor", "Study Count"]
                
                fig = px.pie(
                    factor_data.head(8),
                    values="Study Count",
                    names="Factor",
                    title="Research Factors in OSDR"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Assay type analysis
        if "assay_types" in stats and stats["assay_types"]:
            st.subheader("🔬 Assay Type Distribution")
            assay_data = pd.DataFrame(stats["assay_types"])
            assay_data.columns = ["Assay Type", "Study Count"]
            
            fig = px.bar(
                assay_data.head(10),
                x="Assay Type",
                y="Study Count",
                title="Assay Types in OSDR Database"
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
    
    def render_organism_factor_analysis(self):
        """Render organism-factor interaction analysis using REAL OSDR data"""
        st.subheader("🧬 Organism-Factor Analysis - Real OSDR Data")
        
        # Get real data
        df = self.get_real_research_data()
        
        if df.empty:
            st.error("❌ No OSDR data available for analysis")
            return
        
        st.success("✅ Analysis based on real OSDR studies")
        
        # Check if required columns exist
        if "organism" not in df.columns or "factor" not in df.columns:
            st.warning("⚠️ Organism or factor data not available in current OSDR dataset")
            return
        
        # Create organism-factor heatmap from real data
        pivot_table = df.groupby(["organism", "factor"]).size().reset_index(name="study_count")
        
        if not pivot_table.empty:
            pivot_matrix = pivot_table.pivot(index="organism", columns="factor", values="study_count").fillna(0)
            
            fig = px.imshow(
                pivot_matrix,
                title="OSDR Research Coverage: Organism × Space Factor",
                labels=dict(x="Space Factor", y="Organism", color="Study Count"),
                aspect="auto"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Real research coverage analysis
            st.subheader("📊 Research Coverage Summary")
            
            total_combinations = len(pivot_matrix.index) * len(pivot_matrix.columns)
            covered_combinations = (pivot_matrix > 0).sum().sum()
            coverage_percentage = (covered_combinations / total_combinations) * 100
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Organisms", len(pivot_matrix.index))
            with col2:
                st.metric("Total Factors", len(pivot_matrix.columns))
            with col3:
                st.metric("Coverage", f"{coverage_percentage:.1f}%")
        else:
            st.warning("⚠️ No organism-factor combinations found in current dataset")
    
    def render_data_completeness_analysis(self):
        """Render data completeness analysis using REAL OSDR data"""
        st.subheader("🎯 OSDR Data Completeness Analysis")
        
        # Get real data
        df = self.get_real_research_data()
        
        if df.empty:
            st.error("❌ No OSDR data available for analysis")
            return
        
        st.success("✅ Analysis based on real OSDR studies")
        
        # Analyze data completeness
        st.subheader("📊 Field Completeness")
        
        completeness_data = []
        for column in df.columns:
            non_null_count = df[column].notna().sum()
            total_count = len(df)
            completeness_pct = (non_null_count / total_count) * 100
            
            completeness_data.append({
                "Field": column,
                "Complete Records": non_null_count,
                "Total Records": total_count,
                "Completeness %": completeness_pct
            })
        
        completeness_df = pd.DataFrame(completeness_data)
        
        # Visualize completeness
        fig = px.bar(
            completeness_df,
            x="Field",
            y="Completeness %",
            title="Data Completeness by Field",
            color="Completeness %",
            color_continuous_scale="RdYlGn"
        )
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
        
        # Show completeness table
        st.subheader("📋 Completeness Details")
        st.dataframe(completeness_df, use_container_width=True)
        
        # Data quality insights
        st.subheader("💡 Data Quality Insights")
        
        high_completeness = completeness_df[completeness_df["Completeness %"] >= 90]
        low_completeness = completeness_df[completeness_df["Completeness %"] < 50]
        
        if not high_completeness.empty:
            st.success(f"✅ **High Quality Fields**: {', '.join(high_completeness['Field'].tolist())}")
        
        if not low_completeness.empty:
            st.warning(f"⚠️ **Fields Needing Attention**: {', '.join(low_completeness['Field'].tolist())}")
        
        # Sample data preview
        st.subheader("🔍 Sample Data Preview")
        st.dataframe(df.head(10), use_container_width=True)
    
    def render_research_relationships_analysis(self):
        """Render research relationships analysis using REAL OSDR data"""
        st.subheader("🕸️ OSDR Research Relationships")
        
        # Get real data
        df = self.get_real_research_data()
        
        if df.empty:
            st.error("❌ No OSDR data available for analysis")
            return
        
        st.success("✅ Analysis based on real OSDR studies")
        
        # Check required columns
        required_cols = ["study_id", "organism", "factor"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            st.warning(f"⚠️ Missing columns for network analysis: {', '.join(missing_cols)}")
            return
        
        # Create network based on real study relationships
        G = nx.Graph()
        
        # Add nodes for studies
        for _, study in df.iterrows():
            G.add_node(study["study_id"], 
                      organism=study["organism"],
                      factor=study["factor"])
        
        # Add edges for studies with shared characteristics
        studies = df.to_dict("records")
        edge_count = 0
        
        for i, study1 in enumerate(studies):
            for study2 in studies[i+1:]:
                # Connect studies with same organism or factor
                if (study1["organism"] == study2["organism"] or 
                    study1["factor"] == study2["factor"]):
                    G.add_edge(study1["study_id"], study2["study_id"])
                    edge_count += 1
                    
                # Limit edges for performance
                if edge_count > 1000:
                    break
            if edge_count > 1000:
                break
        
        # Network metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Studies (Nodes)", len(G.nodes()))
        with col2:
            st.metric("Relationships (Edges)", len(G.edges()))
        with col3:
            if len(G.nodes()) > 1:
                density = nx.density(G)
                st.metric("Network Density", f"{density:.3f}")
        
        # Most connected studies (real data)
        if len(G.nodes()) > 0:
            degree_centrality = nx.degree_centrality(G)
            top_studies = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
            
            st.subheader("🔗 Most Connected Studies")
            
            for study_id, centrality_score in top_studies:
                study_info = df[df["study_id"] == study_id].iloc[0]
                connections = G.degree(study_id)
                st.write(f"• **{study_id}**: {study_info['organism']} × {study_info['factor']} ({connections} connections)")
        
        # Research clusters
        if len(G.nodes()) > 2:
            st.subheader("🎯 Research Clusters")
            
            # Find connected components
            components = list(nx.connected_components(G))
            largest_components = sorted(components, key=len, reverse=True)[:5]
            
            for i, component in enumerate(largest_components):
                if len(component) > 1:
                    st.write(f"**Cluster {i+1}**: {len(component)} related studies")
                    
                    # Show sample studies from cluster
                    sample_studies = list(component)[:3]
                    for study_id in sample_studies:
                        study_info = df[df["study_id"] == study_id].iloc[0]
                        st.write(f"  - {study_id}: {study_info['organism']} × {study_info['factor']}")
    
    def render_research_insights(self):
        """Render research insights from REAL OSDR data"""
        st.subheader("💡 OSDR Research Insights")
        
        # Get real statistics
        stats = self.get_real_osdr_statistics()
        
        if not stats:
            st.error("❌ Unable to generate insights - no OSDR data available")
            return
        
        st.success("✅ Insights based on real OSDR database")
        
        # Research focus areas
        st.subheader("🎯 Research Focus Areas")
        
        if "organisms" in stats and stats["organisms"]:
            top_organism = stats["organisms"][0]
            st.info(f"🧬 **Most Studied Organism**: {top_organism['_id']} ({top_organism['count']} studies)")
        
        if "factors" in stats and stats["factors"]:
            top_factor = stats["factors"][0]
            st.info(f"🚀 **Most Studied Factor**: {top_factor['_id']} ({top_factor['count']} studies)")
        
        if "assay_types" in stats and stats["assay_types"]:
            top_assay = stats["assay_types"][0]
            st.info(f"🔬 **Most Used Assay**: {top_assay['_id']} ({top_assay['count']} studies)")
        
        # Research diversity analysis
        st.subheader("📊 Research Diversity")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if "organisms" in stats:
                organism_diversity = len(stats["organisms"])
                st.metric("Organism Diversity", f"{organism_diversity} species")
                
                # Show distribution
                if organism_diversity > 1:
                    top_3_organisms = stats["organisms"][:3]
                    total_top_3 = sum(org["count"] for org in top_3_organisms)
                    total_studies = stats.get("total_studies", 1)
                    concentration = (total_top_3 / total_studies) * 100
                    
                    st.write(f"**Top 3 organisms represent {concentration:.1f}% of studies**")
        
        with col2:
            if "factors" in stats:
                factor_diversity = len(stats["factors"])
                st.metric("Factor Diversity", f"{factor_diversity} factors")
                
                # Show distribution
                if factor_diversity > 1:
                    top_3_factors = stats["factors"][:3]
                    total_top_3 = sum(factor["count"] for factor in top_3_factors)
                    total_studies = stats.get("total_studies", 1)
                    concentration = (total_top_3 / total_studies) * 100
                    
                    st.write(f"**Top 3 factors represent {concentration:.1f}% of studies**")
        
        # Research recommendations based on real data
        st.subheader("🎯 Data-Driven Recommendations")
        
        recommendations = []
        
        # Check for research gaps
        if "organisms" in stats and len(stats["organisms"]) > 0:
            organism_counts = [org["count"] for org in stats["organisms"]]
            if len(organism_counts) > 1:
                max_count = max(organism_counts)
                min_count = min(organism_counts)
                if max_count > min_count * 3:
                    underrepresented = [org["_id"] for org in stats["organisms"] if org["count"] == min_count]
                    recommendations.append(f"Consider more studies on underrepresented organisms: {', '.join(underrepresented[:3])}")
        
        if "factors" in stats and len(stats["factors"]) > 0:
            factor_counts = [factor["count"] for factor in stats["factors"]]
            if len(factor_counts) > 1:
                max_count = max(factor_counts)
                min_count = min(factor_counts)
                if max_count > min_count * 3:
                    underrepresented = [factor["_id"] for factor in stats["factors"] if factor["count"] == min_count]
                    recommendations.append(f"Opportunity to expand research on: {', '.join(underrepresented[:3])}")
        
        for rec in recommendations:
            st.info(f"💡 {rec}")
        
        if not recommendations:
            st.success("✅ Research appears well-balanced across organisms and factors")
    
    def render_complete_analytics_dashboard(self):
        """Render the complete research analytics dashboard - REAL DATA ONLY"""
        st.title("🔬 NASA OSDR Research Analytics - Real Data")
        
        # Data source verification
        from data_source_manager import data_source_manager
        data_source_manager.add_data_accuracy_note("osdr_studies", "Research Analytics")
        
        # Analytics navigation
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Overview",
            "🧬 Organism Analysis", 
            "🎯 Data Completeness",
            "🕸️ Relationships",
            "💡 Insights"
        ])
        
        with tab1:
            self.render_research_overview_dashboard()
        
        with tab2:
            self.render_organism_factor_analysis()
        
        with tab3:
            self.render_data_completeness_analysis()
        
        with tab4:
            self.render_research_relationships_analysis()
        
        with tab5:
            self.render_research_insights()

# Global instance
research_analytics = ResearchAnalytics()