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
DEFAULT_GPT_MODEL = "gpt-5-mini"

class GPTClient(LLMClientBase):
    """Client for interacting with OpenAI GPT-5 API"""
    
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
            # Use Responses API for GPT-5 models, Chat Completions for older models
            if model.startswith("gpt-5"):
                # GPT-5 models use Responses API
                response = requests.post(
                    f"{OPENAI_BASE_URL}/responses",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "input": prompt,
                        "max_output_tokens": 2000
                    },
                    timeout=60
                )
            else:
                # Older models use Chat Completions API
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
                        "max_completion_tokens": 1000
                    },
                    timeout=60
                )
            response.raise_for_status()
            
            # Extract the generated content based on API used
            response_data = response.json()
            
            if model.startswith("gpt-5"):
                # Responses API format
                output_items = response_data.get("output", [])
                for item in output_items:
                    if item.get("type") == "message":
                        content_items = item.get("content", [])
                        for content in content_items:
                            if content.get("type") == "output_text":
                                return content.get("text", "").strip()
                raise ValueError("No output_text found in Responses API response")
            else:
                # Chat Completions API format
                choices = response_data.get("choices", [])
                if choices and len(choices) > 0:
                    return choices[0]["message"]["content"].strip()
                else:
                    raise ValueError("No choices returned from Chat Completions API")
                
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