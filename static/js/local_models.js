/**
 * local_models.js
 * Script for managing local model servers via the web interface
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize page
    loadServerStatus();
    loadModelData();
    setupEventListeners();
    initializeSortableLists();
    loadSettings();
});

/**
 * Load server status information
 */
function loadServerStatus() {
    const container = document.getElementById('server-status-container');
    if (!container) return;
    
    fetch('/api/local_models/servers')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayServerStatus(data.servers);
            } else {
                container.innerHTML = `
                    <div class="alert alert-warning">
                        Failed to load server status: ${data.error || 'Unknown error'}
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            container.innerHTML = `
                <div class="alert alert-danger">
                    Error loading server status. Please try again.
                </div>
            `;
        });
}

/**
 * Display server status information
 */
function displayServerStatus(servers) {
    const container = document.getElementById('server-status-container');
    if (!container) return;
    
    if (!servers || Object.keys(servers).length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                No servers configured. Add a server to get started.
            </div>
        `;
        return;
    }
    
    let html = `
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>Server</th>
                        <th>Status</th>
                        <th>Models</th>
                        <th>Activity</th>
                        <th>Last Checked</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    for (const [serverId, serverData] of Object.entries(servers)) {
        const info = serverData.info || {};
        const status = serverData.status || {};
        
        // Determine status display
        let statusBadge;
        if (status.status === 'online') {
            statusBadge = '<span class="badge bg-success">Online</span>';
        } else if (status.status === 'timeout') {
            statusBadge = '<span class="badge bg-warning text-dark">Timeout</span>';
        } else if (status.status === 'error') {
            statusBadge = '<span class="badge bg-danger">Error</span>';
        } else {
            statusBadge = '<span class="badge bg-secondary">Unknown</span>';
        }
        
        // Format models
        const availableModels = status.available_models || [];
        const modelsList = availableModels.length > 0 
            ? availableModels.join(', ')
            : 'No models detected';
        
        // Format activity
        const activeTasks = status.active_tasks || 0;
        const maxTasks = status.max_tasks || info.max_concurrent_tasks || 3;
        
        // Format last checked time
        const lastChecked = status.last_checked 
            ? new Date(status.last_checked).toLocaleString()
            : 'Never';
        
        html += `
            <tr>
                <td>
                    <strong>${info.name || serverId}</strong>
                    <div class="small text-muted">${info.url || 'No URL'}</div>
                    ${info.gpu ? `<div class="small">GPU: ${info.gpu}</div>` : ''}
                </td>
                <td>${statusBadge}</td>
                <td>
                    <div class="small">${modelsList}</div>
                </td>
                <td>
                    <div class="d-flex align-items-center">
                        <span class="me-2">${activeTasks}/${maxTasks}</span>
                        <div class="progress flex-grow-1" style="height: 6px;">
                            <div class="progress-bar" role="progressbar" style="width: ${(activeTasks / maxTasks) * 100}%"></div>
                        </div>
                    </div>
                </td>
                <td>${lastChecked}</td>
            </tr>
        `;
    }
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = html;
}

/**
 * Load model data for all tabs
 */
function loadModelData() {
    // Load models for each tab
    loadModelsForRole('coding');
    loadModelsForRole('orchestration');
    loadAllLocalModels();
    
    // Load rankings for configuration
    loadModelRankings('coding');
    loadModelRankings('orchestration');
    
    // Load task mappings
    loadTaskModelMappings();
    
    // Load server management interface
    loadServerManagementInterface();
}

/**
 * Load models for a specific role (coding or orchestration)
 */
function loadModelsForRole(role) {
    const container = document.getElementById(`${role}-models-container`);
    if (!container) return;
    
    fetch(`/api/local_models/models/${role}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayRoleModels(container, data.models, role);
            } else {
                container.innerHTML = `
                    <div class="alert alert-warning">
                        Failed to load ${role} models: ${data.error || 'Unknown error'}
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            container.innerHTML = `
                <div class="alert alert-danger">
                    Error loading ${role} models. Please try again.
                </div>
            `;
        });
}

/**
 * Display models for a specific role
 */
function displayRoleModels(container, models, role) {
    if (!models || models.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                No ${role} models available. Please check your server configuration.
            </div>
        `;
        return;
    }
    
    let html = `
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Model</th>
                        <th>Size</th>
                        <th>Server</th>
                        <th>Strengths</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    for (const model of models) {
        // Determine status badge
        let statusBadge;
        if (model.available) {
            statusBadge = '<span class="badge bg-success">Available</span>';
        } else {
            statusBadge = '<span class="badge bg-warning text-dark">Unavailable</span>';
        }
        
        // Format strengths
        const strengths = model.strengths || [];
        const strengthsText = strengths.join(', ');
        
        html += `
            <tr>
                <td>${model.rank || '-'}</td>
                <td>
                    <strong>${model.name}</strong>
                </td>
                <td>${model.parameter_count || '-'}</td>
                <td>${model.server_name || model.server_id || '-'}</td>
                <td>
                    <div class="small">${strengthsText || 'No strengths listed'}</div>
                </td>
                <td>${statusBadge}</td>
            </tr>
        `;
    }
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = html;
}

/**
 * Load all local models
 */
function loadAllLocalModels() {
    const container = document.getElementById('all-models-container');
    if (!container) return;
    
    fetch('/api/local_models/models/all')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayAllModels(container, data.models);
            } else {
                container.innerHTML = `
                    <div class="alert alert-warning">
                        Failed to load models: ${data.error || 'Unknown error'}
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            container.innerHTML = `
                <div class="alert alert-danger">
                    Error loading models. Please try again.
                </div>
            `;
        });
}

