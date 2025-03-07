"""
Script Planner
Module for script complexity estimation and decomposition planning
"""

import os
import re
import ast
import json
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path


class ScriptPlanner:
    """
    Plans script generation by estimating complexity and determining optimal decomposition
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the script planner
        
        Args:
            config: Configuration dictionary with planner settings
        """
        self.config = config or {}
        
    def analyze_script_definition(self, script_definition: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a script definition to determine complexity and recommend decomposition
        
        Args:
            script_definition: Dictionary defining the script requirements
            
        Returns:
            Dictionary containing analysis results and decomposition plan
        """
        # Extract key information
        script_name = script_definition.get("name", "")
        description = script_definition.get("description", "")
        requirements = script_definition.get("requirements", [])
        
        # Analyze complexity
        complexity = self.estimate_complexity(description, requirements)
        
        # Determine if decomposition is needed
        decomposition_threshold = self.config.get("decomposition", {}).get("complexity_threshold", 7.0)
        needs_decomposition = complexity > decomposition_threshold
        
        # Create decomposition plan if needed
        components = []
        if needs_decomposition:
            components = self.plan_decomposition(script_definition, complexity)
        
        return {
            "name": script_name,
            "complexity": complexity,
            "needs_decomposition": needs_decomposition,
            "components": components,
            "estimated_tokens": self.estimate_tokens(description, requirements),
            "recommended_models": self.recommend_models(complexity),
            "generation_hints": self.generate_hints(script_definition)
        }
    
    def estimate_complexity(self, description: str, requirements: List[str]) -> float:
        """
        Estimate the complexity of a script based on its description and requirements
        
        Args:
            description: Script description
            requirements: List of script requirements
            
        Returns:
            Float representing complexity score (1-10)
        """
        complexity = 1.0  # Base complexity
        
        # Analyze description length
        description_length = len(description.split())
        if description_length > 300:
            complexity += 2.0
        elif description_length > 150:
            complexity += 1.0
        
        # Analyze number of requirements
        if len(requirements) > 15:
            complexity += 2.0
        elif len(requirements) > 8:
            complexity += 1.0
        
        # Look for complexity indicators in text
        complexity_indicators = [
            "database", "concurrency", "parallel", "async", "threading", 
            "distributed", "security", "encryption", "authentication",
            "machine learning", "neural", "optimization", "algorithm",
            "scalable", "high performance", "real-time", "streaming",
            "transaction", "validation", "complex"
        ]
        
        combined_text = description + " " + " ".join(requirements)
        combined_text = combined_text.lower()
        
        for indicator in complexity_indicators:
            if indicator in combined_text:
                complexity += 0.5
        
        # Cap complexity score at 10
        return min(10.0, complexity)
    
    def estimate_tokens(self, description: str, requirements: List[str]) -> Dict[str, int]:
        """
        Estimate the token usage for script generation
        
        Args:
            description: Script description
            requirements: List of script requirements
            
        Returns:
            Dictionary with token estimates for prompt and completion
        """
        # Simple token estimation - approximately 1.3 tokens per word
        prompt_text = description + " " + " ".join(requirements)
        prompt_tokens = int(len(prompt_text.split()) * 1.3)
        
        # Estimate completion tokens based on prompt size and complexity
        complexity = self.estimate_complexity(description, requirements)
        completion_tokens = int(prompt_tokens * (0.8 + (complexity * 0.2)))
        
        return {
            "prompt_tokens": prompt_tokens,
            "estimated_completion_tokens": completion_tokens,
            "total_estimated_tokens": prompt_tokens + completion_tokens
        }
    
    def recommend_models(self, complexity: float) -> List[Dict[str, Any]]:
        """
        Recommend suitable AI models based on script complexity
        
        Args:
            complexity: Complexity score of the script
            
        Returns:
            List of recommended models with confidence scores
        """
        # Define model capabilities based on complexity
        model_capabilities = {
            "claude-3-7-sonnet-20250219": {
                "max_complexity": 10.0,
                "strength": "comprehensive reasoning",
                "confidence_factor": 0.95
            },
            "claude-3-opus-20240229": {
                "max_complexity": 10.0,
                "strength": "detailed code generation",
                "confidence_factor": 0.9
            },
            "gpt-4o": {
                "max_complexity": 9.0,
                "strength": "versatile implementation",
                "confidence_factor": 0.85
            },
            "deepseek-coder": {
                "max_complexity": 8.5,
                "strength": "efficient algorithms",
                "confidence_factor": 0.8
            },
            "claude-3-5-haiku-20240620": {
                "max_complexity": 7.0,
                "strength": "rapid generation",
                "confidence_factor": 0.75
            },
            "gpt-3.5-turbo": {
                "max_complexity": 6.5,
                "strength": "simple implementations",
                "confidence_factor": 0.7
            }
        }
        
        recommendations = []
        
        for model, capabilities in model_capabilities.items():
            # Skip models that can't handle this complexity
            if complexity > capabilities["max_complexity"]:
                continue
                
            # Calculate confidence score
            confidence = capabilities["confidence_factor"]
            
            # Adjust confidence based on complexity match
            complexity_match = 1.0 - (abs(complexity - capabilities["max_complexity"]) / 10.0)
            confidence = confidence * (0.7 + (complexity_match * 0.3))
            
            # Add to recommendations
            recommendations.append({
                "model": model,
                "provider": self._get_provider_for_model(model),
                "confidence": round(confidence, 2),
                "strength": capabilities["strength"],
                "suitable_for_complexity": complexity <= capabilities["max_complexity"]
            })
        
        # Sort by confidence
        recommendations.sort(key=lambda x: x["confidence"], reverse=True)
        
        return recommendations
    
    def _get_provider_for_model(self, model: str) -> str:
        """Get the provider name for a given model"""
        if model.startswith("claude"):
            return "claude"
        elif model.startswith("gpt"):
            return "openai"
        elif model.startswith("deepseek"):
            return "deepseek"
        else:
            return "unknown"
    
    def plan_decomposition(self, script_definition: Dict[str, Any], complexity: float) -> List[Dict[str, Any]]:
        """
        Plan the decomposition of a complex script into smaller components
        
        Args:
            script_definition: Dictionary defining the script requirements
            complexity: Complexity score of the script
            
        Returns:
            List of component definitions
        """
        # Extract information
        script_name = script_definition.get("name", "")
        description = script_definition.get("description", "")
        requirements = script_definition.get("requirements", [])
        
        # Analyze requirements and description to identify logical components
        components = self._identify_components(description, requirements)
        
        # If no clear components are identified, use a standard template
        if not components:
            components = self._apply_template_decomposition(script_definition, complexity)
        
        return components
    
    def _identify_components(self, description: str, requirements: List[str]) -> List[Dict[str, Any]]:
        """
        Identify logical components from description and requirements
        
        Args:
            description: Script description
            requirements: List of script requirements
            
        Returns:
            List of identified components
        """
        components = []
        combined_text = description + " " + " ".join(requirements)
        
        # Look for component indicators
        component_patterns = [
            # Pattern: "X component/module that handles/manages Y"
            r'(\w+(?:\s+\w+){0,3})\s+(?:component|module|class|service|utility|handler|manager)\s+that\s+(?:handles|manages|provides|implements)\s+(.*?)(?:\.|\n|$)',
            
            # Pattern: "X functionality for Y"
            r'(\w+(?:\s+\w+){0,3})\s+functionality\s+for\s+(.*?)(?:\.|\n|$)',
            
            # Pattern: "X interface to Y"
            r'(\w+(?:\s+\w+){0,3})\s+interface\s+to\s+(.*?)(?:\.|\n|$)',
        ]
        
        # Extract component candidates
        component_candidates = set()
        for pattern in component_patterns:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            for match in matches:
                component = match[0].strip()
                purpose = match[1].strip()
                component_candidates.add((component, purpose))
        
        # Create component definitions
        for index, (component, purpose) in enumerate(component_candidates):
            clean_name = component.replace(" ", "_").lower()
            components.append({
                "id": f"component_{index}",
                "name": f"{clean_name}",
                "type": "class",
                "description": f"{component} that handles {purpose}",
                "requirements": self._filter_requirements_for_component(component, purpose, requirements)
            })
        
        return components
    
    def _filter_requirements_for_component(self, component: str, purpose: str, requirements: List[str]) -> List[str]:
        """Filter requirements relevant to a specific component"""
        relevant_requirements = []
        component_words = set(component.lower().split())
        purpose_words = set(purpose.lower().split())
        
        for req in requirements:
            req_lower = req.lower()
            
            # Check if requirement mentions component or purpose
            if any(word in req_lower for word in component_words) or any(word in req_lower for word in purpose_words):
                relevant_requirements.append(req)
            
        return relevant_requirements
    
    def _apply_template_decomposition(self, script_definition: Dict[str, Any], complexity: float) -> List[Dict[str, Any]]:
        """
        Apply a template-based decomposition when no clear components are identified
        
        Args:
            script_definition: Dictionary defining the script requirements
            complexity: Complexity score of the script
            
        Returns:
            List of template-based components
        """
        script_name = script_definition.get("name", "")
        base_name = os.path.splitext(script_name)[0]
        
        # Simple template based on script type
        if "api" in script_name.lower() or "service" in script_name.lower():
            # API/Service template
            return [
                {
                    "id": "component_0",
                    "name": f"{base_name}_core",
                    "type": "core",
                    "description": f"Core implementation of {base_name} functionality",
                    "is_primary": True
                },
                {
                    "id": "component_1",
                    "name": f"{base_name}_api",
                    "type": "interface",
                    "description": f"API interface for {base_name}",
                    "is_primary": False,
                    "depends_on": ["component_0"]
                },
                {
                    "id": "component_2",
                    "name": f"{base_name}_utils",
                    "type": "utility",
                    "description": f"Utility functions for {base_name}",
                    "is_primary": False
                }
            ]
        elif "cli" in script_name.lower() or "command" in script_name.lower():
            # CLI tool template
            return [
                {
                    "id": "component_0",
                    "name": f"{base_name}_core",
                    "type": "core",
                    "description": f"Core implementation of {base_name} functionality",
                    "is_primary": True
                },
                {
                    "id": "component_1",
                    "name": f"{base_name}_cli",
                    "type": "interface",
                    "description": f"Command-line interface for {base_name}",
                    "is_primary": False,
                    "depends_on": ["component_0"]
                },
                {
                    "id": "component_2",
                    "name": f"{base_name}_utils",
                    "type": "utility",
                    "description": f"Utility functions for {base_name}",
                    "is_primary": False
                }
            ]
        else:
            # Generic template
            num_components = min(5, max(2, int(complexity / 2)))
            components = [
                {
                    "id": "component_0",
                    "name": f"{base_name}_main",
                    "type": "main",
                    "description": f"Main implementation of {base_name}",
                    "is_primary": True
                }
            ]
            
            for i in range(1, num_components):
                component_type = ["helper", "utility", "handler", "processor", "manager"][i % 5]
                components.append({
                    "id": f"component_{i}",
                    "name": f"{base_name}_{component_type}",
                    "type": component_type,
                    "description": f"{component_type.capitalize()} functions for {base_name}",
                    "is_primary": False,
                    "depends_on": ["component_0"] if i > 1 else []
                })
                
            return components
    
    def generate_hints(self, script_definition: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate hints for script generation
        
        Args:
            script_definition: Dictionary defining the script requirements
            
        Returns:
            Dictionary containing generation hints
        """
        # Extract information
        script_name = script_definition.get("name", "")
        description = script_definition.get("description", "")
        requirements = script_definition.get("requirements", [])
        combined_text = description + " " + " ".join(requirements)
        combined_text = combined_text.lower()
        
        # Detect patterns and provide hints
        hints = {}
        
        # Detect language
        if script_name.endswith(".py") or "python" in combined_text:
            hints["language"] = "python"
        elif script_name.endswith(".js") or "javascript" in combined_text:
            hints["language"] = "javascript"
        elif script_name.endswith(".ts") or "typescript" in combined_text:
            hints["language"] = "typescript"
        else:
            hints["language"] = "python"  # Default to Python
        
        # Detect paradigm
        if "class" in combined_text or "object" in combined_text or "oop" in combined_text:
            hints["paradigm"] = "object-oriented"
        elif "functional" in combined_text:
            hints["paradigm"] = "functional"
        else:
            hints["paradigm"] = "mixed"
        
        # Detect testing needs
        if "test" in combined_text or "unittest" in combined_text or "pytest" in combined_text:
            hints["include_tests"] = True
        else:
            hints["include_tests"] = False
        
        # Detect comment level
        if "document" in combined_text or "documentation" in combined_text:
            hints["comment_level"] = "high"
        else:
            hints["comment_level"] = "normal"
        
        # Detect error handling approach
        if "exception" in combined_text or "error handling" in combined_text:
            hints["error_handling"] = "extensive"
        else:
            hints["error_handling"] = "standard"
        
        return hints


# Test the planner if run directly
if __name__ == "__main__":
    planner = ScriptPlanner()
    
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
    
    result = planner.analyze_script_definition(test_definition)
    print(json.dumps(result, indent=2))
