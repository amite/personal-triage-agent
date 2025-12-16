"""
GPT Client - Handles communication with OpenAI API using official SDK
"""

import os
import logging
from typing import Optional
from openai import OpenAI
from openai import APIError, APIConnectionError, APITimeoutError
from rich.console import Console
from agents.llm_client_base import LLMClientBase

logger = logging.getLogger(__name__)

# Initialize Rich console
console = Console()

# OpenAI configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
DEFAULT_GPT_MODEL = "gpt-5-nano"

class GPTClient(LLMClientBase):
    """Client for interacting with OpenAI API using official SDK"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize GPT client
        
        Args:
            api_key: Optional API key. If not provided, uses OPENAI_API_KEY environment variable
        """
        self.api_key = api_key or OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key not provided and OPENAI_API_KEY environment variable not set")
        self.client = OpenAI(api_key=self.api_key)
    
    def generate(self, prompt: str, model: Optional[str] = None, temperature: float = 0.3) -> str:
        """
        Generate text using OpenAI Responses API
        
        Args:
            prompt: The input prompt for text generation
            model: Optional model identifier (defaults to gpt-5-nano)
            temperature: Temperature for generation (0.0-1.0)
            
        Returns:
            Generated text as string
            
        Raises:
            Exception: If generation fails
        """
        model = model or DEFAULT_GPT_MODEL
        
        try:
            # Use Responses API for all models (simplified, single codepath)
            # Note: GPT-5 models don't support temperature parameter in Responses API
            create_params = {
                "model": model,
                "input": prompt,
                "max_output_tokens": 2000,
                "timeout": 60.0
            }
            
            # Only include temperature for models that support it (non-GPT-5 models)
            if not model.startswith("gpt-5"):
                create_params["temperature"] = temperature
            
            response = self.client.responses.create(**create_params)
            
            # Try direct SDK convenience property first (if available)
            if hasattr(response, 'output_text') and response.output_text:
                logger.debug(f"Using response.output_text property: {len(response.output_text)} chars")
                return response.output_text.strip()
            
            # Fallback: Parse Responses API structure manually
            # Structure: response.output (array) -> message items -> content array -> output_text items -> text
            output_items = getattr(response, 'output', [])
            
            for item in output_items:
                # Find message-type items
                item_type = getattr(item, 'type', None) if hasattr(item, 'type') else (item.get("type") if isinstance(item, dict) else None)
                
                if item_type == "message":
                    # Get content array from message item
                    content_items = getattr(item, 'content', []) if hasattr(item, 'content') else (item.get("content", []) if isinstance(item, dict) else [])
                    
                    for content in content_items:
                        # Check for output_text type
                        content_type = getattr(content, 'type', None) if hasattr(content, 'type') else (content.get("type") if isinstance(content, dict) else None)
                        
                        if content_type in ["output_text", "text"]:
                            # Extract text field
                            text = getattr(content, 'text', None) if hasattr(content, 'text') else (content.get("text") if isinstance(content, dict) else None)
                            
                            if text:
                                logger.debug(f"Extracted text from Responses API structure: {len(text)} chars")
                                return text.strip()
            
            # If no text found, log for debugging
            logger.error(f"No output_text found in Responses API response")
            logger.debug(f"Response type: {type(response)}")
            logger.debug(f"Response attributes: {dir(response)[:20]}...")  # First 20 to avoid spam
            if output_items:
                logger.debug(f"Output items count: {len(output_items)}")
                logger.debug(f"First item type: {getattr(output_items[0], 'type', 'unknown')}")
            raise ValueError("No output text found in Responses API response")
                
        except APITimeoutError as e:
            error_msg = "OpenAI API request timed out."
            console.print(f"[bold red]Error: {error_msg}[/bold red]")
            logger.error(f"Timeout error: {e}")
            raise Exception(error_msg) from e
        except APIConnectionError as e:
            error_msg = "Cannot connect to OpenAI API. Check your internet connection."
            console.print(f"[bold red]Error: {error_msg}[/bold red]")
            logger.error(f"Connection error: {e}")
            raise Exception(error_msg) from e
        except APIError as e:
            status_code = getattr(e, "status_code", "unknown")
            message = getattr(e, "message", str(e))
            error_msg = f"OpenAI API error: {status_code} - {message}"
            console.print(f"[bold red]{error_msg}[/bold red]")
            logger.error(f"API error: {e}")
            raise Exception(error_msg) from e
        except Exception as e:
            console.print(f"[bold red]Error generating response: {e}[/bold red]")
            logger.error(f"Unexpected error: {e}", exc_info=True)
            raise