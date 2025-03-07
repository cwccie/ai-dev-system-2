# AI Code Development Orchestrator

The Orchestrator component analyzes project structure and generates multiple scripts with project context awareness.

## Features

- **Project Analysis**: Analyzes project structure, files, and dependencies
- **Multi-Script Generation**: Generates multiple scripts with dependency awareness
- **Code Review**: Reviews generated scripts and provides feedback
- **Iterative Improvement**: Improves scripts through multiple iterations

## Usage

### Configuration

The orchestrator can be configured using a JSON configuration file at `orchestrator/config/orchestrator_config.json`.

Example configuration:

```json
{
  "model": {
    "provider": "claude",
    "name": "claude-3-7-sonnet-20250219",
    "temperature": 0.7,
    "max_tokens": 4000
  },
  "project": {
    "exclude_dirs": [
      "node_modules",
      "venv",
      ".git"
    ],
    "exclude_files": [
      "*.pyc",
      "*.log"
    ],
    "max_files_to_analyze": 50,
    "max_file_size_kb": 500
  },
  "generation": {
    "iterations": 2,
    "parallel_scripts": 1,
    "add_comments": true,
    "include_tests": false
  },
  "review": {
    "enabled": true,
    "criteria": {
      "functionality": 0.4,
      "code_quality": 0.3,
      "documentation": 0.3
    },
    "min_accepted_score": 0.7
  }
}
```

### Script Definitions

Script definitions describe the scripts to be generated. Each definition includes:

- `name`: Name of the script
- `path`: Path where the script should be saved
- `description`: Detailed description of the script's purpose
- `requirements`: List of specific requirements
- `related_files`: List of related files to include in context
- `dependencies`: List of other scripts this script depends on

Example script definitions:

```json
[
  {
    "name": "data_processor.py",
    "path": "src/processing/data_processor.py",
    "description": "Process input data and prepare it for analysis",
    "requirements": [
      "Handle CSV and JSON input formats",
      "Clean and normalize data",
      "Handle missing values"
    ],
    "related_files": [
      "src/models/data_model.py"
    ]
  },
  {
    "name": "data_analyzer.py",
    "path": "src/analysis/data_analyzer.py",
    "description": "Analyze processed data and generate reports",
    "requirements": [
      "Calculate statistics",
      "Generate visualizations",
      "Export results to CSV"
    ],
    "dependencies": [
      "src/processing/data_processor.py"
    ]
  }
]
```

### Command-Line Usage

You can run the orchestrator directly using the provided shell script:

```bash
./run_orchestrator.sh /path/to/project /path/to/script_definitions.json
```

Or using Python:

```bash
python dev_orchestrator.py --project-dir /path/to/project --script-defs /path/to/script_definitions.json
```

### Programmatic Usage

You can also use the orchestrator programmatically:

```python
from orchestrator.dev_orchestrator import TaskOrchestrator
from model_providers import get_provider

# Initialize provider
provider = get_provider("claude")

# Initialize orchestrator
orchestrator = TaskOrchestrator(provider=provider)

# Define scripts
script_definitions = [
    {
        "name": "data_processor.py",
        "path": "src/processing/data_processor.py",
        "description": "Process input data and prepare it for analysis",
        "requirements": [
            "Handle CSV and JSON input formats",
            "Clean and normalize data",
            "Handle missing values"
        ]
    }
]

# Generate scripts
results = orchestrator.orchestrate(
    project_dir="/path/to/project",
    script_definitions=script_definitions
)
```

## Components

The orchestrator consists of several main classes:

- **ProjectContext**: Analyzes and indexes project files and structures
- **ScriptGenerator**: Handles AI model interactions for script generation
- **CodeReviewer**: Reviews and provides feedback on generated scripts
- **TaskOrchestrator**: Coordinates the workflow of analysis, generation, and review

## Dependencies

- Python 3.6+
- anthropic>=0.5.0
- tqdm>=4.65.0

## Troubleshooting

- **API Key Issues**: Ensure the appropriate API key is set in your environment
- **Project Analysis**: For large projects, adjust `max_files_to_analyze` and `max_file_size_kb`
- **Memory Issues**: Reduce `max_files_to_analyze` if you encounter memory problems
- **Generation Quality**: Increase `iterations` for better results, or adjust `temperature`
