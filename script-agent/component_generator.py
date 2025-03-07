"""
Component Generator
Module for generating specialized script components
"""

import os
import sys
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import the model providers module
try:
    from model_providers.base_provider import BaseModelProvider
except ImportError:
    # Define a fallback if model_providers is not available
    class BaseModelProvider:
        """Fallback base class if model_providers is not available"""
        pass

# Setup logging
logger = logging.getLogger(__name__)


class ComponentGenerator:
    """
    Generates specialized script components with interface contracts
    and validates them against requirements
    """
    
    def __init__(self, provider: Optional[BaseModelProvider] = None, config_path: str = None):
        """
        Initialize the component generator
        
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
    
    def _load_config(self, config_path: str) -> None:
        """Load configuration from a JSON file"""
        try:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {e}")
            # Use default empty config
            self.config = {}
    
    async def generate_component(self, 
                               component_definition: Dict[str, Any],
                               context: Dict[str, Any],
                               interface_contracts: Dict[str, Any] = None,
                               iteration: int = 1) -> Dict[str, Any]:
        """
        Generate a specialized script component
        
        Args:
            component_definition: Dictionary defining the component
            context: Context information for generation
            interface_contracts: Interface contracts the component must follow
            iteration: Current iteration number
            
        Returns:
            Dictionary containing the generated component and metadata
        """
        # Handle the case where we don't have a provider
        if not self.provider:
            return self._fallback_component_generation(component_definition, context)
        
        # Construct the prompt
        prompt = self._construct_prompt(component_definition, context, interface_contracts, iteration)
        
        # Generate the response
        try:
            system_prompt = self._construct_system_prompt(component_definition)
            temperature = self.config.get("model", {}).get("temperature", 0.7)
            max_tokens = self.config.get("model", {}).get("max_tokens", 4000)
            
            response = await self.provider.generate_response(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Extract code from the response
            code_blocks = await self.provider.extract_code(response)
            
            if code_blocks:
                script_content = code_blocks[0]  # Use the first code block
            else:
                # If no code blocks found, use the full response
                script_content = response
            
            # Validate the generated component
            validation_result = self._validate_component(
                script_content, 
                component_definition, 
                interface_contracts
            )
            
            return {
                "success": validation_result["valid"],
                "component": script_content,
                "validation": validation_result,
                "name": component_definition.get("name", "unknown"),
                "type": component_definition.get("type", "unknown"),
                "token_usage": {
                    "prompt_tokens": len(prompt.split()) * 1.3,  # Rough estimate
                    "completion_tokens": len(response.split()) * 1.3,  # Rough estimate
                    "total_tokens": (len(prompt.split()) + len(response.split())) * 1.3
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating component: {e}")
            return {
                "success": False,
                "error": str(e),
                "component": None,
                "name": component_definition.get("name", "unknown"),
                "type": component_definition.get("type", "unknown")
            }
    
    def _fallback_component_generation(self, 
                                     component_definition: Dict[str, Any],
                                     context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback method when no provider is available"""
        component_name = component_definition.get("name", "unknown")
        component_type = component_definition.get("type", "unknown")
        description = component_definition.get("description", "")
        
        return {
            "success": False,
            "error": "No AI provider available",
            "component": f"""
# {component_name} ({component_type})
# 
# This is a placeholder component. The component generator could not connect 
# to an AI model provider. Please ensure you have set up the appropriate
# API keys and dependencies.
#
# Description: {description}
#
""",
            "name": component_name,
            "type": component_type
        }
    
    def _construct_system_prompt(self, component_definition: Dict[str, Any]) -> str:
        """Construct the system prompt for the AI model"""
        component_type = component_definition.get("type", "unknown")
        
        base_prompt = """You are an expert software developer tasked with generating a specialized code component.
Your task is to generate a high-quality, well-structured implementation based on the provided definition and context.
Follow these guidelines:
1. Write clean, efficient, and well-documented code
2. Include appropriate error handling and input validation
3. Follow best practices for the language/framework being used
4. Keep the code modular and maintainable
5. Include detailed comments explaining complex parts of the code
6. Ensure the component follows any specified interface contracts

Return ONLY the code, without additional explanations or markdown formatting.
"""
        
        # Add specific guidance based on component type
        if component_type == "main":
            base_prompt += """
For a main component:
- Implement the entry point and core flow control
- Handle command-line arguments if appropriate
- Import and use other components as needed
- Focus on orchestration rather than detailed implementation
"""
        elif component_type == "class" or component_type == "module":
            base_prompt += """
For a class/module component:
- Implement a clean, well-structured class with appropriate methods
- Follow object-oriented design principles
- Provide clear method signatures with docstrings
- Include proper initialization and cleanup
"""
        elif component_type == "utility" or component_type == "helper":
            base_prompt += """
For a utility/helper component:
- Implement focused, stateless utility functions
- Make functions reusable and composable
- Provide clear, consistent interfaces
- Document parameters and return values thoroughly
"""
        elif component_type == "interface" or component_type == "api":
            base_prompt += """
For an interface/API component:
- Implement clean, well-defined interfaces
- Ensure consistent error handling and responses
- Document the API clearly with examples if possible
- Follow API design best practices
"""
        
        return base_prompt
    
    def _construct_prompt(self, 
                         component_definition: Dict[str, Any],
                         context: Dict[str, Any],
                         interface_contracts: Dict[str, Any] = None,
                         iteration: int = 1) -> str:
        """
        Construct the prompt for the AI model
        
        Args:
            component_definition: Dictionary defining the component
            context: Context information for generation
            interface_contracts: Interface contracts the component must follow
            iteration: Current iteration number
            
        Returns:
            String containing the constructed prompt
        """
        # Extract relevant info
        component_name = component_definition.get("name", "")
        component_type = component_definition.get("type", "")
        description = component_definition.get("description", "")
        requirements = component_definition.get("requirements", [])
        dependencies = component_definition.get("depends_on", [])
        
        # Determine language from context or file extension
        language = context.get("language", "python")
        if "." in component_name:
            ext = component_name.split(".")[-1].lower()
            if ext == "py":
                language = "python"
            elif ext in ["js", "jsx"]:
                language = "javascript"
            elif ext in ["ts", "tsx"]:
                language = "typescript"
            elif ext in ["sh", "bash"]:
                language = "shell"
        
        # Start with the basic component definition
        prompt = f"""Generate a {language} component named '{component_name}' of type '{component_type}'.

Description:
{description}

"""
        
        # Add requirements if provided
        if requirements:
            prompt += "Requirements:\n"
            for req in requirements:
                prompt += f"- {req}\n"
            prompt += "\n"
        
        # Add dependencies information
        if dependencies:
            prompt += "Dependencies:\n"
            for dep in dependencies:
                dep_info = context.get("components", {}).get(dep, {})
                if dep_info:
                    dep_name = dep_info.get("name", dep)
                    dep_type = dep_info.get("type", "unknown")
                    dep_desc = dep_info.get("description", "")
                    prompt += f"- {dep_name} ({dep_type}): {dep_desc}\n"
                else:
                    prompt += f"- {dep}\n"
            prompt += "\n"
        
        # Add interface contracts if provided
        if interface_contracts:
            prompt += "Interface Contracts:\n"
            
            if "functions" in interface_contracts:
                prompt += "Functions that must be implemented:\n"
                for func in interface_contracts["functions"]:
                    func_name = func.get("name", "")
                    func_params = func.get("parameters", [])
                    func_return = func.get("returns", "None")
                    func_desc = func.get("description", "")
                    
                    params_str = ", ".join([f"{p.get('name')}: {p.get('type', 'Any')}" for p in func_params])
                    prompt += f"- {func_name}({params_str}) -> {func_return}: {func_desc}\n"
                prompt += "\n"
            
            if "classes" in interface_contracts:
                prompt += "Classes that must be implemented:\n"
                for cls in interface_contracts["classes"]:
                    cls_name = cls.get("name", "")
                    if cls_name and cls_name not in script_content:
                        results["valid"] = False
                        results["errors"].append(f"Required class '{cls_name}' might be missing")
                    
                    for method in cls.get("methods", []):
                        method_name = method.get("name", "")
                        if method_name and method_name not in script_content:
                            results["valid"] = False
                            results["errors"].append(f"Required method '{method_name}' might be missing")
            
            if "imports" in interface_contracts:
                for imp in interface_contracts["imports"]:
                    if imp not in script_content:
                        results["warnings"].append(f"Required import '{imp}' might be missing")
        
        return results
    
    def _validate_requirements(self, script_content: str, requirements: List[str]) -> Dict[str, Any]:
        """
        Validate that a script meets its requirements
        
        Args:
            script_content: The script content to validate
            requirements: List of requirements to validate against
            
        Returns:
            Dictionary with validation results
        """
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "missing": []
        }
        
        # This is a simple keyword-based validation and isn't foolproof,
        # but it's a basic check to catch obvious issues
        
        # Convert requirements to keywords
        for req in requirements:
            # Extract significant words (3+ chars) from requirement
            keywords = [word for word in req.lower().split() if len(word) >= 3]
            
            # Check if at least 60% of keywords are in the script
            script_lower = script_content.lower()
            matches = sum(1 for keyword in keywords if keyword in script_lower)
            
            if matches / len(keywords) < 0.6 if keywords else False:
                results["valid"] = False
                results["errors"].append(f"Requirement may not be implemented: {req}")
                results["missing"].append(req)
        
        return results