/**
 * Display all local models
 */
function displayAllModels(container, models) {
    if (!models || models.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                No local models detected. Please check your server configuration.
            </div>
        `;
        return;
    }
    
    let html = `
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>Model</th>
                        <th>Role</th>
                        <th>Servers</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    for (const model of models) {
        // Determine model role
        const role = model.role || 'unknown';
        const roleBadge = role === 'coding' 
            ? '<span class="badge bg-info">Coding</span>'
            : role === 'orchestration'
                ? '<span class="badge bg-primary">Orchestration</span>'
                : '<span class="badge bg-secondary">Unknown</span>';
        
        // Get servers
        const servers = model.servers || [];
        const serverNames = model.server_names || [];
        
        // Servers display
        let serversDisplay = '';
        if (servers.length > 0) {
            serversDisplay = serverNames.length > 0
                ? serverNames.join(', ')
                : servers.join(', ');
        } else {
            serversDisplay = 'No servers';
        }
        
        // Determine status badge
        let statusBadge;
        if (model.available) {
            statusBadge = '<span class="badge bg-success">Available</span>';
        } else {
            statusBadge = '<span class="badge bg-warning text-dark">Unavailable</span>';
        }
        
        html += `
            <tr>
                <td>
                    <strong>${model.name}</strong>
                    <div class="small text-muted">${model.parameter_count || ''}</div>
                </td>
                <td>${roleBadge}</td>
                <td>
                    <div class="small">${serversDisplay}</div>
                </td>
                <td>${statusBadge}</td>
            </tr>
        `;
    }
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = html;
}

/**
 * Load model rankings for configuration
 */
function loadModelRankings(role) {
    const container = document.getElementById(`${role}-ranking-container`);
    if (!container) return;
    
    fetch(`/api/local_models/rankings/${role}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayModelRankings(container, data.rankings, role);
            } else {
                container.innerHTML = `
                    <div class="alert alert-warning">
                        Failed to load ${role} rankings: ${data.error || 'Unknown error'}
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            container.innerHTML = `
                <div class="alert alert-danger">
                    Error loading ${role} rankings. Please try again.
                </div>
            `;
        });
}

/**
 * Display model rankings for drag-and-drop configuration
 */
