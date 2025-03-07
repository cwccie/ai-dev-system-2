"""
Claude Provider
Implementation for Anthropic's Claude models
"""

import os
import re
import asyncio
from typing import Dict, Any, List, Optional

import anthropic
from anthropic import Anthropic

from model_providers.base_provider import BaseModelProvider


class ClaudeProvider(BaseModelProvider):
    """
    Provider implementation for Anthropic's Claude models
    """
    
    def __init__(self, api_key: str = None, model: str = "claude-3-7-sonnet-20250219"):
        """
        Initialize the Claude provider
        
        Args:
            api_key: Anthropic API key, defaults to environment variable
            model: Claude model to use
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key is required")
        
        self.model = model
        self.client = Anthropic(api_key=self.api_key)
        
    async def generate_response(self, 
                               prompt: str, 
                               system_prompt: Optional[str] = None,
                               temperature: float = 0.7,
                               max_tokens: int = 4000) -> str:
        """
        Generate a response from Claude
        
        Args:
            prompt: The user prompt to send to Claude
            system_prompt: System instructions for Claude (optional)
            temperature: Controls randomness, higher values = more random
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            String containing Claude's response
        """
        try:
            # Use the appropriate parameters for Claude
            params = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
            
            if system_prompt:
                params["system"] = system_prompt
                
            # Run in an asyncio event loop
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.messages.create(**params)
            )
            
            return response.content[0].text
            
        except Exception as e:
            print(f"Error generating response from Claude: {e}")
            return f"Error: {str(e)}"
    
    async def extract_code(self, response: str) -> List[str]:
        """
        Extract code blocks from Claude's response
        
        Args:
            response: The full text response from Claude
            
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
        """Get the name of the currently used Claude model"""
        return self.model
    
    def get_provider_name(self) -> str:
        """Get the provider name"""
        return "claude"
    
    def get_context_window(self) -> int:
        """
        Get Claude's context window size in tokens
        
        Returns:
            Integer representing the context window size
        """
        # Context window sizes for different Claude models
        context_windows = {
            "claude-3-opus-20240229": 200000,
            "claude-3-5-sonnet-20240620": 200000,
            "claude-3-7-sonnet-20250219": 200000,
            "claude-3-sonnet-20240229": 200000,
            "claude-3-haiku-20240307": 200000,
            "claude-3-5-haiku-20240620": 200000,
            "claude-2.1": 200000,
            "claude-2.0": 100000,
            "claude-instant-1.2": 100000,
            # Add more models as they become available
        }
        
        return context_windows.get(self.model, 100000)  # Default to 100K
    
    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text using Claude's tokenizer
        
        Args:
            text: The text to count tokens for
            
        Returns:
            Integer representing the token count
        """
        try:
            return self.client.count_tokens(text)
        except Exception as e:
            print(f"Error counting tokens: {e}")
            # Fallback to rough estimate
            return len(text.split()) * 1.3  # Rough estimate
