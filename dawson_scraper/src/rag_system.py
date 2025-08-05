"""RAG system for US Tax Court documents using LlamaIndex."""

import os
import json
import logging
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

# Set environment variables before imports
os.environ["TOKENIZERS_PARALLELISM"] = "false"

try:
    from llama_index.core import (
        VectorStoreIndex,
        SimpleDirectoryReader,
        Document,
        StorageContext,
        Settings,
        ServiceContext
    )
    from llama_index.core.node_parser import MarkdownNodeParser
    from llama_index.core.retrievers import VectorIndexRetriever
    from llama_index.core.query_engine import RetrieverQueryEngine
    from llama_index.core.postprocessor import SimilarityPostprocessor
    from llama_index.core.response_synthesizers import get_response_synthesizer
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    from llama_index.core.storage.docstore import SimpleDocumentStore
    from llama_index.core.storage.index_store import SimpleIndexStore
    from llama_index.core.vector_stores import SimpleVectorStore
    
    LLAMAINDEX_AVAILABLE = True
except ImportError:
    LLAMAINDEX_AVAILABLE = False
    print("Warning: LlamaIndex not installed. Install with: pip install llama-index llama-index-embeddings-huggingface")

from .pdf_pipeline import setup_logging


class TaxCourtRAGSystem:
    """RAG system for searching US Tax Court documents."""
    
    def __init__(
        self,
        markdown_dir: str = "data/markdown_documents",
        vector_store_dir: str = "data/vector_store",
        embedding_model: str = "BAAI/bge-base-en-v1.5",
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        similarity_top_k: int = 5,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize RAG system.
        
        Args:
            markdown_dir: Directory containing markdown documents
            vector_store_dir: Directory for vector store persistence
            embedding_model: HuggingFace embedding model name
            chunk_size: Size of text chunks for indexing
            chunk_overlap: Overlap between chunks
            similarity_top_k: Number of similar documents to retrieve
            logger: Logger instance
        """
        if not LLAMAINDEX_AVAILABLE:
            raise ImportError("LlamaIndex is required. Install with: pip install llama-index")
        
        self.markdown_dir = Path(markdown_dir)
        self.vector_store_dir = Path(vector_store_dir)
        self.embedding_model_name = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.similarity_top_k = similarity_top_k
        
        self.logger = logger or setup_logging("INFO")
        self.index = None
        self.query_engine = None
        
        # Create directories
        self.vector_store_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize embedding model
        self._setup_embedding_model()
    
    def _setup_embedding_model(self):
        """Setup HuggingFace embedding model."""
        self.logger.info(f"Setting up embedding model: {self.embedding_model_name}")
        
        # Create embedding model
        self.embed_model = HuggingFaceEmbedding(
            model_name=self.embedding_model_name,
            cache_folder=str(self.vector_store_dir / "model_cache")
        )
        
        # Configure global settings
        Settings.embed_model = self.embed_model
        Settings.chunk_size = self.chunk_size
        Settings.chunk_overlap = self.chunk_overlap
    
    def _extract_metadata_from_path(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from file path and content.
        
        Args:
            file_path: Path to markdown file
        
        Returns:
            Metadata dictionary
        """
        metadata = {
            "source_file": str(file_path),
            "file_name": file_path.name
        }
        
        # Extract date from directory name (e.g., 2020-01)
        parent_dir = file_path.parent.name
        if re.match(r"\d{4}-\d{2}", parent_dir):
            year, month = parent_dir.split("-")
            metadata["year"] = int(year)
            metadata["month"] = int(month)
            metadata["filing_period"] = parent_dir
        
        # Extract docket number from filename
        docket_match = re.match(r"(\d+-\d+)", file_path.stem)
        if docket_match:
            metadata["docket_number"] = docket_match.group(1)
        
        # Check for metadata JSON file
        metadata_file = file_path.with_suffix('.json')
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    json_metadata = json.load(f)
                    metadata.update(json_metadata)
            except Exception as e:
                self.logger.warning(f"Failed to load metadata from {metadata_file}: {e}")
        
        return metadata
    
    def load_documents(self, pattern: str = "**/*.md") -> List[Document]:
        """Load markdown documents from directory.
        
        Args:
            pattern: Glob pattern for finding markdown files
        
        Returns:
            List of Document objects
        """
        self.logger.info(f"Loading documents from {self.markdown_dir}")
        
        documents = []
        markdown_files = list(self.markdown_dir.glob(pattern))
        
        if not markdown_files:
            self.logger.warning(f"No markdown files found in {self.markdown_dir}")
            return documents
        
        self.logger.info(f"Found {len(markdown_files)} markdown files")
        
        for md_file in markdown_files:
            try:
                # Read markdown content
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract metadata
                metadata = self._extract_metadata_from_path(md_file)
                
                # Create document
                doc = Document(
                    text=content,
                    metadata=metadata
                )
                documents.append(doc)
                
            except Exception as e:
                self.logger.error(f"Failed to load {md_file}: {e}")
        
        self.logger.info(f"Loaded {len(documents)} documents")
        return documents
    
    def build_index(
        self,
        documents: Optional[List[Document]] = None,
        persist: bool = True,
        incremental: bool = False
    ) -> VectorStoreIndex:
        """Build or update vector index.
        
        Args:
            documents: List of documents (loads from directory if None)
            persist: Save index to disk
            incremental: Add to existing index instead of rebuilding
        
        Returns:
            VectorStoreIndex instance
        """
        # Check for existing index if incremental
        if incremental and self._index_exists():
            self.logger.info("Loading existing index for incremental update")
            self.load_index()
            
            if documents is None:
                documents = self.load_documents()
            
            # Add new documents to existing index
            for doc in documents:
                self.index.insert(doc)
            
            if persist:
                self.save_index()
            
            return self.index
        
        # Load documents if not provided
        if documents is None:
            documents = self.load_documents()
        
        if not documents:
            raise ValueError("No documents to index")
        
        self.logger.info(f"Building index with {len(documents)} documents")
        
        # Create node parser for markdown
        node_parser = MarkdownNodeParser.from_defaults(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        
        # Create index
        self.index = VectorStoreIndex.from_documents(
            documents,
            transformations=[node_parser],
            show_progress=True
        )
        
        self.logger.info("Index built successfully")
        
        # Save index if requested
        if persist:
            self.save_index()
        
        return self.index
    
    def _index_exists(self) -> bool:
        """Check if saved index exists.
        
        Returns:
            True if index exists on disk
        """
        index_file = self.vector_store_dir / "docstore.json"
        return index_file.exists()
    
    def save_index(self):
        """Save index to disk."""
        if self.index is None:
            raise ValueError("No index to save")
        
        self.logger.info(f"Saving index to {self.vector_store_dir}")
        self.index.storage_context.persist(persist_dir=str(self.vector_store_dir))
        self.logger.info("Index saved successfully")
    
    def load_index(self):
        """Load index from disk."""
        if not self._index_exists():
            raise ValueError(f"No index found at {self.vector_store_dir}")
        
        self.logger.info(f"Loading index from {self.vector_store_dir}")
        
        # Create storage context
        storage_context = StorageContext.from_defaults(
            persist_dir=str(self.vector_store_dir)
        )
        
        # Load index
        self.index = VectorStoreIndex.from_storage_context(storage_context)
        self.logger.info("Index loaded successfully")
    
    def create_query_engine(
        self,
        similarity_top_k: Optional[int] = None,
        similarity_cutoff: float = 0.7,
        response_mode: str = "compact"
    ) -> RetrieverQueryEngine:
        """Create query engine for searching.
        
        Args:
            similarity_top_k: Number of similar documents to retrieve
            similarity_cutoff: Minimum similarity score
            response_mode: Response synthesis mode
        
        Returns:
            Query engine instance
        """
        if self.index is None:
            raise ValueError("Index not built. Call build_index() first")
        
        if similarity_top_k is None:
            similarity_top_k = self.similarity_top_k
        
        # Create retriever
        retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=similarity_top_k
        )
        
        # Create response synthesizer
        response_synthesizer = get_response_synthesizer(
            response_mode=response_mode
        )
        
        # Create query engine
        self.query_engine = RetrieverQueryEngine(
            retriever=retriever,
            response_synthesizer=response_synthesizer,
            node_postprocessors=[
                SimilarityPostprocessor(similarity_cutoff=similarity_cutoff)
            ]
        )
        
        return self.query_engine
    
    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Search for relevant documents.
        
        Args:
            query: Search query
            top_k: Number of results to return
            filters: Metadata filters (e.g., {"year": 2023})
        
        Returns:
            Search results with documents and metadata
        """
        if self.index is None:
            # Try to load existing index
            if self._index_exists():
                self.load_index()
            else:
                raise ValueError("No index available. Build index first")
        
        if self.query_engine is None:
            self.create_query_engine(similarity_top_k=top_k)
        
        self.logger.info(f"Searching for: {query}")
        
        # Apply filters if provided
        if filters:
            # Create metadata filter string
            filter_str = " AND ".join([f"{k}={v}" for k, v in filters.items()])
            query = f"{query} [FILTER: {filter_str}]"
        
        # Perform search
        response = self.query_engine.query(query)
        
        # Extract results
        results = {
            "query": query,
            "response": str(response),
            "source_nodes": []
        }
        
        # Extract source information
        if hasattr(response, 'source_nodes'):
            for node in response.source_nodes:
                node_info = {
                    "text": node.node.text[:500],  # First 500 chars
                    "score": node.score,
                    "metadata": node.node.metadata
                }
                results["source_nodes"].append(node_info)
        
        self.logger.info(f"Found {len(results['source_nodes'])} relevant documents")
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get index statistics.
        
        Returns:
            Statistics dictionary
        """
        stats = {
            "index_exists": self._index_exists(),
            "markdown_dir": str(self.markdown_dir),
            "vector_store_dir": str(self.vector_store_dir),
            "embedding_model": self.embedding_model_name
        }
        
        # Count markdown files
        markdown_files = list(self.markdown_dir.glob("**/*.md"))
        stats["total_markdown_files"] = len(markdown_files)
        
        # Get index stats if available
        if self.index is not None:
            stats["index_loaded"] = True
            stats["total_chunks"] = len(self.index.docstore.docs)
        else:
            stats["index_loaded"] = False
        
        # Get file size statistics
        if markdown_files:
            total_size = sum(f.stat().st_size for f in markdown_files)
            stats["total_size_mb"] = total_size / (1024 * 1024)
            
            # Group by year-month
            periods = {}
            for f in markdown_files:
                parent = f.parent.name
                if re.match(r"\d{4}-\d{2}", parent):
                    periods[parent] = periods.get(parent, 0) + 1
            stats["documents_by_period"] = periods
        
        return stats


# Example usage and testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="US Tax Court RAG System")
    parser.add_argument("--markdown-dir", default="data/markdown_documents", help="Markdown directory")
    parser.add_argument("--build", action="store_true", help="Build index")
    parser.add_argument("--search", help="Search query")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results")
    
    args = parser.parse_args()
    
    # Initialize RAG system
    rag = TaxCourtRAGSystem(markdown_dir=args.markdown_dir)
    
    if args.build:
        print("Building index...")
        rag.build_index(persist=True)
        print("Index built successfully")
    
    if args.search:
        results = rag.search(args.search, top_k=args.top_k)
        print(f"\nSearch Query: {results['query']}")
        print(f"\nResponse: {results['response']}")
        print(f"\nSources ({len(results['source_nodes'])} documents):")
        for i, node in enumerate(results['source_nodes'], 1):
            print(f"\n{i}. Score: {node['score']:.3f}")
            print(f"   File: {node['metadata'].get('source_file', 'Unknown')}")
            print(f"   Text: {node['text'][:200]}...")
    
    if args.stats:
        stats = rag.get_statistics()
        print(json.dumps(stats, indent=2))