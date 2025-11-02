# session_manager.py

import streamlit as st
import json
import os
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
import uuid

# Custom emoji helper for session manager
def get_custom_emoji_for_session(context_name, fallback_emoji=None):
    """Get custom NASA emoji for session manager context"""
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    EMOJI_ASSETS_DIR = os.path.join(BASE_DIR, "assets", "emojis")
    
    emoji_mapping = {
        "history": "Satellite_1.svg",
        "checkpoint": "Rocket_1.svg", 
        "session": "Satellite_Ground_1.svg",
        "save": "MArs_Rover_1.svg",
        "restore": "Earth_2.svg",
        "navigation": "Mars_1.svg",
        "clear": "Scientist_1.svg"
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

class SessionEventType(Enum):
    """Types of session events for tracking"""
    QUERY_EXECUTED = "query_executed"
    CHECKPOINT_CREATED = "checkpoint_created"
    SESSION_RESTORED = "session_restored"
    HISTORY_NAVIGATED = "history_navigated"

@dataclass
class QueryHistoryEntry:
    """Individual query history entry"""
    query: str
    timestamp: datetime
    execution_time_ms: Optional[float] = None
    result_count: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "query": self.query,
            "timestamp": self.timestamp.isoformat(),
            "execution_time_ms": self.execution_time_ms,
            "result_count": self.result_count,
            "success": self.success,
            "error_message": self.error_message
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueryHistoryEntry':
        """Create from dictionary for deserialization"""
        return cls(
            query=data["query"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            execution_time_ms=data.get("execution_time_ms"),
            result_count=data.get("result_count"),
            success=data.get("success", True),
            error_message=data.get("error_message")
        )

@dataclass
class SessionCheckpoint:
    """Named checkpoint for session state"""
    id: str
    name: str
    timestamp: datetime
    query: str
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "timestamp": self.timestamp.isoformat(),
            "query": self.query,
            "description": self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionCheckpoint':
        """Create from dictionary for deserialization"""
        return cls(
            id=data["id"],
            name=data["name"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            query=data["query"],
            description=data.get("description")
        )

@dataclass
class SessionState:
    """Complete session state for the enhanced Cypher editor"""
    current_query: str = ""
    query_history: List[QueryHistoryEntry] = field(default_factory=list)
    history_index: int = -1
    checkpoints: List[SessionCheckpoint] = field(default_factory=list)
    last_execution_result: Optional[Dict[str, Any]] = None
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "current_query": self.current_query,
            "query_history": [entry.to_dict() for entry in self.query_history],
            "history_index": self.history_index,
            "checkpoints": [cp.to_dict() for cp in self.checkpoints],
            "last_execution_result": self.last_execution_result,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionState':
        """Create from dictionary for deserialization"""
        return cls(
            current_query=data.get("current_query", ""),
            query_history=[QueryHistoryEntry.from_dict(entry) for entry in data.get("query_history", [])],
            history_index=data.get("history_index", -1),
            checkpoints=[SessionCheckpoint.from_dict(cp) for cp in data.get("checkpoints", [])],
            last_execution_result=data.get("last_execution_result"),
            session_id=data.get("session_id", str(uuid.uuid4())),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(timezone.utc),
            last_updated=datetime.fromisoformat(data["last_updated"]) if "last_updated" in data else datetime.now(timezone.utc)
        )

class SessionManager:
    """Enhanced session state management for Cypher editor with query history and checkpoints"""
    
    def __init__(self, session_key: str = "enhanced_cypher_session", max_history: int = 20):
        self.session_key = session_key
        self.max_history = max_history
        
        # Initialize session state if not exists
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = SessionState()
    
    def _get_state(self) -> SessionState:
        """Get the current session state"""
        return st.session_state[self.session_key]
    
    def _update_state(self, **kwargs):
        """Update the session state and mark as updated"""
        state = self._get_state()
        for key, value in kwargs.items():
            setattr(state, key, value)
        state.last_updated = datetime.now(timezone.utc)
    
    def save_query_state(self, query: str, results: Optional[Dict[str, Any]] = None):
        """Save current query and results to session state"""
        self._update_state(
            current_query=query,
            last_execution_result=results
        )
    
    def restore_session(self) -> Dict[str, Any]:
        """Restore last session state"""
        state = self._get_state()
        return {
            "current_query": state.current_query,
            "last_execution_result": state.last_execution_result,
            "session_id": state.session_id,
            "history_count": len(state.query_history),
            "checkpoint_count": len(state.checkpoints)
        }
    
    def add_to_history(self, query: str, execution_time_ms: Optional[float] = None, 
                      result_count: Optional[int] = None, success: bool = True, 
                      error_message: Optional[str] = None):
        """Add executed query to history with metadata"""
        if not query.strip():
            return
        
        state = self._get_state()
        
        # Create new history entry
        entry = QueryHistoryEntry(
            query=query.strip(),
            timestamp=datetime.now(timezone.utc),
            execution_time_ms=execution_time_ms,
            result_count=result_count,
            success=success,
            error_message=error_message
        )
        
        # Remove duplicate if it exists (same query)
        state.query_history = [h for h in state.query_history if h.query != query.strip()]
        
        # Add to beginning of history
        state.query_history.insert(0, entry)
        
        # Limit history size
        if len(state.query_history) > self.max_history:
            state.query_history = state.query_history[:self.max_history]
        
        # Reset history index to point to the new entry
        state.history_index = 0
        
        # Update state
        self._update_state(query_history=state.query_history, history_index=0)
    
    def navigate_history(self, direction: str) -> Optional[str]:
        """Navigate through query history. Returns the query at new position or None"""
        state = self._get_state()
        
        if not state.query_history:
            return None
        
        if direction == "previous":
            if state.history_index < len(state.query_history) - 1:
                state.history_index += 1
            else:
                return None  # Already at oldest
        elif direction == "next":
            if state.history_index > 0:
                state.history_index -= 1
            else:
                return None  # Already at newest
        else:
            return None  # Invalid direction
        
        # Update state and return the query
        self._update_state(history_index=state.history_index)
        return state.query_history[state.history_index].query
    
    def get_current_history_entry(self) -> Optional[QueryHistoryEntry]:
        """Get the current history entry based on history_index"""
        state = self._get_state()
        
        if not state.query_history or state.history_index < 0 or state.history_index >= len(state.query_history):
            return None
        
        return state.query_history[state.history_index]
    
    def create_checkpoint(self, name: str, query: str, description: Optional[str] = None) -> str:
        """Create a named checkpoint for the current session state"""
        state = self._get_state()
        
        checkpoint = SessionCheckpoint(
            id=str(uuid.uuid4()),
            name=name,
            timestamp=datetime.now(timezone.utc),
            query=query,
            description=description
        )
        
        # Remove existing checkpoint with same name
        state.checkpoints = [cp for cp in state.checkpoints if cp.name != name]
        
        # Add new checkpoint
        state.checkpoints.append(checkpoint)
        
        # Sort by timestamp (newest first)
        state.checkpoints.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Limit checkpoints (keep last 10)
        if len(state.checkpoints) > 10:
            state.checkpoints = state.checkpoints[:10]
        
        self._update_state(checkpoints=state.checkpoints)
        return checkpoint.id
    
    def restore_checkpoint(self, checkpoint_id: str) -> Optional[str]:
        """Restore session state from a checkpoint. Returns the query or None"""
        state = self._get_state()
        
        checkpoint = next((cp for cp in state.checkpoints if cp.id == checkpoint_id), None)
        if not checkpoint:
            return None
        
        # Restore the query from checkpoint
        self._update_state(current_query=checkpoint.query)
        return checkpoint.query
    
    def get_checkpoints(self) -> List[SessionCheckpoint]:
        """Get all available checkpoints"""
        return self._get_state().checkpoints
    
    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint by ID"""
        state = self._get_state()
        
        original_count = len(state.checkpoints)
        state.checkpoints = [cp for cp in state.checkpoints if cp.id != checkpoint_id]
        
        if len(state.checkpoints) < original_count:
            self._update_state(checkpoints=state.checkpoints)
            return True
        return False
    
    def get_history_stats(self) -> Dict[str, Any]:
        """Get statistics about query history"""
        state = self._get_state()
        
        if not state.query_history:
            return {
                "total_queries": 0,
                "successful_queries": 0,
                "failed_queries": 0,
                "avg_execution_time": 0,
                "most_recent": None
            }
        
        successful = [h for h in state.query_history if h.success]
        failed = [h for h in state.query_history if not h.success]
        
        # Calculate average execution time for successful queries
        exec_times = [h.execution_time_ms for h in successful if h.execution_time_ms is not None]
        avg_exec_time = sum(exec_times) / len(exec_times) if exec_times else 0
        
        return {
            "total_queries": len(state.query_history),
            "successful_queries": len(successful),
            "failed_queries": len(failed),
            "avg_execution_time": avg_exec_time,
            "most_recent": state.query_history[0].timestamp if state.query_history else None
        }
    
    def clear_history(self):
        """Clear all query history"""
        self._update_state(query_history=[], history_index=-1)
    
    def clear_checkpoints(self):
        """Clear all checkpoints"""
        self._update_state(checkpoints=[])
    
    def clear_session(self):
        """Clear entire session state"""
        st.session_state[self.session_key] = SessionState()
    
    def export_session(self) -> str:
        """Export session state as JSON string"""
        state = self._get_state()
        return json.dumps(state.to_dict(), indent=2)
    
    def import_session(self, json_data: str) -> bool:
        """Import session state from JSON string"""
        try:
            data = json.loads(json_data)
            imported_state = SessionState.from_dict(data)
            st.session_state[self.session_key] = imported_state
            return True
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            st.error(f"Failed to import session: {e}")
            return False
    
    def render_history_navigation(self) -> Optional[str]:
        """Render history navigation controls. Returns selected query or None"""
        state = self._get_state()
        
        if not state.query_history:
            st.info("No query history available")
            return None
        
        # History navigation header
        nav_cols = st.columns([1, 10])
        with nav_cols[0]:
            emoji_path = get_custom_emoji_for_session("navigation")
            if emoji_path:
                st.image(emoji_path, width=25)
        with nav_cols[1]:
            st.subheader("Query History Navigation")
        
        # Navigation controls
        control_cols = st.columns([2, 2, 3, 2])
        
        with control_cols[0]:
            if st.button("⬅️ Previous", 
                        disabled=state.history_index >= len(state.query_history) - 1,
                        key=f"{self.session_key}_nav_prev"):
                query = self.navigate_history("previous")
                if query:
                    st.rerun()
        
        with control_cols[1]:
            if st.button("➡️ Next", 
                        disabled=state.history_index <= 0,
                        key=f"{self.session_key}_nav_next"):
                query = self.navigate_history("next")
                if query:
                    st.rerun()
        
        with control_cols[2]:
            if state.history_index >= 0:
                current_entry = self.get_current_history_entry()
                if current_entry:
                    st.caption(f"Query {state.history_index + 1} of {len(state.query_history)}")
                    if current_entry.execution_time_ms:
                        st.caption(f"Executed in {current_entry.execution_time_ms:.0f}ms")
        
        with control_cols[3]:
            if st.button("🧹 Clear History", key=f"{self.session_key}_clear_hist"):
                self.clear_history()
                st.success("History cleared")
                st.rerun()
        
        # Current query display
        if state.history_index >= 0:
            current_entry = self.get_current_history_entry()
            if current_entry:
                st.markdown("**Current Query from History:**")
                st.code(current_entry.query, language="sql")
                
                # Show metadata
                meta_cols = st.columns(4)
                with meta_cols[0]:
                    st.metric("Status", "✅ Success" if current_entry.success else "❌ Failed")
                with meta_cols[1]:
                    if current_entry.execution_time_ms:
                        st.metric("Execution Time", f"{current_entry.execution_time_ms:.0f}ms")
                with meta_cols[2]:
                    if current_entry.result_count is not None:
                        st.metric("Results", current_entry.result_count)
                with meta_cols[3]:
                    st.metric("Executed", current_entry.timestamp.strftime("%H:%M:%S"))
                
                if not current_entry.success and current_entry.error_message:
                    st.error(f"Error: {current_entry.error_message}")
                
                return current_entry.query
        
        return None
    
    def render_checkpoint_management(self) -> Optional[str]:
        """Render checkpoint management interface. Returns restored query or None"""
        state = self._get_state()
        
        # Checkpoint management header
        cp_cols = st.columns([1, 10])
        with cp_cols[0]:
            emoji_path = get_custom_emoji_for_session("checkpoint")
            if emoji_path:
                st.image(emoji_path, width=25)
        with cp_cols[1]:
            st.subheader("Session Checkpoints")
        
        # Create new checkpoint
        with st.expander("💾 Create New Checkpoint"):
            checkpoint_name = st.text_input("Checkpoint Name:", 
                                          placeholder="e.g., 'Study Analysis Query'",
                                          key=f"{self.session_key}_cp_name")
            checkpoint_desc = st.text_area("Description (optional):", 
                                         placeholder="Brief description of this checkpoint...",
                                         key=f"{self.session_key}_cp_desc")
            
            create_cols = st.columns([1, 1])
            with create_cols[0]:
                if st.button("💾 Save Checkpoint", 
                           disabled=not checkpoint_name.strip() or not state.current_query.strip(),
                           key=f"{self.session_key}_create_cp"):
                    checkpoint_id = self.create_checkpoint(
                        checkpoint_name.strip(), 
                        state.current_query,
                        checkpoint_desc.strip() if checkpoint_desc.strip() else None
                    )
                    st.success(f"Checkpoint '{checkpoint_name}' created!")
                    st.rerun()
            
            with create_cols[1]:
                if st.button("🧹 Clear All Checkpoints", key=f"{self.session_key}_clear_cps"):
                    self.clear_checkpoints()
                    st.success("All checkpoints cleared")
                    st.rerun()
        
        # Display existing checkpoints
        checkpoints = self.get_checkpoints()
        if checkpoints:
            st.markdown("**Saved Checkpoints:**")
            
            for i, checkpoint in enumerate(checkpoints):
                with st.expander(f"📌 {checkpoint.name} ({checkpoint.timestamp.strftime('%m/%d %H:%M')})"):
                    if checkpoint.description:
                        st.markdown(f"**Description:** {checkpoint.description}")
                    
                    st.code(checkpoint.query, language="sql")
                    
                    action_cols = st.columns([1, 1, 1])
                    with action_cols[0]:
                        if st.button("🔄 Restore", key=f"{self.session_key}_restore_{checkpoint.id}"):
                            restored_query = self.restore_checkpoint(checkpoint.id)
                            if restored_query:
                                st.success(f"Restored checkpoint '{checkpoint.name}'")
                                return restored_query
                    
                    with action_cols[1]:
                        if st.button("📋 Copy Query", key=f"{self.session_key}_copy_{checkpoint.id}"):
                            # In a real app, this would copy to clipboard
                            st.info("Query copied to editor")
                            return checkpoint.query
                    
                    with action_cols[2]:
                        if st.button("🗑️ Delete", key=f"{self.session_key}_delete_{checkpoint.id}"):
                            if self.delete_checkpoint(checkpoint.id):
                                st.success(f"Deleted checkpoint '{checkpoint.name}'")
                                st.rerun()
        else:
            st.info("No checkpoints saved yet")
        
        return None
    
    def render_session_stats(self):
        """Render session statistics and information"""
        state = self._get_state()
        stats = self.get_history_stats()
        
        # Session stats header
        stats_cols = st.columns([1, 10])
        with stats_cols[0]:
            emoji_path = get_custom_emoji_for_session("session")
            if emoji_path:
                st.image(emoji_path, width=25)
        with stats_cols[1]:
            st.subheader("Session Statistics")
        
        # Display metrics
        metric_cols = st.columns(4)
        
        with metric_cols[0]:
            st.metric("Total Queries", stats["total_queries"])
        
        with metric_cols[1]:
            st.metric("Successful", stats["successful_queries"])
        
        with metric_cols[2]:
            st.metric("Failed", stats["failed_queries"])
        
        with metric_cols[3]:
            if stats["avg_execution_time"] > 0:
                st.metric("Avg Time", f"{stats['avg_execution_time']:.0f}ms")
            else:
                st.metric("Avg Time", "N/A")
        
        # Session info
        info_cols = st.columns(2)
        
        with info_cols[0]:
            st.markdown("**Session Info:**")
            st.write(f"• Session ID: `{state.session_id[:8]}...`")
            st.write(f"• Created: {state.created_at.strftime('%m/%d/%Y %H:%M')}")
            st.write(f"• Last Updated: {state.last_updated.strftime('%m/%d/%Y %H:%M')}")
        
        with info_cols[1]:
            st.markdown("**Current State:**")
            st.write(f"• History Entries: {len(state.query_history)}")
            st.write(f"• Checkpoints: {len(state.checkpoints)}")
            st.write(f"• History Position: {state.history_index + 1 if state.history_index >= 0 else 'N/A'}")
    
    def render_complete_session_interface(self) -> Dict[str, Any]:
        """Render the complete session management interface"""
        # Create tabs for different session management features
        hist_tab, cp_tab, stats_tab = st.tabs(["📚 History", "💾 Checkpoints", "📊 Statistics"])
        
        result = {"restored_query": None, "navigation_query": None}
        
        with hist_tab:
            navigation_query = self.render_history_navigation()
            if navigation_query:
                result["navigation_query"] = navigation_query
        
        with cp_tab:
            restored_query = self.render_checkpoint_management()
            if restored_query:
                result["restored_query"] = restored_query
        
        with stats_tab:
            self.render_session_stats()
        
        return result

# Global instance for the application
session_manager = SessionManager()