"""
Cost Estimator
Module for estimating token usage and costs for script generation
"""

import os
import json
import math
from typing import Dict, List, Any, Optional, Tuple, Union
import logging

# Setup logging
logger = logging.getLogger(__name__)


class CostEstimator:
    """
    Estimates token usage and costs for script generation using different AI models
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the cost estimator
        
        Args:
            config_path: Path to the pricing configuration file
        """
        self.pricing_config = self._load_pricing_config(config_path)
        self.token_estimate_cache = {}
        
    def _load_pricing_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """
        Load pricing configuration from file
        
        Args:
            config_path: Path to the pricing configuration file
            
        Returns:
            Dictionary containing pricing configuration
        """
        default_config = {
            "providers": {
                "claude": {
                    "models": {
                        "claude-3-opus-20240229": {
                            "input_cost_per_1k": 15.0,
                            "output_cost_per_1k": 75.0,
                            "max_context_length": 200000
                        },
                        "claude-3-7-sonnet-20250219": {
                            "input_cost_per_1k": 3.0,
                            "output_cost_per_1k": 15.0,
                            "max_context_length": 200000
                        },
                        "claude-3-5-sonnet-20240620": {
                            "input_cost_per_1k": 3.0,
                            "output_cost_per_1k": 15.0,
                            "max_context_length": 200000
                        },
                        "claude-3-haiku-20240307": {
                            "input_cost_per_1k": 0.25,
                            "output_cost_per_1k": 1.25,
                            "max_context_length": 200000
                        },
                        "claude-3-5-haiku-20240620": {
                            "input_cost_per_1k": 0.25,
                            "output_cost_per_1k": 1.25,
                            "max_context_length": 200000
                        }
                    },
                    "default_model": "claude-3-7-sonnet-20250219"
                },
                "openai": {
                    "models": {
                        "gpt-4o": {
                            "input_cost_per_1k": 5.0,
                            "output_cost_per_1k": 15.0,
                            "max_context_length": 128000
                        },
                        "gpt-4-turbo": {
                            "input_cost_per_1k": 10.0,
                            "output_cost_per_1k": 30.0,
                            "max_context_length": 128000
                        },
                        "gpt-4": {
                            "input_cost_per_1k": 30.0,
                            "output_cost_per_1k": 60.0,
                            "max_context_length": 8192
                        },
                        "gpt-3.5-turbo": {
                            "input_cost_per_1k": 0.5,
                            "output_cost_per_1k": 1.5,
                            "max_context_length": 16384
                        }
                    },
                    "default_model": "gpt-4o"
                },
                "deepseek": {
                    "models": {
                        "deepseek-coder": {
                            "input_cost_per_1k": 2.0,
                            "output_cost_per_1k": 10.0,
                            "max_context_length": 32768
                        }
                    },
                    "default_model": "deepseek-coder"
                }
            },
            "default_provider": "claude",
            "token_constants": {
                "avg_tokens_per_word": 1.3,
                "avg_tokens_per_line_python": 8.5,
                "avg_tokens_per_line_javascript": 10.2,
                "avg_tokens_per_line_html": 12.0,
                "avg_tokens_per_char": 0.25
            },
            "estimation_factors": {
                "complexity_multiplier": 1.2,
                "token_buffer_percentage": 15,
                "output_variation_percentage": 10
            }
        }
        
        # Try to load configuration file
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with default config
                    self._recursive_update(default_config, loaded_config)
            except Exception as e:
                logger.error(f"Error loading pricing configuration from {config_path}: {e}")
                logger.info("Using default pricing configuration")
        
        return default_config
    
    def _recursive_update(self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> None:
        """
        Recursively update a dictionary with another dictionary
        
        Args:
            base_dict: Base dictionary to update
            update_dict: Dictionary with new values
        """
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._recursive_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def estimate_script_cost(self, 
                            script_definition: Dict[str, Any], 
                            provider_name: Optional[str] = None,
                            model_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Estimate token usage and cost for generating a script
        
        Args:
            script_definition: Dictionary defining the script requirements
            provider_name: Name of the AI provider (claude, openai, deepseek)
            model_name: Name of the specific model
            
        Returns:
            Dictionary containing token usage and cost estimates
        """
        # Get provider and model
        provider_name = provider_name or self.pricing_config.get("default_provider", "claude")
        provider_config = self.pricing_config.get("providers", {}).get(provider_name, {})
        model_name = model_name or provider_config.get("default_model")
        model_config = provider_config.get("models", {}).get(model_name, {})
        
        if not model_config:
            return {
                "error": f"Model {model_name} not found for provider {provider_name}",
                "cost": 0.0,
                "token_usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }
        
        # Estimate token usage
        token_usage = self.estimate_token_usage(script_definition)
        
        # Calculate costs
        input_cost = (token_usage["prompt_tokens"] / 1000) * model_config.get("input_cost_per_1k", 0)
        output_cost = (token_usage["completion_tokens"] / 1000) * model_config.get("output_cost_per_1k", 0)
        total_cost = input_cost + output_cost
        
        # Check if it exceeds the model's context length
        max_context = model_config.get("max_context_length", float('inf'))
        exceeds_context = token_usage["total_tokens"] > max_context
        
        return {
            "provider": provider_name,
            "model": model_name,
            "token_usage": token_usage,
            "costs": {
                "input_cost": round(input_cost, 6),
                "output_cost": round(output_cost, 6),
                "total_cost": round(total_cost, 6)
            },
            "exceeds_context": exceeds_context,
            "max_context_length": max_context,
            "context_utilization_percentage": round((token_usage["total_tokens"] / max_context) * 100, 2) if max_context else 0
        }
    
    def estimate_token_usage(self, script_definition: Dict[str, Any]) -> Dict[str, int]:
        """
        Estimate token usage for a script definition
        
        Args:
            script_definition: Dictionary defining the script requirements
            
        Returns:
            Dictionary containing token usage estimates
        """
        # Check cache first
        cache_key = json.dumps(script_definition, sort_keys=True)
        if cache_key in self.token_estimate_cache:
            return self.token_estimate_cache[cache_key]
        
        # Extract relevant information
        script_name = script_definition.get("name", "")
        description = script_definition.get("description", "")
        requirements = script_definition.get("requirements", [])
        
        # Estimate complexity factor (1-2 scale)
        complexity_factor = self._estimate_complexity_factor(description, requirements)
        
        # Estimate prompt tokens
        prompt_text = description + " " + " ".join(requirements)
        token_constants = self.pricing_config.get("token_constants", {})
        avg_tokens_per_word = token_constants.get("avg_tokens_per_word", 1.3)
        
        prompt_tokens = int(len(prompt_text.split()) * avg_tokens_per_word)
        
        # Add tokens for schema and formatting
        prompt_tokens += 200  # Base overhead for formatting
        
        # Estimate output tokens based on requirements and complexity
        completion_tokens = self._estimate_completion_tokens(script_name, requirements, complexity_factor)
        
        # Apply buffer based on config
        buffer_percentage = self.pricing_config.get("estimation_factors", {}).get("token_buffer_percentage", 15)
        prompt_tokens = int(prompt_tokens * (1 + buffer_percentage / 100))
        completion_tokens = int(completion_tokens * (1 + buffer_percentage / 100))
        
        result = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens
        }
        
        # Cache the result
        self.token_estimate_cache[cache_key] = result
        
        return result
    
    def _estimate_complexity_factor(self, description: str, requirements: List[str]) -> float:
        """
        Estimate a complexity factor for the script based on description and requirements
        
        Args:
            description: Script description
            requirements: List of script requirements
            
        Returns:
            Complexity factor (1.0-2.0 scale)
        """
        complexity = 1.0
        
        # Check text length
        description_length = len(description.split())
        if description_length > 300:
            complexity += 0.3
        elif description_length > 150:
            complexity += 0.15
        
        # Check number of requirements
        if len(requirements) > 15:
            complexity += 0.3
        elif len(requirements) > 8:
            complexity += 0.15
        
        # Look for complexity indicators in text
        complexity_indicators = [
            "database", "concurrency", "parallel", "async", "threading", 
            "distributed", "security", "encryption", "authentication",
            "algorithm", "optimization", "machine learning", "neural",
            "scalable", "high performance", "real-time", "streaming",
            "validation", "complex", "interface", "multilayer"
        ]
        
        combined_text = (description + " " + " ".join(requirements)).lower()
        
        for indicator in complexity_indicators:
            if indicator in combined_text:
                complexity += 0.05
        
        # Cap at 2.0
        return min(2.0, complexity)
    
    def _estimate_completion_tokens(self, script_name: str, requirements: List[str], complexity_factor: float) -> int:
        """
        Estimate the number of tokens needed for script completion
        
        Args:
            script_name: Name of the script
            requirements: List of script requirements
            complexity_factor: Complexity factor (1.0-2.0 scale)
            
        Returns:
            Estimated number of completion tokens
        """
        # Base number of lines based on number of requirements
        base_lines = 10 + (len(requirements) * 7)
        
        # Apply complexity factor
        estimated_lines = int(base_lines * complexity_factor)
        
        # Determine language from script name
        token_constants = self.pricing_config.get("token_constants", {})
        if script_name.endswith(".py"):
            tokens_per_line = token_constants.get("avg_tokens_per_line_python", 8.5)
        elif script_name.endswith(".js") or script_name.endswith(".ts"):
            tokens_per_line = token_constants.get("avg_tokens_per_line_javascript", 10.2)
        elif script_name.endswith(".html"):
            tokens_per_line = token_constants.get("avg_tokens_per_line_html", 12.0)
        else:
            tokens_per_line = token_constants.get("avg_tokens_per_line_python", 8.5)  # Default to Python
        
        # Calculate estimated tokens
        return int(estimated_lines * tokens_per_line)
    
    def compare_model_costs(self, script_definition: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Compare costs across different models for the same script definition
        
        Args:
            script_definition: Dictionary defining the script requirements
            
        Returns:
            List of dictionaries containing cost estimates for each model
        """
        results = []
        
        for provider_name, provider_config in self.pricing_config.get("providers", {}).items():
            for model_name in provider_config.get("models", {}):
                # Skip if model is deprecated or not recommended
                model_info = provider_config.get("models", {}).get(model_name, {})
                if model_info.get("deprecated", False):
                    continue
                
                # Get estimate
                estimate = self.estimate_script_cost(
                    script_definition,
                    provider_name=provider_name,
                    model_name=model_name
                )
                
                results.append({
                    "provider": provider_name,
                    "model": model_name,
                    "costs": estimate["costs"],
                    "token_usage": estimate["token_usage"],
                    "exceeds_context": estimate["exceeds_context"],
                    "rank_value": self._calculate_cost_performance_rank(estimate, model_info)
                })
        
        # Sort by rank value (higher is better)
        results.sort(key=lambda x: x["rank_value"], reverse=True)
        return results
    
    def _calculate_cost_performance_rank(self, estimate: Dict[str, Any], model_info: Dict[str, Any]) -> float:
        """
        Calculate a cost-performance rank value for model comparison
        
        Args:
            estimate: Cost estimate for a model
            model_info: Model information from config
            
        Returns:
            Rank value (higher is better)
        """
        # If model exceeds context, it gets a very low rank
        if estimate["exceeds_context"]:
            return 0.0
        
        # Base score from cost efficiency (higher is better)
        # Inverse of cost to make higher better
        cost = estimate["costs"]["total_cost"]
        if cost <= 0:
            cost_score = 100.0  # Avoid division by zero
        else:
            cost_score = 1.0 / cost
        
        # Adjust by context utilization (penalize if using too much of context)
        context_percent = estimate["context_utilization_percentage"]
        context_score = 1.0
        if context_percent > 80:
            # Penalize if using more than 80% of context
            context_score = 0.5
        elif context_percent > 95:
            # Heavy penalty if close to max context
            context_score = 0.1
        
        # Give a quality bonus based on model tier
        quality_bonus = model_info.get("quality_factor", 1.0)
        
        # Calculate final rank
        return cost_score * context_score * quality_bonus * 100.0  # Scale to reasonable number
    
    def estimate_project_cost(self, 
                             script_definitions: List[Dict[str, Any]], 
                             provider_name: Optional[str] = None,
                             model_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Estimate token usage and cost for generating multiple scripts
        
        Args:
            script_definitions: List of script definitions
            provider_name: Name of the AI provider
            model_name: Name of the specific model
            
        Returns:
            Dictionary containing token usage and cost estimates for the project
        """
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_cost = 0.0
        script_estimates = []
        
        for script_def in script_definitions:
            estimate = self.estimate_script_cost(script_def, provider_name, model_name)
            
            total_prompt_tokens += estimate["token_usage"]["prompt_tokens"]
            total_completion_tokens += estimate["token_usage"]["completion_tokens"]
            total_cost += estimate["costs"]["total_cost"]
            
            script_estimates.append({
                "name": script_def.get("name", "unknown"),
                "costs": estimate["costs"],
                "token_usage": estimate["token_usage"],
                "exceeds_context": estimate["exceeds_context"]
            })
        
        return {
            "provider": provider_name,
            "model": model_name,
            "script_count": len(script_definitions),
            "total_costs": round(total_cost, 6),
            "total_token_usage": {
                "prompt_tokens": total_prompt_tokens,
                "completion_tokens": total_completion_tokens,
                "total_tokens": total_prompt_tokens + total_completion_tokens
            },
            "script_estimates": script_estimates
        }
    
    def recommend_cost_efficient_model(self, script_definition: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recommend the most cost-efficient model for a given script
        
        Args:
            script_definition: Dictionary defining the script requirements
            
        Returns:
            Dictionary with recommendation and comparisons
        """
        # Compare all models
        comparisons = self.compare_model_costs(script_definition)
        
        # Get top recommendation
        recommended = comparisons[0] if comparisons else None
        
        # Get top recommendation for each provider
        top_by_provider = {}
        for estimate in comparisons:
            provider = estimate["provider"]
            if provider not in top_by_provider:
                top_by_provider[provider] = estimate
        
        return {
            "recommended_model": recommended["model"] if recommended else None,
            "recommended_provider": recommended["provider"] if recommended else None,
            "estimated_cost": recommended["costs"]["total_cost"] if recommended else 0,
            "comparisons": comparisons,
            "top_by_provider": list(top_by_provider.values())
        }


# Test the cost estimator if run directly
if __name__ == "__main__":
    estimator = CostEstimator()
    
    # Example script definition
    test_definition = {
        "name": "data_processor.py",
        "description": "A data processing script that handles CSV and JSON data. It should clean the data, perform transformations, and output the results to a specified format. The script needs to handle large files efficiently and provide progress indicators.",
        "requirements": [
            "Support CSV and JSON input formats",
            "Clean data by removing duplicates and handling missing values",
            "Transform data using user-defined functions",
            "Support output to CSV, JSON, and SQL formats",
            "Provide progress indicators for long-running operations",
            "Implement efficient memory management for large files",
            "Include error handling and logging"
        ]
    }
    
    # Estimate costs for different models
    print("Claude Estimate:")
    claude_estimate = estimator.estimate_script_cost(test_definition, "claude")
    print(json.dumps(claude_estimate, indent=2))
    
    print("\nGPT Estimate:")
    gpt_estimate = estimator.estimate_script_cost(test_definition, "openai")
    print(json.dumps(gpt_estimate, indent=2))
    
    # Get recommendation
    print("\nRecommendation:")
    recommendation = estimator.recommend_cost_efficient_model(test_definition)
    print(f"Recommended model: {recommendation['recommended_provider']} / {recommendation['recommended_model']}")
    print(f"Estimated cost: ${recommendation['estimated_cost']:.6f}")
