from app.services.neo4j_service import Neo4jService
from app.services.nlp_service import NLPService
from app.services.aws_collector import AwsCollectorService
from app.config import settings
import os

# Singleton instances
_neo4j_service = None
_nlp_service = None

def get_neo4j_service() -> Neo4jService:
    global _neo4j_service
    if _neo4j_service is None:
        _neo4j_service = Neo4jService(
            uri=settings.NEO4J_URI,
            user=settings.NEO4J_USER,
            password=settings.NEO4J_PASSWORD
        )
    return _neo4j_service

def get_nlp_service() -> NLPService:
    global _nlp_service
    # Get the most recent OPENAI_API_KEY if it's been set by the AWS collection endpoint
    openai_api_key = os.environ.get("OPENAI_API_KEY", settings.OPENAI_API_KEY)
    
    if _nlp_service is None or _nlp_service.openai_api_key != openai_api_key:
        _nlp_service = NLPService(
            openai_api_key=openai_api_key,
            openai_model=settings.OPENAI_MODEL
        )
    return _nlp_service

def get_aws_collector_service() -> AwsCollectorService:
    # Get the most recent AWS credentials if they've been set by the AWS collection endpoint
    aws_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID", settings.AWS_ACCESS_KEY_ID)
    aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY", settings.AWS_SECRET_ACCESS_KEY)
    aws_region = os.environ.get("AWS_REGION", settings.AWS_REGION)
    
    # Create a new instance with the current credentials
    aws_collector_service = AwsCollectorService(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_region=aws_region,
        neo4j_service=get_neo4j_service()
    )
    
    return aws_collector_service