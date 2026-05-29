# src/reporter.py
from rich.console import Console
from rich.table import Table

def print_report(entities, risk, leaked_entities=None, output_provided=False):
    """
    Prints a formatted, human-readable terminal report of extracted PII/PHI entities,
    the overall risk score, and leakage detection status.
    """
    console = Console()
    
    # 1. Main extraction table
    if entities:
        table = Table(title="[bold cyan]Extracted PII/PHI Entities[/bold cyan]", show_header=True, header_style="bold magenta")
        table.add_column("Type", style="cyan", width=25)
        table.add_column("Value", style="green", width=45)
        table.add_column("Confidence", justify="right", style="yellow")
        table.add_column("Source", style="italic blue")
        
        for e in entities:
            table.add_row(
                e['type'],
                e['value'],
                f"{e['confidence']:.2f}",
                e['source']
            )
        console.print(table)
    else:
        console.print("[yellow]No PII/PHI entities extracted.[/yellow]")
        
    # 2. Risk score display
    risk_colors = {
        "HIGH": "bold red",
        "MEDIUM": "bold yellow",
        "LOW": "bold green"
    }
    color = risk_colors.get(risk, "white")
    console.print(f"\n[bold]Overall Risk Score:[/bold] [{color}]{risk}[/{color}]")
    
    # 3. Leakage detection table
    if output_provided:
        console.print("\n" + "=" * 50)
        console.print("[bold underline]Leakage Detection Results[/bold underline]")
        if leaked_entities:
            console.print("\n[bold red]⚠️  CRITICAL WARNING: Leakage Detected![/bold red]")
            console.print("The following sensitive entities from the input prompt were found in the target response:\n")
            
            leak_table = Table(show_header=True, header_style="bold red")
            leak_table.add_column("Type", style="cyan", width=25)
            leak_table.add_column("Value", style="red", width=45)
            
            for e in leaked_entities:
                leak_table.add_row(e['type'], e['value'])
            console.print(leak_table)
        else:
            console.print("\n[bold green]✓ Secure: No leakage detected.[/bold green]")
            console.print("No sensitive PII/PHI from the input prompt was found in the target response.")
        console.print("=" * 50)
