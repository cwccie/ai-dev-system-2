#!/bin/bash
#
# AI Code Development Orchestration System
# Runner script to set up environment, install dependencies, and run Flask application
# (Ollama / WebUI references removed)

# Set +e to continue even if commands fail
set +e

# Create a unique temporary directory for logs and intermediate files
TEMP_DIR=$(mktemp -d -t ai-dev-setup-XXXXXXXXXX)

# Colors for console output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

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
trap 'exit 130' INT  # Handle Ctrl+C gracefully

# Number of setup steps for the progress bar
TOTAL_STEPS=10
CURRENT_STEP=0

# Progress bar logic
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

# Check if a command exists
command_exists() {
    if command -v "$1" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
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
    
    # Optional commands
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
    
    # Check if we have write permissions for current directory
    if ! touch .write-test 2>/dev/null; then
        print_warning "You don't have write permissions in this directory."
        print_status "Some operations may fail. Consider running with proper permissions."
    else
        rm -f .write-test
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
    echo "including all necessary Python libraries and a Flask application."
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
    local essential_tools="net-tools curl wget git build-essential software-properties-common"
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
    
    local python_version
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
    local main_deps="flask flask-login anthropic>=0.5.0 tqdm>=4.65.0 python-dotenv aiohttp openai"
    print_status "Dependencies to install: $main_deps"
    if pip3 install $main_deps > /tmp/main-deps-install.log 2>&1; then
        print_success "Main dependencies installed"
    else
        print_error "Failed to install main dependencies"
        cat /tmp/main-deps-install.log
        exit 1
    fi
    
    print_message "Installing additional dependencies..."
    if pip3 install flask-cors flask-wtf werkzeug > /tmp/add-deps-install.log 2>&1; then
        print_success "Additional dependencies installed"
    else
        print_warning "Failed to install additional dependencies"
        cat /tmp/add-deps-install.log
    fi
    
    # Install gunicorn in virtual environment
    print_message "Installing gunicorn in virtual environment..."
    if pip3 install gunicorn > /tmp/gunicorn-install.log 2>&1; then
        print_success "Gunicorn installed"
    else
        print_warning "Failed to install Gunicorn, will fall back to Flask development server"
        cat /tmp/gunicorn-install.log
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
        chmod 600 .env 2>/dev/null || print_warning "Could not set permissions on .env file"
        print_status "Set secure permissions on .env file"
    else
        print_status "Found existing .env file"
        chmod 600 .env 2>/dev/null || print_warning "Could not update permissions on .env file"
        print_status "Updated .env file permissions to be secure"
    fi
    
    if [ -f ".env" ]; then
        print_status "Loading environment variables from .env file..."
        source .env
    fi
    
    # Example: Anthropic API key
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
    
    # Example: OpenAI API key
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
    
    # Example: DeepSeek API key
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
    
    # Set FLASK_SECRET_KEY if not present
    if [ -z "$FLASK_SECRET_KEY" ]; then
        print_status "Generating Flask secret key..."
        RANDOM_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
        echo "FLASK_SECRET_KEY=$RANDOM_KEY" >> .env
        export FLASK_SECRET_KEY="$RANDOM_KEY"
        print_success "Flask secret key generated and saved to .env file"
    fi
    
    update_progress
}

