"""
Ollama Client - Handles communication with Ollama API
"""

import requests
from rich.console import Console

# Initialize Rich console
console = Console()

# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "llama3.1:8b-instruct-q4_K_M"  # You can change this to your preferred model

class OllamaClient:
    """Client for interacting with Ollama API"""

    @staticmethod
    def generate(prompt: str, model: str = MODEL_NAME, temperature: float = 0.7) -> str:
        """Generate text using Ollama"""
        try:
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": temperature
                },
                timeout=60
            )
            response.raise_for_status()
            return response.json()["response"]
        except requests.exceptions.ConnectionError:
            console.print("[bold red]Error: Cannot connect to Ollama. Make sure Ollama is running.[/bold red]")
            console.print("[yellow]Start Ollama with: ollama serve[/yellow]")
            raise
        except Exception as e:
            console.print(f"[bold red]Error generating response: {e}[/bold red]")
            raise
