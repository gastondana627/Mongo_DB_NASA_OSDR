# results_formatter.py

import streamlit as st
import pandas as pd
from pyvis.network import Network
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import json
import re
import logging
from enhanced_neo4j_executor import ResultType, QueryResult

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class FormattedResults:
    """Container for formatted query results"""
    result_type: ResultType
    graph_html: Optional[str] = None
    table_data: Optional[pd.DataFrame] = None
    scalar_values: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ResultsFormatter:
    """Enhanced results formatter that detects and handles different result types"""
    
    def __init__(self):
        # Color mapping for different node types
        self.color_map = {
            "Study": "#0083FF",
            "Organism": "#FF6C00", 
            "Factor": "#C600FF", 
            "Assay": "#00D95A",
            "default": "#CCCCCC"
        }
        
        # Size mapping for different node types
        self.size_map = {
            "Study": 30,
            "Organism": 20,
            "Factor": 20,
            "Assay": 20,
            "default": 15
        }
        
        # Maximum nodes to display in graph (performance limit)
        self.max_graph_nodes = 50
        self.max_table_rows_per_page = 25
        
    def format_results(self, query_result: QueryResult) -> FormattedResults:
        """Main entry point for formatting query results"""
        if not query_result.success:
            return FormattedResults(
                result_type=ResultType.ERROR,
                error_message=query_result.error_message
            )
        
        if not query_result.data:
            return FormattedResults(
                result_type=ResultType.EMPTY,
                metadata={"message": "Query executed successfully but returned no results"}
            )
        
        # Format based on detected result type
        if query_result.result_type == ResultType.GRAPH:
            return self._format_graph_results(query_result)
        elif query_result.result_type == ResultType.MIXED:
            return self._format_mixed_results(query_result)
        elif query_result.result_type == ResultType.SCALAR:
            return self._format_scalar_results(query_result)
        else:  # TABLE
            return self._format_table_results(query_result)
    
    def _format_graph_results(self, query_result: QueryResult) -> FormattedResults:
        """Format results that contain nodes and relationships for graph visualization"""
        try:
            graph_html = self.create_enhanced_graph_visualization(
                query_result.data, 
                query_result.performance_stats.nodes_returned,
                query_result.performance_stats.relationships_returned
            )
            
            # Also create a table view for the raw data
            table_data = self._create_table_from_graph_data(query_result.data)
            
            return FormattedResults(
                result_type=ResultType.GRAPH,
                graph_html=graph_html,
                table_data=table_data,
                metadata={
                    "nodes_count": query_result.performance_stats.nodes_returned,
                    "relationships_count": query_result.performance_stats.relationships_returned,
                    "execution_time_ms": query_result.execution_time
                }
            )
        except Exception as e:
            return FormattedResults(
                result_type=ResultType.ERROR,
                error_message=f"Failed to create graph visualization: {str(e)}"
            )
    
    def _format_mixed_results(self, query_result: QueryResult) -> FormattedResults:
        """Format results that contain both graph elements and scalar data"""
        try:
            # Extract graph elements and scalar data separately
            graph_data, scalar_data = self._separate_mixed_data(query_result.data)
            
            graph_html = None
            if graph_data:
                graph_html = self.create_enhanced_graph_visualization(graph_data)
            
            # Create comprehensive table view
            table_data = self._create_comprehensive_table(query_result.data)
            
            return FormattedResults(
                result_type=ResultType.MIXED,
                graph_html=graph_html,
                table_data=table_data,
                scalar_values=scalar_data,
                metadata={
                    "has_graph_data": graph_html is not None,
                    "has_scalar_data": len(scalar_data) > 0 if scalar_data else False,
                    "total_records": len(query_result.data)
                }
            )
        except Exception as e:
            return FormattedResults(
                result_type=ResultType.ERROR,
                error_message=f"Failed to format mixed results: {str(e)}"
            )
    
    def _format_scalar_results(self, query_result: QueryResult) -> FormattedResults:
        """Format results that contain only scalar values"""
        try:
            # Extract scalar values
            scalar_values = {}
            processed_data = []
            
            for i, record in enumerate(query_result.data):
                processed_record = {}
                for key, value in record.items():
                    try:
                        if isinstance(value, (str, int, float, bool, type(None))):
                            scalar_key = f"{key}_{i}" if len(query_result.data) > 1 else key
                            scalar_values[scalar_key] = value
                            processed_record[key] = str(value) if value is not None else 'None'
                        else:
                            # Handle Neo4j objects or other complex types
                            processed_record[key] = str(value) if value is not None else 'None'
                    except Exception as e:
                        processed_record[f"{key}_error"] = f"Error processing: {str(e)}"
                
                processed_data.append(processed_record)
            
            # Create table view with processed data
            table_data = pd.DataFrame(processed_data)
            
            return FormattedResults(
                result_type=ResultType.SCALAR,
                table_data=table_data,
                scalar_values=scalar_values,
                metadata={
                    "total_values": len(scalar_values),
                    "total_records": len(query_result.data)
                }
            )
        except Exception as e:
            return FormattedResults(
                result_type=ResultType.ERROR,
                error_message=f"Failed to format scalar results: {str(e)}"
            )
    
    def _format_table_results(self, query_result: QueryResult) -> FormattedResults:
        """Format results for tabular display"""
        try:
            # Convert Neo4j objects to serializable format before creating DataFrame
            processed_data = []
            for record in query_result.data:
                processed_record = {}
                for key, value in record.items():
                    try:
                        if hasattr(value, 'labels'):  # Neo4j Node
                            labels = list(value.labels)
                            properties = dict(value)
                            processed_record[f"{key}_type"] = str(labels[0] if labels else "Unknown")
                            # Use element_id if available, fallback to id
                            node_id = getattr(value, 'element_id', getattr(value, 'id', 'unknown'))
                            processed_record[f"{key}_id"] = str(node_id)
                            processed_record[f"{key}_properties"] = json.dumps(properties, default=str)
                        elif hasattr(value, 'type'):  # Neo4j Relationship
                            processed_record[f"{key}_relationship"] = str(value.type)
                            # Use element_id if available, fallback to id
                            start_id = getattr(value.start_node, 'element_id', getattr(value.start_node, 'id', 'unknown'))
                            end_id = getattr(value.end_node, 'element_id', getattr(value.end_node, 'id', 'unknown'))
                            processed_record[f"{key}_start_id"] = str(start_id)
                            processed_record[f"{key}_end_id"] = str(end_id)
                            processed_record[f"{key}_properties"] = json.dumps(dict(value), default=str)
                        else:
                            # Convert all values to strings to avoid struct/non-struct mixing
                            processed_record[key] = str(value) if value is not None else 'None'
                    except Exception as e:
                        # Fallback for any problematic values
                        processed_record[f"{key}_error"] = f"Error processing: {str(e)}"
                
                processed_data.append(processed_record)
            
            table_data = pd.DataFrame(processed_data)
            
            return FormattedResults(
                result_type=ResultType.TABLE,
                table_data=table_data,
                metadata={
                    "total_records": len(query_result.data),
                    "columns": list(table_data.columns) if not table_data.empty else []
                }
            )
        except Exception as e:
            return FormattedResults(
                result_type=ResultType.ERROR,
                error_message=f"Failed to format table results: {str(e)}"
            )
    
    def create_enhanced_graph_visualization(
        self, 
        query_data: List[Dict[str, Any]], 
        nodes_count: int = 0, 
        relationships_count: int = 0
    ) -> Optional[str]:
        """Create enhanced Pyvis graph with interactive node clicking capabilities"""
        if not query_data:
            return None
        
        # Create network with enhanced settings
        net = Network(
            height="600px", 
            width="100%", 
            notebook=True, 
            cdn_resources='in_line', 
            bgcolor="#1E1E1E", 
            font_color="#FFFFFF", 
            directed=True
        )
        
        # Enhanced physics configuration for better interactivity
        net.set_options("""
        var options = {
          "physics": {
            "barnesHut": {
              "gravitationalConstant": -30000,
              "centralGravity": 0.1,
              "springLength": 150,
              "springConstant": 0.05,
              "damping": 0.4
            },
            "minVelocity": 0.75,
            "maxVelocity": 30,
            "stabilization": {
              "enabled": true,
              "iterations": 100,
              "updateInterval": 25
            }
          },
          "interaction": {
            "hover": true,
            "tooltipDelay": 200,
            "selectConnectedEdges": true,
            "hoverConnectedEdges": true
          },
          "nodes": {
            "borderWidth": 2,
            "borderWidthSelected": 4,
            "font": {
              "size": 12,
              "face": "arial"
            }
          },
          "edges": {
            "width": 2,
            "selectionWidth": 4,
            "hoverWidth": 3,
            "arrows": {
              "to": {
                "enabled": true,
                "scaleFactor": 1.2
              }
            }
          }
        }
        """)
        
        added_nodes = set()
        added_edges = set()
        node_count = 0
        
        # Process query results to extract nodes and relationships
        for record in query_data:
            # Stop if we exceed the maximum node limit
            if node_count >= self.max_graph_nodes:
                break
                
            for key, value in record.items():
                try:
                    # Handle Neo4j Node objects
                    if hasattr(value, 'labels') and hasattr(value, 'id'):
                        if self._add_node_to_graph(net, value, added_nodes):
                            node_count += 1
                            if node_count >= self.max_graph_nodes:
                                break
                    
                    # Handle Neo4j Relationship objects
                    elif hasattr(value, 'type') and hasattr(value, 'start_node') and hasattr(value, 'end_node'):
                        self._add_relationship_to_graph(net, value, added_edges, added_nodes)
                        
                        # Ensure both nodes are added
                        for node in [value.start_node, value.end_node]:
                            node_id = getattr(node, 'element_id', getattr(node, 'id', None))
                            if node_id not in added_nodes and node_count < self.max_graph_nodes:
                                if self._add_node_to_graph(net, node, added_nodes):
                                    node_count += 1
                except Exception as e:
                    # Log the error but continue processing other records
                    logger.warning(f"Error processing graph element {key}: {str(e)}")
                    continue
        
        # Add warning if we hit the node limit
        if node_count >= self.max_graph_nodes:
            warning_html = f"""
            <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; color: #856404; 
                        padding: 10px; margin: 10px 0; border-radius: 5px;">
                <strong>Large Result Set:</strong> Displaying top {self.max_graph_nodes} nodes by centrality. 
                Total nodes in result: {nodes_count}. Consider adding LIMIT clause for better performance.
            </div>
            """
        else:
            warning_html = ""
        
        # Only return HTML if we have nodes to display
        if added_nodes:
            graph_html = net.generate_html()
            
            # Add custom JavaScript for node click handling
            click_handler_js = """
            <script>
            // Add click event listener for nodes
            network.on("click", function (params) {
                if (params.nodes.length > 0) {
                    var nodeId = params.nodes[0];
                    var nodeData = nodes.get(nodeId);
                    
                    if (nodeData && nodeData['data-click']) {
                        try {
                            var clickData = JSON.parse(nodeData['data-click']);
                            
                            // Store click data in Streamlit session state via a hidden form
                            var form = document.createElement('form');
                            form.method = 'POST';
                            form.style.display = 'none';
                            
                            var input = document.createElement('input');
                            input.type = 'hidden';
                            input.name = 'node_click_data';
                            input.value = JSON.stringify(clickData);
                            form.appendChild(input);
                            
                            document.body.appendChild(form);
                            
                            // Trigger Streamlit rerun with node data
                            window.parent.postMessage({
                                type: 'streamlit:setComponentValue',
                                value: clickData
                            }, '*');
                            
                            // Show user feedback
                            alert('Node clicked: ' + clickData.node_type + ' - ' + (clickData.properties.name || clickData.properties.study_id || 'Unknown'));
                            
                        } catch (e) {
                            console.error('Error handling node click:', e);
                        }
                    }
                }
            });
            </script>
            """
            
            # Insert the JavaScript before the closing body tag
            if "</body>" in graph_html:
                graph_html = graph_html.replace("</body>", click_handler_js + "</body>")
            else:
                graph_html += click_handler_js
            
            return warning_html + graph_html
        else:
            return None
    
    def _add_node_to_graph(self, net: Network, node, added_nodes: set) -> bool:
        """Add a node to the Pyvis graph with enhanced properties"""
        # Use element_id if available (newer Neo4j versions), fallback to id
        node_id = getattr(node, 'element_id', getattr(node, 'id', None))
        
        if node_id in added_nodes:
            return False
        
        labels = list(node.labels)
        properties = dict(node)
        node_type = labels[0] if labels else "Unknown"
        
        # Create enhanced node label and title
        label, title = self._create_node_display_info(node_type, properties, node_id)
        
        # Add click event data for interactive functionality
        click_data = {
            "node_id": str(node_id),
            "node_type": node_type,
            "properties": properties
        }
        
        # Create enhanced title with click instruction
        enhanced_title = title + "\n\n🖱️ Click to generate related queries"
        
        net.add_node(
            node_id,
            label=label,
            title=enhanced_title,
            color=self.color_map.get(node_type, self.color_map["default"]),
            size=self.size_map.get(node_type, self.size_map["default"]),
            group=node_type,
            # Store click data for JavaScript interaction
            **{"data-click": json.dumps(click_data)}
        )
        
        added_nodes.add(node_id)
        return True
    
    def _add_relationship_to_graph(self, net: Network, relationship, added_edges: set, added_nodes: set):
        """Add a relationship to the Pyvis graph"""
        # Use element_id if available (newer Neo4j versions), fallback to id
        start_id = getattr(relationship.start_node, 'element_id', getattr(relationship.start_node, 'id', None))
        end_id = getattr(relationship.end_node, 'element_id', getattr(relationship.end_node, 'id', None))
        rel_type = relationship.type
        rel_properties = dict(relationship)
        
        edge_key = (start_id, end_id, rel_type)
        if edge_key not in added_edges:
            # Create enhanced relationship title
            title = f"Relationship: {rel_type}"
            if rel_properties:
                title += "\n\nProperties:"
                for prop_key, prop_value in rel_properties.items():
                    title += f"\n{prop_key}: {str(prop_value)[:50]}"
            
            net.add_edge(
                start_id, 
                end_id, 
                label=rel_type,
                title=title,
                color="#888888",
                width=2
            )
            added_edges.add(edge_key)
    
    def _create_node_display_info(self, node_type: str, properties: Dict, node_id: int) -> Tuple[str, str]:
        """Create enhanced display label and tooltip for nodes"""
        # Create node label
        if node_type == "Study":
            label = properties.get('study_id', f'Node_{node_id}')
            title = f"Study: {properties.get('study_id', 'Unknown')}\nTitle: {properties.get('title', 'No title')}"
        elif node_type == "Organism":
            label = properties.get('organism_name', properties.get('name', f'Node_{node_id}'))
            title = f"Organism: {label}"
        elif node_type == "Factor":
            label = properties.get('factor_name', properties.get('name', f'Node_{node_id}'))
            title = f"Factor: {label}"
        elif node_type == "Assay":
            label = properties.get('assay_name', properties.get('name', f'Node_{node_id}'))
            title = f"Assay: {label}"
        else:
            label = properties.get('name', f'Node_{node_id}')
            title = f"{node_type}: {label}"
        
        # Add properties to title with better formatting
        if properties:
            title += "\n\nProperties:"
            for prop_key, prop_value in properties.items():
                if prop_key not in ['name', 'study_id', 'title', 'organism_name', 'factor_name', 'assay_name']:
                    # Truncate long values
                    value_str = str(prop_value)
                    if len(value_str) > 50:
                        value_str = value_str[:47] + "..."
                    title += f"\n{prop_key}: {value_str}"
        
        # Add click instruction
        title += "\n\nClick to generate related queries"
        
        return label, title
    
    def _create_table_from_graph_data(self, query_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Create a table view from graph data for alternative display"""
        table_rows = []
        
        for record in query_data:
            row = {}
            for key, value in record.items():
                try:
                    if hasattr(value, 'labels'):  # Neo4j Node
                        labels = list(value.labels)
                        properties = dict(value)
                        row[f"{key}_type"] = labels[0] if labels else "Unknown"
                        # Use element_id if available, fallback to id
                        node_id = getattr(value, 'element_id', getattr(value, 'id', 'unknown'))
                        row[f"{key}_id"] = str(node_id)
                        # Add key properties
                        if labels and labels[0] == "Study":
                            row[f"{key}_study_id"] = str(properties.get('study_id', 'N/A'))
                            row[f"{key}_title"] = str(properties.get('title', 'N/A'))
                        else:
                            row[f"{key}_name"] = str(properties.get('name', properties.get('organism_name', properties.get('factor_name', 'N/A'))))
                    elif hasattr(value, 'type'):  # Neo4j Relationship
                        row[f"{key}_relationship"] = str(value.type)
                        # Use element_id if available, fallback to id
                        start_id = getattr(value.start_node, 'element_id', getattr(value.start_node, 'id', 'unknown'))
                        end_id = getattr(value.end_node, 'element_id', getattr(value.end_node, 'id', 'unknown'))
                        row[f"{key}_start_id"] = str(start_id)
                        row[f"{key}_end_id"] = str(end_id)
                    else:
                        # Convert all values to strings to avoid struct/non-struct mixing
                        row[key] = str(value) if value is not None else 'None'
                except Exception as e:
                    # Fallback for any problematic values
                    row[f"{key}_error"] = f"Error processing: {str(e)}"
            
            if row:  # Only add non-empty rows
                table_rows.append(row)
        
        return pd.DataFrame(table_rows) if table_rows else pd.DataFrame()
    
    def _separate_mixed_data(self, query_data: List[Dict[str, Any]]) -> Tuple[List[Dict], Dict[str, Any]]:
        """Separate mixed data into graph elements and scalar values"""
        graph_data = []
        scalar_data = {}
        
        for i, record in enumerate(query_data):
            graph_record = {}
            has_graph_elements = False
            
            for key, value in record.items():
                if hasattr(value, 'labels') or hasattr(value, 'type'):  # Graph elements
                    graph_record[key] = value
                    has_graph_elements = True
                else:  # Scalar values
                    scalar_key = f"{key}_{i}" if len(query_data) > 1 else key
                    scalar_data[scalar_key] = value
            
            if has_graph_elements:
                graph_data.append(graph_record)
        
        return graph_data, scalar_data
    
    def _create_comprehensive_table(self, query_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Create a comprehensive table view for mixed data"""
        table_rows = []
        
        for record in query_data:
            row = {}
            for key, value in record.items():
                try:
                    if hasattr(value, 'labels'):  # Neo4j Node
                        labels = list(value.labels)
                        properties = dict(value)
                        row[f"{key}_type"] = str(labels[0] if labels else "Unknown")
                        row[f"{key}_properties"] = json.dumps(properties, default=str)
                    elif hasattr(value, 'type'):  # Neo4j Relationship
                        row[f"{key}_relationship"] = str(value.type)
                        row[f"{key}_properties"] = json.dumps(dict(value), default=str)
                    else:
                        # Convert all values to strings to avoid struct/non-struct mixing
                        row[key] = str(value) if value is not None else 'None'
                except Exception as e:
                    # Fallback for any problematic values
                    row[f"{key}_error"] = f"Error processing: {str(e)}"
            
            table_rows.append(row)
        
        return pd.DataFrame(table_rows)
    
    def create_paginated_table_display(self, df: pd.DataFrame, page_size: int = None) -> Dict[str, Any]:
        """Create paginated table display for large datasets"""
        if page_size is None:
            page_size = self.max_table_rows_per_page
        
        total_rows = len(df)
        total_pages = (total_rows + page_size - 1) // page_size
        
        # Initialize page number in session state if not exists
        if 'table_page' not in st.session_state:
            st.session_state.table_page = 0
        
        # Ensure page number is within bounds
        st.session_state.table_page = max(0, min(st.session_state.table_page, total_pages - 1))
        
        # Calculate slice indices
        start_idx = st.session_state.table_page * page_size
        end_idx = min(start_idx + page_size, total_rows)
        
        # Get current page data
        current_page_df = df.iloc[start_idx:end_idx]
        
        return {
            "data": current_page_df,
            "current_page": st.session_state.table_page + 1,
            "total_pages": total_pages,
            "total_rows": total_rows,
            "start_row": start_idx + 1,
            "end_row": end_idx,
            "has_pagination": total_pages > 1
        }
    
    def render_results_display(self, formatted_results: FormattedResults):
        """Render the formatted results in Streamlit"""
        if formatted_results.result_type == ResultType.ERROR:
            # Custom error with NASA emoji
            import os
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
            EMOJI_ASSETS_DIR = os.path.join(BASE_DIR, "assets", "emojis")
            error_emoji = os.path.join(EMOJI_ASSETS_DIR, "MArs_Rover_1.svg")
            
            error_cols = st.columns([1, 20])
            with error_cols[0]:
                if os.path.exists(error_emoji):
                    st.image(error_emoji, width=20)
            with error_cols[1]:
                st.error(formatted_results.error_message)
            return
        
        if formatted_results.result_type == ResultType.EMPTY:
            # Custom info with NASA emoji
            import os
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
            EMOJI_ASSETS_DIR = os.path.join(BASE_DIR, "assets", "emojis")
            info_emoji = os.path.join(EMOJI_ASSETS_DIR, "Earth_2.svg")
            
            info_cols = st.columns([1, 20])
            with info_cols[0]:
                if os.path.exists(info_emoji):
                    st.image(info_emoji, width=20)
            with info_cols[1]:
                st.info("Query executed successfully but returned no results.")
            return
        
        # Display metadata if available
        if formatted_results.metadata:
            self._render_metadata(formatted_results.metadata)
        
        # Display based on result type
        if formatted_results.result_type == ResultType.GRAPH:
            self._render_graph_results(formatted_results)
        elif formatted_results.result_type == ResultType.MIXED:
            self._render_mixed_results(formatted_results)
        elif formatted_results.result_type == ResultType.SCALAR:
            self._render_scalar_results(formatted_results)
        else:  # TABLE
            self._render_table_results(formatted_results)
    
    def _render_metadata(self, metadata: Dict[str, Any]):
        """Render metadata information"""
        if "nodes_count" in metadata or "relationships_count" in metadata:
            cols = st.columns(4)
            if "execution_time_ms" in metadata:
                cols[0].metric("Execution Time", f"{metadata['execution_time_ms']:.0f}ms")
            if "nodes_count" in metadata:
                cols[1].metric("Nodes", metadata["nodes_count"])
            if "relationships_count" in metadata:
                cols[2].metric("Relationships", metadata["relationships_count"])
            if "total_records" in metadata:
                cols[3].metric("Records", metadata["total_records"])
    
    def _render_graph_results(self, formatted_results: FormattedResults):
        """Render graph results with both graph and table views"""
        # Display graph
        if formatted_results.graph_html:
            # Custom subheader with NASA emoji
            import os
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
            EMOJI_ASSETS_DIR = os.path.join(BASE_DIR, "assets", "emojis")
            web_emoji = os.path.join(EMOJI_ASSETS_DIR, "Satellite_Ground_1.svg")
            
            web_cols = st.columns([1, 10])
            with web_cols[0]:
                if os.path.exists(web_emoji):
                    st.image(web_emoji, width=30)
            with web_cols[1]:
                st.subheader("Graph Visualization")
            st.components.v1.html(formatted_results.graph_html, height=600, scrolling=True)
        
        # Display table view as alternative
        if formatted_results.table_data is not None and not formatted_results.table_data.empty:
            # Custom subheader with NASA emoji
            chart_emoji = os.path.join(EMOJI_ASSETS_DIR, "Satellite_Ground_1.svg")
            
            chart_cols = st.columns([1, 10])
            with chart_cols[0]:
                if os.path.exists(chart_emoji):
                    st.image(chart_emoji, width=30)
            with chart_cols[1]:
                st.subheader("Tabular View")
            with st.expander("Show raw data table", expanded=False):
                pagination_info = self.create_paginated_table_display(formatted_results.table_data)
                
                if pagination_info["has_pagination"]:
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col1:
                        if st.button("Previous", disabled=pagination_info["current_page"] <= 1):
                            st.session_state.table_page -= 1
                            st.rerun()
                    with col2:
                        st.write(f"Page {pagination_info['current_page']} of {pagination_info['total_pages']} "
                               f"(Rows {pagination_info['start_row']}-{pagination_info['end_row']} of {pagination_info['total_rows']})")
                    with col3:
                        if st.button("Next", disabled=pagination_info["current_page"] >= pagination_info["total_pages"]):
                            st.session_state.table_page += 1
                            st.rerun()
                
                st.dataframe(pagination_info["data"], use_container_width=True)
    
    def _render_mixed_results(self, formatted_results: FormattedResults):
        """Render mixed results with both graph and scalar data"""
        # Display graph if available
        if formatted_results.graph_html:
            st.subheader("🕸️ Graph Visualization")
            st.components.v1.html(formatted_results.graph_html, height=600, scrolling=True)
        
        # Display scalar values
        if formatted_results.scalar_values:
            st.subheader("📈 Scalar Values")
            cols = st.columns(min(len(formatted_results.scalar_values), 4))
            for i, (key, value) in enumerate(formatted_results.scalar_values.items()):
                cols[i % 4].metric(key, value)
        
        # Display comprehensive table
        if formatted_results.table_data is not None and not formatted_results.table_data.empty:
            st.subheader("📊 Complete Data")
            pagination_info = self.create_paginated_table_display(formatted_results.table_data)
            
            if pagination_info["has_pagination"]:
                col1, col2, col3 = st.columns([1, 2, 1])
                with col1:
                    if st.button("◀ Previous", disabled=pagination_info["current_page"] <= 1):
                        st.session_state.table_page -= 1
                        st.rerun()
                with col2:
                    st.write(f"Page {pagination_info['current_page']} of {pagination_info['total_pages']}")
                with col3:
                    if st.button("Next ▶", disabled=pagination_info["current_page"] >= pagination_info["total_pages"]):
                        st.session_state.table_page += 1
                        st.rerun()
            
            st.dataframe(pagination_info["data"], use_container_width=True)
    
    def _render_scalar_results(self, formatted_results: FormattedResults):
        """Render scalar results"""
        if formatted_results.scalar_values:
            st.subheader("📈 Results")
            # Display as metrics if we have few values
            if len(formatted_results.scalar_values) <= 8:
                cols = st.columns(min(len(formatted_results.scalar_values), 4))
                for i, (key, value) in enumerate(formatted_results.scalar_values.items()):
                    cols[i % 4].metric(key, value)
            else:
                # Display as table for many values
                st.dataframe(pd.DataFrame([formatted_results.scalar_values]), use_container_width=True)
        
        # Also show table view
        if formatted_results.table_data is not None and not formatted_results.table_data.empty:
            st.subheader("📊 Detailed View")
            st.dataframe(formatted_results.table_data, use_container_width=True)
    
    def _render_table_results(self, formatted_results: FormattedResults):
        """Render table results with pagination and filtering"""
        if formatted_results.table_data is not None and not formatted_results.table_data.empty:
            st.subheader("📊 Query Results")
            
            # Add filtering options for large datasets
            if len(formatted_results.table_data) > 10:
                with st.expander("🔍 Filter Options", expanded=False):
                    # Column-based filtering
                    filter_column = st.selectbox("Filter by column:", ["None"] + list(formatted_results.table_data.columns))
                    if filter_column != "None":
                        unique_values = formatted_results.table_data[filter_column].unique()
                        if len(unique_values) <= 20:  # Dropdown for few unique values
                            filter_value = st.selectbox(f"Select {filter_column}:", ["All"] + list(unique_values))
                            if filter_value != "All":
                                formatted_results.table_data = formatted_results.table_data[
                                    formatted_results.table_data[filter_column] == filter_value
                                ]
                        else:  # Text input for many unique values
                            filter_text = st.text_input(f"Filter {filter_column} contains:")
                            if filter_text:
                                formatted_results.table_data = formatted_results.table_data[
                                    formatted_results.table_data[filter_column].astype(str).str.contains(filter_text, case=False, na=False)
                                ]
            
            # Pagination
            pagination_info = self.create_paginated_table_display(formatted_results.table_data)
            
            if pagination_info["has_pagination"]:
                col1, col2, col3 = st.columns([1, 2, 1])
                with col1:
                    if st.button("◀ Previous", disabled=pagination_info["current_page"] <= 1):
                        st.session_state.table_page -= 1
                        st.rerun()
                with col2:
                    st.write(f"Page {pagination_info['current_page']} of {pagination_info['total_pages']} "
                           f"(Showing {pagination_info['start_row']}-{pagination_info['end_row']} of {pagination_info['total_rows']} rows)")
                with col3:
                    if st.button("Next ▶", disabled=pagination_info["current_page"] >= pagination_info["total_pages"]):
                        st.session_state.table_page += 1
                        st.rerun()
            
            # Display the table with sorting
            st.dataframe(
                pagination_info["data"], 
                use_container_width=True,
                column_config={
                    col: st.column_config.TextColumn(col, width="medium") 
                    for col in pagination_info["data"].columns
                }
            )

# Global instance for the application
results_formatter = ResultsFormatter()