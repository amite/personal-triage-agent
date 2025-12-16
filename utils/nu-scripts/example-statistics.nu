#!/usr/bin/env nu

def main [
    --json
    --category: string
] {
    let cmd = if $json {
        'from utils.example_loader import ExampleLoader; import json; loader = ExampleLoader(); print(json.dumps(loader.get_statistics(), indent=2))'
    } else {
        'from utils.example_loader import ExampleLoader; from rich.console import Console; from rich.json import JSON; import json; console = Console(); loader = ExampleLoader(); console.print(JSON(json.dumps(loader.get_statistics())))'
    }
    
    uv run python -c $cmd
}