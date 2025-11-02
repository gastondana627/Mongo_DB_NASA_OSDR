with tab_kg:
    st.subheader("Cypher Query Interface")
    
    # Query editor
    current_query = st.text_area("Enter Cypher Query:", height=150, placeholder="MATCH (n) RETURN n LIMIT 10")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Execute Query"):
            with st.spinner("Executing..."):
                try:
                    result = neo4j_executor.execute_query(current_query)
                    if result.success:
                        st.session_state.cypher_query_result = result
                        st.success(f"Query executed in {result.execution_time:.0f}ms")
                        if result.data:
                            st.json(result.data[:10])  # Show first 10 results
                    else:
                        st.error(f"Query error: {result.error_message}")
                except Exception as e:
                    st.error(f"Execution error: {str(e)}")
    
    with col2:
        if st.button("Clear Results"):
            st.session_state.cypher_query_result = None
            st.rerun()
    
    with col3:
        if st.button("Sample Query"):
            st.session_state.current_query = "MATCH (s:Study) RETURN s LIMIT 10"
            st.rerun()

with tab_extract:
