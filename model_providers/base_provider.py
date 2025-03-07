"""
Base Model Provider
Abstract base class for all model providers
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class BaseModelProvider(ABC):
    """
    Abstract base class that defines the interface for all model providers
    """
    
    @abstractmethod
    async def generate_response(self, 
                               prompt: str, 
                               system_prompt: Optional[str] = None,
                               temperature: float = 0.7,
                               max_tokens: int = 4000) -> str:
        """
        Generate a response from the model
        
        Args:
            prompt: The user prompt to send to the model
            system_prompt: System instructions for the model (optional)
            temperature: Controls randomness, higher values = more random
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            String containing the model's response
        """
        pass
    
    @abstractmethod
    async def extract_code(self, response: str) -> List[str]:
        """
        Extract code blocks from a model response
        
        Args:
            response: The full text response from the model
            
        Returns:
            List of extracted code blocks
        """
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """
        Get the name of the currently used model
        
        Returns:
            String containing the model name
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the name of the provider
        
        Returns:
            String containing the provider name
        """
        pass
    
    @abstractmethod
    def get_context_window(self) -> int:
        """
        Get the context window size of the model in tokens
        
        Returns:
            Integer representing the context window size
        """
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text
        
        Args:
            text: The text to count tokens for
            
        Returns:
            Integer representing the token count
        """
        pass
