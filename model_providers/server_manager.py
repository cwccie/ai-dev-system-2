"""
Server Manager Module for Local Models Management
This module manages server configurations for local model providers
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class ServerManager:
    """
    Manages server configurations for local model providers.
    Handles adding, updating, and removing server configurations.
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the server manager with an optional config path.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path or os.path.join('config', 'server_config.json')
        self.servers: Dict[str, Dict[str, Any]] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load server configurations from the config file"""
        if not os.path.exists(self.config_path):
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # Create initial config
            initial_config = {
                'servers': {},
                'model_rankings': {
                    'coding': [],
                    'orchestration': []
                },
                'task_model_matching': {},
                'settings': {
                    'default_provider': 'ollama',
                    'auto_refresh': True,
                    'refresh_interval': 300
                }
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(initial_config, f, indent=2)
            
            self.servers = {}
        else:
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                self.servers = config.get('servers', {})
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading server config: {e}")
                self.servers = {}
    
    def _save_config(self) -> bool:
        """
        Save server configurations to the config file
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load current config to preserve other settings
            current_config = {}
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    current_config = json.load(f)
            
            # Update servers section
            current_config['servers'] = self.servers
            
            # Save the updated config
            with open(self.config_path, 'w') as f:
                json.dump(current_config, f, indent=2)
            
            return True
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Error saving server config: {e}")
            return False
    
    def get_all_servers(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all configured servers
        
        Returns:
            dict: Dictionary of server configurations
        """
        return self.servers
    
    def get_server(self, server_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific server configuration
        
        Args:
            server_id: ID of the server to retrieve
            
        Returns:
            dict: Server configuration or None if not found
        """
        return self.servers.get(server_id)
    
    def add_server(self, server_id: str, config: Dict[str, Any]) -> bool:
        """
        Add or update a server configuration
        
        Args:
            server_id: ID of the server
            config: Server configuration
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate required fields
            required_fields = ['name', 'url', 'type']
            for field in required_fields:
                if field not in config:
                    logger.error(f"Missing required field: {field}")
                    return False
            
            # Add or update server
            self.servers[server_id] = config
            
            # Save config
            return self._save_config()
        except Exception as e:
            logger.error(f"Error adding server: {e}")
            return False
    
    def remove_server(self, server_id: str) -> bool:
        """
        Remove a server configuration
        
        Args:
            server_id: ID of the server to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        if server_id not in self.servers:
            logger.error(f"Server not found: {server_id}")
            return False
        
        try:
            # Remove server
            del self.servers[server_id]
            
            # Save config
            return self._save_config()
        except Exception as e:
            logger.error(f"Error removing server: {e}")
            return False
    
    def test_connection(self, server_id: str) -> Dict[str, Any]:
        """
        Test connection to a server
        
        Args:
            server_id: ID of the server to test
            
        Returns:
            dict: Test result
        """
        server = self.get_server(server_id)
        if not server:
            return {'success': False, 'error': f'Server not found: {server_id}'}
        
        try:
            # TODO: Implement actual connection test based on server type
            return {
                'success': True,
                'message': f'Successfully connected to {server["name"]}',
                'details': {
                    'latency': 42,  # Mock latency in ms
                    'version': '1.0.0',  # Mock version
                    'status': 'running'
                }
            }
        except Exception as e:
            logger.error(f"Error testing connection: {e}")
            return {'success': False, 'error': str(e)}

# Helper function to get server manager instance
_server_manager_instance = None

def get_server_manager(config_path: str = None) -> ServerManager:
    """
    Get a singleton instance of the server manager
    
    Args:
        config_path: Optional path to the configuration file
        
    Returns:
        ServerManager: Instance of the server manager
    """
    global _server_manager_instance
    
    if _server_manager_instance is None:
        _server_manager_instance = ServerManager(config_path)
    
    return _server_manager_instance