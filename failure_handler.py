"""
Failure Handler
Module for detecting and recovering from script generation failures
"""

import os
import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from enum import Enum

# Setup logging
logger = logging.getLogger(__name__)


class FailureType(Enum):
    """Types of script generation failures"""
    CONTEXT_OVERFLOW = "context_overflow"
    SYNTAX_ERROR = "syntax_error"
    TRUNCATED_OUTPUT = "truncated_output"
    MISSING_FEATURE = "missing_feature"
    HALLUCINATION = "hallucination"
    LOW_QUALITY = "low_quality"
    RATE_LIMIT = "rate_limit"
    API_ERROR = "api_error"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class RecoveryStrategy(Enum):
    """Recovery strategies for script generation failures"""
    RETRY = "retry"
    SIMPLIFY = "simplify"
    DECOMPOSE = "decompose"
    CHANGE_MODEL = "change_model"
    CHANGE_PROVIDER = "change_provider"
    HUMAN_ASSISTANCE = "human_assistance"
    ABORT = "abort"


class FailureHandler:
    """
    Handles detection and recovery from script generation failures
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the failure handler
        
        Args:
            config: Configuration dictionary with failure handling settings
        """
        self.config = config or {}
        self.failure_patterns = self._initialize_failure_patterns()
        self.strategy_history = {}
    
    def _initialize_failure_patterns(self) -> Dict[FailureType, List[str]]:
        """
        Initialize patterns for detecting different types of failures
        
        Returns:
            Dictionary mapping failure types to pattern lists
        """
        default_patterns = {
            FailureType.CONTEXT_OVERFLOW: [
                "context length exceeded",
                "maximum context length",
                "token limit exceeded",
                "input is too long",
                "too many tokens",
                "context window full"
            ],
            FailureType.SYNTAX_ERROR: [
                "syntax error",
                "invalid syntax",
                "unexpected token",
                "unexpected end of file",
                "parsing error"
            ],
            FailureType.TRUNCATED_OUTPUT: [
                "output was truncated",
                "incomplete response",
                "unfinished code block",
                "ended abruptly"
            ],
            FailureType.MISSING_FEATURE: [
                "feature not implemented",
                "not supported",
                "capability not available"
            ],
            FailureType.HALLUCINATION: [
                "reference to undefined",
                "non-existent module",
                "unknown library",
                "not a valid"
            ],
            FailureType.RATE_LIMIT: [
                "rate limit exceeded",
                "too many requests",
                "request throttled"
            ],
            FailureType.API_ERROR: [
                "api error",
                "service unavailable",
                "internal server error",
                "bad gateway"
            ],
            FailureType.TIMEOUT: [
                "request timed out",
                "timeout exceeded",
                "connection timed out"
            ]
        }
        
        # Update with config values if available
        custom_patterns = self.config.get("failure_patterns", {})
        for failure_type_str, patterns in custom_patterns.items():
            try:
                failure_type = FailureType(failure_type_str)
                if failure_type in default_patterns:
                    default_patterns[failure_type].extend(patterns)
                else:
                    default_patterns[failure_type] = patterns
            except ValueError:
                logger.warning(f"Unknown failure type: {failure_type_str}")
        
        return default_patterns
    
    def detect_failure(self, script_generation_result: Dict[str, Any]) -> Tuple[bool, Optional[FailureType], Dict[str, Any]]:
        """
        Detect if a script generation has failed and identify the failure type
        
        Args:
            script_generation_result: Result of script generation
            
        Returns:
            Tuple of (is_failure, failure_type, failure_details)
        """
        # Check if the result explicitly indicates failure
        if not script_generation_result.get("success", True):
            error_message = script_generation_result.get("error", "")
            
            # Identify failure type from error message
            failure_type = self._identify_failure_type(error_message)
            
            return True, failure_type, {
                "error_message": error_message,
                "failure_type": failure_type.value if failure_type else None
            }
        
        # Check for implicit failures in the generated script
        script = script_generation_result.get("script", "")
        
        # Check for truncated output
        if self._is_truncated(script):
            return True, FailureType.TRUNCATED_OUTPUT, {
                "error_message": "Generated script appears to be truncated",
                "failure_type": FailureType.TRUNCATED_OUTPUT.value
            }
        
        # Check for hallucinations
        hallucination_details = self._detect_hallucinations(script)
        if hallucination_details["has_hallucinations"]:
            return True, FailureType.HALLUCINATION, {
                "error_message": "Generated script contains hallucinations",
                "failure_type": FailureType.HALLUCINATION.value,
                "hallucination_details": hallucination_details
            }
        
        # Check script quality
        quality_details = self._evaluate_quality(script)
        if not quality_details["meets_minimum_quality"]:
            return True, FailureType.LOW_QUALITY, {
                "error_message": "Generated script does not meet minimum quality standards",
                "failure_type": FailureType.LOW_QUALITY.value,
                "quality_details": quality_details
            }
        
        # No failure detected
        return False, None, {}
    
    def _identify_failure_type(self, error_message: str) -> Optional[FailureType]:
        """
        Identify the type of failure from an error message
        
        Args:
            error_message: Error message from the generation process
            
        Returns:
            FailureType enum value or None if unknown
        """
        error_lower = error_message.lower()
        
        for failure_type, patterns in self.failure_patterns.items():
            for pattern in patterns:
                if pattern.lower() in error_lower:
                    return failure_type
        
        return FailureType.UNKNOWN
    
    def _is_truncated(self, script: str) -> bool:
        """
        Check if a script appears to be truncated
        
        Args:
            script: Generated script content
            
        Returns:
            True if the script appears to be truncated
        """
        # Check for obvious truncation indicators
        truncation_indicators = [
            # Unclosed brackets or parentheses
            (script.count('{') != script.count('}')),
            (script.count('(') != script.count(')')),
            (script.count('[') != script.count(']')),
            
            # Abrupt ending
            script.endswith('...'),
            
            # Unclosed triple quotes
            (script.count('"""') % 2 != 0),
            (script.count("'''") % 2 != 0),
            
            # Ends in the middle of a word
            bool(re.search(r'[a-zA-Z]{3,}\Z', script))
        ]
        
        return any(truncation_indicators)
    
    def _detect_hallucinations(self, script: str) -> Dict[str, Any]:
        """
        Detect hallucinations in the generated script
        
        Args:
            script: Generated script content
            
        Returns:
            Dictionary with hallucination detection details
        """
        has_hallucinations = False
        hallucination_indicators = []
        
        # Check for common hallucination patterns
        hallucination_patterns = [
            (r'import\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+#\s+This\s+(?:module|package)\s+doesn\'t\s+exist', 
             "Reference to non-existent module"),
            (r'#\s+Note:.*(?:doesn\'t exist|not available|fictional|made up)', 
             "Acknowledgment of fictional element"),
            (r'#\s+TODO:.*(?:find|create|develop|implement)', 
             "TODO for implementing required functionality")
        ]
        
        for pattern, description in hallucination_patterns:
            matches = re.findall(pattern, script)
            if matches:
                has_hallucinations = True
                hallucination_indicators.append({
                    "description": description,
                    "matches": matches
                })
        
        # Check for comments indicating the model is unsure/guessing
        uncertainty_patterns = [
            r'#\s+(?:I\'m|I am)\s+(?:not sure|uncertain|guessing)',
            r'#\s+(?:This is|Here\'s)\s+(?:an example|a placeholder)',
            r'#\s+(?:You may need to|You\'ll need to)\s+install'
        ]
        
        for pattern in uncertainty_patterns:
            if re.search(pattern, script):
                hallucination_indicators.append({
                    "description": "Expression of uncertainty in comments",
                    "matches": [pattern]
                })
        
        return {
            "has_hallucinations": has_hallucinations,
            "indicators": hallucination_indicators
        }
    
    def _evaluate_quality(self, script: str) -> Dict[str, Any]:
        """
        Evaluate the quality of the generated script
        
        Args:
            script: Generated script content
            
        Returns:
            Dictionary with quality evaluation details
        """
        # Set quality thresholds
        min_length = self.config.get("quality", {}).get("min_length", 100)
        min_doc_ratio = self.config.get("quality", {}).get("min_documentation_ratio", 0.15)
        max_comment_ratio = self.config.get("quality", {}).get("max_comment_ratio", 0.6)
        
        # Calculate metrics
        script_length = len(script)
        
        # Count documentation and comments
        doc_lines = 0
        comment_lines = 0
        code_lines = 0
        
        lines = script.split('\n')
        in_docstring = False
        docstring_delimiters = 0
        
        for line in lines:
            stripped = line.strip()
            
            # Check for docstring delimiters
            if '"""' in stripped or "'''" in stripped:
                docstring_delimiters += stripped.count('"""') + stripped.count("'''")
                in_docstring = docstring_delimiters % 2 != 0
                doc_lines += 1
                continue
                
            # If in docstring, count as documentation
            if in_docstring:
                doc_lines += 1
            # If line starts with #, count as comment
            elif stripped.startswith('#'):
                comment_lines += 1
            # Otherwise, if not empty, count as code
            elif stripped:
                code_lines += 1
        
        total_lines = doc_lines + comment_lines + code_lines
        doc_ratio = doc_lines / total_lines if total_lines > 0 else 0
        comment_ratio = comment_lines / total_lines if total_lines > 0 else 0
        
        # Determine if script meets minimum quality
        meets_minimum_length = script_length >= min_length
        meets_doc_ratio = doc_ratio >= min_doc_ratio
        not_too_many_comments = comment_ratio <= max_comment_ratio
        
        meets_minimum_quality = meets_minimum_length and meets_doc_ratio and not_too_many_comments
        
        return {
            "meets_minimum_quality": meets_minimum_quality,
            "metrics": {
                "length": script_length,
                "total_lines": total_lines,
                "doc_lines": doc_lines,
                "comment_lines": comment_lines,
                "code_lines": code_lines,
                "doc_ratio": doc_ratio,
                "comment_ratio": comment_ratio
            },
            "thresholds_met": {
                "length": meets_minimum_length,
                "doc_ratio": meets_doc_ratio,
                "comment_ratio": not_too_many_comments
            }
        }
    
    def recommend_recovery_strategy(self, 
                                   failure_type: FailureType,
                                   failure_details: Dict[str, Any],
                                   script_definition: Dict[str, Any],
                                   previous_attempts: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Recommend a recovery strategy for a failure
        
        Args:
            failure_type: Type of failure
            failure_details: Details about the failure
            script_definition: Original script definition
            previous_attempts: List of previous recovery attempts
            
        Returns:
            Dictionary with recommended recovery strategy
        """
        previous_attempts = previous_attempts or []
        
        # Get strategies from configuration or use defaults
        strategy_config = self.config.get("recovery_strategies", {})
        
        # Default strategy map
        default_strategies = {
            FailureType.CONTEXT_OVERFLOW: [
                RecoveryStrategy.DECOMPOSE,
                RecoveryStrategy.SIMPLIFY,
                RecoveryStrategy.CHANGE_MODEL
            ],
            FailureType.SYNTAX_ERROR: [
                RecoveryStrategy.RETRY,
                RecoveryStrategy.CHANGE_MODEL,
                RecoveryStrategy.SIMPLIFY
            ],
            FailureType.TRUNCATED_OUTPUT: [
                RecoveryStrategy.DECOMPOSE,
                RecoveryStrategy.SIMPLIFY,
                RecoveryStrategy.CHANGE_MODEL
            ],
            FailureType.MISSING_FEATURE: [
                RecoveryStrategy.CHANGE_MODEL,
                RecoveryStrategy.CHANGE_PROVIDER,
                RecoveryStrategy.SIMPLIFY
            ],
            FailureType.HALLUCINATION: [
                RecoveryStrategy.RETRY,
                RecoveryStrategy.CHANGE_MODEL,
                RecoveryStrategy.CHANGE_PROVIDER
            ],
            FailureType.LOW_QUALITY: [
                RecoveryStrategy.RETRY,
                RecoveryStrategy.CHANGE_MODEL,
                RecoveryStrategy.SIMPLIFY
            ],
            FailureType.RATE_LIMIT: [
                RecoveryStrategy.CHANGE_PROVIDER,
                RecoveryStrategy.RETRY,
                RecoveryStrategy.ABORT
            ],
            FailureType.API_ERROR: [
                RecoveryStrategy.RETRY,
                RecoveryStrategy.CHANGE_PROVIDER,
                RecoveryStrategy.ABORT
            ],
            FailureType.TIMEOUT: [
                RecoveryStrategy.RETRY,
                RecoveryStrategy.CHANGE_PROVIDER,
                RecoveryStrategy.SIMPLIFY
            ],
            FailureType.UNKNOWN: [
                RecoveryStrategy.RETRY,
                RecoveryStrategy.CHANGE_MODEL,
                RecoveryStrategy.CHANGE_PROVIDER
            ]
        }
        
        # Use config strategies if available, otherwise use defaults
        strategies = strategy_config.get(failure_type.value, default_strategies.get(failure_type, []))
        strategies = [RecoveryStrategy(s) if isinstance(s, str) else s for s in strategies]
        
        # Determine which strategies have been tried already
        tried_strategies = set()
        for attempt in previous_attempts:
            strategy = attempt.get("strategy")
            if strategy:
                tried_strategies.add(RecoveryStrategy(strategy) if isinstance(strategy, str) else strategy)
        
        # Filter out strategies that have been tried
        available_strategies = [s for s in strategies if s not in tried_strategies]
        
        # If all strategies have been tried, fall back to human assistance or abort
        if not available_strategies:
            if RecoveryStrategy.HUMAN_ASSISTANCE not in tried_strategies:
                recommended_strategy = RecoveryStrategy.HUMAN_ASSISTANCE
            else:
                recommended_strategy = RecoveryStrategy.ABORT
        else:
            recommended_strategy = available_strategies[0]
        
        # Generate recovery instructions based on the recommended strategy
        recovery_instructions = self._generate_recovery_instructions(
            recommended_strategy,
            failure_type,
            failure_details,
            script_definition
        )
        
        return {
            "recommended_strategy": recommended_strategy.value,
            "failure_type": failure_type.value,
            "recovery_instructions": recovery_instructions,
            "available_strategies": [s.value for s in available_strategies],
            "tried_strategies": [s.value for s in tried_strategies]
        }
    
    def _generate_recovery_instructions(self,
                                      strategy: RecoveryStrategy,
                                      failure_type: FailureType,
                                      failure_details: Dict[str, Any],
                                      script_definition: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate detailed instructions for implementing a recovery strategy
        
        Args:
            strategy: Recovery strategy to implement
            failure_type: Type of failure
            failure_details: Details about the failure
            script_definition: Original script definition
            
        Returns:
            Dictionary with recovery instructions
        """
        if strategy == RecoveryStrategy.RETRY:
            return self._generate_retry_instructions(failure_type, failure_details)
            
        elif strategy == RecoveryStrategy.SIMPLIFY:
            return self._generate_simplify_instructions(script_definition, failure_details)
            
        elif strategy == RecoveryStrategy.DECOMPOSE:
            return self._generate_decompose_instructions(script_definition)
            
        elif strategy == RecoveryStrategy.CHANGE_MODEL:
            return self._generate_change_model_instructions(failure_type)
            
        elif strategy == RecoveryStrategy.CHANGE_PROVIDER:
            return self._generate_change_provider_instructions(failure_type)
            
        elif strategy == RecoveryStrategy.HUMAN_ASSISTANCE:
            return {
                "description": "Request human assistance with the script generation",
                "actions": [
                    {
                        "type": "notify",
                        "message": f"Script generation failed after multiple attempts. Failure type: {failure_type.value}",
                        "requires_response": True
                    }
                ]
            }
            
        elif strategy == RecoveryStrategy.ABORT:
            return {
                "description": "Abort the script generation after multiple failures",
                "actions": [
                    {
                        "type": "abort",
                        "reason": f"Script generation failed after multiple attempts. Failure type: {failure_type.value}"
                    }
                ]
            }
            
        else:
            return {
                "description": f"Unknown recovery strategy: {strategy.value}",
                "actions": []
            }
    
    def _generate_retry_instructions(self, failure_type: FailureType, failure_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate instructions for retry strategy
        
        Args:
            failure_type: Type of failure
            failure_details: Details about the failure
            
        Returns:
            Dictionary with retry instructions
        """
        # Generate prompt enhancement based on failure type
        prompt_enhancement = ""
        
        if failure_type == FailureType.SYNTAX_ERROR:
            prompt_enhancement = "Ensure the generated code has proper syntax without any errors."
            
        elif failure_type == FailureType.HALLUCINATION:
            # Get specific hallucination details to address
            if "hallucination_details" in failure_details:
                hallucinations = failure_details["hallucination_details"].get("indicators", [])
                if hallucinations:
                    prompt_enhancement = "Avoid making up non-existent: " + ", ".join(h["description"] for h in hallucinations)
                else:
                    prompt_enhancement = "Avoid making up non-existent modules, functions, or features."
            else:
                prompt_enhancement = "Avoid making up non-existent modules, functions, or features."
            
        elif failure_type == FailureType.LOW_QUALITY:
            # Get specific quality issues to address
            if "quality_details" in failure_details:
                thresholds = failure_details["quality_details"].get("thresholds_met", {})
                issues = []
                
                if not thresholds.get("length", True):
                    issues.append("make the code more comprehensive")
                if not thresholds.get("doc_ratio", True):
                    issues.append("add more documentation")
                if not thresholds.get("comment_ratio", True):
                    issues.append("reduce the amount of comments in favor of actual code")
                
                if issues:
                    prompt_enhancement = "Please " + ", ".join(issues) + "."
                else:
                    prompt_enhancement = "Improve the quality of the generated code."
            else:
                prompt_enhancement = "Improve the quality of the generated code."
        
        return {
            "description": "Retry script generation with enhanced prompt",
            "actions": [
                {
                    "type": "retry",
                    "prompt_enhancement": prompt_enhancement,
                    "max_attempts": 3
                }
            ]
        }
    
    def _generate_simplify_instructions(self, script_definition: Dict[str, Any], failure_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate instructions for simplify strategy
        
        Args:
            script_definition: Original script definition
            failure_details: Details about the failure
            
        Returns:
            Dictionary with simplify instructions
        """
        # Identify which requirements can be simplified or removed
        requirements = script_definition.get("requirements", [])
        simplified_requirements = []
        
        if not requirements:
            # If no specific requirements, suggest simplifying the description
            return {
                "description": "Simplify the script description",
                "actions": [
                    {
                        "type": "modify_script_definition",
                        "field": "description",
                        "operation": "simplify",
                        "notes": "Remove complex features and focus on core functionality"
                    }
                ]
            }
        
        # Identify complex requirements
        complex_keywords = [
            "advanced", "complex", "comprehensive", "sophisticated",
            "extensive", "high-performance", "real-time", "multi-threaded",
            "concurrent", "distributed", "secure", "encryption"
        ]
        
        # Identify requirements to simplify
        simplify_candidates = []
        for i, req in enumerate(requirements):
            req_lower = req.lower()
            complexity_score = sum(1 for keyword in complex_keywords if keyword in req_lower)
            if complexity_score > 0:
                simplify_candidates.append((i, req, complexity_score))
        
        # Sort by complexity score (descending)
        simplify_candidates.sort(key=lambda x: x[2], reverse=True)
        
        # Select candidates for simplification (up to 30% of requirements)
        max_to_simplify = max(1, len(requirements) // 3)
        to_simplify = simplify_candidates[:max_to_simplify]
        
        if not to_simplify:
            # If no clear candidates, suggest removing some requirements
            return {
                "description": "Remove some requirements to simplify the script",
                "actions": [
                    {
                        "type": "modify_script_definition",
                        "field": "requirements",
                        "operation": "remove",
                        "target_count": max(1, len(requirements) // 3),
                        "notes": "Remove the most complex or optional requirements"
                    }
                ]
            }
        
        # Generate instructions for simplifying specific requirements
        actions = []
        for idx, req, _ in to_simplify:
            actions.append({
                "type": "modify_script_definition",
                "field": "requirements",
                "operation": "simplify",
                "index": idx,
                "original": req,
                "notes": "Focus on basic functionality and remove complex features"
            })
        
        return {
            "description": "Simplify complex requirements",
            "actions": actions
        }
    
    def _generate_decompose_instructions(self, script_definition: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate instructions for decompose strategy
        
        Args:
            script_definition: Original script definition
            
        Returns:
            Dictionary with decompose instructions
        """
        return {
            "description": "Decompose the script into smaller components",
            "actions": [
                {
                    "type": "decompose",
                    "script_definition": script_definition,
                    "component_count": self._estimate_component_count(script_definition),
                    "notes": "Break down the script into independent modules that can be generated separately"
                }
            ]
        }
    
    def _estimate_component_count(self, script_definition: Dict[str, Any]) -> int:
        """
        Estimate the number of components for script decomposition
        
        Args:
            script_definition: Original script definition
            
        Returns:
            Estimated number of components
        """
        requirements = script_definition.get("requirements", [])
        description = script_definition.get("description", "")
        
        # Base component count on requirements
        base_count = max(2, len(requirements) // 3)
        
        # Adjust based on description length
        description_words = len(description.split())
        if description_words > 300:
            base_count += 1
        
        # Ensure a reasonable range
        return min(5, max(2, base_count))
    
    def _generate_change_model_instructions(self, failure_type: FailureType) -> Dict[str, Any]:
        """
        Generate instructions for changing to a different model
        
        Args:
            failure_type: Type of failure
            
        Returns:
            Dictionary with model change instructions
        """
        # Define model selection criteria based on failure type
        criteria = {}
        
        if failure_type == FailureType.CONTEXT_OVERFLOW:
            criteria = {
                "min_context_length": 100000,
                "preferred_features": ["long context"]
            }
        elif failure_type == FailureType.SYNTAX_ERROR:
            criteria = {
                "preferred_features": ["code generation", "instruction following"]
            }
        elif failure_type == FailureType.MISSING_FEATURE:
            criteria = {
                "preferred_features": ["comprehensive capabilities", "code generation"]
            }
        elif failure_type == FailureType.HALLUCINATION:
            criteria = {
                "preferred_features": ["factual accuracy", "code generation"]
            }
        elif failure_type == FailureType.LOW_QUALITY:
            criteria = {
                "quality_threshold": 0.8,
                "preferred_features": ["code quality", "comprehensive reasoning"]
            }
        else:
            criteria = {
                "quality_threshold": 0.75
            }
        
        return {
            "description": "Change to a more suitable model",
            "actions": [
                {
                    "type": "change_model",
                    "selection_criteria": criteria,
                    "same_provider": True,
                    "notes": f"Select a model better suited for handling {failure_type.value} issues"
                }
            ]
        }
    
    def _generate_change_provider_instructions(self, failure_type: FailureType) -> Dict[str, Any]:
        """
        Generate instructions for changing to a different provider
        
        Args:
            failure_type: Type of failure
            
        Returns:
            Dictionary with provider change instructions
        """
        # Define provider preferences based on failure type
        preferred_providers = []
        
        if failure_type == FailureType.CONTEXT_OVERFLOW:
            preferred_providers = ["claude", "openai"]
        elif failure_type == FailureType.SYNTAX_ERROR or failure_type == FailureType.HALLUCINATION:
            preferred_providers = ["deepseek", "openai"]
        elif failure_type == FailureType.MISSING_FEATURE:
            preferred_providers = ["openai", "claude"]
        elif failure_type == FailureType.RATE_LIMIT or failure_type == FailureType.API_ERROR:
            # Recommend any provider different from the current one
            preferred_providers = []
        else:
            preferred_providers = ["openai", "claude", "deepseek"]
        
        return {
            "description": "Change to a different provider",
            "actions": [
                {
                    "type": "change_provider",
                    "preferred_providers": preferred_providers,
                    "exclude_current": True,
                    "notes": f"Switch to a provider better suited for handling {failure_type.value} issues"
                }
            ]
        }
    
    def track_strategy_outcomes(self, strategy: RecoveryStrategy, success: bool) -> None:
        """
        Track the outcomes of recovery strategies for future recommendations
        
        Args:
            strategy: Recovery strategy that was attempted
            success: Whether the strategy was successful
        """
        strategy_str = strategy.value if isinstance(strategy, RecoveryStrategy) else strategy
        
        if strategy_str not in self.strategy_history:
            self.strategy_history[strategy_str] = {
                "success": 0,
                "failure": 0,
                "total": 0
            }
        
        if success:
            self.strategy_history[strategy_str]["success"] += 1
        else:
            self.strategy_history[strategy_str]["failure"] += 1
            
        self.strategy_history[strategy_str]["total"] += 1
    
    def get_strategy_success_rates(self) -> Dict[str, float]:
        """
        Get success rates for all tracked recovery strategies
        
        Returns:
            Dictionary mapping strategy names to success rates
        """
        success_rates = {}
        
        for strategy, stats in self.strategy_history.items():
            total = stats["total"]
            if total > 0:
                success_rates[strategy] = stats["success"] / total
            else:
                success_rates[strategy] = 0.0
        
        return success_rates


# Test the failure handler if run directly
if __name__ == "__main__":
    handler = FailureHandler()
    
    # Test failure detection
    test_result = {
        "success": False,
        "error": "The model's maximum context length is 100000, but the given prompt is 120000 tokens. Please shorten the prompt.",
        "script": None
    }
    
    is_failure, failure_type, details = handler.detect_failure(test_result)
    print(f"Is failure: {is_failure}")
    print(f"Failure type: {failure_type}")
    print(f"Details: {details}")
    
    # Test recovery strategy recommendation
    test_definition = {
        "name": "data_processor.py",
        "description": "A complex data processing script that handles large CSV and JSON files with real-time updates.",
        "requirements": [
            "Support CSV and JSON input formats",
            "Handle files larger than 10GB efficiently",
            "Implement multi-threaded processing for performance",
            "Provide real-time progress updates",
            "Support encryption for secure data handling",
            "Validate input data against complex schema"
        ]
    }
    
    recovery = handler.recommend_recovery_strategy(failure_type, details, test_definition)
    print("\nRecommended recovery strategy:")
    print(f"Strategy: {recovery['recommended_strategy']}")
    print(f"Instructions: {recovery['recovery_instructions']}")
