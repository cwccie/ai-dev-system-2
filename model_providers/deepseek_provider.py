"""
DeepSeek Provider
Implementation for DeepSeek models
"""

import os
import re
import json
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional

from model_providers.base_provider import BaseModelProvider


class DeepSeekProvider(BaseModelProvider):
    """
    Provider implementation for DeepSeek models
    """
    
    def __init__(self, api_key: str = None, model: str = "deepseek-coder"):
        """
        Initialize the DeepSeek provider
        
        Args:
            api_key: DeepSeek API key, defaults to environment variable
            model: DeepSeek model to use
        """
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DeepSeek API key is required")
        
        self.model = model
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        
    async def generate_response(self, 
                               prompt: str, 
                               system_prompt: Optional[str] = None,
                               temperature: float = 0.7,
                               max_tokens: int = 4000) -> str:
        """
        Generate a response from DeepSeek
        
        Args:
            prompt: The user prompt to send to DeepSeek
            system_prompt: System instructions for DeepSeek (optional)
            temperature: Controls randomness, higher values = more random
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            String containing DeepSeek's response
        """
        try:
            messages = []
            
            # Add system message if provided
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
                
            # Add user message
            messages.append({"role": "user", "content": prompt})
            
            # Prepare the request payload
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"API Error: {response.status} - {error_text}")
                    
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
            
        except Exception as e:
            print(f"Error generating response from DeepSeek: {e}")
            return f"Error: {str(e)}"
    
    async def extract_code(self, response: str) -> List[str]:
        """
        Extract code blocks from DeepSeek's response
        
        Args:
            response: The full text response from DeepSeek
            
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
        """Get the name of the currently used DeepSeek model"""
        return self.model
    
    def get_provider_name(self) -> str:
        """Get the provider name"""
        return "deepseek"
    
    def get_context_window(self) -> int:
        """
        Get DeepSeek's context window size in tokens
        
        Returns:
            Integer representing the context window size
        """
        # Context window sizes for different DeepSeek models
        context_windows = {
            "deepseek-coder": 32768,
            "deepseek-chat": 16384,
            # Add more models as they become available
        }
        
        return context_windows.get(self.model, 16384)  # Default to 16K
    
    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text
        
        Args:
            text: The text to count tokens for
            
        Returns:
            Integer representing the token count
        """
        # DeepSeek doesn't have a public tokenizer, so we use a rough estimate
        return len(text.split()) * 1.3  # Rough estimate based on typical tokenization
