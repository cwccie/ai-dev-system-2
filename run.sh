#!/bin/bash

# AI Code Development Orchestration System
# Enhanced runner script to set up environment, install all dependencies, and run the Flask application

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
        print_warning "This script is not running as root. Some operations may require sudo privileges."
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
    python_major=$(echo $python_version | cut -d. -f1)
    python_minor=$(echo $python_version | cut -d. -f2)
    
    if [ "$python_major" -lt 3 ] || ([ "$python_major" -eq 3 ] && [ "$python_minor" -lt 6 ]); then
        print_warning "Python version should be 3.6 or higher. Current version: $python_version"
        print_message "Attempting to install Python 3.10..."
        
        if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
            $USE_SUDO add-apt-repository -y ppa:deadsnakes/ppa
            $USE_SUDO apt-get update
            $USE_SUDO apt-get install -y python3.10 python3.10-venv python3.10-dev
            
            # Create symbolic links if necessary
            if [ ! -f /usr/bin/python3.10 ]; then
                print_error "Python 3.10 installation failed"
                exit 1
            else
                print_success "Python 3.10 installed successfully"
            fi
        else
            print_error "Automatic Python upgrade not supported on this OS"
            print_message "Please install Python 3.6+ manually and run this script again"
            exit 1
        fi
    else
        print_success "Python $python_version detected"
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

# Install Ollama and Web UI
install_ollama() {
    print_message "Installing Ollama..."
    
    if ! command_exists ollama; then
        curl -fsSL https://ollama.com/install.sh | $USE_SUDO sh
        print_success "Ollama installed"
    else
        print_success "Ollama is already installed"
    fi
    
    # Make sure Ollama service is running
    print_message "Starting Ollama service..."
    if command_exists systemctl; then
        $USE_SUDO systemctl enable --now ollama
        $USE_SUDO systemctl restart ollama
    else
        # Start Ollama in the background if not managed by systemd
        nohup ollama serve > ollama.log 2>&1 &
    fi
    
    # Wait for Ollama to start up
    print_message "Waiting for Ollama service to start..."
    sleep 5
    
    # Install Ollama Web UI
    print_message "Installing Ollama Web UI..."
    
    if [ ! -d "ollama-webui" ]; then
        git clone https://github.com/ollama-webui/ollama-webui.git
        cd ollama-webui
        
        # If using Docker method
        if command_exists docker; then
            $USE_SUDO docker-compose up -d
            print_success "Ollama Web UI started with Docker"
        else
            # Install Node.js and build the web UI
            if ! command_exists node; then
                print_message "Installing Node.js..."
                curl -fsSL https://deb.nodesource.com/setup_18.x | $USE_SUDO bash -
                $USE_SUDO apt-get install -y nodejs
            fi
            
            print_message "Building Ollama Web UI..."
            npm install
            npm run build
            
            # Start the Web UI in the background
            npm run start > ollama-webui.log 2>&1 &
            print_success "Ollama Web UI started"
        fi
        
        cd ..
    else
        print_success "Ollama Web UI already installed"
        
        # Ensure it's running
        cd ollama-webui
        if command_exists docker; then
            $USE_SUDO docker-compose restart
        else
            # Kill any existing processes and restart
            pkill -f "npm run start" || true
            npm run start > ollama-webui.log 2>&1 &
        fi
        cd ..
        
        print_success "Ollama Web UI restarted"
    fi
    
    print_message "Ollama available at http://localhost:11434"
    print_message "Ollama Web UI available at http://localhost:3000"
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
    pip3 install flask-cors gunicorn flask-wtf flask-socketio
    
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

# Create template files if they don't exist
create_templates() {
    print_message "Ensuring template files exist..."
    
    # Create CSS file
    if [ ! -f "static/css/main.css" ]; then
        cat > static/css/main.css << 'EOF'
/* Main styles for AI Dev Orchestration System */
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    margin: 0;
    padding: 0;
    color: #333;
    background-color: #f8f9fa;
}

.container {
    width: 90%;
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

header {
    background-color: #0366d6;
    color: white;
    padding: 1rem;
    margin-bottom: 2rem;
}

h1, h2, h3 {
    color: #0366d6;
}

.card {
    background: white;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    padding: 20px;
    margin-bottom: 20px;
}

.form-group {
    margin-bottom: 15px;
}

label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
}

input[type="text"], 
input[type="password"],
select, 
textarea {
    width: 100%;
    padding: 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
    box-sizing: border-box;
    font-size: 16px;
}

textarea {
    min-height: 150px;
}

button, .btn {
    background-color: #0366d6;
    color: white;
    border: none;
    padding: 10px 15px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
}

button:hover, .btn:hover {
    background-color: #0258b8;
}

.alert {
    padding: 10px 15px;
    border-radius: 4px;
    margin-bottom: 15px;
}

.alert-success {
    background-color: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}

.alert-warning {
    background-color: #fff3cd;
    color: #856404;
    border: 1px solid #ffeeba;
}

.alert-danger {
    background-color: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
}

.model-settings {
    display: none;
    padding-top: 15px;
    border-top: 1px solid #eee;
}

.provider-section {
    margin-bottom: 30px;
}

.footer {
    margin-top: 50px;
    text-align: center;
    color: #6c757d;
    font-size: 14px;
    padding: 20px 0;
    border-top: 1px solid #eee;
}
EOF
        print_success "Created main.css"
    fi
    
    # Create JavaScript file
    if [ ! -f "static/js/main.js" ]; then
        cat > static/js/main.js << 'EOF'
// Main JavaScript file for AI Dev Orchestration System

document.addEventListener('DOMContentLoaded', function() {
    // Handle model provider selection
    const modelSelectElements = document.querySelectorAll('.model-select');
    
    modelSelectElements.forEach(select => {
        select.addEventListener('change', function() {
            const parent = this.closest('.provider-section');
            const allSettings = parent.querySelectorAll('.model-settings');
            
            // Hide all settings first
            allSettings.forEach(settings => {
                settings.style.display = 'none';
            });
            
            // Show selected model settings
            const selectedModel = this.value;
            const targetSettings = parent.querySelector(`.${selectedModel}-settings`);
            if (targetSettings) {
                targetSettings.style.display = 'block';
            }
        });
        
        // Trigger change event to set initial state
        select.dispatchEvent(new Event('change'));
    });
    
    // Handle form submissions with AJAX
    const scriptForm = document.getElementById('script-form');
    if (scriptForm) {
        scriptForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const resultContainer = document.getElementById('result-container');
            resultContainer.innerHTML = '<div class="alert alert-info">Generating script... This may take a moment.</div>';
            
            const formData = new FormData(this);
            
            fetch(this.action, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    resultContainer.innerHTML = `
                        <div class="alert alert-success">Script generated successfully!</div>
                        <div class="card">
                            <h3>Generated Script</h3>
                            <pre><code>${data.script}</code></pre>
                        </div>
                    `;
                } else {
                    resultContainer.innerHTML = `
                        <div class="alert alert-danger">Error: ${data.error}</div>
                    `;
                }
            })
            .catch(error => {
                resultContainer.innerHTML = `
                    <div class="alert alert-danger">An error occurred during script generation.</div>
                    <p>${error}</p>
                `;
                console.error('Error:', error);
            });
        });
    }
    
    // API key management
    const apiKeyForms = document.querySelectorAll('.api-key-form');
    if (apiKeyForms) {
        apiKeyForms.forEach(form => {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const formData = new FormData(this);
                const statusElement = this.querySelector('.status-message');
                
                fetch('/save_api_key', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        statusElement.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
                    } else {
                        statusElement.innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
                    }
                })
                .catch(error => {
                    statusElement.innerHTML = `<div class="alert alert-danger">An error occurred while saving the API key.</div>`;
                    console.error('Error:', error);
                });
            });
        });
    }
});
EOF
        print_success "Created main.js"
    fi
    
    # Create Ollama provider module
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
        # A better approach would be to call the tokenize API if/when it becomes available
        return len(text.split()) * 1.3  # Rough estimate based on typical tokenization
