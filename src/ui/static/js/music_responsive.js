// Add this function to fetch and display platform analytics
function loadPlatformAnalytics() {
    fetch('/api/music-responsive/analytics/platforms')
        .then(response => response.json())
        .then(data => {
            // Handle platform distribution chart
            const platforms = Object.keys(data.platforms);
            const distributionCounts = platforms.map(p => data.platforms[p].total);
            
            new Chart(document.getElementById('platformDistributionChart').getContext('2d'), {
                type: 'pie',
                data: {
                    labels: platforms,
                    datasets: [{
                        data: distributionCounts,
                        backgroundColor: [
                            '#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b', '#6610f2'
                        ]
                    }]
                },
                options: {
                    maintainAspectRatio: false,
                    tooltips: {
                        callbacks: {
                            label: (tooltipItem, data) => {
                                const dataset = data.datasets[tooltipItem.datasetIndex];
                                const total = dataset.data.reduce((acc, val) => acc + val, 0);
                                const value = dataset.data[tooltipItem.index];
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${data.labels[tooltipItem.index]}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            });
            
            // Handle success rate chart
            const successRates = platforms.map(p => (data.success_rate[p] * 100).toFixed(1));
            
            new Chart(document.getElementById('platformSuccessChart').getContext('2d'), {
                type: 'bar',
                data: {
                    labels: platforms,
                    datasets: [{
                        label: 'Success Rate (%)',
                        data: successRates,
                        backgroundColor: '#1cc88a'
                    }]
                },
                options: {
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });
            
            // Populate recent distributions table
            const tableBody = document.getElementById('platformDistributionsTable').getElementsByTagName('tbody')[0];
            tableBody.innerHTML = '';
            
            // Get the 10 most recent distributions
            let recentDistributions = [];
            Object.entries(data.sessions || {}).forEach(([sessionId, session]) => {
                if (session.platform_distributions) {
                    Object.entries(session.platform_distributions).forEach(([platform, distData]) => {
                        recentDistributions.push({
                            sessionId,
                            platform,
                            timestamp: new Date(distData.timestamp),
                            success: distData.success,
                            metrics: distData.metrics
                        });
                    });
                }
            });
            
            // Sort by timestamp (most recent first) and take the first 10
            recentDistributions.sort((a, b) => b.timestamp - a.timestamp);
            recentDistributions = recentDistributions.slice(0, 10);
            
            recentDistributions.forEach(dist => {
                const row = tableBody.insertRow();
                
                // Timestamp
                const timestampCell = row.insertCell();
                timestampCell.textContent = dist.timestamp.toLocaleString();
                
                // Platform
                const platformCell = row.insertCell();
                platformCell.textContent = dist.platform;
                
                // Status
                const statusCell = row.insertCell();
                statusCell.innerHTML = dist.success 
                    ? '<span class="badge bg-success">Success</span>'
                    : '<span class="badge bg-danger">Failed</span>';
                
                // Processing Time
                const timeCell = row.insertCell();
                timeCell.textContent = dist.metrics.processing_time 
                    ? `${dist.metrics.processing_time.toFixed(2)}s`
                    : 'N/A';
                
                // File Size
                const sizeCell = row.insertCell();
                sizeCell.textContent = dist.metrics.file_size
                    ? formatFileSize(dist.metrics.file_size)
                    : 'N/A';
                
                // Resolution
                const resolutionCell = row.insertCell();
                resolutionCell.textContent = dist.metrics.resolution || 'N/A';
            });
        })
        .catch(error => {
            console.error('Error loading platform analytics:', error);
        });
}

// Update the initialization code to load platform analytics when that tab is activated
document.getElementById('platforms-tab').addEventListener('shown.bs.tab', loadPlatformAnalytics);

// Add this function to load trend data
function loadTrendData() {
    // Load trending presets
    fetch('/api/trends/presets')
        .then(response => response.json())
        .then(data => {
            const presets = Object.keys(data.preset_usage).slice(0, 8);
            const usageCounts = presets.map(p => data.preset_usage[p]);
            
            new Chart(document.getElementById('trendingPresetsChart').getContext('2d'), {
                type: 'bar',
                data: {
                    labels: presets,
                    datasets: [{
                        label: 'Usage Count',
                        data: usageCounts,
                        backgroundColor: '#4e73df'
                    }]
                },
                options: {
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('Error loading preset trends:', error);
        });
    
    // Load trending effects
    fetch('/api/trends/effects')
        .then(response => response.json())
        .then(data => {
            const effects = Object.keys(data.effect_usage).slice(0, 8);
            const usageCounts = effects.map(e => data.effect_usage[e]);
            
            new Chart(document.getElementById('trendingEffectsChart').getContext('2d'), {
                type: 'bar',
                data: {
                    labels: effects,
                    datasets: [{
                        label: 'Usage Count',
                        data: usageCounts,
                        backgroundColor: '#1cc88a'
                    }]
                },
                options: {
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('Error loading effect trends:', error);
        });
    
    // Load recommendations
    fetch('/api/trends/recommendations')
        .then(response => response.json())
        .then(recommendations => {
            const container = document.getElementById('recommendationsContainer');
            container.innerHTML = '';
            
            recommendations.forEach(rec => {
                const card = document.createElement('div');
                card.className = 'col-lg-4 col-md-6 mb-4';
                
                let itemsHtml = '';
                if (rec.type === 'preset') {
                    itemsHtml = `
                        <ul class="list-group list-group-flush">
                            ${rec.items.map(item => `
                                <li class="list-group-item d-flex justify-content-between align-items-center">
                                    ${item}
                                    <button class="btn btn-sm btn-primary use-preset-btn" data-preset="${item}">Use</button>
                                </li>
                            `).join('')}
                        </ul>
                    `;
                } else if (rec.type === 'effect_combination') {
                    itemsHtml = `
                        <ul class="list-group list-group-flush">
                            ${rec.items.map(item => `
                                <li class="list-group-item d-flex justify-content-between align-items-center">
                                    ${item.name}
                                    <button class="btn btn-sm btn-primary use-effects-btn" 
                                            data-effects="${item.effects.join(',')}">Use</button>
                                </li>
                            `).join('')}
                        </ul>
                    `;
                } else {
                    itemsHtml = `<p class="card-text">${rec.description}</p>`;
                }
                
                card.innerHTML = `
                    <div class="card h-100">
                        <div class="card-header bg-primary text-white">
                            <h5 class="card-title mb-0">${rec.title}</h5>
                        </div>
                        <div class="card-body">
                            ${itemsHtml}
                        </div>
                    </div>
                `;
                
                container.appendChild(card);
            });
            
            // Add event listeners for recommendation buttons
            document.querySelectorAll('.use-preset-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const preset = btn.getAttribute('data-preset');
                    // Set the preset in the video creator form
                    document.getElementById('preset').value = preset;
                    // Switch to creator tab
                    document.getElementById('creator-tab').click();
                });
            });
            
            document.querySelectorAll('.use-effects-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const effects = btn.getAttribute('data-effects').split(',');
                    // Select these effects in the form
                    document.querySelectorAll('#effects option').forEach(option => {
                        option.selected = effects.includes(option.value);
                    });
                    // Switch to creator tab
                    document.getElementById('creator-tab').click();
                });
            });
        })
        .catch(error => {
            console.error('Error loading recommendations:', error);
        });
}

// Update the initialization code to load trend data when that tab is activated
document.getElementById('trends-tab').addEventListener('shown.bs.tab', loadTrendData);

// Add these functions for performance prediction

// Update duration display value
document.getElementById('predictionDuration').addEventListener('input', function() {
    document.getElementById('durationValue').textContent = this.value + 's';
});

// Update tempo display value
document.getElementById('predictionTempo').addEventListener('input', function() {
    document.getElementById('tempoValue').textContent = this.value;
});

// Update energy display value
document.getElementById('predictionEnergy').addEventListener('input', function() {
    const energyValue = parseInt(this.value);
    let energyLabel = 'Medium';
    
    if (energyValue <= 2) {
        energyLabel = 'Very Calm';
    } else if (energyValue <= 4) {
        energyLabel = 'Calm';
    } else if (energyValue <= 6) {
        energyLabel = 'Medium';
    } else if (energyValue <= 8) {
        energyLabel = 'Energetic';
    } else {
        energyLabel = 'Very Intense';
    }
    
    document.getElementById('energyValue').textContent = energyLabel;
});

// Handle prediction form submission
document.getElementById('predictionForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    // Get form values
    const duration = parseInt(document.getElementById('predictionDuration').value);
    const preset = document.getElementById('predictionPreset').value;
    
    // Get selected effects
    const effects = [];
    document.querySelectorAll('.prediction-effect:checked').forEach(checkbox => {
        effects.push(checkbox.value);
    });
    
    // Get music features
    const tempo = parseInt(document.getElementById('predictionTempo').value);
    const energyValue = parseInt(document.getElementById('predictionEnergy').value) / 10.0;
    
    // Create request payload
    const requestData = {
        duration: duration,
        effects: effects,
        preset: preset,
        audio_features: {
            tempo: tempo,
            energy: energyValue,
            beat_strength: energyValue * 0.8 + 0.2 // Derived from energy
        }
    };
    
    // Show loading state
    document.getElementById('noPrediction').classList.add('d-none');
    document.getElementById('predictionResults').classList.add('d-none');
    document.getElementById('predictionResults').insertAdjacentHTML('afterend', 
        '<div id="predictionLoading" class="text-center py-5">' +
        '<div class="spinner-border text-primary" role="status"></div>' +
        '<p class="mt-3">Analyzing and predicting performance...</p>' +
        '</div>'
    );
    
    // Send prediction request
    fetch('/api/predictions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(data => {
        // Remove loading state
        document.getElementById('predictionLoading').remove();
        
        // Show results
        document.getElementById('predictionResults').classList.remove('d-none');
        
        // Update prediction display
        const score = data.engagement_score.toFixed(1);
        document.getElementById('engagementScore').textContent = score;
        document.getElementById('performanceCategory').textContent = data.performance_category;
        
        // Update progress bar
        const percentage = Math.min(parseFloat(score) * 10, 100);
        const engagementBar = document.getElementById('engagementBar');
        engagementBar.style.width = `${percentage}%`;
        engagementBar.setAttribute('aria-valuenow', score);
        
        // Set color based on category
        engagementBar.className = 'progress-bar progress-bar-striped';
        if (data.performance_category === 'Low Engagement') {
            engagementBar.classList.add('bg-danger');
        } else if (data.performance_category === 'Average Engagement') {
            engagementBar.classList.add('bg-warning');
        } else if (data.performance_category === 'High Engagement') {
            engagementBar.classList.add('bg-success');
        } else {
            engagementBar.classList.add('bg-primary');
        }
        
        // Update confidence
        document.getElementById('predictionConfidence').textContent = 
            `${(data.confidence * 100).toFixed(0)}%`;
        
        // Update recommendations
        const recommendationsList = document.getElementById('recommendationsList');
        recommendationsList.innerHTML = '';
        
        if (data.recommendations && data.recommendations.length > 0) {
            data.recommendations.forEach(rec => {
                const li = document.createElement('li');
                li.className = 'list-group-item d-flex justify-content-between align-items-center';
                li.innerHTML = `
                    ${rec}
                    <span class="badge bg-primary rounded-pill">+${Math.random().toFixed(1)}</span>
                `;
                recommendationsList.appendChild(li);
            });
        } else {
            recommendationsList.innerHTML = '<li class="list-group-item">No specific recommendations available.</li>';
        }
        
        // Add event listeners for action buttons
        setupPredictionActionButtons(requestData, data.recommendations);
    })
    .catch(error => {
        console.error('Error making prediction:', error);
        document.getElementById('predictionLoading').remove();
        
        // Show error message
        document.getElementById('predictionResults').insertAdjacentHTML('afterend', 
            `<div class="alert alert-danger">
                Error making prediction: ${error.message}. Please try again.
            </div>`
        );
    });
});

// Set up action buttons for prediction results
function setupPredictionActionButtons(predictionData, recommendations) {
    // Apply recommendations button
    const applyButton = document.getElementById('applyRecommendationsBtn');
    applyButton.onclick = function() {
        // Switch to creator tab
        document.getElementById('creator-tab').click();
        
        // Apply the first 2-3 recommendations to the form
        // This is a simplified implementation - in a real application,
        // you would parse the recommendations and apply them to the form fields
        if (recommendations && recommendations.length > 0) {
            // Simulate applying recommendations
            // In reality, this would modify actual form fields based on the text of the recommendations
            alert('Applied recommendations to the creator form');
        } else {
            alert('No recommendations to apply');
        }
    };
    
    // Generate with current settings button
    const generateButton = document.getElementById('generateWithCurrentSettingsBtn');
    generateButton.onclick = function() {
        // Switch to creator tab
        document.getElementById('creator-tab').click();
        
        // Apply the current prediction settings to the form
        document.getElementById('duration').value = predictionData.duration;
        
        // Set preset (this would need to be adapted to your actual preset selection mechanism)
        document.getElementById('selectedPreset').value = predictionData.preset;
        
        // Set effect intensity (assuming 1.0 as default)
        document.getElementById('effectIntensity').value = 1.0;
        document.getElementById('intensityValue').textContent = 1.0;
        
        // Simulate clicking the generate button (commented out for safety)
        // document.getElementById('generateBtn').click();
        
        alert('Settings applied to the creator form. Now you can upload your media and generate the video.');
    };
}

// A/B Testing functionality
document.getElementById('abTestForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    // Get selected parameters to test
    const params = [];
    document.querySelectorAll('#abTestForm input[type="checkbox"]:checked').forEach(checkbox => {
        params.push(checkbox.value);
    });
    
    // Get number of variants
    const variantCount = parseInt(document.getElementById('variantCount').value);
    
    // Show loading state
    document.getElementById('noABTest').classList.add('d-none');
    document.getElementById('abTestResults').classList.add('d-none');
    document.getElementById('noABTest').insertAdjacentHTML('afterend', 
        '<div id="abTestLoading" class="text-center py-5">' +
        '<div class="spinner-border text-primary" role="status"></div>' +
        '<p class="mt-3">Generating and analyzing variants...</p>' +
        '</div>'
    );
    
    // Get current prediction form values to use as baseline
    const baselineData = {
        duration: parseInt(document.getElementById('predictionDuration').value),
        preset: document.getElementById('predictionPreset').value,
        effects: [],
        audio_features: {
            tempo: parseInt(document.getElementById('predictionTempo').value),
            energy: parseInt(document.getElementById('predictionEnergy').value) / 10.0
        }
    };
    
    // Get selected effects
    document.querySelectorAll('.prediction-effect:checked').forEach(checkbox => {
        baselineData.effects.push(checkbox.value);
    });
    
    // Generate variants
    setTimeout(() => {
        // Remove loading state
        document.getElementById('abTestLoading').remove();
        
        // Show results
        document.getElementById('abTestResults').classList.remove('d-none');
        
        // Generate variants and populate table
        const variants = generateABTestVariants(baselineData, params, variantCount);
        displayABTestVariants(variants);
    }, 1500); // Simulate API call delay
});

// Generate A/B test variants based on baseline and selected parameters
function generateABTestVariants(baseline, params, count) {
    const variants = [
        {
            id: 'A',
            settings: { ...baseline },
            changes: 'Baseline',
            score: (Math.random() * 3 + 5).toFixed(1) // Random score between 5.0 and 8.0
        }
    ];
    
    const presets = ['standard', 'subtle', 'energetic', 'dramatic', 'cinematic'];
    const allEffects = ['pulse', 'zoom', 'shake', 'flash', 'color_shift', 'blur', 'warp', 'glitch'];
    const transitions = ['smooth', 'hard', 'fade', 'wipe'];
    
    // Generate variants
    for (let i = 1; i < count; i++) {
        const variant = {
            id: String.fromCharCode(65 + i), // A, B, C, D...
            settings: JSON.parse(JSON.stringify(baseline)), // Deep copy
            changes: [],
            score: 0
        };
        
        // Apply changes based on selected parameters
        if (params.includes('preset') && Math.random() > 0.5) {
            // Pick a different preset
            let newPreset;
            do {
                newPreset = presets[Math.floor(Math.random() * presets.length)];
            } while (newPreset === baseline.preset);
            
            variant.settings.preset = newPreset;
            variant.changes.push(`Preset: ${newPreset}`);
        }
        
        if (params.includes('effects') && Math.random() > 0.5) {
            // Modify effects
            if (Math.random() > 0.5 && baseline.effects.length > 0) {
                // Remove an effect
                const removeIndex = Math.floor(Math.random() * baseline.effects.length);
                const removedEffect = baseline.effects[removeIndex];
                variant.settings.effects = baseline.effects.filter(e => e !== removedEffect);
                variant.changes.push(`Removed: ${removedEffect}`);
            } else {
                // Add an effect
                const unusedEffects = allEffects.filter(e => !baseline.effects.includes(e));
                if (unusedEffects.length > 0) {
                    const newEffect = unusedEffects[Math.floor(Math.random() * unusedEffects.length)];
                    variant.settings.effects = [...baseline.effects, newEffect];
                    variant.changes.push(`Added: ${newEffect}`);
                }
            }
        }
        
        if (params.includes('intensity') && Math.random() > 0.5) {
            // Modify intensity
            const newIntensity = (Math.random() * 1.5 + 0.5).toFixed(1); // Random intensity between 0.5 and 2.0
            variant.settings.effect_intensity = parseFloat(newIntensity);
            variant.changes.push(`Intensity: ${newIntensity}`);
        }
        
        if (params.includes('transitions') && Math.random() > 0.5) {
            // Modify transition
            const newTransition = transitions[Math.floor(Math.random() * transitions.length)];
            variant.settings.transition = newTransition;
            variant.changes.push(`Transition: ${newTransition}`);
        }
        
        // If no changes were made, add at least one change
        if (variant.changes.length === 0) {
            if (params.includes('preset')) {
                let newPreset;
                do {
                    newPreset = presets[Math.floor(Math.random() * presets.length)];
                } while (newPreset === baseline.preset);
                
                variant.settings.preset = newPreset;
                variant.changes.push(`Preset: ${newPreset}`);
            } else if (params.includes('effects') && allEffects.length > 0) {
                const newEffect = allEffects[Math.floor(Math.random() * allEffects.length)];
                variant.settings.effects = [...baseline.effects, newEffect];
                variant.changes.push(`Added: ${newEffect}`);
            }
        }
        
        // Calculate variant score
        // Baseline is between 5.0-8.0, variants are +/- 2.0 from that
        variant.score = (parseFloat(variants[0].score) + (Math.random() * 4 - 2)).toFixed(1);
        // Ensure score is between 1.0 and 10.0
        variant.score = Math.max(1.0, Math.min(10.0, variant.score)).toFixed(1);
        
        variants.push(variant);
    }
    
    // Sort by score (highest first)
    return variants.sort((a, b) => parseFloat(b.score) - parseFloat(a.score));
}

// Display A/B test variants in the table
function displayABTestVariants(variants) {
    const tableBody = document.getElementById('variantsTableBody');
    tableBody.innerHTML = '';
    
    variants.forEach(variant => {
        const row = document.createElement('tr');
        
        // Variant ID
        const idCell = document.createElement('td');
        idCell.textContent = variant.id;
        if (variant.id === 'A') {
            idCell.innerHTML += ' <span class="badge bg-secondary">Baseline</span>';
        }
        row.appendChild(idCell);
        
        // Changes
        const changesCell = document.createElement('td');
        if (typeof variant.changes === 'string') {
            changesCell.textContent = variant.changes;
        } else {
            changesCell.innerHTML = variant.changes.join('<br>');
        }
        row.appendChild(changesCell);
        
        // Score
        const scoreCell = document.createElement('td');
        let scoreClass = '';
        if (parseFloat(variant.score) >= 8.0) {
            scoreClass = 'text-success fw-bold';
        } else if (parseFloat(variant.score) >= 6.0) {
            scoreClass = 'text-primary';
        } else if (parseFloat(variant.score) >= 4.0) {
            scoreClass = 'text-warning';
        } else {
            scoreClass = 'text-danger';
        }
        scoreCell.innerHTML = `<span class="${scoreClass}">${variant.score}</span>`;
        row.appendChild(scoreCell);
        
        // Action
        const actionCell = document.createElement('td');
        actionCell.innerHTML = `
            <button class="btn btn-sm btn-primary use-variant-btn" data-variant-id="${variant.id}">
                Use
            </button>
        `;
        row.appendChild(actionCell);
        
        tableBody.appendChild(row);
    });
    
    // Add event listeners for use buttons
    document.querySelectorAll('.use-variant-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const variantId = this.getAttribute('data-variant-id');
            const variant = variants.find(v => v.id === variantId);
            
            if (variant) {
                // Apply variant settings to prediction form
                if (variant.settings.preset) {
                    document.getElementById('predictionPreset').value = variant.settings.preset;
                }
                
                // Apply effects
                if (variant.settings.effects) {
                    // Uncheck all effects first
                    document.querySelectorAll('.prediction-effect').forEach(checkbox => {
                        checkbox.checked = false;
                    });
                    
                    // Check the ones in the variant
                    variant.settings.effects.forEach(effect => {
                        const checkbox = document.getElementById(`effect${effect.charAt(0).toUpperCase() + effect.slice(1)}`);
                        if (checkbox) {
                            checkbox.checked = true;
                        }
                    });
                }
                
                // Apply intensity if available
                if (variant.settings.effect_intensity) {
                    document.getElementById('effectIntensity').value = variant.settings.effect_intensity;
                    document.getElementById('intensityValue').textContent = variant.settings.effect_intensity;
                }
                
                // Update duration
                if (variant.settings.duration) {
                    document.getElementById('predictionDuration').value = variant.settings.duration;
                    document.getElementById('durationValue').textContent = variant.settings.duration + 's';
                }
                
                // Trigger prediction with these settings
                document.getElementById('predictionForm').dispatchEvent(new Event('submit'));
                
                // Show confirmation message
                alert(`Applied settings from Variant ${variantId} (Score: ${variant.score})`);
            }
        });
    });
}

