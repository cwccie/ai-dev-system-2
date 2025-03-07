// Main JavaScript file for AI Dev Orchestration System

document.addEventListener('DOMContentLoaded', function() {
    // Handle model provider selection
    initModelSelectors();
    
    // Set up form handlers
    initFormHandlers();
    
    // Set up cost estimation
    initCostEstimation();
    
    // Set up model recommendations
    initModelRecommendations();
    
    // Set up decomposition features
    initDecompositionFeatures();
    
    // Set up dependency visualization
    initDependencyVisualization();
});

/**
 * Initialize model provider and model selection dropdowns
 */
function initModelSelectors() {
    const modelSelectElements = document.querySelectorAll('.model-select');
    
    modelSelectElements.forEach(select => {
        select.addEventListener('change', function() {
            const parent = this.closest('.provider-section');
            const allSettings = parent.querySelectorAll('.model-settings');
            
            // Hide all settings first
            allSettings.forEach(settings => {
                settings.style.display = 'none';
            });
            
            // Show selected model settings
            const selectedModel = this.value;
            const targetSettings = parent.querySelector(`.${selectedModel}-settings`);
            if (targetSettings) {
                targetSettings.style.display = 'block';
            }
        });
        
        // Trigger change event to set initial state
        select.dispatchEvent(new Event('change'));
    });
    
    // Handle model selection within provider
    const modelNameSelects = document.querySelectorAll('.model-name-select');
    modelNameSelects.forEach(select => {
        select.addEventListener('change', function() {
            // Update cost estimation if enabled
            if (typeof updateCostEstimate === 'function') {
                updateCostEstimate();
            }
        });
    });
}

/**
 * Initialize form submission handlers
 */
