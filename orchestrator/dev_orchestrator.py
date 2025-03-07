"""
AI Code Development Orchestrator

This module contains classes for orchestrating the generation of multiple
scripts with project context awareness.
"""

import os
import sys
import json
import glob
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path
import importlib

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

class ProjectContext:
    """
    Analyzes and indexes project files and structures to provide context
    for script generation.
    """
    
    def __init__(self, project_dir: str, config: Dict[str, Any]):
        """
        Initialize the project context analyzer
        
        Args:
            project_dir: Path to the project directory to analyze
            config: Configuration dictionary with analysis settings
        """
        self.project_dir = os.path.abspath(project_dir)
        self.config = config
        self.file_index = {}
        self.directory_structure = {}
        self.dependencies = {}
        
    def analyze(self) -> Dict[str, Any]:
        """
        Analyze the project directory and build the context
        
        Returns:
            Dictionary containing the analysis results
        """
        self._index_files()
        self._analyze_directory_structure()
        self._analyze_dependencies()
        
        return {
            "file_index": self.file_index,
            "directory_structure": self.directory_structure,
            "dependencies": self.dependencies,
            "summary": self._generate_summary()
        }
    
    def _index_files(self) -> None:
        """Index all relevant files in the project directory"""
        excluded_dirs = self.config.get("project", {}).get("exclude_dirs", [])
        excluded_files = self.config.get("project", {}).get("exclude_files", [])
        max_files = self.config.get("project", {}).get("max_files_to_analyze", 50)
        max_size_kb = self.config.get("project", {}).get("max_file_size_kb", 500)
        
        # Convert glob patterns to regex patterns
        import fnmatch
        import re
        excluded_file_patterns = [fnmatch.translate(pattern) for pattern in excluded_files]
        
        file_count = 0
        
        for root, dirs, files in os.walk(self.project_dir):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in excluded_dirs]
            
            for file in files:
                # Skip files matching excluded patterns
                if any(re.match(pattern, file) for pattern in excluded_file_patterns):
                    continue
                
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.project_dir)
                
                # Skip files that are too large
                file_size_kb = os.path.getsize(file_path) / 1024
                if file_size_kb > max_size_kb:
                    continue
                
                # Add file to index
                self.file_index[rel_path] = {
                    "size": file_size_kb,
                    "type": self._get_file_type(file),
                    "path": rel_path,
                    "content": self._read_file_content(file_path)
                }
                
                file_count += 1
                if file_count >= max_files:
                    break
            
            if file_count >= max_files:
                break
    
    def _get_file_type(self, filename: str) -> str:
        """Determine the type of file based on extension"""
        ext = os.path.splitext(filename)[1].lower()
        
        # Map extensions to file types
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".html": "html",
            ".css": "css",
            ".md": "markdown",
            ".json": "json",
            ".txt": "text",
            ".yml": "yaml",
            ".yaml": "yaml",
            ".sh": "shell",
            ".bash": "shell",
            ".zsh": "shell",
            ".fish": "shell",
            ".sql": "sql",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "header",
            ".hpp": "header",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".rb": "ruby",
            ".php": "php"
        }
        
        return extension_map.get(ext, "unknown")
    
    def _read_file_content(self, file_path: str) -> str:
        """Read the content of a file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return f"[Error reading file: {str(e)}]"
    
    def _analyze_directory_structure(self) -> None:
        """Analyze the directory structure of the project"""
        self.directory_structure = {}
        
        for file_path in self.file_index:
            directory = os.path.dirname(file_path)
            
            # Skip empty directory paths
            if not directory:
                directory = "."
            
            # Add directory to structure
            if directory not in self.directory_structure:
                self.directory_structure[directory] = []
            
            # Add file to directory
            self.directory_structure[directory].append(os.path.basename(file_path))
    
    def _analyze_dependencies(self) -> None:
        """Analyze dependencies between files"""
        self.dependencies = {}
        
        for file_path, file_info in self.file_index.items():
            file_type = file_info["type"]
            content = file_info["content"]
            
            # Initialize dependencies for this file
            self.dependencies[file_path] = []
            
            # Check for imports/dependencies based on file type
            if file_type == "python":
                self._find_python_dependencies(file_path, content)
            elif file_type in ["javascript", "typescript"]:
                self._find_js_dependencies(file_path, content)
            elif file_type == "html":
                self._find_html_dependencies(file_path, content)
            # Add more file types as needed
    
    def _find_python_dependencies(self, file_path: str, content: str) -> None:
        """Find Python import dependencies"""
        import re
        
        # Pattern for Python imports
        patterns = [
            r"^import\s+([\w\.]+)",           # import module
            r"^from\s+([\w\.]+)\s+import",    # from module import
        ]
        
        for line in content.split('\n'):
            line = line.strip()
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    module_name = match.group(1)
                    
                    # Check if this is a local module
                    for other_file in self.file_index:
                        if other_file.endswith(f"{module_name.replace('.', '/')}.py"):
                            self.dependencies[file_path].append(other_file)
    
    def _find_js_dependencies(self, file_path: str, content: str) -> None:
        """Find JavaScript/TypeScript import dependencies"""
        import re
        
        # Pattern for JS imports
        patterns = [
            r"import.*from\s+['\"](.+)['\"]",           # import ... from 'module'
            r"require\s*\(\s*['\"](.+)['\"]",           # require('module')
        ]
        
        for line in content.split('\n'):
            line = line.strip()
            for pattern in patterns:
                matches = re.findall(pattern, line)
                for match in matches:
                    # Check if this is a local module
                    if not match.startswith('.'):
                        continue
                    
                    # Resolve relative path
                    base_dir = os.path.dirname(file_path)
                    target_path = os.path.normpath(os.path.join(base_dir, match))
                    
                    # Check for files that match this import
                    for other_file in self.file_index:
                        other_base = os.path.splitext(other_file)[0]
                        if other_base == target_path or other_file.startswith(f"{target_path}/"):
                            self.dependencies[file_path].append(other_file)
    
    def _find_html_dependencies(self, file_path: str, content: str) -> None:
        """Find HTML dependencies (scripts, stylesheets, etc.)"""
        import re
        
        # Patterns for HTML dependencies
        patterns = [
            r"<script\s+src=['\"](.+?)['\"]",           # <script src="...">
            r"<link\s+.*href=['\"](.+?)['\"]",          # <link href="...">
            r"<img\s+.*src=['\"](.+?)['\"]",            # <img src="...">
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                # Skip absolute URLs
                if match.startswith(('http', '//')):
                    continue
                
                # Resolve relative path
                base_dir = os.path.dirname(file_path)
                target_path = os.path.normpath(os.path.join(base_dir, match))
                
                # Check for files that match this dependency
                for other_file in self.file_index:
                    if other_file == target_path:
                        self.dependencies[file_path].append(other_file)
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate a summary of the project analysis"""
        # Count files by type
        file_types = {}
        for file_info in self.file_index.values():
            file_type = file_info["type"]
            file_types[file_type] = file_types.get(file_type, 0) + 1
        
        # Get directory counts
        directories = list(self.directory_structure.keys())
        
        # Count dependencies
        dependency_counts = {file_path: len(deps) for file_path, deps in self.dependencies.items()}
        
        return {
            "total_files": len(self.file_index),
            "file_types": file_types,
            "total_directories": len(directories),
            "directories": directories,
            "dependency_counts": dependency_counts
        }


