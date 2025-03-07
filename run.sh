#!/bin/bash
#
# AI Code Development Orchestration System
# Enhanced runner script to set up environment, install dependencies, and run Flask application
# Modified to prompt for an install location before installing Ollama / WebUI

set -e  # Exit if a command fails

# Create a unique temporary directory
TEMP_DIR=$(mktemp -d -t ai-dev-setup-XXXXXXXXXX)

# Cleanup function
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ] && [ $exit_code -ne 130 ]; then
        echo -e "${RED}Setup failed with exit code $exit_code!${NC}"
        echo -e "Check the log files in ${TEMP_DIR} for details."
    fi
    
    if [ ! -z "$FLASK_PID" ] && ps -p $FLASK_PID > /dev/null; then
        echo -e "${YELLOW}Stopping Flask server (PID: $FLASK_PID)${NC}"
        kill $FLASK_PID 2>/dev/null || true
    fi
    
    if [ "$DEBUG" != "true" ]; then
        echo -e "${CYAN}Cleaning up temporary files...${NC}"
        rm -rf "${TEMP_DIR}"
    else
        echo -e "${YELLOW}Debug mode: Keeping temporary files in ${TEMP_DIR}${NC}"
    fi
    
    exit $exit_code
}

trap cleanup EXIT
trap 'exit 130' INT  # Ctrl+C

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Progress tracking
TOTAL_STEPS=13  # Increased by 1 to account for our new step
CURRENT_STEP=0

progress_bar() {
    local total=$1
    local current=$2
    local width=50
    local percentage=$((current * 100 / total))
    local completed=$((width * current / total))
    local remaining=$((width - completed))
    
    local bar="["
    for ((i=0; i<completed; i++)); do
        bar+="#"
    done
    for ((i=0; i<remaining; i++)); do
        bar+="."
    done
    bar+="] $percentage%"
    
    echo -ne "${CYAN}$bar${NC}\r"
    if [ $current -eq $total ]; then
        echo
    fi
}

update_progress() {
    CURRENT_STEP=$((CURRENT_STEP + 1))
    progress_bar $TOTAL_STEPS $CURRENT_STEP
}

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