function initFormHandlers() {
    // Handle script agent form
    const scriptForm = document.getElementById('script-form');
    if (scriptForm) {
        scriptForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const resultContainer = document.getElementById('result-container');
            resultContainer.innerHTML = '<div class="alert alert-info">Generating script... This may take a moment.</div>';
            
            const formData = new FormData(this);
            
            // Show processing indicator
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generating...';
            
            fetch(this.action, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                // Reset button
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
                
                if (data.success) {
                    let costInfo = '';
                    if (data.cost_info && data.cost_info.costs) {
                        const costs = data.cost_info.costs;
                        costInfo = `
                            <div class="alert alert-light border">
                                <h5>Cost Information</h5>
                                <p><strong>Total Cost:</strong> $${costs.total_cost.toFixed(6)}</p>
                                <p><small>Input: $${costs.input_cost.toFixed(6)}, Output: $${costs.output_cost.toFixed(6)}</small></p>
                            </div>
                        `;
                    }
                    
                    resultContainer.innerHTML = `
                        <div class="alert alert-success">Script generated successfully!</div>
                        <div class="model-info mb-3">
                            <strong>Model used:</strong> ${data.provider_used} / ${data.model_used}
                        </div>
                        ${costInfo}
                        <div class="code-display">
                            <div class="code-header">
                                <span class="code-title">${scriptForm.querySelector('input[name="script_name"]').value}</span>
                            </div>
                            <pre><code>${escapeHtml(data.script)}</code></pre>
                        </div>
                    `;
                } else {
                    resultContainer.innerHTML = `
                        <div class="alert alert-danger">Error: ${data.error}</div>
                    `;
                }
            })
            .catch(error => {
                // Reset button
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
                
                resultContainer.innerHTML = `
                    <div class="alert alert-danger">An error occurred during script generation.</div>
                    <p>${error}</p>
                `;
                console.error('Error:', error);
            });
        });
    }
    
    // Handle orchestrator form
    const orchestratorForm = document.getElementById('orchestrator-form');
    if (orchestratorForm) {
        orchestratorForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const resultContainer = document.getElementById('orchestrator-result-container');
            resultContainer.innerHTML = '<div class="alert alert-info">Orchestrating script generation... This may take a while.</div>';
            
            const formData = new FormData(this);
            
            // Show processing indicator
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Orchestrating...';
            
            fetch(this.action, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                // Reset button
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
                
                if (data.success) {
                    // Build result HTML
                    let resultHtml = `
                        <div class="alert alert-success">Script orchestration completed!</div>
                        <div class="model-info mb-3">
                            <strong>Model used:</strong> ${data.provider_used} / ${data.model_used}
                        </div>
                    `;
                    
                    // Add cost information if available
                    if (data.cost_info) {
                        resultHtml += `
                            <div class="alert alert-light border mb-3">
                                <h5>Cost Information</h5>
                                <p><strong>Total Cost:</strong> $${data.cost_info.total_costs.toFixed(6)}</p>
                                <p><small>Scripts generated: ${data.cost_info.script_count}</small></p>
                            </div>
                        `;
                    }
                    
                    // Add successful scripts
                    const successfulScripts = data.results.successful_scripts || [];
                    if (successfulScripts.length > 0) {
                        resultHtml += `
                            <h4>Successfully Generated Scripts (${successfulScripts.length})</h4>
                            <div class="list-group mb-4">
                        `;
                        
                        successfulScripts.forEach(script => {
                            resultHtml += `
                                <div class="list-group-item list-group-item-action">
                                    <div class="d-flex w-100 justify-content-between">
                                        <h5 class="mb-1">${script.name}</h5>
                                        <span class="badge bg-success">Score: ${(script.score * 100).toFixed(0)}%</span>
                                    </div>
                                    <p class="mb-1">Path: ${script.path}</p>
                                </div>
                            `;
                        });
                        
                        resultHtml += `</div>`;
                    }
                    
                    // Add failed scripts
                    const failedScripts = data.results.failed_scripts || [];
                    if (failedScripts.length > 0) {
                        resultHtml += `
                            <h4>Failed Scripts (${failedScripts.length})</h4>
                            <div class="list-group mb-4">
                        `;
                        
                        failedScripts.forEach(script => {
                            resultHtml += `
                                <div class="list-group-item list-group-item-action">
                                    <div class="d-flex w-100 justify-content-between">
                                        <h5 class="mb-1">${script.name}</h5>
                                        <span class="badge bg-danger">Score: ${(script.score * 100).toFixed(0)}%</span>
                                    </div>
                                    <p class="mb-1">Path: ${script.path}</p>
                                    <small class="text-muted">${script.feedback}</small>
                                </div>
                            `;
                        });
                        
                        resultHtml += `</div>`;
                    }
                    
                    // Add project analysis summary
                    if (data.results.project_analysis) {
                        const analysis = data.results.project_analysis;
                        resultHtml += `
                            <div class="card mb-4">
                                <div class="card-header">
                                    <h5 class="mb-0">Project Analysis</h5>
                                </div>
                                <div class="card-body">
                                    <p><strong>Files analyzed:</strong> ${analysis.total_files || 0}</p>
                                    <p><strong>Directories:</strong> ${analysis.total_directories || 0}</p>
                                    <p><strong>File types:</strong> ${JSON.stringify(analysis.file_types || {})}</p>
                                </div>
                            </div>
                        `;
                    }
                    
                    resultContainer.innerHTML = resultHtml;
                } else {
                    resultContainer.innerHTML = `
                        <div class="alert alert-danger">Error: ${data.error}</div>
                    `;
                }
            })
            .catch(error => {
                // Reset button
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
                
                resultContainer.innerHTML = `
                    <div class="alert alert-danger">An error occurred during orchestration.</div>
                    <p>${error}</p>
                `;
                console.error('Error:', error);
            });
        });
    }
    
    // API key management
    const apiKeyForms = document.querySelectorAll('.api-key-form');
    if (apiKeyForms) {
        apiKeyForms.forEach(form => {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const formData = new FormData(this);
                const statusElement = this.querySelector('.status-message');
                
                fetch('/save_api_key', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        statusElement.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
                    } else {
                        statusElement.innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
                    }
                })
                .catch(error => {
                    statusElement.innerHTML = `<div class="alert alert-danger">An error occurred while saving the API key.</div>`;
                    console.error('Error:', error);
                });
            });
        });
    }
}

/**
 * Initialize cost estimation features
 */
