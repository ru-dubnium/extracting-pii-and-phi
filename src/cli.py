# src/cli.py
import os
import sys
import json
import time
import click
from rich.console import Console

# Add parent directory to path to allow running directly or via python -m
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.extractor import HybridExtractor
    from src.risk import compute_risk
    from src.leakage import detect_leakage
    from src.reporter import print_report
except ImportError:
    from extractor import HybridExtractor
    from risk import compute_risk
    from leakage import detect_leakage
    from reporter import print_report

@click.command()
@click.option('--prompt', help='Text prompt to analyze for PII/PHI.')
@click.option('--image', help='Path to image file to perform OCR and analyze.')
@click.option('--input-file', help='Path to file containing input prompt.')
# Support both --output-file and --output for user convenience
@click.option('--output-file', '--output', 'output_file', help='Path to file containing target LLM response (for leakage detection).')
@click.option('--detect-leakage', 'should_detect_leakage', is_flag=True, help='Explicitly enable leakage detection (requires output file).')
@click.option('--model', default='llama3.2', help='Ollama model name to use (defaults to llama3.2).')
def main(prompt, image, input_file, output_file, should_detect_leakage, model):
    """
    PII/PHI Extraction and Leakage Detection CLI tool.
    Extracts sensitive information from prompts/images and checks for leakage.
    """
    console = Console(record=True)
    extractor = HybridExtractor(default_model=model)
    
    source_text = ""
    is_image = False
    source_name = ""
    
    # 1. Determine input source
    if image:
        if not os.path.exists(image):
            console.print(f"[bold red]Error:[/bold red] Image file not found: {image}")
            sys.exit(1)
        source_text = image
        is_image = True
        source_name = f"Image OCR ({os.path.basename(image)})"
    elif prompt:
        source_text = prompt
        source_name = "Console prompt input"
    elif input_file:
        if not os.path.exists(input_file):
            console.print(f"[bold red]Error:[/bold red] Input file not found: {input_file}")
            sys.exit(1)
        with open(input_file, 'r', encoding='utf-8') as f:
            source_text = f.read()
        source_name = f"Input file ({os.path.basename(input_file)})"
    else:
        click.echo("Error: Please provide one of --prompt, --image, or --input-file")
        click.echo("Use --help for usage details.")
        sys.exit(1)

    console.print(f"[bold blue]Processing input source:[/bold blue] {source_name}")
    
    # 2. Extract entities
    try:
        entities = extractor.extract(source_text, is_image=is_image, model=model)
    except Exception as e:
        console.print(f"[bold red]Extraction failed:[/bold red] {e}")
        sys.exit(1)
        
    risk = compute_risk(entities)
    
    # 3. Handle leakage detection if output file is provided
    leaked_entities = None
    output_provided = False
    
    if output_file or should_detect_leakage:
        if not output_file:
            console.print("[bold red]Error:[/bold red] --detect-leakage requires a target output file via --output or --output-file")
            sys.exit(1)
            
        if not os.path.exists(output_file):
            console.print(f"[bold red]Error:[/bold red] Output file not found: {output_file}")
            sys.exit(1)
            
        with open(output_file, 'r', encoding='utf-8') as f:
            target_response = f.read()
            
        output_provided = True
        console.print(f"[bold blue]Running Leakage Detection against:[/bold blue] {output_file}")
        
        try:
            # Extract from target output using the same extractor/model settings
            target_entities = extractor.extract(target_response, model=model)
            leaked_entities = detect_leakage(entities, target_entities)
        except Exception as e:
            console.print(f"[bold red]Failed to extract entities from target response:[/bold red] {e}")
            sys.exit(1)
            
    # 4. Generate report
    print_report(entities, risk, leaked_entities, output_provided)
    
    # 5. Save report outputs to artifacts (reports directory)
    timestamp = int(time.time())
    os.makedirs("reports", exist_ok=True)
    
    # Structured JSON output
    json_output = {
        "timestamp": timestamp,
        "input_source": source_name,
        "entities_extracted": entities,
        "risk_score": risk,
        "leakage_checked": output_provided,
        "leaked_entities": leaked_entities if output_provided else []
    }
    
    json_path = f"reports/extraction_{timestamp}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_output, f, indent=2)
        
    # Pretty TXT output
    txt_path = f"reports/report_{timestamp}.txt"
    console.save_text(txt_path)
    
    console.print(f"\n[bold green]✓ Reports saved successfully:[/bold green]")
    console.print(f"  - Structured JSON: [dim]{json_path}[/dim]")
    console.print(f"  - Text Summary: [dim]{txt_path}[/dim]")

if __name__ == "__main__":
    main()
