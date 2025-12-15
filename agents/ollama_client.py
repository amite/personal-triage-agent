"""
Ollama Client - Handles communication with Ollama API
"""

import requests
from rich.console import Console
from typing import Optional
from agents.llm_client_base import LLMClientBase

# Initialize Rich console
console = Console()

# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "llama3.1:8b-instruct-q4_K_M"  # You can change this to your preferred model

class OllamaClient(LLMClientBase):
    """Client for interacting with Ollama API"""

    def generate(self, prompt: str, model: Optional[str] = None, temperature: float = 0.3) -> str:
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
