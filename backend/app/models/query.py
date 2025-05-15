from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class QueryRequest(BaseModel):
    natural_language_query: str
    include_query_details: bool = False

class CypherQueryDetails(BaseModel):
    cypher_query: str
    parameters: Dict[str, Any] = {}
    explanation: str = ""

class NodeData(BaseModel):
    id: str
    labels: List[str]
    properties: Dict[str, Any]

class RelationshipData(BaseModel):
    id: str
    type: str
    start_node: str
    end_node: str
    properties: Dict[str, Any]

class GraphData(BaseModel):
    nodes: List[NodeData]
    relationships: List[RelationshipData]

class QueryResponse(BaseModel):
    graph_data: GraphData
    query_details: Optional[CypherQueryDetails] = None