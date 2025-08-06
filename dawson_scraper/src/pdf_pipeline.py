"""PDF processing pipeline using IBM Docling for high-quality document conversion."""

import os
import json
import multiprocessing
import logging
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, Tuple, Union

from docling.datamodel.accelerator_options import AcceleratorOptions, AcceleratorDevice
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions, 
    TableStructureOptions,
    TableFormerMode
)
from docling.datamodel.base_models import InputFormat
from docling.datamodel import vlm_model_specs

# Environment setup moved to function to avoid issues with multiprocessing
def setup_environment():
    """Setup environment variables for optimal performance."""
    # Performance optimization: Set thread count for maximum throughput
    cpu_count = multiprocessing.cpu_count()
    os.environ['OMP_NUM_THREADS'] = str(cpu_count)
    
    # Fix Windows symlink permission issue for Hugging Face Hub
    os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
    os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN'] = '1'
    
    # Configure logging levels for production use
    os.environ['DOCLING_LOG_LEVEL'] = 'INFO'
    os.environ['TRANSFORMERS_VERBOSITY'] = 'error'  # Reduce transformer noise
    
    # CUDA stability settings for GPU processing
    try:
        import torch
        if torch.cuda.is_available():
            # Enable synchronous CUDA operations for debugging
            os.environ['CUDA_LAUNCH_BLOCKING'] = '1'
            # Optimize memory allocation to prevent fragmentation
            os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:512'
            # Ensure deterministic operations for reproducibility
            torch.backends.cudnn.benchmark = False
            torch.backends.cudnn.deterministic = True
    except ImportError:
        pass  # PyTorch not available or CPU-only version


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    
    Returns:
        Configured logger instance
    """
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(name)-30s | %(levelname)-8s | %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(getattr(logging, log_level))
    
    # File handler
    file_handler = logging.FileHandler(
        log_dir / f'docling_{datetime.now():%Y%m%d_%H%M%S}.log'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    
    # Configure logger
    logger = logging.getLogger("pdf_pipeline")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


def get_device() -> AcceleratorDevice:
    """Detect available acceleration device.
    
    Returns:
        AcceleratorDevice.CUDA if GPU available, else AcceleratorDevice.CPU
    """
    try:
        import torch
        if torch.cuda.is_available():
            return AcceleratorDevice.CUDA
    except ImportError:
        pass
    return AcceleratorDevice.CPU


def create_docling_converter(
    enable_ocr: bool = True,
    enable_table_structure: bool = True,
    enable_vlm: bool = False,
    max_threads: Optional[int] = None,
    device: Optional[AcceleratorDevice] = None
) -> DocumentConverter:
    """Create a configured Docling DocumentConverter.
    
    Args:
        enable_ocr: Enable OCR for scanned documents
        enable_table_structure: Enable table structure recognition
        enable_vlm: Enable Vision-Language Model for enhanced understanding
        max_threads: Maximum threads to use (None = auto-detect)
        device: Acceleration device (None = auto-detect)
    
    Returns:
        Configured DocumentConverter instance
    """
    # Setup environment on first converter creation
    setup_environment()
    
    if device is None:
        device = get_device()
    
    if max_threads is None:
        max_threads = multiprocessing.cpu_count()
    
    # Create accelerator options
    accelerator_options = AcceleratorOptions(
        device=device,
        num_threads=max_threads
    )
    
    # Configure table structure options for highest accuracy
    table_structure_options = None
    if enable_table_structure:
        table_structure_options = TableStructureOptions(
            do_cell_matching=True,
            mode=TableFormerMode.ACCURATE
        )
    
    # Create PDF pipeline options
    pdf_pipeline_options = PdfPipelineOptions(
        do_ocr=enable_ocr,
        do_table_structure=enable_table_structure,
        table_structure_options=table_structure_options,
        accelerator_options=accelerator_options,
        images_scale=2.0,  # High quality
        generate_page_images=True
    )
    
    # Add VLM if requested
    if enable_vlm:
        pdf_pipeline_options.vlm_options = vlm_model_specs.SMOLDOCLING_TRANSFORMERS
    
    # Create converter
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pdf_pipeline_options
            )
        }
    )
    
    return converter


def convert_pdf_to_markdown(
    pdf_path: Union[str, Path],
    converter: Optional[DocumentConverter] = None,
    logger: Optional[logging.Logger] = None
) -> Tuple[str, Dict[str, Any]]:
    """Convert a PDF file to markdown format.
    
    Args:
        pdf_path: Path to the PDF file
        converter: DocumentConverter instance (creates new if None)
        logger: Logger instance (creates new if None)
    
    Returns:
        Tuple of (markdown_content, metadata_dict)
    """
    if logger is None:
        logger = setup_logging()
    
    if converter is None:
        converter = create_docling_converter()
    
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    logger.info(f"Converting PDF: {pdf_path.name}")
    
    try:
        start_time = time.time()
        
        # Convert the PDF
        result = converter.convert(str(pdf_path))
        
        # Extract markdown content
        markdown_content = result.document.export_to_markdown()
        
        # Extract metadata
        metadata = {
            "source_file": str(pdf_path),
            "pages": len(result.document.pages) if hasattr(result.document, 'pages') else 0,
            "processing_time": time.time() - start_time,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add document metadata if available
        if hasattr(result.document, 'metadata'):
            metadata['document_metadata'] = result.document.metadata
        
        logger.info(f"Conversion complete: {metadata['pages']} pages in {metadata['processing_time']:.2f}s")
        
        return markdown_content, metadata
        
    except Exception as e:
        logger.error(f"Failed to convert {pdf_path}: {str(e)}")
        raise


def save_markdown_with_metadata(
    markdown_content: str,
    metadata: Dict[str, Any],
    output_path: Union[str, Path],
    logger: Optional[logging.Logger] = None
) -> None:
    """Save markdown content and metadata to files.
    
    Args:
        markdown_content: Markdown text content
        metadata: Document metadata
        output_path: Base path for output (without extension)
        logger: Logger instance
    """
    if logger is None:
        logger = setup_logging()
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save markdown
    markdown_path = output_path.with_suffix('.md')
    with open(markdown_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    logger.info(f"Saved markdown: {markdown_path}")
    
    # Save metadata
    metadata_path = output_path.with_suffix('.json')
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)
    logger.info(f"Saved metadata: {metadata_path}")


def process_single_pdf(
    pdf_path: Union[str, Path],
    output_dir: Union[str, Path],
    converter: Optional[DocumentConverter] = None,
    logger: Optional[logging.Logger] = None,
    preserve_structure: bool = True
) -> Dict[str, Any]:
    """Process a single PDF file and save as markdown.
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Output directory for markdown files
        converter: DocumentConverter instance (creates new if None)
        logger: Logger instance (creates new if None)
        preserve_structure: Preserve directory structure in output
    
    Returns:
        Processing result dictionary
    """
    if logger is None:
        logger = setup_logging()
    
    if converter is None:
        converter = create_docling_converter()
    
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    
    try:
        # Convert PDF to markdown
        markdown_content, metadata = convert_pdf_to_markdown(pdf_path, converter, logger)
        
        # Determine output path
        if preserve_structure:
            # Preserve directory structure from data/documents to data/markdown_documents
            relative_path = pdf_path.relative_to(pdf_path.parent.parent)
            output_path = output_dir / relative_path.parent / pdf_path.stem
        else:
            output_path = output_dir / pdf_path.stem
        
        # Save files
        save_markdown_with_metadata(markdown_content, metadata, output_path, logger)
        
        return {
            "status": "success",
            "pdf_path": str(pdf_path),
            "output_path": str(output_path),
            "pages": metadata.get("pages", 0),
            "processing_time": metadata.get("processing_time", 0)
        }
        
    except Exception as e:
        logger.error(f"Failed to process {pdf_path}: {str(e)}")
        return {
            "status": "error",
            "pdf_path": str(pdf_path),
            "error": str(e)
        }


# Example usage
if __name__ == "__main__":
    logger = setup_logging("INFO")
    
    # Example: Process a single PDF
    pdf_path = Path("data/documents/2020-01/sample.pdf")
    output_dir = Path("data/markdown_documents")
    
    if pdf_path.exists():
        logger.info("Starting PDF conversion...")
        converter = create_docling_converter(
            enable_ocr=True,
            enable_table_structure=True,
            enable_vlm=False  # Set to True for enhanced processing
        )
        
        result = process_single_pdf(pdf_path, output_dir, converter, logger)
        logger.info(f"Processing result: {result}")
    else:
        logger.warning(f"Sample PDF not found: {pdf_path}")
        logger.info("Use batch_pdf_processor.py to process all PDFs in data/documents/")