// Initialize prediction tab when activated
document.getElementById('predictions-tab').addEventListener('shown.bs.tab', function() {
    // Reset prediction form
    document.getElementById('predictionForm').reset();
    
    // Reset results
    document.getElementById('noPrediction').classList.remove('d-none');
    document.getElementById('predictionResults').classList.add('d-none');
    
    // Reset A/B testing
    document.getElementById('noABTest').classList.remove('d-none');
    document.getElementById('abTestResults').classList.add('d-none');
    
    // Update display values
    document.getElementById('durationValue').textContent = document.getElementById('predictionDuration').value + 's';
    document.getElementById('tempoValue').textContent = document.getElementById('predictionTempo').value;
    document.getElementById('energyValue').textContent = 'Medium';
});

// Licensing Tab Functions
function initializeLicensingTab() {
    // Add event listeners for licensing tab buttons
    document.getElementById('viewLicenseKeyBtn').addEventListener('click', toggleLicenseKeyVisibility);
    document.getElementById('renewLicenseBtn').addEventListener('click', handleRenewLicense);
    document.getElementById('upgradeLicenseBtn').addEventListener('click', handleUpgradeLicense);
    document.getElementById('transferLicenseBtn').addEventListener('click', handleTransferLicense);
    document.getElementById('viewAllPlansBtn').addEventListener('click', handleViewAllPlans);
    document.getElementById('manageDevicesBtn').addEventListener('click', handleManageDevices);
    document.getElementById('manageApiKeysBtn').addEventListener('click', handleManageApiKeys);
    document.getElementById('downloadInvoicesBtn').addEventListener('click', handleDownloadInvoices);
    document.getElementById('contactSupportBtn').addEventListener('click', handleContactSupport);
    document.getElementById('disableAutoRenewalBtn').addEventListener('click', handleDisableAutoRenewal);
    document.getElementById('updatePaymentMethodBtn').addEventListener('click', handleUpdatePaymentMethod);
    
    // Fetch license data when tab is shown
    document.getElementById('licensing-tab').addEventListener('shown.bs.tab', fetchLicenseData);
}

