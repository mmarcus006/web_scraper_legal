"""Enhanced CLI interface for Legal RAG System."""

import click
import json
import sys
from pathlib import Path
from typing import Optional
import logging
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown
from rich.panel import Panel

from .advanced_rag_system import AdvancedRAGSystem
from .config import settings


console = Console()


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(settings.data_dir / 'legal_rag.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


@click.group()
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, verbose):
    """Legal RAG System - Advanced document retrieval and generation for US Tax Court documents."""
    ctx.ensure_object(dict)
    ctx.obj['logger'] = setup_logging(verbose)
    ctx.obj['verbose'] = verbose
    console.print("[bold green]Legal RAG System v1.0.0[/bold green]")


@cli.command()
@click.option('--input-dir', default='data/documents', help='Input directory with PDFs')
@click.option('--pattern', default='*.pdf', help='File pattern to match')
@click.option('--skip-existing/--no-skip', default=True, help='Skip already processed files')
@click.option('--workers', default=4, help='Number of parallel workers')
@click.pass_context
def process(ctx, input_dir, pattern, skip_existing, workers):
    """Process PDF documents with Docling."""
    logger = ctx.obj['logger']
    
    console.print(f"\n[bold]Processing PDFs from {input_dir}[/bold]")
    console.print(f"Pattern: {pattern}")
    console.print(f"Workers: {workers}")
    console.print(f"Skip existing: {skip_existing}\n")
    
    try:
        rag_system = AdvancedRAGSystem(use_milvus_lite=True, logger=logger)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Processing documents...", total=None)
            
            stats = rag_system.process_documents(
                input_dir=Path(input_dir),
                pattern=pattern,
                skip_existing=skip_existing
            )
            
            progress.update(task, completed=True)
        
        # Display results
        table = Table(title="Processing Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total PDFs", str(stats.get('total', 0)))
        table.add_row("Processed", str(stats.get('processed', 0)))
        table.add_row("Failed", str(stats.get('failed', 0)))
        table.add_row("Skipped", str(stats.get('skipped', 0)))
        
        console.print(table)
        
        if stats.get('errors'):
            console.print("\n[red]Errors encountered:[/red]")
            for error in stats['errors'][:5]:
                console.print(f"  - {error['file']}: {error['error']}")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--documents-dir', default='data/processed', help='Directory with processed documents')
@click.option('--recreate', is_flag=True, help='Recreate Milvus collection')
@click.option('--use-lite', is_flag=True, help='Use Milvus Lite (embedded)')
@click.pass_context
def index(ctx, documents_dir, recreate, use_lite):
    """Build vector index from processed documents."""
    logger = ctx.obj['logger']
    
    console.print(f"\n[bold]Building index from {documents_dir}[/bold]")
    console.print(f"Recreate collection: {recreate}")
    console.print(f"Use Milvus Lite: {use_lite}\n")
    
    if recreate:
        if not Confirm.ask("[yellow]This will delete existing data. Continue?[/yellow]"):
            console.print("[red]Aborted[/red]")
            return
    
    try:
        rag_system = AdvancedRAGSystem(use_milvus_lite=use_lite, logger=logger)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Building index...", total=None)
            
            index = rag_system.build_index(
                documents_dir=Path(documents_dir),
                recreate_collection=recreate
            )
            
            progress.update(task, completed=True)
        
        console.print("[green]✓ Index built successfully[/green]")
        
        # Show statistics
        stats = rag_system.get_statistics()
        if stats.get('milvus'):
            console.print(f"\nCollection: {stats['milvus'].get('collection_name')}")
            console.print(f"Documents: {stats['milvus'].get('num_entities', 0)}")
            console.print(f"Dimension: {stats['milvus'].get('dimension')}")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('query')