function initCostEstimation() {
    // Get elements
    const costEstimateBtn = document.getElementById('estimate-cost-btn');
    const costDisplay = document.getElementById('cost-estimate-display');
    
    if (!costEstimateBtn || !costDisplay) return;
    
    // Add event listener
    costEstimateBtn.addEventListener('click', function() {
        updateCostEstimate();
    });
    
    // Setup auto-update on parameter changes
    const scriptNameInput = document.querySelector('input[name="script_name"]');
    const scriptDescInput = document.querySelector('textarea[name="script_description"]');
    const requirementsList = document.getElementById('requirements-list');
    
    if (scriptNameInput) {
        scriptNameInput.addEventListener('blur', updateCostEstimate);
    }
    
    if (scriptDescInput) {
        scriptDescInput.addEventListener('blur', updateCostEstimate);
    }
    
    if (requirementsList) {
        // Monitor for changes in requirements (added or removed)
        const observer = new MutationObserver(updateCostEstimate);
        observer.observe(requirementsList, { childList: true });
    }
}

/**
 * Update cost estimate display
 */
function updateCostEstimate() {
    const costDisplay = document.getElementById('cost-estimate-display');
    if (!costDisplay) return;
    
    // Get current form data
    const scriptName = document.querySelector('input[name="script_name"]')?.value || '';
    const scriptDescription = document.querySelector('textarea[name="script_description"]')?.value || '';
    
    // Get requirements
    const requirementInputs = document.querySelectorAll('input[name="requirements[]"]');
    const requirements = Array.from(requirementInputs).map(input => input.value).filter(Boolean);
    
    // Get selected provider and model
    const providerSelect = document.querySelector('.model-select');
    const modelSelect = document.querySelector('.model-name-select');
    
    const provider = providerSelect?.value || 'claude';
    const model = modelSelect?.value || '';
    
    // Show loading state
    costDisplay.innerHTML = '<div class="spinner-border spinner-border-sm text-primary" role="status"><span class="visually-hidden">Loading...</span></div> Estimating cost...';
    
    // Prepare data for API request
    const data = {
        name: scriptName,
        description: scriptDescription,
        requirements: requirements,
        provider_name: provider,
        model_name: model
    };
    
    // Make API request
    fetch('/api/estimate_cost', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.estimate) {
            const estimate = data.estimate;
            const costs = estimate.costs;
            
            // Format cost display
            let html = `
                <div class="card">
                    <div class="card-header bg-light">
                        <h5 class="mb-0">Estimated Cost</h5>
                    </div>
                    <div class="card-body">
                        <div class="d-flex justify-content-between mb-2">
                            <span><strong>Total:</strong></span>
                            <span class="text-primary">${costs.total_cost.toFixed(6)}</span>
                        </div>
                        <div class="d-flex justify-content-between mb-2">
                            <span>Input Cost:</span>
                            <span>${costs.input_cost.toFixed(6)}</span>
                        </div>
                        <div class="d-flex justify-content-between mb-2">
                            <span>Output Cost:</span>
                            <span>${costs.output_cost.toFixed(6)}</span>
                        </div>
                        <hr>
                        <div class="d-flex justify-content-between">
                            <span><small>Model:</small></span>
                            <span><small>${estimate.model}</small></span>
                        </div>
                        <div class="d-flex justify-content-between">
                            <span><small>Provider:</small></span>
                            <span><small>${estimate.provider}</small></span>
                        </div>
                    </div>
                </div>
            `;
            
            // If context utilization is high, show warning
            if (estimate.context_utilization_percentage > 80) {
                html += `
                    <div class="alert alert-warning mt-2">
                        <small>
                            <strong>Warning:</strong> This script may use ${estimate.context_utilization_percentage.toFixed(1)}% 
                            of the model's context window. Consider using decomposition.
                        </small>
                    </div>
                `;
            }
            
            costDisplay.innerHTML = html;
        } else {
            costDisplay.innerHTML = `
                <div class="alert alert-warning">
                    Unable to estimate cost. 
                    ${data.error ? `<br><small>${data.error}</small>` : ''}
                </div>
            `;
        }
    })
    .catch(error => {
        costDisplay.innerHTML = '<div class="alert alert-danger">Error estimating cost</div>';
        console.error('Error:', error);
    });
}

