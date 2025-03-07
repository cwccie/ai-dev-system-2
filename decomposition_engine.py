"""
Decomposition Engine
Module for breaking down complex scripts into manageable components
"""

import os
import re
import json
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path

from orchestrator.script_planner import ScriptPlanner


class DecompositionEngine:
    """
    Engine for decomposing complex scripts into smaller, manageable components
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the decomposition engine
        
        Args:
            config: Configuration dictionary with decomposition settings
        """
        self.config = config or {}
        self.script_planner = ScriptPlanner(config)
        
    def decompose_script(self, script_definition: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decompose a complex script into smaller components
        
        Args:
            script_definition: Dictionary defining the script requirements
            
        Returns:
            Dictionary containing decomposition results and component definitions
        """
        # First, analyze the script using the planner
        analysis = self.script_planner.analyze_script_definition(script_definition)
        
        # If script doesn't need decomposition, return early
        if not analysis.get("needs_decomposition", False):
            return {
                "original_script": script_definition,
                "needs_decomposition": False,
                "components": [],
                "analysis": analysis
            }
        
        # Get component definitions from the analysis
        components = analysis.get("components", [])
        
        # Apply decomposition strategy based on script type
        if not components:
            # If planner didn't identify components, apply a template
            components = self._apply_decomposition_template(script_definition)
        else:
            # Enhance component definitions with additional details
            components = self._enhance_component_definitions(script_definition, components)
        
        # Create a dependency graph for the components
        dependency_graph = self._create_dependency_graph(components)
        
        return {
            "original_script": script_definition,
            "needs_decomposition": True,
            "components": components,
            "dependency_graph": dependency_graph,
            "generation_order": self._determine_generation_order(dependency_graph),
            "analysis": analysis
        }
    
    def _apply_decomposition_template(self, script_definition: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Apply a decomposition template based on script type
        
        Args:
            script_definition: Dictionary defining the script requirements
            
        Returns:
            List of component definitions
        """
        # Get script type
        script_path = script_definition.get("path", "")
        script_name = os.path.basename(script_path)
        base_name = os.path.splitext(script_name)[0]
        
        description = script_definition.get("description", "")
        requirements = script_definition.get("requirements", [])
        
        # Select appropriate template
        template_name = self._select_template(script_name, description, requirements)
        templates = self._get_decomposition_templates()
        
        # Apply the selected template
        if template_name in templates:
            template = templates[template_name]
            return self._instantiate_template(template, script_definition)
        
        # Fallback to generic template
        return self._instantiate_template(templates["generic"], script_definition)
    
    def _select_template(self, script_name: str, description: str, requirements: List[str]) -> str:
        """Select the most appropriate template based on script characteristics"""
        # Combine text for analysis
        combined_text = f"{script_name} {description} {' '.join(requirements)}".lower()
        
        # Check for keywords indicating script type
        if any(kw in combined_text for kw in ["api", "rest", "http", "endpoint", "service"]):
            return "api_service"
        elif any(kw in combined_text for kw in ["cli", "command", "terminal", "console"]):
            return "cli_tool"
        elif any(kw in combined_text for kw in ["data", "processor", "transform", "csv", "json"]):
            return "data_processor"
        elif any(kw in combined_text for kw in ["web", "scraper", "crawler", "html", "parse"]):
            return "web_scraper"
        elif any(kw in combined_text for kw in ["database", "sql", "orm", "query"]):
            return "database_tool"
        
        return "generic"
    
    def _get_decomposition_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get predefined decomposition templates"""
        templates = {
            "api_service": {
                "components": [
                    {
                        "type": "main",
                        "name": "{base_name}",
                        "description": "Main entry point for the {base_name} API service",
                        "is_primary": True,
                        "template": "api_main"
                    },
                    {
                        "type": "router",
                        "name": "{base_name}_router",
                        "description": "Router for API endpoints",
                        "depends_on": ["{base_name}"],
                        "template": "api_router"
                    },
                    {
                        "type": "controller",
                        "name": "{base_name}_controller",
                        "description": "Controller for handling business logic",
                        "depends_on": ["{base_name}"],
                        "template": "api_controller"
                    },
                    {
                        "type": "model",
                        "name": "{base_name}_model",
                        "description": "Data models for the API",
                        "template": "api_model"
                    },
                    {
                        "type": "util",
                        "name": "{base_name}_utils",
                        "description": "Utility functions for the API",
                        "template": "api_utils"
                    }
                ]
            },
            "cli_tool": {
                "components": [
                    {
                        "type": "main",
                        "name": "{base_name}",
                        "description": "Main entry point for the {base_name} CLI tool",
                        "is_primary": True,
                        "template": "cli_main"
                    },
                    {
                        "type": "commands",
                        "name": "{base_name}_commands",
                        "description": "Command implementations",
                        "depends_on": ["{base_name}"],
                        "template": "cli_commands"
                    },
                    {
                        "type": "core",
                        "name": "{base_name}_core",
                        "description": "Core functionality",
                        "template": "cli_core"
                    },
                    {
                        "type": "util",
                        "name": "{base_name}_utils",
                        "description": "Utility functions",
                        "template": "cli_utils"
                    }
                ]
            },
            "data_processor": {
                "components": [
                    {
                        "type": "main",
                        "name": "{base_name}",
                        "description": "Main entry point for the data processor",
                        "is_primary": True,
                        "template": "data_main"
                    },
                    {
                        "type": "reader",
                        "name": "{base_name}_reader",
                        "description": "Data input reader",
                        "template": "data_reader"
                    },
                    {
                        "type": "processor",
                        "name": "{base_name}_processor",
                        "description": "Data processing logic",
                        "depends_on": ["{base_name}_reader"],
                        "template": "data_processor"
                    },
                    {
                        "type": "writer",
                        "name": "{base_name}_writer",
                        "description": "Data output writer",
                        "depends_on": ["{base_name}_processor"],
                        "template": "data_writer"
                    },
                    {
                        "type": "util",
                        "name": "{base_name}_utils",
                        "description": "Utility functions",
                        "template": "data_utils"
                    }
                ]
            },
            "web_scraper": {
                "components": [
                    {
                        "type": "main",
                        "name": "{base_name}",
                        "description": "Main entry point for the web scraper",
                        "is_primary": True,
                        "template": "scraper_main"
                    },
                    {
                        "type": "fetcher",
                        "name": "{base_name}_fetcher",
                        "description": "HTTP request handling",
                        "template": "scraper_fetcher"
                    },
                    {
                        "type": "parser",
                        "name": "{base_name}_parser",
                        "description": "HTML/XML parsing logic",
                        "depends_on": ["{base_name}_fetcher"],
                        "template": "scraper_parser"
                    },
                    {
                        "type": "storage",
                        "name": "{base_name}_storage",
                        "description": "Data storage handling",
                        "depends_on": ["{base_name}_parser"],
                        "template": "scraper_storage"
                    },
                    {
                        "type": "util",
                        "name": "{base_name}_utils",
                        "description": "Utility functions",
                        "template": "scraper_utils"
                    }
                ]
            },
            "database_tool": {
                "components": [
                    {
                        "type": "main",
                        "name": "{base_name}",
                        "description": "Main entry point for the database tool",
                        "is_primary": True,
                        "template": "db_main"
                    },
                    {
                        "type": "connection",
                        "name": "{base_name}_connection",
                        "description": "Database connection handling",
                        "template": "db_connection"
                    },
                    {
                        "type": "models",
                        "name": "{base_name}_models",
                        "description": "Database models",
                        "depends_on": ["{base_name}_connection"],
                        "template": "db_models"
                    },
                    {
                        "type": "queries",
                        "name": "{base_name}_queries",
                        "description": "Query implementations",
                        "depends_on": ["{base_name}_models"],
                        "template": "db_queries"
                    },
                    {
                        "type": "util",
                        "name": "{base_name}_utils",
                        "description": "Utility functions",
                        "template": "db_utils"
                    }
                ]
            },
            "generic": {
                "components": [
                    {
                        "type": "main",
                        "name": "{base_name}",
                        "description": "Main implementation of {base_name}",
                        "is_primary": True,
                        "template": "generic_main"
                    },
                    {
                        "type": "core",
                        "name": "{base_name}_core",
                        "description": "Core functionality for {base_name}",
                        "template": "generic_core"
                    },
                    {
                        "type": "helpers",
                        "name": "{base_name}_helpers",
                        "description": "Helper functions for {base_name}",
                        "template": "generic_helpers"
                    },
                    {
                        "type": "util",
                        "name": "{base_name}_utils",
                        "description": "Utility functions for {base_name}",
                        "template": "generic_utils"
                    }
                ]
            }
        }
        
        return templates
    
    def _instantiate_template(self, template: Dict[str, Any], script_definition: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Instantiate a template with script-specific information
        
        Args:
            template: Template definition
            script_definition: Script definition
            
        Returns:
            List of instantiated component definitions
        """
        # Extract script info
        script_path = script_definition.get("path", "")
        script_name = os.path.basename(script_path)
        base_name = os.path.splitext(script_name)[0]
        
        # Clean base_name for use in variable/function names
        clean_base_name = re.sub(r'[^\w]', '_', base_name).lower()
        
        # Parse requirements to distribute to components
        requirements = script_definition.get("requirements", [])
        
        # Instantiate components
        components = []
        for i, component_template in enumerate(template["components"]):
            # Create a copy of the template
            component = component_template.copy()
            
            # Add component ID
            component["id"] = f"component_{i}"
            
            # Replace placeholders
            component["name"] = component["name"].format(base_name=clean_base_name)
            component["description"] = component["description"].format(base_name=base_name)
            
            # Handle dependencies
            if "depends_on" in component:
                component["depends_on"] = [dep.format(base_name=clean_base_name) for dep in component["depends_on"]]
            
            components.append(component)
        
        return components
    
    def _enhance_component_definitions(self, script_definition: Dict[str, Any], components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enhance component definitions with additional details
        
        Args:
            script_definition: Dictionary defining the script requirements
            components: List of initial component definitions
            
        Returns:
            Enhanced list of component definitions
        """
        # Extract script info
        script_name = script_definition.get("name", "")
        description = script_definition.get("description", "")
        requirements = script_definition.get("requirements", [])
        
        # Identify primary component if not already defined
        primary_component_defined = any(comp.get("is_primary", False) for comp in components)
        if not primary_component_defined and components:
            components[0]["is_primary"] = True
        
        # Distribute requirements to components if not already assigned
        for component in components:
            if "requirements" not in component:
                component["requirements"] = self._assign_requirements_to_component(
                    component, 
                    requirements,
                    components
                )
        
        # Set file paths for components based on script path
        script_path = script_definition.get("path", "")
        if script_path:
            dir_path = os.path.dirname(script_path)
            filename = os.path.basename(script_path)
            base_name, ext = os.path.splitext(filename)
            
            for component in components:
                if "path" not in component:
                    component_name = component.get("name", "").replace(".", "_")
                    component["path"] = os.path.join(dir_path, f"{component_name}{ext}")
        
        return components
    
    def _assign_requirements_to_component(self, component: Dict[str, Any], 
                                        all_requirements: List[str],
                                        all_components: List[Dict[str, Any]]) -> List[str]:
        """
        Assign relevant requirements to a component
        
        Args:
            component: Component definition
            all_requirements: List of all requirements
            all_components: List of all components
            
        Returns:
            List of requirements assigned to this component
        """
        component_name = component.get("name", "").lower()
        component_type = component.get("type", "").lower()
        component_desc = component.get("description", "").lower()
        
        # Words that identify this component
        component_keywords = set(component_name.split("_") + 
                                component_type.split("_") + 
                                component_desc.split())
        
        # Filter requirements relevant to this component
        relevant_requirements = []
        for req in all_requirements:
            req_lower = req.lower()
            
            # Check if requirement mentions component words
            if any(keyword in req_lower for keyword in component_keywords if len(keyword) > 2):
                relevant_requirements.append(req)
                continue
                
            # For primary components, include general requirements
            if component.get("is_primary", False) and not any(
                any(keyword in req_lower for keyword in set(comp.get("name", "").lower().split("_"))
                    if len(keyword) > 2 and comp != component)
                for comp in all_components
            ):
                relevant_requirements.append(req)
        
        return relevant_requirements
    
    def _create_dependency_graph(self, components: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Create a dependency graph for the components
        
        Args:
            components: List of component definitions
            
        Returns:
            Dictionary representing the dependency graph
        """
        graph = {}
        
        # Initialize graph with empty dependencies
        for component in components:
            component_id = component.get("id")
            graph[component_id] = []
        
        # Add dependencies
        for component in components:
            component_id = component.get("id")
            dependencies = component.get("depends_on", [])
            
            # Convert name-based dependencies to IDs
            for dependency in dependencies:
                # If dependency is already an ID, use it directly
                if dependency.startswith("component_"):
                    graph[component_id].append(dependency)
                else:
                    # Find component by name
                    for dep_component in components:
                        if dep_component.get("name") == dependency:
                            graph[component_id].append(dep_component.get("id"))
                            break
        
        return graph
    
    def _determine_generation_order(self, dependency_graph: Dict[str, List[str]]) -> List[str]:
        """
        Determine the order in which components should be generated
        
        Args:
            dependency_graph: Dictionary representing the dependency graph
            
        Returns:
            List of component IDs in generation order
        """
        # Topological sort
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(node):
            if node in temp_visited:
                # Circular dependency detected
                return
            if node in visited:
                return
            
            temp_visited.add(node)
            
            # Visit dependencies
            for dep in dependency_graph.get(node, []):
                visit(dep)
            
            temp_visited.remove(node)
            visited.add(node)
            order.append(node)
        
        # Visit all nodes
        for node in dependency_graph:
            if node not in visited:
                visit(node)
        
        # Reverse to get the correct generation order
        order.reverse()
        return order