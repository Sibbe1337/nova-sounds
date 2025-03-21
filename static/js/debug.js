/**
 * Debug.js - Debug Mode Helper Functions
 * 
 * This file provides functionality for debug mode including:
 * - Debug panel UI interactions
 * - Resource monitoring (detect missing images, files, etc.)
 * - System metrics monitoring
 * - Mock data generation
 * - API request logging
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize debug mode components
    initDebugPanel();
    detectMissingResources();
    monitorSystemMetrics();
    interceptAPIRequests();
    handleMockDataGeneration();
});

/**
 * Initialize Debug Panel UI and interactions
 */
function initDebugPanel() {
    const debugModeIndicator = document.querySelector('.debug-mode-indicator');
    const toggleDebugPanelBtn = document.getElementById('toggleDebugPanel');
    const closeDebugPanelBtn = document.getElementById('closeDebugPanel');
    const debugPanel = document.getElementById('debugPanel');
    
    // Toggle debug panel
    if (toggleDebugPanelBtn) {
        toggleDebugPanelBtn.addEventListener('click', function() {
            debugPanel.classList.toggle('open');
        });
    }
    
    // Allow clicking on the indicator to toggle panel
    if (debugModeIndicator) {
        debugModeIndicator.addEventListener('click', function(e) {
            if (e.target !== toggleDebugPanelBtn && !toggleDebugPanelBtn.contains(e.target)) {
                debugPanel.classList.toggle('open');
            }
        });
    }
    
    // Close debug panel
    if (closeDebugPanelBtn) {
        closeDebugPanelBtn.addEventListener('click', function() {
            debugPanel.classList.remove('open');
        });
    }
    
    // Close panel with Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && debugPanel.classList.contains('open')) {
            debugPanel.classList.remove('open');
        }
    });
    
    // Add debug panel version info
    addDebugLog('Debug mode initialized v1.0.0', 'success', 'apiLogs');
}

/**
 * Detect missing resources (images, scripts, etc.)
 */