EOF
        print_success "Created Ollama provider module"
    fi
    
    # Update __init__.py to include Ollama provider
    if [ -f "model_providers/__init__.py" ]; then
        # Check if Ollama provider is already included
        if ! grep -q "ollama" "model_providers/__init__.py"; then
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
    else
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
    fi
    
    print_success "Template files created/updated"
}

# Create production configuration for Flask
create_production_config() {
    print_message "Creating production configuration..."
    
    # Create a proper systemd service file for the Flask application
    if command_exists systemctl; then
        cat > ai-dev-orchestrator.service << EOF
[Unit]
Description=AI Development Orchestration System
After=network.target

[Service]
User=$(whoami)
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/gunicorn -b 0.0.0.0:9000 -w 4 app:app
Restart=always
RestartSec=5
Environment="PATH=$(pwd)/venv/bin:$PATH"
EnvironmentFile=$(pwd)/.env

[Install]
WantedBy=multi-user.target
EOF
        
        # Install the service if running as root
        if [ -z "$USE_SUDO" ]; then
            mv ai-dev-orchestrator.service /etc/systemd/system/
            systemctl daemon-reload
            systemctl enable ai-dev-orchestrator.service
            print_success "Systemd service installed and enabled"
        else
            print_message "To install the systemd service, run:"
            print_message "$USE_SUDO mv $(pwd)/ai-dev-orchestrator.service /etc/systemd/system/"
            print_message "$USE_SUDO systemctl daemon-reload"
            print_message "$USE_SUDO systemctl enable ai-dev-orchestrator.service"
        fi
    fi
    
    # Create a backup startup script that doesn't rely on systemd
    cat > start_server.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
export FLASK_APP=app.py
export FLASK_ENV=production
gunicorn -b 0.0.0.0:9000 -w 4 app:app
EOF
    chmod +x start_server.sh
    
    print_success "Production configuration created"
}

# Configure firewall rules
configure_firewall() {
    print_message "Configuring firewall rules..."
    
    if command_exists ufw; then
        $USE_SUDO ufw allow 9000/tcp
        $USE_SUDO ufw allow 11434/tcp
        $USE_SUDO ufw allow 3000/tcp
        
        # Only enable if ufw is installed but not active
        if ! $USE_SUDO ufw status | grep -q "Status: active"; then
            print_warning "Firewall (ufw) is not active. Enable with: sudo ufw enable"
        fi
        
        print_success "Firewall rules configured for ports 9000, 11434, and 3000"
    elif command_exists firewall-cmd; then
        $USE_SUDO firewall-cmd --permanent --add-port=9000/tcp
        $USE_SUDO firewall-cmd --permanent --add-port=11434/tcp
        $USE_SUDO firewall-cmd --permanent --add-port=3000/tcp
        $USE_SUDO firewall-cmd --reload
        
        print_success "Firewall rules configured for ports 9000, 11434, and 3000"
    else
        print_warning "No supported firewall detected. Please manually configure firewall rules if needed."
        print_warning "You may need to allow traffic on ports 9000, 11434, and 3000"
    fi