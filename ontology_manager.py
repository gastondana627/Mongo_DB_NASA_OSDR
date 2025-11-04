#!/usr/bin/env python3
"""
NASA OSDR Ontology Manager
Implements formal ontology standards for space biology research data.
"""

import streamlit as st
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json

class OntologyStandard(Enum):
    """Supported ontology standards for space biology research"""
    FAIR = "FAIR Data Principles"
    OMICS = "Multi-Omics Standards"
    SPACE_BIOLOGY = "Space Biology Ontology"
    EXPERIMENTAL_FACTORS = "Experimental Factor Ontology (EFO)"
    GENE_ONTOLOGY = "Gene Ontology (GO)"

@dataclass
class MetadataField:
    """Formal metadata field definition"""
    name: str
    ontology_term: str
    description: str
    data_type: str
    required: bool
    controlled_vocabulary: Optional[List[str]] = None
    units: Optional[str] = None
    example: Optional[str] = None

class OntologyManager:
    """Manages formal ontology standards and metadata validation"""
    
    def __init__(self):
        self.metadata_schema = self._initialize_metadata_schema()
        self.controlled_vocabularies = self._initialize_controlled_vocabularies()
    
    def _initialize_metadata_schema(self) -> Dict[str, List[MetadataField]]:
        """Initialize formal metadata schema for NASA OSDR"""
        return {
            "study": [
                MetadataField(
                    name="study_id",
                    ontology_term="OSDR:study_identifier", 
                    description="Unique NASA OSDR study identifier",
                    data_type="string",
                    required=True,
                    example="OSD-840"
                ),
                MetadataField(
                    name="title",
                    ontology_term="DC:title",
                    description="Formal study title",
                    data_type="string", 
                    required=True
                ),
                MetadataField(
                    name="space_environment_factor",
                    ontology_term="OSDR:space_environment_factor",
                    description="Primary space environment factor studied",
                    data_type="controlled_vocabulary",
                    required=True,
                    controlled_vocabulary=["Microgravity", "Ionizing Radiation", "Isolation", "Confinement"]
                ),
                MetadataField(
                    name="mission_duration",
                    ontology_term="OSDR:mission_duration",
                    description="Duration of space mission or simulation",
                    data_type="numeric",
                    required=False,
                    units="days"
                )
            ],
            "organism": [
                MetadataField(
                    name="species",
                    ontology_term="NCBITaxon:species",
                    description="Taxonomic species name",
                    data_type="controlled_vocabulary",
                    required=True,
                    controlled_vocabulary=["Mus musculus", "Rattus norvegicus", "Homo sapiens", "Arabidopsis thaliana"]
                ),
                MetadataField(
                    name="strain",
                    ontology_term="NCBITaxon:strain",
                    description="Organism strain or variety",
                    data_type="string",
                    required=False
                ),
                MetadataField(
                    name="developmental_stage",
                    ontology_term="UBERON:developmental_stage",
                    description="Developmental stage at time of study",
                    data_type="controlled_vocabulary",
                    required=False,
                    controlled_vocabulary=["Adult", "Juvenile", "Embryonic", "Larval"]
                )
            ],
            "assay": [
                MetadataField(
                    name="assay_type",
                    ontology_term="OBI:assay_type",
                    description="Type of molecular assay performed",
                    data_type="controlled_vocabulary",
                    required=True,
                    controlled_vocabulary=["RNA-seq", "Proteomics", "Metabolomics", "Microarray", "qPCR"]
                ),
                MetadataField(
                    name="platform",
                    ontology_term="OBI:instrument_model",
                    description="Sequencing or analysis platform used",
                    data_type="string",
                    required=False
                ),
                MetadataField(
                    name="data_processing_pipeline",
                    ontology_term="EDAM:data_processing_pipeline",
                    description="Computational pipeline used for data processing",
                    data_type="string",
                    required=False
                )
            ]
        }
    
    def _initialize_controlled_vocabularies(self) -> Dict[str, List[str]]:
        """Initialize controlled vocabularies for space biology research"""
        return {
            "space_factors": [
                "Microgravity", "Simulated Microgravity", "Hypergravity",
                "Ionizing Radiation", "Galactic Cosmic Rays", "Solar Particle Events",
                "Isolation", "Confinement", "Altered Atmosphere", "CO2 Exposure"
            ],
            "mission_types": [
                "International Space Station", "Space Shuttle", "Ground-based Simulation",
                "Parabolic Flight", "Centrifuge", "Bed Rest Study", "Analog Environment"
            ],
            "tissue_types": [
                "Whole Blood", "Plasma", "Serum", "Muscle Tissue", "Bone Tissue",
                "Liver", "Kidney", "Heart", "Brain", "Lung", "Skin"
            ],
            "experimental_conditions": [
                "Flight", "Ground Control", "Vivarium Control", "Synchronous Control",
                "Baseline", "Recovery", "In-flight", "Post-flight"
            ]
        }
    
    def validate_metadata(self, entity_type: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Validate metadata against formal schema"""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }
        
        if entity_type not in self.metadata_schema:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"Unknown entity type: {entity_type}")
            return validation_result
        
        schema_fields = {field.name: field for field in self.metadata_schema[entity_type]}
        
        # Check required fields
        for field_name, field_def in schema_fields.items():
            if field_def.required and field_name not in metadata:
                validation_result["errors"].append(f"Required field missing: {field_name}")
                validation_result["is_valid"] = False
        
        # Validate field values
        for field_name, value in metadata.items():
            if field_name in schema_fields:
                field_def = schema_fields[field_name]
                
                # Check controlled vocabulary
                if field_def.controlled_vocabulary and value not in field_def.controlled_vocabulary:
                    validation_result["warnings"].append(
                        f"'{value}' not in controlled vocabulary for {field_name}. "
                        f"Allowed values: {', '.join(field_def.controlled_vocabulary)}"
                    )
        
        return validation_result
    
    def get_ontology_suggestions(self, query: str, entity_type: str = None) -> List[Dict[str, str]]:
        """Get ontology-based suggestions for queries"""
        suggestions = []
        
        # Search through metadata schema
        for etype, fields in self.metadata_schema.items():
            if entity_type and etype != entity_type:
                continue
                
            for field in fields:
                if query.lower() in field.name.lower() or query.lower() in field.description.lower():
                    suggestions.append({
                        "term": field.name,
                        "ontology_id": field.ontology_term,
                        "description": field.description,
                        "entity_type": etype
                    })
        
        return suggestions[:10]  # Limit to top 10 suggestions
    
    def render_ontology_browser(self):
        """Render interactive ontology browser"""
        st.subheader("🧬 Ontology Browser")
        
        # Entity type selector
        entity_type = st.selectbox(
            "Browse ontology for:",
            options=list(self.metadata_schema.keys()),
            format_func=lambda x: x.title()
        )
        
        if entity_type:
            fields = self.metadata_schema[entity_type]
            
            # Display fields in expandable sections
            for field in fields:
                with st.expander(f"{field.name} ({field.ontology_term})"):
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        st.write(f"**Description:** {field.description}")
                        st.write(f"**Data Type:** {field.data_type}")
                        st.write(f"**Required:** {'Yes' if field.required else 'No'}")
                        
                    with col2:
                        if field.controlled_vocabulary:
                            st.write("**Controlled Vocabulary:**")
                            for term in field.controlled_vocabulary:
                                st.write(f"• {term}")
                        
                        if field.units:
                            st.write(f"**Units:** {field.units}")
                        
                        if field.example:
                            st.write(f"**Example:** {field.example}")
    
    def render_metadata_validator(self):
        """Render metadata validation interface"""
        st.subheader("✅ Metadata Validator")
        
        entity_type = st.selectbox(
            "Entity type to validate:",
            options=list(self.metadata_schema.keys()),
            key="validator_entity_type"
        )
        
        # JSON input for metadata
        metadata_json = st.text_area(
            "Enter metadata as JSON:",
            height=200,
            placeholder='{\n  "study_id": "OSD-840",\n  "title": "Example Study",\n  "space_environment_factor": "Microgravity"\n}'
        )
        
        if st.button("Validate Metadata"):
            try:
                metadata = json.loads(metadata_json)
                result = self.validate_metadata(entity_type, metadata)
                
                if result["is_valid"]:
                    st.success("✅ Metadata is valid!")
                else:
                    st.error("❌ Validation failed:")
                    for error in result["errors"]:
                        st.error(f"• {error}")
                
                if result["warnings"]:
                    st.warning("⚠️ Warnings:")
                    for warning in result["warnings"]:
                        st.warning(f"• {warning}")
                        
            except json.JSONDecodeError:
                st.error("Invalid JSON format")

# Global instance
ontology_manager = OntologyManager()