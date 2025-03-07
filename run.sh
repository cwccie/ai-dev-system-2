#!/bin/bash

# AI Code Development Orchestration System
# Enhanced runner script to set up environment, install all dependencies, and run Flask

set -e  # Exit immediately if a command exits with a non-zero status

# Colors for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    echo -e "${BLUE}[AI-Dev-Orchestrator]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_warning "This script is not running as root. Some operations may require sudo."
        print_warning "You may be prompted for your password during execution."
        USE_SUDO="sudo"
    else
        USE_SUDO=""
    fi
}

# Function to detect the OS
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        OS_VERSION=$VERSION_ID
        print_message "Detected OS: $OS $OS_VERSION"
    else
        print_warning "Could not detect OS, assuming Debian/Ubuntu compatible"
        OS="Unknown"
    fi
}

# Update and upgrade the system
update_system() {
    print_message "Updating system packages..."
    $USE_SUDO apt-get update -y
    print_success "Package lists updated"
    
    print_message "Upgrading installed packages..."
    $USE_SUDO apt-get upgrade -y
    print_success "System packages upgraded"
    
    print_message "Installing essential tools..."
    $USE_SUDO apt-get install -y net-tools curl wget git build-essential software-properties-common
    print_success "Essential tools installed"
}

# Install Python 3 if not already installed
install_python() {
    if ! command_exists python3; then
        print_message "Installing Python 3..."
        $USE_SUDO apt-get install -y python3 python3-dev python3-venv
        print_success "Python 3 installed"
    else
        print_success "Python 3 is already installed"
    fi
    
    # Check Python version
    python_version=$(python3 --version | cut -d' ' -f2)
    print_success "Python $python_version detected"
    
    # Make sure python3-venv is installed
    if ! $USE_SUDO dpkg -l | grep -q python3-venv; then
        print_message "Installing python3-venv package..."
        $USE_SUDO apt-get install -y python3-venv
        print_success "python3-venv installed"
    fi
}

# Install pip if not already installed
install_pip() {
    if ! command_exists pip3; then
        print_message "Installing pip for Python 3..."
        $USE_SUDO apt-get install -y python3-pip
        print_success "pip3 installed"
    else
        print_success "pip3 is already installed"
        
        print_message "Upgrading pip to latest version..."
        $USE_SUDO python3 -m pip install --upgrade pip
        print_success "pip upgraded"
    fi
}

# Install Ollama
install_ollama() {
    print_message "Installing Ollama..."
    
    if ! command_exists ollama; then
        curl -fsSL https://ollama.com/install.sh | $USE_SUDO sh
        print_success "Ollama installed"
    else
        print_success "Ollama is already installed"
    fi
    
    # Start Ollama service
    print_message "Starting Ollama service..."
    if command_exists systemctl; then
        $USE_SUDO systemctl enable --now ollama
        $USE_SUDO systemctl restart ollama
    else
        # Start Ollama in the background if not managed by systemd
        nohup ollama serve > ollama.log 2>&1 &
    fi
    
    print_message "Waiting for Ollama service to start..."
    sleep 5
    print_success "Ollama service started"
}

# Check if virtual environment exists, create if not
setup_venv() {
    if [ ! -d "venv" ]; then
        print_message "Creating virtual environment..."
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_success "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    print_success "Virtual environment activated"
}

# Install required dependencies
install_dependencies() {
    print_message "Installing dependencies..."
    pip3 install --upgrade pip
    
    # Install Flask and other main dependencies
    pip3 install flask flask-login anthropic>=0.5.0 tqdm>=4.65.0 python-dotenv aiohttp openai
    
    # Additional dependencies for better functionality
    pip3 install flask-cors gunicorn flask-wtf
    
    # Install component-specific dependencies
    if [ -f "orchestrator/requirements.txt" ]; then
        pip3 install -r orchestrator/requirements.txt
    fi
    
    if [ -f "script-agent/requirements.txt" ]; then
        pip3 install -r script-agent/requirements.txt
    fi
    
    print_success "Dependencies installed"
}