command_exists() {
    if command -v "$1" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# ---------------------------------------------------
# New function to let user pick an install directory
# ---------------------------------------------------
select_install_location() {
    print_status "Detecting available block devices..."
    echo
    # Show block devices with name/size/mountpoint. Adjust columns as needed.
    lsblk -o NAME,SIZE,MOUNTPOINT
    
    echo
    print_message "Please specify the directory path you want Ollama/WebUI to use for storing models."
    print_message "For example, something like /mnt/data or /media/username/SomeDrive, etc."
    read -p "Enter the full path: " selected_path

    # Basic check if user typed something
    if [ -z "$selected_path" ]; then
        print_warning "No path entered. Defaulting to /var/lib/ollama."
        selected_path="/var/lib/ollama"
    fi

    # Attempt to create the directory if it doesn’t exist
    if [ ! -d "$selected_path" ]; then
        print_status "Creating directory: $selected_path"
        $USE_SUDO mkdir -p "$selected_path"
    fi

    # Store this in an env variable that we reuse for Ollama and WebUI
    export OLLAMA_LIBRARY_DIR="$selected_path"
    print_success "Models will be installed in: $OLLAMA_LIBRARY_DIR"
    update_progress
}

check_required_commands() {
    print_status "Checking for required commands..."
    
    local missing_commands=()
    for cmd in curl wget python3; do
        if ! command_exists "$cmd"; then
            missing_commands+=("$cmd")
        fi
    done
    
    if [ ${#missing_commands[@]} -gt 0 ]; then
        print_error "Required command(s) not found: ${missing_commands[*]}"
        print_status "Please install the missing commands and try again."
        print_status "On Debian/Ubuntu systems, you can use: sudo apt-get install ${missing_commands[*]}"
        exit 1
    fi
    
    local optional_commands=("lsof" "netstat" "gunicorn" "systemctl")
    local missing_optional=()
    for cmd in "${optional_commands[@]}"; do
        if ! command_exists "$cmd"; then
            missing_optional+=("$cmd")
        fi
    done
    
    if [ ${#missing_optional[@]} -gt 0 ]; then
        print_warning "Some optional commands are not available: ${missing_optional[*]}"
        print_status "The script will continue, but some features may be limited."
    fi
    
    print_success "All required commands are available"
}

check_project_directory() {
    print_status "Checking project directory..."
    if [ ! -f "./run.sh" ]; then
        print_error "This script must be run from the project root directory."
        print_status "Please cd to the directory containing run.sh and try again."
        exit 1
    fi
    
    local expected_dirs=("orchestrator" "script-agent" "model_providers" "templates" "static")
    local missing_dirs=()
    for dir in "${expected_dirs[@]}"; do
        if [ ! -d "./$dir" ] && [ ! -f "./$dir" ]; then
            missing_dirs+=("$dir")
        fi
    done
    
    if [ ${#missing_dirs[@]} -gt 0 ]; then
        print_warning "Some expected directories are missing: ${missing_dirs[*]}"
        print_status "This might indicate you're not in the correct project directory."
        read -p "Continue anyway? (y/n): " continue_anyway
        if [[ "$continue_anyway" != "y" && "$continue_anyway" != "Y" ]]; then
            print_error "Aborted by user"
            exit 1
        fi
    else
        print_success "Running from project root directory"
    fi
}

show_banner() {
    echo -e "${BOLD}${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                                                               ║"
    echo "║     AI CODE DEVELOPMENT ORCHESTRATION SYSTEM INSTALLER        ║"
    echo "║                                                               ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo "This script will set up and configure the AI Development Orchestration System"
    echo "including all necessary dependencies, Python libraries, and Ollama integration."
    echo
    echo -e "Total setup steps: ${CYAN}$TOTAL_STEPS${NC}"
    echo "Estimated time: 5-10 minutes (depending on your internet connection)"
    echo
    echo -e "${YELLOW}Press Enter to continue or Ctrl+C to cancel${NC}"
    read
}

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

update_system() {
    print_status "Starting system update process..."
    print_message "Updating system packages..."
    if $USE_SUDO apt-get update -y > /tmp/apt-update.log 2>&1; then
        print_success "Package lists updated"
    else
        print_error "Failed to update package lists"
        cat /tmp/apt-update.log
        exit 1
    fi
    
    print_message "Upgrading installed packages..."
    if $USE_SUDO apt-get upgrade -y > /tmp/apt-upgrade.log 2>&1; then
        print_success "System packages upgraded"
    else
        print_error "Failed to upgrade packages"
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
        cat /tmp/apt-install-tools.log
        exit 1
    fi
    
    update_progress
}

install_python() {
    print_status "Checking Python installation..."
    if ! command_exists python3; then
        print_message "Python 3 not found. Installing Python 3..."
        if $USE_SUDO apt-get install -y python3 python3-dev > /tmp/python-install.log 2>&1; then
            print_success "Python 3 installed"
        else
            print_error "Failed to install Python 3"
            cat /tmp/python-install.log
            exit 1
        fi
    else
        print_success "Python 3 is already installed"
    fi
    
    python_version=$(python3 --version | cut -d' ' -f2)
    print_status "Found Python version: $python_version"
    
    print_status "Checking for python3-venv package..."
    if ! $USE_SUDO dpkg -l | grep -q python3-venv; then
        print_message "Installing python3-venv package..."
        if $USE_SUDO apt-get install -y python3-venv > /tmp/venv-install.log 2>&1; then
            print_success "python3-venv installed"
        else
            print_error "Failed to install python3-venv"
            cat /tmp/venv-install.log
            exit 1
        fi
    else
        print_success "python3-venv package is already installed"
    fi
    
    update_progress
}

install_pip() {
    print_status "Checking pip installation..."
    if ! command_exists pip3; then
        print_message "Installing pip for Python 3..."
        if $USE_SUDO apt-get install -y python3-pip > /tmp/pip-install.log 2>&1; then
            print_success "pip3 installed"
        else
            print_error "Failed to install pip3"
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
            cat /tmp/pip-upgrade.log
        fi
    fi
    
    update_progress
}

wait_for_ollama() {
    print_message "Waiting for Ollama service to start..."
    local max_attempts=30
    local attempt=0
    local ollama_ready=false
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s --head --fail http://localhost:11434/api/tags > /dev/null 2>&1; then
            ollama_ready=true
            break
        fi
        
        attempt=$((attempt + 1))
        if [ $attempt -lt $max_attempts ]; then
            echo -ne "Waiting for Ollama to start: ${attempt}/${max_attempts}\r"
            sleep 1
        fi
    done
    
    if [ "$ollama_ready" = "true" ]; then
        print_success "Ollama service is running and responding"
        return 0
    else
        print_warning "Ollama might not be running correctly after $max_attempts attempts."
        print_status "Will continue anyway, but you may need to start Ollama manually."
        return 1
    fi
}

install_ollama() {
    print_status "Setting up Ollama..."
    
    local ollama_running=false
    if command_exists curl; then
        if curl -s --head --fail http://localhost:11434/api/tags > /dev/null 2>&1; then
            print_success "Ollama is already running"
            ollama_running=true
        fi
    fi
    
    if [ "$ollama_running" = "false" ]; then
        if ! command_exists ollama; then
            print_message "Ollama not found. Installing Ollama..."
            print_status "Downloading and running Ollama installer..."
            
            local ollama_installer="${TEMP_DIR}/ollama-install.sh"
            if curl -fsSL https://ollama.com/install.sh -o "$ollama_installer"; then
                chmod +x "$ollama_installer"
                if $USE_SUDO bash "$ollama_installer" > "${TEMP_DIR}/ollama-install.log" 2>&1; then
                    print_success "Ollama installed"
                else
                    print_error "Failed to install Ollama"
                    cat "${TEMP_DIR}/ollama-install.log"
                    exit 1
                fi
            else
                print_error "Failed to download Ollama installer"
                exit 1
            fi
        else
            print_success "Ollama is already installed"
        fi
        
        print_status "Starting Ollama service..."
        if command_exists systemctl; then
            print_status "Using systemd to start Ollama..."
            if $USE_SUDO systemctl enable --now ollama > "${TEMP_DIR}/ollama-service.log" 2>&1; then
                if $USE_SUDO systemctl stop ollama >> "${TEMP_DIR}/ollama-service.log" 2>&1; then
                    # Relaunch with library dir if set
                    # “systemctl” version of Ollama might not let us pass “--library” easily;
                    # you may need to override the systemd service file to do so. This is for illustration.
                    print_status "Restarting Ollama service with custom library path (if applicable)."
                    if [ -n "$OLLAMA_LIBRARY_DIR" ]; then
                        # This is an example approach: you’d actually update /etc/systemd/system/ollama.service
                        # or create an override. We'll do a direct run for demonstration here:
                        nohup ollama serve --library "$OLLAMA_LIBRARY_DIR" > "${TEMP_DIR}/ollama.log" 2>&1 &
                        OLLAMA_PID=$!
                        print_status "Ollama started with PID: $OLLAMA_PID and --library $OLLAMA_LIBRARY_DIR"
                    else
                        if $USE_SUDO systemctl start ollama >> "${TEMP_DIR}/ollama-service.log" 2>&1; then
                            print_success "Ollama service started with systemd"
                        else
                            print_error "Failed to start Ollama service"
                            cat "${TEMP_DIR}/ollama-service.log"
                            exit 1
                        fi
                    fi
                else
                    print_error "Failed to stop Ollama service"
                    cat "${TEMP_DIR}/ollama-service.log"
                    exit 1
                fi
            else
                print_error "Failed to enable Ollama service"
                cat "${TEMP_DIR}/ollama-service.log"
                exit 1
            fi
        else
            print_status "systemd not found, starting Ollama directly..."
            if pkill -f "ollama serve" > /dev/null 2>&1; then
                print_status "Killed existing Ollama process"
            fi
            if [ -n "$OLLAMA_LIBRARY_DIR" ]; then
                print_status "Starting Ollama in background, using: $OLLAMA_LIBRARY_DIR"
                nohup ollama serve --library "$OLLAMA_LIBRARY_DIR" > "${TEMP_DIR}/ollama.log" 2>&1 &
            else
                nohup ollama serve > "${TEMP_DIR}/ollama.log" 2>&1 &
            fi
            OLLAMA_PID=$!
            print_status "Ollama started with PID: $OLLAMA_PID"
        fi
        
        wait_for_ollama
    fi
    
    update_progress
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

# -------------------------------------------------------------
# Placeholder function for Ollama WebUI that uses the same dir
# -------------------------------------------------------------
install_ollama_webui() {
    print_status "Installing Ollama WebUI..."
    # This is just a placeholder example. You can customize as needed.
    # The key is: if WebUI supports specifying a library location, set it here.
    
    # For demonstration, we’ll pretend we clone a hypothetical repo:
    #   git clone https://github.com/someone/ollama-webui
    # and pass OLLAMA_LIBRARY_DIR to it.
    
    # Example only:
    if [ ! -d "ollama-webui" ]; then
        print_message "Cloning hypothetical Ollama WebUI..."
        git clone https://github.com/jmorganca/ollama-webui.git ollama-webui
        # Then, if the webui has some config or environment variable for the model path:
        # echo "OLLAMA_LIBRARY_DIR=$OLLAMA_LIBRARY_DIR" >> ollama-webui/.env
        # etc.
    else
        print_status "WebUI repository already exists. Pulling latest changes..."
        (cd ollama-webui && git pull)
    fi
    
    print_success "Ollama WebUI installed (placeholder)."
    print_message "Make sure to configure the WebUI to use $OLLAMA_LIBRARY_DIR for models."
    update_progress
}

setup_venv() {
    print_status "Setting up Python virtual environment..."
    if [ ! -d "venv" ]; then
        print_message "Creating virtual environment..."
        if python3 -m venv venv > /tmp/venv-create.log 2>&1; then
            print_success "Virtual environment created"
        else
            print_error "Failed to create virtual environment"
            cat /tmp/venv-create.log
            exit 1
        fi
    else
        print_success "Virtual environment already exists"
    fi
    
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

install_dependencies() {
    print_status "Installing Python dependencies..."
    print_message "Upgrading pip in virtual environment..."
    if pip3 install --upgrade pip > /tmp/venv-pip-upgrade.log 2>&1; then
        print_success "pip upgraded in virtual environment"
    else
        print_warning "Failed to upgrade pip in virtual environment"
        cat /tmp/venv-pip-upgrade.log
    fi
    
    print_message "Installing main dependencies..."
    main_deps="flask flask-login anthropic>=0.5.0 tqdm>=4.65.0 python-dotenv aiohttp openai"
    print_status "Dependencies to install: $main_deps"
    if pip3 install $main_deps > /tmp/main-deps-install.log 2>&1; then
        print_success "Main dependencies installed"
    else
        print_error "Failed to install main dependencies"
        cat /tmp/main-deps-install.log
        exit 1
    fi
    
    print_message "Installing additional dependencies..."
    if pip3 install flask-cors gunicorn flask-wtf > /tmp/add-deps-install.log 2>&1; then
        print_success "Additional dependencies installed"
    else
        print_warning "Failed to install additional dependencies"
        cat /tmp/add-deps-install.log
    fi
    
    if [ -f "orchestrator/requirements.txt" ]; then
        print_message "Installing orchestrator dependencies..."
        if pip3 install -r orchestrator/requirements.txt > /tmp/orchestrator-deps.log 2>&1; then
            print_success "Orchestrator dependencies installed"
        else
            print_warning "Failed to install orchestrator dependencies"
            cat /tmp/orchestrator-deps.log
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
            cat /tmp/script-agent-deps.log
        fi
    else
        print_status "No script-agent/requirements.txt found, skipping"
    fi
    
    update_progress
}

check_api_keys() {
    print_status "Managing API keys..."
    if [ ! -f ".env" ]; then
        print_status "Creating .env file..."
        touch .env
        chmod 600 .env
        print_status "Set secure permissions on .env file"
    else
        print_status "Found existing .env file"
        if [ "$(stat -c %a .env)" != "600" ]; then
            chmod 600 .env
            print_status "Updated .env file permissions to be secure"
        fi
    fi
    
    if [ -f ".env" ]; then
        print_status "Loading environment variables from .env file..."
        source .env
    fi
    
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        print_warning "ANTHROPIC_API_KEY environment variable is not set."
        read -p "Enter your Anthropic API key (or leave blank to skip): " api_key
        if [ ! -z "$api_key" ]; then
            if [ ${#api_key} -lt 20 ]; then
                print_warning "The API key seems too short. Please verify it's correct."
            fi
            echo "ANTHROPIC_API_KEY=$api_key" >> .env
            export ANTHROPIC_API_KEY="$api_key"
            print_success "Anthropic API key saved to .env file"
        else
            print_warning "Anthropic API key not provided. Some features may not work."
        fi
    else
        print_success "Anthropic API key detected"
    fi
    
    if [ -z "$OPENAI_API_KEY" ]; then
        print_warning "OPENAI_API_KEY environment variable is not set."
        read -p "Enter your OpenAI API key (or leave blank to skip): " api_key
        if [ ! -z "$api_key" ]; then
            if [[ ! "$api_key" =~ ^sk- ]]; then
                print_warning "The API key doesn't start with 'sk-'. Please verify it's correct."
            fi
            echo "OPENAI_API_KEY=$api_key" >> .env
            export OPENAI_API_KEY="$api_key"
            print_success "OpenAI API key saved to .env file"
        else
            print_warning "OpenAI API key not provided. Some features may not work."
        fi
    else
        print_success "OpenAI API key detected"
    fi
    
    if [ -z "$DEEPSEEK_API_KEY" ]; then
        print_warning "DEEPSEEK_API_KEY environment variable is not set."
        read -p "Enter your DeepSeek API key (or leave blank to skip): " api_key
        if [ ! -z "$api_key" ]; then
            if [ ${#api_key} -lt 20 ]; then
                print_warning "The API key seems too short. Please verify it's correct."
            fi
            echo "DEEPSEEK_API_KEY=$api_key" >> .env
            export DEEPSEEK_API_KEY="$api_key"
            print_success "DeepSeek API key saved to .env file"
        else
            print_warning "DeepSeek API key not provided. Some features may not work."
        fi
    else
        print_success "DeepSeek API key detected"
    fi
    
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

create_directories() {
    print_status "Creating directory structure..."
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

create_ollama_provider() {
    print_status "Setting up Ollama provider module..."
    
    if [ ! -f "model_providers/ollama_provider.py" ]; then
        print_message "Creating Ollama provider module..."
        mkdir -p model_providers
        
        cat > model_providers/ollama_provider.py << 'EOF_PROVIDER'
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
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            
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
        """
        pattern = r'```(?:\w+\n)?(.*?)```'
        matches = re.findall(pattern, response, re.DOTALL)
        
        if not matches and not response.startswith('```') and not response.endswith('```'):
            lines = response.split('\n')
            if len(lines) > 1 and any(line.strip().startswith(('def ', 'class ', 'import ', 'from ')) for line in lines):
                return [response]
        
        return matches
    
    def get_model_name(self) -> str:
        return self.model
    
    def get_provider_name(self) -> str:
        return "ollama"
    
    def get_context_window(self) -> int:
        context_windows = {
            "llama3": 8192,
            "llama2": 4096,
            "codellama": 16384,
            "mistral": 8192,
            "mixtral": 32768,
            "phi3": 8192
        }
        base_model = self.model.split(':')[0].lower()
        return context_windows.get(base_model, 4096)
    
    def count_tokens(self, text: str) -> int:
        return len(text.split()) * 1.3
EOF_PROVIDER
        
        print_success "Created model_providers/ollama_provider.py"
    else
        print_status "Ollama provider module already exists"
    fi
    
    if [ ! -f "model_providers/__init__.py" ]; then
        print_status "Creating model_providers/__init__.py with Ollama support..."
        
        cat > model_providers/__init__.py << 'EOF_INIT'
"""
Model Providers Module
Factory for getting appropriate model providers
"""

import os
import importlib
from typing import Optional, Any

PROVIDERS = {
    'ollama': 'model_providers.ollama_provider',
    'claude': 'model_providers.claude_provider',
    'openai': 'model_providers.openai_provider',
    'deepseek': 'model_providers.deepseek_provider'
}

def get_provider(provider_name: str) -> Optional[Any]:
    if provider_name not in PROVIDERS:
        raise ValueError(f"Unknown provider: {provider_name}")
    
    api_key_env_vars = {
        'ollama': 'OLLAMA_API_URL',
        'claude': 'ANTHROPIC_API_KEY',
        'openai': 'OPENAI_API_KEY',
        'deepseek': 'DEEPSEEK_API_KEY'
    }
    
    api_key = os.environ.get(api_key_env_vars.get(provider_name))
    
    if provider_name == 'ollama' and not api_key:
        api_key = "http://localhost:11434"
    
    if not api_key and provider_name != 'ollama':
        print(f"Warning: No API key found for {provider_name}")
        return None
    
    try:
        module_path = PROVIDERS[provider_name]
        module = importlib.import_module(module_path)
        
        provider_classes = {
            'ollama': 'OllamaProvider',
            'claude': 'ClaudeProvider',
            'openai': 'OpenAIProvider',
            'deepseek': 'DeepSeekProvider'
        }
        
        provider_class = getattr(module, provider_classes[provider_name])
        
        if provider_name == 'ollama':
            return provider_class(api_url=api_key)
        else:
            return provider_class(api_key=api_key)
    
    except (ImportError, AttributeError) as e:
        print(f"Error initializing provider {provider_name}: {e}")
        return None
EOF_INIT
        
        print_success "Created model_providers/__init__.py with Ollama support"
    elif ! grep -q "ollama" "model_providers/__init__.py"; then
        print_status "Updating model_providers/__init__.py to include Ollama..."
        cp model_providers/__init__.py model_providers/__init__.py.bak
        
        sed -i 's/PROVIDERS = {/PROVIDERS = {\n    "ollama": "model_providers.ollama_provider",/g' model_providers/__init__.py
        sed -i 's/api_key_env_vars = {/api_key_env_vars = {\n        "ollama": "OLLAMA_API_URL",/g' model_providers/__init__.py
        sed -i 's/provider_classes = {/provider_classes = {\n            "ollama": "OllamaProvider",/g' model_providers/__init__.py
        
        print_success "Updated model_providers/__init__.py to include Ollama"
    else
        print_success "Ollama provider already included in model_providers/__init__.py"
    fi
    
    update_progress
}

setup_models() {
    print_status "Setting up base models in Ollama..."
    
    if ! curl -s --head --fail http://localhost:11434/api/tags > /dev/null 2>&1; then
        print_status "Waiting for Ollama to be ready before downloading models..."
        if ! wait_for_ollama; then
            print_warning "Ollama is not running, skipping model downloads"
            update_progress
            return
        fi
    fi
    
    local available_models
    available_models=$(curl -s http://localhost:11434/api/tags 2>/dev/null | grep -o '"name":"[^"]*"' | cut -d':' -f2 | tr -d '"' | sort || echo "")
    
    if echo "$available_models" | grep -q "llama3"; then
        print_success "llama3 model is already downloaded"
        update_progress
        return
    fi
    
    print_message "Downloading base model (llama3)..."
    print_status "This may take a while depending on your internet connection"
    
    local spin='-\|/'
    local i=0
    
    # Pass library param if we have it, else just do normal "ollama pull"
    if [ -n "$OLLAMA_LIBRARY_DIR" ]; then
        ollama pull llama3 --library "$OLLAMA_LIBRARY_DIR" > "${TEMP_DIR}/ollama-pull.log" 2>&1 &
    else
        ollama pull llama3 > "${TEMP_DIR}/ollama-pull.log" 2>&1 &
    fi
    local pull_pid=$!
    
    while kill -0 $pull_pid 2>/dev/null; do
        i=$(( (i+1) % 4 ))
        printf "\r${CYAN}Downloading model... ${spin:$i:1} ${NC}"
        sleep 0.5
    done
    
    if wait $pull_pid; then
        printf "\r${GREEN}Download complete!     ${NC}\n"
        print_success "Successfully pulled llama3 model"
    else
        printf "\r${RED}Download failed!      ${NC}\n"
        print_warning "Failed to pull llama3 model"
        print_status "You can manually download models later with 'ollama pull <model>'"
        cat "${TEMP_DIR}/ollama-pull.log"
        
        print_status "Trying to pull a smaller model (phi) as fallback..."
        if [ -n "$OLLAMA_LIBRARY_DIR" ]; then
            ollama pull phi --library "$OLLAMA_LIBRARY_DIR" > "${TEMP_DIR}/ollama-pull-phi.log" 2>&1
        else
            ollama pull phi > "${TEMP_DIR}/ollama-pull-phi.log" 2>&1
        fi
        
        if [ $? -eq 0 ]; then
            print_success "Successfully pulled phi model (lightweight alternative)"
        else
            print_warning "Failed to pull any models. You'll need to pull them manually."
            cat "${TEMP_DIR}/ollama-pull-phi.log"
        fi
    fi
    
    update_progress
}

verify_config() {
    print_status "Verifying application configuration..."
    
    if [ ! -f "app.py" ]; then
        print_warning "app.py not found in the current directory"
        print_status "Make sure you're in the right directory or create app.py"
    else
        print_status "Found app.py"
    fi
    
    if [ ! -d "templates" ] || [ -z "$(ls -A templates 2>/dev/null)" ]; then
        print_warning "templates directory is empty or missing"
        print_status "You may need to create template files for the Flask application"
    else
        print_status "Found templates directory with files"
    fi
    
    if [ ! -d "static" ] || [ -z "$(ls -A static 2>/dev/null)" ]; then
        print_warning "static directory is empty or missing"
        print_status "You may need to create static files for the Flask application"
    else
        print_status "Found static directory with files"
    fi
    
    update_progress
}

start_flask() {
    print_status "Preparing to start Flask application..."
    mkdir -p logs
    
    if [ -z "$VIRTUAL_ENV" ]; then
        print_status "Activating virtual environment..."
        source venv/bin/activate
    fi
    
    export FLASK_APP=app.py
    print_status "Set FLASK_APP=app.py"
    
    LOG_FILE="logs/flask_$(date +%Y%m%d_%H%M%S).log"
    print_status "Logs will be written to: $LOG_FILE"
    
    if command_exists lsof; then
        PORT_PID=$(lsof -ti:9000 2>/dev/null)
        if [ ! -z "$PORT_PID" ]; then
            print_warning "Port 9000 is already in use by process $PORT_PID"
            read -p "Do you want to stop the existing process and continue? (y/n): " stop_process
            if [[ "$stop_process" == "y" || "$stop_process" == "Y" ]]; then
                print_status "Stopping process $PORT_PID..."
                kill -9 $PORT_PID 2>/dev/null || $USE_SUDO kill -9 $PORT_PID
                sleep 2
            else
                print_error "Port 9000 is already in use. Please stop the existing process or use a different port."
                exit 1
            fi
        fi
    elif command_exists netstat; then
        if netstat -tuln | grep -q ":9000 "; then
            print_warning "Port 9000 is already in use"
            read -p "Do you want to continue anyway? (y/n): " continue_anyway
            if [[ "$continue_anyway" != "y" && "$continue_anyway" != "Y" ]]; then
                print_error "Aborted by user"
                exit 1
            fi
        fi
    fi
    
    print_message "Starting Flask application on http://0.0.0.0:9000"
    if command_exists gunicorn; then
        print_status "Using gunicorn for production-ready server..."
        nohup gunicorn -b 0.0.0.0:9000 -w 4 --access-logfile logs/access.log --error-logfile logs/error.log app:app > "$LOG_FILE" 2>&1 &
        FLASK_PID=$!
    else
        print_status "Using Flask development server (consider installing gunicorn for production)..."
        nohup flask run --host=0.0.0.0 --port=9000 > "$LOG_FILE" 2>&1 &
        FLASK_PID=$!
    fi
    
    print_status "Waiting for server to start..."
    sleep 3
    
    if ps -p $FLASK_PID > /dev/null; then
        print_success "Application started in background with PID: $FLASK_PID"
        
        if command_exists curl; then
            if curl -s --head --fail http://localhost:9000 > /dev/null; then
                print_success "Server is responding to requests"
            else
                print_warning "Server is running but not responding yet. It may need more time to initialize."
            fi
        fi
    else
        print_error "Flask application failed to start"
        print_status "Check the log at $LOG_FILE for details"
        cat "$LOG_FILE"
        exit 1
    fi
    
    LOCAL_IP=$(hostname -I | awk '{print $1}')
    if [ -z "$LOCAL_IP" ]; then
        LOCAL_IP="localhost"
    fi
    
    update_progress
    
    echo
    echo -e "${BOLD}${GREEN}====== Application Summary ======${NC}"
    echo -e "${BOLD}Flask Web Interface:${NC} http://$LOCAL_IP:9000"
    echo -e "${BOLD}Ollama API:${NC} http://$LOCAL_IP:11434"
    echo -e "${BOLD}Log File:${NC} $(pwd)/$LOG_FILE"
    echo -e "${BOLD}Process ID:${NC} $FLASK_PID (use 'kill $FLASK_PID' to stop)"
    echo
    echo -e "${BOLD}${GREEN}==================================${NC}"
    echo
    print_message "AI Development Orchestration System is now running!"
}

main() {
    show_banner
    START_TIME=$(date +%s)
    
    print_message "Starting AI Code Development Orchestration System setup at $(date)"
    
    check_project_directory
    check_required_commands
    check_root
    detect_os
    
    # --------------------------------------------------------
    # Step: Prompt user for the Ollama install (models) drive
    # --------------------------------------------------------
    select_install_location
    
    if [ "$SKIP_SYSTEM" = "false" ]; then
        print_message "Preparing system..."
        update_system
        install_python
        install_pip
    else
        print_message "Skipping system updates as requested."
        update_progress
        update_progress
        update_progress
    fi
    
    if [ "$SKIP_OLLAMA" = "false" ]; then
        print_message "Setting up Ollama..."
        install_ollama
    else
        print_message "Skipping Ollama installation as requested."
        update_progress
    fi
    
    print_message "Installing Ollama WebUI (placeholder)..."
    install_ollama_webui
    
    print_message "Setting up Python environment..."
    setup_venv
    install_dependencies
    check_api_keys
    create_directories
    create_ollama_provider
    
    if [ "$SKIP_OLLAMA" = "false" ]; then
        setup_models
    else
        print_message "Skipping model downloads as Ollama is skipped."
        update_progress
    fi
    
    verify_config
    
    print_message "Starting Flask application..."
    start_flask
    
    END_TIME=$(date +%s)
    TOTAL_TIME=$((END_TIME - START_TIME))
    MINUTES=$((TOTAL_TIME / 60))
    SECONDS=$((TOTAL_TIME % 60))
    
    print_success "Setup completed in ${MINUTES}m ${SECONDS}s"
}

if [ "$DEBUG" = "true" ]; then
    print_warning "Debug mode enabled"
    print_debug "Bash version: $BASH_VERSION"
    print_debug "OS details: $(uname -a)"
    print_debug "Current working directory: $(pwd)"
    set -x
fi

if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo -e "${BOLD}${BLUE}AI Development Orchestration System Setup Script${NC}"
    echo
    echo "Usage: ./run.sh [OPTIONS]"
    echo
    echo "Options:"
    echo "  --help, -h     Show this help message"
    echo "  --debug        Enable debug output"
    echo "  --skip-system  Skip system updates and tool installation"
    echo "  --skip-ollama  Skip Ollama installation"
    echo
    echo "Environment variables:"
    echo "  DEBUG=true     Enable debug mode"
    echo
    exit 0
fi

SKIP_SYSTEM=false
SKIP_OLLAMA=false

for arg in "$@"; do
    case $arg in
        --debug)
            DEBUG=true
            print_warning "Debug mode enabled"
            ;;
        --skip-system)
            SKIP_SYSTEM=true
            print_warning "Skipping system updates and tool installation"
            ;;
        --skip-ollama)
            SKIP_OLLAMA=true
            print_warning "Skipping Ollama installation"
            ;;
        *)
            print_warning "Unknown option: $arg"
            ;;
    esac
done

unset PYTHONPATH
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
[ -z "$DEBUG" ] && DEBUG=false

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main
else
    print_warning "This script is meant to be executed, not sourced."
    print_message "Run it with: ./run.sh [OPTIONS]"
fi
