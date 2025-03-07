"""
Agent Pool
Module for managing a pool of parallel script generation agents
"""

import os
import time
import json
import asyncio
import logging
import uuid
from typing import Dict, List, Any, Optional, Tuple, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

# Setup logging
logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Status of a task in the agent pool"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


@dataclass
class Task:
    """Represents a task in the agent pool"""
    id: str
    script_definition: Dict[str, Any]
    provider_name: str
    model_name: str
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    priority: int = 0
    dependencies: List[str] = field(default_factory=list)
    
    def start(self):
        """Mark the task as started"""
        self.started_at = time.time()
        self.status = TaskStatus.RUNNING
    
    def complete(self, result: Dict[str, Any]):
        """Mark the task as completed"""
        self.completed_at = time.time()
        self.status = TaskStatus.COMPLETED
        self.result = result
    
    def fail(self, error: str):
        """Mark the task as failed"""
        self.completed_at = time.time()
        self.status = TaskStatus.FAILED
        self.error = error
    
    def cancel(self):
        """Mark the task as canceled"""
        self.completed_at = time.time()
        self.status = TaskStatus.CANCELED
    
    @property
    def duration(self) -> Optional[float]:
        """Get the task duration in seconds"""
        if self.started_at is None:
            return None
        
        end_time = self.completed_at or time.time()
        return end_time - self.started_at
    
    @property
    def wait_time(self) -> float:
        """Get the task wait time in seconds"""
        start_time = self.started_at or time.time()
        return start_time - self.created_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for serialization"""
        return {
            "id": self.id,
            "script_name": self.script_definition.get("name", "unknown"),
            "provider_name": self.provider_name,
            "model_name": self.model_name,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "status": self.status.value,
            "error": self.error,
            "priority": self.priority,
            "dependencies": self.dependencies,
            "duration": self.duration,
            "wait_time": self.wait_time
        }


class AgentPool:
    """
    Manages a pool of script generation agents that can run in parallel,
    handling task queuing, priority, and provider rate limiting
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the agent pool
        
        Args:
            config: Configuration dictionary with pool settings
        """
        self.config = config or {}
        self.max_parallel = self.config.get("parallelism", {}).get("max_workers", 3)
        self.tasks: Dict[str, Task] = {}
        self.active_tasks: Set[str] = set()
        self.rate_limits: Dict[str, Dict[str, Any]] = self._initialize_rate_limits()
        self.provider_tokens: Dict[str, int] = {}
        self.event_handlers: Dict[str, List[Callable]] = {
            "task_created": [],
            "task_started": [],
            "task_completed": [],
            "task_failed": [],
            "task_canceled": []
        }
    
    def _initialize_rate_limits(self) -> Dict[str, Dict[str, Any]]:
        """Initialize rate limits for providers"""
        default_limits = {
            "claude": {
                "requests_per_minute": 10,
                "concurrent_requests": 5,
                "tokens_per_minute": 100000
            },
            "openai": {
                "requests_per_minute": 15,
                "concurrent_requests": 8,
                "tokens_per_minute": 150000
            },
            "deepseek": {
                "requests_per_minute": 5,
                "concurrent_requests": 3,
                "tokens_per_minute": 60000
            }
        }
        
        # Update with config values if available
        provider_limits = self.config.get("rate_limits", {})
        for provider, limits in provider_limits.items():
            if provider in default_limits:
                default_limits[provider].update(limits)
            else:
                default_limits[provider] = limits
        
        return default_limits
    
    def add_task(self, 
                script_definition: Dict[str, Any], 
                provider_name: str,
                model_name: str,
                dependencies: List[str] = None,
                priority: int = 0) -> str:
        """
        Add a new task to the pool
        
        Args:
            script_definition: Dictionary defining the script to generate
            provider_name: Name of the AI provider to use
            model_name: Name of the specific model to use
            dependencies: List of task IDs that must complete before this task
            priority: Task priority (higher is more important)
            
        Returns:
            Task ID string
        """
        task_id = str(uuid.uuid4())
        
        task = Task(
            id=task_id,
            script_definition=script_definition,
            provider_name=provider_name,
            model_name=model_name,
            priority=priority,
            dependencies=dependencies or []
        )
        
        self.tasks[task_id] = task
        
        # Trigger event
        self._trigger_event("task_created", task)
        
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Get a task by ID
        
        Args:
            task_id: Task ID
            
        Returns:
            Task or None if not found
        """
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """
        Get all tasks in the pool
        
        Returns:
            List of task dictionaries
        """
        return [task.to_dict() for task in self.tasks.values()]
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task
        
        Args:
            task_id: Task ID
            
        Returns:
            True if the task was canceled, False otherwise
        """
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            task.cancel()
            
            # Remove from active tasks if running
            if task_id in self.active_tasks:
                self.active_tasks.remove(task_id)
                
            # Trigger event
            self._trigger_event("task_canceled", task)
            
            return True
        
        return False
    
    def is_task_ready(self, task_id: str) -> bool:
        """
        Check if a task is ready to run
        
        Args:
            task_id: Task ID
            
        Returns:
            True if the task is ready to run
        """
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        # Check task status
        if task.status != TaskStatus.PENDING:
            return False
        
        # Check dependencies
        for dep_id in task.dependencies:
            dep_task = self.tasks.get(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        
        return True
    
    def get_next_task(self) -> Optional[Task]:
        """
        Get the next task to run based on readiness and priority
        
        Returns:
            Next task or None if no tasks are ready
        """
        ready_tasks = []
        
        for task_id, task in self.tasks.items():
            if task_id not in self.active_tasks and self.is_task_ready(task_id):
                ready_tasks.append(task)
        
        if not ready_tasks:
            return None
        
        # Sort by priority (high to low) and then by creation time (old to new)
        ready_tasks.sort(key=lambda t: (-t.priority, t.created_at))
        
        # Check rate limits
        for task in ready_tasks:
            provider = task.provider_name
            
            # Skip if provider rate limit is reached
            if not self._check_rate_limit(provider):
                continue
                
            return task
        
        return None
    
    def _check_rate_limit(self, provider: str) -> bool:
        """
        Check if a provider is rate-limited
        
        Args:
            provider: Provider name
            
        Returns:
            True if the provider is not rate-limited
        """
        limits = self.rate_limits.get(provider)
        if not limits:
            return True  # No limits defined
        
        # Check concurrent requests
        concurrent_limit = limits.get("concurrent_requests", float('inf'))
        current_concurrent = sum(1 for task in self.tasks.values()
                                if task.status == TaskStatus.RUNNING
                                and task.provider_name == provider)
        
        if current_concurrent >= concurrent_limit:
            return False
        
        # Other limits could be implemented here
        
        return True
    
    def _update_token_usage(self, provider: str, tokens: int) -> None:
        """
        Update token usage for a provider
        
        Args:
            provider: Provider name
            tokens: Number of tokens used
        """
        self.provider_tokens[provider] = self.provider_tokens.get(provider, 0) + tokens
    
    def register_event_handler(self, event_type: str, handler: Callable) -> None:
        """
        Register an event handler
        
        Args:
            event_type: Event type name
            handler: Callback function
        """
        if event_type in self.event_handlers:
            self.event_handlers[event_type].append(handler)
    
    def _trigger_event(self, event_type: str, task: Task) -> None:
        """
        Trigger an event
        
        Args:
            event_type: Event type name
            task: Task that triggered the event
        """
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    handler(task)
                except Exception as e:
                    logger.error(f"Error in event handler: {e}")
    
    async def process_tasks(self, 
                           task_processor: Callable[[Task], Any], 
                           limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Process tasks in the pool
        
        Args:
            task_processor: Function to process a task
            limit: Maximum number of tasks to process (None for all)
            
        Returns:
            Dictionary with processing results
        """
        processed_count = 0
        success_count = 0
        failure_count = 0
        
        active_tasks = set()
        tasks_futures = {}
        
        # Process tasks until limit is reached or all tasks are processed
        while limit is None or processed_count < limit:
            # Check if we can start more tasks
            while len(active_tasks) < self.max_parallel:
                next_task = self.get_next_task()
                if not next_task:
                    break  # No more tasks to process
                
                # Mark task as running
                next_task.start()
                self.active_tasks.add(next_task.id)
                active_tasks.add(next_task.id)
                
                # Trigger event
                self._trigger_event("task_started", next_task)
                
                # Create task future
                future = asyncio.create_task(self._process_task(next_task, task_processor))
                tasks_futures[next_task.id] = future
                
                processed_count += 1
                
                # Check if we've reached the limit
                if limit is not None and processed_count >= limit:
                    break
            
            if not active_tasks:
                break  # No active tasks, we're done
            
            # Wait for any task to complete
            done, pending = await asyncio.wait(
                [tasks_futures[task_id] for task_id in active_tasks],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Process completed tasks
            for future in done:
                try:
                    completed_task_id, success = future.result()
                    
                    # Remove task from active sets
                    active_tasks.remove(completed_task_id)
                    self.active_tasks.remove(completed_task_id)
                    
                    # Update counts
                    if success:
                        success_count += 1
                    else:
                        failure_count += 1
                    
                    # Remove from futures
                    del tasks_futures[completed_task_id]
                    
                except Exception as e:
                    logger.error(f"Error processing task result: {e}")
        
        # Wait for remaining active tasks if any
        if active_tasks:
            remaining_futures = [tasks_futures[task_id] for task_id in active_tasks]
            done, _ = await asyncio.wait(remaining_futures)
            
            for future in done:
                try:
                    completed_task_id, success = future.result()
                    
                    # Update counts
                    if success:
                        success_count += 1
                    else:
                        failure_count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing task result: {e}")
        
        return {
            "processed_count": processed_count,
            "success_count": success_count,
            "failure_count": failure_count,
            "pending_count": sum(1 for task in self.tasks.values() if task.status == TaskStatus.PENDING)
        }
    
    async def _process_task(self, task: Task, processor: Callable[[Task], Any]) -> Tuple[str, bool]:
        """
        Process a single task
        
        Args:
            task: Task to process
            processor: Function to process the task
            
        Returns:
            Tuple of (task_id, success)
        """
        try:
            # Process the task
            result = await processor(task)
            
            # Mark task as completed
            task.complete(result)
            
            # Update token usage if provided
            if isinstance(result, dict) and "token_usage" in result:
                tokens = result["token_usage"].get("total_tokens", 0)
                self._update_token_usage(task.provider_name, tokens)
            
            # Trigger event
            self._trigger_event("task_completed", task)
            
            return task.id, True
            
        except Exception as e:
            # Mark task as failed
            error_msg = str(e)
            task.fail(error_msg)
            
            # Trigger event
            self._trigger_event("task_failed", task)
            
            logger.error(f"Task {task.id} failed: {error_msg}")
            return task.id, False
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the agent pool
        
        Returns:
            Dictionary with pool statistics
        """
        tasks_by_status = {
            status.value: sum(1 for task in self.tasks.values() if task.status == status)
            for status in TaskStatus
        }
        
        tasks_by_provider = {}
        for task in self.tasks.values():
            provider = task.provider_name
            if provider not in tasks_by_provider:
                tasks_by_provider[provider] = {
                    "total": 0,
                    "active": 0,
                    "completed": 0,
                    "failed": 0
                }
            
            tasks_by_provider[provider]["total"] += 1
            
            if task.status == TaskStatus.RUNNING:
                tasks_by_provider[provider]["active"] += 1
            elif task.status == TaskStatus.COMPLETED:
                tasks_by_provider[provider]["completed"] += 1
            elif task.status == TaskStatus.FAILED:
                tasks_by_provider[provider]["failed"] += 1
        
        # Calculate average durations
        completed_tasks = [task for task in self.tasks.values() 
                          if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]]
        
        avg_duration = 0
        avg_wait_time = 0
        
        if completed_tasks:
            durations = [task.duration for task in completed_tasks if task.duration is not None]
            wait_times = [task.wait_time for task in completed_tasks]
            
            if durations:
                avg_duration = sum(durations) / len(durations)
            
            if wait_times:
                avg_wait_time = sum(wait_times) / len(wait_times)
        
        return {
            "total_tasks": len(self.tasks),
            "active_tasks": len(self.active_tasks),
            "tasks_by_status": tasks_by_status,
            "tasks_by_provider": tasks_by_provider,
            "avg_duration": avg_duration,
            "avg_wait_time": avg_wait_time,
            "max_parallel": self.max_parallel,
            "provider_tokens": self.provider_tokens
        }


# Simple test for the agent pool
if __name__ == "__main__":
    import random
    
    # Define a mock task processor
    async def mock_processor(task: Task) -> Dict[str, Any]:
        # Simulate processing time
        delay = random.uniform(0.5, 2.0)
        await asyncio.sleep(delay)
        
        # 90% success rate
        if random.random() < 0.9:
            return {
                "script": f"# Generated script for {task.script_definition.get('name', 'unknown')}",
                "token_usage": {
                    "total_tokens": random.randint(1000, 5000)
                }
            }
        else:
            raise Exception("Random task failure")
    
    # Create a pool
    pool = AgentPool({"parallelism": {"max_workers": 3}})
    
    # Add event handlers
    pool.register_event_handler("task_completed", lambda task: print(f"Task completed: {task.id}"))
    pool.register_event_handler("task_failed", lambda task: print(f"Task failed: {task.id} - {task.error}"))
    
    # Add some tasks
    for i in range(10):
        task_id = pool.add_task(
            script_definition={"name": f"script_{i}.py", "description": f"Test script {i}"},
            provider_name=random.choice(["claude", "openai", "deepseek"]),
            model_name=f"model_{i}",
            priority=random.randint(0, 5)
        )
        print(f"Added task: {task_id}")
    
    # Process tasks
    async def run_test():
        results = await pool.process_tasks(mock_processor)
        print(f"Results: {results}")
        
        stats = pool.get_pool_stats()
        print(f"Pool stats: {json.dumps(stats, indent=2)}")
    
    asyncio.run(run_test())