class ScriptGenerator:
    """
    Handles AI model interactions for script generation
    """
    
    def __init__(self, provider: Optional[BaseModelProvider] = None, config: Dict[str, Any] = None):
        """
        Initialize the script generator
        
        Args:
            provider: AI model provider to use
            config: Configuration dictionary with generation settings
        """
        self.provider = provider
        self.config = config or {}
        
    async def generate_script(self, 
                             script_definition: Dict[str, Any], 
                             project_context: Dict[str, Any],
                             iteration: int = 1) -> str:
        """
        Generate a script based on the definition and project context
        
        Args:
            script_definition: Dictionary defining the script requirements
            project_context: Project context from the analyzer
            iteration: Current iteration number
            
        Returns:
            String containing the generated script
        """
        # Handle the case where we don't have a provider
        if not self.provider:
            return self._fallback_script_generation(script_definition)
        
        # Construct the prompt
        prompt = self._construct_prompt(script_definition, project_context, iteration)
        
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
            
            # Extract code from the response
            code_blocks = await self.provider.extract_code(response)
            
            if code_blocks:
                return code_blocks[0]  # Return the first code block
            else:
                # If no code blocks found, return the full response
                return response
            
        except Exception as e:
            print(f"Error generating script: {e}")
            return f"# Error generating script: {str(e)}"
    
    def _fallback_script_generation(self, script_definition: Dict[str, Any]) -> str:
        """Fallback method when no provider is available"""
        script_name = script_definition.get("name", "unknown")
        return f"""
# {script_name}
# 
# This is a placeholder script. The script generator could not connect 
# to an AI model provider. Please ensure you have set up the appropriate
# API keys and dependencies.
#
# Script definition:
# {json.dumps(script_definition, indent=2)}
"""
    
    def _construct_system_prompt(self) -> str:
        """Construct the system prompt for the AI model"""
        return """You are an expert software developer tasked with generating high-quality code for a software project.
Your task is to generate a script based on the provided definition and project context.
Follow these guidelines:
1. Write clean, efficient, and well-documented code
2. Include appropriate error handling and input validation
3. Follow best practices for the language/framework being used
4. Keep the code modular and maintainable
5. Include detailed comments explaining complex parts of the code
6. Ensure the code meets the requirements specified in the script definition

Return ONLY the code, without additional explanations or markdown formatting.
"""
    
    def _construct_prompt(self, 
                         script_definition: Dict[str, Any],
                         project_context: Dict[str, Any],
                         iteration: int) -> str:
        """
        Construct the prompt for the AI model
        
        Args:
            script_definition: Dictionary defining the script requirements
            project_context: Project context from the analyzer
            iteration: Current iteration number
            
        Returns:
            String containing the constructed prompt
        """
        # Extract relevant info
        script_name = script_definition.get("name", "")
        script_path = script_definition.get("path", "")
        description = script_definition.get("description", "")
        requirements = script_definition.get("requirements", [])
        related_files = script_definition.get("related_files", [])
        
        # Start with the basic script definition
        prompt = f"""Generate a script named '{script_name}' to be saved at '{script_path}'.

Description:
{description}

Requirements:
"""
        
        # Add requirements
        for req in requirements:
            prompt += f"- {req}\n"
        
        # Add related files context
        if related_files:
            prompt += "\nRelated files content:\n"
            for file_path in related_files:
                if file_path in project_context.get("file_index", {}):
                    file_info = project_context["file_index"][file_path]
                    prompt += f"\n--- {file_path} ---\n"
                    prompt += file_info.get("content", "[File content not available]")
                    prompt += "\n--- End of file ---\n"
        
        # Add project summary
        summary = project_context.get("summary", {})
        if summary:
            prompt += "\nProject summary:\n"
            prompt += f"- Total files: {summary.get('total_files', 0)}\n"
            prompt += f"- Directories: {', '.join(summary.get('directories', [])[:5])}\n"
            
            file_types = summary.get("file_types", {})
            if file_types:
                prompt += "- File types: "
                prompt += ", ".join([f"{type}: {count}" for type, count in file_types.items()])
                prompt += "\n"
        
        # Add iteration context for improvements
        if iteration > 1:
            prompt += f"\nThis is iteration #{iteration}. Please improve the previous version."
        
        return prompt


