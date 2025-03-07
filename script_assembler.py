"""
Script Assembler
Module for assembling script components into coherent scripts
"""

import os
import re
import ast
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path

# Setup logging
logger = logging.getLogger(__name__)


class ScriptAssembler:
    """
    Assembles script components into coherent scripts, handling imports,
    references, and ensuring code consistency
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the script assembler
        
        Args:
            config: Configuration dictionary with assembler settings
        """
        self.config = config or {}
    
    def assemble_script(self, 
                       original_definition: Dict[str, Any],
                       components: List[Dict[str, Any]],
                       component_scripts: Dict[str, str]) -> Dict[str, Any]:
        """
        Assemble a complete script from generated components
        
        Args:
            original_definition: Original script definition
            components: List of component definitions
            component_scripts: Dictionary mapping component IDs to their generated scripts
            
        Returns:
            Dictionary with assembled script and assembly info
        """
        # Identify primary component
        primary_component = self._identify_primary_component(components)
        
        if not primary_component:
            return {
                "success": False,
                "error": "No primary component identified",
                "assembled_script": "",
                "missing_components": []
            }
        
        # Check for missing component scripts
        missing_components = []
        for component in components:
            component_id = component.get("id")
            if component_id not in component_scripts:
                missing_components.append(component_id)
        
        if missing_components:
            return {
                "success": False,
                "error": f"Missing component scripts: {', '.join(missing_components)}",
                "assembled_script": "",
                "missing_components": missing_components
            }
        
        # Get script language from file extension
        script_name = original_definition.get("name", "script")
        language = self._detect_language(script_name)
        
        # Assemble the script based on language
        if language == "python":
            result = self._assemble_python_script(
                primary_component,
                components,
                component_scripts
            )
        elif language in ["javascript", "typescript"]:
            result = self._assemble_js_script(
                primary_component,
                components,
                component_scripts
            )
        else:
            # Default to generic assembly
            result = self._assemble_generic_script(
                primary_component,
                components,
                component_scripts
            )
        
        # Validate the assembled script
        validation = self.validate_assembled_script(result["assembled_script"], language)
        result["validation"] = validation
        
        # Add completion status
        result["success"] = validation["valid"]
        if not validation["valid"]:
            result["error"] = f"Assembled script failed validation: {validation['error']}"
        
        return result
    
    def _identify_primary_component(self, components: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Identify the primary component from a list of components
        
        Args:
            components: List of component definitions
            
        Returns:
            Dictionary containing the primary component, or None if not found
        """
        # First, look for component explicitly marked as primary
        for component in components:
            if component.get("is_primary", False):
                return component
        
        # If no primary marked, use heuristics
        # Look for a component named "main" or containing "main"
        for component in components:
            component_name = component.get("name", "").lower()
            if "main" in component_name:
                return component
        
        # If still not found, use the first component
        if components:
            return components[0]
        
        return None
    
    def _detect_language(self, script_name: str) -> str:
        """
        Detect the programming language from the script name
        
        Args:
            script_name: Name of the script
            
        Returns:
            String representing the detected language
        """
        extension = os.path.splitext(script_name)[1].lower()
        
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".sh": "shell",
            ".bash": "shell",
            ".html": "html",
            ".css": "css",
            ".sql": "sql",
            ".rb": "ruby",
            ".go": "go",
            ".java": "java",
            ".php": "php",
            ".c": "c",
            ".cpp": "cpp",
            ".cs": "csharp"
        }
        
        return language_map.get(extension, "unknown")
    
    def _assemble_python_script(self,
                               primary_component: Dict[str, Any],
                               components: List[Dict[str, Any]],
                               component_scripts: Dict[str, str]) -> Dict[str, Any]:
        """
        Assemble a Python script from components
        
        Args:
            primary_component: The primary component
            components: List of all components
            component_scripts: Dictionary mapping component IDs to scripts
            
        Returns:
            Dictionary with assembled script and assembly info
        """
        primary_id = primary_component.get("id")
        primary_script = component_scripts.get(primary_id, "")
        
        # Parse the primary script
        try:
            primary_ast = ast.parse(primary_script)
        except SyntaxError as e:
            return {
                "assembled_script": primary_script,
                "imports": [],
                "imported_components": [],
                "error": f"Primary component has syntax error: {str(e)}"
            }
        
        # Collect imports from primary script
        existing_imports = set()
        for node in ast.walk(primary_ast):
            if isinstance(node, ast.Import):
                for name in node.names:
                    existing_imports.add(name.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    existing_imports.add(node.module)
        
        # Identify which components are imported/referenced in the primary script
        imported_components = []
        for component in components:
            if component.get("id") == primary_id:
                continue  # Skip primary component
            
            component_name = component.get("name")
            if not component_name:
                continue
                
            # Clean up component name for use as module name
            module_name = component_name.replace("-", "_").lower()
            
            # Check if this component is imported in the primary script
            if module_name in existing_imports or f"{module_name}.py" in primary_script:
                imported_components.append(component.get("id"))
        
        # Handle additional components - make each component a separate module
        imports_block = ""
        imported_modules = []
        for component_id in imported_components:
            component = next((c for c in components if c.get("id") == component_id), None)
            if not component:
                continue
                
            component_name = component.get("name", "")
            module_name = component_name.replace("-", "_").lower()
            component_script = component_scripts.get(component_id, "")
            
            # Create a Python module for this component
            module_path = f"{module_name}.py"
            
            # Write the component to its own file
            self._write_component_file(module_path, component_script)
            
            # Build import statement if not already present
            if module_name not in existing_imports:
                imports_block += f"import {module_name}\n"
            
            imported_modules.append({
                "module_name": module_name,
                "component_id": component_id,
                "component_name": component_name,
                "path": module_path
            })
        
        # Assemble the final script with new imports
        assembled_script = primary_script
        if imports_block:
            # Insert imports after existing imports
            # Find where to insert new imports (after last import or at start)
            import_insert_pos = 0
            for i, node in enumerate(primary_ast.body):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    # Keep track of the last import
                    if node.end_lineno:
                        import_insert_pos = node.end_lineno
                    else:
                        # Fall back to line number if end_lineno not available
                        import_insert_pos = node.lineno
            
            if import_insert_pos > 0:
                # Insert after the last import
                lines = assembled_script.split('\n')
                lines.insert(import_insert_pos, imports_block)
                assembled_script = '\n'.join(lines)
            else:
                # Insert at the beginning, after docstring if present
                if primary_ast.body and isinstance(primary_ast.body[0], ast.Expr) and isinstance(primary_ast.body[0].value, ast.Str):
                    # Add imports after docstring
                    docstring_end = primary_ast.body[0].end_lineno if hasattr(primary_ast.body[0], 'end_lineno') else primary_ast.body[0].lineno
                    lines = assembled_script.split('\n')
                    lines.insert(docstring_end, "\n" + imports_block)
                    assembled_script = '\n'.join(lines)
                else:
                    # Add imports at the beginning
                    assembled_script = imports_block + "\n" + assembled_script
        
        return {
            "assembled_script": assembled_script,
            "imports": list(existing_imports),
            "imported_components": imported_components,
            "modules": imported_modules
        }
    
    def _assemble_js_script(self,
                          primary_component: Dict[str, Any],
                          components: List[Dict[str, Any]],
                          component_scripts: Dict[str, str]) -> Dict[str, Any]:
        """
        Assemble a JavaScript/TypeScript script from components
        
        Args:
            primary_component: The primary component
            components: List of all components
            component_scripts: Dictionary mapping component IDs to scripts
            
        Returns:
            Dictionary with assembled script and assembly info
        """
        primary_id = primary_component.get("id")
        primary_script = component_scripts.get(primary_id, "")
        
        # Extract existing imports using regex
        import_regex = r'(import\s+.*?from\s+[\'"].*?[\'"];|require\s*\(\s*[\'"].*?[\'"]\s*\))'
        existing_imports = set(re.findall(import_regex, primary_script))
        
        # Identify which components are imported/referenced in the primary script
        imported_components = []
        for component in components:
            if component.get("id") == primary_id:
                continue  # Skip primary component
            
            component_name = component.get("name")
            if not component_name:
                continue
                
            # Clean up component name for use as module name
            module_name = component_name.replace("-", "_").toLowerCase()
            
            # Check if this component is imported in the primary script
            is_imported = False
            for imp in existing_imports:
                if f"'{module_name}'" in imp or f'"{module_name}"' in imp:
                    is_imported = True
                    break
                    
            if is_imported or f"{module_name}.js" in primary_script:
                imported_components.append(component.get("id"))
        
        # Handle additional components - make each component a separate module
        imports_block = ""
        imported_modules = []
        for component_id in imported_components:
            component = next((c for c in components if c.get("id") == component_id), None)
            if not component:
                continue
                
            component_name = component.get("name", "")
            module_name = component_name.replace("-", "_").lower()
            component_script = component_scripts.get(component_id, "")
            
            # Ensure the component exports something
            if "export" not in component_script:
                # Add default export if none exists
                component_script += "\n\nexport default " + module_name + ";\n"
            
            # Create a JS module for this component
            module_path = f"{module_name}.js"
            
            # Write the component to its own file
            self._write_component_file(module_path, component_script)
            
            # Build import statement if not already present
            import_statement = f"import {{ {module_name} }} from './{module_name}';"
            is_already_imported = False
            for imp in existing_imports:
                if module_name in imp:
                    is_already_imported = True
                    break
                    
            if not is_already_imported:
                imports_block += import_statement + "\n"
            
            imported_modules.append({
                "module_name": module_name,
                "component_id": component_id,
                "component_name": component_name,
                "path": module_path
            })
        
        # Assemble the final script with new imports
        assembled_script = primary_script
        if imports_block:
            # Find the position to insert new imports
            # We'll insert after the last existing import or at the beginning
            last_import_pos = 0
            for match in re.finditer(import_regex, assembled_script):
                last_import_pos = max(last_import_pos, match.end())
            
            if last_import_pos > 0:
                # Insert after the last import
                assembled_script = assembled_script[:last_import_pos] + "\n" + imports_block + assembled_script[last_import_pos:]
            else:
                # Insert at the beginning
                assembled_script = imports_block + "\n" + assembled_script
        
        return {
            "assembled_script": assembled_script,
            "imports": list(existing_imports),
            "imported_components": imported_components,
            "modules": imported_modules
        }
    
    def _assemble_generic_script(self,
                               primary_component: Dict[str, Any],
                               components: List[Dict[str, Any]],
                               component_scripts: Dict[str, str]) -> Dict[str, Any]:
        """
        Assemble a generic script from components (for languages without modules)
        
        Args:
            primary_component: The primary component
            components: List of all components
            component_scripts: Dictionary mapping component IDs to scripts
            
        Returns:
            Dictionary with assembled script and assembly info
        """
        primary_id = primary_component.get("id")
        primary_script = component_scripts.get(primary_id, "")
        
        # For generic scripts, we'll simply concatenate the scripts
        # with separation markers
        assembled_script = f"/* {primary_component.get('name', 'Main Component')} */\n\n"
        assembled_script += primary_script + "\n\n"
        
        # Add other components
        imported_components = []
        for component in components:
            if component.get("id") == primary_id:
                continue  # Skip primary component
                
            component_id = component.get("id")
            component_name = component.get("name", "Unnamed Component")
            component_script = component_scripts.get(component_id, "")
            
            if component_script:
                assembled_script += f"\n\n/* {component_name} */\n\n"
                assembled_script += component_script
                imported_components.append(component_id)
        
        return {
            "assembled_script": assembled_script,
            "imports": [],
            "imported_components": imported_components,
            "modules": []
        }
    
    def _write_component_file(self, path: str, content: str) -> None:
        """
        Write a component script to a file
        
        Args:
            path: File path
            content: File content
        """
        try:
            output_dir = self.config.get("output", {}).get("component_dir", "components")
            os.makedirs(output_dir, exist_ok=True)
            
            full_path = os.path.join(output_dir, path)
            with open(full_path, 'w') as f:
                f.write(content)
                
            logger.info(f"Wrote component to {full_path}")
        except Exception as e:
            logger.error(f"Error writing component file {path}: {e}")
    
    def validate_assembled_script(self, script: str, language: str) -> Dict[str, Any]:
        """
        Validate the assembled script for syntax errors
        
        Args:
            script: The assembled script content
            language: The script language
            
        Returns:
            Dictionary with validation results
        """
        if language == "python":
            return self._validate_python_script(script)
        elif language in ["javascript", "typescript"]:
            return self._validate_js_script(script)
        else:
            # For other languages, we can't validate syntax
            return {
                "valid": True,
                "error": None,
                "warnings": ["Cannot validate syntax for {language} scripts"]
            }
    
    def _validate_python_script(self, script: str) -> Dict[str, Any]:
        """
        Validate a Python script for syntax errors
        
        Args:
            script: The script content
            
        Returns:
            Dictionary with validation results
        """
        try:
            ast.parse(script)
            return {
                "valid": True,
                "error": None,
                "warnings": []
            }
        except SyntaxError as e:
            return {
                "valid": False,
                "error": str(e),
                "error_line": e.lineno,
                "error_offset": e.offset,
                "error_text": e.text,
                "warnings": []
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "warnings": []
            }
    
    def _validate_js_script(self, script: str) -> Dict[str, Any]:
        """
        Validate a JavaScript script for basic syntax errors
        
        Args:
            script: The script content
            
        Returns:
            Dictionary with validation results
        """
        # Simple validation for obvious syntax errors
        # For a real implementation, you might want to use a proper JS parser
        
        warnings = []
        
        # Check for mismatched braces
        opening_braces = script.count('{')
        closing_braces = script.count('}')
        if opening_braces != closing_braces:
            return {
                "valid": False,
                "error": f"Mismatched braces: {opening_braces} opening vs {closing_braces} closing",
                "warnings": warnings
            }
        
        # Check for mismatched parentheses
        opening_parens = script.count('(')
        closing_parens = script.count(')')
        if opening_parens != closing_parens:
            return {
                "valid": False,
                "error": f"Mismatched parentheses: {opening_parens} opening vs {closing_parens} closing",
                "warnings": warnings
            }
        
        # Check for mismatched brackets
        opening_brackets = script.count('[')
        closing_brackets = script.count(']')
        if opening_brackets != closing_brackets:
            return {
                "valid": False,
                "error": f"Mismatched brackets: {opening_brackets} opening vs {closing_brackets} closing",
                "warnings": warnings
            }
        
        # Check for obvious missing semicolons (very basic check)
        if not script.strip().endswith(';') and not script.strip().endswith('}'):
            warnings.append("Script may be missing a trailing semicolon")
        
        return {
            "valid": True,
            "error": None,
            "warnings": warnings
        }


# Test the script assembler if run directly
if __name__ == "__main__":
    assembler = ScriptAssembler()
    
    # Example components and scripts
    test_components = [
        {
            "id": "component_0",
            "name": "data_processor",
            "type": "main",
            "description": "Main entry point for the data processor",
            "is_primary": True
        },
        {
            "id": "component_1",
            "name": "data_processor_reader",
            "type": "reader",
            "description": "Data input reader"
        },
        {
            "id": "component_2",
            "name": "data_processor_processor",
            "type": "processor",
            "description": "Data processing logic",
            "depends_on": ["data_processor_reader"]
        }
    ]
    
    test_scripts = {
        "component_0": """#!/usr/bin/env python3
\"\"\"
Data Processor - Main module for processing data
\"\"\"

import os
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description='Process data files')
    parser.add_argument('--input', required=True, help='Input file path')
    parser.add_argument('--output', required=True, help='Output file path')
    parser.add_argument('--format', choices=['csv', 'json', 'sql'], default='csv', help='Output format')
    args = parser.parse_args()
    
    # TODO: Process the data using components
    
    print(f"Processing {args.input} to {args.output} in {args.format} format")
    
