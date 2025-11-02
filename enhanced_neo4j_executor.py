# enhanced_neo4j_executor.py

import streamlit as st
from neo4j import GraphDatabase, exceptions as neo4j_exceptions
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import re
import logging
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResultType(Enum):
    """Enumeration of possible query result types"""
    GRAPH = "graph"
    TABLE = "table" 
    MIXED = "mixed"
    SCALAR = "scalar"
    ERROR = "error"
    EMPTY = "empty"

class CypherErrorType(Enum):
    """Classification of Cypher query errors"""
    SYNTAX_ERROR = "syntax"
    CONNECTION_ERROR = "connection"
    TIMEOUT_ERROR = "timeout"
    RESOURCE_ERROR = "resource"
    PERMISSION_ERROR = "permission"
    UNKNOWN_ERROR = "unknown"

@dataclass
class PerformanceMetrics:
    """Performance metrics for query execution"""
    execution_time_ms: float
    planning_time_ms: Optional[float] = None
    db_hits: Optional[int] = None
    nodes_returned: int = 0
    relationships_returned: int = 0
    memory_usage_mb: Optional[float] = None
    query_complexity: Optional[str] = None

@dataclass
class QueryResult:
    """Structured result from query execution"""
    success: bool
    data: List[Dict[str, Any]]
    execution_time: float
    performance_stats: PerformanceMetrics
    error_message: Optional[str] = None
    result_type: ResultType = ResultType.TABLE
    warning_message: Optional[str] = None

@dataclass
class ValidationResult:
    """Result of query validation"""
    is_valid: bool
    error_message: Optional[str] = None
    error_type: Optional[CypherErrorType] = None
    suggestions: List[str] = None

