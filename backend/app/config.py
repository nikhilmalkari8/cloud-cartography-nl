import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "Cloud Cartography NL Query System"
    API_V1_STR: str = "/api/v1"
    
    # Neo4j settings - use the working credentials
    NEO4J_URI: str = "bolt://localhost:7690"  # This port worked in your test
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "ssrtLvuf43123!"  # Use the same password that worked in your test
    
    # AWS settings
    AWS_ACCESS_KEY_ID: str = os.environ.get("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION: str = os.environ.get("AWS_REGION", "us-east-1")
    
    # OpenAI settings
    OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
    
    # CORS settings
    CORS_ORIGINS: list = ["http://localhost:3000", "http://frontend:3000"]
    
    class Config:
        env_file = ".env"

settings = Settings()