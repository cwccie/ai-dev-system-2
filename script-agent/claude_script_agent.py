"""
AI Script Agent

This module provides functionality for generating individual scripts using AI models.
"""

import os
import sys
import json
import time
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

# Add parent directory to sys.path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Try to import the model providers module
    from model_providers.base_provider import BaseModelProvider
except ImportError:
    # Define a fallback if model_providers is not available
    class BaseModelProvider:
        """Fallback base class if model_providers is not available"""
        pass


class ScriptAgent:
    """
    Agent for generating individual scripts using AI models
    """
    
    def __init__(self, provider: Optional[BaseModelProvider] = None, config_path: str = None):
        """
        Initialize the script agent
        
        Args:
            provider: AI model provider to use
            config_path: Path to the configuration file
        """
        self.provider = provider
        
        # Load configuration
        self.config = {}
        if config_path:
            self._load_config(config_path)
        else:
            # Try to load from default location
            default_config = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "config.json"
            )
            if os.path.exists(default_config):
                self._load_config(default_config)
        
        # Initialize conversation history
        self.conversation_history = []
    
    def _load_config(self, config_path: str) -> None:
        """Load configuration from a JSON file"""
        try:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        except Exception as e:
            print(f"Error loading configuration from {config_path}: {e}")
            # Use default empty config
            self.config = {}
    
    async def generate_script(self, 
                             name: str, 
                             description: str, 
                             requirements: List[str] = None,
                             file_path: str = None,
                             iterations: int = None) -> str:
        """
        Generate a script based on the provided specifications
        
        Args:
            name: Name of the script
            description: Detailed description of the script's purpose
            requirements: List of specific requirements
            file_path: Path where the script should be saved
            iterations: Number of iterations to run (overrides config)
            
        Returns:
            String containing the generated script
        """
        if requirements is None:
            requirements = []
            
        # Handle the case where we don't have a provider
        if not self.provider:
            return self._fallback_script_generation(name, description, requirements)
        
        # Get number of iterations from config or parameter
        if iterations is None:
            iterations = self.config.get("generation", {}).get("iterations", 1)
        
        # Generate script through multiple iterations
        script_content = None
        
        for iteration in range(1, iterations + 1):
            print(f"Iteration {iteration}/{iterations}")
            
            # Construct the prompt
            prompt = self._construct_prompt(name, description, requirements, iteration, script_content)
            
            # Add prompt to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": prompt,
                "timestamp": datetime.now().isoformat()
            })
            
            # Generate the response
            try:
                system_prompt = self._construct_system_prompt()
                temperature = self.config.get("model", {}).get("temperature", 0.7)
                max_tokens = self.config.get("model", {}).get("max_tokens", 4000)
                
                response = await self.provider.generate_response(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                # Add response to conversation history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Extract code from the response
                code_blocks = await self.provider.extract_code(response)
                
                if code_blocks:
                    script_content = code_blocks[0]  # Use the first code block
                else:
                    # If no code blocks found, use the full response
                    script_content = response
                
            except Exception as e:
                print(f"Error generating script: {e}")
                error_message = f"# Error generating script: {str(e)}"
                
                # Add error to conversation history
                self.conversation_history.append({
                    "role": "system",
                    "content": error_message,
                    "timestamp": datetime.now().isoformat()
                })
                
                return error_message
        
        # Save the script if configured to do so
        if self.config.get("output", {}).get("save_scripts", True) and file_path:
            self._save_script(script_content, file_path)
        elif self.config.get("output", {}).get("save_scripts", True):
            # Save to default location
            output_dir = self.config.get("output", {}).get("output_dir", "generated_scripts")
            os.makedirs(output_dir, exist_ok=True)
            
            # Clean the script name for use as a filename
            clean_name = re.sub(r'[^\w\-\.]', '_', name)
            if not clean_name.endswith('.py'):
                clean_name += '.py'
                
            file_path = os.path.join(output_dir, clean_name)
            self._save_script(script_content, file_path)
        
        # Save conversation history if configured to do so
        if self.config.get("output", {}).get("save_conversation", True):
            self._save_conversation(name)
        
        return script_content
    
    def _fallback_script_generation(self, 
                                   name: str, 
                                   description: str, 
                                   requirements: List[str]) -> str:
        """Fallback method when no provider is available"""
        return f"""
# {name}
# 
# This is a placeholder script. The script agent could not connect 
# to an AI model provider. Please ensure you have set up the appropriate
# API keys and dependencies.
#
# Description: {description}
#
# Requirements:
# {os.linesep.join(['# - ' + req for req in requirements])}
"""
    
    def _construct_system_prompt(self) -> str:
        """Construct the system prompt for the AI model"""
        add_comments = self.config.get("generation", {}).get("add_comments", True)
        include_tests = self.config.get("generation", {}).get("include_tests", False)
        
        prompt = """You are an expert software developer tasked with generating high-quality code.
Your task is to generate a script based on the provided name, description, and requirements.
Follow these guidelines:
1. Write clean, efficient, and well-documented code
2. Include appropriate error handling and input validation
3. Follow best practices for the language/framework being used
4. Keep the code modular and maintainable"""

        if add_comments:
            prompt += """
5. Include detailed comments explaining complex parts of the code
6. Add a docstring at the beginning of the script and for each function/class"""
            
        if include_tests:
            prompt += """
7. Include unit tests for the main functionality"""
            
        prompt += """

Return ONLY the code, without additional explanations or markdown formatting.
"""
        
        return prompt
    
    def _construct_prompt(self, 
                         name: str, 
                         description: str, 
                         requirements: List[str],
                         iteration: int,
                         previous_script: Optional[str] = None) -> str:
        """
        Construct the prompt for the AI model
        
        Args:
            name: Name of the script
            description: Detailed description of the script's purpose
            requirements: List of specific requirements
            iteration: Current iteration number
            previous_script: Script from previous iteration (if any)
            
        Returns:
            String containing the constructed prompt
        """
        # Start with the basic script definition
        prompt = f"""Generate a script named '{name}'.

Description:
{description}
"""
        
        # Add requirements if provided
        if requirements:
            prompt += "\nRequirements:\n"
            for req in requirements:
                prompt += f"- {req}\n"
        
        # Add model-specific information if available
        if self.provider:
            prompt += f"\nUsing {self.provider.get_provider_name()} as the model provider.\n"
        
        # Add iteration context for improvements
        if iteration > 1 and previous_script:
            prompt += f"\nThis is iteration #{iteration}. Here is the previous version of the script that needs improvement:\n\n```\n{previous_script}\n```\n\nPlease improve the script based on the requirements."
        
        return prompt
    
    def _save_script(self, script_content: str, file_path: str) -> None:
        """
        Save the generated script to a file
        
        Args:
            script_content: Content of the script to save
            file_path: Path where the script should be saved
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            # Add metadata as a comment
            metadata = f"""# Generated by AI Script Agent
# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            if self.provider:
                metadata += f"# Model: {self.provider.get_model_name()}\n"
                
            # Add metadata at the top of the file, but after any shebang if present
            if script_content.startswith('#!'):
                shebang_end = script_content.find('\n') + 1
                script_content = script_content[:shebang_end] + '\n' + metadata + script_content[shebang_end:]
            else:
                script_content = metadata + script_content
            
            # Write the script to file
            with open(file_path, 'w') as f:
                f.write(script_content)
                
            print(f"Script saved to: {file_path}")
            
        except Exception as e:
            print(f"Error saving script to {file_path}: {e}")
    
    def _save_conversation(self, script_name: str) -> None:
        """
        Save the conversation history to a file
        
        Args:
            script_name: Name of the script being generated
        """
        try:
            # Create directory if it doesn't exist
            output_dir = self.config.get("output", {}).get("output_dir", "generated_scripts")
            os.makedirs(output_dir, exist_ok=True)
            
            # Clean the script name for use as a filename
            clean_name = re.sub(r'[^\w\-\.]', '_', script_name)
            
            # Create a timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Construct the conversation file path
            file_path = os.path.join(output_dir, f"{clean_name}_conversation_{timestamp}.json")
            
            # Write the conversation to file
            with open(file_path, 'w') as f:
                json.dump({
                    "script_name": script_name,
                    "timestamp": timestamp,
                    "model": self.provider.get_model_name() if self.provider else "unknown",
                    "conversation": self.conversation_history
                }, f, indent=2)
                
            print(f"Conversation saved to: {file_path}")
            
        except Exception as e:
            print(f"Error saving conversation: {e}")


# Command-line interface
if __name__ == "__main__":
    import argparse
    import asyncio
    
    parser = argparse.ArgumentParser(description="Generate a script using the AI Script Agent")
    parser.add_argument("--name", type=str, required=True, help="Name of the script")
    parser.add_argument("--description", type=str, required=True, help="Description of the script")
    parser.add_argument("--requirements", type=str, nargs="*", help="Requirements for the script")
    parser.add_argument("--output", type=str, help="Path where the script should be saved")
    parser.add_argument("--config", type=str, help="Path to the configuration file")
    parser.add_argument("--provider", type=str, choices=["claude", "openai", "deepseek"], 
                        default="claude", help="AI model provider to use")
    parser.add_argument("--iterations", type=int, help="Number of iterations to run")
    
    args = parser.parse_args()
    
    # Try to import the model providers module
    try:
        from model_providers import get_provider
        
        # Get the appropriate provider
        provider = get_provider(args.provider)
        if not provider:
            print(f"Could not initialize {args.provider} provider. Check your API key.")
            sys.exit(1)
            
        # Initialize the script agent
        agent = ScriptAgent(provider=provider, config_path=args.config)
        
        # Generate the script
        script = asyncio.run(agent.generate_script(
            name=args.name,
            description=args.description,
            requirements=args.requirements,
            file_path=args.output,
            iterations=args.iterations
        ))
        
        print("Script generation complete.")
        
    except ImportError:
        print("Could not import model providers. Running in fallback mode.")
        
        # Initialize the script agent without a provider
        agent = ScriptAgent(config_path=args.config)
        
        # Generate the script in fallback mode
        script = agent._fallback_script_generation(
            name=args.name,
            description=args.description,
            requirements=args.requirements or []
        )
        
        # Save the script if an output path is provided
        if args.output:
            try:
                os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
                with open(args.output, 'w') as f:
                    f.write(script)
                print(f"Script saved to: {args.output}")
            except Exception as e:
                print(f"Error saving script to {args.output}: {e}")
                
        print("Script generation complete (fallback mode).")
