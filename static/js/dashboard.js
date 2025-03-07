/**
 * Dashboard.js
 * Script for the real-time monitoring dashboard of the AI Dev Orchestration System
 */

// Dashboard initialization
document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard components
    initTaskMonitor();
    initCostTracker();
    initDependencyGraph();
    initModelPerformance();
    
    // Set up refresh interval (every 5 seconds)
    setInterval(refreshDashboard, 5000);
    
    // Initial refresh
    refreshDashboard();
});

/**
 * Refresh all dashboard components
 */
function refreshDashboard() {
    fetchActiveAgents();
    fetchTaskStatus();
    fetchCostData();
    fetchModelStats();
}

/**
 * Initialize task monitor component
 */
function initTaskMonitor() {
    const taskMonitorEl = document.getElementById('task-monitor');
    if (!taskMonitorEl) return;
    
    // Create task monitor layout
    taskMonitorEl.innerHTML = `
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h3>Active Tasks</h3>
                <div class="controls">
                    <button id="refresh-tasks" class="btn btn-sm btn-primary">Refresh</button>
                </div>
            </div>
            <div class="card-body">
                <div class="task-filters mb-3">
                    <div class="btn-group btn-group-sm" role="group">
                        <button type="button" class="btn btn-outline-primary active" data-filter="all">All</button>
                        <button type="button" class="btn btn-outline-primary" data-filter="running">Running</button>
                        <button type="button" class="btn btn-outline-primary" data-filter="pending">Pending</button>
                        <button type="button" class="btn btn-outline-primary" data-filter="completed">Completed</button>
                        <button type="button" class="btn btn-outline-primary" data-filter="failed">Failed</button>
                    </div>
                </div>
                <div class="task-list-container">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Script</th>
                                <th>Provider</th>
                                <th>Status</th>
                                <th>Progress</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="task-list">
                            <tr>
                                <td colspan="6" class="text-center">Loading tasks...</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
    
    // Set up event listeners
    document.getElementById('refresh-tasks').addEventListener('click', fetchTaskStatus);
    
    // Set up filter buttons
    const filterButtons = document.querySelectorAll('.task-filters button');
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            filterButtons.forEach(btn => btn.classList.remove('active'));
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Apply filter
            const filter = this.getAttribute('data-filter');
            filterTasks(filter);
        });
    });
}

/**
 * Initialize cost tracker component
 */
function initCostTracker() {
    const costTrackerEl = document.getElementById('cost-tracker');
    if (!costTrackerEl) return;
    
    // Create cost tracker layout
    costTrackerEl.innerHTML = `
        <div class="card">
            <div class="card-header">
                <h3>Cost Monitoring</h3>
            </div>
            <div class="card-body">
                <div class="row mb-4">
                    <div class="col-md-4">
                        <div class="cost-card text-center p-3 border rounded">
                            <h5>Current Session</h5>
                            <h2 id="current-session-cost">$0.00</h2>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="cost-card text-center p-3 border rounded">
                            <h5>Daily Usage</h5>
                            <h2 id="daily-cost">$0.00</h2>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="cost-card text-center p-3 border rounded">
                            <h5>Monthly Budget</h5>
                            <div class="d-flex align-items-center justify-content-center">
                                <h2 id="monthly-cost">$0.00</h2>
                                <span class="ms-2 text-muted">/ $50.00</span>
                            </div>
                            <div class="progress mt-2">
                                <div id="budget-progress" class="progress-bar" role="progressbar" style="width: 0%"></div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <h4>Cost Breakdown by Provider</h4>
                <div id="cost-by-provider" class="mt-3">
                    <div class="placeholder-glow">
                        <div class="placeholder col-12 mb-2" style="height: 20px;"></div>
                        <div class="placeholder col-10 mb-2" style="height: 20px;"></div>
                        <div class="placeholder col-8 mb-2" style="height: 20px;"></div>
                    </div>
                </div>
                
                <div class="mt-4">
                    <h4>Historical Cost Trend</h4>
                    <canvas id="cost-trend-chart" height="200"></canvas>
                </div>
            </div>
        </div>
    `;
    
    // Initialize cost trend chart
    initCostTrendChart();
}

/**
 * Initialize dependency graph component
 */
function initDependencyGraph() {
    const dependencyGraphEl = document.getElementById('dependency-graph');
    if (!dependencyGraphEl) return;
    
    // Create dependency graph layout
    dependencyGraphEl.innerHTML = `
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h3>Dependency Graph</h3>
                <div class="controls">
                    <select id="graph-project-select" class="form-select form-select-sm" style="width: auto;">
                        <option value="">Select Project</option>
                    </select>
                </div>
            </div>
            <div class="card-body">
                <div id="dependency-graph-container" class="border rounded p-3 text-center">
                    <div id="cy" style="height: 400px;"></div>
                    <div id="graph-placeholder" class="text-muted">
                        <p>Select a project to view its dependency graph</p>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Set up event listeners
    document.getElementById('graph-project-select').addEventListener('change', function() {
        const projectId = this.value;
        if (projectId) {
            document.getElementById('graph-placeholder').style.display = 'none';
            fetchDependencyGraph(projectId);
        } else {
            document.getElementById('graph-placeholder').style.display = 'block';
            // Clear graph
            if (window.cy) {
                window.cy.destroy();
            }
        }
    });
    
    // Fetch available projects
    fetchProjects();
}

