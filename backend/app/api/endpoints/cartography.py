from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os

from app.services.cartography_service import CartographyService
from app.services.neo4j_service import Neo4jService
from app.config import settings

router = APIRouter()

class CartographyOptions(BaseModel):
    collect_dns: bool = False
    collect_gcp: bool = False
    collect_okta: bool = False
    days_of_data: int = 7

class CartographyRequest(BaseModel):
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    openai_api_key: str = ""
    use_sample_data: bool = False
    advanced_options: Optional[CartographyOptions] = None

@router.post("/run")
async def run_cartography(request: CartographyRequest):
    """
    Run Cartography to collect cloud infrastructure data and store it in Neo4j.
    """
    try:
        # Set OpenAI API key if provided
        if request.openai_api_key:
            os.environ["OPENAI_API_KEY"] = request.openai_api_key
        
        # Create Cartography service
        cartography_service = CartographyService(
            neo4j_uri=settings.NEO4J_URI,
            neo4j_user=settings.NEO4J_USER,
            neo4j_password=settings.NEO4J_PASSWORD
        )
        
        # Run Cartography
        result = await cartography_service.run_cartography(
            aws_access_key_id=request.aws_access_key_id,
            aws_secret_access_key=request.aws_secret_access_key,
            aws_region=request.aws_region,
            use_sample_data=request.use_sample_data,
            advanced_options=request.advanced_options.dict() if request.advanced_options else None
        )
        
        if result.get("status") == "error":
            raise HTTPException(
                status_code=500,
                detail=f"Cartography failed: {result.get('message', 'Unknown error')}"
            )
        
        return {
            "status": "success",
            "message": "Knowledge graph created successfully with Cartography"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error running Cartography: {str(e)}"
        )