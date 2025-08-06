"""Command-line interface for PDF processing and RAG system."""

import click
import json
import sys
import multiprocessing
from pathlib import Path
from datetime import datetime
from typing import Optional

from .batch_pdf_processor import BatchPDFProcessor
from .rag_system import TaxCourtRAGSystem
from .pdf_pipeline import setup_logging


@click.group()
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, verbose):
    """US Tax Court Document Processing and Search System."""
    ctx.ensure_object(dict)
    ctx.obj['logger'] = setup_logging("DEBUG" if verbose else "INFO")


@cli.command()
@click.option('--input-dir', default='data/documents', help='Input directory with PDFs')
@click.option('--output-dir', default='data/markdown_documents', help='Output directory for markdown')
@click.option('--json-output-dir', default='data/json_documents', help='Output directory for JSON documents')
@click.option('--workers', default=2, help='Number of parallel workers')
@click.option('--skip-existing/--no-skip', default=True, help='Skip already processed files')
@click.option('--filter', 'pdf_filter', help='Filter pattern (e.g., "2020-01/*.pdf")')
@click.option('--enable-ocr/--no-ocr', default=True, help='Enable OCR for scanned documents')
@click.option('--enable-tables/--no-tables', default=True, help='Enable table structure recognition')
@click.option('--enable-vlm', is_flag=True, help='Enable Vision-Language Model (slower but more accurate)')
@click.pass_context
def process_pdfs(ctx, input_dir, output_dir, json_output_dir, workers, skip_existing, pdf_filter, 
                 enable_ocr, enable_tables, enable_vlm):
    """Process all PDFs to markdown and JSON formats."""
    logger = ctx.obj['logger']
    
    click.echo(f"Processing PDFs from {input_dir}")
    click.echo(f"  Markdown output: {output_dir}")
    click.echo(f"  JSON output: {json_output_dir}")
    click.echo(f"Workers: {workers}, OCR: {enable_ocr}, Tables: {enable_tables}, VLM: {enable_vlm}")
    
    processor = BatchPDFProcessor(
        input_dir=input_dir,
        output_dir=output_dir,
        json_output_dir=json_output_dir,
        max_workers=workers,
        enable_ocr=enable_ocr,
        enable_table_structure=enable_tables,
        enable_vlm=enable_vlm
    )
    
    stats = processor.process_all_pdfs(
        skip_existing=skip_existing,
        pdf_filter=pdf_filter
    )
    
    # Display results
    click.echo("\n" + "=" * 60)
    click.echo("Processing Complete!")
    click.echo(f"Total PDFs: {stats['total']}")
    click.echo(f"Processed: {stats['processed']}")
    click.echo(f"Skipped: {stats['skipped']}")
    click.echo(f"Failed: {stats['failed']}")
    
    if stats['processed'] > 0:
        click.echo(f"Total pages: {stats['total_pages']}")
        click.echo(f"Average speed: {stats['avg_pages_per_second']:.2f} pages/second")
    
    return 0 if stats['failed'] == 0 else 1


@cli.command()
@click.option('--markdown-dir', default='data/markdown_documents', help='Directory with markdown files')
@click.option('--vector-dir', default='data/vector_store', help='Directory for vector store')
@click.option('--incremental', is_flag=True, help='Add to existing index instead of rebuilding')
@click.option('--embedding-model', default='BAAI/bge-base-en-v1.5', help='HuggingFace embedding model')
@click.option('--chunk-size', default=512, help='Text chunk size for indexing')
@click.pass_context
def build_index(ctx, markdown_dir, vector_dir, incremental, embedding_model, chunk_size):
    """Build or update the vector search index."""
    logger = ctx.obj['logger']
    
    click.echo(f"Building index from {markdown_dir}")
    click.echo(f"Vector store: {vector_dir}")
    click.echo(f"Embedding model: {embedding_model}")
    click.echo(f"Incremental: {incremental}")
    
    try:
        rag = TaxCourtRAGSystem(
            markdown_dir=markdown_dir,
            vector_store_dir=vector_dir,
            embedding_model=embedding_model,
            chunk_size=chunk_size,
            logger=logger
        )
        
        # Build index
        with click.progressbar(length=100, label='Building index') as bar:
            rag.build_index(persist=True, incremental=incremental)
            bar.update(100)
        
        # Get statistics
        stats = rag.get_statistics()
        
        click.echo("\n" + "=" * 60)
        click.echo("Index Built Successfully!")
        click.echo(f"Total documents: {stats.get('total_markdown_files', 0)}")
        click.echo(f"Total chunks: {stats.get('total_chunks', 'Unknown')}")
        click.echo(f"Total size: {stats.get('total_size_mb', 0):.2f} MB")
        
        return 0
        
    except ImportError as e:
        click.echo(f"Error: {e}", err=True)
        click.echo("Install required packages: pip install llama-index llama-index-embeddings-huggingface", err=True)
        return 1
    except Exception as e:
        click.echo(f"Error building index: {e}", err=True)
        return 1