create_directories() {
    print_status "Creating directory structure..."
    
    # Create directories safely, ignoring errors if they already exist
    mkdir -p orchestrator/config 2>/dev/null || print_warning "Could not create orchestrator/config/"
    print_status "Created orchestrator/config/"
    
    mkdir -p script-agent 2>/dev/null || print_warning "Could not create script-agent/"
    print_status "Created script-agent/"
    
    mkdir -p model_providers 2>/dev/null || print_warning "Could not create model_providers/"
    print_status "Created model_providers/"
    
    mkdir -p templates 2>/dev/null || print_warning "Could not create templates/"
    print_status "Created templates/"
    
    mkdir -p static/css 2>/dev/null || print_warning "Could not create static/css/"
    print_status "Created static/css/"
    
    mkdir -p static/js 2>/dev/null || print_warning "Could not create static/js/"
    print_status "Created static/js/"
    
    mkdir -p logs 2>/dev/null || print_warning "Could not create logs/"
    print_status "Created logs/"
    
    print_status "Setting executable permissions on scripts..."
    
    # Don't fail if chmod fails
    if [ -f "./run.sh" ]; then
        chmod +x run.sh 2>/dev/null || print_warning "Could not make run.sh executable"
        print_status "Made run.sh executable"
    fi
    
    if [ -f "orchestrator/run_orchestrator.sh" ]; then
        chmod +x orchestrator/run_orchestrator.sh 2>/dev/null || print_warning "Could not make orchestrator/run_orchestrator.sh executable"
        print_status "Made orchestrator/run_orchestrator.sh executable"
    else
        print_warning "orchestrator/run_orchestrator.sh not found, skipping"
    fi
    
    if [ -f "script-agent/run_agent.sh" ]; then
        chmod +x script-agent/run_agent.sh 2>/dev/null || print_warning "Could not make script-agent/run_agent.sh executable"
        print_status "Made script-agent/run_agent.sh executable"
    else
        print_warning "script-agent/run_agent.sh not found, skipping"
    fi
    
    print_success "Directory structure ensured"
    update_progress
}

verify_config() {
    print_status "Verifying application configuration..."
    
    if [ ! -f "app.py" ]; then
        print_warning "app.py not found in the current directory"
        print_status "Make sure you're in the correct folder or create app.py"
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
    mkdir -p logs 2>/dev/null || print_warning "Could not create logs directory"
    
    if [ -z "$VIRTUAL_ENV" ]; then
        print_status "Activating virtual environment..."
        source venv/bin/activate
    fi
    
    export FLASK_APP=app.py
    export FLASK_DEBUG=1  # Enable debug mode for development
    print_status "Set FLASK_APP=app.py and FLASK_DEBUG=1"
    
    local LOG_FILE="logs/flask_$(date +%Y%m%d_%H%M%S).log"
    print_status "Logs will be written to: $LOG_FILE"
    
    # Check port 9000 usage
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
                return 1
            fi
        fi
    elif command_exists netstat; then
        if netstat -tuln | grep -q ":9000 "; then
            print_warning "Port 9000 is already in use"
            read -p "Do you want to continue anyway? (y/n): " continue_anyway
            if [[ "$continue_anyway" != "y" && "$continue_anyway" != "Y" ]]; then
                print_error "Aborted by user"
                return 1
            fi
        fi
    fi
    
    # Test if app can be imported before starting
    print_status "Testing Flask application configuration..."
    if ! python3 -c "import app" > /tmp/app-import-test.log 2>&1; then
        print_error "Failed to import app.py - check the application code"
        cat /tmp/app-import-test.log
        print_status "You can try running 'python3 -c \"import app\"' to see the error"
        print_warning "Continuing setup but skipping Flask startup"
        update_progress
        return 1
    fi
    
    # Try a simpler approach first - just run python directly
    print_message "Starting Flask application in test mode..."
    python3 -c "from app import app; print('Flask app found and configured correctly')" > /tmp/app-test.log 2>&1
    if [ $? -ne 0 ]; then
        print_error "Flask application configuration test failed"
        cat /tmp/app-test.log
        print_status "Skipping Flask startup, please fix app.py and try again"
        print_warning "Continuing setup but skipping Flask startup"
        update_progress
        return 1
    else
        print_success "Flask application configuration test passed"
    fi
    
    print_message "Starting Flask application on http://0.0.0.0:9000"
    
    # First try with gunicorn if available
    if command_exists gunicorn || pip3 list | grep -q gunicorn; then
        print_status "Using gunicorn for a production-ready server..."
        gunicorn -b 0.0.0.0:9000 -w 2 --access-logfile logs/access.log --error-logfile logs/error.log app:app > "$LOG_FILE" 2>&1 &
        FLASK_PID=$!
    else
        print_status "Using Flask development server (consider installing gunicorn for production)..."
        python3 -m flask run --host=0.0.0.0 --port=9000 > "$LOG_FILE" 2>&1 &
        FLASK_PID=$!
    fi
    
    print_status "Waiting for server to start..."
    sleep 5  # Give more time for the server to start
    
    if ps -p $FLASK_PID > /dev/null; then
        print_success "Application started in background with PID: $FLASK_PID"
        
        # Save PID to a file for easier management
        echo $FLASK_PID > logs/flask.pid 2>/dev/null || print_warning "Could not save PID to logs/flask.pid"
        print_status "PID saved to logs/flask.pid"
        
        if command_exists curl; then
            # Retry a few times as server might take time to start
            for i in {1..3}; do
                if curl -s --head --fail http://localhost:9000 > /dev/null; then
                    print_success "Server is responding to requests"
                    break
                else
                    print_status "Waiting for server to respond (attempt $i/3)..."
                    sleep 3
                fi
            done
            
            if ! curl -s --head --fail http://localhost:9000 > /dev/null; then
                print_warning "Server started but is not responding to requests yet."
                print_status "Check the logs for more information: $LOG_FILE"
                tail -n 20 "$LOG_FILE" 2>/dev/null || print_warning "Could not read log file"
            fi
        fi
    else
        print_error "Flask application failed to start"
        print_status "Check the log at $LOG_FILE for details"
        cat "$LOG_FILE" 2>/dev/null || print_warning "Could not read log file"
        print_warning "Continuing setup but Flask is not running"
        return 1
    fi
    
    local LOCAL_IP
    LOCAL_IP=$(hostname -I | awk '{print $1}')
    if [ -z "$LOCAL_IP" ]; then
        LOCAL_IP="localhost"
    fi
    
    update_progress
    
    echo
    echo -e "${BOLD}${GREEN}====== Application Summary ======${NC}"
    echo -e "${BOLD}Flask Web Interface:${NC} http://$LOCAL_IP:9000"
    echo -e "${BOLD}Log File:${NC} $(pwd)/$LOG_FILE"
    if [ ! -z "$FLASK_PID" ]; then
        echo -e "${BOLD}Process ID:${NC} $FLASK_PID (use 'kill $FLASK_PID' to stop)"
        echo -e "${BOLD}To stop the server:${NC} kill $(cat logs/flask.pid 2>/dev/null || echo $FLASK_PID)"
    else
        echo -e "${BOLD}Flask Status:${NC} Not running (manual start required)"
    fi
    echo
    echo -e "${BOLD}${GREEN}==================================${NC}"
    echo
    print_message "AI Development Orchestration System setup complete!"
    if [ ! -z "$FLASK_PID" ]; then
        print_message "System is now running!"
    else
        print_message "Setup complete, but Flask is not running. Start it manually after fixing any issues."
    fi
}