function detectMissingResources() {
    const missingResourcesContainer = document.getElementById('missingResources');
    const missingResources = [];
    
    // Create a log entry in the missing resources section
    function logMissingResource(resource, type) {
        missingResources.push({ resource, type });
        
        if (missingResourcesContainer) {
            // Clear initial message if this is the first entry
            if (missingResources.length === 1) {
                missingResourcesContainer.innerHTML = '';
            }
            
            const logElement = document.createElement('div');
            logElement.className = 'debug-log error';
            logElement.textContent = `${type}: ${resource}`;
            missingResourcesContainer.appendChild(logElement);
        }
    }
    
    // Monitor image errors
    document.querySelectorAll('img').forEach(img => {
        if (img.complete && (img.naturalWidth === 0 || img.naturalHeight === 0)) {
            handleMissingImage(img);
        }
        
        img.addEventListener('error', function() {
            handleMissingImage(img);
        });
    });
    
    function handleMissingImage(img) {
        logMissingResource(img.src, 'Image');
        img.classList.add('error');
        
        // Get path for checks
        const path = img.src || '';
        
        // Check if this is an onboarding image (they're loaded but not displayed yet)
        const isOnboardingImage = path.includes('/onboarding/') && 
            (img.closest('.onboarding-slide') || path.includes('welcome.png') || 
             path.includes('music.png') || path.includes('style.png') || 
             path.includes('preview.png') || path.includes('upload.png'));
        
        // If it's an onboarding image, just log it but don't try to replace
        if (isOnboardingImage) {
            console.warn(`Onboarding image not loaded: ${path} - Will be handled when modal opens`);
            return;
        }
        
        // Replace with placeholder for height/width
        const width = img.width || img.getAttribute('width') || 150;
        const height = img.height || img.getAttribute('height') || 100;
        
        // Create auto placeholder if needed
        if (!img.classList.contains('placeholder-applied')) {
            const placeholder = document.createElement('div');
            placeholder.className = 'img-placeholder';
            placeholder.style.width = width + 'px';
            placeholder.style.height = height + 'px';
            placeholder.setAttribute('title', 'Missing image: ' + img.src);
            placeholder.setAttribute('data-original-src', img.src);
            
            // Add placeholder text showing just the filename
            const filename = img.src.split('/').pop();
            const placeholderText = document.createElement('span');
            placeholderText.textContent = filename;
            placeholder.appendChild(placeholderText);
            
            // Replace img with placeholder - add null check for parentNode
            if (img.parentNode) {
                img.parentNode.replaceChild(placeholder, img);
            } else {
                console.warn('Cannot replace image: parent node is null', img.src);
            }
        }
    }
    
    // Monitor stylesheet errors
    document.querySelectorAll('link[rel="stylesheet"]').forEach(link => {
        const originalHref = link.href;
        
        // Attempt to fetch the stylesheet to check if it exists
        fetch(originalHref, { method: 'HEAD' })
            .then(response => {
                if (!response.ok) {
                    logMissingResource(originalHref, 'CSS');
                }
            })
            .catch(() => {
                logMissingResource(originalHref, 'CSS');
            });
    });
    
    // Monitor script errors
    document.querySelectorAll('script[src]').forEach(script => {
        const originalSrc = script.src;
        
        // Create a test script element to check if it exists
        const testScript = document.createElement('script');
        testScript.src = originalSrc;
        testScript.async = true;
        
        testScript.onerror = function() {
            logMissingResource(originalSrc, 'Script');
        };
        
        // Add and then remove the test script
        document.head.appendChild(testScript);
        setTimeout(() => {
            document.head.removeChild(testScript);
        }, 100);
    });
    
    // Check known required resources based on HTML inspection
    const requiredResources = [
        { path: '/static/images/ai-editing.jpg', type: 'Image' },
        { path: '/static/images/onboarding/welcome.png', type: 'Image' },
        { path: '/static/images/onboarding/music.png', type: 'Image' },
        { path: '/mock-media/covers/track1.jpg', type: 'Image' }
    ];
    
    requiredResources.forEach(resource => {
        // Use Image object instead of fetch to check if images exist
        // This approach doesn't generate 404 errors in the console
        if (resource.type === 'Image') {
            const img = new Image();
            img.onload = () => {
                // Image loaded successfully
            };
            img.onerror = () => {
                logMissingResource(resource.path, resource.type);
            };
            img.src = resource.path;
        } else {
            // For non-image resources, use a custom method that suppresses errors
            checkResourceExists(resource.path)
                .then(exists => {
                    if (!exists) {
                        logMissingResource(resource.path, resource.type);
                    }
                });
        }
    });
    
    // Helper function to check if a resource exists without logging 404 errors
    function checkResourceExists(url) {
        return new Promise(resolve => {
            // Use XMLHttpRequest with a short timeout to reduce errors
            const xhr = new XMLHttpRequest();
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4) {
                    resolve(xhr.status === 200);
                }
            };
            xhr.onerror = function() {
                resolve(false);
            };
            xhr.ontimeout = function() {
                resolve(false);
            };
            try {
                xhr.open('HEAD', url, true);
                xhr.timeout = 1000; // 1 second timeout
                xhr.send();
            } catch (e) {
                resolve(false);
            }
        });
    }
    
    // If no missing resources found after checks
    setTimeout(() => {
        if (missingResources.length === 0 && missingResourcesContainer) {
            const logElement = document.createElement('div');
            logElement.className = 'debug-log success';
            logElement.textContent = 'No missing resources detected.';
            missingResourcesContainer.innerHTML = '';
            missingResourcesContainer.appendChild(logElement);
        }
    }, 2000);
}

/**
 * Monitor system metrics (memory usage, CPU, etc.)
 */