# Check for API keys
check_api_keys() {
    # Check if .env file exists, create if not
    if [ ! -f ".env" ]; then
        touch .env
    fi
    
    # Source .env file if it exists
    if [ -f ".env" ]; then
        source .env
    fi
    
    # Check for Anthropic API key
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        print_warning "ANTHROPIC_API_KEY environment variable is not set."
        read -p "Enter your Anthropic API key (or leave blank to skip): " api_key
        if [ ! -z "$api_key" ]; then
            echo "ANTHROPIC_API_KEY=$api_key" >> .env
            export ANTHROPIC_API_KEY="$api_key"
            print_success "Anthropic API key saved to .env file"
        else
            print_warning "Anthropic API key not provided. Some features may not work."
        fi
    else
        print_success "Anthropic API key detected"
    fi
    
    # Check for OpenAI API key
    if [ -z "$OPENAI_API_KEY" ]; then
        print_warning "OPENAI_API_KEY environment variable is not set."
        read -p "Enter your OpenAI API key (or leave blank to skip): " api_key
        if [ ! -z "$api_key" ]; then
            echo "OPENAI_API_KEY=$api_key" >> .env
            export OPENAI_API_KEY="$api_key"
            print_success "OpenAI API key saved to .env file"
        else
            print_warning "OpenAI API key not provided. Some features may not work."
        fi
    else
        print_success "OpenAI API key detected"
    fi
    
    # Check for DeepSeek API key
    if [ -z "$DEEPSEEK_API_KEY" ]; then
        print_warning "DEEPSEEK_API_KEY environment variable is not set."
        read -p "Enter your DeepSeek API key (or leave blank to skip): " api_key
        if [ ! -z "$api_key" ]; then
            echo "DEEPSEEK_API_KEY=$api_key" >> .env
            export DEEPSEEK_API_KEY="$api_key"
            print_success "DeepSeek API key saved to .env file"
        else
            print_warning "DeepSeek API key not provided. Some features may not work."
        fi
    else
        print_success "DeepSeek API key detected"
    fi
    
    # Set Ollama API URL
    if [ -z "$OLLAMA_API_URL" ]; then
        print_message "Setting Ollama API URL..."
        echo "OLLAMA_API_URL=http://localhost:11434" >> .env
        export OLLAMA_API_URL="http://localhost:11434"
        print_success "Ollama API URL set to http://localhost:11434"
    fi
}

# Create necessary directories if they don't exist
create_directories() {
    mkdir -p orchestrator/config
    mkdir -p script-agent
    mkdir -p model_providers
    mkdir -p templates
    mkdir -p static/css
    mkdir -p static/js
    mkdir -p logs
    
    # Set proper permissions for execution
    chmod +x run.sh
    
    if [ -f "orchestrator/run_orchestrator.sh" ]; then
        chmod +x orchestrator/run_orchestrator.sh
    fi
    
    if [ -f "script-agent/run_agent.sh" ]; then
        chmod +x script-agent/run_agent.sh
    fi
    
    print_success "Directory structure ensured"
}

