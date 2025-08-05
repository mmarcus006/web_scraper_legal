"""Embedding manager for multiple HuggingFace models and BM25."""

import logging
from typing import List, Dict, Any, Optional, Union, Tuple
import numpy as np
from pathlib import Path
import torch
from tqdm import tqdm
import pickle

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("Warning: sentence-transformers not installed")

try:
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    from llama_index.embeddings.gemini import GeminiEmbedding
    LLAMAINDEX_AVAILABLE = True
except ImportError:
    LLAMAINDEX_AVAILABLE = False
    print("Warning: llama-index embeddings not installed")

from rank_bm25 import BM25Okapi
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

from .config import settings


class EmbeddingManager:
    """Manages multiple embedding models for dense and sparse retrieval."""
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        use_gpu: bool = True,
        cache_dir: Optional[Path] = None,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize embedding manager.
        
        Args:
            model_name: HuggingFace model name or path
            use_gpu: Use GPU if available
            cache_dir: Directory for caching models
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.model_name = model_name or settings.embedding_model
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.cache_dir = cache_dir or settings.vector_store_dir / "model_cache"
        
        # Device configuration
        self.device = "cuda" if self.use_gpu else "cpu"
        if self.use_gpu:
            self.logger.info(f"Using GPU for embeddings: {torch.cuda.get_device_name(0)}")
        else:
            self.logger.info("Using CPU for embeddings")
        
        # Initialize models
        self.dense_model = None
        self.gemini_model = None
        self.bm25_model = None
        
        # Download NLTK data if needed
        self._setup_nltk()
        
        # Initialize dense embedding model
        self._initialize_dense_model()
    
    def _setup_nltk(self):
        """Download required NLTK data."""
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            self.logger.info("Downloading NLTK punkt tokenizer...")
            nltk.download('punkt')
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            self.logger.info("Downloading NLTK stopwords...")
            nltk.download('stopwords')
    
    def _initialize_dense_model(self):
        """Initialize dense embedding model based on configuration."""
        self.logger.info(f"Initializing embedding model: {self.model_name}")
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            # Use sentence-transformers for better performance
            self.dense_model = SentenceTransformer(
                self.model_name,
                device=self.device,
                cache_folder=str(self.cache_dir)
            )
            
            # Set max sequence length based on model
            if "e5" in self.model_name.lower():
                self.dense_model.max_seq_length = 512
            elif "bge" in self.model_name.lower():
                self.dense_model.max_seq_length = 512
            elif "gte-qwen2" in self.model_name.lower():
                self.dense_model.max_seq_length = 8192  # Qwen2 supports longer context
            
        elif LLAMAINDEX_AVAILABLE:
            # Fallback to LlamaIndex embeddings
            self.dense_model = HuggingFaceEmbedding(
                model_name=self.model_name,
                cache_folder=str(self.cache_dir),
                device=self.device
            )
        else:
            raise ImportError("Neither sentence-transformers nor llama-index installed")
        
        self.logger.info(f"Dense model initialized: {self.model_name}")
    
    def initialize_gemini_embeddings(self, api_key: Optional[str] = None):
        """Initialize Gemini embeddings for comparison.
        
        Args:
            api_key: Google API key
        """
        if not LLAMAINDEX_AVAILABLE:
            raise ImportError("llama-index required for Gemini embeddings")
        
        api_key = api_key or settings.google_api_key
        if not api_key:
            raise ValueError("Google API key required for Gemini embeddings")
        
        self.gemini_model = GeminiEmbedding(
            api_key=api_key,
            model_name="models/embedding-001"
        )
        self.logger.info("Gemini embeddings initialized")
    
    def get_dense_embedding(
        self,
        text: Union[str, List[str]],
        normalize: bool = True,
        show_progress: bool = False
    ) -> Union[np.ndarray, List[np.ndarray]]:
        """Get dense embeddings for text.
        
        Args:
            text: Single text or list of texts
            normalize: Normalize embeddings to unit length
            show_progress: Show progress bar for batch processing
            
        Returns:
            Embedding vector(s)
        """
        if not self.dense_model:
            raise ValueError("Dense model not initialized")
        
        # Handle single text
        if isinstance(text, str):
            text = [text]
            single_input = True
        else:
            single_input = False
        
        # Add instruction prefix for E5 models
        if "e5" in self.model_name.lower():
            text = [f"query: {t}" for t in text]
        
        # Generate embeddings
        if SENTENCE_TRANSFORMERS_AVAILABLE and isinstance(self.dense_model, SentenceTransformer):
            embeddings = self.dense_model.encode(
                text,
                normalize_embeddings=normalize,
                show_progress_bar=show_progress,
                batch_size=32,
                convert_to_numpy=True
            )
        else:
            # LlamaIndex embedding
            embeddings = []
            iterator = tqdm(text, desc="Generating embeddings") if show_progress else text
            for t in iterator:
                emb = self.dense_model.get_text_embedding(t)
                embeddings.append(emb)
            embeddings = np.array(embeddings)
            
            if normalize:
                embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        
        return embeddings[0] if single_input else embeddings
    
    def get_gemini_embedding(
        self,
        text: Union[str, List[str]]
    ) -> Union[np.ndarray, List[np.ndarray]]:
        """Get Gemini embeddings for text.
        
        Args:
            text: Single text or list of texts
            
        Returns:
            Embedding vector(s)
        """
        if not self.gemini_model:
            raise ValueError("Gemini model not initialized")
        
        if isinstance(text, str):
            embedding = self.gemini_model.get_text_embedding(text)
            return np.array(embedding)
        else:
            embeddings = []
            for t in text:
                emb = self.gemini_model.get_text_embedding(t)
                embeddings.append(emb)
            return np.array(embeddings)
    
    def build_bm25_index(
        self,
        documents: List[str],
        save_path: Optional[Path] = None
    ) -> BM25Okapi:
        """Build BM25 index for sparse retrieval.
        
        Args:
            documents: List of document texts
            save_path: Optional path to save index
            
        Returns:
            BM25 model
        """
        self.logger.info(f"Building BM25 index for {len(documents)} documents")
        
        # Tokenize documents
        stop_words = set(stopwords.words('english'))
        tokenized_docs = []
        
        for doc in tqdm(documents, desc="Tokenizing documents"):
            tokens = word_tokenize(doc.lower())
            tokens = [t for t in tokens if t.isalnum() and t not in stop_words]
            tokenized_docs.append(tokens)
        
        # Build BM25 model
        self.bm25_model = BM25Okapi(tokenized_docs)
        
        # Save if requested
        if save_path:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'wb') as f:
                pickle.dump(self.bm25_model, f)
            self.logger.info(f"BM25 index saved to {save_path}")
        
        return self.bm25_model
    
    def load_bm25_index(self, load_path: Path) -> BM25Okapi:
        """Load BM25 index from file.
        
        Args:
            load_path: Path to saved index
            
        Returns:
            BM25 model
        """
        with open(load_path, 'rb') as f:
            self.bm25_model = pickle.load(f)
        self.logger.info(f"BM25 index loaded from {load_path}")
        return self.bm25_model
    
    def get_bm25_scores(
        self,
        query: str,
        top_k: Optional[int] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Get BM25 scores for query.
        
        Args:
            query: Query text
            top_k: Return only top k documents
            
        Returns:
            Tuple of (scores, indices)
        """
        if not self.bm25_model:
            raise ValueError("BM25 model not initialized")
        
        # Tokenize query
        stop_words = set(stopwords.words('english'))
        tokens = word_tokenize(query.lower())
        tokens = [t for t in tokens if t.isalnum() and t not in stop_words]
        
        # Get scores
        scores = self.bm25_model.get_scores(tokens)
        
        # Get top k if requested
        if top_k:
            top_indices = np.argsort(scores)[-top_k:][::-1]
            top_scores = scores[top_indices]
            return top_scores, top_indices
        else:
            return scores, np.arange(len(scores))
    
    def get_sparse_embedding(self, query: str) -> Dict[int, float]:
        """Convert query to sparse embedding for Milvus.
        
        Args:
            query: Query text
            
        Returns:
            Sparse embedding dictionary
        """
        # Tokenize query
        stop_words = set(stopwords.words('english'))
        tokens = word_tokenize(query.lower())
        tokens = [t for t in tokens if t.isalnum() and t not in stop_words]
        
        # Create sparse vector (simplified - can be enhanced with TF-IDF)
        sparse_vec = {}
        for token in tokens:
            # Use hash of token as dimension (simplified approach)
            dim = abs(hash(token)) % 100000  # Limit dimensions
            sparse_vec[dim] = sparse_vec.get(dim, 0) + 1
        
        # Normalize
        max_val = max(sparse_vec.values()) if sparse_vec else 1
        sparse_vec = {k: v/max_val for k, v in sparse_vec.items()}
        
        return sparse_vec
    
    def batch_embed_documents(
        self,
        documents: List[Dict[str, Any]],
        text_field: str = "text",
        batch_size: int = 32
    ) -> List[Dict[str, Any]]:
        """Batch embed documents with dense and sparse embeddings.
        
        Args:
            documents: List of document dictionaries
            text_field: Field name containing text
            batch_size: Batch size for processing
            
        Returns:
            Documents with added embeddings
        """
        self.logger.info(f"Embedding {len(documents)} documents")
        
        # Extract texts
        texts = [doc[text_field] for doc in documents]
        
        # Generate dense embeddings
        dense_embeddings = self.get_dense_embedding(texts, show_progress=True)
        
        # Generate sparse embeddings
        sparse_embeddings = []
        for text in tqdm(texts, desc="Generating sparse embeddings"):
            sparse_emb = self.get_sparse_embedding(text)
            sparse_embeddings.append(sparse_emb)
        
        # Add embeddings to documents
        for i, doc in enumerate(documents):
            doc["embedding"] = dense_embeddings[i].tolist()
            doc["sparse_embedding"] = sparse_embeddings[i]
        
        return documents
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models.
        
        Returns:
            Model information dictionary
        """
        info = {
            "dense_model": self.model_name,
            "dimension": settings.get_embedding_dimension(),
            "device": self.device,
            "has_gemini": self.gemini_model is not None,
            "has_bm25": self.bm25_model is not None,
        }
        
        if self.use_gpu:
            info["gpu_name"] = torch.cuda.get_device_name(0)
            info["gpu_memory"] = f"{torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB"
        
        return info