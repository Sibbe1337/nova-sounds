/**
 * Debug Toolbar
 * Real-time debugging tools for development mode
 */

document.addEventListener('DOMContentLoaded', function() {
  // Initialize debug toolbar
  initDebugToolbar();
  
  // Update performance metrics
  updatePerformanceMetrics();
  
  // Add event listeners for debug actions
  initDebugActions();
});

/**
 * Initialize debug toolbar visibility
 */
function initDebugToolbar() {
  const debugToolbar = document.getElementById('debugToolbar');
  const showDebugToolbarBtn = document.getElementById('showDebugToolbar');
  const toggleDebugToolbarBtn = document.getElementById('toggleDebugToolbar');
  
  // Only continue if we found the toolbar (it might not be present in production)
  if (!debugToolbar || !showDebugToolbarBtn || !toggleDebugToolbarBtn) return;
  
  // Check for saved state in local storage
  const toolbarVisible = localStorage.getItem('debugToolbarVisible') === 'true';
  if (toolbarVisible) {
    debugToolbar.classList.add('active');
  }
  
  // Toggle toolbar when clicking the button
  toggleDebugToolbarBtn.addEventListener('click', function() {
    debugToolbar.classList.toggle('active');
    const isVisible = debugToolbar.classList.contains('active');
    localStorage.setItem('debugToolbarVisible', isVisible);
  });
  
  // Show toolbar when clicking the fab button
  showDebugToolbarBtn.addEventListener('click', function() {
    debugToolbar.classList.add('active');
    localStorage.setItem('debugToolbarVisible', 'true');
  });
}

/**
 * Update performance metrics in real-time
 */
function updatePerformanceMetrics() {
  // Only run if debug toolbar is present
  const debugToolbar = document.getElementById('debugToolbar');
  if (!debugToolbar) return;
  
  // Set up memory usage tracking
  const memoryElement = document.getElementById('memoryUsage');
  const memoryProgressBar = document.querySelector('.memory-progress .progress-bar-fill');
  
  // Set up CPU usage tracking
  const cpuElement = document.getElementById('cpuUsage');
  const cpuProgressBar = document.querySelector('.cpu-progress .progress-bar-fill');
  
  /**
   * Fetch memory usage from API
   */
  function updateMemoryUsage() {
    // Always use mock data since API doesn't exist
    const mockMemoryPercent = Math.floor(Math.random() * 40) + 30;
    
    if (memoryElement) {
      // Update text display
      memoryElement.textContent = `${mockMemoryPercent.toFixed(2)}% (mock)`;
      
      // Update progress bar
      if (memoryProgressBar) {
        memoryProgressBar.style.width = `${mockMemoryPercent}%`;
        
        // Update color based on usage
        memoryProgressBar.classList.remove('success', 'warning', 'danger');
        if (mockMemoryPercent < 50) {
          memoryProgressBar.classList.add('success');
        } else if (mockMemoryPercent < 80) {
          memoryProgressBar.classList.add('warning');
        } else {
          memoryProgressBar.classList.add('danger');
        }
      }
    }
  }
  
  /**
   * Fetch CPU usage from API
   */
  function updateCpuUsage() {
    // Always use mock data since API doesn't exist
    const mockCpuPercent = Math.floor(Math.random() * 40) + 20;
    
    if (cpuElement) {
      // Update text display
      cpuElement.textContent = `${mockCpuPercent.toFixed(2)}% (mock)`;
      
      // Update progress bar
      if (cpuProgressBar) {
        cpuProgressBar.style.width = `${mockCpuPercent}%`;
        
        // Update color based on usage
        cpuProgressBar.classList.remove('success', 'warning', 'danger');
        if (mockCpuPercent < 40) {
          cpuProgressBar.classList.add('success');
        } else if (mockCpuPercent < 70) {
          cpuProgressBar.classList.add('warning');
        } else {
          cpuProgressBar.classList.add('danger');
        }
      }
    }
  }
  
  // Initial update
  updateMemoryUsage();
  updateCpuUsage();
  
  // Set up interval to update metrics (every 5 seconds)
  setInterval(() => {
    updateMemoryUsage();
    updateCpuUsage();
  }, 5000);
}