/**
 * Initialize model recommendation features
 */
function initModelRecommendations() {
    // Get elements
    const recommendModelBtn = document.getElementById('recommend-model-btn');
    const recommendationDisplay = document.getElementById('model-recommendation-display');
    
    if (!recommendModelBtn || !recommendationDisplay) return;
    
    // Add event listener
    recommendModelBtn.addEventListener('click', function() {
        updateModelRecommendation();
    });
    
    // Auto-recommend on substantial changes
    const scriptDescInput = document.querySelector('textarea[name="script_description"]');
    if (scriptDescInput) {
        scriptDescInput.addEventListener('blur', function() {
            if (this.value.length > 50) {  // Only auto-update if description is substantial
                updateModelRecommendation();
            }
        });
    }
}

/**
 * Update model recommendation display
 */
function updateModelRecommendation() {
    const recommendationDisplay = document.getElementById('model-recommendation-display');
    if (!recommendationDisplay) return;
    
    // Get current form data
    const scriptName = document.querySelector('input[name="script_name"]')?.value || '';
    const scriptDescription = document.querySelector('textarea[name="script_description"]')?.value || '';
    
    // Get requirements
    const requirementInputs = document.querySelectorAll('input[name="requirements[]"]');
    const requirements = Array.from(requirementInputs).map(input => input.value).filter(Boolean);
    
    // Get selected provider as preference
    const providerSelect = document.querySelector('.model-select');
    const providerPreference = providerSelect?.value || null;
    
    // Show loading state
    recommendationDisplay.innerHTML = '<div class="spinner-border spinner-border-sm text-primary" role="status"><span class="visually-hidden">Loading...</span></div> Finding best model...';
    
    // Prepare data for API request
    const data = {
        name: scriptName,
        description: scriptDescription,
        requirements: requirements,
        provider_preference: providerPreference
    };
    
    // Make API request
    fetch('/api/recommend_model', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.recommendation) {
            const recommendation = data.recommendation;
            
            // Update model select dropdowns if available
            if (recommendation.recommended_provider && recommendation.recommended_model) {
                const providerSelect = document.querySelector('.model-select');
                if (providerSelect) {
                    providerSelect.value = recommendation.recommended_provider;
                    providerSelect.dispatchEvent(new Event('change'));
                    
                    // After provider change has taken effect, set the model
                    setTimeout(() => {
                        const modelSelect = document.querySelector('.model-name-select');
                        if (modelSelect) {
                            // Find option with value or containing text
                            const options = Array.from(modelSelect.options);
                            const option = options.find(opt => 
                                opt.value === recommendation.recommended_model || 
                                opt.text.includes(recommendation.recommended_model)
                            );
                            
                            if (option) {
                                modelSelect.value = option.value;
                                modelSelect.dispatchEvent(new Event('change'));
                            }
                        }
                    }, 50);
                }
            }
            
            // Format recommendation display
            let html = `
                <div class="card">
                    <div class="card-header bg-light">
                        <h5 class="mb-0">Recommended Model</h5>
                    </div>
                    <div class="card-body">
                        <div class="d-flex justify-content-between mb-2">
                            <span><strong>Model:</strong></span>
                            <span class="text-primary">${recommendation.recommended_model}</span>
                        </div>
                        <div class="d-flex justify-content-between mb-2">
                            <span><strong>Provider:</strong></span>
                            <span>${recommendation.recommended_provider}</span>
                        </div>
                        <div class="d-flex justify-content-between mb-2">
                            <span>Match Score:</span>
                            <span>${(recommendation.score * 100).toFixed(0)}%</span>
                        </div>
                    </div>
                </div>
            `;
            
            // Add analysis details
            if (recommendation.analysis) {
                const analysis = recommendation.analysis;
                html += `
                    <div class="card mt-2">
                        <div class="card-header bg-light">
                            <h6 class="mb-0">Script Analysis</h6>
                        </div>
                        <div class="card-body">
                            <div class="d-flex justify-content-between mb-2">
                                <span>Complexity:</span>
                                <span>${analysis.complexity.toFixed(1)}/10</span>
                            </div>
                            <div class="d-flex justify-content-between">
                                <span>Estimated Tokens:</span>
                                <span>${analysis.estimated_tokens.total_tokens}</span>
                            </div>
                        </div>
                    </div>
                `;
            }
            
            recommendationDisplay.innerHTML = html;
        } else if (data.fallback) {
            // Use fallback recommendation
            recommendationDisplay.innerHTML = `
                <div class="card">
                    <div class="card-header bg-light">
                        <h5 class="mb-0">Recommended Model</h5>
                    </div>
                    <div class="card-body">
                        <div class="d-flex justify-content-between mb-2">
                            <span><strong>Model:</strong></span>
                            <span class="text-primary">${data.fallback.recommended_model}</span>
                        </div>
                        <div class="d-flex justify-content-between mb-2">
                            <span><strong>Provider:</strong></span>
                            <span>${data.fallback.recommended_provider}</span>
                        </div>
                        <div class="alert alert-info mt-2 mb-0">
                            <small>This is a fallback recommendation. ${data.error}</small>
                        </div>
                    </div>
                </div>
            `;
        } else {
            recommendationDisplay.innerHTML = `
                <div class="alert alert-warning">
                    Unable to provide model recommendation. 
                    ${data.error ? `<br><small>${data.error}</small>` : ''}
                </div>
            `;
        }
    })
    .catch(error => {
        recommendationDisplay.innerHTML = '<div class="alert alert-danger">Error getting recommendation</div>';
        console.error('Error:', error);
    });
}

