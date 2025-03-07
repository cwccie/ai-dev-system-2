#!/bin/bash

# AI Code Development Orchestration System
# Main runner script to set up environment and run the Flask application

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

# Check if Python 3.6+ is installed
check_python() {
    if ! command_exists python3; then
        print_error "Python 3 is not installed. Please install Python 3.6 or higher."
        exit 1
    fi
    
    # Check Python version
    python_version=$(python3 --version | cut -d' ' -f2)
    python_major=$(echo $python_version | cut -d. -f1)
    python_minor=$(echo $python_version | cut -d. -f2)
    
    if [ "$python_major" -lt 3 ] || ([ "$python_major" -eq 3 ] && [ "$python_minor" -lt 6 ]); then
        print_error "Python version must be 3.6 or higher. Current version: $python_version"
        exit 1
    fi
    
    print_success "Python $python_version detected"
}

# Check if pip is installed
check_pip() {
    if ! command_exists pip3; then
        print_error "pip3 is not installed. Please install pip for Python 3."
        exit 1
    fi
    
    print_success "pip3 detected"
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
}

# Create necessary directories if they don't exist
create_directories() {
    mkdir -p orchestrator/config
    mkdir -p script-agent
    mkdir -p model_providers
    mkdir -p templates
    mkdir -p static/css
    mkdir -p static/js
    
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
    
    print_success "Template files created"
}

# Main function
main() {
    print_message "Starting AI Code Development Orchestration System setup..."
    
    # Perform checks
    check_python
    check_pip
    setup_venv
    install_dependencies
    check_api_keys
    create_directories
    create_templates
    
    # Run the Flask application with nohup
    print_message "Starting Flask application on http://0.0.0.0:9000 in the background"
    export FLASK_APP=app.py
    nohup flask run --host=0.0.0.0 --port=9000 > flask.log 2>&1 &
    print_success "Application started in background with PID: $!"
    print_message "You can view logs at: $(pwd)/flask.log"
}

# Run the main function
main