/**
 * Initialize debug action buttons
 */
function initDebugActions() {
  // Only run if debug toolbar is present
  const debugToolbar = document.getElementById('debugToolbar');
  if (!debugToolbar) return;
  
  // Add error handling for API endpoints
  const handleApiError = (endpoint, error) => {
    console.warn(`Debug API error for ${endpoint}:`, error);
    // Check if it's a 500 error
    if (error.message && error.message.includes('500')) {
      console.warn(`Server returned 500 error for ${endpoint}. This is expected in development mode if the endpoint isn't implemented.`);
    }
    
    // Show in the UI if needed
    const apiLogsContainer = document.getElementById('apiLogs');
    if (apiLogsContainer) {
      const logElement = document.createElement('div');
      logElement.className = 'debug-log error';
      logElement.textContent = `API Error (${endpoint}): ${error.message || 'Unknown error'}`;
      apiLogsContainer.appendChild(logElement);
    }
  };
  
  // Clear cache button
  const clearCacheBtn = document.getElementById('clearCacheBtn');
  if (clearCacheBtn) {
    clearCacheBtn.addEventListener('click', function() {
      fetch('/api/debug/clear-cache')
        .then(response => {
          if (!response.ok) {
            throw new Error(`API returned ${response.status} ${response.statusText}`);
          }
          return response.json();
        })
        .then(data => {
          if (data.status === 'success') {
            // Show success notification if available
            if (window.showSuccess) {
              window.showSuccess('Cache cleared successfully');
            } else {
              alert('Cache cleared successfully');
            }
          } else {
            throw new Error(data.message || 'Unknown error');
          }
        })
        .catch(error => {
          handleApiError('/api/debug/clear-cache', error);
          // Show error notification if available
          if (window.showError) {
            window.showError(`Failed to clear cache: ${error.message}`);
          } else {
            alert(`Failed to clear cache: ${error.message}`);
          }
        });
    });
  }
  
  // Reset session button
  const resetSessionBtn = document.getElementById('resetSessionBtn');
  if (resetSessionBtn) {
    resetSessionBtn.addEventListener('click', function() {
      fetch('/api/debug/session/reset')
        .then(response => {
          if (!response.ok) {
            throw new Error(`API returned ${response.status} ${response.statusText}`);
          }
          return response.json();
        })
        .then(data => {
          if (data.status === 'success') {
            // Show success notification if available
            if (window.showSuccess) {
              window.showSuccess('Session reset successfully');
            } else {
              alert('Session reset successfully');
            }
          } else {
            throw new Error(data.message || 'Unknown error');
          }
        })
        .catch(error => {
          console.error('Error resetting session:', error);
          // Show error notification if available
          if (window.showError) {
            window.showError(`Failed to reset session: ${error.message}`);
          } else {
            alert(`Failed to reset session: ${error.message}`);
          }
        });
    });
  }
  
  // Test error button
  const testErrorBtn = document.getElementById('testErrorBtn');
  if (testErrorBtn) {
    testErrorBtn.addEventListener('click', function() {
      fetch('/api/debug/error/test')
        .catch(error => {
          console.error('Error response (expected):', error);
          // Show error notification if available
          if (window.showError) {
            window.showError('Test error triggered successfully');
          } else {
            alert('Test error triggered successfully');
          }
        });
    });
  }
  
  // Toggle mock API button
  const mockApiToggle = document.getElementById('mockApiToggle');
  if (mockApiToggle) {
    // Check for saved state in local storage
    const mockApiEnabled = localStorage.getItem('mockApiEnabled') === 'true';
    mockApiToggle.checked = mockApiEnabled;
    
    mockApiToggle.addEventListener('change', function() {
      const isEnabled = mockApiToggle.checked;
      localStorage.setItem('mockApiEnabled', isEnabled);
      
      // Show notification of change
      if (window.showInfo) {
        window.showInfo(`Mock API ${isEnabled ? 'enabled' : 'disabled'}`);
      }
    });
  }
  
  // Toggle mock auth button
  const mockAuthToggle = document.getElementById('mockAuthToggle');
  if (mockAuthToggle) {
    // Check for saved state in local storage
    const mockAuthEnabled = localStorage.getItem('mockAuthEnabled') === 'true';
    mockAuthToggle.checked = mockAuthEnabled;
    
    mockAuthToggle.addEventListener('change', function() {
      const isEnabled = mockAuthToggle.checked;
      localStorage.setItem('mockAuthEnabled', isEnabled);
      
      // Show notification of change
      if (window.showInfo) {
        window.showInfo(`Mock Authentication ${isEnabled ? 'enabled' : 'disabled'}`);
      }
    });
  }

  // Performance refresh button
  const refreshPerformanceBtn = document.getElementById('refreshPerformanceBtn');
  if (refreshPerformanceBtn) {
    refreshPerformanceBtn.addEventListener('click', function() {
      // Show a loading indicator in the button
      this.classList.add('loading');
      
      // Refresh both memory and CPU data
      Promise.all([
        fetch('/api/debug/memory').then(res => res.ok ? res.json() : Promise.reject('Memory fetch failed')),
        fetch('/api/debug/cpu').then(res => res.ok ? res.json() : Promise.reject('CPU fetch failed'))
      ])
      .then(([memoryData, cpuData]) => {
        // Update memory
        if (memoryElement && memoryData) {
          const memoryPercent = parseFloat(memoryData.system.percent.replace('%', ''));
          memoryElement.textContent = `${memoryPercent.toFixed(2)}%`;
          
          if (memoryProgressBar) {
            memoryProgressBar.style.width = `${memoryPercent}%`;
            memoryProgressBar.classList.remove('success', 'warning', 'danger');
            if (memoryPercent < 50) {
              memoryProgressBar.classList.add('success');
            } else if (memoryPercent < 80) {
              memoryProgressBar.classList.add('warning');
            } else {
              memoryProgressBar.classList.add('danger');
            }
          }
        }
        
        // Update CPU
        if (cpuElement && cpuData) {
          const cpuPercent = parseFloat(cpuData.system.percent.replace('%', ''));
          cpuElement.textContent = `${cpuPercent.toFixed(2)}%`;
          
          if (cpuProgressBar) {
            cpuProgressBar.style.width = `${cpuPercent}%`;
            cpuProgressBar.classList.remove('success', 'warning', 'danger');
            if (cpuPercent < 40) {
              cpuProgressBar.classList.add('success');
            } else if (cpuPercent < 70) {
              cpuProgressBar.classList.add('warning');
            } else {
              cpuProgressBar.classList.add('danger');
            }
          }
        }
        
        // Show success notification
        if (window.showSuccess) {
          window.showSuccess('Performance data refreshed');
        }
      })
      .catch(error => {
        console.error('Error refreshing performance data:', error);
        if (window.showError) {
          window.showError('Failed to refresh performance data');
        }
      })
      .finally(() => {
        // Remove loading indicator
        this.classList.remove('loading');
      });
    });
  }
}

// Expose public API for debugging features
window.DebugTools = {
  triggerError: function(message) {
    try {
      throw new Error(message || 'Manually triggered error');
    } catch (error) {
      console.error('Debug error:', error);
      if (window.showError) {
        window.showError(`Debug error: ${error.message}`);
      }
      return error;
    }
  },
  
  getSystemInfo: function() {
    return {
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      screenSize: `${window.innerWidth}x${window.innerHeight}`,
      language: navigator.language,
      darkMode: window.matchMedia('(prefers-color-scheme: dark)').matches,
    };
  },
  
  toggleDebugMode: function() {
    const toolbar = document.getElementById('debugToolbar');
    if (toolbar) {
      toolbar.classList.toggle('active');
      localStorage.setItem('debugToolbarVisible', toolbar.classList.contains('active'));
    }
  }
}; 