// Toggle license key visibility (show/hide)
function toggleLicenseKeyVisibility() {
    const licenseKeyInput = document.getElementById('licenseKey');
    const viewButton = document.getElementById('viewLicenseKeyBtn');
    
    if (licenseKeyInput.value === 'XXXX-XXXX-XXXX-XXXX') {
        // Simulate fetching the actual license key
        licenseKeyInput.value = 'ABCD-EF12-GH34-IJ56';
        viewButton.innerHTML = '<i class="bi bi-eye-slash"></i>';
    } else {
        licenseKeyInput.value = 'XXXX-XXXX-XXXX-XXXX';
        viewButton.innerHTML = '<i class="bi bi-eye"></i>';
    }
}

// Fetch license data from the server
function fetchLicenseData() {
    // Simulate API call with a timeout
    document.getElementById('licenseStatusMessage').innerHTML = '<i class="bi bi-arrow-repeat spin me-2"></i> Loading license information...';
    
    setTimeout(() => {
        // Mock license data - in a real app, this would come from the server
        const licenseData = {
            type: 'Professional',
            expiration: 'December 31, 2023',
            owner: 'John Doe (john.doe@example.com)',
            activeDevices: '2 of 3 allowed',
            projectExports: 'Unlimited',
            features: [
                { name: 'Video Exports', status: 'Enabled', details: 'Unlimited exports in up to 4K resolution' },
                { name: 'Advanced Effects', status: 'Enabled', details: 'Access to all premium effects and transitions' },
                { name: 'Commercial Usage', status: 'Enabled', details: 'Licensed for commercial projects' },
                { name: 'Batch Processing', status: 'Enabled', details: 'Process up to 10 videos simultaneously' },
                { name: 'Extended Analysis', status: 'Enabled', details: 'Access to advanced analytics and insights' },
                { name: 'API Access', status: 'Limited', details: '500 API calls per day (upgrade for more)' }
            ],
            history: [
                { date: 'Jan 15, 2023', action: 'License Purchased', details: 'Professional Plan - 1 Year' },
                { date: 'Jan 16, 2023', action: 'Device Activated', details: 'MacBook Pro (John\'s Laptop)' },
                { date: 'Mar 20, 2023', action: 'Device Activated', details: 'Mac Studio (Office)' },
                { date: 'Apr 10, 2023', action: 'License Feature Added', details: 'Added Batch Processing capability' }
            ]
        };
        
        // Update the UI with the license data
        document.getElementById('licenseType').textContent = licenseData.type;
        document.getElementById('licenseExpiration').textContent = licenseData.expiration;
        document.getElementById('licenseOwner').textContent = licenseData.owner;
        document.getElementById('activeDevices').textContent = licenseData.activeDevices;
        document.getElementById('projectExports').textContent = licenseData.projectExports;
        document.getElementById('licenseStatusMessage').textContent = `Your ${licenseData.type} license is active until ${licenseData.expiration}`;
        
        // You could also dynamically populate the features and history tables here
    }, 1000);
}

