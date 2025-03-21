/**
 * Debug Toolbar
 * Controls the debug toolbar UI and functionality
 */

// Initialize the debug toolbar when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeDebugToolbar();
});

/**
 * Initialize the debug toolbar
 */
function initializeDebugToolbar() {
    // Get toolbar elements
    const toolbar = document.getElementById('debugToolbar');
    const showButton = document.getElementById('showDebugToolbar');
    const toggleButton = document.getElementById('toggleDebugToolbar');
    
    // Toolbar state from localStorage
    const isToolbarActive = localStorage.getItem('debugToolbarActive') === 'true';
    
    // Setup toolbar state
    if (isToolbarActive && toolbar) {
        toolbar.classList.add('active');
    }
    
    // Setup event listeners for toggling toolbar
    if (showButton) {
        showButton.addEventListener('click', function() {
            toggleToolbar(true);
        });
    }
    
    if (toggleButton) {
        toggleButton.addEventListener('click', function() {
            toggleToolbar();
        });
    }
    
    // Setup interactive elements
    setupToggleSwitches();
    setupActionButtons();
    setupPerformanceMetrics();
    
    // Initial connection check
    checkAPIConnection();
}

/**
 * Toggle the toolbar visibility
 * @param {boolean} show Force show the toolbar
 */
function toggleToolbar(show = null) {
    const toolbar = document.getElementById('debugToolbar');
    if (!toolbar) return;
    
    if (show === true) {
        toolbar.classList.add('active');
        localStorage.setItem('debugToolbarActive', 'true');
    } else if (show === false) {
        toolbar.classList.remove('active');
        localStorage.setItem('debugToolbarActive', 'false');
    } else {
        toolbar.classList.toggle('active');
        localStorage.setItem('debugToolbarActive', toolbar.classList.contains('active').toString());
    }
    
    // Update toggle button direction
    const toggleIcon = toolbar.querySelector('.debug-toolbar-toggle i');
    if (toggleIcon) {
        if (toolbar.classList.contains('active')) {
            toggleIcon.className = 'fas fa-chevron-right';
        } else {
            toggleIcon.className = 'fas fa-chevron-left';
        }
    }
}

/**
 * Setup toggle switches in the toolbar
 */
function setupToggleSwitches() {
    // Mock API toggle
    const mockApiToggle = document.getElementById('mockApiToggle');
    if (mockApiToggle) {
        mockApiToggle.checked = localStorage.getItem('mockApi') === 'true';
        mockApiToggle.addEventListener('change', function() {
            localStorage.setItem('mockApi', this.checked.toString());
            
            // Show notification about setting change
            if (window.Notifications) {
                window.Notifications.info(
                    `Mock API ${this.checked ? 'enabled' : 'disabled'}`,
                    {
                        title: 'Debug Setting Changed',
                        duration: 3000
                    }
                );
            }
        });
    }
    
    // Mock Authentication toggle
    const mockAuthToggle = document.getElementById('mockAuthToggle');
    if (mockAuthToggle) {
        mockAuthToggle.checked = localStorage.getItem('mockAuth') === 'true';
        mockAuthToggle.addEventListener('change', function() {
            localStorage.setItem('mockAuth', this.checked.toString());
            
            // Show notification about setting change
            if (window.Notifications) {
                window.Notifications.info(
                    `Mock Authentication ${this.checked ? 'enabled' : 'disabled'}`,
                    {
                        title: 'Debug Setting Changed',
                        duration: 3000
                    }
                );
            }
        });
    }
}

/**
 * Setup action buttons in the toolbar
 */
function setupActionButtons() {
    // Clear cache button
    const clearCacheBtn = document.getElementById('clearCacheBtn');
    if (clearCacheBtn) {
        clearCacheBtn.addEventListener('click', function() {
            // Clear localStorage (except debug toolbar state)
            const toolbarState = localStorage.getItem('debugToolbarActive');
            localStorage.clear();
            localStorage.setItem('debugToolbarActive', toolbarState);
            
            // Show notification
            if (window.Notifications) {
                window.Notifications.success(
                    'Local storage cache cleared',
                    {
                        title: 'Cache Cleared',
                        duration: 3000
                    }
                );
            }
        });
    }
    
    // Reset session button
    const resetSessionBtn = document.getElementById('resetSessionBtn');
    if (resetSessionBtn) {
        resetSessionBtn.addEventListener('click', function() {
            // Clear all cookies
            document.cookie.split(';').forEach(function(c) {
                document.cookie = c.trim().split('=')[0] + '=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;';
            });
            
            // Show notification
            if (window.Notifications) {
                window.Notifications.success(
                    'Session reset complete',
                    {
                        title: 'Session Reset',
                        duration: 3000
                    }
                );
            }
            
            // Reload page after a short delay
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        });
    }
    
    // Test error button
    const testErrorBtn = document.getElementById('testErrorBtn');
    if (testErrorBtn) {
        testErrorBtn.addEventListener('click', function() {
            // Show error notification
            if (window.Notifications) {
                window.Notifications.error(
                    'This is a test error notification',
                    {
                        title: 'Test Error',
                        duration: 5000
                    }
                );
            }
            
            // Log test error to console
            console.error('Test error triggered from debug toolbar');
        });
    }
}

