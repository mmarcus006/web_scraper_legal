"""Configuration management for Legal RAG System."""

import os
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load environment variables from root directory
root_dir = Path(__file__).parent.parent.parent
env_file = root_dir / ".env"
load_dotenv(env_file)


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_file=str(env_file),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Google Gemini Configuration
    google_api_key: Optional[str] = Field(default=None, alias="GOOGLE_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")
    
    # Milvus Configuration
    milvus_host: str = Field(default="localhost", alias="MILVUS_HOST")
    milvus_port: int = Field(default=19530, alias="MILVUS_PORT")
    milvus_user: str = Field(default="root", alias="MILVUS_USER")
    milvus_password: str = Field(default="Milvus", alias="MILVUS_PASSWORD")
    milvus_collection: str = Field(default="tax_court_documents", alias="MILVUS_COLLECTION")
    
    # Embedding Model Configuration
    embedding_model: str = Field(
        default="intfloat/e5-large-v2",
        alias="EMBEDDING_MODEL",
        description="HuggingFace embedding model name"
    )
    
    # Processing Configuration
    batch_size: int = Field(default=100, alias="BATCH_SIZE")
    max_workers: int = Field(default=8, alias="MAX_WORKERS")
    chunk_size: int = Field(default=512, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=50, alias="CHUNK_OVERLAP")
    similarity_top_k: int = Field(default=10, alias="SIMILARITY_TOP_K")
    
    # Docling Configuration
    enable_ocr: bool = Field(default=True, alias="ENABLE_OCR")
    enable_tables: bool = Field(default=True, alias="ENABLE_TABLES")
    enable_formulas: bool = Field(default=True, alias="ENABLE_FORMULAS")
    enable_vlm: bool = Field(default=True, alias="ENABLE_VLM")
    
    # Paths
    data_dir: Path = Field(default=Path("./data"), alias="DATA_DIR")
    documents_dir: Path = Field(default=Path("./data/documents"), alias="DOCUMENTS_DIR")
    processed_dir: Path = Field(default=Path("./data/processed"), alias="PROCESSED_DIR")
    vector_store_dir: Path = Field(default=Path("./data/vector_store"), alias="VECTOR_STORE_DIR")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.documents_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.vector_store_dir.mkdir(parents=True, exist_ok=True)
    
    @property
    def milvus_uri(self) -> str:
        """Get Milvus connection URI."""
        return f"http://{self.milvus_host}:{self.milvus_port}"
    
    @property
    def has_gemini_key(self) -> bool:
        """Check if Gemini API key is configured."""
        return bool(self.google_api_key)
    
    def get_embedding_dimension(self) -> int:
        """Get embedding dimension based on model."""
        model_dimensions = {
            "Alibaba-NLP/gte-Qwen2-7B-instruct": 7680,
            "intfloat/e5-large-v2": 1024,
            "BAAI/bge-large-en-v1.5": 1024,
            "sentence-transformers/all-MiniLM-L6-v2": 384,
        }
        return model_dimensions.get(self.embedding_model, 768)


# Global settings instance
settings = Settings()