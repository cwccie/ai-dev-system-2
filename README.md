# AI Code Development Orchestration System

An AI-powered development framework that leverages various AI models to generate scripts for software projects. The system provides tools for both comprehensive multi-script generation with project context awareness and simpler individual script creation.

## Features

- **User Authentication**: Secure login system restricts access to authorized users
- **Multi-Model Support**: Use Claude (Anthropic), GPT (OpenAI), or DeepSeek for code generation
- **Orchestrator Component**: Generate multiple interdependent scripts with project context awareness
- **Script Agent**: Generate individual scripts with simple specifications
- **Web Interface**: User-friendly UI for interacting with the system
- **API Key Management**: Securely store and manage API keys

## System Architecture

The system consists of the following main components:

1. **Model Providers Module**: Abstract layer for interacting with different AI models
2. **Orchestrator Component**: Analyzes project structure and generates multiple scripts
3. **Script Agent Component**: Simpler component for generating individual scripts
4. **Web Interface**: Flask-based UI for interacting with the system

## Installation

### Prerequisites

- Python 3.6 or higher
- pip3
- API key for at least one of: Anthropic (Claude), OpenAI (GPT), or DeepSeek

### Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/ai-dev-system-2
   cd ai-dev-orchestration
   ```

2. Run the setup script:
   ```bash
   chmod +x run.sh
   ./run.sh
   ```

The script will:
- Check for Python and pip installation
- Create a virtual environment
- Install required dependencies
- Prompt for API keys (if not already set)
- Create necessary directories and files
- Start the Flask application

## Usage

After starting the application, navigate to http://localhost:9000 in your web browser. You'll be prompted to log in with the following credentials:

Username: `cwccie`  
Password: `password` (you can change this in the app.py file)

### Using the Orchestrator

The orchestrator is designed for generating multiple interdependent scripts:

1. Navigate to the Orchestrator page
2. Specify the project directory to analyze
3. Define the scripts you want to generate
4. Select the AI model to use
5. Configure model-specific settings (optional)
6. Click "Generate Scripts"

### Using the Script Agent

The script agent is designed for generating individual scripts:

1. Navigate to the Script Agent page
2. Provide a name and description for your script
3. Select the AI model to use
4. Configure model-specific settings (optional)
5. Click "Generate Script"

## Components Details

### Model Providers

The system abstracts AI model interactions through a provider interface:

- **BaseModelProvider**: Abstract base class that defines the interface
- **ClaudeProvider**: Implementation for Anthropic's Claude
- **OpenAIProvider**: Implementation for OpenAI's GPT models
- **DeepSeekProvider**: Implementation for DeepSeek

### Orchestrator

The orchestrator analyzes project structure and generates multiple scripts:

- **ProjectContext**: Analyzes and indexes project files and structures
- **ScriptGenerator**: Handles AI model interactions for script generation
- **CodeReviewer**: Reviews and provides feedback on generated scripts
- **TaskOrchestrator**: Coordinates the workflow of analysis, generation, and review

### Script Agent

The script agent generates individual scripts:

- Loads project specifications
- Interacts with AI models to generate scripts
- Performs iterative improvement cycles
- Evaluates script quality
- Saves outputs and conversation history

## Configuration

### Orchestrator Configuration

The orchestrator configuration is stored in `orchestrator/config/orchestrator_config.json`:

- Model parameters (name, token limits)
- Directory paths to analyze
- Script definitions and requirements
- Review criteria and weights
- Parallelism settings

### Script Agent Configuration

The script agent configuration is stored in `script-agent/config.json`:

- Script definitions
- Iteration settings
- Evaluation criteria

## API Key Management

API keys are stored in a `.env` file in the project root directory. You can set or update API keys:

1. Through the web interface
2. By editing the `.env` file directly
3. By setting environment variables before running the application

## Troubleshooting

- **Missing API Keys**: Ensure you have set at least one API key
- **Import Errors**: Check that all components are properly installed
- **Generation Failures**: Check the logs for detailed error messages

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
