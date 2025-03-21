/**
 * Progress Tracker for Video Processing
 * Monitors the status of video processing and updates the UI
 */
class ProgressTracker {
    /**
     * Initialize progress tracker
     * @param {Object} options Configuration options
     * @param {string} options.videoId ID of the video being processed
     * @param {number} options.pollingInterval Interval in ms to poll for updates (default: 2000)
     * @param {Function} options.onStatusChange Callback when status changes (optional)
     */
    constructor(options = {}) {
        // Configuration
        this.videoId = options.videoId;
        this.pollingInterval = options.pollingInterval || 2000;
        this.onStatusChange = options.onStatusChange || null;
        this.apiUrl = options.apiUrl || '/api/videos/';
        
        // State
        this.isPolling = false;
        this.pollingTimer = null;
        this.currentStatus = null;
        this.currentProgress = 0;
        this.currentStep = 'prepare';
        
        // DOM Elements
        this.progressBar = document.getElementById('processingProgressBar');
        this.statusText = document.getElementById('processingStatus');
        this.percentageText = document.getElementById('processingPercentage');
        this.progressSteps = document.querySelectorAll('.progress-step');
        
        if (!this.videoId) {
            console.error('Video ID is required for progress tracking');
        }
    }
    
    /**
     * Start polling for progress updates
     */
    start() {
        if (this.isPolling) return;
        
        this.isPolling = true;
        this._poll();
        
        // Set up regular polling
        this.pollingTimer = setInterval(() => {
            this._poll();
        }, this.pollingInterval);
    }
    
    /**
     * Stop polling for progress updates
     */
    stop() {
        this.isPolling = false;
        
        if (this.pollingTimer) {
            clearInterval(this.pollingTimer);
            this.pollingTimer = null;
        }
    }
    
    /**
     * Poll for video status
     * @private
     */
    _poll() {
        if (!this.isPolling) return;
        
        fetch(`${this.apiUrl}${this.videoId}`)
            .then(response => response.json())
            .then(data => {
                const videoData = data.video || {};
                
                // Get status
                const status = videoData.status || 'processing';
                
                // Check for status change
                if (status !== this.currentStatus) {
                    this.currentStatus = status;
                    
                    // Notify listeners
                    if (typeof this.onStatusChange === 'function') {
                        this.onStatusChange(status);
                    }
                    
                    // If processing is complete, stop polling
                    if (status !== 'processing') {
                        this.stop();
                    }
                }
                
                // Update progress if processing
                if (status === 'processing') {
                    this._updateProgress(videoData);
                }
            })
            .catch(error => {
                console.error('Error polling for video status:', error);
            });
    }
    
    /**
     * Update progress UI
     * @param {Object} videoData Video data from API
     * @private
     */
    _updateProgress(videoData) {
        // Get progress details
        const progress = videoData.progress || {};
        const percentage = progress.percentage || this._calculateFakeProgress();
        const step = progress.step || this._estimateStep(percentage);
        const message = progress.message || this._getStepMessage(step);
        
        // Update state
        this.currentProgress = percentage;
        this.currentStep = step;
        
        // Update UI
        if (this.progressBar) {
            this.progressBar.style.width = `${percentage}%`;
        }
        
        if (this.statusText) {
            this.statusText.textContent = message;
        }
        
        if (this.percentageText) {
            this.percentageText.textContent = `${Math.round(percentage)}%`;
        }
        
        // Update steps
        this._updateSteps(step);
    }
    
    /**
     * Calculate fake progress for demo purposes
     * @returns {number} Progress percentage
     * @private
     */
    _calculateFakeProgress() {
        // Simulate progress between 0-95% (we'll hit 100% when status actually changes)
        // Makes progress appear to move even without real updates
        if (this.currentProgress < 95) {
            // Move faster at the beginning, slower as we approach 95%
            const increment = Math.max(0.5, (95 - this.currentProgress) / 20);
            return this.currentProgress + increment;
        }
        
        return this.currentProgress;
    }
    
    /**
     * Estimate current step based on progress percentage
     * @param {number} percentage Progress percentage
     * @returns {string} Step identifier
     * @private
     */
    _estimateStep(percentage) {
        if (percentage < 25) return 'prepare';
        if (percentage < 65) return 'process';
        if (percentage < 85) return 'optimize';
        return 'finalize';
    }
    
    /**
     * Get message for current step
     * @param {string} step Step identifier
     * @returns {string} Step message
     * @private
     */
    _getStepMessage(step) {
        switch (step) {
            case 'prepare':
                return 'Preparing assets for video creation...';
            case 'process':
                return 'Processing video with selected music...';
            case 'optimize':
                return 'Optimizing video quality...';
            case 'finalize':
                return 'Finalizing video...';
            default:
                return 'Processing video...';
        }
    }
    
    /**
     * Update progress steps in UI
     * @param {string} currentStep Current step identifier
     * @private
     */
    _updateSteps(currentStep) {
        if (!this.progressSteps || !this.progressSteps.length) return;
        
        const steps = ['prepare', 'process', 'optimize', 'finalize'];
        const currentIndex = steps.indexOf(currentStep);
        
        this.progressSteps.forEach(step => {
            const stepId = step.getAttribute('data-step');
            const stepIndex = steps.indexOf(stepId);
            
            // Remove all classes
            step.classList.remove('active', 'completed');
            
            // Add appropriate class
            if (stepIndex < currentIndex) {
                step.classList.add('completed');
            } else if (stepIndex === currentIndex) {
                step.classList.add('active');
            }
        });
    }
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ProgressTracker;
} 