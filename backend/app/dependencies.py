from app.services.neo4j_service import Neo4jService
from app.services.nlp_service import NLPService
from app.services.aws_collector import AwsCollectorService
from app.config import settings

# Singleton instances
_neo4j_service = None
_nlp_service = None
_aws_collector_service = None

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
    if _nlp_service is None:
        _nlp_service = NLPService(
            openai_api_key=settings.OPENAI_API_KEY,
            openai_model=settings.OPENAI_MODEL
        )
    return _nlp_service

def get_aws_collector_service() -> AwsCollectorService:
    global _aws_collector_service
    if _aws_collector_service is None:
        _aws_collector_service = AwsCollectorService(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            aws_region=settings.AWS_REGION,
            neo4j_service=get_neo4j_service()
        )
    return _aws_collector_service