/**
 * Initialize script decomposition features
 */
function initDecompositionFeatures() {
    // Get elements
    const decomposeBtn = document.getElementById('decompose-script-btn');
    const decompositionDisplay = document.getElementById('decomposition-display');
    
    if (!decomposeBtn || !decompositionDisplay) return;
    
    // Add event listener
    decomposeBtn.addEventListener('click', function() {
        requestDecomposition();
    });
}

/**
 * Request script decomposition from the API
 */
function requestDecomposition() {
    const decompositionDisplay = document.getElementById('decomposition-display');
    if (!decompositionDisplay) return;
    
    // Get current form data
    const scriptName = document.querySelector('input[name="script_name"]')?.value || '';
    const scriptDescription = document.querySelector('textarea[name="script_description"]')?.value || '';
    
    // Get requirements
    const requirementInputs = document.querySelectorAll('input[name="requirements[]"]');
    const requirements = Array.from(requirementInputs).map(input => input.value).filter(Boolean);
    
    // Show loading state
    decompositionDisplay.innerHTML = '<div class="spinner-border spinner-border-sm text-primary" role="status"><span class="visually-hidden">Loading...</span></div> Analyzing script for decomposition...';
    
    // Prepare data for API request
    const data = {
        name: scriptName,
        description: scriptDescription,
        requirements: requirements,
        path: scriptName
    };
    
    // Make API request
    fetch('/api/decompose_script', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.decomposition) {
            const decomposition = data.decomposition;
            
            if (!decomposition.needs_decomposition) {
                decompositionDisplay.innerHTML = `
                    <div class="alert alert-info">
                        <strong>No decomposition needed.</strong> 
                        <p>This script is simple enough to generate as a single component.</p>
                        <p><small>Complexity score: ${decomposition.analysis.complexity.toFixed(1)}/10</small></p>
                    </div>
                `;
                return;
            }
            
            // Format decomposition display
            let html = `
                <div class="card">
                    <div class="card-header bg-light">
                        <h5 class="mb-0">Recommended Decomposition</h5>
                    </div>
                    <div class="card-body">
                        <p>This script can be decomposed into ${decomposition.components.length} components:</p>
                        <div class="list-group">
            `;
            
            // Add components
            decomposition.components.forEach((component, index) => {
                const isPrimary = component.is_primary ? 
                    '<span class="badge bg-primary ms-2">Primary</span>' : '';
                
                const dependencies = component.depends_on ? 
                    `<div class="mt-1"><small>Depends on: ${component.depends_on.join(', ')}</small></div>` : '';
                
                html += `
                    <div class="list-group-item">
                        <div class="d-flex w-100 justify-content-between">
                            <h6 class="mb-1">${component.name}${isPrimary}</h6>
                            <small>${component.type}</small>
                        </div>
                        <p class="mb-1">${component.description}</p>
                        ${dependencies}
                    </div>
                `;
            });
            
            html += `
                        </div>
                    </div>
                    <div class="card-footer">
                        <button class="btn btn-primary" id="apply-decomposition-btn">Apply Decomposition</button>
                    </div>
                </div>
            `;
            
            decompositionDisplay.innerHTML = html;
            
            // Add event listener to apply button
            document.getElementById('apply-decomposition-btn')?.addEventListener('click', function() {
                applyDecomposition(decomposition.components);
            });
        } else {
            decompositionDisplay.innerHTML = `
                <div class="alert alert-warning">
                    Unable to decompose script. 
                    ${data.error ? `<br><small>${data.error}</small>` : ''}
                </div>
            `;
        }
    })
    .catch(error => {
        decompositionDisplay.innerHTML = '<div class="alert alert-danger">Error analyzing script</div>';
        console.error('Error:', error);
    });
}

