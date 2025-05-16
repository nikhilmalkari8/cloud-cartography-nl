from fastapi import APIRouter
from app.api.endpoints import queries, aws

api_router = APIRouter()
api_router.include_router(queries.router, prefix="/queries", tags=["queries"])
api_router.include_router(aws.router, prefix="/aws", tags=["aws"])