function monitorSystemMetrics() {
    const memoryUsageElement = document.getElementById('memoryUsage');
    const cpuUsageElement = document.getElementById('cpuUsage');
    
    // Function to fetch and update system metrics
    function updateSystemMetrics() {
        // Always use mock data - APIs don't exist
        const mockMemoryData = { usage: Math.floor(Math.random() * 500) + 200 };
        const mockCpuData = { usage: Math.floor(Math.random() * 80) + 10 };
        
        if (memoryUsageElement) {
            memoryUsageElement.textContent = `${mockMemoryData.usage} MB`;
        }
        
        if (cpuUsageElement) {
            cpuUsageElement.textContent = `${mockCpuData.usage}%`;
        }
    }
    
    // Update immediately and then every 5 seconds
    updateSystemMetrics();
    setInterval(updateSystemMetrics, 5000);
}

/**
 * Intercept and log API requests
 */
function interceptAPIRequests() {
    const apiLogsContainer = document.getElementById('apiLogs');
    
    // Clear initial message
    if (apiLogsContainer) {
        apiLogsContainer.innerHTML = '';
    }
    
    // Intercept fetch requests
    const originalFetch = window.fetch;
    window.fetch = async function(input, init) {
        const url = typeof input === 'string' ? input : input.url;
        
        // Skip intercepting API calls to debug endpoints to avoid endless loops
        if (url.includes('/api/debug/')) {
            return originalFetch.apply(this, arguments);
        }
        
        const startTime = performance.now();
        let status, statusText;
        
        try {
            const response = await originalFetch.apply(this, arguments);
            status = response.status;
            statusText = response.statusText;
            
            // Clone response for logging
            const clone = response.clone();
            clone.text().then(text => {
                let responseData = text;
                try {
                    // Try to parse as JSON if possible
                    responseData = JSON.parse(text);
                } catch (e) {
                    // Keep as text if not JSON
                }
                
                logAPIRequest(url, status, startTime, responseData);
            });
            
            return response;
        } catch (error) {
            status = 'Error';
            statusText = error.message;
            logAPIRequest(url, status, startTime, { error: error.message });
            throw error;
        }
    };
    
    // Log API request to debug panel
    function logAPIRequest(url, status, startTime, data) {
        const endTime = performance.now();
        const duration = (endTime - startTime).toFixed(2);
        
        // Skip logging static resources and debug API itself to avoid clutter
        if (url.match(/\.(css|js|png|jpg|svg|gif|ico|woff|woff2|ttf|eot)$/) || 
            url.includes('/api/debug/')) {
            return;
        }
        
        // Create log message
        let statusClass = 'success';
        if (status >= 400 || status === 'Error') {
            statusClass = 'error';
        } else if (status >= 300) {
            statusClass = 'warning';
        }
        
        addDebugLog(`${url} - ${status} (${duration}ms)`, statusClass, 'apiLogs');
    }
}

/**
 * Handle mock data generation
 */
function handleMockDataGeneration() {
    const generateMockTracksBtn = document.getElementById('generateMockTracks');
    const mockProcessingBtn = document.getElementById('mockProcessing');
    const clearMockDataBtn = document.getElementById('clearMockData');
    
    // Generate mock music tracks
    if (generateMockTracksBtn) {
        generateMockTracksBtn.addEventListener('click', function() {
            const mockTracks = generateMockTracks();
            localStorage.setItem('mockTracks', JSON.stringify(mockTracks));
            addDebugLog(`Generated ${mockTracks.length} mock tracks`, 'success', 'apiLogs');
            
            // Refresh page to show mock tracks
            if (confirm('Mock tracks generated. Refresh page to see them?')) {
                window.location.reload();
            }
        });
    }
    
    // Simulate video processing
    if (mockProcessingBtn) {
        mockProcessingBtn.addEventListener('click', function() {
            simulateVideoProcessing();
            addDebugLog('Simulating video processing...', 'info', 'apiLogs');
        });
    }
    
    // Clear mock data
    if (clearMockDataBtn) {
        clearMockDataBtn.addEventListener('click', function() {
            localStorage.removeItem('mockTracks');
            localStorage.removeItem('mockProcessing');
            addDebugLog('Mock data cleared', 'success', 'apiLogs');
            
            if (confirm('Mock data cleared. Refresh page?')) {
                window.location.reload();
            }
        });
    }
}