class EnhancedNeo4jExecutor:
    """Enhanced Neo4j query executor with performance monitoring and error handling"""
    
    def __init__(self):
        self.driver = None
        self.connection_pool_size = 10
        self.connection_timeout = 30
        self.max_transaction_retry_time = 15
        self.performance_metrics = {}
        self._connection_attempts = 0
        self._max_connection_attempts = 3
        
        # Query validation patterns
        self.destructive_patterns = [
            r'\bDELETE\b',
            r'\bDETACH\s+DELETE\b',
            r'\bDROP\b',
            r'\bCREATE\s+CONSTRAINT\b',
            r'\bDROP\s+CONSTRAINT\b',
            r'\bCREATE\s+INDEX\b',
            r'\bDROP\s+INDEX\b'
        ]
        
        # Performance warning thresholds
        self.slow_query_threshold_ms = 2000
        self.large_result_threshold = 50
        
    def _get_connection_config(self) -> Dict[str, Any]:
        """Get Neo4j connection configuration from Streamlit secrets"""
        try:
            return {
                'uri': st.secrets.neo4j.URI,
                'user': st.secrets.neo4j.USER,
                'password': st.secrets.neo4j.PASSWORD
            }
        except Exception as e:
            logger.error(f"Failed to load Neo4j credentials: {e}")
            raise ConnectionError("Neo4j credentials not found in Streamlit secrets")
    
    def _create_driver(self) -> GraphDatabase.driver:
        """Create Neo4j driver with connection pooling and resilience settings"""
        config = self._get_connection_config()
        
        return GraphDatabase.driver(
            config['uri'],
            auth=(config['user'], config['password']),
            max_connection_lifetime=3600,  # 1 hour
            max_connection_pool_size=self.connection_pool_size,
            connection_timeout=self.connection_timeout,
            max_transaction_retry_time=self.max_transaction_retry_time
        )
    
    @contextmanager
    def _get_session(self):
        """Context manager for Neo4j sessions with automatic cleanup"""
        session = None
        try:
            if not self.driver:
                self.driver = self._create_driver()
            
            session = self.driver.session()
            yield session
            
        except neo4j_exceptions.ServiceUnavailable as e:
            logger.error(f"Neo4j service unavailable: {e}")
            raise ConnectionError("Neo4j database is currently unavailable")
        except neo4j_exceptions.AuthError as e:
            logger.error(f"Neo4j authentication failed: {e}")
            raise ConnectionError("Neo4j authentication failed")
        except Exception as e:
            logger.error(f"Unexpected error creating session: {e}")
            raise
        finally:
            if session:
                session.close()
    
    def validate_query(self, query: str) -> ValidationResult:
        """Validate Cypher query syntax and security"""
        if not query or not query.strip():
            return ValidationResult(
                is_valid=False,
                error_message="Query cannot be empty",
                error_type=CypherErrorType.SYNTAX_ERROR
            )
        
        # Check for destructive operations
        query_upper = query.upper()
        for pattern in self.destructive_patterns:
            if re.search(pattern, query_upper):
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Destructive operation detected: {pattern}",
                    error_type=CypherErrorType.PERMISSION_ERROR,
                    suggestions=["Use READ-ONLY queries only", "Remove DELETE, DROP, or CREATE operations"]
                )
        
        # Basic syntax validation
        try:
            # Check for balanced parentheses and brackets
            if query.count('(') != query.count(')'):
                return ValidationResult(
                    is_valid=False,
                    error_message="Unbalanced parentheses in query",
                    error_type=CypherErrorType.SYNTAX_ERROR,
                    suggestions=["Check that all parentheses are properly closed"]
                )
            
            if query.count('[') != query.count(']'):
                return ValidationResult(
                    is_valid=False,
                    error_message="Unbalanced brackets in query",
                    error_type=CypherErrorType.SYNTAX_ERROR,
                    suggestions=["Check that all brackets are properly closed"]
                )
            
            # Check for basic Cypher keywords
            if not re.search(r'\b(MATCH|RETURN|WITH|CREATE|MERGE)\b', query_upper):
                return ValidationResult(
                    is_valid=False,
                    error_message="Query must contain at least one Cypher clause (MATCH, RETURN, etc.)",
                    error_type=CypherErrorType.SYNTAX_ERROR,
                    suggestions=["Add a MATCH clause to start your query", "Include a RETURN clause to specify output"]
                )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_message=f"Query validation error: {str(e)}",
                error_type=CypherErrorType.SYNTAX_ERROR
            )
        
        return ValidationResult(is_valid=True)
    
    def _detect_result_type(self, results: List[Dict[str, Any]]) -> ResultType:
        """Detect the type of query results"""
        if not results:
            return ResultType.EMPTY
        
        has_nodes = False
        has_relationships = False
        has_scalar = False
        
        for record in results:
            for key, value in record.items():
                if hasattr(value, 'labels'):  # Neo4j Node
                    has_nodes = True
                elif hasattr(value, 'type'):  # Neo4j Relationship
                    has_relationships = True
                elif isinstance(value, (str, int, float, bool)):
                    has_scalar = True
        
        if has_nodes and has_relationships:
            return ResultType.GRAPH
        elif has_nodes or has_relationships:
            return ResultType.MIXED
        elif has_scalar:
            return ResultType.SCALAR
        else:
            return ResultType.TABLE
    
    def _extract_performance_metrics(self, result, execution_time_ms: float) -> PerformanceMetrics:
        """Extract performance metrics from Neo4j result"""
        metrics = PerformanceMetrics(execution_time_ms=execution_time_ms)
        
        try:
            # Try to get query statistics if available
            if hasattr(result, 'consume'):
                summary = result.consume()
                if hasattr(summary, 'result_available_after'):
                    metrics.planning_time_ms = summary.result_available_after
                if hasattr(summary, 'counters'):
                    counters = summary.counters
                    metrics.nodes_returned = getattr(counters, 'nodes_created', 0) + getattr(counters, 'nodes_deleted', 0)
                    metrics.relationships_returned = getattr(counters, 'relationships_created', 0) + getattr(counters, 'relationships_deleted', 0)
        except Exception as e:
            logger.warning(f"Could not extract performance metrics: {e}")
        
        return metrics
    
    def _classify_error(self, error: Exception) -> CypherErrorType:
        """Classify Neo4j errors into categories"""
        error_str = str(error).lower()
        
        if isinstance(error, neo4j_exceptions.CypherSyntaxError):
            return CypherErrorType.SYNTAX_ERROR
        elif isinstance(error, (neo4j_exceptions.ServiceUnavailable, neo4j_exceptions.SessionExpired)):
            return CypherErrorType.CONNECTION_ERROR
        elif isinstance(error, neo4j_exceptions.TransientError):
            if 'timeout' in error_str or 'time' in error_str:
                return CypherErrorType.TIMEOUT_ERROR
            else:
                return CypherErrorType.RESOURCE_ERROR
        elif isinstance(error, neo4j_exceptions.ClientError):
            if 'permission' in error_str or 'auth' in error_str:
                return CypherErrorType.PERMISSION_ERROR
            else:
                return CypherErrorType.SYNTAX_ERROR
        else:
            return CypherErrorType.UNKNOWN_ERROR
    
    def _create_user_friendly_error(self, error: Exception, error_type: CypherErrorType) -> str:
        """Create user-friendly error messages"""
        error_messages = {
            CypherErrorType.SYNTAX_ERROR: f"Query syntax error: {str(error)}. Please check your Cypher syntax.",
            CypherErrorType.CONNECTION_ERROR: "Unable to connect to Neo4j database. Please check your connection and try again.",
            CypherErrorType.TIMEOUT_ERROR: f"Query timed out after {self.connection_timeout} seconds. Try simplifying your query or adding LIMIT clauses.",
            CypherErrorType.RESOURCE_ERROR: "Query requires too many resources. Try limiting results with LIMIT clause or simplifying the query.",
            CypherErrorType.PERMISSION_ERROR: "Permission denied. You may not have access to perform this operation.",
            CypherErrorType.UNKNOWN_ERROR: f"An unexpected error occurred: {str(error)}"
        }
        
        return error_messages.get(error_type, f"Error: {str(error)}")
    
    def execute_query(self, query: str, params: Dict[str, Any] = None) -> QueryResult:
        """Execute Cypher query with comprehensive error handling and performance monitoring"""
        start_time = time.time()
        
        # Validate query first
        validation = self.validate_query(query)
        if not validation.is_valid:
            return QueryResult(
                success=False,
                data=[],
                execution_time=0,
                performance_stats=PerformanceMetrics(execution_time_ms=0),
                error_message=validation.error_message,
                result_type=ResultType.ERROR
            )
        
        try:
            with self._get_session() as session:
                # Execute query with timeout
                result = session.run(query, parameters=params or {})
                data = result.data()
                
                execution_time_ms = (time.time() - start_time) * 1000
                
                # Extract performance metrics
                performance_stats = self._extract_performance_metrics(result, execution_time_ms)
                performance_stats.nodes_returned = len([r for r in data if any(hasattr(v, 'labels') for v in r.values())])
                performance_stats.relationships_returned = len([r for r in data if any(hasattr(v, 'type') for v in r.values())])
                
                # Detect result type
                result_type = self._detect_result_type(data)
                
                # Generate warnings for performance issues
                warning_message = None
                if execution_time_ms > self.slow_query_threshold_ms:
                    warning_message = f"Query took {execution_time_ms:.0f}ms (slower than {self.slow_query_threshold_ms}ms threshold)"
                elif len(data) > self.large_result_threshold:
                    warning_message = f"Large result set ({len(data)} records). Consider adding LIMIT clause for better performance."
                
                return QueryResult(
                    success=True,
                    data=data,
                    execution_time=execution_time_ms,
                    performance_stats=performance_stats,
                    result_type=result_type,
                    warning_message=warning_message
                )
                
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            error_type = self._classify_error(e)
            error_message = self._create_user_friendly_error(e, error_type)
            
            logger.error(f"Query execution failed: {error_message}")
            
            return QueryResult(
                success=False,
                data=[],
                execution_time=execution_time_ms,
                performance_stats=PerformanceMetrics(execution_time_ms=execution_time_ms),
                error_message=error_message,
                result_type=ResultType.ERROR
            )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get detailed performance statistics"""
        return {
            "connection_pool_size": self.connection_pool_size,
            "connection_timeout": self.connection_timeout,
            "slow_query_threshold_ms": self.slow_query_threshold_ms,
            "large_result_threshold": self.large_result_threshold,
            "driver_connected": self.driver is not None
        }
    
    def test_connection(self) -> bool:
        """Test Neo4j database connection"""
        try:
            with self._get_session() as session:
                result = session.run("RETURN 1 as test")
                return result.single()["test"] == 1
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def close(self):
        """Close the Neo4j driver and cleanup resources"""
        if self.driver:
            self.driver.close()
            self.driver = None
            logger.info("Neo4j driver closed")

# Global instance for the application
neo4j_executor = EnhancedNeo4jExecutor()