function displayModelRankings(container, rankings, role) {
    if (!rankings || rankings.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                No ${role} models available for ranking. Please check your server configuration.
            </div>
        `;
        return;
    }
    
    let html = `<ul class="list-group" id="${role}-ranking-list" data-role="${role}">`;
    
    for (const model of rankings) {
        html += `
            <li class="list-group-item" data-model-id="${model.model}">
                <div class="d-flex justify-content-between align-items-center">
                    <div class="d-flex align-items-center">
                        <div class="drag-handle me-3">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-grip-vertical" viewBox="0 0 16 16">
                                <path d="M7 2a1 1 0 1 1-2 0 1 1 0 0 1 2 0zm3 0a1 1 0 1 1-2 0 1 1 0 0 1 2 0zM7 5a1 1 0 1 1-2 0 1 1 0 0 1 2 0zm3 0a1 1 0 1 1-2 0 1 1 0 0 1 2 0zM7 8a1 1 0 1 1-2 0 1 1 0 0 1 2 0zm3 0a1 1 0 1 1-2 0 1 1 0 0 1 2 0zm-3 3a1 1 0 1 1-2 0 1 1 0 0 1 2 0zm3 0a1 1 0 1 1-2 0 1 1 0 0 1 2 0zm-3 3a1 1 0 1 1-2 0 1 1 0 0 1 2 0zm3 0a1 1 0 1 1-2 0 1 1 0 0 1 2 0z"/>
                            </svg>
                        </div>
                        <div>
                            <strong>${model.model}</strong>
                            <div class="small text-muted">${model.parameter_count || ''}</div>
                        </div>
                    </div>
                    <span class="badge bg-primary">Rank ${model.rank}</span>
                </div>
            </li>
        `;
    }
    
    html += `</ul>`;
    
    container.innerHTML = html;
    
    // Initialize sortable for the new list
    const listElement = document.getElementById(`${role}-ranking-list`);
    if (listElement) {
        Sortable.create(listElement, {
            animation: 150,
            handle: '.drag-handle',
            onEnd: function(evt) {
                updateRankNumbers(listElement);
            }
        });
    }
}

/**
 * Update rank numbers after drag-and-drop
 */
function updateRankNumbers(listElement) {
    const items = listElement.querySelectorAll('li');
    items.forEach((item, index) => {
        const badge = item.querySelector('.badge');
        if (badge) {
            badge.textContent = `Rank ${index + 1}`;
        }
    });
}

/**
 * Load task-model mappings
 */
function loadTaskModelMappings() {
    const container = document.getElementById('task-mapping-container');
    if (!container) return;
    
    fetch('/api/local_models/task_mappings')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayTaskModelMappings(container, data.mappings);
            } else {
                container.innerHTML = `
                    <div class="alert alert-warning">
                        Failed to load task mappings: ${data.error || 'Unknown error'}
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            container.innerHTML = `
                <div class="alert alert-danger">
                    Error loading task mappings. Please try again.
                </div>
            `;
        });
}

/**
 * Display task-model mappings
 */