/**
 * Generate mock music tracks for development
 */
function generateMockTracks() {
    const genres = ['Pop', 'Electronic', 'Hip Hop', 'Rock', 'Ambient', 'Dance'];
    const artists = ['Electro Beats', 'Cloud 9', 'Urban Flow', 'Studio Vibes', 'Night Wave'];
    const tracks = [];
    
    for (let i = 1; i <= 15; i++) {
        const genre = genres[Math.floor(Math.random() * genres.length)];
        const artist = artists[Math.floor(Math.random() * artists.length)];
        const bpm = Math.floor(Math.random() * 60) + 90;
        const duration = `${Math.floor(Math.random() * 2) + 1}:${Math.floor(Math.random() * 60).toString().padStart(2, '0')}`;
        
        tracks.push({
            id: i,
            title: `Track ${i} - ${genre} Beat`,
            artist: artist,
            genre: genre,
            bpm: bpm,
            duration: duration,
            image_url: `/static/img/track${i % 5 + 1}.jpg`,
            url: `/static/sample_music/track${i % 5 + 1}.mp3`,
            track_name: `track${i}`,
            waveform_data: generateRandomWaveformData(50)
        });
    }
    
    return tracks;
}

/**
 * Generate random waveform data for visualization
 */
function generateRandomWaveformData(length) {
    const data = [];
    const baseline = Math.random() * 0.4 + 0.3; // Base amplitude between 0.3 and 0.7
    
    for (let i = 0; i < length; i++) {
        // Random value with a baseline trend and some noise
        let value = baseline + (Math.random() * 0.5 - 0.25);
        
        // Ensure value is between 0 and 1
        value = Math.max(0, Math.min(1, value));
        
        data.push(value);
    }
    
    return data;
}

/**
 * Simulate video processing with a modal
 */
function simulateVideoProcessing() {
    const processingDialog = document.getElementById('processingDialog');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const processingMessage = document.getElementById('processingMessage');
    
    if (!processingDialog || !progressFill || !progressText) return;
    
    // Show processing dialog
    processingDialog.style.display = 'flex';
    
    // Initialize progress
    let progress = 0;
    progressFill.style.width = '0%';
    progressText.textContent = '0%';
    
    // Simulate processing steps
    const interval = setInterval(() => {
        progress += Math.random() * 5;
        
        if (progress > 100) {
            progress = 100;
            clearInterval(interval);
            
            // Complete the process
            setTimeout(() => {
                processingDialog.style.display = 'none';
                alert('Video processing complete! This is a simulation.');
            }, 1000);
        }
        
        progressFill.style.width = `${progress}%`;
        progressText.textContent = `${Math.round(progress)}%`;
        
        // Update message based on progress
        if (progress < 30) {
            processingMessage.textContent = 'Preparing images...';
        } else if (progress < 60) {
            processingMessage.textContent = 'Adding music track...';
        } else if (progress < 90) {
            processingMessage.textContent = 'Generating YouTube Short...';
        } else {
            processingMessage.textContent = 'Finalizing your video...';
        }
    }, 300);
}

/**
 * Add a log entry to the debug panel
 */
function addDebugLog(message, type, containerId) {
    const logsContainer = document.getElementById(containerId);
    if (!logsContainer) return;
    
    // Create log element
    const logElement = document.createElement('div');
    logElement.className = `debug-log ${type || ''}`;
    
    // Add timestamp
    const now = new Date();
    const timestamp = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
    
    logElement.textContent = `[${timestamp}] ${message}`;
    
    // Add to container and scroll to bottom
    logsContainer.appendChild(logElement);
    logsContainer.scrollTop = logsContainer.scrollHeight;
    
    // Limit log entries to prevent overflow
    while (logsContainer.children.length > 50) {
        logsContainer.removeChild(logsContainer.firstChild);
    }
} 