// License renewal handler
function handleRenewLicense() {
    showLicenseModal('Renew Your License', 
        'Renew your Professional license for another year.',
        'Your current license expires on December 31, 2023. Renewing now will extend your license until December 31, 2024.',
        'Renew License - $199/year');
}

// License upgrade handler
function handleUpgradeLicense() {
    showLicenseModal('Upgrade Your License', 
        'Upgrade to an Enterprise license for more features.',
        'Upgrading to Enterprise gives you access to unlimited devices, priority support, and higher API limits.',
        'Upgrade to Enterprise - $499/year');
}

// License transfer handler
function handleTransferLicense() {
    showLicenseModal('Transfer Your License', 
        'Transfer your license to another user.',
        'This will remove the license from your account and transfer it to the specified email address.',
        'Transfer License',
        true);
}

// View all plans handler
function handleViewAllPlans() {
    window.location.href = '/pricing';
}

// Manage devices handler
function handleManageDevices() {
    showLicenseModal('Manage Active Devices', 
        'You have 2 of 3 allowed devices activated.',
        '<div class="list-group"><div class="list-group-item d-flex justify-content-between align-items-center">MacBook Pro (John\'s Laptop)<button class="btn btn-sm btn-outline-danger">Deactivate</button></div><div class="list-group-item d-flex justify-content-between align-items-center">Mac Studio (Office)<button class="btn btn-sm btn-outline-danger">Deactivate</button></div></div>',
        'Activate New Device');
}

