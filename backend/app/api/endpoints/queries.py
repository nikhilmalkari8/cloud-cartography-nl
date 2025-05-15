from fastapi import APIRouter, Depends, HTTPException
from app.models.query import QueryRequest, QueryResponse
from app.services.neo4j_service import Neo4jService
from app.services.nlp_service import NLPService
from app.dependencies import get_neo4j_service, get_nlp_service

router = APIRouter()

@router.post("/", response_model=QueryResponse)
async def process_query(
    query_request: QueryRequest,
    neo4j_service: Neo4jService = Depends(get_neo4j_service),
    nlp_service: NLPService = Depends(get_nlp_service)
):
    try:
        # Translate natural language to Cypher
        cypher_details = await nlp_service.translate_to_cypher(
            query_request.natural_language_query
        )
        
        # Execute Cypher query
        graph_data = neo4j_service.execute_query(
            cypher_details.cypher_query,
            cypher_details.parameters
        )
        
        # Prepare response
        response = QueryResponse(
            graph_data=graph_data,
            query_details=cypher_details if query_request.include_query_details else None
        )
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))