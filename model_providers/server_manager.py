"""
Server Manager
Module for managing connections to multiple local model servers
"""

import os
import json
import asyncio
import aiohttp
import logging
import random
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta

# Set up logging
logger = logging.getLogger(__name__)

class ServerManager:
    """
    Manages connections and load balancing for multiple Ollama servers
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the server manager
        
        Args:
            config_path: Path to the server configuration file
        """
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config",
            "server_config.json"
        )
        
        self.servers = {}
        self.server_status = {}
        self.model_availability = {}
        self.active_tasks = {}
        self.last_check = {}
        
        # Load server configuration
        self._load_config()
        
        # Periodically check server status
        asyncio.create_task(self._periodic_status_check())
    
    def _load_config(self) -> None:
        """Load server configuration from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    
                    self.servers = config.get('servers', {})
                    logger.info(f"Loaded configuration for {len(self.servers)} servers")
            else:
                logger.warning(f"Server configuration file not found: {self.config_path}")
                self._create_default_config()
        except Exception as e:
            logger.error(f"Error loading server configuration: {e}")
            self._create_default_config()
    
    def _create_default_config(self) -> None:
        """Create a default server configuration"""
        self.servers = {
            "server1": {
                "name": "Server 1",
                "url": "http://localhost:11434",
                "max_concurrent_tasks": 3,
                "models": ["codellama:34b", "llama2:13b", "wizardcoder:15b"]
            }
        }
        
        # Save the default configuration
        self._save_config()
    
    def _save_config(self) -> None:
        """Save server configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump({
                    'servers': self.servers
                }, f, indent=2)
                
            logger.info(f"Saved server configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving server configuration: {e}")
    
    async def _check_server_status(self, server_id: str) -> Dict[str, Any]:
        """
        Check the status of a server and its available models
        
        Args:
            server_id: ID of the server to check
            
        Returns:
            Dictionary with server status information
        """
        server_info = self.servers.get(server_id)
        if not server_info:
            return {
                "server_id": server_id,
                "status": "unknown",
                "error": "Server not found in configuration"
            }
        
        server_url = server_info.get("url")
        if not server_url:
            return {
                "server_id": server_id,
                "status": "error",
                "error": "Server URL not configured"
            }
        
        try:
            async with aiohttp.ClientSession() as session:
                # Add a timeout to avoid waiting too long
                async with session.get(f"{server_url}/api/tags", timeout=5) as response:
                    if response.status != 200:
                        return {
                            "server_id": server_id,
                            "status": "error",
                            "error": f"Server returned status {response.status}"
                        }
                    
                    result = await response.json()
                    available_models = [model.get("name") for model in result.get("models", [])]
                    
                    # Update model availability
                    for model in available_models:
                        if model not in self.model_availability:
                            self.model_availability[model] = []
                        
                        if server_id not in self.model_availability[model]:
                            self.model_availability[model].append(server_id)
                    
                    # Update server status
                    status = {
                        "server_id": server_id,
                        "status": "online",
                        "available_models": available_models,
                        "active_tasks": self.active_tasks.get(server_id, 0),
                        "max_tasks": server_info.get("max_concurrent_tasks", 3),
                        "last_checked": datetime.now().isoformat()
                    }
                    
                    self.server_status[server_id] = status
                    self.last_check[server_id] = datetime.now()
                    
                    return status
        
        except asyncio.TimeoutError:
            status = {
                "server_id": server_id,
                "status": "timeout",
                "error": "Connection timed out"
            }
            self.server_status[server_id] = status
            return status
            
        except Exception as e:
            status = {
                "server_id": server_id,
                "status": "error",
                "error": str(e)
            }
            self.server_status[server_id] = status
            return status
    
    async def _periodic_status_check(self) -> None:
        """Periodically check status of all servers"""
        while True:
            try:
                for server_id in self.servers:
                    # Check if it's been more than 5 minutes since last check
                    last_check_time = self.last_check.get(server_id)
                    if not last_check_time or (datetime.now() - last_check_time) > timedelta(minutes=5):
                        await self._check_server_status(server_id)
                
                # Sleep for a minute before checking again
                await asyncio.sleep(60)
            
            except Exception as e:
                logger.error(f"Error in periodic status check: {e}")
                await asyncio.sleep(60)  # Still sleep on error
    
    async def check_all_servers(self) -> Dict[str, Dict[str, Any]]:
        """
        Check status of all configured servers
        
        Returns:
            Dictionary mapping server IDs to their status information
        """
        tasks = []
        for server_id in self.servers:
            tasks.append(self._check_server_status(server_id))
        
        results = await asyncio.gather(*tasks)
        
        # Convert to dictionary with server IDs as keys
        return {result["server_id"]: result for result in results}
    
    async def find_server_for_model(self, model_name: str) -> Optional[str]:
        """
        Find the best server to run a specific model based on current load
        
        Args:
            model_name: Name of the model to run
            
        Returns:
            Server ID of the best server, or None if no suitable server found
        """
        # Check if we need to refresh server status
        need_refresh = False
        for server_id in self.servers:
            last_check_time = self.last_check.get(server_id)
            if not last_check_time or (datetime.now() - last_check_time) > timedelta(minutes=5):
                need_refresh = True
                break
        
        if need_refresh:
            await self.check_all_servers()
        
        # Get list of servers that have this model available
        available_servers = self.model_availability.get(model_name, [])
        
        if not available_servers:
            logger.warning(f"No servers found with model {model_name}")
            return None
        
        # Filter servers that are online and not at capacity
        eligible_servers = []
        for server_id in available_servers:
            server_status = self.server_status.get(server_id, {})
            if server_status.get("status") == "online":
                active_tasks = self.active_tasks.get(server_id, 0)
                max_tasks = self.servers.get(server_id, {}).get("max_concurrent_tasks", 3)
                
                if active_tasks < max_tasks:
                    eligible_servers.append((server_id, active_tasks))
        
        if not eligible_servers:
            logger.warning(f"No eligible servers found for model {model_name} (all at capacity or offline)")
            return None
        
        # Sort by number of active tasks (ascending)
        eligible_servers.sort(key=lambda x: x[1])
        
        # Return the server with the fewest active tasks
        return eligible_servers[0][0]
    
    def register_task(self, server_id: str, task_id: str) -> bool:
        """
        Register an active task on a server
        
        Args:
            server_id: ID of the server
            task_id: ID of the task
            
        Returns:
            True if registration was successful, False otherwise
        """
        if server_id not in self.servers:
            logger.warning(f"Attempted to register task on unknown server: {server_id}")
            return False
        
        # Update active tasks count
        self.active_tasks.setdefault(server_id, 0)
        self.active_tasks[server_id] += 1
        
        logger.info(f"Registered task {task_id} on server {server_id} (active tasks: {self.active_tasks[server_id]})")
        return True
    
    def unregister_task(self, server_id: str, task_id: str) -> bool:
        """
        Unregister an active task from a server
        
        Args:
            server_id: ID of the server
            task_id: ID of the task
            
        Returns:
            True if unregistration was successful, False otherwise
        """
        if server_id not in self.servers:
            logger.warning(f"Attempted to unregister task from unknown server: {server_id}")
            return False
        
        # Update active tasks count
        self.active_tasks.setdefault(server_id, 0)
        if self.active_tasks[server_id] > 0:
            self.active_tasks[server_id] -= 1
        
        logger.info(f"Unregistered task {task_id} from server {server_id} (active tasks: {self.active_tasks[server_id]})")
        return True
    
    def add_server(self, server_id: str, server_info: Dict[str, Any]) -> bool:
        """
        Add or update a server configuration
        
        Args:
            server_id: ID of the server
            server_info: Dictionary with server information
            
        Returns:
            True if the server was added/updated successfully
        """
        # Validate required fields
        if "url" not in server_info:
            logger.error("Server URL is required")
            return False
        
        # Add default values if missing
        if "name" not in server_info:
            server_info["name"] = f"Server {len(self.servers) + 1}"
        
        if "max_concurrent_tasks" not in server_info:
            server_info["max_concurrent_tasks"] = 3
        
        if "models" not in server_info:
            server_info["models"] = []
        
        # Update server configuration
        self.servers[server_id] = server_info
        
        # Save the updated configuration
        self._save_config()
        
        # Trigger a status check for the new server
        asyncio.create_task(self._check_server_status(server_id))
        
        return True
    
    def remove_server(self, server_id: str) -> bool:
        """
        Remove a server configuration
        
        Args:
            server_id: ID of the server to remove
            
        Returns:
            True if the server was removed successfully
        """
        if server_id not in self.servers:
            logger.warning(f"Attempted to remove unknown server: {server_id}")
            return False
        
        # Remove from servers dict
        del self.servers[server_id]
        
        # Remove from status tracking
        if server_id in self.server_status:
            del self.server_status[server_id]
        
        if server_id in self.active_tasks:
            del self.active_tasks[server_id]
        
        if server_id in self.last_check:
            del self.last_check[server_id]
        
        # Remove from model availability
        for model, servers in list(self.model_availability.items()):
            if server_id in servers:
                servers.remove(server_id)
            
            # If no servers left for this model, remove the model
            if not servers:
                del self.model_availability[model]
        
        # Save the updated configuration
        self._save_config()
        
        return True
    
    def get_server_info(self, server_id: str) -> Dict[str, Any]:
        """
        Get information about a server
        
        Args:
            server_id: ID of the server
            
        Returns:
            Dictionary with server information
        """
        server_info = self.servers.get(server_id, {})
        server_status = self.server_status.get(server_id, {})
        
        return {
            "server_id": server_id,
            "info": server_info,
            "status": server_status
        }
    
    def get_all_servers(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all servers
        
        Returns:
            Dictionary mapping server IDs to their information
        """
        result = {}
        for server_id in self.servers:
            result[server_id] = self.get_server_info(server_id)
        
        return result
    
    def get_model_servers(self, model_name: str) -> List[str]:
        """
        Get list of servers that have a specific model available
        
        Args:
            model_name: Name of the model
            
        Returns:
            List of server IDs
        """
        return self.model_availability.get(model_name, [])
    
    def get_all_available_models(self) -> Dict[str, List[str]]:
        """
        Get mapping of all available models to the servers they're on
        
        Returns:
            Dictionary mapping model names to lists of server IDs
        """
        return self.model_availability