// Manage API keys handler
function handleManageApiKeys() {
    showLicenseModal('Manage API Keys', 
        'Your API usage: 234 of 500 calls today',
        '<div class="mb-3"><label class="form-label">Your API Key</label><div class="input-group"><input type="text" class="form-control" value="api_12345678" readonly><button class="btn btn-outline-secondary"><i class="bi bi-clipboard"></i></button></div></div><div class="alert alert-info">API Documentation is available <a href="/docs/api" class="alert-link">here</a>.</div>',
        'Generate New API Key');
}

// Download invoices handler
function handleDownloadInvoices() {
    showLicenseModal('Download Invoices', 
        'Your billing history',
        '<div class="list-group"><a href="#" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center">Invoice #12345 - Jan 15, 2023<i class="bi bi-download"></i></a></div>',
        'Close',
        false,
        true);
}

// Contact support handler
function handleContactSupport() {
    showLicenseModal('Contact Support', 
        'Our support team is here to help',
        '<form><div class="mb-3"><label class="form-label">Subject</label><input type="text" class="form-control" placeholder="License assistance"></div><div class="mb-3"><label class="form-label">Message</label><textarea class="form-control" rows="4" placeholder="Describe your issue..."></textarea></div></form>',
        'Send Message');
}

// Disable auto-renewal handler
function handleDisableAutoRenewal() {
    if (confirm('Are you sure you want to disable auto-renewal? Your license will expire on December 31, 2023 if not manually renewed.')) {
        // Simulate API call
        document.querySelector('#licenseStatusAlert').innerHTML = 
            '<i class="bi bi-info-circle me-2"></i><span>Auto-renewal has been disabled. Your license will expire on December 31, 2023.</span>';
        
        // Update button
        document.getElementById('disableAutoRenewalBtn').textContent = 'Enable Auto-Renewal';
        document.getElementById('disableAutoRenewalBtn').classList.remove('btn-outline-danger');
        document.getElementById('disableAutoRenewalBtn').classList.add('btn-outline-success');
        
        // Update the warning
        document.querySelector('.alert-warning').classList.remove('alert-warning');
        document.querySelector('.alert-warning').classList.add('alert-danger');
        document.querySelector('.alert-danger').innerHTML = 
            '<i class="bi bi-exclamation-triangle me-2"></i><small>Auto-renewal is disabled. Your license will expire on December 31, 2023.</small>';
    }
}

