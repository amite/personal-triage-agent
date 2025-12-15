"""
GPT-4 Client - Handles communication with OpenAI GPT-4 API
"""

import os
import requests
from typing import Optional
from rich.console import Console
from agents.llm_client_base import LLMClientBase

# Initialize Rich console
console = Console()

# OpenAI configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_GPT_MODEL = "gpt-4-0"

class GPTClient(LLMClientBase):
    """Client for interacting with OpenAI GPT-4 API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize GPT client
        
        Args:
            api_key: Optional API key. If not provided, uses OPENAI_API_KEY environment variable
        """
        self.api_key = api_key or OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key not provided and OPENAI_API_KEY environment variable not set")
    
    def generate(self, prompt: str, model: Optional[str] = None, temperature: float = 0.3) -> str:
        """
        Generate text using GPT-4 API
        
        Args:
            prompt: The input prompt for text generation
            model: Optional model identifier (defaults to gpt-4-0)
            temperature: Temperature for generation (0.0-1.0)
            
        Returns:
            Generated text as string
            
        Raises:
            Exception: If generation fails
        """
        model = model or DEFAULT_GPT_MODEL
        
        try:
            response = requests.post(
                f"{OPENAI_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": temperature,
                    "max_tokens": 1000
                },
                timeout=60
            )
            response.raise_for_status()
            
            # Extract the generated content
            choices = response.json().get("choices", [])
            if choices and len(choices) > 0:
                return choices[0]["message"]["content"].strip()
            else:
                raise ValueError("No choices returned from GPT-4 API")
                
        except requests.exceptions.ConnectionError:
            console.print("[bold red]Error: Cannot connect to OpenAI API. Check your internet connection.[/bold red]")
            raise
        except requests.exceptions.HTTPError as e:
            error_msg = f"OpenAI API error: {e.response.status_code} - {e.response.text}"
            console.print(f"[bold red]{error_msg}[/bold red]")
            raise Exception(error_msg)
        except Exception as e:
            console.print(f"[bold red]Error generating response: {e}[/bold red]")
            raise