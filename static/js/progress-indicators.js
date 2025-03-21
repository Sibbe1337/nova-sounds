/**
 * Progress Indicators
 * Helpers for managing progress bars, loaders, and status indicators
 */

// Track loading states globally
const loadingStates = {};

document.addEventListener('DOMContentLoaded', function() {
  // Initialize any progress bars with data attributes
  initProgressBars();
  
  // Initialize step indicators
  initProgressSteps();
});

/**
 * Initialize progress bars from data attributes
 */
function initProgressBars() {
  document.querySelectorAll('[data-progress]').forEach(element => {
    const value = parseInt(element.dataset.progress) || 0;
    const progressBar = element.querySelector('.progress-bar-fill');
    
    if (progressBar) {
      updateProgressBar(progressBar, value);
      
      // Update percentage label if it exists
      const percentageLabel = element.querySelector('.progress-percentage');
      if (percentageLabel) {
        percentageLabel.textContent = `${value}%`;
      }
    }
  });
}

/**
 * Initialize step progress indicators
 */
function initProgressSteps() {
  document.querySelectorAll('.progress-steps').forEach(stepsContainer => {
    const currentStep = parseInt(stepsContainer.dataset.step) || 1;
    
    // Mark steps as active or completed
    const steps = stepsContainer.querySelectorAll('.progress-step');
    steps.forEach((step, index) => {
      const stepNumber = index + 1;
      
      if (stepNumber < currentStep) {
        step.classList.add('completed');
        step.classList.remove('active');
        
        // Add check icon for completed steps
        const icon = step.querySelector('.progress-step-icon');
        if (icon) {
          icon.innerHTML = '<i class="fas fa-check"></i>';
        }
      } else if (stepNumber === currentStep) {
        step.classList.add('active');
        step.classList.remove('completed');
      } else {
        step.classList.remove('active', 'completed');
      }
    });
  });
}

/**
 * Update a progress bar to a specific value
 * 
 * @param {HTMLElement} progressBar - The progress bar element
 * @param {number} value - Progress value (0-100)
 * @param {string} status - Optional status (success, warning, danger)
 */
function updateProgressBar(progressBar, value, status = null) {
  // Ensure value is between 0-100
  value = Math.max(0, Math.min(100, value));
  
  // Set the width to the value
  progressBar.style.width = `${value}%`;
  
  // Set ARIA attributes for accessibility
  const progressContainer = progressBar.closest('.progress-bar');
  if (progressContainer) {
    progressContainer.setAttribute('aria-valuenow', value);
    progressContainer.setAttribute('aria-valuemin', 0);
    progressContainer.setAttribute('aria-valuemax', 100);
    
    // Remove existing status classes
    progressContainer.classList.remove('success', 'warning', 'danger');
    
    // Add status class if provided
    if (status) {
      progressContainer.classList.add(status);
    }
  }
}

/**
 * Progress Indicators Module
 * Provides visual feedback for loading and processing tasks
 */

/**
 * Show a loading indicator on a container
 * @param {string|Element} container - Container element or selector
 * @param {string} operation - Name of the operation
 * @param {Object} options - Additional options
 */
function showLoading(container, operation = 'default', options = {}) {
    const containerEl = typeof container === 'string' ? document.querySelector(container) : container;
    if (!containerEl) return false;
    
    // Set loading state
    const id = containerEl.id || `container-${Math.random().toString(36).substring(2, 9)}`;
    loadingStates[id] = { operation, startTime: Date.now(), ...options };
    
    // Create loader elements
    const loader = document.createElement('div');
    loader.className = `loader-overlay ${options.transparentBg ? 'transparent-bg' : ''}`;
    
    // Create loader content
    const loaderContent = document.createElement('div');
    loaderContent.className = 'loader-content';
    
    // Add spinner
    const spinner = document.createElement('div');
    spinner.className = `spinner ${options.spinnerType || 'pulse'}`;
    loaderContent.appendChild(spinner);
    
    // Add text if specified
    if (options.text) {
        const text = document.createElement('div');
        text.className = 'loader-text';
        text.textContent = options.text;
        loaderContent.appendChild(text);
    }
    
    // Add progress bar if requested
    if (options.showProgress) {
        const progressContainer = document.createElement('div');
        progressContainer.className = 'progress-container';
        
        const progressBar = document.createElement('div');
        progressBar.className = 'progress-bar';
        progressBar.style.width = '0%';
        
        const progressText = document.createElement('div');
        progressText.className = 'progress-text';
        progressText.textContent = '0%';
        
        progressContainer.appendChild(progressBar);
        progressContainer.appendChild(progressText);
        loaderContent.appendChild(progressContainer);
    }
    
    // Insert into DOM
    loader.appendChild(loaderContent);
    
    // Set position property to relative if it's not already positioned
    const containerPosition = window.getComputedStyle(containerEl).position;
    if (containerPosition === 'static') {
        containerEl.style.position = 'relative';
    }
    
    // Add to container
    containerEl.appendChild(loader);
    containerEl.classList.add('is-loading');
    
    // Check if container already has a loader
    const existingLoader = containerEl.querySelector('.loader-overlay');
    if (existingLoader && existingLoader !== loader) {
        existingLoader.remove();
    }
    
    // Return the loader element for future reference
    return loader;
}

