from fastapi import APIRouter, Depends, HTTPException
from app.services.neo4j_service import Neo4jService
from app.dependencies import get_neo4j_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/test-connection")
async def test_neo4j_connection(neo4j_service: Neo4jService = Depends(get_neo4j_service)):
    """
    Test the Neo4j connection.
    """
    try:
        # Try a simple query
        result = neo4j_service.execute_query("RETURN 1 as test")
        return {
            "status": "success",
            "message": "Neo4j connection successful",
            "details": {
                "uri": neo4j_service.uri,
                "user": neo4j_service.user
            }
        }
    except Exception as e:
        logger.error(f"Neo4j connection test failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Neo4j connection test failed: {str(e)}"
        )