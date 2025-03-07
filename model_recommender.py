"""
Model Recommender
Module for recommending appropriate AI models for script generation
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
import math

# Setup logging
logger = logging.getLogger(__name__)


class ModelRecommender:
    """
    Recommends appropriate AI models for script generation based on
    script characteristics, historical performance, and preferences
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the model recommender
        
        Args:
            config_path: Path to the models configuration file
        """
        self.models_config = self._load_models_config(config_path)
        self.performance_history = {}
    
    def _load_models_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """
        Load models configuration from file
        
        Args:
            config_path: Path to the models configuration file
            
        Returns:
            Dictionary containing models configuration
        """
        default_config = {
            "providers": {
                "claude": {
                    "models": {
                        "claude-3-opus-20240229": {
                            "strengths": ["complex reasoning", "creative writing", "long context", "instruction following"],
                            "weaknesses": ["mathematical calculations", "very specific formatting"],
                            "complexity_range": [7, 10],
                            "context_length": 200000,
                            "quality_factor": 0.9,
                            "speed_factor": 0.7,
                            "cost_factor": 0.5  # Higher is more cost-effective
                        },
                        "claude-3-7-sonnet-20250219": {
                            "strengths": ["balanced performance", "code generation", "long context", "reasoning"],
                            "weaknesses": ["complex mathematical proofs"],
                            "complexity_range": [4, 9],
                            "context_length": 200000,
                            "quality_factor": 0.85,
                            "speed_factor": 0.8,
                            "cost_factor": 0.7
                        },
                        "claude-3-5-haiku-20240620": {
                            "strengths": ["speed", "simple tasks", "basic code", "shorter outputs"],
                            "weaknesses": ["very complex tasks", "research-level problems"],
                            "complexity_range": [1, 7],
                            "context_length": 200000,
                            "quality_factor": 0.7,
                            "speed_factor": 0.95,
                            "cost_factor": 0.9
                        }
                    }
                },
                "openai": {
                    "models": {
                        "gpt-4o": {
                            "strengths": ["balanced performance", "code generation", "instruction following", "math"],
                            "weaknesses": [],
                            "complexity_range": [3, 9],
                            "context_length": 128000,
                            "quality_factor": 0.88,
                            "speed_factor": 0.82,
                            "cost_factor": 0.75
                        },
                        "gpt-4-turbo": {
                            "strengths": ["complex reasoning", "code generation", "math"],
                            "weaknesses": ["sometimes verbose"],
                            "complexity_range": [5, 9],
                            "context_length": 128000,
                            "quality_factor": 0.85,
                            "speed_factor": 0.75,
                            "cost_factor": 0.6
                        },
                        "gpt-3.5-turbo": {
                            "strengths": ["speed", "simple code", "summarization"],
                            "weaknesses": ["complex reasoning", "nuanced tasks"],
                            "complexity_range": [1, 6],
                            "context_length": 16384,
                            "quality_factor": 0.65,
                            "speed_factor": 0.9,
                            "cost_factor": 0.95
                        }
                    }
                },
                "deepseek": {
                    "models": {
                        "deepseek-coder": {
                            "strengths": ["code generation", "algorithms", "technical documentation"],
                            "weaknesses": ["creative writing", "conversational tasks"],
                            "complexity_range": [3, 8],
                            "context_length": 32768,
                            "quality_factor": 0.8,
                            "speed_factor": 0.8,
                            "cost_factor": 0.8
                        }
                    }
                }
            },
            "task_categories": {
                "code_generation": {
                    "keywords": ["code", "script", "function", "class", "algorithm", "implement"],
                    "preferred_models": ["deepseek-coder", "gpt-4o", "claude-3-7-sonnet-20250219"]
                },
                "data_processing": {
                    "keywords": ["data", "csv", "json", "parse", "transform", "clean", "format"],
                    "preferred_models": ["claude-3-7-sonnet-20250219", "gpt-4o", "deepseek-coder"]
                },
                "web_development": {
                    "keywords": ["html", "css", "javascript", "web", "frontend", "backend", "api"],
                    "preferred_models": ["gpt-4o", "claude-3-7-sonnet-20250219", "deepseek-coder"]
                },
                "database": {
                    "keywords": ["sql", "database", "query", "schema", "orm", "nosql", "mongodb"],
                    "preferred_models": ["gpt-4o", "claude-3-7-sonnet-20250219", "deepseek-coder"]
                },
                "system_script": {
                    "keywords": ["system", "shell", "bash", "command", "script", "automation"],
                    "preferred_models": ["claude-3-7-sonnet-20250219", "gpt-4o", "deepseek-coder"]
                },
                "documentation": {
                    "keywords": ["document", "readme", "documentation", "comment", "explain"],
                    "preferred_models": ["claude-3-opus-20240229", "claude-3-7-sonnet-20250219", "gpt-4o"]
                }
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
                logger.error(f"Error loading models configuration from {config_path}: {e}")
                logger.info("Using default models configuration")
        
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
    
    def recommend_model(self, script_definition: Dict[str, Any], 
                       provider_preference: Optional[str] = None) -> Dict[str, Any]:
        """
        Recommend an appropriate model for a script definition
        
        Args:
            script_definition: Dictionary defining the script requirements
            provider_preference: Optional preferred provider name
            
        Returns:
            Dictionary with recommendation details
        """
        # Analyze script characteristics
        script_analysis = self._analyze_script(script_definition)
        
        # Get appropriate models based on complexity
        complexity = script_analysis["complexity"]
        complexity_matches = self._get_models_by_complexity(complexity)
        
        # Get appropriate models based on task category
        category_matches = self._get_models_by_category(script_analysis["categories"])
        
        # Combine results with appropriate weights
        final_scores = self._calculate_final_scores(
            complexity_matches, 
            category_matches,
            script_analysis,
            provider_preference
        )
        
        # Sort models by score
        sorted_models = sorted(final_scores.items(), key=lambda x: x[1]["score"], reverse=True)
        
        # Group recommendations by provider
        provider_recommendations = {}
        for model, details in sorted_models:
            provider = self._get_provider_for_model(model)
            if provider not in provider_recommendations:
                provider_recommendations[provider] = []
            provider_recommendations[provider].append({
                "model": model,
                "score": details["score"],
                "details": details
            })
        
        # Get top overall recommendation
        top_model, top_details = sorted_models[0] if sorted_models else (None, None)
        
        if top_model is None:
            return {
                "recommended_model": None,
                "recommended_provider": None,
                "score": 0,
                "details": {},
                "analysis": script_analysis,
                "all_models": [],
                "provider_recommendations": {}
            }
        
        return {
            "recommended_model": top_model,
            "recommended_provider": self._get_provider_for_model(top_model),
            "score": top_details["score"],
            "details": top_details,
            "analysis": script_analysis,
            "all_models": sorted_models,
            "provider_recommendations": provider_recommendations
        }
    
    def _analyze_script(self, script_definition: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a script definition to extract relevant characteristics
        
        Args:
            script_definition: Dictionary defining the script requirements
            
        Returns:
            Dictionary with script analysis
        """
        script_name = script_definition.get("name", "")
        description = script_definition.get("description", "")
        requirements = script_definition.get("requirements", [])
        
        # Combine text for analysis
        combined_text = f"{script_name} {description} {' '.join(requirements)}".lower()
        word_count = len(combined_text.split())
        
        # Estimate complexity (1-10 scale)
        complexity = self._estimate_complexity(script_definition)
        
        # Identify script categories
        categories = self._identify_categories(combined_text)
        
        # Identify required strengths
        required_strengths = self._identify_required_strengths(combined_text)
        
        # Identify file type
        file_extension = os.path.splitext(script_name)[1].lower() if script_name else ""
        
        return {
            "complexity": complexity,
            "categories": categories,
            "required_strengths": required_strengths,
            "word_count": word_count,
            "file_extension": file_extension
        }
    
    def _estimate_complexity(self, script_definition: Dict[str, Any]) -> float:
        """
        Estimate the complexity of a script based on its definition
        
        Args:
            script_definition: Dictionary defining the script requirements
            
        Returns:
            Complexity score (1-10 scale)
        """
        description = script_definition.get("description", "")
        requirements = script_definition.get("requirements", [])
        
        complexity = 1.0  # Base complexity
        
        # Check text length
        description_length = len(description.split())
        if description_length > 300:
            complexity += 2.0
        elif description_length > 150:
            complexity += 1.0
        
        # Check number of requirements
        if len(requirements) > 15:
            complexity += 2.0
        elif len(requirements) > 8:
            complexity += 1.0
        
        # Look for complexity indicators in text
        complexity_indicators = {
            "database": 0.5,
            "concurrent": 0.8,
            "parallel": 0.8,
            "async": 0.7,
            "threading": 0.7,
            "distributed": 0.9,
            "security": 0.6,
            "encryption": 0.7,
            "authentication": 0.6,
            "algorithm": 0.5,
            "optimization": 0.6,
            "machine learning": 0.9,
            "neural": 0.9,
            "scalable": 0.5,
            "high performance": 0.7,
            "real-time": 0.6,
            "streaming": 0.6,
            "complex": 0.5
        }
        
        combined_text = (description + " " + " ".join(requirements)).lower()
        
        for indicator, value in complexity_indicators.items():
            if indicator in combined_text:
                complexity += value
        
        # Cap complexity at 10
        return min(10.0, complexity)
    
    def _identify_categories(self, text: str) -> List[Tuple[str, float]]:
        """
        Identify script categories based on text
        
        Args:
            text: Text to analyze
            
        Returns:
            List of (category, confidence) tuples
        """
        categories = []
        
        for category, details in self.models_config.get("task_categories", {}).items():
            keywords = details.get("keywords", [])
            matched_keywords = sum(1 for keyword in keywords if keyword in text)
            
            if matched_keywords > 0:
                # Calculate confidence based on percentage of matched keywords
                confidence = matched_keywords / len(keywords) if keywords else 0
                categories.append((category, confidence))
        
        # Sort by confidence
        categories.sort(key=lambda x: x[1], reverse=True)
        
        return categories
    
    def _identify_required_strengths(self, text: str) -> List[str]:
        """
        Identify required model strengths based on text
        
        Args:
            text: Text to analyze
            
        Returns:
            List of required strengths
        """
        # Compile all possible strengths from model definitions
        all_strengths = set()
        for provider_details in self.models_config.get("providers", {}).values():
            for model_details in provider_details.get("models", {}).values():
                strengths = model_details.get("strengths", [])
                all_strengths.update(strengths)
        
        # Check which strengths are mentioned in the text
        required_strengths = []
        for strength in all_strengths:
            # Convert to simple keywords for matching
            keywords = strength.lower().split()
            
            # Check if all keywords in the strength are in the text
            if all(keyword in text for keyword in keywords):
                required_strengths.append(strength)
        
        return required_strengths
    
    def _get_models_by_complexity(self, complexity: float) -> Dict[str, float]:
        """
        Get appropriate models based on complexity
        
        Args:
            complexity: Complexity score (1-10 scale)
            
        Returns:
            Dictionary mapping model names to match scores
        """
        matches = {}
        
        for provider, provider_details in self.models_config.get("providers", {}).items():
            for model, model_details in provider_details.get("models", {}).items():
                # Get complexity range for this model
                min_complexity, max_complexity = model_details.get("complexity_range", [1, 10])
                
                # Calculate match score based on how well the complexity fits within the range
                if complexity < min_complexity:
                    # Script is simpler than model's optimal range
                    match_score = 1.0 - (min_complexity - complexity) / min_complexity
                elif complexity > max_complexity:
                    # Script is more complex than model's optimal range
                    match_score = 1.0 - (complexity - max_complexity) / (10 - max_complexity)
                else:
                    # Script complexity is within model's optimal range
                    # Higher score for being in the middle of the range
                    range_width = max_complexity - min_complexity
                    if range_width == 0:
                        relative_position = 0.5  # Avoid division by zero
                    else:
                        relative_position = (complexity - min_complexity) / range_width
                    
                    # Highest score when in the middle of the range
                    match_score = 1.0 - 2 * abs(relative_position - 0.5)
                
                # Ensure score is between 0 and 1
                match_score = max(0.0, min(1.0, match_score))
                
                matches[model] = match_score
        
        return matches
    
    def _get_models_by_category(self, categories: List[Tuple[str, float]]) -> Dict[str, float]:
        """
        Get appropriate models based on script categories
        
        Args:
            categories: List of (category, confidence) tuples
            
        Returns:
            Dictionary mapping model names to match scores
        """
        matches = {}
        
        if not categories:
            # No identified categories, all models get a neutral score
            for provider, provider_details in self.models_config.get("providers", {}).items():
                for model in provider_details.get("models", {}):
                    matches[model] = 0.5
            return matches
        
        # Get preferred models for each category
        for category, confidence in categories:
            category_details = self.models_config.get("task_categories", {}).get(category, {})
            preferred_models = category_details.get("preferred_models", [])
            
            # Assign scores to preferred models based on their order and confidence
            for i, model in enumerate(preferred_models):
                position_score = 1.0 - (i / len(preferred_models)) if preferred_models else 0
                category_score = position_score * confidence
                
                if model in matches:
                    # Take the maximum score across categories
                    matches[model] = max(matches[model], category_score)
                else:
                    matches[model] = category_score
        
        # Assign a base score to models not explicitly preferred
        all_models = []
        for provider, provider_details in self.models_config.get("providers", {}).items():
            all_models.extend(provider_details.get("models", {}).keys())
        
        for model in all_models:
            if model not in matches:
                matches[model] = 0.3  # Base score for non-preferred models
        
        return matches
    
    def _calculate_final_scores(self, 
                              complexity_matches: Dict[str, float], 
                              category_matches: Dict[str, float],
                              script_analysis: Dict[str, Any],
                              provider_preference: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Calculate final scores for models
        
        Args:
            complexity_matches: Dictionary mapping models to complexity match scores
            category_matches: Dictionary mapping models to category match scores
            script_analysis: Script analysis results
            provider_preference: Optional preferred provider
            
        Returns:
            Dictionary mapping models to score details
        """
        final_scores = {}
        
        # Weights for different factors
        weights = {
            "complexity": 0.25,
            "category": 0.25,
            "strengths": 0.20,
            "quality": 0.15,
            "speed": 0.05,
            "cost": 0.10
        }
        
        required_strengths = set(script_analysis.get("required_strengths", []))
        
        for provider, provider_details in self.models_config.get("providers", {}).items():
            for model, model_details in provider_details.get("models", {}).items():
                # Skip if the model isn't in both matches (shouldn't happen)
                if model not in complexity_matches or model not in category_matches:
                    continue
                
                # Get base scores
                complexity_score = complexity_matches[model]
                category_score = category_matches[model]
                
                # Calculate strength match score
                model_strengths = set(model_details.get("strengths", []))
                if required_strengths and model_strengths:
                    strength_match = len(required_strengths.intersection(model_strengths)) / len(required_strengths)
                else:
                    strength_match = 0.5  # Neutral if no strengths required or defined
                
                # Get quality, speed, and cost factors
                quality_factor = model_details.get("quality_factor", 0.5)
                speed_factor = model_details.get("speed_factor", 0.5)
                cost_factor = model_details.get("cost_factor", 0.5)
                
                # Check if context length is sufficient
                context_length = model_details.get("context_length", 0)
                word_count = script_analysis.get("word_count", 0)
                estimated_tokens = word_count * 1.3  # Rough estimate
                
                context_sufficient = context_length > estimated_tokens * 2  # 2x safety factor
                
                # Calculate weighted score
                weighted_score = (
                    weights["complexity"] * complexity_score +
                    weights["category"] * category_score +
                    weights["strengths"] * strength_match +
                    weights["quality"] * quality_factor +
                    weights["speed"] * speed_factor +
                    weights["cost"] * cost_factor
                )
                
                # Apply provider preference bonus
                if provider_preference and provider == provider_preference:
                    weighted_score *= 1.2  # 20% bonus for preferred provider
                
                # Apply performance history adjustment if available
                history_factor = self._get_performance_history_factor(model)
                weighted_score *= history_factor
                
                # Apply severe penalty if context is insufficient
                if not context_sufficient:
                    weighted_score *= 0.3  # 70% penalty
                
                # Record detailed scores
                final_scores[model] = {
                    "score": weighted_score,
                    "complexity_score": complexity_score,
                    "category_score": category_score,
                    "strength_match": strength_match,
                    "quality_factor": quality_factor,
                    "speed_factor": speed_factor,
                    "cost_factor": cost_factor,
                    "history_factor": history_factor,
                    "context_sufficient": context_sufficient,
                    "provider": provider
                }
        
        return final_scores
    
    def _get_performance_history_factor(self, model: str) -> float:
        """
        Get performance history factor for a model
        
        Args:
            model: Model name
            
        Returns:
            Performance history factor (default 1.0)
        """
        if model not in self.performance_history:
            return 1.0
        
        history = self.performance_history[model]
        
        # Calculate success rate
        total = history.get("success", 0) + history.get("failure", 0)
        if total == 0:
            return 1.0
            
        success_rate = history.get("success", 0) / total
        
        # Map success rate to factor (0.8 to 1.2)
        # 0% success -> 0.8 factor (20% penalty)
        # 100% success -> 1.2 factor (20% bonus)
        return 0.8 + (success_rate * 0.4)
    
    def update_performance_history(self, model: str, success: bool) -> None:
        """
        Update performance history for a model
        
        Args:
            model: Model name
            success: Whether the generation was successful
        """
        if model not in self.performance_history:
            self.performance_history[model] = {
                "success": 0,
                "failure": 0
            }
        
        if success:
            self.performance_history[model]["success"] += 1
        else:
            self.performance_history[model]["failure"] += 1
    
    def get_model_details(self, model: str) -> Dict[str, Any]:
        """
        Get details for a specific model
        
        Args:
            model: Model name
            
        Returns:
            Dictionary with model details
        """
        for provider, provider_details in self.models_config.get("providers", {}).items():
            if model in provider_details.get("models", {}):
                details = provider_details["models"][model].copy()
                details["provider"] = provider
                return details
        
        return {}
    
    def _get_provider_for_model(self, model: str) -> str:
        """
        Get the provider name for a model
        
        Args:
            model: Model name
            
        Returns:
            Provider name or "unknown"
        """
        for provider, provider_details in self.models_config.get("providers", {}).items():
            if model in provider_details.get("models", {}):
                return provider
        
        return "unknown"
    
    def get_all_models(self) -> List[Dict[str, Any]]:
        """
        Get information about all available models
        
        Returns:
            List of dictionaries with model details
        """
        models = []
        
        for provider, provider_details in self.models_config.get("providers", {}).items():
            for model, model_details in provider_details.get("models", {}).items():
                models.append({
                    "name": model,
                    "provider": provider,
                    "strengths": model_details.get("strengths", []),
                    "weaknesses": model_details.get("weaknesses", []),
                    "complexity_range": model_details.get("complexity_range", [1, 10]),
                    "context_length": model_details.get("context_length", 0),
                    "quality_factor": model_details.get("quality_factor", 0.5),
                    "speed_factor": model_details.get("speed_factor", 0.5),
                    "cost_factor": model_details.get("cost_factor", 0.5)
                })
        
        return models


# Test the model recommender if run directly
if __name__ == "__main__":
    recommender = ModelRecommender()
    
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
    
    # Get recommendation
    recommendation = recommender.recommend_model(test_definition)
    
    print("Recommended model:")
    print(f"Model: {recommendation['recommended_model']}")
    print(f"Provider: {recommendation['recommended_provider']}")
    print(f"Score: {recommendation['score']:.4f}")
    
    print("\nScript analysis:")
    for key, value in recommendation["analysis"].items():
        print(f"{key}: {value}")
    
    print("\nTop models by provider:")
    for provider, models in recommendation["provider_recommendations"].items():
        if models:
            top_model = models[0]
            print(f"{provider}: {top_model['model']} (score: {top_model['score']:.4f})")
