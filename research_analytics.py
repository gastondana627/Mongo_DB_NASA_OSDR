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
    
    def generate_sample_research_data(self) -> pd.DataFrame:
        """Generate sample research data for demonstration"""
        np.random.seed(42)
        
        organisms = ["Mus musculus", "Rattus norvegicus", "Homo sapiens", "Arabidopsis thaliana", "Caenorhabditis elegans"]
        factors = ["Microgravity", "Ionizing Radiation", "Isolation", "Altered Atmosphere", "Hypergravity"]
        assays = ["RNA-seq", "Proteomics", "Metabolomics", "Microarray", "qPCR"]
        
        data = []
        for i in range(200):
            data.append({
                "study_id": f"OSD-{800 + i}",
                "organism": np.random.choice(organisms),
                "factor": np.random.choice(factors),
                "assay_type": np.random.choice(assays),
                "publication_date": datetime.now() - timedelta(days=np.random.randint(0, 1095)),
                "sample_count": np.random.randint(6, 48),
                "gene_count": np.random.randint(15000, 25000),
                "significant_genes": np.random.randint(100, 2000),
                "effect_size": np.random.normal(1.5, 0.5),
                "p_value": np.random.exponential(0.01),
                "citation_count": np.random.poisson(8),
                "data_quality_score": np.random.normal(85, 10),
                "processing_time_days": np.random.gamma(2, 15)
            })
        
        return pd.DataFrame(data)
    
    def calculate_research_metrics(self, df: pd.DataFrame) -> List[ResearchMetric]:
        """Calculate key research performance metrics"""
        metrics = []
        
        # Data production rate
        recent_studies = df[df["publication_date"] > datetime.now() - timedelta(days=365)]
        studies_per_month = len(recent_studies) / 12
        
        metrics.append(ResearchMetric(
            name="Studies per Month",
            value=studies_per_month,
            unit="studies",
            trend="up",
            description="Average number of studies published per month",
            benchmark=15.0
        ))
        
        # Average data quality
        avg_quality = df["data_quality_score"].mean()
        metrics.append(ResearchMetric(
            name="Data Quality Score",
            value=avg_quality,
            unit="points",
            trend="stable",
            description="Average data quality score across all studies",
            benchmark=80.0
        ))
        
        # Research impact (citations)
        avg_citations = df["citation_count"].mean()
        metrics.append(ResearchMetric(
            name="Average Citations",
            value=avg_citations,
            unit="citations",
            trend="up",
            description="Average citations per study",
            benchmark=10.0
        ))
        
        # Processing efficiency
        avg_processing = df["processing_time_days"].mean()
        metrics.append(ResearchMetric(
            name="Processing Time",
            value=avg_processing,
            unit="days",
            trend="down",
            description="Average time from data collection to publication",
            benchmark=45.0
        ))
        
        return metrics
    
    def render_research_overview_dashboard(self):
        """Render comprehensive research overview dashboard"""
        st.subheader("📊 Research Analytics Overview")
        
        # Generate sample data
        df = self.generate_sample_research_data()
        metrics = self.calculate_research_metrics(df)
        
        # Key metrics row
        cols = st.columns(len(metrics))
        for i, metric in enumerate(metrics):
            with cols[i]:
                delta = None
                if metric.benchmark:
                    delta = f"{metric.value - metric.benchmark:.1f}"
                
                st.metric(
                    label=metric.name,
                    value=f"{metric.value:.1f} {metric.unit}",
                    delta=delta,
                    help=metric.description
                )
        
        # Research trends over time
        st.subheader("📈 Research Trends")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Studies by organism over time
            df_monthly = df.groupby([df["publication_date"].dt.to_period("M"), "organism"]).size().reset_index()
            df_monthly["publication_date"] = df_monthly["publication_date"].astype(str)
            
            fig = px.line(
                df_monthly,
                x="publication_date",
                y=0,
                color="organism",
                title="Studies by Organism Over Time",
                labels={0: "Number of Studies"}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Research impact distribution
            fig = px.histogram(
                df,
                x="citation_count",
                nbins=20,
                title="Research Impact Distribution",
                labels={"citation_count": "Citations", "count": "Number of Studies"}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def render_organism_factor_analysis(self):
        """Render organism-factor interaction analysis"""
        st.subheader("🧬 Organism-Factor Interaction Analysis")
        
        df = self.generate_sample_research_data()
        
        # Create organism-factor heatmap
        pivot_table = df.groupby(["organism", "factor"]).size().reset_index(name="study_count")
        pivot_matrix = pivot_table.pivot(index="organism", columns="factor", values="study_count").fillna(0)
        
        fig = px.imshow(
            pivot_matrix,
            title="Research Coverage: Organism × Space Factor",
            labels=dict(x="Space Factor", y="Organism", color="Study Count"),
            aspect="auto"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Research gaps analysis
        st.subheader("🔍 Research Gap Analysis")
        
        # Find underrepresented combinations
        threshold = pivot_matrix.mean().mean()
        gaps = []
        
        for organism in pivot_matrix.index:
            for factor in pivot_matrix.columns:
                count = pivot_matrix.loc[organism, factor]
                if count < threshold:
                    gaps.append({
                        "organism": organism,
                        "factor": factor,
                        "current_studies": int(count),
                        "gap_score": threshold - count
                    })
        
        gaps_df = pd.DataFrame(gaps).sort_values("gap_score", ascending=False)
        
        if not gaps_df.empty:
            st.write("**Top Research Opportunities:**")
            for _, gap in gaps_df.head(5).iterrows():
                st.write(f"• **{gap['organism']}** × **{gap['factor']}**: {gap['current_studies']} studies (opportunity score: {gap['gap_score']:.1f})")
    
    def render_data_quality_analysis(self):
        """Render data quality and processing analysis"""
        st.subheader("🎯 Data Quality & Processing Analysis")
        
        df = self.generate_sample_research_data()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Quality score by assay type
            fig = px.box(
                df,
                x="assay_type",
                y="data_quality_score",
                title="Data Quality by Assay Type"
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Processing time vs quality correlation
            fig = px.scatter(
                df,
                x="processing_time_days",
                y="data_quality_score",
                color="assay_type",
                title="Processing Time vs Data Quality",
                trendline="ols"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Quality improvement recommendations
        st.subheader("💡 Quality Improvement Recommendations")
        
        # Analyze correlations
        quality_corr = df[["sample_count", "processing_time_days", "data_quality_score"]].corr()["data_quality_score"]
        
        recommendations = []
        if quality_corr["sample_count"] > 0.3:
            recommendations.append("Increase sample sizes to improve data quality")
        if quality_corr["processing_time_days"] < -0.3:
            recommendations.append("Reduce processing time to maintain data quality")
        
        for rec in recommendations:
            st.info(f"📋 {rec}")
    
    def render_research_network_analysis(self):
        """Render research collaboration and citation network"""
        st.subheader("🕸️ Research Network Analysis")
        
        df = self.generate_sample_research_data()
        
        # Create a simplified network based on shared organisms/factors
        G = nx.Graph()
        
        # Add nodes for studies
        for _, study in df.iterrows():
            G.add_node(study["study_id"], 
                      organism=study["organism"],
                      factor=study["factor"],
                      citations=study["citation_count"])
        
        # Add edges for studies with shared organisms or factors
        studies = df.to_dict("records")
        for i, study1 in enumerate(studies):
            for study2 in studies[i+1:i+10]:  # Limit connections for performance
                if (study1["organism"] == study2["organism"] or 
                    study1["factor"] == study2["factor"]):
                    G.add_edge(study1["study_id"], study2["study_id"])
        
        # Network metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Network Nodes", len(G.nodes()))
        with col2:
            st.metric("Network Edges", len(G.edges()))
        with col3:
            if len(G.nodes()) > 0:
                density = nx.density(G)
                st.metric("Network Density", f"{density:.3f}")
        
        # Most connected studies
        if len(G.nodes()) > 0:
            centrality = nx.degree_centrality(G)
            top_studies = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:5]
            
            st.write("**Most Connected Studies:**")
            for study_id, centrality_score in top_studies:
                study_info = df[df["study_id"] == study_id].iloc[0]
                st.write(f"• **{study_id}**: {study_info['organism']} × {study_info['factor']} (centrality: {centrality_score:.3f})")
    
    def render_predictive_analytics(self):
        """Render predictive analytics for research outcomes"""
        st.subheader("🔮 Predictive Research Analytics")
        
        df = self.generate_sample_research_data()
        
        # Predict citation potential
        st.write("**Citation Potential Prediction**")
        
        # Simple model features
        features = ["sample_count", "gene_count", "significant_genes", "data_quality_score"]
        X = df[features]
        y = df["citation_count"]
        
        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Simple correlation analysis (replace with ML model in production)
        correlations = df[features + ["citation_count"]].corr()["citation_count"].drop("citation_count")
        
        st.write("**Factors influencing citation potential:**")
        for feature, corr in correlations.items():
            direction = "📈" if corr > 0 else "📉"
            st.write(f"{direction} **{feature}**: correlation = {corr:.3f}")
        
        # Research success probability
        st.write("**Research Success Indicators**")
        
        success_threshold = df["citation_count"].quantile(0.75)
        df["high_impact"] = df["citation_count"] > success_threshold
        
        success_factors = df.groupby("high_impact")[features].mean()
        
        fig = go.Figure()
        
        for feature in features:
            fig.add_trace(go.Bar(
                name=feature,
                x=["Low Impact", "High Impact"],
                y=[success_factors.loc[False, feature], success_factors.loc[True, feature]]
            ))
        
        fig.update_layout(
            title="Success Factors: High vs Low Impact Studies",
            barmode="group"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    def render_complete_analytics_dashboard(self):
        """Render the complete research analytics dashboard"""
        st.title("🔬 Advanced Research Analytics")
        
        # Analytics navigation
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Overview",
            "🧬 Organism Analysis", 
            "🎯 Data Quality",
            "🕸️ Network Analysis",
            "🔮 Predictive Analytics"
        ])
        
        with tab1:
            self.render_research_overview_dashboard()
        
        with tab2:
            self.render_organism_factor_analysis()
        
        with tab3:
            self.render_data_quality_analysis()
        
        with tab4:
            self.render_research_network_analysis()
        
        with tab5:
            self.render_predictive_analytics()

# Global instance
research_analytics = ResearchAnalytics()