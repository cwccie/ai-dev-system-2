#!/bin/bash

# AI Code Development Orchestrator Runner Script
# This script runs the orchestrator with the specified project directory and script definitions

set -e  # Exit immediately if a command exits with a non-zero status

# Colors for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    echo -e "${BLUE}[Orchestrator]${NC} $1"
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

# Function to show usage
show_usage() {
    echo "Usage: $0 <project_directory> <script_definitions_file> [--config <config_file>]"
    echo ""
    echo "Arguments:"
    echo "  project_directory       Path to the project directory to analyze"
    echo "  script_definitions_file Path to the JSON file containing script definitions"
    echo ""
    echo "Options:"
    echo "  --config <config_file>  Path to the orchestrator configuration file"
    echo "  --provider <provider>   AI model provider to use (claude, openai, deepseek)"
    echo "  --help                  Show this help message"
    exit 1
}

# Parse arguments
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    show_usage
fi

if [ $# -lt 2 ]; then
    print_error "Missing required arguments"
    show_usage
fi

PROJECT_DIR="$1"
SCRIPT_DEFS="$2"
CONFIG_FILE=""
PROVIDER=""

# Parse optional arguments
shift 2
while [ $# -gt 0 ]; do
    case "$1" in
        --config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --provider)
            PROVIDER="$2"
            shift 2
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            ;;
    esac
done

# Check if project directory exists
if [ ! -d "$PROJECT_DIR" ]; then
    print_error "Project directory does not exist: $PROJECT_DIR"
    exit 1
fi

# Check if script definitions file exists
if [ ! -f "$SCRIPT_DEFS" ]; then
    print_error "Script definitions file does not exist: $SCRIPT_DEFS"
    exit 1
fi

# Check if config file exists if specified
if [ ! -z "$CONFIG_FILE" ] && [ ! -f "$CONFIG_FILE" ]; then
    print_error "Config file does not exist: $CONFIG_FILE"
    exit 1
fi

# Load environment variables from .env file in the parent directory
if [ -f "../.env" ]; then
    source "../.env"
    print_success "Loaded environment variables from ../.env"
fi

# Activate virtual environment if it exists
if [ -d "../venv" ]; then
    source "../venv/bin/activate"
    print_success "Activated virtual environment"
fi

# Run the orchestrator
print_message "Running orchestrator on $PROJECT_DIR with script definitions from $SCRIPT_DEFS"

# Build the command
CMD="python3 dev_orchestrator.py --project-dir \"$PROJECT_DIR\" --script-defs \"$SCRIPT_DEFS\""

if [ ! -z "$CONFIG_FILE" ]; then
    CMD="$CMD --config \"$CONFIG_FILE\""
fi

if [ ! -z "$PROVIDER" ]; then
    CMD="$CMD --provider \"$PROVIDER\""
fi

# Execute the command
eval $CMD

# Check if the orchestrator ran successfully
if [ $? -eq 0 ]; then
    print_success "Orchestrator completed successfully"
else
    print_error "Orchestrator failed to complete"
    exit 1
fi