/**
 * Update progress for a loading operation
 * @param {string|Element} container - Container element or selector
 * @param {number} progress - Progress value (0-100)
 * @param {string} text - Optional text to display
 */
function updateProgress(container, progress, text = null) {
    const containerEl = typeof container === 'string' ? document.querySelector(container) : container;
    if (!containerEl) return false;
    
    const progressBar = containerEl.querySelector('.progress-bar');
    const progressText = containerEl.querySelector('.progress-text');
    
    if (progressBar) {
        progressBar.style.width = `${progress}%`;
    }
    
    if (progressText) {
        progressText.textContent = `${Math.round(progress)}%`;
    }
    
    if (text && containerEl.querySelector('.loader-text')) {
        containerEl.querySelector('.loader-text').textContent = text;
    }
    
    return true;
}

/**
 * Hide loading indicator from a container
 * @param {string|Element} container - Container element or selector
 * @param {Object} options - Additional options
 */
function hideLoading(container, options = {}) {
    const containerEl = typeof container === 'string' ? document.querySelector(container) : container;
    if (!containerEl) return false;
    
    // Get loader element
    const loader = containerEl.querySelector('.loader-overlay');
    if (!loader) return false;
    
    // Add fade-out animation
    if (options.fadeOut !== false) {
        loader.classList.add('fade-out');
        // Remove after animation
        setTimeout(() => {
            loader.remove();
            containerEl.classList.remove('is-loading');
            
            // Restore position if we modified it
            if (containerEl.style.position === 'relative' && !options.keepRelative) {
                containerEl.style.position = '';
            }
        }, 300);
    } else {
        // Remove immediately
        loader.remove();
        containerEl.classList.remove('is-loading');
        
        // Restore position if we modified it
        if (containerEl.style.position === 'relative' && !options.keepRelative) {
            containerEl.style.position = '';
        }
    }
    
    // Clear loading state
    const id = containerEl.id || null;
    if (id && loadingStates[id]) {
        delete loadingStates[id];
    }
    
    return true;
}

/**
 * Create a standalone progress tracker
 * @param {Object} options - Configuration options
 * @returns {Object} - Progress controller
 */
