# cypher_editor.py

import streamlit as st
from streamlit_ace import st_ace
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import re
import os
from enhanced_neo4j_executor import neo4j_executor, ValidationResult
from session_manager import session_manager

# Custom emoji helper for cypher editor
def get_custom_emoji_for_editor(context_name, fallback_emoji=None):
    """Get custom NASA emoji for editor context"""
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    EMOJI_ASSETS_DIR = os.path.join(BASE_DIR, "assets", "emojis")
    
    emoji_mapping = {
        "templates": "Scientist_1.svg",
        "history": "Satellite_1.svg", 
        "editor": "Satellite_Ground_1.svg",
        "execute": "Rocket_1.svg",
        "clear": "MArs_Rover_1.svg",
        "format": "Earth_2.svg",
        "suggestions": "Mars_1.svg"
    }
    
    if context_name in emoji_mapping:
        emoji_path = os.path.join(EMOJI_ASSETS_DIR, emoji_mapping[context_name])
        if os.path.exists(emoji_path):
            return emoji_path
    
    # If no specific emoji found, try to return any available emoji file
    if os.path.exists(EMOJI_ASSETS_DIR):
        available_emojis = [f for f in os.listdir(EMOJI_ASSETS_DIR) if f.endswith('.svg')]
        if available_emojis:
            return os.path.join(EMOJI_ASSETS_DIR, available_emojis[0])
    
    return fallback_emoji

@dataclass
class CypherEditorState:
    """State management for the Cypher editor"""
    current_query: str = ""
    query_history: List[str] = None
    history_index: int = -1
    last_validation: Optional[ValidationResult] = None
    
    def __post_init__(self):
        if self.query_history is None:
            self.query_history = []