@click.option('--top-k', default=10, help='Number of results to return')
@click.option('--year', type=int, help='Filter by year')
@click.option('--month', type=int, help='Filter by month')
@click.option('--judge', help='Filter by judge name')
@click.option('--docket', help='Filter by docket number')
@click.option('--hybrid/--no-hybrid', default=True, help='Use hybrid search')
@click.option('--json-output', is_flag=True, help='Output as JSON')
@click.option('--use-lite', is_flag=True, help='Use Milvus Lite')
@click.pass_context
def search(ctx, query, top_k, year, month, judge, docket, hybrid, json_output, use_lite):
    """Search for relevant documents."""
    logger = ctx.obj['logger']
    
    # Build filters
    filters = {}
    if year:
        filters['year'] = year
    if month:
        filters['month'] = month
    if judge:
        filters['judge'] = judge
    if docket:
        filters['docket_number'] = docket
    
    try:
        rag_system = AdvancedRAGSystem(use_milvus_lite=use_lite, logger=logger)
        
        # Ensure index exists
        rag_system.milvus_manager.connect(use_lite=use_lite)
        
        with console.status("[bold green]Searching...[/bold green]"):
            results = rag_system.search(
                query=query,
                top_k=top_k,
                filters=filters if filters else None,
                use_hybrid=hybrid
            )
        
        if json_output:
            console.print_json(json.dumps(results, indent=2, default=str))
        else:
            # Display results in rich format
            console.print(Panel(f"[bold]Query:[/bold] {query}", expand=False))
            
            if filters:
                filter_text = ", ".join([f"{k}={v}" for k, v in filters.items()])
                console.print(f"[cyan]Filters:[/cyan] {filter_text}\n")
            
            if results.get('response'):
                console.print(Panel(
                    Markdown(results['response']),
                    title="[bold green]AI Response[/bold green]",
                    expand=False
                ))
            
            # Display documents
            documents = results.get('documents', [])
            if documents:
                console.print(f"\n[bold]Found {len(documents)} relevant documents:[/bold]\n")
                
                for i, doc in enumerate(documents[:5], 1):
                    score = doc.get('score', 0) if not hybrid else doc.get('combined_score', 0)
                    console.print(f"[bold cyan]{i}. Score: {score:.3f}[/bold cyan]")
                    
                    if doc.get('docket_number'):
                        console.print(f"   Docket: {doc['docket_number']}")
                    if doc.get('case_title'):
                        console.print(f"   Title: {doc['case_title']}")
                    if doc.get('judge'):
                        console.print(f"   Judge: {doc['judge']}")
                    if doc.get('source_file'):
                        console.print(f"   Source: {Path(doc['source_file']).name}")
                    
                    text_preview = doc.get('text', '')[:300].replace('\n', ' ')
                    console.print(f"   [dim]{text_preview}...[/dim]\n")
            else:
                console.print("[yellow]No documents found[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--use-lite', is_flag=True, help='Use Milvus Lite')
@click.pass_context
def chat(ctx, use_lite):
    """Interactive chat interface."""
    logger = ctx.obj['logger']
    
    console.print("[bold]Legal RAG Chat Interface[/bold]")
    console.print("Type 'exit' or 'quit' to end the session\n")
    
    if not settings.has_gemini_key:
        console.print("[red]Chat requires Gemini API key to be configured[/red]")
        console.print("Add GOOGLE_API_KEY to your .env file")
        return
    
    try:
        rag_system = AdvancedRAGSystem(use_milvus_lite=use_lite, logger=logger)
        
        # Ensure index exists
        rag_system.milvus_manager.connect(use_lite=use_lite)
        
        chat_history = []
        
        while True:
            # Get user input
            user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]")
            
            if user_input.lower() in ['exit', 'quit']:
                console.print("[yellow]Goodbye![/yellow]")
                break
            
            # Get response
            with console.status("[bold green]Thinking...[/bold green]"):
                response = rag_system.chat(
                    message=user_input,
                    chat_history=chat_history
                )
            
            # Display response
            console.print(f"\n[bold green]Assistant:[/bold green]")
            console.print(Markdown(response))
            
            # Update history
            chat_history.append({"role": "user", "content": user_input})
            chat_history.append({"role": "assistant", "content": response})
            
            # Keep history limited
            if len(chat_history) > 10:
                chat_history = chat_history[-10:]
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--use-lite', is_flag=True, help='Use Milvus Lite')
@click.pass_context
def stats(ctx, use_lite):
    """Show system statistics."""
    logger = ctx.obj['logger']
    
    try:
        rag_system = AdvancedRAGSystem(use_milvus_lite=use_lite, logger=logger)
        
        # Connect to Milvus
        rag_system.milvus_manager.connect(use_lite=use_lite)
        
        stats = rag_system.get_statistics()
        
        # Display Milvus stats
        if stats.get('milvus'):
            table = Table(title="Milvus Statistics")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            milvus_stats = stats['milvus']
            table.add_row("Collection", str(milvus_stats.get('collection_name', 'N/A')))
            table.add_row("Documents", str(milvus_stats.get('num_entities', 0)))
            table.add_row("Dimension", str(milvus_stats.get('dimension', 0)))
            
            console.print(table)
        
        # Display embedding stats
        if stats.get('embeddings'):
            table = Table(title="Embedding Configuration")
            table.add_column("Setting", style="cyan")
            table.add_column("Value", style="green")
            
            emb_stats = stats['embeddings']
            table.add_row("Model", emb_stats.get('dense_model', 'N/A'))
            table.add_row("Dimension", str(emb_stats.get('dimension', 0)))
            table.add_row("Device", emb_stats.get('device', 'cpu'))
            
            if emb_stats.get('gpu_name'):
                table.add_row("GPU", emb_stats['gpu_name'])
                table.add_row("GPU Memory", emb_stats.get('gpu_memory', 'N/A'))
            
            console.print(table)
        
        # Display LLM stats
        if stats.get('llm'):
            table = Table(title="LLM Configuration")
            table.add_column("Setting", style="cyan")
            table.add_column("Value", style="green")
            
            llm_stats = stats['llm']
            table.add_row("Configured", "Yes" if llm_stats.get('configured') else "No")
            if llm_stats.get('model'):
                table.add_row("Model", llm_stats['model'])
            
            console.print(table)
        
        # Display settings
        if stats.get('settings'):
            table = Table(title="RAG Settings")
            table.add_column("Setting", style="cyan")
            table.add_column("Value", style="green")
            
            rag_settings = stats['settings']
            table.add_row("Chunk Size", str(rag_settings.get('chunk_size', 0)))
            table.add_row("Chunk Overlap", str(rag_settings.get('chunk_overlap', 0)))
            table.add_row("Top K", str(rag_settings.get('similarity_top_k', 0)))
            
            console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
def quickstart():
    """Quick setup guide."""
    console.print(Panel.fit(
        """[bold]Legal RAG System - Quick Start Guide[/bold]

1. [cyan]Set up environment:[/cyan]
   - Copy .env.sample to .env
   - Add your GOOGLE_API_KEY for Gemini

2. [cyan]Start Milvus (optional):[/cyan]
   docker-compose up -d
   
   Or use --use-lite flag for embedded mode

3. [cyan]Process PDFs:[/cyan]
   legal-rag process --input-dir data/documents

4. [cyan]Build index:[/cyan]
   legal-rag index --use-lite

5. [cyan]Search documents:[/cyan]
   legal-rag search "capital gains tax" --top-k 5

6. [cyan]Interactive chat:[/cyan]
   legal-rag chat --use-lite

For more options, use --help with any command.""",
        title="Quick Start",
        border_style="green"
    ))


def main():
    """Main entry point."""
    return cli(obj={})


if __name__ == '__main__':
    sys.exit(main())