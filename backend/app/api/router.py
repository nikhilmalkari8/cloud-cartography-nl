from fastapi import APIRouter
from app.api.endpoints import queries, cartography, neo4j_test

api_router = APIRouter()
api_router.include_router(queries.router, prefix="/queries", tags=["queries"])
api_router.include_router(cartography.router, prefix="/cartography", tags=["cartography"])
api_router.include_router(neo4j_test.router, prefix="/neo4j", tags=["neo4j"])