"""
Abstract Base Class for LLM Clients
Provides a common interface for all LLM implementations
"""

from abc import ABC, abstractmethod
from typing import Optional

class LLMClientBase(ABC):
    """
    Abstract base class for LLM clients
    Defines the common interface that all LLM implementations must follow
    """
    
    @abstractmethod
    def generate(self, prompt: str, model: Optional[str] = None, temperature: float = 0.3) -> str:
        """
        Generate text from a prompt using the LLM
        
        Args:
            prompt: The input prompt for text generation
            model: Optional model identifier
            temperature: Temperature for generation (0.0-1.0)
            
        Returns:
            Generated text as string
            
        Raises:
            Exception: If generation fails
        """
        pass