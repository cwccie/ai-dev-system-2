// Main JavaScript file for AI Dev Orchestration System

document.addEventListener('DOMContentLoaded', function() {
    // Add animation classes to cards
    document.querySelectorAll('.card').forEach((card, index) => {
        setTimeout(() => {
            card.classList.add('fadeIn');
        }, index * 100);
    });

    // Handle model provider selection
    const modelSelectElements = document.querySelectorAll('.model-select');
    
    modelSelectElements.forEach(select => {
        select.addEventListener('change', function() {
            const parent = this.closest('.provider-section');
            const allSettings = parent.querySelectorAll('.model-settings');
            
            // Hide all settings first
            allSettings.forEach(settings => {
                settings.style.display = 'none';
            });
            
            // Show selected model settings with animation
            const selectedModel = this.value;
            const targetSettings = parent.querySelector(`.${selectedModel}-settings`);
            if (targetSettings) {
                targetSettings.style.display = 'block';
                targetSettings.classList.add('slideIn');
            }
        });
        
        // Trigger change event to set initial state
        select.dispatchEvent(new Event('change'));
    });
    
    // Update temperature value display
    document.querySelectorAll('input[type="range"]').forEach(range => {
        const valueDisplay = document.getElementById(`${range.id}-value`);
        if (valueDisplay) {
            // Update on page load
            valueDisplay.textContent = range.value;
            
            // Update on change
            range.addEventListener('input', function() {
                valueDisplay.textContent = this.value;
            });
        }
    });
    
    // Handle form submissions with AJAX
    const scriptForm = document.getElementById('script-form');
    if (scriptForm) {
        scriptForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const resultContainer = document.getElementById('result-container');
            resultContainer.innerHTML = '<div class="alert alert-info">Generating script... This may take a moment.</div>';
            resultContainer.classList.add('slideIn');
            
            const formData = new FormData(this);
            
            // Collect requirements from textarea (one per line)
            const requirementsTextarea = document.getElementById('requirements');
            if (requirementsTextarea && requirementsTextarea.value.trim()) {
                // Clear existing requirements
                const existingReqs = formData.getAll('requirements');
                existingReqs.forEach(() => formData.delete('requirements'));
                
                // Add each line as a separate requirement
                requirementsTextarea.value.split('\n').filter(req => req.trim()).forEach(req => {
                    formData.append('requirements', req.trim());
                });
            }
            
            fetch(this.action, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    resultContainer.innerHTML = `
                        <div class="alert alert-success">Script generated successfully using ${data.provider_used}!</div>
                        <div class="code-display">
                            <div class="code-header">
                                <span class="code-title">Generated Script</span>
                            </div>
                            <pre><code>${escapeHtml(data.script)}</code></pre>
                        </div>
                    `;
                } else {
                    resultContainer.innerHTML = `
                        <div class="alert alert-danger">Error: ${escapeHtml(data.error)}</div>
                    `;
                }
                resultContainer.classList.add('slideIn');
            })
            .catch(error => {
                resultContainer.innerHTML = `
                    <div class="alert alert-danger">An error occurred during script generation.</div>
                    <p>${escapeHtml(error.toString())}</p>
                `;
                resultContainer.classList.add('slideIn');
                console.error('Error:', error);
            });
        });
    }
    
    // Handle orchestrator form
    const orchestratorForm = document.getElementById('orchestrator-form');
    if (orchestratorForm) {
        orchestratorForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const resultContainer = document.getElementById('result-container');
            resultContainer.innerHTML = '<div class="alert alert-info">Orchestrating script generation... This may take several minutes for complex projects.</div>';
            resultContainer.classList.add('slideIn');
            
            const formData = new FormData(this);
            
            fetch(this.action, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    let resultHtml = `
                        <div class="alert alert-success">Orchestration completed successfully using ${data.provider_used}!</div>
                        <h3>Results Summary</h3>
                        <p>Generated ${data.results.successful_scripts.length} scripts successfully.</p>
                    `;
                    
                    if (data.results.successful_scripts.length > 0) {
                        resultHtml += `<h4>Successful Scripts</h4><ul>`;
                        data.results.successful_scripts.forEach(script => {
                            resultHtml += `<li><strong>${escapeHtml(script.name)}</strong> - Saved to: ${escapeHtml(script.path)} (Score: ${script.score.toFixed(2)})</li>`;
                        });
                        resultHtml += `</ul>`;
                    }
                    
                    if (data.results.failed_scripts.length > 0) {
                        resultHtml += `<h4>Failed Scripts</h4><ul>`;
                        data.results.failed_scripts.forEach(script => {
                            resultHtml += `<li><strong>${escapeHtml(script.name)}</strong> - Failed with score: ${script.score.toFixed(2)}
                                <div class="alert alert-warning">${escapeHtml(script.feedback)}</div></li>`;
                        });
                        resultHtml += `</ul>`;
                    }
                    
                    resultContainer.innerHTML = resultHtml;
                } else {
                    resultContainer.innerHTML = `
                        <div class="alert alert-danger">Error: ${escapeHtml(data.error)}</div>
                    `;
                }
                resultContainer.classList.add('slideIn');
            })
            .catch(error => {
                resultContainer.innerHTML = `
                    <div class="alert alert-danger">An error occurred during orchestration.</div>
                    <p>${escapeHtml(error.toString())}</p>
                `;
                resultContainer.classList.add('slideIn');
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
                        statusElement.innerHTML = `<div class="alert alert-success">${escapeHtml(data.message)}</div>`;
                    } else {
                        statusElement.innerHTML = `<div class="alert alert-danger">${escapeHtml(data.message)}</div>`;
                    }
                    
                    // Show the result with animation
                    const alert = statusElement.querySelector('.alert');
                    if (alert) alert.classList.add('fadeIn');
                    
                    // Hide after 5 seconds
                    setTimeout(() => {
                        if (statusElement.querySelector('.alert')) {
                            statusElement.querySelector('.alert').style.opacity = '0';
                            setTimeout(() => {
                                statusElement.innerHTML = '';
                            }, 300);
                        }
                    }, 5000);
                })
                .catch(error => {
                    statusElement.innerHTML = `<div class="alert alert-danger">An error occurred while saving the API key.</div>`;
                    console.error('Error:', error);
                });
            });
        });
    }
    
    // Helper function to escape HTML
    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