main() {
    show_banner
    START_TIME=$(date +%s)
    
    print_message "Starting AI Code Development Orchestration System setup at $(date)"
    
    check_project_directory
    check_required_commands
    check_root
    detect_os
    
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
    
    print_message "Setting up Python environment..."
    setup_venv
    install_dependencies
    check_api_keys
    create_directories
    
    verify_config
    
    print_message "Starting Flask application..."
    start_flask
    
    END_TIME=$(date +%s)
    TOTAL_TIME=$((END_TIME - START_TIME))
    local MINUTES=$((TOTAL_TIME / 60))
    local SECONDS=$((TOTAL_TIME % 60))
    
    print_success "Setup completed in ${MINUTES}m ${SECONDS}s"
}

# Debug mode checks
if [ "$DEBUG" = "true" ]; then
    print_warning "Debug mode enabled"
    print_debug "Current working directory: $(pwd)"
    set -x
fi

# Help flag
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo -e "${BOLD}${BLUE}AI Development Orchestration System Setup Script${NC}"
    echo
    echo "Usage: ./run.sh [OPTIONS]"
    echo
    echo "Options:"
    echo "  --help, -h     Show this help message"
    echo "  --debug        Enable debug output"
    echo "  --skip-system  Skip system updates and tool installation"
    echo
    echo "Environment variables:"
    echo "  DEBUG=true     Enable debug mode"
    echo
    exit 0
fi

# Default flags
SKIP_SYSTEM=false

# Parse arguments
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
        *)
            print_warning "Unknown option: $arg"
            ;;
    esac
done

unset PYTHONPATH
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
[ -z "$DEBUG" ] && DEBUG=false

# Run main if script is executed, not sourced
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main
else
    print_warning "This script is meant to be executed, not sourced."
    print_message "Run it with: ./run.sh [OPTIONS]"
fi

# Debug information (moved outside the if-else block)
print_debug "Bash version: $BASH_VERSION"
print_debug "OS details: $(uname -a)"