if __name__ == "__main__":
    main()
""",
        "component_1": """\"\"\"
Data Reader Component
Handles reading data from different file formats
\"\"\"

import csv
import json
import os

class DataReader:
    def __init__(self, file_path):
        self.file_path = file_path
        
    def read(self):
        \"\"\"Read data from the file\"\"\"
        file_ext = os.path.splitext(self.file_path)[1].lower()
        
        if file_ext == '.csv':
            return self._read_csv()
        elif file_ext == '.json':
            return self._read_json()
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
    
    def _read_csv(self):
        \"\"\"Read data from CSV file\"\"\"
        data = []
        with open(self.file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        return data
    
    def _read_json(self):
        \"\"\"Read data from JSON file\"\"\"
        with open(self.file_path, 'r') as f:
            return json.load(f)
"""
    }
    
    # Test assembly
    original_definition = {
        "name": "data_processor.py",
        "description": "A data processing script that handles CSV and JSON data.",
        "requirements": [
            "Support CSV and JSON input formats",
            "Clean data by removing duplicates and handling missing values"
        ]
    }
    
    result = assembler.assemble_script(original_definition, test_components, test_scripts)
    print("Assembly Result:")
    print(f"Success: {result.get('success')}")
    if not result.get('success'):
        print(f"Error: {result.get('error')}")
    
    print("\nAssembled Script:")
    print(result.get('assembled_script'))
    
    print("\nValidation:")
    validation = result.get('validation', {})
    print(f"Valid: {validation.get('valid')}")
    if not validation.get('valid'):
        print(f"Error: {validation.get('error')}")
    
    warnings = validation.get('warnings', [])
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")
