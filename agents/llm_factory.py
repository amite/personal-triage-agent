"""
LLM Client Factory - Provides a way to create and switch between different LLM clients
"""

import os
from typing import Optional
from agents.llm_client_base import LLMClientBase
from agents.ollama_client import OllamaClient
from agents.gpt_client import GPTClient

class LLMFactory:
    """
    Factory class for creating LLM clients
    Allows easy switching between different LLM providers
    """
    
    @staticmethod
    def create_llm_client(client_type: str = "ollama", **kwargs) -> LLMClientBase:
        """
        Create an LLM client based on the specified type
        
        Args:
            client_type: Type of LLM client ('ollama' or 'gpt')
            **kwargs: Additional arguments for client initialization
            
        Returns:
            Instance of LLMClientBase
            
        Raises:
            ValueError: If client_type is not supported
        """
        client_type = client_type.lower()
        
        if client_type == "ollama":
            return OllamaClient()
        elif client_type == "gpt":
            # Get API key from kwargs or environment
            api_key = kwargs.get("api_key") or os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key required for GPT client. Set OPENAI_API_KEY environment variable or provide api_key parameter.")
            return GPTClient(api_key=api_key)
        else:
            raise ValueError(f"Unsupported LLM client type: {client_type}. Choose 'ollama' or 'gpt'")
    
    @staticmethod
    def get_llm_client_from_env() -> LLMClientBase:
        """
        Create LLM client based on environment variables
        
        Uses LLM_PROVIDER environment variable to determine which client to create
        Defaults to Ollama if not specified
        
        Returns:
            Instance of LLMClientBase
        """
        provider = os.environ.get("LLM_PROVIDER", "ollama").lower()
        return LLMFactory.create_llm_client(provider)