@cli.command()
@click.argument('query')
@click.option('--markdown-dir', default='data/markdown_documents', help='Directory with markdown files')
@click.option('--vector-dir', default='data/vector_store', help='Directory for vector store')
@click.option('--top-k', default=5, help='Number of results to return')
@click.option('--year', type=int, help='Filter by year')
@click.option('--month', type=int, help='Filter by month')
@click.option('--docket', help='Filter by docket number')
@click.option('--json-output', is_flag=True, help='Output results as JSON')
@click.pass_context
def search(ctx, query, markdown_dir, vector_dir, top_k, year, month, docket, json_output):
    """Search the document index."""
    logger = ctx.obj['logger']
    
    try:
        rag = TaxCourtRAGSystem(
            markdown_dir=markdown_dir,
            vector_store_dir=vector_dir,
            logger=logger
        )
        
        # Build filters
        filters = {}
        if year:
            filters['year'] = year
        if month:
            filters['month'] = month
        if docket:
            filters['docket_number'] = docket
        
        # Perform search
        results = rag.search(query, top_k=top_k, filters=filters if filters else None)
        
        if json_output:
            click.echo(json.dumps(results, indent=2, default=str))
        else:
            # Display results in readable format
            click.echo("\n" + "=" * 60)
            click.echo(f"Query: {query}")
            
            if filters:
                click.echo(f"Filters: {filters}")
            
            click.echo("\n" + "-" * 60)
            click.echo("Response:")
            click.echo("-" * 60)
            click.echo(results['response'])
            
            if results['source_nodes']:
                click.echo("\n" + "-" * 60)
                click.echo(f"Sources ({len(results['source_nodes'])} documents):")
                click.echo("-" * 60)
                
                for i, node in enumerate(results['source_nodes'], 1):
                    click.echo(f"\n{i}. Relevance Score: {node['score']:.3f}")
                    
                    metadata = node['metadata']
                    if 'source_file' in metadata:
                        click.echo(f"   File: {Path(metadata['source_file']).name}")
                    if 'filing_period' in metadata:
                        click.echo(f"   Period: {metadata['filing_period']}")
                    if 'docket_number' in metadata:
                        click.echo(f"   Docket: {metadata['docket_number']}")
                    
                    # Show snippet
                    text_snippet = node['text'][:300].replace('\n', ' ')
                    click.echo(f"   Snippet: {text_snippet}...")
        
        return 0
        
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        click.echo("Build the index first: python -m dawson_scraper.src.cli_rag build-index", err=True)
        return 1
    except ImportError as e:
        click.echo(f"Error: {e}", err=True)
        click.echo("Install required packages: pip install llama-index llama-index-embeddings-huggingface", err=True)
        return 1
    except Exception as e:
        click.echo(f"Error searching: {e}", err=True)
        return 1


@cli.command()
@click.option('--markdown-dir', default='data/markdown_documents', help='Directory with markdown files')
@click.option('--vector-dir', default='data/vector_store', help='Directory for vector store')
@click.option('--processing-db', default='data/processing_stats/processing.db', help='Processing database')
@click.pass_context
def stats(ctx, markdown_dir, vector_dir, processing_db):
    """Show system statistics."""
    logger = ctx.obj['logger']
    
    click.echo("System Statistics")
    click.echo("=" * 60)
    
    # PDF Processing Stats
    if Path(processing_db).exists():
        processor = BatchPDFProcessor(db_path=processing_db)
        proc_stats = processor.get_processing_stats()
        
        click.echo("\nPDF Processing:")
        click.echo(f"  Total PDFs: {proc_stats['total']}")
        click.echo(f"  Completed: {proc_stats['completed']}")
        click.echo(f"  Failed: {proc_stats['failed']}")
        click.echo(f"  Pending: {proc_stats['pending']}")
        
        if proc_stats['completed'] > 0:
            click.echo(f"  Total pages: {proc_stats['total_pages']}")
            click.echo(f"  Total time: {proc_stats['total_time']:.2f} seconds")
            click.echo(f"  Avg speed: {proc_stats['avg_pages_per_second']:.2f} pages/second")
    
    # RAG System Stats
    try:
        rag = TaxCourtRAGSystem(
            markdown_dir=markdown_dir,
            vector_store_dir=vector_dir,
            logger=logger
        )
        rag_stats = rag.get_statistics()
        
        click.echo("\nRAG System:")
        click.echo(f"  Markdown files: {rag_stats['total_markdown_files']}")
        click.echo(f"  Total size: {rag_stats.get('total_size_mb', 0):.2f} MB")
        click.echo(f"  Index exists: {rag_stats['index_exists']}")
        click.echo(f"  Index loaded: {rag_stats['index_loaded']}")
        
        if 'total_chunks' in rag_stats:
            click.echo(f"  Total chunks: {rag_stats['total_chunks']}")
        
        if 'documents_by_period' in rag_stats and rag_stats['documents_by_period']:
            click.echo("\n  Documents by period:")
            periods = sorted(rag_stats['documents_by_period'].items())
            for period, count in periods[:10]:  # Show first 10
                click.echo(f"    {period}: {count} documents")
            if len(periods) > 10:
                click.echo(f"    ... and {len(periods) - 10} more periods")
                
    except Exception as e:
        click.echo(f"\nRAG System: Not initialized ({e})")
    
    return 0


@cli.command()
@click.pass_context
def quickstart(ctx):
    """Quick setup guide for new users."""
    click.echo("US Tax Court RAG System - Quick Start Guide")
    click.echo("=" * 60)
    click.echo("\n1. Process PDFs to Markdown:")
    click.echo("   python -m dawson_scraper.src.cli_rag process-pdfs")
    click.echo("\n2. Build Search Index:")
    click.echo("   python -m dawson_scraper.src.cli_rag build-index")
    click.echo("\n3. Search Documents:")
    click.echo('   python -m dawson_scraper.src.cli_rag search "capital gains"')
    click.echo("\n4. View Statistics:")
    click.echo("   python -m dawson_scraper.src.cli_rag stats")
    click.echo("\nFor more options, use --help with any command")
    click.echo("\nExample with filters:")
    click.echo('   python -m dawson_scraper.src.cli_rag search "tax deduction" --year 2023 --top-k 10')
    return 0


def main():
    """Main entry point."""
    return cli(obj={})


if __name__ == '__main__':
    # Required for Windows multiprocessing
    multiprocessing.freeze_support()
    sys.exit(main())