/**
 * Setup performance metrics in the toolbar
 */
function setupPerformanceMetrics() {
    // Memory usage
    updateMemoryUsage();
    
    // CPU usage (simulated for demo)
    updateCPUUsage();
    
    // Refresh button
    const refreshPerformanceBtn = document.getElementById('refreshPerformanceBtn');
    if (refreshPerformanceBtn) {
        refreshPerformanceBtn.addEventListener('click', function() {
            updateMemoryUsage();
            updateCPUUsage();
            
            // Show small success indicator
            this.classList.add('refreshing');
            setTimeout(() => {
                this.classList.remove('refreshing');
            }, 500);
        });
    }
}

/**
 * Update memory usage display
 */
function updateMemoryUsage() {
    const memoryElement = document.getElementById('memoryUsage');
    const memoryProgress = document.querySelector('.memory-progress .progress-bar-fill');
    
    if (!memoryElement || !memoryProgress) return;
    
    // Try to get actual memory usage if available
    if (performance && performance.memory) {
        const used = Math.round(performance.memory.usedJSHeapSize / 1048576);
        const total = Math.round(performance.memory.jsHeapSizeLimit / 1048576);
        const percent = Math.min(100, Math.round((used / total) * 100));
        
        memoryElement.textContent = `${used} MB / ${total} MB (${percent}%)`;
        memoryProgress.style.width = `${percent}%`;
        
        // Set color based on usage
        if (percent > 80) {
            memoryProgress.className = 'progress-bar-fill error';
        } else if (percent > 60) {
            memoryProgress.className = 'progress-bar-fill warning';
        } else {
            memoryProgress.className = 'progress-bar-fill success';
        }
    } else {
        // Fallback to simulated data
        const used = Math.floor(Math.random() * 500) + 200;
        const total = 1024;
        const percent = Math.round((used / total) * 100);
        
        memoryElement.textContent = `${used} MB / ${total} MB (${percent}%)`;
        memoryProgress.style.width = `${percent}%`;
        
        // Set color based on usage
        if (percent > 80) {
            memoryProgress.className = 'progress-bar-fill error';
        } else if (percent > 60) {
            memoryProgress.className = 'progress-bar-fill warning';
        } else {
            memoryProgress.className = 'progress-bar-fill success';
        }
    }
}

/**
 * Update CPU usage display (simulated)
 */
function updateCPUUsage() {
    const cpuElement = document.getElementById('cpuUsage');
    const cpuProgress = document.querySelector('.cpu-progress .progress-bar-fill');
    
    if (!cpuElement || !cpuProgress) return;
    
    // Simulate CPU usage for demo purposes
    const cpuPercent = Math.floor(Math.random() * 60) + 10;
    
    cpuElement.textContent = `${cpuPercent}%`;
    cpuProgress.style.width = `${cpuPercent}%`;
    
    // Set color based on usage
    if (cpuPercent > 80) {
        cpuProgress.className = 'progress-bar-fill error';
    } else if (cpuPercent > 60) {
        cpuProgress.className = 'progress-bar-fill warning';
    } else {
        cpuProgress.className = 'progress-bar-fill success';
    }
}

/**
 * Check API connection status
 */
function checkAPIConnection() {
    // API status indicator
    const apiStatusElement = document.querySelector('.debug-info-value:has(.status-dot)');
    
    if (!apiStatusElement) return;
    
    // Try to make a request to the API health endpoint
    fetch('/health')
        .then(response => {
            if (response.ok) {
                // API is connected
                apiStatusElement.innerHTML = '<span class="status-dot success"></span> Connected';
            } else {
                // API returned error
                apiStatusElement.innerHTML = '<span class="status-dot error"></span> Error';
            }
        })
        .catch(error => {
            // API connection failed
            apiStatusElement.innerHTML = '<span class="status-dot error"></span> Disconnected';
            console.error('API connection check failed:', error);
        });
} 