/**
 * Apply script decomposition by preparing the orchestrator form
 */
function applyDecomposition(components) {
    // Check if we're on the script agent page
    if (document.getElementById('script-form')) {
        // Redirect to orchestrator page with decomposition data
        const scriptName = document.querySelector('input[name="script_name"]')?.value || '';
        const scriptDescription = document.querySelector('textarea[name="script_description"]')?.value || '';
        const requirementInputs = document.querySelectorAll('input[name="requirements[]"]');
        const requirements = Array.from(requirementInputs).map(input => input.value).filter(Boolean);
        
        // Prepare data to send to orchestrator
        const decompositionData = {
            scriptName: scriptName,
            scriptDescription: scriptDescription,
            requirements: requirements,
            components: components
        };
        
        // Store in session storage
        sessionStorage.setItem('decompositionData', JSON.stringify(decompositionData));
        
        // Redirect to orchestrator
        window.location.href = '/orchestrator?decomposition=true';
    } else {
        // We're already on the orchestrator page, apply directly
        const scriptDefsTextarea = document.querySelector('textarea[name="script_definitions"]');
        if (scriptDefsTextarea) {
            // Format components as script definitions
            const scriptDefs = components.map(component => ({
                name: component.name,
                path: component.path || component.name,
                description: component.description,
                requirements: component.requirements || [],
                dependencies: component.depends_on || []
            }));
            
            // Update the textarea
            scriptDefsTextarea.value = JSON.stringify(scriptDefs, null, 2);
            
            // Enable parallelism if available
            const parallelismCheckbox = document.getElementById('use-parallelism');
            if (parallelismCheckbox) {
                parallelismCheckbox.checked = true;
            }
            
            // Scroll to form
            scriptDefsTextarea.scrollIntoView({ behavior: 'smooth' });
            
            // Highlight textarea
            scriptDefsTextarea.classList.add('border-primary');
            setTimeout(() => {
                scriptDefsTextarea.classList.remove('border-primary');
            }, 2000);
        }
    }
}

/**
 * Initialize dependency visualization features
 */
function initDependencyVisualization() {
    // Check if we're on the orchestrator page and have the decomposition parameter
    if (window.location.pathname === '/orchestrator' && 
        new URLSearchParams(window.location.search).get('decomposition') === 'true') {
        
        // Load decomposition data from session storage
        const decompositionData = JSON.parse(sessionStorage.getItem('decompositionData') || '{}');
        if (decompositionData.components) {
            // Apply decomposition data to form
            setTimeout(() => {
                applyDecomposition(decompositionData.components);
            }, 500);
        }
    }
    
    // Add visualization button if we're on the orchestrator page
    const scriptDefsTextarea = document.querySelector('textarea[name="script_definitions"]');
    if (scriptDefsTextarea) {
        // Create visualization button
        const visualizeBtn = document.createElement('button');
        visualizeBtn.type = 'button';
        visualizeBtn.className = 'btn btn-sm btn-outline-primary mt-2';
        visualizeBtn.textContent = 'Visualize Dependencies';
        visualizeBtn.id = 'visualize-deps-btn';
        
        // Insert button after textarea
        scriptDefsTextarea.parentNode.insertBefore(visualizeBtn, scriptDefsTextarea.nextSibling);
        
        // Add event listener
        visualizeBtn.addEventListener('click', function() {
            visualizeDependencies(scriptDefsTextarea.value);
        });
    }
}

