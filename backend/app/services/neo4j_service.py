from neo4j import GraphDatabase
from app.models.query import GraphData, NodeData, RelationshipData
from typing import Dict, Any, List

class Neo4jService:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

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
        with self.driver.session() as session:
            result = session.run(cypher_query, parameters)
            return self._process_result(result)
    
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