function displayTaskModelMappings(container, mappings) {
    if (!mappings || Object.keys(mappings).length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                No task mappings available. Please check your server configuration.
            </div>
        `;
        return;
    }
    
    let html = '';
    
    for (const [taskType, mapping] of Object.entries(mappings)) {
        const primaryRole = mapping.primary_role || '';
        const complexityMapping = mapping.complexity_mapping || {};
        
        html += `
            <div class="card mb-3">
                <div class="card-header">
                    <h5 class="mb-0">${formatTaskTypeName(taskType)}</h5>
                </div>
                <div class="card-body">
                    <div class="mb-3">
                        <label class="form-label">Primary Role</label>
                        <select class="form-select task-role-select" data-task-type="${taskType}">
                            <option value="coding" ${primaryRole === 'coding' ? 'selected' : ''}>Coding</option>
                            <option value="orchestration" ${primaryRole === 'orchestration' ? 'selected' : ''}>Orchestration</option>
                        </select>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">High Complexity Models</label>
                        <select class="form-select task-models-select" data-task-type="${taskType}" data-complexity="high" multiple>
                            ${generateModelOptions(complexityMapping.high || [])}
                        </select>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">Medium Complexity Models</label>
                        <select class="form-select task-models-select" data-task-type="${taskType}" data-complexity="medium" multiple>
                            ${generateModelOptions(complexityMapping.medium || [])}
                        </select>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">Low Complexity Models</label>
                        <select class="form-select task-models-select" data-task-type="${taskType}" data-complexity="low" multiple>
                            ${generateModelOptions(complexityMapping.low || [])}
                        </select>
                    </div>
                </div>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

/**
 * Format task type name for display
 */
function formatTaskTypeName(taskType) {
    return taskType
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

/**
 * Generate options for model select elements
 */
function generateModelOptions(selectedModels) {
    // This would typically come from a complete list of available models
    // For now, we just use the selected models
    return selectedModels.map(model => `<option value="${model}" selected>${model}</option>`).join('');
}

/**
 * Load server management interface
 */
function loadServerManagementInterface() {
    const container = document.getElementById('manage-servers-container');
    if (!container) return;
    
    fetch('/api/local_models/servers')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayServerManagement(container, data.servers);
            } else {
                container.innerHTML = `
                    <div class="alert alert-warning">
                        Failed to load server information: ${data.error || 'Unknown error'}
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            container.innerHTML = `
                <div class="alert alert-danger">
                    Error loading server information. Please try again.
                </div>
            `;
        });
}

/**
 * Display server management interface
 */
function displayServerManagement(container, servers) {
    if (!servers || Object.keys(servers).length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                No servers configured. Add a server to get started.
            </div>
        `;
        return;
    }
    
    let html = '';
    
    for (const [serverId, serverData] of Object.entries(servers)) {
        const info = serverData.info || {};
        const status = serverData.status || {};
        
        html += `
            <div class="card mb-3">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h5 class="mb-0">${info.name || serverId}</h5>
                    <button class="btn btn-sm btn-outline-danger remove-server-btn" data-server-id="${serverId}">Remove</button>
                </div>
                <div class="card-body">
                    <form class="update-server-form" data-server-id="${serverId}">
                        <div class="mb-3">
                            <label class="form-label">Server Name</label>
                            <input type="text" class="form-control" name="server_name" value="${info.name || ''}" required>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Server URL</label>
                            <input type="url" class="form-control" name="server_url" value="${info.url || ''}" required>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Max Concurrent Tasks</label>
                            <input type="number" class="form-control" name="max_tasks" value="${info.max_concurrent_tasks || 3}" min="1" max="10" required>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">GPU Model</label>
                            <input type="text" class="form-control" name="server_gpu" value="${info.gpu || ''}">
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Priority</label>
                            <select class="form-select" name="server_priority">
                                <option value="1" ${info.priority === 1 ? 'selected' : ''}>1 - High</option>
                                <option value="2" ${info.priority === 2 ? 'selected' : ''}>2 - Medium</option>
                                <option value="3" ${info.priority === 3 ? 'selected' : ''}>3 - Low</option>
                            </select>
                        </div>
                        
                        <button type="submit" class="btn btn-primary">Update Server</button>
                    </form>
                </div>
            </div>
        `;
    }
    
    container.innerHTML = html;
    
    // Add event listeners for server update forms
    const updateForms = container.querySelectorAll('.update-server-form');
    updateForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            updateServerConfig(form);
        });
    });
    
    // Add event listeners for server removal buttons
    const removeButtons = container.querySelectorAll('.remove-server-btn');
    removeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const serverId = this.getAttribute('data-server-id');
            if (confirm(`Are you sure you want to remove server ${serverId}?`)) {
                removeServer(serverId);
            }
        });
    });
}

/**
 * Update server configuration
 */