# Basic test code
if __name__ == "__main__":
    # Example component definition
    test_component = {
        "id": "component_0",
        "name": "data_processor.py",
        "type": "class",
        "description": "A class for processing data from different file formats",
        "requirements": [
            "Support CSV and JSON input formats",
            "Provide methods to clean and transform data",
            "Handle errors gracefully"
        ],
        "depends_on": []
    }
    
    # Example context
    test_context = {
        "language": "python",
        "project_summary": {
            "description": "Data processing utility library",
            "structure": ["data_processor.py", "utils.py", "reader.py"]
        }
    }
    
    # Example interface contracts
    test_contracts = {
        "classes": [
            {
                "name": "DataProcessor",
                "description": "Main data processing class",
                "methods": [
                    {"name": "process", "parameters": [{"name": "data", "type": "Dict"}], "returns": "Dict", "description": "Process data"},
                    {"name": "read_file", "parameters": [{"name": "file_path", "type": "str"}], "returns": "Dict", "description": "Read data from file"}
                ]
            }
        ],
        "functions": [
            {"name": "clean_data", "parameters": [{"name": "data", "type": "Dict"}], "returns": "Dict", "description": "Clean data dictionary"}
        ],
        "imports": ["os", "json", "csv"]
    }
    
    async def test_generator():
        # Create component generator (without a real provider)
        generator = ComponentGenerator()
        
        # Generate a component using fallback (since no provider is set)
        result = await generator.generate_component(test_component, test_context, test_contracts)
        
        print("Generation result:")
        print(f"Success: {result['success']}")
        if "error" in result:
            print(f"Error: {result['error']}")
        
        print("\nGenerated component:")
        print(result.get("component", "No component generated"))
    
    # Run the test
    import asyncio
    asyncio.run(test_generator())

                    cls_desc = cls.get("description", "")
                    methods = cls.get("methods", [])
                    
                    prompt += f"- {cls_name}: {cls_desc}\n"
                    for method in methods:
                        method_name = method.get("name", "")
                        method_params = method.get("parameters", [])
                        method_return = method.get("returns", "None")
                        method_desc = method.get("description", "")
                        
                        params_str = ", ".join([f"{p.get('name')}: {p.get('type', 'Any')}" for p in method_params])
                        prompt += f"  - {method_name}({params_str}) -> {method_return}: {method_desc}\n"
                prompt += "\n"
            
            if "imports" in interface_contracts:
                prompt += "Required imports:\n"
                for imp in interface_contracts["imports"]:
                    prompt += f"- {imp}\n"
                prompt += "\n"
        
        # Add context information
        if "project_summary" in context:
            prompt += "Project Context:\n"
            summary = context["project_summary"]
            
            if "description" in summary:
                prompt += f"Project description: {summary['description']}\n"
            
            if "structure" in summary:
                prompt += "Project structure:\n"
                for file_path in summary["structure"][:10]:  # Limit to 10 files
                    prompt += f"- {file_path}\n"
                
                if len(summary["structure"]) > 10:
                    prompt += f"- ... and {len(summary['structure']) - 10} more files\n"
                
                prompt += "\n"
        
        # Add iteration context for improvements
        if iteration > 1:
            prompt += f"\nThis is iteration #{iteration}. Please improve the previous version based on the following feedback:\n"
            
            if "feedback" in context:
                prompt += context["feedback"]
            else:
                prompt += "Focus on making the code more robust and maintainable."
        
        return prompt
    
    def _validate_component(self, 
                          script_content: str, 
                          component_definition: Dict[str, Any],
                          interface_contracts: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Validate the generated component against requirements and interface contracts
        
        Args:
            script_content: The generated script content
            component_definition: Dictionary defining the component
            interface_contracts: Interface contracts the component must follow
            
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            "valid": True,
            "syntax_valid": True,
            "interface_valid": True,
            "requirements_met": True,
            "errors": [],
            "warnings": []
        }
        
        # Determine language from component name
        language = "python"  # Default
        if "." in component_definition.get("name", ""):
            ext = component_definition["name"].split(".")[-1].lower()
            if ext == "py":
                language = "python"
            elif ext in ["js", "jsx"]:
                language = "javascript"
            elif ext in ["ts", "tsx"]:
                language = "typescript"
            elif ext in ["sh", "bash"]:
                language = "shell"
        
        # Check for syntax errors based on language
        syntax_result = self._validate_syntax(script_content, language)
        validation_results["syntax_valid"] = syntax_result["valid"]
        
        if not syntax_result["valid"]:
            validation_results["valid"] = False
            validation_results["errors"].append(f"Syntax error: {syntax_result.get('error', 'Unknown error')}")
        
        # Check interface contracts if provided
        if interface_contracts:
            interface_result = self._validate_interface(script_content, interface_contracts, language)
            validation_results["interface_valid"] = interface_result["valid"]
            
            if not interface_result["valid"]:
                validation_results["valid"] = False
                for error in interface_result.get("errors", []):
                    validation_results["errors"].append(f"Interface error: {error}")
            
            for warning in interface_result.get("warnings", []):
                validation_results["warnings"].append(f"Interface warning: {warning}")
        
        # Check requirements if provided
        requirements = component_definition.get("requirements", [])
        if requirements:
            req_result = self._validate_requirements(script_content, requirements)
            validation_results["requirements_met"] = req_result["valid"]
            
            if not req_result["valid"]:
                validation_results["valid"] = False
                for error in req_result.get("errors", []):
                    validation_results["errors"].append(f"Requirement error: {error}")
            
            validation_results["missing_requirements"] = req_result.get("missing", [])
        
        return validation_results
    
    def _validate_syntax(self, script_content: str, language: str) -> Dict[str, Any]:
        """
        Validate the syntax of a script
        
        Args:
            script_content: The script content to validate
            language: Programming language of the script
            
        Returns:
            Dictionary with validation results
        """
        if language == "python":
            try:
                import ast
                ast.parse(script_content)
                return {"valid": True}
            except SyntaxError as e:
                return {
                    "valid": False,
                    "error": str(e),
                    "line": e.lineno,
                    "column": e.offset,
                    "text": e.text
                }
            except Exception as e:
                return {
                    "valid": False,
                    "error": str(e)
                }
        elif language in ["javascript", "typescript"]:
            # Simple validation for JS/TS (just check for balanced braces)
            if script_content.count('{') != script_content.count('}'):
                return {
                    "valid": False,
                    "error": "Unbalanced braces"
                }
            if script_content.count('(') != script_content.count(')'):
                return {
                    "valid": False,
                    "error": "Unbalanced parentheses"
                }
            return {"valid": True}
        else:
            # For other languages, we can't validate syntax easily
            return {"valid": True, "warning": f"No syntax validation available for {language}"}
    
    def _validate_interface(self, script_content: str, interface_contracts: Dict[str, Any], language: str) -> Dict[str, Any]:
        """
        Validate that a script implements required interfaces
        
        Args:
            script_content: The script content to validate
            interface_contracts: Interface contracts to validate against
            language: Programming language of the script
            
        Returns:
            Dictionary with validation results
        """
        results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        if language == "python":
            try:
                import ast
                tree = ast.parse(script_content)
                
                # Extract defined functions and classes
                defined_functions = set()
                defined_classes = {}
                
                for node in tree.body:
                    if isinstance(node, ast.FunctionDef):
                        defined_functions.add(node.name)
                    elif isinstance(node, ast.ClassDef):
                        class_methods = set()
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef):
                                class_methods.add(item.name)
                        defined_classes[node.name] = class_methods
                
                # Check required functions
                if "functions" in interface_contracts:
                    for func in interface_contracts["functions"]:
                        func_name = func.get("name", "")
                        if func_name and func_name not in defined_functions:
                            results["valid"] = False
                            results["errors"].append(f"Required function '{func_name}' is not implemented")
                
                # Check required classes and methods
                if "classes" in interface_contracts:
                    for cls in interface_contracts["classes"]:
                        cls_name = cls.get("name", "")
                        if cls_name and cls_name not in defined_classes:
                            results["valid"] = False
                            results["errors"].append(f"Required class '{cls_name}' is not implemented")
                        elif cls_name:
                            # Check methods
                            class_methods = defined_classes[cls_name]
                            for method in cls.get("methods", []):
                                method_name = method.get("name", "")
                                if method_name and method_name not in class_methods:
                                    results["valid"] = False
                                    results["errors"].append(f"Required method '{cls_name}.{method_name}' is not implemented")
                
                # Check imports (less strict, just warnings)
                if "imports" in interface_contracts:
                    imported_modules = set()
                    for node in tree.body:
                        if isinstance(node, ast.Import):
                            for name in node.names:
                                imported_modules.add(name.name)
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                imported_modules.add(node.module)
                    
                    for imp in interface_contracts["imports"]:
                        if imp not in imported_modules:
                            results["warnings"].append(f"Required import '{imp}' might be missing")
            
            except Exception as e:
                logger.error(f"Error validating interface: {e}")
                results["warnings"].append(f"Interface validation error: {str(e)}")
        
        else:
            # For non-Python languages, we'll do a simpler text-based check
            if "functions" in interface_contracts:
                for func in interface_contracts["functions"]:
                    func_name = func.get("name", "")
                    if func_name and func_name not in script_content:
                        results["valid"] = False
                        results["errors"].append(f"Required function '{func_name}' might be missing")
            
            if "classes" in interface_contracts:
                for cls in interface_contracts["classes"]:
                    cls_name = cls.get("name", "")