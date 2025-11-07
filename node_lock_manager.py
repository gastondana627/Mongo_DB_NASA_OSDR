# node_lock_manager.py

import streamlit as st
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class LockableTab(Enum):
    """Tabs that are allowed to lock nodes"""
    AI_SEMANTIC_SEARCH = "ai_semantic_search"
    STUDY_EXPLORER = "study_explorer"

@dataclass
class LockedNode:
    """Represents a locked node with metadata"""
    study_id: str
    locked_by_tab: LockableTab
    study_title: Optional[str] = None
    study_description: Optional[str] = None
    lock_timestamp: Optional[str] = None

class NodeLockManager:
    """Centralized manager for node locking functionality"""
    
    def __init__(self):
        self.session_key = "node_lock_state"
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize session state for node locking"""
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = {
                "locked_node": None,
                "kg_auto_executed": False,
                "cypher_query_result": None,
                "graph_html": None
            }
        
        # Also initialize legacy keys for compatibility
        if 'selected_study_for_kg' not in st.session_state:
            st.session_state.selected_study_for_kg = None
        if 'kg_auto_executed' not in st.session_state:
            st.session_state.kg_auto_executed = False
    
    def can_lock_nodes(self, tab_name: str) -> bool:
        """Check if a tab is allowed to lock nodes"""
        try:
            # Convert tab name to enum
            if tab_name == "ai_semantic_search":
                return True
            elif tab_name == "study_explorer":
                return True
            else:
                return False
        except:
            return False
    
    def lock_node(self, study_id: str, tab_name: str, study_title: Optional[str] = None, 
                  study_description: Optional[str] = None) -> bool:
        """Lock a node from an authorized tab"""
        if not self.can_lock_nodes(tab_name):
            logger.warning(f"Tab '{tab_name}' is not authorized to lock nodes")
            return False
        
        try:
            # Convert tab name to enum
            if tab_name == "ai_semantic_search":
                tab_enum = LockableTab.AI_SEMANTIC_SEARCH
            elif tab_name == "study_explorer":
                tab_enum = LockableTab.STUDY_EXPLORER
            else:
                logger.error(f"Unknown tab name: {tab_name}")
                return False
            
            # Create locked node
            import datetime
            locked_node = LockedNode(
                study_id=study_id,
                locked_by_tab=tab_enum,
                study_title=study_title,
                study_description=study_description,
                lock_timestamp=datetime.datetime.now().isoformat()
            )
            
            # Ensure session state key exists
            if self.session_key not in st.session_state:
                self._initialize_session_state()
            
            # Update session state with explicit assignments
            st.session_state[self.session_key]["locked_node"] = locked_node
            st.session_state[self.session_key]["kg_auto_executed"] = False
            st.session_state[self.session_key]["cypher_query_result"] = None
            st.session_state[self.session_key]["graph_html"] = None
            
            # Also update legacy session state for compatibility
            st.session_state.selected_study_for_kg = study_id
            st.session_state.kg_auto_executed = False
            
            # Clear any existing KG state to ensure fresh start
            if 'cypher_query_result' in st.session_state:
                st.session_state.cypher_query_result = None
            if 'graph_html' in st.session_state:
                st.session_state.graph_html = None
            
            logger.info(f"✅ Node {study_id} successfully locked by {tab_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to lock node {study_id}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def release_node(self) -> bool:
        """Release the currently locked node"""
        try:
            # Clear centralized state
            st.session_state[self.session_key] = {
                "locked_node": None,
                "kg_auto_executed": False,
                "cypher_query_result": None,
                "graph_html": None
            }
            
            # Clear legacy session state for compatibility
            st.session_state.selected_study_for_kg = None
            st.session_state.kg_auto_executed = False
            st.session_state.cypher_query_result = None
            st.session_state.graph_html = None
            
            # Clear other KG-related state
            if 'kg_study_ids' in st.session_state:
                st.session_state.kg_study_ids = []
            if 'ai_comparison_text' in st.session_state:
                st.session_state.ai_comparison_text = None
            if 'kg_mock_result' in st.session_state:
                st.session_state.kg_mock_result = None
            
            logger.info("Node released successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to release node: {str(e)}")
            return False
    
    def get_locked_node(self) -> Optional[LockedNode]:
        """Get the currently locked node"""
        return st.session_state[self.session_key].get("locked_node")
    
    def is_node_locked(self) -> bool:
        """Check if any node is currently locked"""
        locked_node = self.get_locked_node()
        return locked_node is not None
    
    def get_locked_study_id(self) -> Optional[str]:
        """Get the study ID of the locked node"""
        locked_node = self.get_locked_node()
        return locked_node.study_id if locked_node else None
    
    def mark_kg_executed(self):
        """Mark that the KG query has been executed for the locked node"""
        st.session_state[self.session_key]["kg_auto_executed"] = True
        st.session_state.kg_auto_executed = True  # Legacy compatibility
    
    def is_kg_executed(self) -> bool:
        """Check if KG query has been executed for the locked node"""
        return st.session_state[self.session_key].get("kg_auto_executed", False)
    
    def set_query_result(self, result: Any):
        """Set the query result for the locked node"""
        st.session_state[self.session_key]["cypher_query_result"] = result
        st.session_state.cypher_query_result = result  # Legacy compatibility
    
    def get_query_result(self) -> Any:
        """Get the query result for the locked node"""
        return st.session_state[self.session_key].get("cypher_query_result")
    
    def render_lock_button(self, study_id: str, tab_name: str, study_title: Optional[str] = None,
                          study_description: Optional[str] = None, button_key: str = None) -> bool:
        """Render a lock button for authorized tabs"""
        if not self.can_lock_nodes(tab_name):
            return False
        
        # Check if this study is already locked
        current_locked = self.get_locked_study_id()
        if current_locked == study_id:
            # Show pulsing lock indicator for already locked study
            try:
                from loading_animations import loading_animations
                loading_animations.create_pulsing_lock_indicator(study_id)
            except ImportError:
                st.success(f"🔒 **Study {study_id} is currently LOCKED**")
            return False
        
        # Create unique button key
        if not button_key:
            button_key = f"lock_{tab_name}_{study_id}"
        
        # Check if we're in the middle of a locking process
        locking_key = f"locking_{study_id}"
        if st.session_state.get(locking_key, False):
            st.info("🔄 Locking in progress...")
            return False
        
        if st.button("🔒 Lock into Knowledge Graph", key=button_key):
            # Set locking flag to prevent double-clicks
            st.session_state[locking_key] = True
            
            try:
                # Immediate locking without blocking animations
                with st.spinner("🔒 Locking node..."):
                    success = self.lock_node(study_id, tab_name, study_title, study_description)
                
                if success:
                    # Show immediate success without blocking animations
                    st.success(f"🔒 **Study {study_id} LOCKED into Knowledge Graph!** \n\n👉 **Switch to Knowledge Graph tab** to see the visualization. Use **Release Node** to unlock.")
                    
                    # Add a small visual indicator
                    try:
                        from loading_animations import loading_animations
                        # Quick success indicator without blocking
                        st.balloons()
                    except ImportError:
                        pass
                    
                    # Clear locking flag before rerun
                    st.session_state[locking_key] = False
                    
                    # Immediate rerun to update the UI
                    st.rerun()
                else:
                    st.error("Failed to lock node. This tab may not have permission to lock nodes.")
                    # Clear locking flag on failure
                    st.session_state[locking_key] = False
                
                return success
                
            except Exception as e:
                # Clear locking flag on exception
                st.session_state[locking_key] = False
                st.error(f"Error during locking: {str(e)}")
                return False
        
        return False
    
    def render_locked_node_display(self):
        """Render the locked node display in the Knowledge Graph tab"""
        locked_node = self.get_locked_node()
        if not locked_node:
            return False
        
        # Import here to avoid circular imports
        import os
        from simple_elegant_ui import get_custom_emoji_for_context
        
        # Prominent locked node display
        st.container()
        lock_cols = st.columns([1, 15, 3])
        
        with lock_cols[0]:
            st.image(get_custom_emoji_for_context("study_id"), width=40)
        
        with lock_cols[1]:
            st.markdown(f"### 🔒 **LOCKED NODE**: {locked_node.study_id}")
            
            # Display study details if available
            if locked_node.study_title:
                st.markdown(f"**{locked_node.study_title}**")
            if locked_node.study_description:
                description = locked_node.study_description[:150]
                if len(locked_node.study_description) > 150:
                    description += "..."
                st.caption(description)
            
            # Show which tab locked it
            tab_display = {
                LockableTab.AI_SEMANTIC_SEARCH: "🔍 AI Semantic Search",
                LockableTab.STUDY_EXPLORER: "📚 Study Explorer"
            }
            st.caption(f"Locked by: {tab_display.get(locked_node.locked_by_tab, 'Unknown')}")
        
        with lock_cols[2]:
            # Release Node button
            if st.button("🔓 **Release Node**", key="release_node", type="primary"):
                success = self.release_node()
                if success:
                    st.success("🔓 Node released! Knowledge Graph reset.")
                    st.rerun()
                else:
                    st.error("Failed to release node.")
        
        st.markdown("---")
        return True
    
    def render_unauthorized_message(self, tab_name: str):
        """Render a message for tabs that cannot lock nodes"""
        if not self.can_lock_nodes(tab_name):
            st.info("🔒 **Node locking is only available in AI Semantic Search and Study Explorer tabs.**")
            return True
        return False

# Global instance for the application
node_lock_manager = NodeLockManager()