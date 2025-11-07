#!/usr/bin/env python3
"""
OSDR Researcher Extractor
Comprehensive system to extract ALL researchers, authors, and contributors 
from NASA OSDR studies for the tribute system.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
import time
from urllib.parse import urljoin
import streamlit as st
from pymongo import MongoClient
import certifi
from config import MONGO_URI

@dataclass
class OSDRResearcher:
    """Complete researcher information from OSDR studies"""
    name: str
    role: str  # "Principal Investigator", "Co-Investigator", "Author", etc.
    affiliation: str
    email: Optional[str] = None
    orcid: Optional[str] = None
    studies: List[str] = None  # List of OSD study IDs
    expertise_areas: Set[str] = None  # Inferred from studies
    total_studies: int = 0
    
    def __post_init__(self):
        if self.studies is None:
            self.studies = []
        if self.expertise_areas is None:
            self.expertise_areas = set()

class OSDRResearcherExtractor:
    """Extracts comprehensive researcher information from OSDR studies"""
    
    def __init__(self):
        self.researchers_db = {}  # name -> OSDRResearcher
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
    def extract_researchers_from_study_page(self, study_url: str, study_id: str) -> List[OSDRResearcher]:
        """Extract all researchers from a single OSDR study page"""
        try:
            response = self.session.get(study_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            researchers = []
            
            # Look for various researcher sections
            researcher_patterns = [
                # Principal Investigator section
                {'section': 'Principal Investigator', 'role': 'Principal Investigator'},
                {'section': 'Co-Investigator', 'role': 'Co-Investigator'},
                {'section': 'Project Scientist', 'role': 'Project Scientist'},
                {'section': 'Authors', 'role': 'Author'},
                {'section': 'Contributors', 'role': 'Contributor'},
                {'section': 'Contact', 'role': 'Contact Person'},
                {'section': 'Investigators', 'role': 'Investigator'}
            ]
            
            # Extract from metadata sections
            for pattern in researcher_patterns:
                section_researchers = self._extract_from_section(soup, pattern['section'], pattern['role'], study_id)
                researchers.extend(section_researchers)
            
            # Extract from publication information
            pub_researchers = self._extract_from_publications(soup, study_id)
            researchers.extend(pub_researchers)
            
            # Extract from study description
            desc_researchers = self._extract_from_description(soup, study_id)
            researchers.extend(desc_researchers)
            
            return researchers
            
        except Exception as e:
            st.warning(f"Could not extract researchers from {study_url}: {e}")
            return []
    
    def _extract_from_section(self, soup: BeautifulSoup, section_name: str, role: str, study_id: str) -> List[OSDRResearcher]:
        """Extract researchers from a specific section of the page"""
        researchers = []
        
        # Look for section headers
        section_patterns = [
            section_name,
            section_name.lower(),
            section_name.upper(),
            section_name.replace(' ', '_'),
            section_name.replace(' ', '-')
        ]
        
        for pattern in section_patterns:
            # Find section by various methods
            section_elements = (
                soup.find_all(text=re.compile(pattern, re.IGNORECASE)) +
                soup.find_all(attrs={'class': re.compile(pattern, re.IGNORECASE)}) +
                soup.find_all(attrs={'id': re.compile(pattern, re.IGNORECASE)})
            )
            
            for element in section_elements:
                # Get the parent container
                if hasattr(element, 'parent'):
                    container = element.parent
                else:
                    container = element
                
                # Look for researcher information in the container
                researcher_info = self._parse_researcher_info(container, role, study_id)
                researchers.extend(researcher_info)
        
        return researchers
    
    def _extract_from_publications(self, soup: BeautifulSoup, study_id: str) -> List[OSDRResearcher]:
        """Extract researchers from publication sections"""
        researchers = []
        
        # Look for publication sections
        pub_sections = soup.find_all(text=re.compile(r'publication|paper|article|journal', re.IGNORECASE))
        
        for section in pub_sections:
            if hasattr(section, 'parent'):
                container = section.parent
                
                # Look for author lists in citations
                citations = container.find_all(text=re.compile(r'\w+,\s*\w+\.', re.IGNORECASE))
                
                for citation in citations:
                    authors = self._parse_author_list(str(citation), study_id)
                    researchers.extend(authors)
        
        return researchers
    
    def _extract_from_description(self, soup: BeautifulSoup, study_id: str) -> List[OSDRResearcher]:
        """Extract researchers mentioned in study descriptions"""
        researchers = []
        
        # Get all text content
        text_content = soup.get_text()
        
        # Look for researcher name patterns
        name_patterns = [
            r'Dr\.\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'Professor\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+),\s*PhD',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+et\s+al',
        ]
        
        for pattern in name_patterns:
            matches = re.findall(pattern, text_content)
            for match in matches:
                researcher = OSDRResearcher(
                    name=match,
                    role="Researcher",
                    affiliation="Unknown",
                    studies=[study_id]
                )
                researchers.append(researcher)
        
        return researchers
    
    def _parse_researcher_info(self, container, role: str, study_id: str) -> List[OSDRResearcher]:
        """Parse researcher information from a container element"""
        researchers = []
        
        # Get all text from the container
        text = container.get_text() if hasattr(container, 'get_text') else str(container)
        
        # Look for email addresses
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        
        # Look for names (various patterns)
        name_patterns = [
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)',  # First Last
            r'([A-Z][a-z]+,\s*[A-Z]\.)',     # Last, F.
            r'([A-Z]\.?\s*[A-Z][a-z]+)',     # F. Last
        ]
        
        names = []
        for pattern in name_patterns:
            matches = re.findall(pattern, text)
            names.extend(matches)
        
        # Create researcher objects
        for name in names:
            # Clean up the name
            clean_name = re.sub(r'[,.]', '', name).strip()
            
            # Try to find associated email
            associated_email = None
            if emails:
                # Simple heuristic: use first email found in same container
                associated_email = emails[0]
            
            # Try to extract affiliation
            affiliation = self._extract_affiliation(text, clean_name)
            
            researcher = OSDRResearcher(
                name=clean_name,
                role=role,
                affiliation=affiliation,
                email=associated_email,
                studies=[study_id]
            )
            researchers.append(researcher)
        
        return researchers
    
    def _parse_author_list(self, citation_text: str, study_id: str) -> List[OSDRResearcher]:
        """Parse author list from citation text"""
        researchers = []
        
        # Split by common author separators
        authors = re.split(r',\s*(?=\w)', citation_text)
        
        for author in authors:
            # Clean up author name
            clean_author = re.sub(r'[^\w\s.]', '', author).strip()
            
            if len(clean_author) > 3 and ' ' in clean_author:  # Basic validation
                researcher = OSDRResearcher(
                    name=clean_author,
                    role="Author",
                    affiliation="Unknown",
                    studies=[study_id]
                )
                researchers.append(researcher)
        
        return researchers
    
    def _extract_affiliation(self, text: str, researcher_name: str) -> str:
        """Extract affiliation for a researcher from text"""
        # Look for common affiliation patterns near the researcher name
        affiliation_patterns = [
            r'University\s+of\s+\w+',
            r'\w+\s+University',
            r'NASA\s+\w+\s+\w+\s+Center',
            r'NASA\s+\w+',
            r'\w+\s+Institute',
            r'\w+\s+Laboratory',
            r'\w+\s+Research\s+Center'
        ]
        
        for pattern in affiliation_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0]
        
        return "Unknown"
    
    def extract_all_researchers_from_osdr(self) -> Dict[str, OSDRResearcher]:
        """Extract researchers from all OSDR studies in the database"""
        try:
            # Connect to MongoDB
            client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
            db = client.nasa_osdr
            collection = db.studies
            
            # Get all studies
            studies = list(collection.find({}, {"study_id": 1, "study_link": 1, "title": 1, "organisms": 1, "factors": 1}))
            
            st.info(f"🔍 Extracting researchers from {len(studies)} OSDR studies...")
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            total_researchers = 0
            processed_studies = 0
            
            for i, study in enumerate(studies):
                study_id = study.get('study_id', 'Unknown')
                study_link = study.get('study_link', '')
                
                if study_link:
                    status_text.text(f"Processing {study_id}... ({i+1}/{len(studies)})")
                    
                    # Extract researchers from this study
                    study_researchers = self.extract_researchers_from_study_page(study_link, study_id)
                    
                    # Add to database
                    for researcher in study_researchers:
                        self._add_researcher_to_db(researcher, study)
                        total_researchers += 1
                    
                    processed_studies += 1
                    
                    # Update progress
                    progress_bar.progress((i + 1) / len(studies))
                    
                    # Rate limiting
                    time.sleep(0.5)  # Be respectful to NASA servers
                
                # Process in batches to avoid timeouts
                if i > 0 and i % 50 == 0:
                    st.success(f"✅ Processed {i} studies, found {total_researchers} researchers so far...")
            
            progress_bar.progress(1.0)
            status_text.text(f"✅ Complete! Processed {processed_studies} studies, found {len(self.researchers_db)} unique researchers")
            
            return self.researchers_db
            
        except Exception as e:
            st.error(f"❌ Error extracting researchers: {e}")
            return {}
    
    def _add_researcher_to_db(self, researcher: OSDRResearcher, study: Dict[str, Any]):
        """Add researcher to the database, merging if already exists"""
        name_key = researcher.name.lower().strip()
        
        if name_key in self.researchers_db:
            # Merge with existing researcher
            existing = self.researchers_db[name_key]
            existing.studies.extend(researcher.studies)
            existing.total_studies = len(set(existing.studies))
            
            # Add expertise areas from study
            if 'organisms' in study:
                existing.expertise_areas.update(study['organisms'])
            if 'factors' in study:
                existing.expertise_areas.update(study['factors'])
            
            # Update role if more specific
            if researcher.role != "Unknown" and existing.role == "Unknown":
                existing.role = researcher.role
            
            # Update affiliation if more specific
            if researcher.affiliation != "Unknown" and existing.affiliation == "Unknown":
                existing.affiliation = researcher.affiliation
                
        else:
            # Add new researcher
            researcher.total_studies = len(researcher.studies)
            
            # Add expertise areas from study
            if 'organisms' in study:
                researcher.expertise_areas.update(study['organisms'])
            if 'factors' in study:
                researcher.expertise_areas.update(study['factors'])
            
            self.researchers_db[name_key] = researcher
    
    def get_top_researchers(self, limit: int = 50) -> List[OSDRResearcher]:
        """Get top researchers by number of studies"""
        researchers = list(self.researchers_db.values())
        researchers.sort(key=lambda r: r.total_studies, reverse=True)
        return researchers[:limit]
    
    def get_researchers_by_expertise(self, expertise: str) -> List[OSDRResearcher]:
        """Get researchers by expertise area"""
        matching_researchers = []
        
        for researcher in self.researchers_db.values():
            if any(expertise.lower() in area.lower() for area in researcher.expertise_areas):
                matching_researchers.append(researcher)
        
        matching_researchers.sort(key=lambda r: r.total_studies, reverse=True)
        return matching_researchers
    
    def save_researchers_to_database(self):
        """Save extracted researchers to MongoDB for future use"""
        try:
            client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
            db = client.nasa_osdr
            researchers_collection = db.researchers
            
            # Clear existing data
            researchers_collection.delete_many({})
            
            # Convert researchers to documents
            researcher_docs = []
            for researcher in self.researchers_db.values():
                doc = {
                    'name': researcher.name,
                    'role': researcher.role,
                    'affiliation': researcher.affiliation,
                    'email': researcher.email,
                    'orcid': researcher.orcid,
                    'studies': researcher.studies,
                    'expertise_areas': list(researcher.expertise_areas),
                    'total_studies': researcher.total_studies
                }
                researcher_docs.append(doc)
            
            # Insert all researchers
            if researcher_docs:
                researchers_collection.insert_many(researcher_docs)
                st.success(f"✅ Saved {len(researcher_docs)} researchers to database")
            
        except Exception as e:
            st.error(f"❌ Error saving researchers: {e}")
    
    def load_researchers_from_database(self) -> Dict[str, OSDRResearcher]:
        """Load previously extracted researchers from MongoDB"""
        try:
            client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
            db = client.nasa_osdr
            researchers_collection = db.researchers
            
            researchers = {}
            
            for doc in researchers_collection.find({}):
                researcher = OSDRResearcher(
                    name=doc['name'],
                    role=doc['role'],
                    affiliation=doc['affiliation'],
                    email=doc.get('email'),
                    orcid=doc.get('orcid'),
                    studies=doc['studies'],
                    expertise_areas=set(doc.get('expertise_areas', [])),
                    total_studies=doc['total_studies']
                )
                researchers[doc['name'].lower().strip()] = researcher
            
            self.researchers_db = researchers
            return researchers
            
        except Exception as e:
            st.warning(f"Could not load researchers from database: {e}")
            return {}

# Global instance
osdr_researcher_extractor = OSDRResearcherExtractor()