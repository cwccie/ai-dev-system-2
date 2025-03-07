#!/bin/bash

# AI Code Development Orchestration System
# Enhanced runner script to set up environment, install all dependencies, and run Flask

set -e  # Exit immediately if a command exits with a non-zero status

# Colors for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    echo -e "${BLUE}[AI-Dev-Orchestrator]${NC} $1"
}

print_status() {
    echo -e "${CYAN}[STATUS]${NC} $1"
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

print_debug() {
    if [ "$DEBUG" = "true" ]; then
        echo -e "${YELLOW}[DEBUG]${NC} $1"
    fi
}

# Simple progress bar implementation
progress_bar() {
    local total=$1
    local current=$2
    local width=50
    local percentage=$((current * 100 / total))
    local completed=$((width * current / total))
    local remaining=$((width - completed))
    
    # Build the progress bar
    local bar="["
    for ((i=0; i<completed; i++)); do
        bar+="#"
    done
    for ((i=0; i<remaining; i++)); do
        bar+="."
    done
    bar+="] $percentage%"
    
    # Print the progress bar
    echo -ne "${CYAN}$bar${NC}\r"
    if [ $current -eq $total ]; then
        echo
    fi
}

# Count total steps for progress tracking
TOTAL_STEPS=12
CURRENT_STEP=0

update_progress

    # Print summary information
    echo
    echo -e "${BOLD}${GREEN}====== Application Summary ======${NC}"
    echo -e "${BOLD}Flask Web Interface:${NC} http://$LOCAL_IP:9000"
    echo -e "${BOLD}Ollama API:${NC} http://$LOCAL_IP:11434"
    echo -e "${BOLD}Log File:${NC} $(pwd)/$LOG_FILE"
    echo
    echo -e "${BOLD}${GREEN}==================================${NC}"
    echo
    print_message "AI Development Orchestration System is now running!"() {
    CURRENT_STEP=$((CURRENT_STEP + 1))
    progress_bar $TOTAL_STEPS $CURRENT_STEP
}

# Function to check if a command exists
command_exists() {
    if command -v "$1" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to check if running as root
check_root() {
    print_status "Checking execution privileges..."
    if [ "$EUID" -ne 0 ]; then
        print_warning "This script is not running as root. Some operations may require sudo."
        print_warning "You may be prompted for your password during execution."
        USE_SUDO="sudo"
    else
        print_status "Running with root privileges."
        USE_SUDO=""
    fi
    update_progress
}

# Function to detect the OS
detect_os() {
    print_status "Detecting operating system..."
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        OS_VERSION=$VERSION_ID
        print_message "Detected OS: $OS $OS_VERSION"
    else
        print_warning "Could not detect OS, assuming Debian/Ubuntu compatible"
        OS="Unknown"
    fi
    update_progress
}

# Update and upgrade the system
update_system() {
    print_status "Starting system update process..."
    
    print_message "Updating system packages..."
    if $USE_SUDO apt-get update -y > /tmp/apt-update.log 2>&1; then
        print_success "Package lists updated"
    else
        print_error "Failed to update package lists"
        print_status "Check the log at /tmp/apt-update.log for details"
        cat /tmp/apt-update.log
        exit 1
    fi
    
    print_message "Upgrading installed packages..."
    if $USE_SUDO apt-get upgrade -y > /tmp/apt-upgrade.log 2>&1; then
        print_success "System packages upgraded"
    else
        print_error "Failed to upgrade packages"
        print_status "Check the log at /tmp/apt-upgrade.log for details"
        cat /tmp/apt-upgrade.log
        exit 1
    fi
    
    print_message "Installing essential tools..."
    essential_tools="net-tools curl wget git build-essential software-properties-common"
    print_status "Tools to be installed: $essential_tools"
    
    if $USE_SUDO apt-get install -y $essential_tools > /tmp/apt-install-tools.log 2>&1; then
        print_success "Essential tools installed"
    else
        print_error "Failed to install essential tools"
        print_status "Check the log at /tmp/apt-install-tools.log for details"
        cat /tmp/apt-install-tools.log
        exit 1
    fi
    
    update_progress
}

# Install Python 3 if not already installed
install_python() {
    print_status "Checking Python installation..."
    if ! command_exists python3; then
        print_message "Python 3 not found. Installing Python 3..."
        if $USE_SUDO apt-get install -y python3 python3-dev > /tmp/python-install.log 2>&1; then
            print_success "Python 3 installed"
        else
            print_error "Failed to install Python 3"
            print_status "Check the log at /tmp/python-install.log for details"
            cat /tmp/python-install.log
            exit 1
        fi
    else
        print_success "Python 3 is already installed"
    fi
    
    # Check Python version
    python_version=$(python3 --version | cut -d' ' -f2)
    print_status "Found Python version: $python_version"
    
    # Make sure python3-venv is installed
    print_status "Checking for python3-venv package..."
    if ! $USE_SUDO dpkg -l | grep -q python3-venv; then
        print_message "Installing python3-venv package..."
        if $USE_SUDO apt-get install -y python3-venv > /tmp/venv-install.log 2>&1; then
            print_success "python3-venv installed"
        else
            print_error "Failed to install python3-venv"
            print_status "Check the log at /tmp/venv-install.log for details"
            cat /tmp/venv-install.log
            exit 1
        fi
    else
        print_success "python3-venv package is already installed"
    fi
    
    update_progress
}

# Install pip if not already installed
install_pip() {
    print_status "Checking pip installation..."
    if ! command_exists pip3; then
        print_message "Installing pip for Python 3..."
        if $USE_SUDO apt-get install -y python3-pip > /tmp/pip-install.log 2>&1; then
            print_success "pip3 installed"
        else
            print_error "Failed to install pip3"
            print_status "Check the log at /tmp/pip-install.log for details"
            cat /tmp/pip-install.log
            exit 1
        fi
    else
        print_success "pip3 is already installed"
        
        print_message "Upgrading pip to latest version..."
        if $USE_SUDO python3 -m pip install --upgrade pip > /tmp/pip-upgrade.log 2>&1; then
            print_success "pip upgraded"
        else
            print_warning "Failed to upgrade pip"
            print_status "Check the log at /tmp/pip-upgrade.log for details"
            # This is just a warning, not fatal
        fi
    fi
    
    update_progress
}

# Install Ollama
install_ollama() {
    print_status "Setting up Ollama..."
    
    if ! command_exists ollama; then
        print_message "Ollama not found. Installing Ollama..."
        print_status "Downloading and running Ollama installer..."
        
        if curl -fsSL https://ollama.com/install.sh -o /tmp/ollama-install.sh; then
            if $USE_SUDO bash /tmp/ollama-install.sh > /tmp/ollama-install.log 2>&1; then
                print_success "Ollama installed"
            else
                print_error "Failed to install Ollama"
                print_status "Check the log at /tmp/ollama-install.log for details"
                cat /tmp/ollama-install.log
                exit 1
            fi
        else
            print_error "Failed to download Ollama installer"
            exit 1
        fi
    else
        print_success "Ollama is already installed"
    fi
    
    # Start Ollama service
    print_status "Starting Ollama service..."
    if command_exists systemctl; then
        print_status "Using systemd to start Ollama..."
        if $USE_SUDO systemctl enable --now ollama > /tmp/ollama-service.log 2>&1; then
            if $USE_SUDO systemctl restart ollama >> /tmp/ollama-service.log 2>&1; then
                print_success "Ollama service started with systemd"
            else
                print_error "Failed to restart Ollama service"
                print_status "Check the log at /tmp/ollama-service.log for details"
                cat /tmp/ollama-service.log
                exit 1
            fi
        else
            print_error "Failed to enable Ollama service"
            print_status "Check the log at /tmp/ollama-service.log for details"
            cat /tmp/ollama-service.log
            exit 1
        fi
    else
        print_status "systemd not found, starting Ollama directly..."
        if pkill -f "ollama serve" > /dev/null 2>&1; then
            print_status "Killed existing Ollama process"
        fi
        print_status "Starting Ollama in background..."
        nohup ollama serve > ollama.log 2>&1 &
        print_success "Ollama started in background"
    fi
    
    print_message "Waiting for Ollama service to start..."
    sleep 5
    
    # Verify Ollama is running
    if curl -s --head http://localhost:11434/api/tags > /dev/null; then
        print_success "Ollama service is running and responding"
    else
        print_warning "Ollama might not be running correctly. Will continue anyway."
        print_status "You can check the Ollama logs for issues."
    fi
    
    update_progress
}

# Check if virtual environment exists, create if not
setup_venv() {
    print_status "Setting up Python virtual environment..."
    if [ ! -d "venv" ]; then
        print_message "Creating virtual environment..."
        if python3 -m venv venv > /tmp/venv-create.log 2>&1; then
            print_success "Virtual environment created"
        else
            print_error "Failed to create virtual environment"
            print_status "Check the log at /tmp/venv-create.log for details"
            cat /tmp/venv-create.log
            exit 1
        fi
    else
        print_success "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    print_status "Activating virtual environment..."
    if source venv/bin/activate; then
        print_success "Virtual environment activated"
        print_status "Python version in venv: $(python3 --version)"
        print_status "Pip version in venv: $(pip3 --version)"
    else
        print_error "Failed to activate virtual environment"
        exit 1
    fi
    
    update_progress
}

# Install required dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Upgrade pip first
    print_message "Upgrading pip in virtual environment..."
    if pip3 install --upgrade pip > /tmp/venv-pip-upgrade.log 2>&1; then
        print_success "pip upgraded in virtual environment"
    else
        print_warning "Failed to upgrade pip in virtual environment"
        print_status "Check the log at /tmp/venv-pip-upgrade.log for details"
        # This is just a warning, not fatal
    fi
    
    # Install Flask and other main dependencies
    print_message "Installing main dependencies..."
    main_deps="flask flask-login anthropic>=0.5.0 tqdm>=4.65.0 python-dotenv aiohttp openai"
    print_status "Dependencies to install: $main_deps"
    
    if pip3 install $main_deps > /tmp/main-deps-install.log 2>&1; then
        print_success "Main dependencies installed"
    else
        print_error "Failed to install main dependencies"
        print_status "Check the log at /tmp/main-deps-install.log for details"
        cat /tmp/main-deps-install.log
        exit 1
    fi
    
    # Install additional dependencies
    print_message "Installing additional dependencies..."
    if pip3 install flask-cors gunicorn flask-wtf > /tmp/add-deps-install.log 2>&1; then
        print_success "Additional dependencies installed"
    else
        print_warning "Failed to install additional dependencies"
        print_status "Check the log at /tmp/add-deps-install.log for details"
        # This is not fatal
    fi
    
    # Install component-specific dependencies
    if [ -f "orchestrator/requirements.txt" ]; then
        print_message "Installing orchestrator dependencies..."
        if pip3 install -r orchestrator/requirements.txt > /tmp/orchestrator-deps.log 2>&1; then
            print_success "Orchestrator dependencies installed"
        else
            print_warning "Failed to install orchestrator dependencies"
            print_status "Check the log at /tmp/orchestrator-deps.log for details"
            # This is not fatal
        fi
    else
        print_status "No orchestrator/requirements.txt found, skipping"
    fi
    
    if [ -f "script-agent/requirements.txt" ]; then
        print_message "Installing script-agent dependencies..."
        if pip3 install -r script-agent/requirements.txt > /tmp/script-agent-deps.log 2>&1; then
            print_success "Script-agent dependencies installed"
        else
            print_warning "Failed to install script-agent dependencies"
            print_status "Check the log at /tmp/script-agent-deps.log for details"
            # This is not fatal
        fi
    else
        print_status "No script-agent/requirements.txt found, skipping"
    fi
    
    update_progress
}

# Check for API keys
check_api_keys() {
    print_status "Managing API keys..."
    
    # Check if .env file exists, create if not
    if [ ! -f ".env" ]; then
        print_status "Creating .env file..."
        touch .env
    else
        print_status "Found existing .env file"
    fi
    
    # Source .env file if it exists
    if [ -f ".env" ]; then
        print_status "Loading environment variables from .env file..."
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
    else
        print_status "Using existing Ollama API URL: $OLLAMA_API_URL"
    fi
    
    update_progress
}

# Create necessary directories if they don't exist
create_directories() {
    print_status "Creating directory structure..."
    
    # Create all required directories
    mkdir -p orchestrator/config
    print_status "Created orchestrator/config/"
    
    mkdir -p script-agent
    print_status "Created script-agent/"
    
    mkdir -p model_providers
    print_status "Created model_providers/"
    
    mkdir -p templates
    print_status "Created templates/"
    
    mkdir -p static/css
    print_status "Created static/css/"
    
    mkdir -p static/js
    print_status "Created static/js/"
    
    mkdir -p logs
    print_status "Created logs/"
    
    # Set proper permissions for execution
    print_status "Setting executable permissions on scripts..."
    
    chmod +x run.sh
    print_status "Made run.sh executable"
    
    if [ -f "orchestrator/run_orchestrator.sh" ]; then
        chmod +x orchestrator/run_orchestrator.sh
        print_status "Made orchestrator/run_orchestrator.sh executable"
    else
        print_warning "orchestrator/run_orchestrator.sh not found, skipping"
    fi
    
    if [ -f "script-agent/run_agent.sh" ]; then
        chmod +x script-agent/run_agent.sh
        print_status "Made script-agent/run_agent.sh executable"
    else
        print_warning "script-agent/run_agent.sh not found, skipping"
    fi
    
    print_success "Directory structure ensured"
    update_progress
}

# Create Ollama provider module
create_ollama_provider() {
    print_status "Setting up Ollama provider module..."
    
    # Create ollama_provider.py
    if [ ! -f "model_providers/ollama_provider.py" ]; then
        print_message "Creating Ollama provider module..."
        mkdir -p model_providers
        
        cat > model_providers/ollama_provider.py << 'EOFPROVIDER'
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
EOFPROVIDER
        
        print_success "Created model_providers/ollama_provider.py"
    else
        print_status "Ollama provider module already exists"
    fi
    
    # Update __init__.py to include Ollama provider
    if [ ! -f "model_providers/__init__.py" ]; then
        # Create the __init__.py file with Ollama support
        print_status "Creating model_providers/__init__.py with Ollama support..."
        
        cat > model_providers/__init__.py << 'EOFMINIT'
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
EOFMINIT
        
        print_success "Created model_providers/__init__.py with Ollama support"
    elif ! grep -q "ollama" "model_providers/__init__.py"; then
        # Backup the original file
        print_status "Updating model_providers/__init__.py to include Ollama..."
        cp model_providers/__init__.py model_providers/__init__.py.bak
        print_status "Backed up original __init__.py file"
        
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
    
    update_progress
}

# Pull and download base models
setup_models() {
    print_status "Setting up base models in Ollama..."
    
    # Check if Ollama is running
    if ! curl -s --head http://localhost:11434/api/tags > /dev/null; then
        print_warning "Ollama is not running, skipping model downloads"
        update_progress
        return
    fi
    
    # Try to download llama3 model (or whatever is available)
    print_message "Downloading base model (llama3)..."
    print_status "This may take a while depending on your internet connection"
    
    if ollama pull llama3 > /tmp/ollama-pull.log 2>&1; then
        print_success "Successfully pulled llama3 model"
    else
        print_warning "Failed to pull llama3 model"
        print_status "You can manually download models later with 'ollama pull <model>'"
        print_status "Check the log at /tmp/ollama-pull.log for details"
    fi
    
    update_progress
}

# Verify app configuration
verify_config() {
    print_status "Verifying application configuration..."
    
    # Check for app.py
    if [ ! -f "app.py" ]; then
        print_warning "app.py not found in the current directory"
        print_status "Make sure you're in the right directory or create app.py"
    else
        print_status "Found app.py"
    fi
    
    # Check for templates directory
    if [ ! -d "templates" ] || [ -z "$(ls -A templates 2>/dev/null)" ]; then
        print_warning "templates directory is empty or missing"
        print_status "You may need to create template files for the Flask application"
    else
        print_status "Found templates directory with files"
    fi
    
    # Check for static files
    if [ ! -d "static" ] || [ -z "$(ls -A static 2>/dev/null)" ]; then
        print_warning "static directory is empty or missing"
        print_status "You may need to create static files for the Flask application"
    else
        print_status "Found static directory with files"
    fi
    
    update_progress
}

# Start the Flask application
start_flask() {
    print_status "Preparing to start Flask application..."
    
    # Create logs directory if it doesn't exist
    mkdir -p logs
    
    # Activate virtual environment if not already activated
    if [ -z "$VIRTUAL_ENV" ]; then
        print_status "Activating virtual environment..."
        source venv/bin/activate
    fi
    
    # Set Flask environment variables
    export FLASK_APP=app.py
    print_status "Set FLASK_APP=app.py"
    
    # Create a more descriptive log file name with timestamp
    LOG_FILE="logs/flask_$(date +%Y%m%d_%H%M%S).log"
    print_status "Logs will be written to: $LOG_FILE"
    
    # Start Flask in background
    print_message "Starting Flask application on http://0.0.0.0:9000"
    if command_exists gunicorn; then
        print_status "Using gunicorn for production-ready server..."
        nohup gunicorn -b 0.0.0.0:9000 -w 4 app:app > "$LOG_FILE" 2>&1 &
        FLASK_PID=$!
    else
        print_status "Using Flask development server (consider installing gunicorn for production)..."
        nohup flask run --host=0.0.0.0 --port=9000 > "$LOG_FILE" 2>&1 &
        FLASK_PID=$!
    fi
    
    # Wait a moment for the server to start
    sleep 3
    
    # Check if the process is still running
    if ps -p $FLASK_PID > /dev/null; then
        print_success "Application started in background with PID: $FLASK_PID"
    else
        print_error "Flask application failed to start"
        print_status "Check the log at $LOG_FILE for details"
        cat "$LOG_FILE"
        exit 1
    fi
    
    # Try to get the local IP address for user convenience
    LOCAL_IP=$(hostname -I | awk '{print $1}')
    if [ -z "$LOCAL_IP" ]; then
        LOCAL_IP="localhost"
    fi
    
    update_progress