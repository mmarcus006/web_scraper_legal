"""Milvus vector database manager for Legal RAG System."""

import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np
from pymilvus import (
    connections,
    utility,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    MilvusClient
)
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import settings


class MilvusManager:
    """Manages Milvus vector database operations."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize Milvus manager.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.collection_name = settings.milvus_collection
        self.dimension = settings.get_embedding_dimension()
        self.client = None
        self.collection = None
        
        # Connection parameters
        self.host = settings.milvus_host
        self.port = settings.milvus_port
        self.uri = settings.milvus_uri
        
    def connect(self, use_lite: bool = False) -> None:
        """Connect to Milvus server.
        
        Args:
            use_lite: Use Milvus Lite for local development
        """
        try:
            if use_lite:
                # Use Milvus Lite (embedded)
                self.client = MilvusClient(
                    uri=str(settings.vector_store_dir / "milvus.db")
                )
                self.logger.info(f"Connected to Milvus Lite at {settings.vector_store_dir}")
            else:
                # Connect to Milvus server
                connections.connect(
                    alias="default",
                    host=self.host,
                    port=self.port,
                    user=settings.milvus_user,
                    password=settings.milvus_password
                )
                self.logger.info(f"Connected to Milvus server at {self.host}:{self.port}")
                
        except Exception as e:
            self.logger.error(f"Failed to connect to Milvus: {e}")
            raise
    
    def create_collection(self, recreate: bool = False) -> Collection:
        """Create or get collection with optimized schema.
        
        Args:
            recreate: Drop and recreate collection if exists
            
        Returns:
            Collection instance
        """
        # Check if collection exists
        if utility.has_collection(self.collection_name):
            if recreate:
                self.logger.info(f"Dropping existing collection: {self.collection_name}")
                utility.drop_collection(self.collection_name)
            else:
                self.logger.info(f"Using existing collection: {self.collection_name}")
                self.collection = Collection(self.collection_name)
                return self.collection
        
        # Define schema
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="doc_id", dtype=DataType.VARCHAR, max_length=256),
            FieldSchema(name="chunk_id", dtype=DataType.INT64),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dimension),
            
            # Metadata fields
            FieldSchema(name="docket_number", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="case_title", dtype=DataType.VARCHAR, max_length=500),
            FieldSchema(name="judge", dtype=DataType.VARCHAR, max_length=200),
            FieldSchema(name="year", dtype=DataType.INT64),
            FieldSchema(name="month", dtype=DataType.INT64),
            FieldSchema(name="filing_date", dtype=DataType.VARCHAR, max_length=20),
            FieldSchema(name="document_type", dtype=DataType.VARCHAR, max_length=50),
            FieldSchema(name="source_file", dtype=DataType.VARCHAR, max_length=500),
            
            # BM25 sparse embedding for hybrid search
            FieldSchema(name="sparse_embedding", dtype=DataType.SPARSE_FLOAT_VECTOR),
        ]
        
        schema = CollectionSchema(
            fields=fields,
            description="US Tax Court documents for RAG system",
            enable_dynamic_field=True
        )
        
        # Create collection
        self.collection = Collection(
            name=self.collection_name,
            schema=schema,
            consistency_level="Session"
        )
        
        self.logger.info(f"Created collection: {self.collection_name}")
        
        # Create indexes for better search performance
        self._create_indexes()
        
        return self.collection
    
    def _create_indexes(self) -> None:
        """Create optimized indexes for the collection."""
        # Dense vector index (for semantic search)
        dense_index_params = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }
        
        self.collection.create_index(
            field_name="embedding",
            index_params=dense_index_params
        )
        
        # Sparse vector index (for keyword search)
        sparse_index_params = {
            "metric_type": "IP",
            "index_type": "SPARSE_INVERTED_INDEX"
        }
        
        self.collection.create_index(
            field_name="sparse_embedding",
            index_params=sparse_index_params
        )
        
        self.logger.info("Created indexes for collection")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def insert_documents(
        self,
        documents: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> List[int]:
        """Insert documents into collection.
        
        Args:
            documents: List of document dictionaries with embeddings
            batch_size: Batch size for insertion
            
        Returns:
            List of inserted IDs
        """
        if not self.collection:
            raise ValueError("Collection not initialized")
        
        # Load collection
        self.collection.load()
        
        inserted_ids = []
        total_docs = len(documents)
        
        for i in range(0, total_docs, batch_size):
            batch = documents[i:i+batch_size]
            
            # Prepare data for insertion
            data = {
                "doc_id": [doc["doc_id"] for doc in batch],
                "chunk_id": [doc["chunk_id"] for doc in batch],
                "text": [doc["text"][:65535] for doc in batch],  # Truncate if needed
                "embedding": [doc["embedding"] for doc in batch],
                "docket_number": [doc.get("docket_number", "") for doc in batch],
                "case_title": [doc.get("case_title", "") for doc in batch],
                "judge": [doc.get("judge", "") for doc in batch],
                "year": [doc.get("year", 0) for doc in batch],
                "month": [doc.get("month", 0) for doc in batch],
                "filing_date": [doc.get("filing_date", "") for doc in batch],
                "document_type": [doc.get("document_type", "") for doc in batch],
                "source_file": [doc.get("source_file", "") for doc in batch],
                "sparse_embedding": [doc.get("sparse_embedding", {}) for doc in batch],
            }
            
            # Insert batch
            result = self.collection.insert(data)
            inserted_ids.extend(result.primary_keys)
            
            self.logger.info(f"Inserted batch {i//batch_size + 1}/{(total_docs + batch_size - 1)//batch_size}")
        
        # Flush to ensure data is persisted
        self.collection.flush()
        
        self.logger.info(f"Successfully inserted {len(inserted_ids)} documents")
        return inserted_ids
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        filters: Optional[str] = None,
        output_fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar documents.
        
        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            filters: Filter expression (e.g., "year == 2024")
            output_fields: Fields to return in results
            
        Returns:
            List of search results
        """
        if not self.collection:
            raise ValueError("Collection not initialized")
        
        # Default output fields
        if output_fields is None:
            output_fields = [
                "doc_id", "chunk_id", "text", "docket_number",
                "case_title", "judge", "year", "month", "source_file"
            ]
        
        # Load collection if not loaded
        self.collection.load()
        
        # Search parameters
        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10}
        }
        
        # Perform search
        results = self.collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=filters,
            output_fields=output_fields
        )
        
        # Format results
        formatted_results = []
        for hits in results:
            for hit in hits:
                result = {
                    "score": hit.score,
                    "id": hit.id,
                }
                # Add output fields
                for field in output_fields:
                    if hasattr(hit.entity, field):
                        result[field] = getattr(hit.entity, field)
                formatted_results.append(result)
        
        return formatted_results
    
    def hybrid_search(
        self,
        dense_embedding: np.ndarray,
        sparse_embedding: Dict[int, float],
        top_k: int = 10,
        alpha: float = 0.7,
        filters: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search combining dense and sparse embeddings.
        
        Args:
            dense_embedding: Dense query vector
            sparse_embedding: Sparse query vector (BM25)
            top_k: Number of results to return
            alpha: Weight for dense search (1-alpha for sparse)
            filters: Filter expression
            
        Returns:
            List of search results
        """
        # Perform dense search
        dense_results = self.search(
            query_embedding=dense_embedding,
            top_k=top_k * 2,  # Get more for reranking
            filters=filters
        )
        
        # Perform sparse search
        sparse_params = {
            "metric_type": "IP",
            "params": {}
        }
        
        sparse_results = self.collection.search(
            data=[sparse_embedding],
            anns_field="sparse_embedding",
            param=sparse_params,
            limit=top_k * 2,
            expr=filters,
            output_fields=["doc_id", "chunk_id", "text"]
        )
        
        # Combine and rerank results
        combined_scores = {}
        all_results = {}
        
        # Process dense results
        for result in dense_results:
            key = f"{result['doc_id']}_{result['chunk_id']}"
            combined_scores[key] = alpha * result['score']
            all_results[key] = result
        
        # Process sparse results
        for hits in sparse_results:
            for hit in hits:
                key = f"{hit.entity.doc_id}_{hit.entity.chunk_id}"
                if key in combined_scores:
                    combined_scores[key] += (1 - alpha) * hit.score
                else:
                    combined_scores[key] = (1 - alpha) * hit.score
                    all_results[key] = {
                        "score": hit.score,
                        "doc_id": hit.entity.doc_id,
                        "chunk_id": hit.entity.chunk_id,
                        "text": hit.entity.text
                    }
        
        # Sort by combined score
        sorted_keys = sorted(combined_scores.keys(), key=lambda k: combined_scores[k], reverse=True)
        
        # Return top k results
        final_results = []
        for key in sorted_keys[:top_k]:
            result = all_results[key]
            result["combined_score"] = combined_scores[key]
            final_results.append(result)
        
        return final_results
    
    def delete_documents(self, doc_ids: List[str]) -> None:
        """Delete documents by doc_id.
        
        Args:
            doc_ids: List of document IDs to delete
        """
        if not self.collection:
            raise ValueError("Collection not initialized")
        
        expr = f"doc_id in {doc_ids}"
        self.collection.delete(expr)
        self.logger.info(f"Deleted {len(doc_ids)} documents")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics.
        
        Returns:
            Dictionary with collection statistics
        """
        if not self.collection:
            return {"error": "Collection not initialized"}
        
        stats = {
            "collection_name": self.collection_name,
            "dimension": self.dimension,
            "num_entities": self.collection.num_entities,
            "schema": str(self.collection.schema),
            "indexes": self.collection.indexes,
        }
        
        return stats
    
    def disconnect(self) -> None:
        """Disconnect from Milvus."""
        if self.collection:
            self.collection.release()
        
        if self.client:
            # Milvus Lite
            self.client = None
        else:
            # Milvus server
            connections.disconnect("default")
        
        self.logger.info("Disconnected from Milvus")