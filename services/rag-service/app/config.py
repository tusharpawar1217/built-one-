"""Configuration management using pydantic-settings."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""
    
    # API Settings
    app_name: str = "Sarkari AI RAG Service"
    api_version: str = "v1"
    debug: bool = False
    
    # Gemini API
    google_api_key: str
    gemini_model: str = "gemini-1.5-flash-8b"
    gemini_model_pro: str = "gemini-1.5-pro"
    gemini_temperature: float = 0.1
    gemini_max_tokens: int = 2048
    
    # Database
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "sarkari_ai"
    postgres_user: str = "sarkari_user"
    postgres_password: str
    
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0
    
    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: str = ""
    
    @property
    def qdrant_url(self) -> str:
        return f"http://{self.qdrant_host}:{self.qdrant_port}"
    
    # S3 Storage
    s3_endpoint: str
    s3_access_key: str
    s3_secret_key: str
    s3_bucket_name: str = "sarkari-ai-pdfs"
    s3_region: str = "us-west-002"
    
    # ML Models
    embedding_model: str = "BAAI/bge-m3"
    reranker_model: str = "BAAI/bge-reranker-base"
    embedding_dimension: int = 1024
    
    # OCR
    ocr_languages: str = "eng+hin+mar"
    enable_ocr: bool = True
    ocr_min_confidence: float = 0.3  # Minimum OCR confidence threshold
    
    # Chunking
    chunk_size: int = 800
    chunk_overlap: int = 120  # 15% overlap
    
    # Retrieval
    top_k_retrieval: int = 20
    top_k_rerank: int = 5
    enable_reranker: bool = True
    
    # Rate Limiting
    free_tier_queries_per_day: int = 3
    free_tier_pages_per_month: int = 50
    premium_tier_queries_per_day: int = 999999
    premium_tier_pages_per_month: int = 999999
    
    # File Upload
    max_upload_size_mb: int = 100
    allowed_extensions: list[str] = [".pdf"]
    upload_dir: str = "/app/uploads"
    temp_dir: str = "/app/temp"
    
    # Feature Flags
    enable_quiz_generation: bool = False
    enable_eligibility_extraction: bool = False
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