/**
 * Initialize model performance component
 */
function initModelPerformance() {
    const modelPerformanceEl = document.getElementById('model-performance');
    if (!modelPerformanceEl) return;
    
    // Create model performance layout
    modelPerformanceEl.innerHTML = `
        <div class="card">
            <div class="card-header">
                <h3>Model Performance</h3>
            </div>
            <div class="card-body">
                <ul class="nav nav-tabs" id="modelTabs" role="tablist">
                    <li class="nav-item" role="presentation">
                        <button class="nav-link active" id="success-tab" data-bs-toggle="tab" data-bs-target="#success-rates" type="button" role="tab">Success Rates</button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="latency-tab" data-bs-toggle="tab" data-bs-target="#latency" type="button" role="tab">Latency</button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="quality-tab" data-bs-toggle="tab" data-bs-target="#quality" type="button" role="tab">Quality Scores</button>
                    </li>
                </ul>
                <div class="tab-content p-3 border border-top-0 rounded-bottom" id="modelTabsContent">
                    <div class="tab-pane fade show active" id="success-rates" role="tabpanel">
                        <canvas id="success-rate-chart" height="250"></canvas>
                    </div>
                    <div class="tab-pane fade" id="latency" role="tabpanel">
                        <canvas id="latency-chart" height="250"></canvas>
                    </div>
                    <div class="tab-pane fade" id="quality" role="tabpanel">
                        <canvas id="quality-chart" height="250"></canvas>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Initialize charts
    initModelPerformanceCharts();
}

/**
 * Initialize cost trend chart
 */
function initCostTrendChart() {
    const ctx = document.getElementById('cost-trend-chart');
    if (!ctx) return;
    
    // Sample data - will be replaced with real data from API
    const data = {
        labels: Array.from({length: 14}, (_, i) => {
            const date = new Date();
            date.setDate(date.getDate() - (13 - i));
            return date.toLocaleDateString('en-US', {month: 'short', day: 'numeric'});
        }),
        datasets: [{
            label: 'Daily Cost ($)',
            data: Array.from({length: 14}, () => Math.random() * 5),
            borderColor: '#6a11cb',
            backgroundColor: 'rgba(106, 17, 203, 0.1)',
            fill: true,
            tension: 0.4
        }]
    };
    
    window.costTrendChart = new Chart(ctx, {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Cost: $${context.parsed.y.toFixed(2)}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toFixed(2);
                        }
                    }
                }
            }
        }
    });
}

/**
 * Initialize model performance charts
 */
function initModelPerformanceCharts() {
    // Success rate chart
    const successCtx = document.getElementById('success-rate-chart');
    if (successCtx) {
        window.successRateChart = new Chart(successCtx, {
            type: 'bar',
            data: {
                labels: ['Claude 3 Sonnet', 'GPT-4o', 'Claude 3 Haiku', 'DeepSeek Coder'],
                datasets: [{
                    label: 'Success Rate (%)',
                    data: [92, 88, 94, 85],
                    backgroundColor: [
                        'rgba(54, 162, 235, 0.7)',
                        'rgba(75, 192, 192, 0.7)',
                        'rgba(153, 102, 255, 0.7)',
                        'rgba(255, 159, 64, 0.7)'
                    ],
                    borderColor: [
                        'rgb(54, 162, 235)',
                        'rgb(75, 192, 192)',
                        'rgb(153, 102, 255)',
                        'rgb(255, 159, 64)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Success Rate: ${context.parsed.y}%`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Latency chart
    const latencyCtx = document.getElementById('latency-chart');
    if (latencyCtx) {
        window.latencyChart = new Chart(latencyCtx, {
            type: 'bar',
            data: {
                labels: ['Claude 3 Sonnet', 'GPT-4o', 'Claude 3 Haiku', 'DeepSeek Coder'],
                datasets: [{
                    label: 'Average Latency (s)',
                    data: [8.2, 5.4, 3.6, 6.8],
                    backgroundColor: [
                        'rgba(54, 162, 235, 0.7)',
                        'rgba(75, 192, 192, 0.7)',
                        'rgba(153, 102, 255, 0.7)',
                        'rgba(255, 159, 64, 0.7)'
                    ],
                    borderColor: [
                        'rgb(54, 162, 235)',
                        'rgb(75, 192, 192)',
                        'rgb(153, 102, 255)',
                        'rgb(255, 159, 64)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value + 's';
                            }
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Latency: ${context.parsed.y}s`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Quality chart
    const qualityCtx = document.getElementById('quality-chart');
    if (qualityCtx) {
        window.qualityChart = new Chart(qualityCtx, {
            type: 'radar',
            data: {
                labels: [
                    'Code Quality', 
                    'Documentation',
                    'Error Handling',
                    'Performance',
                    'Reliability',
                    'Maintainability'
                ],
                datasets: [
                    {
                        label: 'Claude 3 Sonnet',
                        data: [88, 95, 85, 78, 92, 90],
                        fill: true,
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        borderColor: 'rgb(54, 162, 235)',
                        pointBackgroundColor: 'rgb(54, 162, 235)',
                        pointBorderColor: '#fff',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: 'rgb(54, 162, 235)'
                    },
                    {
                        label: 'GPT-4o',
                        data: [92, 88, 90, 85, 86, 89],
                        fill: true,
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        borderColor: 'rgb(75, 192, 192)',
                        pointBackgroundColor: 'rgb(75, 192, 192)',
                        pointBorderColor: '#fff',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: 'rgb(75, 192, 192)'
                    }
                ]
            },
            options: {
                elements: {
                    line: {
                        borderWidth: 3
                    }
                },
                scales: {
                    r: {
                        angleLines: {
                            display: true
                        },
                        suggestedMin: 50,
                        suggestedMax: 100
                    }
                }
            }
        });
    }
}

/**
 * Fetch active agent data
 */
function fetchActiveAgents() {
    // In a real implementation, this would be an API call
    // For demo purposes, we'll use mock data
    const mockData = {
        active_agents: 3,
        max_agents: 5,
        busy_agents: 2,
        waiting_agents: 1,
        processing_stats: {
            tasks_completed: 24,
            tasks_pending: 5,
            tasks_in_progress: 3,
            tasks_failed: 2
        }
    };
    
    updateAgentStats(mockData);
}

/**
 * Update agent statistics in the UI
 */
function updateAgentStats(data) {
    // Update agent count display
    const agentCountEl = document.getElementById('agent-count');
    if (agentCountEl) {
        agentCountEl.innerHTML = `
            <div class="d-flex justify-content-between mb-1">
                <span>Active Agents:</span>
                <span>${data.active_agents}/${data.max_agents}</span>
            </div>
            <div class="progress mb-3" style="height: 10px;">
                <div class="progress-bar" role="progressbar" style="width: ${(data.active_agents / data.max_agents) * 100}%"></div>
            </div>
            <div class="d-flex justify-content-between text-muted">
                <span>Busy: ${data.busy_agents}</span>
                <span>Idle: ${data.waiting_agents}</span>
            </div>
        `;
    }
    
    // Update task stats
    const taskStatsEl = document.getElementById('task-stats');
    if (taskStatsEl) {
        taskStatsEl.innerHTML = `
            <div class="row text-center">
                <div class="col-md-3 col-6 mb-3">
                    <div class="p-3 border rounded">
                        <h3 class="text-primary">${data.processing_stats.tasks_completed}</h3>
                        <p class="mb-0">Completed</p>
                    </div>
                </div>
                <div class="col-md-3 col-6 mb-3">
                    <div class="p-3 border rounded">
                        <h3 class="text-warning">${data.processing_stats.tasks_in_progress}</h3>
                        <p class="mb-0">In Progress</p>
                    </div>
                </div>
                <div class="col-md-3 col-6 mb-3">
                    <div class="p-3 border rounded">
                        <h3 class="text-info">${data.processing_stats.tasks_pending}</h3>
                        <p class="mb-0">Pending</p>
                    </div>
                </div>
                <div class="col-md-3 col-6 mb-3">
                    <div class="p-3 border rounded">
                        <h3 class="text-danger">${data.processing_stats.tasks_failed}</h3>
                        <p class="mb-0">Failed</p>
                    </div>
                </div>
            </div>
        `;
    }
}

/**
 * Fetch task status data
 */
function fetchTaskStatus() {
    // In a real implementation, this would be an API call
    // For demo purposes, we'll use mock data
    const mockTasks = [
        {
            id: 'task-001',
            script_name: 'data_processor.py',
            provider: 'claude',
            model: 'claude-3-7-sonnet-20250219',
            status: 'running',
            progress: 65,
            started_at: new Date(Date.now() - 120000).toISOString()
        },
        {
            id: 'task-002',
            script_name: 'api_client.py',
            provider: 'openai',
            model: 'gpt-4o',
            status: 'pending',
            progress: 0,
            started_at: null
        },
        {
            id: 'task-003',
            script_name: 'utils.py',
            provider: 'claude',
            model: 'claude-3-5-haiku-20240620',
            status: 'completed',
            progress: 100,
            started_at: new Date(Date.now() - 360000).toISOString(),
            completed_at: new Date(Date.now() - 300000).toISOString()
        },
        {
            id: 'task-004',
            script_name: 'database.py',
            provider: 'deepseek',
            model: 'deepseek-coder',
            status: 'failed',
            progress: 40,
            error: 'Context limit exceeded',
            started_at: new Date(Date.now() - 240000).toISOString(),
            completed_at: new Date(Date.now() - 180000).toISOString()
        }
    ];
    
    updateTaskList(mockTasks);
}

/**
 * Update task list in the UI
 */
function updateTaskList(tasks) {
    const taskListEl = document.getElementById('task-list');
    if (!taskListEl) return;
    
    if (tasks.length === 0) {
        taskListEl.innerHTML = `
            <tr>
                <td colspan="6" class="text-center">No tasks found</td>
            </tr>
        `;
        return;
    }
    
    // Sort tasks: running first, then pending, then completed/failed
    tasks.sort((a, b) => {
        const order = { 'running': 0, 'pending': 1, 'completed': 2, 'failed': 3 };
        return order[a.status] - order[b.status];
    });
    
    taskListEl.innerHTML = tasks.map(task => {
        // Create status badge
        let statusBadge = '';
        switch(task.status) {
            case 'running':
                statusBadge = '<span class="badge bg-primary">Running</span>';
                break;
            case 'pending':
                statusBadge = '<span class="badge bg-warning text-dark">Pending</span>';
                break;
            case 'completed':
                statusBadge = '<span class="badge bg-success">Completed</span>';
                break;
            case 'failed':
                statusBadge = '<span class="badge bg-danger">Failed</span>';
                break;
            default:
                statusBadge = '<span class="badge bg-secondary">Unknown</span>';
        }
        
        // Create progress bar
        let progressBar = '';
        if (task.status === 'running') {
            progressBar = `
                <div class="progress">
                    <div class="progress-bar progress-bar-striped progress-bar-animated" 
                         role="progressbar" 
                         style="width: ${task.progress}%">
                        ${task.progress}%
                    </div>
                </div>
            `;
        } else if (task.status === 'completed') {
            progressBar = `
                <div class="progress">
                    <div class="progress-bar bg-success" 
                         role="progressbar" 
                         style="width: 100%">
                        100%
                    </div>
                </div>
            `;
        } else if (task.status === 'failed') {
            progressBar = `
                <div class="progress">
                    <div class="progress-bar bg-danger" 
                         role="progressbar" 
                         style="width: ${task.progress}%">
                        ${task.progress}%
                    </div>
                </div>
            `;
        } else {
            progressBar = `
                <div class="progress">
                    <div class="progress-bar" 
                         role="progressbar" 
                         style="width: 0%">
                        0%
                    </div>
                </div>
            `;
        }
        
        // Create actions based on status
        let actions = '';
        if (task.status === 'running') {
            actions = `
                <button class="btn btn-sm btn-outline-danger" onclick="cancelTask('${task.id}')">Cancel</button>
            `;
        } else if (task.status === 'pending') {
            actions = `
                <button class="btn btn-sm btn-outline-primary" onclick="prioritizeTask('${task.id}')">Prioritize</button>
                <button class="btn btn-sm btn-outline-danger" onclick="cancelTask('${task.id}')">Cancel</button>
            `;
        } else if (task.status === 'completed') {
            actions = `
                <button class="btn btn-sm btn-outline-secondary" onclick="viewResult('${task.id}')">View</button>
            `;
        } else if (task.status === 'failed') {
            actions = `
                <button class="btn btn-sm btn-outline-primary" onclick="retryTask('${task.id}')">Retry</button>
                <button class="btn btn-sm btn-outline-info" onclick="viewError('${task.id}')">View Error</button>
            `;
        }
        
        return `
            <tr data-status="${task.status}" data-id="${task.id}">
                <td><small class="text-muted">${task.id}</small></td>
                <td>${task.script_name}</td>
                <td>${task.provider} (${task.model.split('-')[0]})</td>
                <td>${statusBadge}</td>
                <td>${progressBar}</td>
                <td>${actions}</td>
            </tr>
        `;
    }).join('');
}

/**
 * Filter tasks by status
 */
function filterTasks(filter) {
    const rows = document.querySelectorAll('#task-list tr[data-status]');
    
    rows.forEach(row => {
        const status = row.getAttribute('data-status');
        
        if (filter === 'all' || status === filter) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

/**
 * Fetch cost data
 */
function fetchCostData() {
    // In a real implementation, this would be an API call
    // For demo purposes, we'll use mock data
    const mockCostData = {
        current_session: 1.24,
        daily: 3.75,
        monthly: 45.20,
        monthly_budget: 50.00,
        by_provider: {
            'claude': 24.30,
            'openai': 14.50,
            'deepseek': 6.40
        },
        trend: [
            { date: '2023-03-01', cost: 1.20 },
            { date: '2023-03-02', cost: 0.85 },
            { date: '2023-03-03', cost: 1.50 },
            { date: '2023-03-04', cost: 2.30 },
            { date: '2023-03-05', cost: 1.75 },
            { date: '2023-03-06', cost: 1.35 },
            { date: '2023-03-07', cost: 3.75 }
        ]
    };
    
    updateCostDisplay(mockCostData);
}

/**
 * Update cost display in the UI
 */
function updateCostDisplay(data) {
    // Update current session cost
    const sessionCostEl = document.getElementById('current-session-cost');
    if (sessionCostEl) {
        sessionCostEl.textContent = `${data.current_session.toFixed(2)}`;
    }
    
    // Update daily cost
    const dailyCostEl = document.getElementById('daily-cost');
    if (dailyCostEl) {
        dailyCostEl.textContent = `${data.daily.toFixed(2)}`;
    }
    
    // Update monthly cost and progress
    const monthlyCostEl = document.getElementById('monthly-cost');
    const budgetProgressEl = document.getElementById('budget-progress');
    
    if (monthlyCostEl && budgetProgressEl) {
        monthlyCostEl.textContent = `${data.monthly.toFixed(2)}`;
        
        const budgetPercentage = (data.monthly / data.monthly_budget) * 100;
        budgetProgressEl.style.width = `${budgetPercentage}%`;
        
        // Change color based on percentage
        if (budgetPercentage > 90) {
            budgetProgressEl.className = 'progress-bar bg-danger';
        } else if (budgetPercentage > 70) {
            budgetProgressEl.className = 'progress-bar bg-warning';
        } else {
            budgetProgressEl.className = 'progress-bar bg-success';
        }
    }
    
    // Update cost by provider
    const providerCostEl = document.getElementById('cost-by-provider');
    if (providerCostEl) {
        const totalCost = Object.values(data.by_provider).reduce((sum, cost) => sum + cost, 0);
        
        let html = '<div>';
        
        // Sort providers by cost (highest first)
        const sortedProviders = Object.entries(data.by_provider).sort((a, b) => b[1] - a[1]);
        
        for (const [provider, cost] of sortedProviders) {
            const percentage = (cost / totalCost) * 100;
            const providerColor = provider === 'claude' ? '#6a11cb' : 
                                provider === 'openai' ? '#008a7d' : 
                                provider === 'deepseek' ? '#e67e22' : '#888';
            
            html += `
                <div class="mb-2">
                    <div class="d-flex justify-content-between mb-1">
                        <span>${provider.charAt(0).toUpperCase() + provider.slice(1)}</span>
                        <span>${cost.toFixed(2)} (${percentage.toFixed(1)}%)</span>
                    </div>
                    <div class="progress" style="height: 8px;">
                        <div class="progress-bar" role="progressbar" 
                             style="width: ${percentage}%; background-color: ${providerColor}">
                        </div>
                    </div>
                </div>
            `;
        }
        
        html += '</div>';
        providerCostEl.innerHTML = html;
    }
    
    // Update cost trend chart
    if (window.costTrendChart && data.trend) {
        const labels = data.trend.map(point => {
            const date = new Date(point.date);
            return date.toLocaleDateString('en-US', {month: 'short', day: 'numeric'});
        });
        
        const costData = data.trend.map(point => point.cost);
        
        window.costTrendChart.data.labels = labels;
        window.costTrendChart.data.datasets[0].data = costData;
        window.costTrendChart.update();
    }
}

/**
 * Fetch projects for dependency graph
 */
function fetchProjects() {
    // In a real implementation, this would be an API call
    // For demo purposes, we'll use mock data
    const mockProjects = [
        { id: 'proj-001', name: 'Data Processing Utility' },
        { id: 'proj-002', name: 'Web API Client' },
        { id: 'proj-003', name: 'Dashboard Frontend' }
    ];
    
    // Populate project select dropdown
    const projectSelectEl = document.getElementById('graph-project-select');
    if (projectSelectEl) {
        const options = mockProjects.map(project => 
            `<option value="${project.id}">${project.name}</option>`
        ).join('');
        
        projectSelectEl.innerHTML = '<option value="">Select Project</option>' + options;
    }
}

/**
 * Fetch dependency graph for a project
 */
function fetchDependencyGraph(projectId) {
    // In a real implementation, this would be an API call
    // For demo purposes, we'll use mock data
    const mockGraphData = {
        'proj-001': {
            nodes: [
                { id: 'main', label: 'data_processor.py', type: 'main' },
                { id: 'reader', label: 'reader.py', type: 'utility' },
                { id: 'processor', label: 'processor.py', type: 'core' },
                { id: 'writer', label: 'writer.py', type: 'utility' },
                { id: 'utils', label: 'utils.py', type: 'utility' }
            ],
            edges: [
                { source: 'main', target: 'reader' },
                { source: 'main', target: 'processor' },
                { source: 'main', target: 'writer' },
                { source: 'processor', target: 'reader' },
                { source: 'writer', target: 'processor' },
                { source: 'reader', target: 'utils' },
                { source: 'processor', target: 'utils' },
                { source: 'writer', target: 'utils' }
            ]
        },
        'proj-002': {
            nodes: [
                { id: 'client', label: 'api_client.py', type: 'main' },
                { id: 'auth', label: 'auth.py', type: 'security' },
                { id: 'http', label: 'http_handler.py', type: 'utility' },
                { id: 'models', label: 'models.py', type: 'data' },
                { id: 'cache', label: 'cache.py', type: 'utility' }
            ],
            edges: [
                { source: 'client', target: 'auth' },
                { source: 'client', target: 'http' },
                { source: 'client', target: 'models' },
                { source: 'http', target: 'auth' },
                { source: 'http', target: 'cache' },
                { source: 'models', target: 'cache' }
            ]
        },
        'proj-003': {
            nodes: [
                { id: 'app', label: 'app.js', type: 'main' },
                { id: 'dashboard', label: 'dashboard.js', type: 'view' },
                { id: 'charts', label: 'charts.js', type: 'utility' },
                { id: 'api', label: 'api.js', type: 'service' },
                { id: 'utils', label: 'utils.js', type: 'utility' },
                { id: 'auth', label: 'auth.js', type: 'security' }
            ],
            edges: [
                { source: 'app', target: 'dashboard' },
                { source: 'app', target: 'api' },
                { source: 'app', target: 'auth' },
                { source: 'dashboard', target: 'charts' },
                { source: 'dashboard', target: 'api' },
                { source: 'api', target: 'auth' },
                { source: 'charts', target: 'utils' },
                { source: 'api', target: 'utils' }
            ]
        }
    };
    
    // Get graph data for selected project
    const graphData = mockGraphData[projectId];
    if (!graphData) return;
    
    // Render dependency graph
    renderDependencyGraph(graphData);
}

/**
 * Render dependency graph
 */
function renderDependencyGraph(data) {
    const container = document.getElementById('cy');
    if (!container) return;
    
    // Clear previous graph
    if (window.cy) {
        window.cy.destroy();
    }
    
    // Define node colors by type
    const nodeColors = {
        main: '#6a11cb',
        core: '#2ecc71',
        utility: '#3498db',
        security: '#e74c3c',
        data: '#f39c12',
        service: '#9b59b6',
        view: '#1abc9c'
    };
    
    // Create cytoscape elements
    const elements = [];
    
    // Add nodes
    data.nodes.forEach(node => {
        elements.push({
            data: {
                id: node.id,
                label: node.label,
                type: node.type,
                color: nodeColors[node.type] || '#888'
            }
        });
    });
    
    // Add edges
    data.edges.forEach(edge => {
        elements.push({
            data: {
                id: `${edge.source}-${edge.target}`,
                source: edge.source,
                target: edge.target
            }
        });
    });
    
    // Initialize cytoscape
    window.cy = cytoscape({
        container: container,
        elements: elements,
        style: [
            {
                selector: 'node',
                style: {
                    'background-color': 'data(color)',
                    'label': 'data(label)',
                    'color': '#fff',
                    'text-outline-color': 'data(color)',
                    'text-outline-width': 2,
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'font-size': '12px',
                    'width': 60,
                    'height': 60
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 3,
                    'line-color': '#ccc',
                    'target-arrow-color': '#ccc',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier'
                }
            }
        ],
        layout: {
            name: 'dagre',
            rankDir: 'TB',
            padding: 30,
            spacingFactor: 1.5
        }
    });
    
    // Add interactivity
    window.cy.on('tap', 'node', function(evt) {
        const node = evt.target;
        
        // Display node info (to be implemented with a modal or tooltip)
        console.log('Node clicked:', node.data());
    });
}

/**
 * Fetch model performance statistics
 */
function fetchModelStats() {
    // In a real implementation, this would be an API call
    // For demo purposes, we'll update charts with random variations
    if (window.successRateChart) {
        const data = window.successRateChart.data.datasets[0].data;
        // Add small random variations (-2 to +2)
        const newData = data.map(val => Math.min(100, Math.max(50, val + (Math.random() * 4 - 2))));
        window.successRateChart.data.datasets[0].data = newData;
        window.successRateChart.update();
    }
    
    if (window.latencyChart) {
        const data = window.latencyChart.data.datasets[0].data;
        // Add small random variations (-0.5 to +0.5)
        const newData = data.map(val => Math.max(1, val + (Math.random() - 0.5)));
        window.latencyChart.data.datasets[0].data = newData;
        window.latencyChart.update();
    }
}

// Action handler functions (would make API calls in a real implementation)
function cancelTask(taskId) {
    console.log(`Canceling task: ${taskId}`);
    alert(`Task ${taskId} cancellation requested`);
    // In a real implementation, make an API call and then refresh the task list
}

function prioritizeTask(taskId) {
    console.log(`Prioritizing task: ${taskId}`);
    alert(`Task ${taskId} prioritized`);
    // In a real implementation, make an API call and then refresh the task list
}

function viewResult(taskId) {
    console.log(`Viewing result for task: ${taskId}`);
    // In a real implementation, this would open a modal with the result
    window.location.href = `/view_task_result?id=${taskId}`;
}

function viewError(taskId) {
    console.log(`Viewing error for task: ${taskId}`);
    // In a real implementation, this would open a modal with the error details
    alert(`Task ${taskId} failed: Context limit exceeded during generation. Recommended action: Decompose the script into smaller components.`);
}

function retryTask(taskId) {
    console.log(`Retrying task: ${taskId}`);
    alert(`Task ${taskId} retry requested`);
    // In a real implementation, make an API call and then refresh the task list
}

        