# Create Ollama provider module
create_ollama_provider() {
    print_message "Creating Ollama provider module..."
    
    # Create ollama_provider.py
    if [ ! -f "model_providers/ollama_provider.py" ]; then
        mkdir -p model_providers
        cat > model_providers/ollama_provider.py << 'EOF'
"""
Ollama Provider
Implementation for Ollama local models
"""

import os
import re
import json
import aiohttp
from typing import Dict, Any, List, Optional

from model_providers.base_provider import BaseModelProvider


class OllamaProvider(BaseModelProvider):
    """
    Provider implementation for Ollama local models
    """
    
    def __init__(self, api_url: str = None, model: str = "llama3"):
        """
        Initialize the Ollama provider
        
        Args:
            api_url: Ollama API URL, defaults to environment variable
            model: Ollama model to use
        """
        self.api_url = api_url or os.environ.get("OLLAMA_API_URL", "http://localhost:11434")
        self.model = model
        
    async def generate_response(self, 
                               prompt: str, 
                               system_prompt: Optional[str] = None,
                               temperature: float = 0.7,
                               max_tokens: int = 4000) -> str:
        """
        Generate a response from Ollama
        
        Args:
            prompt: The user prompt to send to Ollama
            system_prompt: System instructions for Ollama (optional)
            temperature: Controls randomness, higher values = more random
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            String containing Ollama's response
        """
        try:
            # Prepare the request payload
            payload = {
                "model": self.model,
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            # Add system prompt if provided
            if system_prompt:
                payload["system"] = system_prompt
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/api/generate", json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"API Error: {response.status} - {error_text}")
                    
                    result = await response.json()
                    return result.get("response", "")
            
        except Exception as e:
            print(f"Error generating response from Ollama: {e}")
            return f"Error: {str(e)}"
    
    async def extract_code(self, response: str) -> List[str]:
        """
        Extract code blocks from Ollama's response
        
        Args:
            response: The full text response from Ollama
            
        Returns:
            List of extracted code blocks
        """
        # Pattern to match code blocks with or without language specification
        pattern = r'```(?:\w+\n)?(.*?)```'
        matches = re.findall(pattern, response, re.DOTALL)
        
        # If no matches found, check if the entire response might be code
        if not matches and not response.startswith('```') and not response.endswith('```'):
            # Heuristic: If response has multiple lines and looks like code
            lines = response.split('\n')
            if len(lines) > 1 and any(line.strip().startswith(('def ', 'class ', 'import ', 'from ')) for line in lines):
                return [response]
        
        return matches
    
    def get_model_name(self) -> str:
        """Get the name of the currently used Ollama model"""
        return self.model
    
    def get_provider_name(self) -> str:
        """Get the provider name"""
        return "ollama"
    
    def get_context_window(self) -> int:
        """
        Get Ollama's context window size in tokens
        
        Returns:
            Integer representing the context window size
        """
        # Context window sizes for different Ollama models
        context_windows = {
            "llama3": 8192,
            "llama2": 4096,
            "codellama": 16384,
            "mistral": 8192,
            "mixtral": 32768,
            "phi3": 8192
        }
        
        # Try to extract base model from model name (e.g., "llama3:latest" -> "llama3")
        base_model = self.model.split(':')[0].lower()
        
        return context_windows.get(base_model, 4096)  # Default to 4K if unknown
    
    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text
        
        Args:
            text: The text to count tokens for
            
        Returns:
            Integer representing the token count
        """
        # Ollama doesn't have a public tokenizer endpoint, so use rough estimate
        return len(text.split()) * 1.3  # Rough estimate based on typical tokenization
EOF
        print_success "Created model_providers/ollama_provider.py"
    fi
    
    # Update __init__.py to include Ollama provider
    if [ ! -f "model_providers/__init__.py" ]; then
        # Create the __init__.py file with Ollama support
        cat > model_providers/__init__.py << 'EOF'
"""
Model Providers Module
Factory for getting appropriate model providers
"""

import os
import importlib
from typing import Optional, Any

# Define provider mapping
PROVIDERS = {
    'ollama': 'model_providers.ollama_provider',
    'claude': 'model_providers.claude_provider',
    'openai': 'model_providers.openai_provider',
    'deepseek': 'model_providers.deepseek_provider'
}

def get_provider(provider_name: str) -> Optional[Any]:
    """
    Factory function to get the appropriate model provider
    
    Args:
        provider_name: Name of the provider to instantiate
    
    Returns:
        An instance of the requested provider or None if not available
    """
    if provider_name not in PROVIDERS:
        raise ValueError(f"Unknown provider: {provider_name}")
    
    # Check for API key
    api_key_env_vars = {
        'ollama': 'OLLAMA_API_URL',
        'claude': 'ANTHROPIC_API_KEY',
        'openai': 'OPENAI_API_KEY',
        'deepseek': 'DEEPSEEK_API_KEY'
    }
    
    api_key = os.environ.get(api_key_env_vars.get(provider_name))
    
    # Special case for Ollama - use default URL if not set
    if provider_name == 'ollama' and not api_key:
        api_key = "http://localhost:11434"
    
    if not api_key and provider_name != 'ollama':
        print(f"Warning: No API key found for {provider_name}")
        return None
    
    try:
        # Import the module dynamically
        module_path = PROVIDERS[provider_name]
        module = importlib.import_module(module_path)
        
        # Get the provider class
        provider_classes = {
            'ollama': 'OllamaProvider',
            'claude': 'ClaudeProvider',
            'openai': 'OpenAIProvider',
            'deepseek': 'DeepSeekProvider'
        }
        
        provider_class = getattr(module, provider_classes[provider_name])
        
        # Instantiate the provider
        if provider_name == 'ollama':
            return provider_class(api_url=api_key)
        else:
            return provider_class(api_key=api_key)
    
    except (ImportError, AttributeError) as e:
        print(f"Error initializing provider {provider_name}: {e}")
        return None
EOF
        print_success "Created model_providers/__init__.py with Ollama support"
    elif ! grep -q "ollama" "model_providers/__init__.py"; then
        # Backup the original file
        cp model_providers/__init__.py model_providers/__init__.py.bak
        
        # Update the provider mapping to include Ollama
        sed -i 's/PROVIDERS = {/PROVIDERS = {\n    \'ollama\': \'model_providers.ollama_provider\',/g' model_providers/__init__.py
        
        # Update the api_key_env_vars dictionary
        sed -i 's/api_key_env_vars = {/api_key_env_vars = {\n        \'ollama\': \'OLLAMA_API_URL\',/g' model_providers/__init__.py
        
        # Update the provider_classes dictionary
        sed -i 's/provider_classes = {/provider_classes = {\n            \'ollama\': \'OllamaProvider\',/g' model_providers/__init__.py
        
        print_success "Updated model_providers/__init__.py to include Ollama"
    else
        print_success "Ollama provider already included in model_providers/__init__.py"
    fi
}

# Main function
main() {
    print_message "Starting AI Code Development Orchestration System setup..."
    
    # Check if running as root and detect OS
    check_root
    detect_os
    
    # Update and install system packages
    print_message "Preparing system..."
    update_system
    install_python
    install_pip
    
    # Install and configure Ollama
    print_message "Setting up Ollama..."
    install_ollama
    
    # Set up the Python environment
    print_message "Setting up Python environment..."
    setup_venv
    install_dependencies
    check_api_keys
    create_directories
    create_ollama_provider
    
    # Run the Flask application
    print_message "Starting Flask application on http://0.0.0.0:9000"
    source venv/bin/activate
    export FLASK_APP=app.py
    
    mkdir -p logs
    nohup flask run --host=0.0.0.0 --port=9000 > logs/flask.log 2>&1 &
    
    print_success "Application started in background with PID: $!"
    print_message "You can view logs at: $(pwd)/logs/flask.log"
    print_message "AI Development Orchestration System is now running at http://$(hostname -I | awk '{print $1}'):9000"
    print_message "Ollama is available at http://$(hostname -I | awk '{print $1}'):11434"
}

# Run the main function
main