/**
 * Visualize dependencies between script components
 */
function visualizeDependencies(scriptDefsJson) {
    try {
        // Parse script definitions
        const scriptDefs = JSON.parse(scriptDefsJson);
        
        // Send to API for analysis
        fetch('/api/dependencies', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(scriptDefs)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showDependencyGraph(data.analysis, data.parallel_suggestion);
            } else {
                alert(`Error analyzing dependencies: ${data.error}`);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error analyzing dependencies');
        });
    } catch (error) {
        alert('Invalid script definitions JSON');
    }
}

/**
 * Show dependency graph in a modal
 */
function showDependencyGraph(analysis, parallelSuggestion) {
    // Create modal if not exists
    let modal = document.getElementById('dependency-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'dependency-modal';
        modal.tabIndex = '-1';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Script Dependencies</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div id="dependency-vis" style="height: 400px;"></div>
                        <div id="parallel-groups" class="mt-3"></div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
    
    // Show modal
    const modalObj = new bootstrap.Modal(modal);
    modalObj.show();
    
    // Create the visualization when modal is shown
    modal.addEventListener('shown.bs.modal', function() {
        const container = document.getElementById('dependency-vis');
        
        // Format data for visualization
        const nodes = [];
        const edges = [];
        
        // Map component IDs to names
        const componentMap = {};
        for (const [componentId, dependencies] of Object.entries(analysis.dependency_graph)) {
            componentMap[componentId] = `Component ${componentId.split('_')[1]}`;
        }
        
        // Create nodes
        for (const componentId in analysis.dependency_graph) {
            nodes.push({
                id: componentId,
                label: componentMap[componentId]
            });
        }
        
        // Create edges
        for (const [componentId, dependencies] of Object.entries(analysis.dependency_graph)) {
            for (const dependency of dependencies) {
                edges.push({
                    from: dependency,
                    to: componentId,
                    arrows: 'to'
                });
            }
        }
        
        // Create the network
        const data = {
            nodes: new vis.DataSet(nodes),
            edges: new vis.DataSet(edges)
        };
        
        const options = {
            layout: {
                hierarchical: {
                    direction: 'UD',
                    sortMethod: 'directed'
                }
            },
            physics: {
                hierarchicalRepulsion: {
                    nodeDistance: 150
                }
            }
        };
        
        // Create network
        const network = new vis.Network(container, data, options);
        
        // Display parallel execution groups
        const parallelGroupsContainer = document.getElementById('parallel-groups');
        if (parallelGroupsContainer && parallelSuggestion) {
            let html = `
                <h5>Parallel Execution Groups</h5>
                <p>These components can be generated in parallel (${parallelSuggestion.max_parallel_workers} workers needed):</p>
            `;
            
            parallelSuggestion.parallel_groups.forEach((group, index) => {
                html += `<h6>Group ${index + 1}:</h6><ul>`;
                group.forEach(node => {
                    html += `<li>${node.name}</li>`;
                });
                html += `</ul>`;
            });
            
            parallelGroupsContainer.innerHTML = html;
        }
    });
}

/**
 * Utility function to escape HTML special characters
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Add a new requirement input field to the requirements list
 */
function addRequirement() {
    const list = document.getElementById('requirements-list');
    if (!list) return;
    
    const index = list.children.length;
    const item = document.createElement('div');
    item.className = 'requirement-item input-group mb-2';
    item.innerHTML = `
        <input type="text" class="form-control" name="requirements[]" placeholder="Requirement ${index + 1}">
        <button type="button" class="btn btn-outline-danger" onclick="removeRequirement(this)">Remove</button>
    `;
    
    list.appendChild(item);
}

/**
 * Remove a requirement input field
 */
function removeRequirement(button) {
    const item = button.closest('.requirement-item');
    item.remove();
}