class CodeReviewer:
    """
    Reviews and provides feedback on generated scripts
    """
    
    def __init__(self, provider: Optional[BaseModelProvider] = None, config: Dict[str, Any] = None):
        """
        Initialize the code reviewer
        
        Args:
            provider: AI model provider to use
            config: Configuration dictionary with review settings
        """
        self.provider = provider
        self.config = config or {}
        
    async def review_script(self, 
                          script: str,
                          script_definition: Dict[str, Any]) -> Dict[str, Any]:
        """
        Review a generated script and provide feedback
        
        Args:
            script: The script content to review
            script_definition: Dictionary defining the script requirements
            
        Returns:
            Dictionary containing review results
        """
        # Check if reviews are enabled
        if not self.config.get("review", {}).get("enabled", True):
            return {
                "score": 1.0,
                "feedback": "Code review is disabled",
                "passed": True
            }
        
        # Handle the case where we don't have a provider
        if not self.provider:
            return self._fallback_review(script, script_definition)
        
        # Construct the prompt
        prompt = self._construct_review_prompt(script, script_definition)
        
        # Generate the review
        try:
            system_prompt = self._construct_system_prompt()
            
            response = await self.provider.generate_response(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3,  # Lower temperature for more consistent reviews
                max_tokens=2000
            )
            
            # Parse the review
            review_result = self._parse_review(response)
            
            # Determine if the script passed the review
            min_score = self.config.get("review", {}).get("min_accepted_score", 0.7)
            review_result["passed"] = review_result["score"] >= min_score
            
            return review_result
            
        except Exception as e:
            print(f"Error reviewing script: {e}")
            return {
                "score": 0.5,
                "feedback": f"Error during review: {str(e)}",
                "passed": False
            }
    
    def _fallback_review(self, script: str, script_definition: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback method when no provider is available"""
        return {
            "score": 0.8,
            "feedback": "Automatic review not available. Using default passing score.",
            "passed": True
        }
    
    def _construct_system_prompt(self) -> str:
        """Construct the system prompt for the AI model"""
        return """You are an expert code reviewer tasked with evaluating the quality of a script.
Your task is to review the provided script against its requirements and provide a score and feedback.
Follow these guidelines:
1. Evaluate the code's functionality, does it meet the specified requirements?
2. Assess code quality, including readability, maintainability, and efficiency
3. Check for proper error handling and input validation
4. Look for adequate documentation and comments
5. Identify any potential bugs or issues

Provide your review in the following format:
SCORE: [0.0-1.0]
FEEDBACK:
- [Your feedback points]

The score should be a number between 0.0 (completely fails requirements) and 1.0 (perfect implementation).
"""
    
    def _construct_review_prompt(self, 
                                script: str,
                                script_definition: Dict[str, Any]) -> str:
        """
        Construct the review prompt for the AI model
        
        Args:
            script: The script content to review
            script_definition: Dictionary defining the script requirements
            
        Returns:
            String containing the constructed prompt
        """
        # Extract relevant info
        script_name = script_definition.get("name", "")
        description = script_definition.get("description", "")
        requirements = script_definition.get("requirements", [])
        
        # Construct the prompt
        prompt = f"""Review the following script named '{script_name}'.

Script requirements:
{description}

Specific requirements:
"""
        
        # Add requirements
        for req in requirements:
            prompt += f"- {req}\n"
        
        # Add criteria weights
        criteria = self.config.get("review", {}).get("criteria", {})
        if criteria:
            prompt += "\nReview criteria weights:\n"
            for criterion, weight in criteria.items():
                prompt += f"- {criterion}: {weight}\n"
        
        # Add the script to review
        prompt += f"\nScript to review:\n{script}\n"
        
        return prompt
    
    def _parse_review(self, review_text: str) -> Dict[str, Any]:
        """
        Parse the review response from the AI model
        
        Args:
            review_text: The review text from the AI model
            
        Returns:
            Dictionary containing the parsed review
        """
        # Extract the score
        import re
        score_match = re.search(r"SCORE:\s*([\d\.]+)", review_text)
        score = 0.7  # Default score
        
        if score_match:
            try:
                score = float(score_match.group(1))
                # Ensure score is in range [0, 1]
                score = max(0.0, min(1.0, score))
            except ValueError:
                pass
        
        # Extract feedback
        feedback = review_text
        feedback_match = re.search(r"FEEDBACK:(.*)", review_text, re.DOTALL)
        if feedback_match:
            feedback = feedback_match.group(1).strip()
        
        return {
            "score": score,
            "feedback": feedback
        }


class TaskOrchestrator:
    """
    Coordinates the workflow of analysis, generation, and review
    """
    
    def __init__(self, provider: Optional[BaseModelProvider] = None, config_path: str = None):
        """
        Initialize the task orchestrator
        
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
                "config",
                "orchestrator_config.json"
            )
            if os.path.exists(default_config):
                self._load_config(default_config)
        
        # Initialize components
        self.analyzer = None  # Will be initialized for each project
        self.generator = ScriptGenerator(provider=provider, config=self.config)
        self.reviewer = CodeReviewer(provider=provider, config=self.config)
    
    def _load_config(self, config_path: str) -> None:
        """Load configuration from a JSON file"""
        try:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        except Exception as e:
            print(f"Error loading configuration from {config_path}: {e}")
            # Use default empty config
            self.config = {}
    
    async def orchestrate(self, 
                         project_dir: str, 
                         script_definitions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Orchestrate the script generation process
        
        Args:
            project_dir: Directory of the project to analyze
            script_definitions: List of script definitions to generate
            
        Returns:
            Dictionary containing the orchestration results
        """
        results = {
            "successful_scripts": [],
            "failed_scripts": [],
            "project_analysis": {}
        }
        
        # Initialize the project analyzer
        self.analyzer = ProjectContext(project_dir, self.config)
        
        # Analyze the project
        print(f"Analyzing project directory: {project_dir}")
        project_context = self.analyzer.analyze()
        results["project_analysis"] = project_context.get("summary", {})
        
        # Sort script definitions based on dependencies
        sorted_scripts = self._sort_scripts_by_dependency(script_definitions)
        
        # Generate scripts
        for script_def in sorted_scripts:
            script_name = script_def.get("name", "unknown")
            script_path = script_def.get("path", f"generated_{script_name}")
            
            print(f"Generating script: {script_name}")
            
            # Get the number of iterations
            iterations = self.config.get("generation", {}).get("iterations", 1)
            
            # Generate and improve the script through iterations
            script_content = None
            for iteration in range(1, iterations + 1):
                print(f"  Iteration {iteration}/{iterations}")
                
                # Generate script
                script_content = await self.generator.generate_script(
                    script_definition=script_def,
                    project_context=project_context,
                    iteration=iteration
                )
                
                # Skip review for intermediate iterations
                if iteration < iterations:
                    continue
                
                # Review final script
                print(f"  Reviewing script: {script_name}")
                review_result = await self.reviewer.review_script(
                    script=script_content,
                    script_definition=script_def
                )
                
                # Check if script passed the review
                if review_result.get("passed", False):
                    # Save the script
                    full_path = os.path.join(project_dir, script_path)
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    
                    with open(full_path, 'w') as f:
                        f.write(script_content)
                    
                    print(f"  ✓ Script saved to: {full_path}")
                    
                    # Add to successful scripts
                    results["successful_scripts"].append({
                        "name": script_name,
                        "path": script_path,
                        "score": review_result.get("score", 0),
                        "feedback": review_result.get("feedback", "")
                    })
                else:
                    print(f"  ✗ Script failed review: {script_name}")
                    
                    # Add to failed scripts
                    results["failed_scripts"].append({
                        "name": script_name,
                        "path": script_path,
                        "score": review_result.get("score", 0),
                        "feedback": review_result.get("feedback", "")
                    })
        
        return results
    
    def _sort_scripts_by_dependency(self, script_definitions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sort script definitions based on their dependencies
        
        Args:
            script_definitions: List of script definitions to sort
            
        Returns:
            Sorted list of script definitions
        """
        # Build dependency graph
        graph = {}
        for i, script in enumerate(script_definitions):
            script_path = script.get("path", "")
            graph[script_path] = {
                "index": i,
                "dependencies": script.get("dependencies", [])
            }
        
        # Perform topological sort
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
            for dep in graph.get(node, {}).get("dependencies", []):
                visit(dep)
            
            temp_visited.remove(node)
            visited.add(node)
            order.append(node)
        
        # Visit all nodes
        for node in graph:
            if node not in visited:
                visit(node)
        
        # Reverse the order to get the correct dependency order
        order.reverse()
        
        # Map back to original script definitions
        sorted_scripts = []
        for path in order:
            index = graph.get(path, {}).get("index")
            if index is not None:
                sorted_scripts.append(script_definitions[index])
        
        # Add any scripts that weren't in the graph
        for script in script_definitions:
            script_path = script.get("path", "")
            if script_path not in graph:
                sorted_scripts.append(script)
        
        return sorted_scripts