function updateServerConfig(form) {
    const serverId = form.getAttribute('data-server-id');
    const formData = new FormData(form);
    
    // Convert form data to JSON object
    const serverConfig = {
        name: formData.get('server_name'),
        url: formData.get('server_url'),
        max_concurrent_tasks: parseInt(formData.get('max_tasks')),
        gpu: formData.get('server_gpu'),
        priority: parseInt(formData.get('server_priority'))
    };
    
    fetch(`/api/local_models/servers/${serverId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(serverConfig)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show success message
            alert('Server configuration updated successfully.');
            
            // Reload server data
            loadServerStatus();
            loadServerManagementInterface();
        } else {
            alert(`Failed to update server: ${data.error || 'Unknown error'}`);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error updating server configuration. Please try again.');
    });
}

/**
 * Remove a server
 */
function removeServer(serverId) {
    fetch(`/api/local_models/servers/${serverId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show success message
            alert('Server removed successfully.');
            
            // Reload server data
            loadServerStatus();
            loadServerManagementInterface();
            loadAllLocalModels();
        } else {
            alert(`Failed to remove server: ${data.error || 'Unknown error'}`);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error removing server. Please try again.');
    });
}

/**
 * Load settings from server
 */
function loadSettings() {
    fetch('/api/local_models/settings')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                populateSettingsForm(data.settings);
            } else {
                console.error('Failed to load settings:', data.error);
            }
        })
        .catch(error => {
            console.error('Error loading settings:', error);
        });
}

/**
 * Populate settings form with values from server
 */
function populateSettingsForm(settings) {
    const form = document.getElementById('settings-form');
    if (!form) return;
    
    const autoFailover = document.getElementById('auto-failover');
    const loadBalancing = document.getElementById('load-balancing');
    const healthCheckInterval = document.getElementById('health-check-interval');
    const connectionTimeout = document.getElementById('connection-timeout');
    const maxRetryAttempts = document.getElementById('max-retry-attempts');
    const modelCooldown = document.getElementById('model-cooldown');
    
    if (autoFailover) autoFailover.checked = settings.auto_failover !== false;
    if (loadBalancing) loadBalancing.checked = settings.load_balancing !== false;
    
    if (healthCheckInterval) healthCheckInterval.value = settings.health_check_interval_minutes || 5;
    if (connectionTimeout) connectionTimeout.value = settings.connection_timeout_seconds || 10;
    if (maxRetryAttempts) maxRetryAttempts.value = settings.max_retry_attempts || 3;
    if (modelCooldown) modelCooldown.value = settings.model_cooldown_seconds || 30;
}

/**
 * Save settings to server
 */
function saveSettings(form) {
    const formData = new FormData(form);
    
    const settings = {
        auto_failover: formData.get('auto_failover') === 'on',
        load_balancing: formData.get('load_balancing') === 'on',
        health_check_interval_minutes: parseInt(formData.get('health_check_interval')),
        connection_timeout_seconds: parseInt(formData.get('connection_timeout')),
        max_retry_attempts: parseInt(formData.get('max_retry_attempts')),
        model_cooldown_seconds: parseInt(formData.get('model_cooldown'))
    };
    
    fetch('/api/local_models/settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Settings saved successfully.');
        } else {
            alert(`Failed to save settings: ${data.error || 'Unknown error'}`);
        }
    })
    .catch(error => {
        console.error('Error saving settings:', error);
        alert('Error saving settings. Please try again.');
    });
}

/**
 * Save model rankings
 */
