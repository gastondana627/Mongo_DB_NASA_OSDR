# node_click_handler.py

import streamlit as st
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

@dataclass
class NodeClickEvent:
    """Represents a node click event with context"""
    node_id: str
    node_type: str
    properties: Dict[str, Any]
    generated_query: str

class NodeType(Enum):
    """Supported node types for query generation"""
    STUDY = "Study"
    ORGANISM = "Organism"
    FACTOR = "Factor"
    ASSAY = "Assay"
    UNKNOWN = "Unknown"

class NodeClickHandler:
    """Handles node click events and generates contextual Cypher queries"""
    
    def __init__(self):
        # Query templates for different node types and interactions
        self.query_templates = {
            NodeType.STUDY: {
                "connections": "MATCH (s:Study {{study_id: '{study_id}'}})-[r]-(n) RETURN s, r, n LIMIT 20",
                "organisms": "MATCH (s:Study {{study_id: '{study_id}'}})-[:HAS_ORGANISM]->(o:Organism) RETURN s, o",
                "factors": "MATCH (s:Study {{study_id: '{study_id}'}})-[:HAS_FACTOR]->(f:Factor) RETURN s, f",
                "assays": "MATCH (s:Study {{study_id: '{study_id}'}})-[:HAS_ASSAY]->(a:Assay) RETURN s, a",
                "similar_studies": """
                    MATCH (s1:Study {{study_id: '{study_id}'}})-[:HAS_ORGANISM]->(o:Organism)<-[:HAS_ORGANISM]-(s2:Study)
                    WHERE s1 <> s2
                    RETURN s1, s2, o
                    LIMIT 10
                """
            },
            NodeType.ORGANISM: {
                "studies": "MATCH (o:Organism {{organism_name: '{organism_name}'}})<-[:HAS_ORGANISM]-(s:Study) RETURN o, s LIMIT 15",
                "studies_by_name": "MATCH (o:Organism)<-[:HAS_ORGANISM]-(s:Study) WHERE o.organism_name CONTAINS '{name}' RETURN o, s LIMIT 15",
                "factors": """
                    MATCH (o:Organism {{organism_name: '{organism_name}'}})<-[:HAS_ORGANISM]-(s:Study)-[:HAS_FACTOR]->(f:Factor)
                    RETURN o, s, f
                    LIMIT 15
                """,
                "related_organisms": """
                    MATCH (o1:Organism {{organism_name: '{organism_name}'}})<-[:HAS_ORGANISM]-(s:Study)-[:HAS_ORGANISM]->(o2:Organism)
                    WHERE o1 <> o2
                    RETURN o1, s, o2
                    LIMIT 10
                """
            },
            NodeType.FACTOR: {
                "studies": "MATCH (f:Factor {{factor_name: '{factor_name}'}})<-[:HAS_FACTOR]-(s:Study) RETURN f, s LIMIT 15",
                "studies_by_name": "MATCH (f:Factor)<-[:HAS_FACTOR]-(s:Study) WHERE f.factor_name CONTAINS '{name}' RETURN f, s LIMIT 15",
                "organisms": """
                    MATCH (f:Factor {{factor_name: '{factor_name}'}})<-[:HAS_FACTOR]-(s:Study)-[:HAS_ORGANISM]->(o:Organism)
                    RETURN f, s, o
                    LIMIT 15
                """,
                "related_factors": """
                    MATCH (f1:Factor {{factor_name: '{factor_name}'}})<-[:HAS_FACTOR]-(s:Study)-[:HAS_FACTOR]->(f2:Factor)
                    WHERE f1 <> f2
                    RETURN f1, s, f2
                    LIMIT 10
                """
            },
            NodeType.ASSAY: {
                "studies": "MATCH (a:Assay {{assay_name: '{assay_name}'}})<-[:HAS_ASSAY]-(s:Study) RETURN a, s LIMIT 15",
                "studies_by_name": "MATCH (a:Assay)<-[:HAS_ASSAY]-(s:Study) WHERE a.assay_name CONTAINS '{name}' RETURN a, s LIMIT 15",
                "organisms": """
                    MATCH (a:Assay {{assay_name: '{assay_name}'}})<-[:HAS_ASSAY]-(s:Study)-[:HAS_ORGANISM]->(o:Organism)
                    RETURN a, s, o
                    LIMIT 15
                """,
                "factors": """
                    MATCH (a:Assay {{assay_name: '{assay_name}'}})<-[:HAS_ASSAY]-(s:Study)-[:HAS_FACTOR]->(f:Factor)
                    RETURN a, s, f
                    LIMIT 15
                """
            }
        }
        
        # User-friendly descriptions for query types
        self.query_descriptions = {
            "connections": "Show all direct connections",
            "organisms": "Find associated organisms",
            "factors": "Find associated factors", 
            "assays": "Find associated assays",
            "studies": "Find studies using this",
            "studies_by_name": "Find studies by name match",
            "similar_studies": "Find similar studies",
            "related_organisms": "Find related organisms",
            "related_factors": "Find related factors"
        }
    
    def handle_node_click(self, node_id: str, node_type: str, properties: Dict[str, Any]) -> List[NodeClickEvent]:
        """Handle a node click event and generate contextual queries"""
        try:
            node_type_enum = NodeType(node_type)
        except ValueError:
            node_type_enum = NodeType.UNKNOWN
        
        if node_type_enum == NodeType.UNKNOWN:
            return []
        
        generated_queries = []
        templates = self.query_templates.get(node_type_enum, {})
        
        for query_type, template in templates.items():
            try:
                query = self._generate_query_from_template(template, node_type_enum, properties)
                if query:
                    event = NodeClickEvent(
                        node_id=node_id,
                        node_type=node_type,
                        properties=properties,
                        generated_query=query
                    )
                    generated_queries.append(event)
            except Exception as e:
                st.warning(f"Failed to generate {query_type} query: {str(e)}")
                continue
        
        return generated_queries
    
    def _generate_query_from_template(self, template: str, node_type: NodeType, properties: Dict[str, Any]) -> Optional[str]:
        """Generate a Cypher query from a template and node properties"""
        try:
            if node_type == NodeType.STUDY:
                study_id = properties.get('study_id')
                if not study_id:
                    return None
                return template.format(study_id=study_id)
            
            elif node_type == NodeType.ORGANISM:
                organism_name = properties.get('organism_name') or properties.get('name')
                if not organism_name:
                    return None
                
                # Handle both exact match and name-based queries
                if '{organism_name}' in template:
                    return template.format(organism_name=organism_name)
                elif '{name}' in template:
                    # Extract a searchable part of the name
                    search_name = self._extract_searchable_name(organism_name)
                    return template.format(name=search_name)
            
            elif node_type == NodeType.FACTOR:
                factor_name = properties.get('factor_name') or properties.get('name')
                if not factor_name:
                    return None
                
                if '{factor_name}' in template:
                    return template.format(factor_name=factor_name)
                elif '{name}' in template:
                    search_name = self._extract_searchable_name(factor_name)
                    return template.format(name=search_name)
            
            elif node_type == NodeType.ASSAY:
                assay_name = properties.get('assay_name') or properties.get('name')
                if not assay_name:
                    return None
                
                if '{assay_name}' in template:
                    return template.format(assay_name=assay_name)
                elif '{name}' in template:
                    search_name = self._extract_searchable_name(assay_name)
                    return template.format(name=search_name)
            
            return None
            
        except Exception as e:
            st.error(f"Error generating query: {str(e)}")
            return None
    
    def _extract_searchable_name(self, full_name: str) -> str:
        """Extract a searchable portion from a full name"""
        if not full_name:
            return ""
        
        # For organism names like "Mus musculus", take the first word
        # For factor names, take the first significant word
        words = full_name.split()
        if len(words) >= 2:
            # Return the first two words for scientific names
            return " ".join(words[:2])
        else:
            return words[0] if words else full_name
    
    def get_query_suggestions_for_node(self, node_type: str, properties: Dict[str, Any]) -> List[Dict[str, str]]:
        """Get user-friendly query suggestions for a node"""
        try:
            node_type_enum = NodeType(node_type)
        except ValueError:
            return []
        
        suggestions = []
        templates = self.query_templates.get(node_type_enum, {})
        
        for query_type in templates.keys():
            description = self.query_descriptions.get(query_type, query_type.replace("_", " ").title())
            suggestions.append({
                "type": query_type,
                "description": description,
                "node_type": node_type
            })
        
        return suggestions
    
    def generate_contextual_query(self, node_type: str, properties: Dict[str, Any], query_type: str) -> Optional[str]:
        """Generate a specific contextual query for a node"""
        try:
            node_type_enum = NodeType(node_type)
        except ValueError:
            return None
        
        templates = self.query_templates.get(node_type_enum, {})
        template = templates.get(query_type)
        
        if not template:
            return None
        
        return self._generate_query_from_template(template, node_type_enum, properties)
    
    def render_node_interaction_panel(self, node_id: str, node_type: str, properties: Dict[str, Any]):
        """Render an interactive panel for node-based query generation"""
        # Custom subheader with NASA emoji
        import os
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        EMOJI_ASSETS_DIR = os.path.join(BASE_DIR, "assets", "emojis")
        target_emoji = os.path.join(EMOJI_ASSETS_DIR, "Satellite_Ground_1.svg")
        
        target_cols = st.columns([1, 10])
        with target_cols[0]:
            if os.path.exists(target_emoji):
                st.image(target_emoji, width=30)
        with target_cols[1]:
            st.subheader(f"Explore {node_type}: {self._get_node_display_name(node_type, properties)}")
        
        # Get query suggestions
        suggestions = self.get_query_suggestions_for_node(node_type, properties)
        
        if not suggestions:
            st.info("No contextual queries available for this node type.")
            return None
        
        # Create buttons for each suggestion
        cols = st.columns(min(len(suggestions), 3))
        selected_query = None
        
        for i, suggestion in enumerate(suggestions):
            with cols[i % 3]:
                if st.button(
                    suggestion["description"], 
                    key=f"node_query_{node_id}_{suggestion['type']}",
                    help=f"Generate query to {suggestion['description'].lower()}"
                ):
                    selected_query = self.generate_contextual_query(
                        node_type, properties, suggestion["type"]
                    )
                    break
        
        return selected_query
    
    def _get_node_display_name(self, node_type: str, properties: Dict[str, Any]) -> str:
        """Get a display-friendly name for a node"""
        if node_type == "Study":
            return properties.get('study_id', 'Unknown Study')
        elif node_type == "Organism":
            return properties.get('organism_name', properties.get('name', 'Unknown Organism'))
        elif node_type == "Factor":
            return properties.get('factor_name', properties.get('name', 'Unknown Factor'))
        elif node_type == "Assay":
            return properties.get('assay_name', properties.get('name', 'Unknown Assay'))
        else:
            return properties.get('name', f'Unknown {node_type}')
    
    def create_sample_queries_for_demo(self) -> List[Dict[str, str]]:
        """Create sample queries for demonstration purposes"""
        return [
            {
                "title": "Find all studies with mice",
                "query": "MATCH (s:Study)-[:HAS_ORGANISM]->(o:Organism) WHERE o.organism_name CONTAINS 'mouse' RETURN s, o LIMIT 10",
                "description": "Shows studies that use mouse organisms"
            },
            {
                "title": "Spaceflight factor studies", 
                "query": "MATCH (s:Study)-[:HAS_FACTOR]->(f:Factor) WHERE f.factor_name CONTAINS 'spaceflight' RETURN s, f LIMIT 10",
                "description": "Studies involving spaceflight as a factor"
            },
            {
                "title": "Study OSD-840 connections",
                "query": "MATCH (s:Study {study_id: 'OSD-840'})-[r]-(n) RETURN s, r, n LIMIT 20",
                "description": "All connections for a specific study"
            },
            {
                "title": "Organism-Factor relationships",
                "query": "MATCH (o:Organism)<-[:HAS_ORGANISM]-(s:Study)-[:HAS_FACTOR]->(f:Factor) RETURN o, s, f LIMIT 15",
                "description": "Shows which organisms are studied with which factors"
            }
        ]

# Global instance for the application
node_click_handler = NodeClickHandler()