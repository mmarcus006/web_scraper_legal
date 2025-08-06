"""Legal RAG System - Advanced document retrieval and generation for US Tax Court documents."""

from .advanced_rag_system import AdvancedRAGSystem
from .milvus_manager import MilvusManager
from .docling_processor import DoclingProcessor
from .embedding_manager import EmbeddingManager
from .config import settings

__all__ = [
    'AdvancedRAGSystem',
    'MilvusManager',
    'DoclingProcessor',
    'EmbeddingManager',
    'settings'
]

__version__ = "1.0.0"