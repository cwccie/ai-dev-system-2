#!/bin/bash

# AI Script Agent Runner Script
# This script runs the script agent with the specified parameters

set -e  # Exit immediately if a command exits with a non-zero status

# Colors for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    echo -e "${BLUE}[Script Agent]${NC} $1"
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
    echo "Usage: $0 --name <script_name> --description <description> [options]"
    echo ""
    echo "Required Arguments:"
    echo "  --name <script_name>          Name of the script to generate"
    echo "  --description <description>   Description of the script's purpose"
    echo ""
    echo "Options:"
    echo "  --requirements <req1> <req2>  Specific requirements for the script (multiple args)"
    echo "  --output <output_path>        Path where the script should be saved"
    echo "  --config <config_file>        Path to the script agent configuration file"
    echo "  --provider <provider>         AI model provider to use (claude, openai, deepseek)"
    echo "  --iterations <num>            Number of iterations to run"
    echo "  --help                        Show this help message"
    exit 1
}

# Parse arguments
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    show_usage
fi

# Initialize variables
SCRIPT_NAME=""
DESCRIPTION=""
REQUIREMENTS=()
OUTPUT_PATH=""
CONFIG_FILE=""
PROVIDER=""
ITERATIONS=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --name)
            SCRIPT_NAME="$2"
            shift 2
            ;;
        --description)
            DESCRIPTION="$2"
            shift 2
            ;;
        --requirements)
            # Collect all requirements until next option
            while [[ $# -gt 1 && ! "$2" =~ ^-- ]]; do
                REQUIREMENTS+=("$2")
                shift
            done
            shift
            ;;
        --output)
            OUTPUT_PATH="$2"
            shift 2
            ;;
        --config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --provider)
            PROVIDER="$2"
            shift 2
            ;;
        --iterations)
            ITERATIONS="$2"
            shift 2
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            ;;
    esac
done

# Check required arguments
if [ -z "$SCRIPT_NAME" ]; then
    print_error "Missing required argument: --name"
    show_usage
fi

if [ -z "$DESCRIPTION" ]; then
    print_error "Missing required argument: --description"
    show_usage
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

# Run the script agent
print_message "Running script agent to generate \"$SCRIPT_NAME\""

# Build the command
CMD="python3 claude_script_agent.py --name \"$SCRIPT_NAME\" --description \"$DESCRIPTION\""

# Add requirements if any
if [ ${#REQUIREMENTS[@]} -gt 0 ]; then
    CMD="$CMD --requirements"
    for req in "${REQUIREMENTS[@]}"; do
        CMD="$CMD \"$req\""
    done
fi

# Add optional arguments
if [ ! -z "$OUTPUT_PATH" ]; then
    CMD="$CMD --output \"$OUTPUT_PATH\""
fi

if [ ! -z "$CONFIG_FILE" ]; then
    CMD="$CMD --config \"$CONFIG_FILE\""
fi

if [ ! -z "$PROVIDER" ]; then
    CMD="$CMD --provider \"$PROVIDER\""
fi

if [ ! -z "$ITERATIONS" ]; then
    CMD="$CMD --iterations \"$ITERATIONS\""
fi

# Execute the command
eval $CMD

# Check if the script agent ran successfully
if [ $? -eq 0 ]; then
    print_success "Script generation completed successfully"
else
    print_error "Script generation failed"
    exit 1
fi
