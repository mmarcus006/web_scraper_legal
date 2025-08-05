"""Advanced RAG system using Docling, Milvus, and Gemini with LlamaIndex."""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import json
import os
from tqdm import tqdm

# LlamaIndex imports
try:
    from llama_index.core import (
        VectorStoreIndex,
        StorageContext,
        Settings,
        Document,
        ServiceContext
    )
    from llama_index.core.node_parser import SimpleNodeParser
    from llama_index.core.retrievers import VectorIndexRetriever
    from llama_index.core.query_engine import RetrieverQueryEngine
    from llama_index.core.response_synthesizers import get_response_synthesizer
    from llama_index.vector_stores.milvus import MilvusVectorStore
    from llama_index.llms.gemini import Gemini
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    LLAMAINDEX_AVAILABLE = True
except ImportError:
    LLAMAINDEX_AVAILABLE = False
    print("Warning: LlamaIndex not fully installed")

from .config import settings
from .milvus_manager import MilvusManager
from .docling_processor import DoclingProcessor
from .embedding_manager import EmbeddingManager


class AdvancedRAGSystem:
    """Advanced RAG system orchestrating all components."""
    
    def __init__(
        self,
        use_milvus_lite: bool = False,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize RAG system.
        
        Args:
            use_milvus_lite: Use embedded Milvus for development
            logger: Optional logger instance
        """
        if not LLAMAINDEX_AVAILABLE:
            raise ImportError("LlamaIndex required for RAG system")
        
        self.logger = logger or logging.getLogger(__name__)
        self.use_milvus_lite = use_milvus_lite
        
        # Initialize components
        self.milvus_manager = MilvusManager(logger=self.logger)
        self.docling_processor = DoclingProcessor(logger=self.logger)
        self.embedding_manager = EmbeddingManager(logger=self.logger)
        
        # LlamaIndex components
        self.index = None
        self.query_engine = None
        self.llm = None
        
        # Initialize LLM if API key available
        if settings.has_gemini_key:
            self._initialize_llm()
        else:
            self.logger.warning("No Gemini API key found. Using mock LLM.")
            Settings.llm = None
        
        # Configure embeddings
        self._configure_embeddings()
    
    def _initialize_llm(self):
        """Initialize Gemini LLM."""
        try:
            self.llm = Gemini(
                model=settings.gemini_model,
                api_key=settings.google_api_key,
                temperature=0.7,
                max_tokens=2048
            )
            Settings.llm = self.llm
            self.logger.info(f"Initialized Gemini LLM: {settings.gemini_model}")
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini: {e}")
            Settings.llm = None
    
    def _configure_embeddings(self):
        """Configure embedding model for LlamaIndex."""
        embed_model = HuggingFaceEmbedding(
            model_name=settings.embedding_model,
            cache_folder=str(settings.vector_store_dir / "model_cache"),
            embed_batch_size=32
        )
        Settings.embed_model = embed_model
        Settings.chunk_size = settings.chunk_size
        Settings.chunk_overlap = settings.chunk_overlap
        self.logger.info(f"Configured embeddings: {settings.embedding_model}")
    
    def process_documents(
        self,
        input_dir: Path,
        pattern: str = "*.pdf",
        skip_existing: bool = True
    ) -> Dict[str, Any]:
        """Process PDF documents with Docling.
        
        Args:
            input_dir: Directory containing PDFs
            pattern: File pattern to match
            skip_existing: Skip already processed files
            
        Returns:
            Processing statistics
        """
        input_dir = Path(input_dir)
        processed_dir = settings.processed_dir
        
        self.logger.info(f"Processing documents from {input_dir}")
        
        # Process PDFs to markdown
        stats = self.docling_processor.process_directory(
            input_dir=input_dir,
            output_dir=processed_dir,
            output_format="markdown",
            skip_existing=skip_existing,
            pattern=pattern
        )
        
        # Also save as JSON for metadata
        json_stats = self.docling_processor.process_directory(
            input_dir=input_dir,
            output_dir=processed_dir / "json",
            output_format="json",
            skip_existing=skip_existing,
            pattern=pattern
        )
        
        stats["json_processed"] = json_stats["processed"]
        
        return stats
    
    def build_index(
        self,
        documents_dir: Optional[Path] = None,
        recreate_collection: bool = False
    ) -> VectorStoreIndex:
        """Build vector index from processed documents.
        
        Args:
            documents_dir: Directory with processed documents
            recreate_collection: Recreate Milvus collection
            
        Returns:
            VectorStoreIndex instance
        """
        documents_dir = documents_dir or settings.processed_dir
        
        # Connect to Milvus
        self.milvus_manager.connect(use_lite=self.use_milvus_lite)
        
        # Create/get collection
        self.milvus_manager.create_collection(recreate=recreate_collection)
        
        # Load documents
        documents = self._load_documents(documents_dir)
        
        if not documents:
            raise ValueError("No documents found to index")
        
        self.logger.info(f"Loaded {len(documents)} documents")
        
        # Create chunks
        all_chunks = []
        for doc in tqdm(documents, desc="Creating chunks"):
            chunks = self.docling_processor.extract_chunks(
                content=doc["content"],
                metadata=doc["metadata"],
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap
            )
            
            # Add doc_id to chunks
            for chunk in chunks:
                chunk["doc_id"] = doc["metadata"].get("source_file", "unknown")
            
            all_chunks.extend(chunks)
        
        self.logger.info(f"Created {len(all_chunks)} chunks")
        
        # Add embeddings
        all_chunks = self.embedding_manager.batch_embed_documents(
            all_chunks,
            text_field="text"
        )
        
        # Insert into Milvus
        self.milvus_manager.insert_documents(all_chunks, batch_size=settings.batch_size)
        
        # Create LlamaIndex vector store
        vector_store = MilvusVectorStore(
            uri=settings.milvus_uri if not self.use_milvus_lite else str(settings.vector_store_dir / "milvus.db"),
            collection_name=settings.milvus_collection,
            dim=settings.get_embedding_dimension(),
            overwrite=False
        )
        
        # Create storage context
        storage_context = StorageContext.from_defaults(
            vector_store=vector_store
        )
        
        # Create index from documents
        llama_documents = [
            Document(
                text=chunk["text"],
                metadata={k: v for k, v in chunk.items() if k not in ["text", "embedding", "sparse_embedding"]}
            )
            for chunk in all_chunks
        ]
        
        self.index = VectorStoreIndex.from_documents(
            llama_documents,
            storage_context=storage_context,
            show_progress=True
        )
        
        self.logger.info("Index built successfully")
        
        return self.index
    
    def _load_documents(self, documents_dir: Path) -> List[Dict[str, Any]]:
        """Load processed documents from directory.
        
        Args:
            documents_dir: Directory with processed documents
            
        Returns:
            List of document dictionaries
        """
        documents = []
        
        # Load markdown files
        md_files = list(documents_dir.rglob("*.md"))
        json_dir = documents_dir / "json"
        
        for md_file in md_files:
            try:
                # Load content
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Try to load corresponding JSON for metadata
                json_file = json_dir / md_file.relative_to(documents_dir).with_suffix('.json')
                
                if json_file.exists():
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        metadata = data.get("metadata", {})
                else:
                    # Basic metadata from file path
                    metadata = {
                        "source_file": str(md_file),
                        "file_name": md_file.name
                    }
                
                documents.append({
                    "content": content,
                    "metadata": metadata
                })
                
            except Exception as e:
                self.logger.error(f"Failed to load {md_file}: {e}")
        
        return documents
    
    def create_query_engine(
        self,
        similarity_top_k: Optional[int] = None,
        response_mode: str = "tree_summarize",
        streaming: bool = False
    ) -> RetrieverQueryEngine:
        """Create query engine for searching.
        
        Args:
            similarity_top_k: Number of similar documents to retrieve
            response_mode: Response synthesis mode
            streaming: Enable streaming responses
            
        Returns:
            Query engine instance
        """
        if not self.index:
            raise ValueError("Index not built. Call build_index() first")
        
        similarity_top_k = similarity_top_k or settings.similarity_top_k
        
        # Create retriever
        retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=similarity_top_k
        )
        
        # Create response synthesizer
        response_synthesizer = get_response_synthesizer(
            response_mode=response_mode,
            streaming=streaming
        )
        
        # Create query engine
        self.query_engine = RetrieverQueryEngine(
            retriever=retriever,
            response_synthesizer=response_synthesizer
        )
        
        return self.query_engine
    
    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        use_hybrid: bool = True
    ) -> Dict[str, Any]:
        """Search for relevant documents.
        
        Args:
            query: Search query
            top_k: Number of results to return
            filters: Metadata filters
            use_hybrid: Use hybrid search (dense + sparse)
            
        Returns:
            Search results with documents and response
        """
        top_k = top_k or settings.similarity_top_k
        
        # Build filter expression for Milvus
        filter_expr = None
        if filters:
            conditions = []
            for key, value in filters.items():
                if isinstance(value, str):
                    conditions.append(f'{key} == "{value}"')
                else:
                    conditions.append(f'{key} == {value}')
            filter_expr = " && ".join(conditions)
        
        # Get query embedding
        query_embedding = self.embedding_manager.get_dense_embedding(query)
        
        if use_hybrid:
            # Get sparse embedding
            sparse_embedding = self.embedding_manager.get_sparse_embedding(query)
            
            # Perform hybrid search
            results = self.milvus_manager.hybrid_search(
                dense_embedding=query_embedding,
                sparse_embedding=sparse_embedding,
                top_k=top_k,
                filters=filter_expr
            )
        else:
            # Dense search only
            results = self.milvus_manager.search(
                query_embedding=query_embedding,
                top_k=top_k,
                filters=filter_expr
            )
        
        # Generate response if LLM available
        response_text = None
        if self.query_engine and self.llm:
            try:
                response = self.query_engine.query(query)
                response_text = str(response)
            except Exception as e:
                self.logger.error(f"Failed to generate response: {e}")
                response_text = "Error generating response"
        
        # Format results
        formatted_results = {
            "query": query,
            "filters": filters,
            "num_results": len(results),
            "response": response_text,
            "documents": results
        }
        
        return formatted_results
    
    def chat(
        self,
        message: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        top_k: int = 5
    ) -> str:
        """Chat interface with context awareness.
        
        Args:
            message: User message
            chat_history: Previous chat history
            top_k: Number of documents to retrieve
            
        Returns:
            Assistant response
        """
        if not self.llm:
            return "Chat requires Gemini API key to be configured"
        
        # Search for relevant context
        search_results = self.search(message, top_k=top_k, use_hybrid=True)
        
        # Build context from search results
        context_docs = search_results.get("documents", [])
        context = "\n\n".join([
            f"Document {i+1}:\n{doc.get('text', '')}"
            for i, doc in enumerate(context_docs[:3])
        ])
        
        # Build prompt with context
        prompt = f"""You are a helpful assistant for US Tax Court document analysis.
        
Context from relevant documents:
{context}

User message: {message}

Please provide a helpful and accurate response based on the context provided."""
        
        # Generate response
        try:
            response = self.llm.complete(prompt)
            return str(response)
        except Exception as e:
            self.logger.error(f"Chat error: {e}")
            return f"Error generating response: {e}"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics.
        
        Returns:
            Statistics dictionary
        """
        stats = {
            "milvus": self.milvus_manager.get_collection_stats() if self.milvus_manager.collection else {},
            "embeddings": self.embedding_manager.get_model_info(),
            "llm": {
                "configured": self.llm is not None,
                "model": settings.gemini_model if self.llm else None
            },
            "settings": {
                "chunk_size": settings.chunk_size,
                "chunk_overlap": settings.chunk_overlap,
                "similarity_top_k": settings.similarity_top_k
            }
        }
        
        return stats