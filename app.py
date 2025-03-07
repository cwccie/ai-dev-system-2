"""
AI Code Development Orchestration System
Main Flask application serving as the entry point
"""

import os
import sys
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import components
try:
    from orchestrator.dev_orchestrator import TaskOrchestrator
    from script_agent.claude_script_agent import ScriptAgent
    from model_providers import get_provider
except ImportError as e:
    print(f"Import error: {e}. Some components may not be available.")

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Single user with hardcoded credentials
# In a real application, you would use a database
users = {
    1: User(1, 'cwccie', generate_password_hash('password'))  # Replace 'password' with a secure password
}

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return users.get(int(user_id))

# Available model providers
MODEL_PROVIDERS = {
    'claude': 'Claude (Anthropic)',
    'openai': 'GPT (OpenAI)',
    'deepseek': 'DeepSeek'
}

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check if username is correct
        if username != 'cwccie':
            return render_template('login.html', error="Invalid username or password")
        
        # Find user by username
        for user in users.values():
            if user.username == username:
                # Check password
                if user.check_password(password):
                    login_user(user)
                    return redirect(url_for('index'))
        
        # If we get here, authentication failed
        return render_template('login.html', error="Invalid username or password")
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Handle user logout"""
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """Render the main landing page"""
    # Check which API keys are set
    api_keys = {
        'claude': bool(os.environ.get('ANTHROPIC_API_KEY')),
        'openai': bool(os.environ.get('OPENAI_API_KEY')),
        'deepseek': bool(os.environ.get('DEEPSEEK_API_KEY'))
    }
    
    return render_template('index.html', 
                           model_providers=MODEL_PROVIDERS,
                           api_keys=api_keys)

@app.route('/orchestrator')
@login_required
def orchestrator():
    """Render the orchestrator interface"""
    # Check for config file
    config_path = os.path.join('orchestrator', 'config', 'orchestrator_config.json')
    config = {}
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
    
    return render_template('orchestrator.html',
                           model_providers=MODEL_PROVIDERS,
                           config=config)

@app.route('/script_agent')
@login_required
def script_agent():
    """Render the script agent interface"""
    # Check for config file
    config_path = os.path.join('script-agent', 'config.json')
    config = {}
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
    
    return render_template('script_agent.html',
                           model_providers=MODEL_PROVIDERS,
                           config=config)

@app.route('/save_api_key', methods=['POST'])
@login_required
def save_api_key():
    """Save API key to .env file"""
    provider = request.form.get('provider')
    api_key = request.form.get('api_key')
    
    if not provider or provider not in MODEL_PROVIDERS:
        return jsonify({'success': False, 'message': 'Invalid provider'})
    
    if not api_key and api_key.strip() == '':
        return jsonify({'success': False, 'message': 'API key cannot be empty'})
    
    # Map provider to environment variable name
    env_vars = {
        'claude': 'ANTHROPIC_API_KEY',
        'openai': 'OPENAI_API_KEY',
        'deepseek': 'DEEPSEEK_API_KEY'
    }
    
    env_var = env_vars.get(provider)
    if not env_var:
        return jsonify({'success': False, 'message': 'Unknown provider'})
    
    # Update environment variable
    os.environ[env_var] = api_key
    
    # Update .env file
    env_file_path = '.env'
    env_data = {}
    
    # Read existing .env file
    if os.path.exists(env_file_path):
        with open(env_file_path, 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    env_data[key] = value
    
    # Update with new key
    env_data[env_var] = api_key
    
    # Write back to .env file
    with open(env_file_path, 'w') as f:
        for key, value in env_data.items():
            f.write(f"{key}={value}\n")
    
    return jsonify({'success': True, 'message': f'{MODEL_PROVIDERS[provider]} API key saved successfully'})

@app.route('/run_script_agent', methods=['POST'])
@login_required
def run_script_agent():
    """Run the script agent to generate a single script"""
    try:
        # Get form data
        script_name = request.form.get('script_name')
        script_description = request.form.get('script_description')
        model_provider = request.form.get('model_provider', 'claude')
        
        if not script_name or not script_description:
            return jsonify({'success': False, 'error': 'Script name and description are required'})
        
        # Initialize model provider
        provider = get_provider(model_provider)
        if not provider:
            return jsonify({'success': False, 'error': f'Could not initialize {MODEL_PROVIDERS[model_provider]} provider'})
        
        # Initialize script agent
        agent = ScriptAgent(provider=provider)
        
        # Generate script
        script = agent.generate_script(
            name=script_name,
            description=script_description,
            iterations=int(request.form.get('iterations', 1))
        )
        
        return jsonify({
            'success': True,
            'script': script,
            'provider_used': MODEL_PROVIDERS[model_provider]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/run_orchestrator', methods=['POST'])
@login_required
def run_orchestrator():
    """Run the orchestrator to generate multiple scripts"""
    try:
        # Get form data
        project_dir = request.form.get('project_dir')
        script_definitions = request.form.get('script_definitions')
        model_provider = request.form.get('model_provider', 'claude')
        
        if not project_dir or not script_definitions:
            return jsonify({'success': False, 'error': 'Project directory and script definitions are required'})
        
        # Parse script definitions
        try:
            script_defs = json.loads(script_definitions)
        except json.JSONDecodeError:
            return jsonify({'success': False, 'error': 'Invalid script definitions format'})
        
        # Initialize model provider
        provider = get_provider(model_provider)
        if not provider:
            return jsonify({'success': False, 'error': f'Could not initialize {MODEL_PROVIDERS[model_provider]} provider'})
        
        # Initialize orchestrator
        orchestrator = TaskOrchestrator(provider=provider)
        
        # Generate scripts
        results = orchestrator.orchestrate(
            project_dir=project_dir,
            script_definitions=script_defs
        )
        
        return jsonify({
            'success': True,
            'results': results,
            'provider_used': MODEL_PROVIDERS[model_provider]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000, debug=True)