class CypherEditor:
    """Enhanced Cypher query editor with syntax highlighting and auto-completion"""
    
    def __init__(self, session_key: str = "cypher_editor"):
        self.session_key = session_key
        self.max_history = 20
        
        # Initialize session state
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = CypherEditorState()
        
        # Cypher keywords for auto-completion
        self.cypher_keywords = [
            # Core clauses
            "MATCH", "WHERE", "RETURN", "WITH", "CREATE", "MERGE", "DELETE", "DETACH DELETE",
            "SET", "REMOVE", "FOREACH", "CALL", "YIELD", "UNION", "UNWIND",
            
            # Functions
            "count", "sum", "avg", "min", "max", "collect", "distinct",
            "size", "length", "type", "id", "labels", "keys", "properties",
            "exists", "coalesce", "head", "tail", "last", "nodes", "relationships",
            "startNode", "endNode", "toString", "toInteger", "toFloat",
            
            # Operators and keywords
            "AND", "OR", "NOT", "XOR", "IN", "STARTS WITH", "ENDS WITH", "CONTAINS",
            "IS NULL", "IS NOT NULL", "AS", "DISTINCT", "ORDER BY", "SKIP", "LIMIT",
            "ASC", "DESC", "OPTIONAL", "CASE", "WHEN", "THEN", "ELSE", "END",
            
            # Common patterns for NASA OSDR
            "Study", "Organism", "Factor", "Assay", "RELATED_TO", "HAS_ORGANISM", 
            "HAS_FACTOR", "HAS_ASSAY", "study_id", "organism_name", "factor_name"
        ]
        
        # Common query templates
        self.query_templates = {
            "Find Study": "MATCH (s:Study) WHERE s.study_id = 'OSD-XXX' RETURN s",
            "Studies by Organism": "MATCH (s:Study)-[:HAS_ORGANISM]->(o:Organism) WHERE o.organism_name CONTAINS 'mouse' RETURN s, o",
            "Studies by Factor": "MATCH (s:Study)-[:HAS_FACTOR]->(f:Factor) WHERE f.factor_name CONTAINS 'spaceflight' RETURN s, f",
            "Connected Studies": "MATCH (s1:Study)-[:HAS_ORGANISM]->(o:Organism)<-[:HAS_ORGANISM]-(s2:Study) WHERE s1.study_id = 'OSD-XXX' RETURN s1, s2, o",
            "Study Details": "MATCH (s:Study) WHERE s.study_id = 'OSD-XXX' OPTIONAL MATCH (s)-[r]-(n) RETURN s, r, n"
        }
    
    def _get_state(self) -> CypherEditorState:
        """Get the current editor state"""
        try:
            # Ensure session state exists
            if self.session_key not in st.session_state:
                st.session_state[self.session_key] = CypherEditorState()
            return st.session_state[self.session_key]
        except (KeyError, AttributeError, Exception):
            # Fallback: create new state if anything goes wrong
            new_state = CypherEditorState()
            try:
                st.session_state[self.session_key] = new_state
            except Exception:
                pass  # If we can't even set session state, just return the new state
            return new_state
    
    def _update_state(self, **kwargs):
        """Update the editor state"""
        state = self._get_state()
        for key, value in kwargs.items():
            setattr(state, key, value)
    
    def _validate_query_live(self, query: str) -> ValidationResult:
        """Perform live validation of the query"""
        if not query.strip():
            return ValidationResult(is_valid=True)  # Empty query is valid for editing
        
        return neo4j_executor.validate_query(query)
    
    def render_query_templates(self):
        """Render query template selector"""
        st.subheader("📝 Query Templates")
        
        selected_template = st.selectbox(
            "Choose a template:",
            options=[""] + list(self.query_templates.keys()),
            key=f"{self.session_key}_template_select"
        )
        
        if st.button("Use Template", disabled=not selected_template, key=f"{self.session_key}_use_template"):
            if selected_template:
                template_query = self.query_templates[selected_template]
                self._update_state(current_query=template_query)
                st.success(f"Template '{selected_template}' loaded!")
                st.rerun()
    
    def render_history_controls(self):
        """Render query history navigation controls using session manager"""
        # Use the session manager for history navigation (if available)
        try:
            navigation_result = session_manager.render_history_navigation()
            if navigation_result:
                # Update current query if user navigated to a different query
                self._update_state(current_query=navigation_result)
        except (KeyError, AttributeError):
            # Session manager not properly initialized, use fallback
            st.info("Session management not available")
    
    def render_editor(self) -> str:
        """Render the main Cypher editor with syntax highlighting"""
        try:
            state = self._get_state()
            
            st.subheader("⚡ Cypher Query Editor")
            
            # Editor configuration
            editor_config = {
                'language': 'sql',  # Closest to Cypher syntax highlighting
                'theme': 'monokai',
                'key': f"{self.session_key}_ace_editor",
                'height': 200,
                'auto_update': True,
                'font_size': 14,
                'tab_size': 2,
                'wrap': True,
                'annotations': None,
                'markers': None
            }
            
            # Render the ACE editor
            current_query = st_ace(
                value=state.current_query,
                placeholder="Enter your Cypher query here...\n\nExample:\nMATCH (s:Study) WHERE s.study_id = 'OSD-840' RETURN s",
                **editor_config
            )
            
            # Update state if query changed
            if current_query != state.current_query:
                self._update_state(current_query=current_query)
                # Perform live validation
                validation = self._validate_query_live(current_query)
                self._update_state(last_validation=validation)
            
            return current_query
            
        except Exception as e:
            # Fallback editor if ACE editor fails
            st.warning(f"Advanced editor unavailable: {str(e)}")
            st.subheader("📝 Simple Query Editor")
            
            # Simple text area fallback
            current_query = st.text_area(
                "Enter Cypher Query:",
                value="MATCH (n) RETURN n LIMIT 10",
                height=200,
                key=f"{self.session_key}_simple_editor",
                placeholder="Enter your Cypher query here..."
            )
            
            return current_query
    
    def render_validation_indicators(self):
        """Render query validation status and suggestions"""
        state = self._get_state()
        
        if not state.current_query.strip():
            return
        
        validation = state.last_validation or self._validate_query_live(state.current_query)
        
        if validation.is_valid:
            st.success("✅ Query syntax is valid")
        else:
            st.error(f"❌ {validation.error_message}")
            
            if validation.suggestions:
                st.info("💡 Suggestions:")
                for suggestion in validation.suggestions:
                    st.write(f"• {suggestion}")
    
    def render_execute_controls(self) -> bool:
        """Render execute button and related controls. Returns True if execute was clicked."""
        state = self._get_state()
        
        execute_cols = st.columns([2, 1, 1])
        
        with execute_cols[0]:
            # Execute button - disabled if query is invalid
            validation = state.last_validation or self._validate_query_live(state.current_query)
            execute_disabled = not state.current_query.strip() or not validation.is_valid
            
            execute_clicked = st.button(
                "🚀 Execute Query",
                disabled=execute_disabled,
                key=f"{self.session_key}_execute",
                help="Execute the Cypher query (Ctrl+Enter)" if not execute_disabled else "Fix query errors before executing"
            )
        
        with execute_cols[1]:
            if st.button("🧹 Clear", key=f"{self.session_key}_clear"):
                self._update_state(current_query="", last_validation=None)
                st.rerun()
        
        with execute_cols[2]:
            if st.button("🎨 Format", key=f"{self.session_key}_format"):
                formatted_query = self._format_query(state.current_query)
                self._update_state(current_query=formatted_query)
                st.rerun()
        
        return execute_clicked
    
    def _format_query(self, query: str) -> str:
        """Basic Cypher query formatting"""
        if not query.strip():
            return query
        
        # Basic formatting rules
        formatted = query.strip()
        
        # Add line breaks after major clauses
        major_clauses = ['MATCH', 'WHERE', 'RETURN', 'WITH', 'CREATE', 'MERGE', 'SET', 'DELETE']
        for clause in major_clauses:
            pattern = rf'\b{clause}\b'
            formatted = re.sub(pattern, f'\n{clause}', formatted, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        lines = [line.strip() for line in formatted.split('\n') if line.strip()]
        formatted = '\n'.join(lines)
        
        return formatted
    
    def add_to_history(self, query: str, execution_time_ms: Optional[float] = None, 
                      result_count: Optional[int] = None, success: bool = True, 
                      error_message: Optional[str] = None):
        """Add executed query to history using session manager"""
        try:
            session_manager.add_to_history(
                query=query,
                execution_time_ms=execution_time_ms,
                result_count=result_count,
                success=success,
                error_message=error_message
            )
        except (KeyError, AttributeError):
            # Session manager not properly initialized, add to local history as fallback
            state = self._get_state()
            if query not in state.query_history:
                state.query_history.insert(0, query)
                if len(state.query_history) > self.max_history:
                    state.query_history = state.query_history[:self.max_history]
    
    def set_query(self, query: str):
        """Set the current query (used for node click generation)"""
        self._update_state(current_query=query)
        # Also save to session manager (only if it exists and is initialized)
        try:
            session_manager.save_query_state(query)
        except (KeyError, AttributeError):
            # Session manager not properly initialized, skip
            pass
        # Validate the new query
        validation = self._validate_query_live(query)
        self._update_state(last_validation=validation)
    
    def get_current_query(self) -> str:
        """Get the current query text"""
        return self._get_state().current_query
    
    def render_help_section(self):
        """Render help section with Cypher syntax guide"""
        with st.expander("📖 Cypher Query Help"):
            st.markdown("""
            ### Common Cypher Patterns for NASA OSDR Data
            
            **Find a specific study:**
            ```cypher
            MATCH (s:Study) WHERE s.study_id = 'OSD-840' RETURN s
            ```
            
            **Find studies by organism:**
            ```cypher
            MATCH (s:Study)-[:HAS_ORGANISM]->(o:Organism) 
            WHERE o.organism_name CONTAINS 'mouse' 
            RETURN s, o
            ```
            
            **Find related studies:**
            ```cypher
            MATCH (s1:Study)-[:HAS_ORGANISM]->(o:Organism)<-[:HAS_ORGANISM]-(s2:Study) 
            WHERE s1.study_id = 'OSD-840' 
            RETURN s1, s2, o
            ```
            
            **Explore study connections:**
            ```cypher
            MATCH (s:Study)-[r]-(n) 
            WHERE s.study_id = 'OSD-840' 
            RETURN s, r, n LIMIT 25
            ```
            
            ### Tips:
            - Use `LIMIT` to control result size
            - Use `CONTAINS` for partial text matching
            - Use `OPTIONAL MATCH` for optional relationships
            - Press Ctrl+Enter to execute queries
            """)
    
    def render_complete_editor(self) -> tuple[str, bool]:
        """Render the complete editor interface. Returns (query, execute_clicked)"""
        try:
            # Render all components
            self.render_query_templates()
            st.markdown("---")
            
            # Enhanced session management interface (if available)
            try:
                session_result = session_manager.render_complete_session_interface()
                
                # Handle session navigation/restoration
                if session_result.get("navigation_query"):
                    self._update_state(current_query=session_result["navigation_query"])
                elif session_result.get("restored_query"):
                    self._update_state(current_query=session_result["restored_query"])
            except (KeyError, AttributeError):
                # Session manager not available, use basic history controls
                self.render_history_controls()
            
            st.markdown("---")
            
            current_query = self.render_editor()
            
            st.markdown("---")
            self.render_validation_indicators()
            
            st.markdown("---")
            execute_clicked = self.render_execute_controls()
            
            st.markdown("---")
            self.render_help_section()
            
            return current_query, execute_clicked
            
        except Exception as e:
            # Fallback interface if anything goes wrong
            st.error(f"Cypher editor error: {str(e)}")
            st.info("Using simplified query interface...")
            
            # Simple fallback interface
            query = st.text_area(
                "Enter Cypher Query:", 
                value="MATCH (n) RETURN n LIMIT 10",
                height=200,
                key="fallback_cypher_query"
            )
            execute_clicked = st.button("Execute Query", key="fallback_cypher_execute")
            
            return query, execute_clicked

# Global instance for the application
cypher_editor = CypherEditor()