function saveModelRankings(role) {
    const listElement = document.getElementById(`${role}-ranking-list`);
    if (!listElement) return;
    
    const items = listElement.querySelectorAll('li');
    const rankings = [];
    
    items.forEach((item, index) => {
        const modelId = item.getAttribute('data-model-id');
        if (modelId) {
            rankings.push({
                model: modelId,
                rank: index + 1
            });
        }
    });
    
    fetch(`/api/local_models/rankings/${role}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ rankings })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(`${role} model rankings saved successfully.`);
        } else {
            alert(`Failed to save ${role} rankings: ${data.error || 'Unknown error'}`);
        }
    })
    .catch(error => {
        console.error('Error saving rankings:', error);
        alert(`Error saving ${role} rankings. Please try again.`);
    });
}

/**
 * Save task-model mappings
 */
function saveTaskModelMappings() {
    const container = document.getElementById('task-mapping-container');
    if (!container) return;
    
    const taskRoleSelects = container.querySelectorAll('.task-role-select');
    const taskModelSelects = container.querySelectorAll('.task-models-select');
    
    const mappings = {};
    
    taskRoleSelects.forEach(select => {
        const taskType = select.getAttribute('data-task-type');
        const primaryRole = select.value;
        
        if (!mappings[taskType]) {
            mappings[taskType] = {
                primary_role: primaryRole,
                complexity_mapping: {
                    high: [],
                    medium: [],
                    low: []
                }
            };
        } else {
            mappings[taskType].primary_role = primaryRole;
        }
    });
    
    taskModelSelects.forEach(select => {
        const taskType = select.getAttribute('data-task-type');
        const complexity = select.getAttribute('data-complexity');
        
        if (!mappings[taskType]) {
            mappings[taskType] = {
                primary_role: 'coding', // Default
                complexity_mapping: {
                    high: [],
                    medium: [],
                    low: []
                }
            };
        }
        
        const selectedModels = Array.from(select.selectedOptions).map(option => option.value);
        mappings[taskType].complexity_mapping[complexity] = selectedModels;
    });
    
    fetch('/api/local_models/task_mappings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ mappings })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Task mappings saved successfully.');
        } else {
            alert(`Failed to save task mappings: ${data.error || 'Unknown error'}`);
        }
    })
    .catch(error => {
        console.error('Error saving task mappings:', error);
        alert('Error saving task mappings. Please try again.');
    });
}

/**
 * Add a new server
 */
function addServer(form) {
    const formData = new FormData(form);
    
    const serverId = formData.get('server_id');
    const serverConfig = {
        name: formData.get('server_name'),
        url: formData.get('server_url'),
        max_concurrent_tasks: parseInt(formData.get('max_tasks')),
        gpu: formData.get('server_gpu'),
        priority: parseInt(formData.get('server_priority'))
    };
    
    fetch(`/api/local_models/servers/${serverId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(serverConfig)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show success message
            alert('Server added successfully.');
            
            // Reset form
            form.reset();
            
            // Reload server data
            loadServerStatus();
            loadServerManagementInterface();
            loadAllLocalModels();
        } else {
            alert(`Failed to add server: ${data.error || 'Unknown error'}`);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error adding server. Please try again.');
    });
}

/**
 * Initialize sortable lists for drag-and-drop
 */
function initializeSortableLists() {
    // This will be done when the lists are populated
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
    // Refresh servers button
    const refreshServersBtn = document.getElementById('refresh-servers-btn');
    if (refreshServersBtn) {
        refreshServersBtn.addEventListener('click', function() {
            loadServerStatus();
            loadAllLocalModels();
        });
    }
    
    // Add server form
    const addServerForm = document.getElementById('add-server-form');
    if (addServerForm) {
        addServerForm.addEventListener('submit', function(e) {
            e.preventDefault();
            addServer(this);
        });
    }
    
    // Settings form
    const settingsForm = document.getElementById('settings-form');
    if (settingsForm) {
        settingsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            saveSettings(this);
        });
    }
    
    // Save rankings buttons
    const saveCodingRankingBtn = document.getElementById('save-coding-ranking-btn');
    if (saveCodingRankingBtn) {
        saveCodingRankingBtn.addEventListener('click', function() {
            saveModelRankings('coding');
        });
    }
    
    const saveOrchestrationRankingBtn = document.getElementById('save-orchestration-ranking-btn');
    if (saveOrchestrationRankingBtn) {
        saveOrchestrationRankingBtn.addEventListener('click', function() {
            saveModelRankings('orchestration');
        });
    }
    
    // Save task mappings button
    const saveTaskMappingBtn = document.getElementById('save-task-mapping-btn');
    if (saveTaskMappingBtn) {
        saveTaskMappingBtn.addEventListener('click', function() {
            saveTaskModelMappings();
        });
    }
}