function createProgressTracker(options = {}) {
    const defaultOptions = {
        container: document.body,
        title: 'Processing...',
        steps: [],
        showPercentage: true,
        autoStart: false,
        theme: 'light',
        position: 'bottom-right'
    };
    
    const config = { ...defaultOptions, ...options };
    
    // Create tracker element
    const trackerEl = document.createElement('div');
    trackerEl.className = `progress-tracker ${config.theme} ${config.position}`;
    
    // Create header
    const header = document.createElement('div');
    header.className = 'tracker-header';
    
    const titleEl = document.createElement('div');
    titleEl.className = 'tracker-title';
    titleEl.textContent = config.title;
    header.appendChild(titleEl);
    
    const closeBtn = document.createElement('button');
    closeBtn.className = 'tracker-close';
    closeBtn.innerHTML = '&times;';
    header.appendChild(closeBtn);
    
    trackerEl.appendChild(header);
    
    // Create progress bar
    const progressContainer = document.createElement('div');
    progressContainer.className = 'tracker-progress-container';
    
    const progressBar = document.createElement('div');
    progressBar.className = 'tracker-progress-bar';
    progressBar.style.width = '0%';
    progressContainer.appendChild(progressBar);
    
    trackerEl.appendChild(progressContainer);
    
    // Create steps list if steps are provided
    if (config.steps && config.steps.length > 0) {
        const stepsList = document.createElement('ul');
        stepsList.className = 'tracker-steps';
        
        config.steps.forEach((step, index) => {
            const stepItem = document.createElement('li');
            stepItem.className = 'tracker-step';
            stepItem.dataset.step = index;
            
            const stepIcon = document.createElement('span');
            stepIcon.className = 'step-icon';
            stepIcon.innerHTML = '<i class="fas fa-circle"></i>';
            stepItem.appendChild(stepIcon);
            
            const stepText = document.createElement('span');
            stepText.className = 'step-text';
            stepText.textContent = step;
            stepItem.appendChild(stepText);
            
            stepsList.appendChild(stepItem);
        });
        
        trackerEl.appendChild(stepsList);
    }
    
    // Create status text
    const statusEl = document.createElement('div');
    statusEl.className = 'tracker-status';
    statusEl.innerHTML = config.showPercentage ? '0%' : '&nbsp;';
    trackerEl.appendChild(statusEl);
    
    // Append to container
    if (typeof config.container === 'string') {
        config.container = document.querySelector(config.container);
    }
    
    config.container.appendChild(trackerEl);
    
    // State variables
    let currentProgress = 0;
    let currentStep = -1;
    let isRunning = false;
    
    // Event listeners
    closeBtn.addEventListener('click', () => {
        hideTracker();
    });
    
    // Methods
    function updateProgress(progress, stepMessage = null) {
        currentProgress = Math.min(Math.max(progress, 0), 100);
        progressBar.style.width = `${currentProgress}%`;
        
        if (config.showPercentage) {
            statusEl.textContent = `${Math.round(currentProgress)}%`;
        }
        
        if (stepMessage) {
            statusEl.textContent = stepMessage;
        }
        
        return true;
    }
    
    function nextStep() {
        if (currentStep < config.steps.length - 1) {
            currentStep++;
            
            // Update UI to reflect current step
            const steps = trackerEl.querySelectorAll('.tracker-step');
            steps.forEach((step, index) => {
                if (index < currentStep) {
                    step.classList.add('completed');
                    step.classList.remove('current');
                } else if (index === currentStep) {
                    step.classList.add('current');
                    step.classList.remove('completed');
                } else {
                    step.classList.remove('completed', 'current');
                }
            });
            
            // Update status text
            if (!config.showPercentage && currentStep >= 0 && currentStep < config.steps.length) {
                statusEl.textContent = config.steps[currentStep];
            }
            
            // Calculate progress based on steps
            const stepProgress = ((currentStep + 1) / config.steps.length) * 100;
            updateProgress(stepProgress);
        }
        
        return currentStep;
    }
    
    function start() {
        if (!isRunning) {
            isRunning = true;
            trackerEl.classList.add('active');
            
            if (config.steps && config.steps.length > 0) {
                nextStep();
            } else {
                updateProgress(0);
            }
        }
        
        return true;
    }
    
    function complete(message = 'Completed') {
        isRunning = false;
        updateProgress(100);
        statusEl.textContent = message;
        trackerEl.classList.add('completed');
        
        // Auto-hide after delay if requested
        if (config.autoHide) {
            setTimeout(hideTracker, config.autoHideDelay || 2000);
        }
        
        return true;
    }
    
    function hideTracker() {
        trackerEl.classList.add('fade-out');
        
        setTimeout(() => {
            if (trackerEl.parentNode) {
                trackerEl.parentNode.removeChild(trackerEl);
            }
        }, 300);
        
        return true;
    }
    
    // Auto-start if specified
    if (config.autoStart) {
        start();
    }
    
    // Return controller
    return {
        element: trackerEl,
        updateProgress,
        nextStep,
        start,
        complete,
        hide: hideTracker
    };
}

// Export functions to global scope
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.updateProgress = updateProgress;
window.createProgressTracker = createProgressTracker; 