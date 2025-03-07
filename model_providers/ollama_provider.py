"""
Ollama Provider
Implementation for locally hosted models via Ollama
"""

import os
import re
import json
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Union
import logging

from model_providers.base_provider import BaseModelProvider

# Set up logging
logger = logging.getLogger(__name__)

class OllamaProvider(BaseModelProvider):
    """
    Provider implementation for locally hosted models via Ollama
    """
    
    def __init__(self, api_url: str = None, model: str = "codellama:34b", server_id: str = None):
        """
        Initialize the Ollama provider
        
        Args:
            api_url: Base URL for the Ollama API, defaults to environment variable
            model: Ollama model to use
            server_id: Identifier for the server running this model
        """
        self.api_url = api_url or os.environ.get("OLLAMA_API_URL", "http://localhost:11434")
        self.model = model
        self.server_id = server_id
        
        # Strip any trailing slashes from the API URL
        if self.api_url.endswith('/'):
            self.api_url = self.api_url[:-1]
        
        # Validate URL
        if not self.api_url.startswith(('http://', 'https://')):
            raise ValueError(f"Invalid Ollama API URL: {self.api_url}")
        
        logger.info(f"Initialized Ollama provider with model {model} on server {server_id} at {self.api_url}")
    
    async def generate_response(self, 
                              prompt: str, 
                              system_prompt: Optional[str] = None,
                              temperature: float = 0.7,
                              max_tokens: int = 4000) -> str:
        """
        Generate a response from a local Ollama model
        
        Args:
            prompt: The user prompt to send to the model
            system_prompt: System instructions for the model (optional)
            temperature: Controls randomness, higher values = more random
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            String containing the model's response
        """
        try:
            # Construct the payload
            payload = {
                "model": self.model,
                "prompt": prompt,
                "temperature": temperature,
                "num_predict": max_tokens,
                "stream": False
            }
            
            # Add system prompt if provided
            if system_prompt:
                # Different models may have different formats for system prompts
                # For Llama models, we use this format
                if "llama" in self.model.lower():
                    full_prompt = f"<s>[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n{prompt} [/INST]"
                    payload["prompt"] = full_prompt
                else:
                    # For models that support system as a separate field
                    payload["system"] = system_prompt
            
            # Make the request
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/api/generate", json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Ollama API error: {response.status} - {error_text}")
                    
                    result = await response.json()
                    return result.get("response", "")
        
        except Exception as e:
            logger.error(f"Error generating response from Ollama model: {e}")
            return f"Error: {str(e)}"
    
    async def extract_code(self, response: str) -> List[str]:
        """
        Extract code blocks from model's response
        
        Args:
            response: The full text response from the model
            
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
        """Get the name of the currently used model"""
        return self.model
    
    def get_provider_name(self) -> str:
        """Get the provider name"""
        return "ollama"
    
    def get_context_window(self) -> int:
        """
        Get model's context window size in tokens
        
        Returns:
            Integer representing the context window size
        """
        # Context window sizes for different local models
        context_windows = {
            "codellama:34b": 16384,
            "codellama:13b": 16384,
            "codellama:7b": 16384,
            "llama2:70b": 4096,
            "llama2:13b": 4096,
            "llama2:7b": 4096,
            "wizardcoder:15b": 8192,
            "wizardlm:30b": 4096,
            "mpt:30b": 8192,
            "mpt:7b": 8192,
            "vicuna:13b": 4096,
            "wizard-coder:python": 16384,
            "starcoder": 16384
        }
        
        # Extract the base model name before any customization tags
        base_model = self.model.split(':')[0].lower() + ":" + self.model.split(':')[1].lower() if ":" in self.model else self.model.lower()
        
        # Return the context window size or a default value
        return context_windows.get(base_model, 4096)
    
    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text
        
        Args:
            text: The text to count tokens for
            
        Returns:
            Integer representing the token count
        """
        # Simple estimation based on whitespace tokenization
        # For more accurate counts, you'd need model-specific tokenizers
        words = len(text.split())
        return int(words * 1.3)  # Rough estimate (1.3 tokens per word)
    
    async def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the model
        
        Returns:
            Dictionary with model information
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/api/tags") as response:
                    if response.status != 200:
                        return {"error": f"Failed to get model info: {response.status}"}
                    
                    result = await response.json()
                    
                    # Find the specific model in the list
                    model_info = None
                    for model in result.get("models", []):
                        if model.get("name") == self.model:
                            model_info = model
                            break
                    
                    if model_info:
                        return {
                            "name": model_info.get("name"),
                            "size": model_info.get("size"),
                            "modified_at": model_info.get("modified_at"),
                            "server_id": self.server_id,
                            "api_url": self.api_url
                        }
                    else:
                        return {"error": f"Model {self.model} not found on server {self.server_id}"}
        
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return {"error": str(e)}
    
    async def check_availability(self) -> Dict[str, Any]:
        """
        Check if the model is available and ready
        
        Returns:
            Dictionary with availability status
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/api/tags") as response:
                    if response.status != 200:
                        return {
                            "available": False,
                            "reason": f"Server returned status {response.status}"
                        }
                    
                    result = await response.json()
                    models = [model.get("name") for model in result.get("models", [])]
                    
                    if self.model in models:
                        return {
                            "available": True,
                            "server_id": self.server_id
                        }
                    else:
                        return {
                            "available": False,
                            "reason": f"Model {self.model} not found on server {self.server_id}",
                            "available_models": models
                        }
        
        except Exception as e:
            logger.error(f"Error checking model availability: {e}")
            return {
                "available": False,
                "reason": str(e)
            }
