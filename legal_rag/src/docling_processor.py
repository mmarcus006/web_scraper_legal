"""Docling PDF processor for advanced document processing."""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat, OutputFormat
    from docling.datamodel.pipeline_options import (
        PipelineOptions,
        TableFormerMode,
        OCRMode
    )
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    print("Warning: Docling not installed. Install with: pip install docling docling-core docling-ibm-models")

from .config import settings


class DoclingProcessor:
    """Process PDFs using IBM Docling for advanced document understanding."""
    
    def __init__(
        self,
        enable_ocr: bool = True,
        enable_tables: bool = True,
        enable_formulas: bool = True,
        enable_vlm: bool = False,
        max_workers: int = 4,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize Docling processor.
        
        Args:
            enable_ocr: Enable OCR for scanned documents
            enable_tables: Enable table structure recognition
            enable_formulas: Enable formula extraction
            enable_vlm: Enable Vision-Language Model
            max_workers: Number of parallel workers
            logger: Optional logger instance
        """
        if not DOCLING_AVAILABLE:
            raise ImportError("Docling is required. Install with: pip install docling")
        
        self.logger = logger or logging.getLogger(__name__)
        self.enable_ocr = enable_ocr or settings.enable_ocr
        self.enable_tables = enable_tables or settings.enable_tables
        self.enable_formulas = enable_formulas or settings.enable_formulas
        self.enable_vlm = enable_vlm or settings.enable_vlm
        self.max_workers = max_workers or settings.max_workers
        
        # Initialize Docling converter
        self.converter = self._initialize_converter()
    
    def _initialize_converter(self) -> DocumentConverter:
        """Initialize Docling converter with configured options.
        
        Returns:
            Configured DocumentConverter instance
        """
        # Configure pipeline options
        pipeline_options = PipelineOptions()
        
        # OCR configuration
        if self.enable_ocr:
            pipeline_options.ocr_mode = OCRMode.RAPID_OCR
            self.logger.info("OCR enabled with RapidOCR")
        else:
            pipeline_options.ocr_mode = OCRMode.OFF
        
        # Table recognition configuration
        if self.enable_tables:
            pipeline_options.table_former_mode = TableFormerMode.ACCURATE
            self.logger.info("Table recognition enabled with TableFormer")
        else:
            pipeline_options.table_former_mode = TableFormerMode.OFF
        
        # Formula extraction
        pipeline_options.extract_formulas = self.enable_formulas
        if self.enable_formulas:
            self.logger.info("Formula extraction enabled")
        
        # Vision-Language Model
        if self.enable_vlm:
            pipeline_options.use_vision_model = True
            self.logger.info("Vision-Language Model enabled")
        
        # Create converter
        converter = DocumentConverter(
            pipeline_options=pipeline_options,
            pdf_backend="pypdfium2"  # Better PDF rendering
        )
        
        return converter
    
    def process_pdf(
        self,
        pdf_path: Path,
        output_format: str = "markdown"
    ) -> Tuple[str, Dict[str, Any]]:
        """Process a single PDF document.
        
        Args:
            pdf_path: Path to PDF file
            output_format: Output format (markdown, json, html)
            
        Returns:
            Tuple of (processed_text, metadata)
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        self.logger.info(f"Processing PDF: {pdf_path.name}")
        
        try:
            # Convert document
            result = self.converter.convert(
                str(pdf_path),
                input_format=InputFormat.PDF
            )
            
            # Extract content based on format
            if output_format == "markdown":
                content = result.to_markdown()
            elif output_format == "json":
                content = result.to_json()
            elif output_format == "html":
                content = result.to_html()
            else:
                content = result.to_text()
            
            # Extract metadata
            metadata = self._extract_metadata(result, pdf_path)
            
            self.logger.info(f"Successfully processed {pdf_path.name}")
            return content, metadata
            
        except Exception as e:
            self.logger.error(f"Failed to process {pdf_path}: {e}")
            raise
    
    def _extract_metadata(self, result: Any, pdf_path: Path) -> Dict[str, Any]:
        """Extract metadata from processed document.
        
        Args:
            result: Docling conversion result
            pdf_path: Original PDF path
            
        Returns:
            Metadata dictionary
        """
        metadata = {
            "source_file": str(pdf_path),
            "file_name": pdf_path.name,
            "file_size": pdf_path.stat().st_size,
            "processing_timestamp": Path(pdf_path).stat().st_mtime
        }
        
        # Extract document metadata if available
        if hasattr(result, 'metadata'):
            doc_meta = result.metadata
            metadata.update({
                "num_pages": getattr(doc_meta, 'num_pages', 0),
                "title": getattr(doc_meta, 'title', ''),
                "author": getattr(doc_meta, 'author', ''),
                "creation_date": getattr(doc_meta, 'creation_date', ''),
            })
        
        # Extract structure information
        if hasattr(result, 'document'):
            doc = result.document
            metadata.update({
                "num_tables": len(getattr(doc, 'tables', [])),
                "num_figures": len(getattr(doc, 'figures', [])),
                "num_formulas": len(getattr(doc, 'formulas', [])),
                "has_ocr_content": any(getattr(p, 'is_ocr', False) for p in getattr(doc, 'pages', [])),
            })
        
        # Extract from filename pattern (e.g., "10086-98_uuid.pdf")
        file_stem = pdf_path.stem
        if '_' in file_stem:
            docket_part = file_stem.split('_')[0]
            metadata['docket_number'] = docket_part
        
        # Extract from directory structure (e.g., "2024-01/")
        parent_dir = pdf_path.parent.name
        if '-' in parent_dir and len(parent_dir) == 7:  # YYYY-MM format
            year, month = parent_dir.split('-')
            metadata['year'] = int(year)
            metadata['month'] = int(month)
        
        return metadata
    
    def process_directory(
        self,
        input_dir: Path,
        output_dir: Path,
        output_format: str = "markdown",
        skip_existing: bool = True,
        pattern: str = "*.pdf"
    ) -> Dict[str, Any]:
        """Process all PDFs in a directory.
        
        Args:
            input_dir: Input directory with PDFs
            output_dir: Output directory for processed files
            output_format: Output format (markdown, json, html)
            skip_existing: Skip already processed files
            pattern: File pattern to match
            
        Returns:
            Processing statistics
        """
        input_dir = Path(input_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Find all PDFs
        pdf_files = list(input_dir.rglob(pattern))
        self.logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        # Filter existing if needed
        if skip_existing:
            pdf_files = self._filter_existing(pdf_files, output_dir, output_format)
            self.logger.info(f"Processing {len(pdf_files)} new files")
        
        # Process statistics
        stats = {
            "total": len(pdf_files),
            "processed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": []
        }
        
        # Process files in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit tasks
            future_to_pdf = {
                executor.submit(
                    self._process_and_save,
                    pdf_path,
                    output_dir,
                    output_format
                ): pdf_path
                for pdf_path in pdf_files
            }
            
            # Process results with progress bar
            with tqdm(total=len(pdf_files), desc="Processing PDFs") as pbar:
                for future in as_completed(future_to_pdf):
                    pdf_path = future_to_pdf[future]
                    try:
                        success = future.result()
                        if success:
                            stats["processed"] += 1
                        else:
                            stats["failed"] += 1
                    except Exception as e:
                        stats["failed"] += 1
                        stats["errors"].append({
                            "file": str(pdf_path),
                            "error": str(e)
                        })
                        self.logger.error(f"Failed to process {pdf_path}: {e}")
                    finally:
                        pbar.update(1)
        
        return stats
    
    def _process_and_save(
        self,
        pdf_path: Path,
        output_dir: Path,
        output_format: str
    ) -> bool:
        """Process and save a single PDF.
        
        Args:
            pdf_path: Path to PDF
            output_dir: Output directory
            output_format: Output format
            
        Returns:
            Success status
        """
        try:
            # Process PDF
            content, metadata = self.process_pdf(pdf_path, output_format)
            
            # Determine output path
            relative_path = pdf_path.relative_to(pdf_path.parent.parent)
            output_subdir = output_dir / relative_path.parent
            output_subdir.mkdir(parents=True, exist_ok=True)
            
            # Save content
            if output_format == "markdown":
                ext = ".md"
            elif output_format == "json":
                ext = ".json"
            elif output_format == "html":
                ext = ".html"
            else:
                ext = ".txt"
            
            output_file = output_subdir / f"{pdf_path.stem}{ext}"
            
            if output_format == "json":
                # Save as JSON with metadata
                output_data = {
                    "content": content,
                    "metadata": metadata
                }
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, indent=2, ensure_ascii=False)
            else:
                # Save content
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Save metadata separately
                metadata_file = output_subdir / f"{pdf_path.stem}_metadata.json"
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to process and save {pdf_path}: {e}")
            return False
    
    def _filter_existing(
        self,
        pdf_files: List[Path],
        output_dir: Path,
        output_format: str
    ) -> List[Path]:
        """Filter out already processed files.
        
        Args:
            pdf_files: List of PDF files
            output_dir: Output directory
            output_format: Output format
            
        Returns:
            List of unprocessed PDF files
        """
        if output_format == "markdown":
            ext = ".md"
        elif output_format == "json":
            ext = ".json"
        elif output_format == "html":
            ext = ".html"
        else:
            ext = ".txt"
        
        unprocessed = []
        for pdf_path in pdf_files:
            relative_path = pdf_path.relative_to(pdf_path.parent.parent)
            output_file = output_dir / relative_path.parent / f"{pdf_path.stem}{ext}"
            
            if not output_file.exists():
                unprocessed.append(pdf_path)
        
        return unprocessed
    
    def extract_chunks(
        self,
        content: str,
        metadata: Dict[str, Any],
        chunk_size: int = 512,
        chunk_overlap: int = 50
    ) -> List[Dict[str, Any]]:
        """Extract chunks from processed content for vector indexing.
        
        Args:
            content: Processed document content
            metadata: Document metadata
            chunk_size: Size of each chunk in tokens
            chunk_overlap: Overlap between chunks
            
        Returns:
            List of chunk dictionaries
        """
        # Simple character-based chunking (can be replaced with token-based)
        chunks = []
        text_length = len(content)
        
        chunk_id = 0
        start = 0
        
        while start < text_length:
            end = min(start + chunk_size, text_length)
            
            # Try to find a good break point (sentence end)
            if end < text_length:
                for sep in ['. ', '.\n', '! ', '? ', '\n\n']:
                    sep_pos = content.rfind(sep, start, end)
                    if sep_pos != -1:
                        end = sep_pos + len(sep)
                        break
            
            chunk_text = content[start:end].strip()
            
            if chunk_text:
                chunk = {
                    "chunk_id": chunk_id,
                    "text": chunk_text,
                    "start_pos": start,
                    "end_pos": end,
                    **metadata  # Include all metadata
                }
                chunks.append(chunk)
                chunk_id += 1
            
            # Move to next chunk with overlap
            start = end - chunk_overlap if end < text_length else end
        
        return chunks