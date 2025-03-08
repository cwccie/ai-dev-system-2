"""
AI Code Development Orchestration System
Main Flask application serving as the entry point
"""

import os
import sys
import json
import logging
import asyncio
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import components
try:
    from orchestrator.dev_orchestrator import TaskOrchestrator
    from orchestrator.script_planner import ScriptPlanner
    from orchestrator.decomposition_engine import DecompositionEngine
    from orchestrator.dependency_manager import DependencyManager
    from orchestrator.cost_estimator import CostEstimator
    from orchestrator.agent_pool import AgentPool
    from orchestrator.script_assembler import ScriptAssembler
    from orchestrator.model_recommender import ModelRecommender
    from orchestrator.failure_handler import FailureHandler
    from script_agent.claude_script_agent import ScriptAgent
    from script_agent.component_generator import ComponentGenerator
    from model_providers import get_provider
except ImportError as e:
    logger.error(f"Import error: {e}. Some components may not be available.")

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('ENVIRONMENT') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=4)

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

# Global instances for shared components
cost_estimator = None
model_recommender = None
agent_pool = None

# Helper function to run async functions in a synchronous context
def run_async(coro):
    """Runs an async function in a synchronous context using the current event loop or a new one."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)

# Initialize shared components
def init_shared_components():
    global cost_estimator, model_recommender, agent_pool
    
    try:
        # Load configurations
        pricing_config_path = os.path.join('orchestrator', 'config', 'pricing_config.json')
        models_config_path = os.path.join('orchestrator', 'config', 'models_config.json')
        orchestrator_config_path = os.path.join('orchestrator', 'config', 'orchestrator_config.json')
        
        # Initialize components if not already initialized
        if cost_estimator is None and os.path.exists(pricing_config_path):
            cost_estimator = CostEstimator(pricing_config_path)
            logger.info("CostEstimator initialized")
            
        if model_recommender is None and os.path.exists(models_config_path):
            model_recommender = ModelRecommender(models_config_path)
            logger.info("ModelRecommender initialized")
            
        if agent_pool is None:
            # Load orchestrator config for pool settings
            config = {}
            if os.path.exists(orchestrator_config_path):
                with open(orchestrator_config_path, 'r') as f:
                    config = json.load(f)
            
            agent_pool = AgentPool(config)
            logger.info("AgentPool initialized")
    
    except Exception as e:
        logger.error(f"Error initializing shared components: {e}")

# Initialize components at startup
init_shared_components()

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
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
                    next_page = request.args.get('next')
                    return redirect(next_page or url_for('index'))
        
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

@app.route('/dashboard')
@login_required
def dashboard():
    """Render the monitoring dashboard"""
    return render_template('dashboard.html')

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

# Async version of generate_script
async def async_generate_script(agent, name, description, requirements, iterations):
    """Async wrapper for generate_script"""
    return await agent.generate_script(
        name=name,
        description=description,
        requirements=requirements,
        iterations=iterations
    )

@app.route('/run_script_agent', methods=['POST'])
@login_required
def run_script_agent():
    """Run the script agent to generate a single script"""
    try:
        # Get form data
        script_name = request.form.get('script_name')
        script_description = request.form.get('script_description')
        model_provider = request.form.get('model_provider', 'claude')
        model_name = request.form.get('model_name', '')
        
        if not script_name or not script_description:
            return jsonify({'success': False, 'error': 'Script name and description are required'})
        
        # Get model recommendation if no specific model selected
        if not model_name and model_recommender:
            script_def = {
                'name': script_name,
                'description': script_description,
                'requirements': request.form.getlist('requirements[]')
            }
            
            recommendation = model_recommender.recommend_model(script_def, provider_preference=model_provider)
            model_name = recommendation.get('recommended_model')
            
            logger.info(f"Using recommended model: {model_name}")
        
        # Initialize model provider
        provider = get_provider(model_provider)
        if not provider:
            return jsonify({'success': False, 'error': f'Could not initialize {MODEL_PROVIDERS[model_provider]} provider'})
        
        # Set model if specified
        if model_name:
            provider.model = model_name
        
        # Initialize script agent
        agent = ScriptAgent(provider=provider)
        
        # Generate script - using the synchronous wrapper for the async call
        script = run_async(async_generate_script(
            agent=agent,
            name=script_name,
            description=script_description,
            requirements=request.form.getlist('requirements[]'),
            iterations=int(request.form.get('iterations', 1))
        ))
        
        # Estimate cost if available
        cost_info = {}
        if cost_estimator:
            script_def = {
                'name': script_name,
                'description': script_description,
                'requirements': request.form.getlist('requirements[]')
            }
            cost_info = cost_estimator.estimate_script_cost(
                script_def, 
                provider_name=model_provider,
                model_name=model_name or provider.model
            )
        
        return jsonify({
            'success': True,
            'script': script,
            'provider_used': MODEL_PROVIDERS[model_provider],
            'model_used': model_name or provider.model,
            'cost_info': cost_info
        })
        
    except Exception as e:
        logger.error(f"Error in run_script_agent: {e}")
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
        model_name = request.form.get('model_name', '')
        use_parallelism = request.form.get('use_parallelism', 'false') == 'true'
        
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
        
        # Set model if specified
        if model_name:
            provider.model = model_name
        
        # Initialize orchestrator with enhanced components
        config_path = os.path.join('orchestrator', 'config', 'orchestrator_config.json')
        orchestrator = TaskOrchestrator(provider=provider, config_path=config_path)
        
        # Enable or disable advanced features based on form data
        orchestrator_config = orchestrator.config.copy()
        
        # Update parallelism setting
        if 'parallelism' in orchestrator_config:
            orchestrator_config['parallelism']['enabled'] = use_parallelism
        
        # Generate scripts
        results = orchestrator.orchestrate(
            project_dir=project_dir,
            script_definitions=script_defs,
            config_override=orchestrator_config
        )
        
        # Estimate total cost if available
        cost_info = {}
        if cost_estimator:
            cost_info = cost_estimator.estimate_project_cost(
                script_defs,
                provider_name=model_provider,
                model_name=model_name or provider.model
            )
        
        return jsonify({
            'success': True,
            'results': results,
            'provider_used': MODEL_PROVIDERS[model_provider],
            'model_used': model_name or provider.model,
            'cost_info': cost_info
        })
        
    except Exception as e:
        logger.error(f"Error in run_orchestrator: {e}")
        return jsonify({'success': False, 'error': str(e)})

# Dashboard API endpoints
@app.route('/api/dashboard/tasks', methods=['GET'])
@login_required
def get_dashboard_tasks():
    """Get tasks for dashboard"""
    if agent_pool:
        tasks = agent_pool.get_all_tasks()
        return jsonify({'success': True, 'tasks': tasks})
    else:
        return jsonify({'success': False, 'error': 'Agent pool not initialized', 'tasks': []})

@app.route('/api/dashboard/stats', methods=['GET'])
@login_required
def get_dashboard_stats():
    """Get stats for dashboard"""
    if agent_pool:
        stats = agent_pool.get_pool_stats()
        return jsonify({'success': True, 'stats': stats})
    else:
        return jsonify({'success': False, 'error': 'Agent pool not initialized', 'stats': {}})

@app.route('/api/dashboard/cost', methods=['GET'])
@login_required
def get_dashboard_cost():
    """Get cost data for dashboard"""
    try:
        # In a real implementation, this would come from a database
        # Mock data for demonstration
        cost_data = {
            'current_session': 1.24,
            'daily': 3.75,
            'monthly': 45.20,
            'monthly_budget': 50.00,
            'by_provider': {
                'claude': 24.30,
                'openai': 14.50,
                'deepseek': 6.40
            },
            'trend': [
                {'date': '2023-03-01', 'cost': 1.20},
                {'date': '2023-03-02', 'cost': 0.85},
                {'date': '2023-03-03', 'cost': 1.50},
                {'date': '2023-03-04', 'cost': 2.30},
                {'date': '2023-03-05', 'cost': 1.75},
                {'date': '2023-03-06', 'cost': 1.35},
                {'date': '2023-03-07', 'cost': 3.75}
            ]
        }
        
        return jsonify({'success': True, 'data': cost_data})
    except Exception as e:
        logger.error(f"Error getting cost data: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/recommend_model', methods=['POST'])
@login_required
def recommend_model():
    """Recommend model for a script definition"""
    try:
        data = request.json
        
        if not data or not isinstance(data, dict):
            return jsonify({'success': False, 'error': 'Invalid request data'})
        
        script_def = {
            'name': data.get('name', ''),
            'description': data.get('description', ''),
            'requirements': data.get('requirements', [])
        }
        
        provider_preference = data.get('provider_preference')
        
        # Make recommendation if model recommender is available
        if model_recommender:
            recommendation = model_recommender.recommend_model(script_def, provider_preference)
            return jsonify({
                'success': True, 
                'recommendation': recommendation
            })
        else:
            return jsonify({
                'success': False, 
                'error': 'Model recommender not initialized',
                'fallback': {
                    'recommended_model': 'claude-3-7-sonnet-20250219',
                    'recommended_provider': 'claude'
                }
            })
            
    except Exception as e:
        logger.error(f"Error in recommend_model: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/estimate_cost', methods=['POST'])
@login_required
def estimate_cost():
    """Estimate cost for a script definition"""
    try:
        data = request.json
        
        if not data or not isinstance(data, dict):
            return jsonify({'success': False, 'error': 'Invalid request data'})
        
        script_def = {
            'name': data.get('name', ''),
            'description': data.get('description', ''),
            'requirements': data.get('requirements', [])
        }
        
        provider_name = data.get('provider_name')
        model_name = data.get('model_name')
        
        # Make estimate if cost estimator is available
        if cost_estimator:
            estimate = cost_estimator.estimate_script_cost(script_def, provider_name, model_name)
            return jsonify({
                'success': True, 
                'estimate': estimate
            })
        else:
            return jsonify({
                'success': False, 
                'error': 'Cost estimator not initialized'
            })
            
    except Exception as e:
        logger.error(f"Error in estimate_cost: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/decompose_script', methods=['POST'])
@login_required
def decompose_script():
    """Decompose a script definition into components"""
    try:
        data = request.json
        
        if not data or not isinstance(data, dict):
            return jsonify({'success': False, 'error': 'Invalid request data'})
        
        script_def = {
            'name': data.get('name', ''),
            'description': data.get('description', ''),
            'requirements': data.get('requirements', []),
            'path': data.get('path', '')
        }
        
        # Initialize decomposition engine
        config_path = os.path.join('orchestrator', 'config', 'orchestrator_config.json')
        config = {}
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
        
        decomposition_engine = DecompositionEngine(config)
        
        # Decompose the script
        result = decomposition_engine.decompose_script(script_def)
        
        return jsonify({
            'success': True,
            'decomposition': result
        })
        
    except Exception as e:
        logger.error(f"Error in decompose_script: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/dependencies', methods=['POST'])
@login_required
def analyze_dependencies():
    """Analyze dependencies between components"""
    try:
        data = request.json
        
        if not data or not isinstance(data, list):
            return jsonify({'success': False, 'error': 'Invalid request data'})
        
        # Initialize dependency manager
        config_path = os.path.join('orchestrator', 'config', 'orchestrator_config.json')
        config = {}
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
        
        dependency_manager = DependencyManager(config)
        
        # Analyze dependencies
        analysis = dependency_manager.analyze_dependencies(data)
        
        # Suggest parallelization
        parallel_suggestion = dependency_manager.suggest_parallel_execution(data)
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'parallel_suggestion': parallel_suggestion
        })
        
    except Exception as e:
        logger.error(f"Error in analyze_dependencies: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    logger.error(f"Server error: {error}")
    return render_template('500.html'), 500

# Async helper for get_available_models
async def async_get_available_models():
    """Async wrapper for get_available_models"""
    from model_providers import get_available_models
    return await get_available_models()

@app.route('/api/local_models/models/<role>', methods=['GET'])
@login_required
def get_models_by_role(role):
    """Get models for a specific role (coding or orchestration)"""
    try:
        # Check if role is valid
        if role not in ['coding', 'orchestration', 'all']:
            return jsonify({
                'success': False,
                'error': f'Invalid role: {role}'
            })
        
        # Get models using the synchronous wrapper for the async call
        all_models = run_async(async_get_available_models())
        
        # Get ollama models
        local_models = all_models.get('ollama', [])
        
        if role == 'all':
            # Return all models
            models = local_models
        else:
            # Filter by role
            models = [model for model in local_models if model.get('role') == role]
            
            # Sort by rank
            models.sort(key=lambda m: m.get('rank', 999))
        
        return jsonify({
            'success': True,
            'models': models
        })
    except Exception as e:
        logger.error(f"Error getting {role} models: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

"""
API Routes for Local Models Management
These routes need to be added to the app.py file
"""

@app.route('/local_models')
@login_required
def local_models():
    """Render the local models management page"""
    return render_template('local_models.html')

@app.route('/api/local_models/servers', methods=['GET'])
@login_required
def get_servers():
    """Get all configured servers"""
    try:
        # Initialize server manager if not already done
        from model_providers.server_manager import get_server_manager
        server_manager = get_server_manager()
        
        # Get all servers
        servers = server_manager.get_all_servers()
        
        return jsonify({
            'success': True,
            'servers': servers
        })
    except Exception as e:
        logger.error(f"Error getting servers: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/local_models/servers/<server_id>', methods=['POST'])
@login_required
def add_server(server_id):
    """Add a new server"""
    try:
        # Get request data
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            })
        
        # Initialize server manager
        from model_providers.server_manager import get_server_manager
        server_manager = get_server_manager()
        
        # Add server
        success = server_manager.add_server(server_id, data)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Server {server_id} added successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to add server {server_id}'
            })
    except Exception as e:
        logger.error(f"Error adding server: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/local_models/servers/<server_id>', methods=['PUT'])
@login_required
def update_server(server_id):
    """Update an existing server"""
    try:
        # Get request data
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            })
        
        # Initialize server manager
        from model_providers.server_manager import get_server_manager
        server_manager = get_server_manager()
        
        # Check if server exists
        if server_id not in server_manager.servers:
            return jsonify({
                'success': False,
                'error': f'Server {server_id} not found'
            })
        
        # Update server
        success = server_manager.add_server(server_id, data)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Server {server_id} updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to update server {server_id}'
            })
    except Exception as e:
        logger.error(f"Error updating server: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/local_models/servers/<server_id>', methods=['DELETE'])
@login_required
def remove_server(server_id):
    """Remove a server"""
    try:
        # Initialize server manager
        from model_providers.server_manager import get_server_manager
        server_manager = get_server_manager()
        
        # Remove server
        success = server_manager.remove_server(server_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Server {server_id} removed successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to remove server {server_id}'
            })
    except Exception as e:
        logger.error(f"Error removing server: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/local_models/rankings/<role>', methods=['GET'])
@login_required
def get_model_rankings(role):
    """Get model rankings for a specific role"""
    try:
        # Check if role is valid
        if role not in ['coding', 'orchestration']:
            return jsonify({
                'success': False,
                'error': f'Invalid role: {role}'
            })
        
        # Load config from file
        config_path = os.path.join('config', 'server_config.json')
        
        if not os.path.exists(config_path):
            return jsonify({
                'success': False,
                'error': 'Server configuration file not found'
            })
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Get rankings for the specified role
        rankings = config.get('model_rankings', {}).get(role, [])
        
        return jsonify({
            'success': True,
            'rankings': rankings
        })
    except Exception as e:
        logger.error(f"Error getting {role} rankings: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/local_models/rankings/<role>', methods=['POST'])
@login_required
def update_model_rankings(role):
    """Update model rankings for a specific role"""
    try:
        # Check if role is valid
        if role not in ['coding', 'orchestration']:
            return jsonify({
                'success': False,
                'error': f'Invalid role: {role}'
            })
        
        # Get request data
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            })
        
        rankings = data.get('rankings', [])
        if not rankings:
            return jsonify({
                'success': False,
                'error': 'No rankings provided'
            })
        
        # Load existing config
        config_path = os.path.join('config', 'server_config.json')
        
        if not os.path.exists(config_path):
            return jsonify({
                'success': False,
                'error': 'Server configuration file not found'
            })
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Update rankings
        if 'model_rankings' not in config:
            config['model_rankings'] = {}
        
        config['model_rankings'][role] = rankings
        
        # Save updated config
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        return jsonify({
            'success': True,
            'message': f'{role} rankings updated successfully'
        })
    except Exception as e:
        logger.error(f"Error updating {role} rankings: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/local_models/task_mappings', methods=['GET'])
@login_required
def get_task_mappings():
    """Get task-model mappings"""
    try:
        # Load config from file
        config_path = os.path.join('config', 'server_config.json')
        
        if not os.path.exists(config_path):
            return jsonify({
                'success': False,
                'error': 'Server configuration file not found'
            })
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Get task mappings
        mappings = config.get('task_model_matching', {})
        
        return jsonify({
            'success': True,
            'mappings': mappings
        })
    except Exception as e:
        logger.error(f"Error getting task mappings: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/local_models/task_mappings', methods=['POST'])
@login_required
def update_task_mappings():
    """Update task-model mappings"""
    try:
        # Get request data
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            })
        
        mappings = data.get('mappings', {})
        if not mappings:
            return jsonify({
                'success': False,
                'error': 'No mappings provided'
            })
        
        # Load existing config
        config_path = os.path.join('config', 'server_config.json')
        
        if not os.path.exists(config_path):
            return jsonify({
                'success': False,
                'error': 'Server configuration file not found'
            })
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Update mappings
        config['task_model_matching'] = mappings
        
        # Save updated config
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        return jsonify({
            'success': True,
            'message': 'Task mappings updated successfully'
        })
    except Exception as e:
        logger.error(f"Error updating task mappings: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/local_models/settings', methods=['GET'])
@login_required
def get_settings():
    """Get local model settings"""
    try:
        # Load config from file
        config_path = os.path.join('config', 'server_config.json')
        
        if not os.path.exists(config_path):
            return jsonify({
                'success': False,
                'error': 'Server configuration file not found'
            })
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Get settings
        settings = config.get('settings', {})
        
        return jsonify({
            'success': True,
            'settings': settings
        })
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/local_models/settings', methods=['POST'])
@login_required
def update_settings():
    """Update local model settings"""
    try:
        # Get request data
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            })
        
        # Load existing config
        config_path = os.path.join('config', 'server_config.json')
        
        if not os.path.exists(config_path):
            return jsonify({
                'success': False,
                'error': 'Server configuration file not found'
            })
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Update settings
        config['settings'] = data
        
        # Save updated config
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        return jsonify({
            'success': True,
            'message': 'Settings updated successfully'
        })
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000, debug=True)