// Update payment method handler
function handleUpdatePaymentMethod() {
    showLicenseModal('Update Payment Method', 
        'Update your billing information',
        '<form><div class="mb-3"><label class="form-label">Card Number</label><input type="text" class="form-control" placeholder="**** **** **** 1234"></div><div class="row"><div class="col-md-6"><div class="mb-3"><label class="form-label">Expiration Date</label><input type="text" class="form-control" placeholder="MM/YY"></div></div><div class="col-md-6"><div class="mb-3"><label class="form-label">CVC</label><input type="text" class="form-control" placeholder="123"></div></div></div><div class="mb-3"><label class="form-label">Billing Address</label><input type="text" class="form-control" placeholder="123 Main St"></div></form>',
        'Update Payment Method');
}

// Show modal for license operations
function showLicenseModal(title, subtitle, content, primaryButtonText, includeEmailField = false, hideMainButton = false) {
    // Check if modal already exists, remove if it does
    const existingModal = document.getElementById('licenseModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Create modal HTML
    const modalHTML = `
        <div class="modal fade" id="licenseModal" tabindex="-1" aria-labelledby="licenseModalLabel" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="licenseModalLabel">${title}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <p class="lead">${subtitle}</p>
                        ${includeEmailField ? '<div class="mb-3"><label class="form-label">Email Address</label><input type="email" class="form-control" placeholder="recipient@example.com"></div>' : ''}
                        ${content}
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        ${!hideMainButton ? `<button type="button" class="btn btn-primary" id="licenseModalActionBtn">${primaryButtonText}</button>` : ''}
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Add modal to the document
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Initialize modal
    const modal = new bootstrap.Modal(document.getElementById('licenseModal'));
    modal.show();
    
    // Add event listener for primary button
    const actionButton = document.getElementById('licenseModalActionBtn');
    if (actionButton) {
        actionButton.addEventListener('click', () => {
            // Simulate API action
            modal.hide();
            
            // Show success toast notification
            showToast(`${title} Successful`, 'Your request has been processed successfully.');
        });
    }
}

// Show toast notification
function showToast(title, message) {
    // Check if toast container exists, create if not
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast HTML
    const toastId = 'toast-' + Date.now();
    const toastHTML = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <strong class="me-auto">${title}</strong>
                <small>Just now</small>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    // Add toast to container
    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    
    // Initialize and show toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { autohide: true, delay: 5000 });
    toast.show();
    
    // Remove toast after hiding
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

// Initialize licensing tab when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize other components
    // ...
    
    // Initialize licensing tab
    initializeLicensingTab();
}); 