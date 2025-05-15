from fastapi import APIRouter
from app.api.endpoints import queries

api_router = APIRouter()
api_router.include_router(queries.router, prefix="/queries", tags=["queries"])