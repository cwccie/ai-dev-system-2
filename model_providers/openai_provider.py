"""
OpenAI Provider
Implementation for OpenAI's GPT models
"""

import os
import re
import asyncio
from typing import Dict, Any, List, Optional

import openai
from openai import OpenAI

from model_providers.base_provider import BaseModelProvider


class OpenAIProvider(BaseModelProvider):
    """
    Provider implementation for OpenAI's GPT models
    """
    
    def __init__(self, api_key: str = None, model: str = "gpt-4o"):
        """
        Initialize the OpenAI provider
        
        Args:
            api_key: OpenAI API key, defaults to environment variable
            model: GPT model to use
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.model = model
        self.client = OpenAI(api_key=self.api_key)
        
    async def generate_response(self, 
                               prompt: str, 
                               system_prompt: Optional[str] = None,
                               temperature: float = 0.7,
                               max_tokens: int = 4000) -> str:
        """
        Generate a response from GPT
        
        Args:
            prompt: The user prompt to send to GPT
            system_prompt: System instructions for GPT (optional)
            temperature: Controls randomness, higher values = more random
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            String containing GPT's response
        """
        try:
            messages = []
            
            # Add system message if provided
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
                
            # Add user message
            messages.append({"role": "user", "content": prompt})
            
            # Use the appropriate parameters for GPT
            params = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            # Run in an asyncio event loop
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(**params)
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating response from GPT: {e}")
            return f"Error: {str(e)}"
    
    async def extract_code(self, response: str) -> List[str]:
        """
        Extract code blocks from GPT's response
        
        Args:
            response: The full text response from GPT
            
        Returns:
            List of extracted code blocks
        """
        # Pattern to match code blocks with or without language specification
        pattern = r'```(?:\w+\n)?(.*?)```'
        matches = re.findall(pattern, response, re.DOTALL)
        
        # If no matches found, check if the entire response might be code
        if not matches and not response.startswith('```') and not response.endswith('```'):
            # Heuristic: If response has multiple lines and looks like code
            lines = response.split('\n')
            if len(lines) > 1 and any(line.strip().startswith(('def ', 'class ', 'import ', 'from ')) for line in lines):
                return [response]
        
        return matches
    
    def get_model_name(self) -> str:
        """Get the name of the currently used GPT model"""
        return self.model
    
    def get_provider_name(self) -> str:
        """Get the provider name"""
        return "openai"
    
    def get_context_window(self) -> int:
        """
        Get GPT's context window size in tokens
        
        Returns:
            Integer representing the context window size
        """
        # Context window sizes for different GPT models
        context_windows = {
            "gpt-4o": 128000,
            "gpt-4-turbo": 128000,
            "gpt-4": 8192,
            "gpt-4-32k": 32768,
            "gpt-3.5-turbo": 16385,
            "gpt-3.5-turbo-16k": 16385,
            # Add more models as they become available
        }
        
        return context_windows.get(self.model, 8192)  # Default to 8K
    
    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text
        
        Args:
            text: The text to count tokens for
            
        Returns:
            Integer representing the token count
        """
        try:
            # Use tiktoken if available (not imported by default to reduce dependencies)
            try:
                import tiktoken
                encoding = tiktoken.encoding_for_model(self.model)
                return len(encoding.encode(text))
            except ImportError:
                # Fallback to rough estimate
                return len(text.split()) * 1.3  # Rough estimate
        except Exception as e:
            print(f"Error counting tokens: {e}")
            # Fallback to rough estimate
            return len(text.split()) * 1.3  # Rough estimate
