from app.services.neo4j_service import Neo4jService
from app.services.nlp_service import NLPService
from app.services.cartography_service import CartographyService
from app.config import settings
import os

# Singleton instances
_neo4j_service = None
_nlp_service = None
_cartography_service = None

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
    # Get the latest OpenAI API key from environment variable if it exists
    openai_api_key = os.environ.get("OPENAI_API_KEY", settings.OPENAI_API_KEY)
    
    if _nlp_service is None or _nlp_service.openai_api_key != openai_api_key:
        _nlp_service = NLPService(
            openai_api_key=openai_api_key,
            openai_model=settings.OPENAI_MODEL
        )
    return _nlp_service

def get_cartography_service() -> CartographyService:
    global _cartography_service
    if _cartography_service is None:
        _cartography_service = CartographyService(
            neo4j_uri=settings.NEO4J_URI,
            neo4j_user=settings.NEO4J_USER,
            neo4j_password=settings.NEO4J_PASSWORD
        )
    return _cartography_service