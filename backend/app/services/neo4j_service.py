from neo4j import GraphDatabase
from app.models.query import GraphData, NodeData, RelationshipData
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class Neo4jService:
    def __init__(self, uri: str, user: str, password: str):
        # Ensure uri uses localhost, not neo4j
        if "neo4j:" in uri:
            uri = uri.replace("neo4j:", "localhost:")
        
        # Store connection details (without password)
        self.uri = uri
        self.user = user
        
        logger.info(f"Connecting to Neo4j at {uri} with user {user}")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        
        # Test connection
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            logger.info("Successfully connected to Neo4j")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {str(e)}")
            raise

    def close(self):
        self.driver.close()

    def execute_query(self, cypher_query: str, parameters: Dict[str, Any] = {}) -> GraphData:
        """
        Execute a Cypher query and return the results in a standardized format.
        
        Args:
            cypher_query: The Cypher query to execute
            parameters: Parameters for the Cypher query
            
        Returns:
            GraphData object containing nodes and relationships
        """
        try:
            with self.driver.session() as session:
                result = session.run(cypher_query, parameters)
                return self._process_result(result)
        except Exception as e:
            logger.error(f"Error executing Cypher query: {str(e)}")
            logger.error(f"Query: {cypher_query}")
            logger.error(f"Parameters: {parameters}")
            raise
    
    def _process_result(self, result):
        """
        Process Neo4j result into standardized GraphData format.
        """
        nodes_dict = {}
        relationships_dict = {}
        
        # Process all records
        for record in result:
            for item in record.values():
                if hasattr(item, "nodes") and hasattr(item, "relationships"):
                    # This is a path
                    for node in item.nodes:
                        self._add_node_to_dict(node, nodes_dict)
                    for rel in item.relationships:
                        self._add_relationship_to_dict(rel, relationships_dict)
                elif hasattr(item, "labels"):
                    # This is a node
                    self._add_node_to_dict(item, nodes_dict)
                elif hasattr(item, "type"):
                    # This is a relationship
                    self._add_relationship_to_dict(item, relationships_dict)
        
        # Convert dictionaries to lists
        nodes = [NodeData(
            id=str(node_id),
            labels=list(node.labels),
            properties=dict(node)
        ) for node_id, node in nodes_dict.items()]
        
        relationships = [RelationshipData(
            id=str(rel_id),
            type=rel.type,
            start_node=str(rel.start_node.id),
            end_node=str(rel.end_node.id),
            properties=dict(rel)
        ) for rel_id, rel in relationships_dict.items()]
        
        return GraphData(nodes=nodes, relationships=relationships)
    
    def _add_node_to_dict(self, node, nodes_dict):
        if node.id not in nodes_dict:
            nodes_dict[node.id] = node
    
    def _add_relationship_to_dict(self, rel, relationships_dict):
        if rel.id not in relationships_dict:
            relationships_dict[rel.id] = rel