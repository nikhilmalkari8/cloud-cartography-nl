from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.aws_collector import AwsCollectorService
from app.services.neo4j_service import Neo4jService
from app.services.nlp_service import NLPService
from app.dependencies import get_neo4j_service
import os

router = APIRouter()

class AwsCredentials(BaseModel):
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    openai_api_key: str = ""
    use_sample_data: bool = False

@router.post("/collect")
async def collect_aws_data(
    credentials: AwsCredentials,
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    try:
        # Set environment variables for the AWS collector
        if not credentials.use_sample_data:
            os.environ["AWS_ACCESS_KEY_ID"] = credentials.aws_access_key_id
            os.environ["AWS_SECRET_ACCESS_KEY"] = credentials.aws_secret_access_key
        
        os.environ["AWS_REGION"] = credentials.aws_region
        
        if credentials.openai_api_key:
            os.environ["OPENAI_API_KEY"] = credentials.openai_api_key
        
        # Clear existing data in Neo4j (optional)
        neo4j_service.execute_query("MATCH (n) DETACH DELETE n")
        
        # Create AWS collector service with the provided credentials
        aws_collector = AwsCollectorService(
            aws_access_key_id=credentials.aws_access_key_id if not credentials.use_sample_data else "",
            aws_secret_access_key=credentials.aws_secret_access_key if not credentials.use_sample_data else "",
            aws_region=credentials.aws_region,
            neo4j_service=neo4j_service
        )
        
        # Collect and store AWS data
        result = await aws_collector.collect_and_store_aws_data()
        
        return {
            "status": "success",
            "message": "AWS data collected and stored in Neo4j successfully",
            "details": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))