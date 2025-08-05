"""Batch PDF processor for converting all court documents to markdown format."""

import os
import json
import time
import multiprocessing
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed
import logging

from tqdm import tqdm
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .pdf_pipeline import (
    create_docling_converter,
    convert_pdf_to_markdown,
    save_markdown_with_metadata,
    setup_logging
)

Base = declarative_base()


class ProcessingRecord(Base):
    """Database model for tracking PDF processing."""
    __tablename__ = "pdf_processing"
    
    id = Column(Integer, primary_key=True)
    pdf_path = Column(String, nullable=False, unique=True)
    markdown_path = Column(String)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    pages = Column(Integer)
    processing_time = Column(Float)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime)


class BatchPDFProcessor:
    """Batch processor for converting PDFs to markdown."""
    
    def __init__(
        self,
        input_dir: str = "data/documents",
        output_dir: str = "data/markdown_documents",
        db_path: str = "data/processing_stats/processing.db",
        max_workers: int = 4,
        enable_ocr: bool = True,
        enable_table_structure: bool = True,
        enable_vlm: bool = False
    ):
        """
        Initialize batch PDF processor.
        
        Args:
            input_dir: Directory containing PDF files
            output_dir: Directory for markdown output
            db_path: Path to SQLite database for tracking
            max_workers: Maximum parallel workers
            enable_ocr: Enable OCR for scanned documents
            enable_table_structure: Enable table structure recognition
            enable_vlm: Enable Vision-Language Model
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.db_path = Path(db_path)
        self.max_workers = max_workers
        self.enable_ocr = enable_ocr
        self.enable_table_structure = enable_table_structure
        self.enable_vlm = enable_vlm
        
        # Setup database
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Setup logging
        self.logger = setup_logging("INFO")
    
    def get_pdf_files(self) -> List[Path]:
        """Get all PDF files from input directory.
        
        Returns:
            List of PDF file paths
        """
        pdf_files = list(self.input_dir.rglob("*.pdf"))
        self.logger.info(f"Found {len(pdf_files)} PDF files in {self.input_dir}")
        return pdf_files
    
    def get_output_path(self, pdf_path: Path) -> Path:
        """Get markdown output path for a PDF file.
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Path for markdown output
        """
        # Calculate relative path from input directory
        relative_path = pdf_path.relative_to(self.input_dir)
        
        # Create corresponding path in output directory
        output_path = self.output_dir / relative_path.parent / pdf_path.stem
        
        return output_path
    
    def should_process_pdf(self, pdf_path: Path) -> bool:
        """Check if PDF needs processing.
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            True if PDF should be processed
        """
        session = self.SessionLocal()
        try:
            # Check database for existing record
            record = session.query(ProcessingRecord).filter_by(
                pdf_path=str(pdf_path)
            ).first()
            
            if record and record.status == "completed":
                # Check if markdown file exists
                output_path = self.get_output_path(pdf_path)
                markdown_path = output_path.with_suffix('.md')
                
                if markdown_path.exists():
                    # Check if PDF is newer than markdown
                    pdf_mtime = pdf_path.stat().st_mtime
                    md_mtime = markdown_path.stat().st_mtime
                    
                    if pdf_mtime <= md_mtime:
                        return False  # Skip, already processed
            
            return True
            
        finally:
            session.close()
    
    def update_processing_record(
        self,
        pdf_path: Path,
        status: str,
        markdown_path: Optional[str] = None,
        pages: Optional[int] = None,
        processing_time: Optional[float] = None,
        error_message: Optional[str] = None
    ):
        """Update processing record in database.
        
        Args:
            pdf_path: Path to PDF file
            status: Processing status
            markdown_path: Path to generated markdown
            pages: Number of pages processed
            processing_time: Time taken to process
            error_message: Error message if failed
        """
        session = self.SessionLocal()
        try:
            record = session.query(ProcessingRecord).filter_by(
                pdf_path=str(pdf_path)
            ).first()
            
            if not record:
                record = ProcessingRecord(pdf_path=str(pdf_path))
                session.add(record)
            
            record.status = status
            
            if markdown_path:
                record.markdown_path = str(markdown_path)
            if pages is not None:
                record.pages = pages
            if processing_time is not None:
                record.processing_time = processing_time
            if error_message:
                record.error_message = error_message
            
            if status == "completed":
                record.completed_at = datetime.now()
            
            session.commit()
            
        finally:
            session.close()
    
    def process_single_pdf_wrapper(self, pdf_path: Path) -> Dict[str, Any]:
        """Wrapper for processing single PDF with error handling.
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Processing result dictionary
        """
        try:
            # Update status to processing
            self.update_processing_record(pdf_path, "processing")
            
            # Get output path
            output_path = self.get_output_path(pdf_path)
            
            # Create converter for this process
            converter = create_docling_converter(
                enable_ocr=self.enable_ocr,
                enable_table_structure=self.enable_table_structure,
                enable_vlm=self.enable_vlm
            )
            
            # Convert PDF
            start_time = time.time()
            markdown_content, metadata = convert_pdf_to_markdown(
                pdf_path, converter, self.logger
            )
            processing_time = time.time() - start_time
            
            # Save markdown and metadata
            save_markdown_with_metadata(
                markdown_content, metadata, output_path, self.logger
            )
            
            # Update database
            self.update_processing_record(
                pdf_path,
                "completed",
                markdown_path=str(output_path.with_suffix('.md')),
                pages=metadata.get("pages", 0),
                processing_time=processing_time
            )
            
            return {
                "status": "success",
                "pdf_path": str(pdf_path),
                "output_path": str(output_path),
                "pages": metadata.get("pages", 0),
                "processing_time": processing_time
            }
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Failed to process {pdf_path}: {error_msg}")
            
            # Update database with error
            self.update_processing_record(
                pdf_path,
                "failed",
                error_message=error_msg
            )
            
            return {
                "status": "error",
                "pdf_path": str(pdf_path),
                "error": error_msg
            }
    
    def process_all_pdfs(
        self,
        skip_existing: bool = True,
        pdf_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process all PDFs in the input directory.
        
        Args:
            skip_existing: Skip already processed PDFs
            pdf_filter: Optional filter pattern (e.g., "2020-01/*.pdf")
        
        Returns:
            Processing statistics
        """
        self.logger.info("Starting batch PDF processing...")
        self.logger.info(f"Input directory: {self.input_dir}")
        self.logger.info(f"Output directory: {self.output_dir}")
        self.logger.info(f"Max workers: {self.max_workers}")
        
        # Get PDF files
        if pdf_filter:
            pdf_files = list(self.input_dir.glob(pdf_filter))
        else:
            pdf_files = self.get_pdf_files()
        
        if not pdf_files:
            self.logger.warning("No PDF files found to process")
            return {"total": 0, "processed": 0, "skipped": 0, "failed": 0}
        
        # Filter PDFs based on skip_existing
        if skip_existing:
            pdfs_to_process = [
                pdf for pdf in pdf_files
                if self.should_process_pdf(pdf)
            ]
            skipped = len(pdf_files) - len(pdfs_to_process)
            self.logger.info(f"Skipping {skipped} already processed PDFs")
        else:
            pdfs_to_process = pdf_files
            skipped = 0
        
        if not pdfs_to_process:
            self.logger.info("All PDFs already processed")
            return {
                "total": len(pdf_files),
                "processed": 0,
                "skipped": skipped,
                "failed": 0
            }
        
        # Process PDFs in parallel
        results = []
        successful = 0
        failed = 0
        total_pages = 0
        total_time = 0
        
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_pdf = {
                executor.submit(self.process_single_pdf_wrapper, pdf): pdf
                for pdf in pdfs_to_process
            }
            
            # Process results with progress bar
            with tqdm(total=len(pdfs_to_process), desc="Processing PDFs") as pbar:
                for future in as_completed(future_to_pdf):
                    pdf_path = future_to_pdf[future]
                    
                    try:
                        result = future.result(timeout=300)  # 5 minute timeout
                        results.append(result)
                        
                        if result["status"] == "success":
                            successful += 1
                            total_pages += result.get("pages", 0)
                            total_time += result.get("processing_time", 0)
                        else:
                            failed += 1
                        
                    except Exception as e:
                        self.logger.error(f"Processing failed for {pdf_path}: {e}")
                        failed += 1
                        results.append({
                            "status": "error",
                            "pdf_path": str(pdf_path),
                            "error": str(e)
                        })
                    
                    pbar.update(1)
                    pbar.set_postfix({
                        "Success": successful,
                        "Failed": failed,
                        "Pages": total_pages
                    })
        
        # Calculate statistics
        stats = {
            "total": len(pdf_files),
            "processed": successful,
            "skipped": skipped,
            "failed": failed,
            "total_pages": total_pages,
            "total_time": total_time,
            "avg_time_per_pdf": total_time / successful if successful > 0 else 0,
            "avg_pages_per_second": total_pages / total_time if total_time > 0 else 0
        }
        
        # Log summary
        self.logger.info("=" * 60)
        self.logger.info("BATCH PROCESSING COMPLETE")
        self.logger.info(f"Total PDFs: {stats['total']}")
        self.logger.info(f"Processed: {stats['processed']}")
        self.logger.info(f"Skipped: {stats['skipped']}")
        self.logger.info(f"Failed: {stats['failed']}")
        self.logger.info(f"Total pages: {stats['total_pages']}")
        self.logger.info(f"Total time: {stats['total_time']:.2f} seconds")
        self.logger.info(f"Average speed: {stats['avg_pages_per_second']:.2f} pages/second")
        self.logger.info("=" * 60)
        
        return stats
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics from database.
        
        Returns:
            Processing statistics
        """
        session = self.SessionLocal()
        try:
            total = session.query(ProcessingRecord).count()
            completed = session.query(ProcessingRecord).filter_by(status="completed").count()
            failed = session.query(ProcessingRecord).filter_by(status="failed").count()
            processing = session.query(ProcessingRecord).filter_by(status="processing").count()
            pending = session.query(ProcessingRecord).filter_by(status="pending").count()
            
            # Get total pages and processing time
            completed_records = session.query(ProcessingRecord).filter_by(status="completed").all()
            total_pages = sum(r.pages or 0 for r in completed_records)
            total_time = sum(r.processing_time or 0 for r in completed_records)
            
            return {
                "total": total,
                "completed": completed,
                "failed": failed,
                "processing": processing,
                "pending": pending,
                "total_pages": total_pages,
                "total_time": total_time,
                "avg_time_per_pdf": total_time / completed if completed > 0 else 0,
                "avg_pages_per_second": total_pages / total_time if total_time > 0 else 0
            }
            
        finally:
            session.close()


# CLI usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Batch process PDFs to markdown")
    parser.add_argument("--input-dir", default="data/documents", help="Input directory")
    parser.add_argument("--output-dir", default="data/markdown_documents", help="Output directory")
    parser.add_argument("--workers", type=int, default=4, help="Number of parallel workers")
    parser.add_argument("--no-skip", action="store_true", help="Process all PDFs, don't skip existing")
    parser.add_argument("--filter", help="Filter pattern (e.g., '2020-01/*.pdf')")
    parser.add_argument("--enable-vlm", action="store_true", help="Enable Vision-Language Model")
    parser.add_argument("--stats", action="store_true", help="Show statistics only")
    
    args = parser.parse_args()
    
    processor = BatchPDFProcessor(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        max_workers=args.workers,
        enable_vlm=args.enable_vlm
    )
    
    if args.stats:
        stats = processor.get_processing_stats()
        print(json.dumps(stats, indent=2))
    else:
        stats = processor.process_all_pdfs(
            skip_existing=not args.no_skip,
            pdf_filter=args.filter
        )
        print(json.dumps(stats, indent=2))