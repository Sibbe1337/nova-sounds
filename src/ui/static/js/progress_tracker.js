// Real-Time Progress Tracker
// Visualizes Celery task progress in real-time

class ProgressTracker {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.socket = null;
        this.taskId = null;
        this.status = 'idle'; // idle, pending, running, success, failed
        this.pollingInterval = null;
        this.pollingDelay = 2000; // ms between polls
        this.retryCount = 0;
        this.maxRetries = 3;
        this.progressData = {
            current: 0,
            total: 100,
            message: '',
            steps: []
        };
        
        // Default options
        this.options = {
            showDetailedSteps: true,
            showPercentage: true,
            autoHide: false,
            pollInterval: 2000, // ms
            autoStartPolling: true,
            enableWebsocket: false,
            showElapsedTime: true,
            showEstimatedTime: true,
            statusEndpoint: '/api/tasks/status/',
            onStatusChange: null,
            onComplete: null,
            ...options
        };
        
        // Set polling delay from options
        if (this.options.pollInterval) {
            this.pollingDelay = this.options.pollInterval;
        }
        
        // Bind methods
        this.pollTaskStatus = this.pollTaskStatus.bind(this);
        this.handleWebSocketMessage = this.handleWebSocketMessage.bind(this);
        
        // Initialize UI
        this.initialize();
    }
    
    initialize() {
        if (!this.container) {
            console.error(`Container element with ID "${this.containerId}" not found`);
            return;
        }
        
        // Create tracker UI
        this.createUI();
        
        // Set initial state
        this.updateUI();
    }
    
    createUI() {
        this.container.innerHTML = `
            <div class="progress-tracker-container">
                <div class="progress-header d-flex justify-content-between align-items-center mb-2">
                    <div class="progress-status">
                        <span class="status-label badge bg-secondary">Idle</span>
                        <span class="task-message ms-2 small"></span>
                    </div>
                    <div class="progress-time small text-muted">
                        <span class="elapsed-time d-none">Elapsed: <span class="elapsed-value">00:00</span></span>
                        <span class="estimated-time d-none ms-2">ETA: <span class="eta-value">00:00</span></span>
                    </div>
                </div>
                
                <div class="progress mb-2" style="height: 20px;">
                    <div class="progress-bar progress-bar-striped" 
                         role="progressbar" 
                         style="width: 0%;" 
                         aria-valuenow="0" 
                         aria-valuemin="0" 
                         aria-valuemax="100">0%</div>
                </div>
                
                <div class="detailed-progress">
                    <div class="progress-steps-container d-none">
                        <h6 class="steps-header small fw-bold mb-2">Processing Steps:</h6>
                        <ul class="progress-steps list-group list-group-flush"></ul>
                    </div>
                </div>
                
                <div class="progress-actions d-flex justify-content-end mt-2">
                    <button type="button" class="btn btn-sm btn-outline-secondary cancel-btn me-2" disabled>
                        <i class="bi bi-x-circle"></i> Cancel
                    </button>
                    <button type="button" class="btn btn-sm btn-outline-primary details-toggle-btn">
                        <i class="bi bi-info-circle"></i> <span class="toggle-text">Show Details</span>
                    </button>
                </div>
                
                <div class="progress-error alert alert-danger mt-3 d-none" role="alert">
                    <div class="d-flex">
                        <div class="me-2">
                            <i class="bi bi-exclamation-triangle-fill"></i>
                        </div>
                        <div>
                            <h6 class="alert-heading mb-1">Error Processing Task</h6>
                            <p class="error-message mb-1"></p>
                            <div class="error-details small">
                                <a href="#" class="error-details-toggle">Show technical details</a>
                                <pre class="error-stack d-none mt-2 p-2 bg-light"></pre>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Cache DOM elements
        this.statusLabel = this.container.querySelector('.status-label');
        this.taskMessage = this.container.querySelector('.task-message');
        this.progressBar = this.container.querySelector('.progress-bar');
        this.progressStepsContainer = this.container.querySelector('.progress-steps-container');
        this.progressStepsList = this.container.querySelector('.progress-steps');
        this.elapsedTimeContainer = this.container.querySelector('.elapsed-time');
        this.elapsedTimeValue = this.container.querySelector('.elapsed-value');
        this.estimatedTimeContainer = this.container.querySelector('.estimated-time');
        this.estimatedTimeValue = this.container.querySelector('.eta-value');
        this.cancelBtn = this.container.querySelector('.cancel-btn');
        this.detailsToggleBtn = this.container.querySelector('.details-toggle-btn');
        this.errorContainer = this.container.querySelector('.progress-error');
        this.errorMessage = this.container.querySelector('.error-message');
        this.errorStack = this.container.querySelector('.error-stack');
        
        // Add event listeners
        this.detailsToggleBtn.addEventListener('click', () => {
            const isVisible = !this.progressStepsContainer.classList.contains('d-none');
            this.progressStepsContainer.classList.toggle('d-none', isVisible);
            this.detailsToggleBtn.querySelector('.toggle-text').textContent = isVisible ? 'Show Details' : 'Hide Details';
        });
        
        this.cancelBtn.addEventListener('click', () => {
            this.cancelTask();
        });
        
        this.container.querySelector('.error-details-toggle')?.addEventListener('click', (e) => {
            e.preventDefault();
            const stack = this.container.querySelector('.error-stack');
            const isVisible = !stack.classList.contains('d-none');
            stack.classList.toggle('d-none', isVisible);
            e.target.textContent = isVisible ? 'Show technical details' : 'Hide technical details';
        });
    }
    
    startTask(taskId, initialData = null) {
        if (!taskId) {
            console.error('No task ID provided');
            return false;
        }
        
        // Stop any existing polling
        this.stopPolling();
        
        // Reset state
        this.taskId = taskId;
        this.status = 'pending';
        this.startTime = Date.now();
        this.progressData = {
            current: 0,
            total: 100,
            message: initialData?.message || 'Starting task...',
            steps: initialData?.steps || []
        };
        
        // Update UI
        this.updateUI();
        
        // Start tracking progress
        if (this.options.enableWebsocket) {
            this.connectWebSocket();
        } else if (this.options.autoStartPolling) {
            this.startPolling();
        }
        
        return true;
    }
    
    updateProgress(data) {
        if (!data) return;
        
        // Update progress data
        if (data.current !== undefined) this.progressData.current = data.current;
        if (data.total !== undefined) this.progressData.total = data.total;
        if (data.message) this.progressData.message = data.message;
        if (data.steps) this.progressData.steps = data.steps;
        
        // Update status if provided
        if (data.status) {
            const prevStatus = this.status;
            this.status = data.status;
            
            // Handle status change
            if (prevStatus !== this.status) {
                this.handleStatusChange(prevStatus, this.status);
            }
        }
        
        // Update UI
        this.updateUI();
    }
    
    updateUI() {
        // Calculate percentage
        const percent = this.calculatePercentage();
        
        // Update progress bar
        this.progressBar.style.width = `${percent}%`;
        this.progressBar.setAttribute('aria-valuenow', percent);
        
        if (this.options.showPercentage) {
            this.progressBar.textContent = `${percent}%`;
        }
        
        // Update status classes
        this.updateStatusUI();
        
        // Update message
        this.taskMessage.textContent = this.progressData.message;
        
        // Update detailed steps
        if (this.options.showDetailedSteps && this.progressData.steps.length > 0) {
            this.updateDetailedStepsUI();
        }
        
        // Update time information
        this.updateTimeInfo();
        
        // Show/hide cancel button based on status
        this.cancelBtn.disabled = !['pending', 'running'].includes(this.status);
    }
    
    updateStatusUI() {
        // Remove all status classes
        this.statusLabel.classList.remove(
            'bg-secondary', 'bg-primary', 'bg-info', 
            'bg-success', 'bg-danger', 'bg-warning'
        );
        this.progressBar.classList.remove(
            'bg-secondary', 'bg-primary', 'bg-info', 
            'bg-success', 'bg-danger', 'bg-warning',
            'progress-bar-striped', 'progress-bar-animated'
        );
        
        // Set appropriate classes and text based on status
        switch (this.status) {
            case 'idle':
                this.statusLabel.classList.add('bg-secondary');
                this.progressBar.classList.add('bg-secondary');
                this.statusLabel.textContent = 'Idle';
                break;
            case 'pending':
                this.statusLabel.classList.add('bg-warning');
                this.progressBar.classList.add('bg-warning', 'progress-bar-striped', 'progress-bar-animated');
                this.statusLabel.textContent = 'Pending';
                break;
            case 'running':
                this.statusLabel.classList.add('bg-primary');
                this.progressBar.classList.add('bg-primary', 'progress-bar-striped', 'progress-bar-animated');
                this.statusLabel.textContent = 'Processing';
                break;
            case 'success':
                this.statusLabel.classList.add('bg-success');
                this.progressBar.classList.add('bg-success');
                this.statusLabel.textContent = 'Complete';
                break;
            case 'failed':
                this.statusLabel.classList.add('bg-danger');
                this.progressBar.classList.add('bg-danger');
                this.statusLabel.textContent = 'Failed';
                break;
            default:
                this.statusLabel.classList.add('bg-info');
                this.progressBar.classList.add('bg-info');
                this.statusLabel.textContent = this.status;
        }
    }
    
    updateDetailedStepsUI() {
        // Show steps container
        this.progressStepsContainer.classList.remove('d-none');
        
        // Clear existing steps
        this.progressStepsList.innerHTML = '';
        
        // Add each step
        this.progressData.steps.forEach((step, index) => {
            const listItem = document.createElement('li');
            listItem.className = 'list-group-item p-2 border-0';
            
            let stepStatus = '';
            if (step.status === 'complete') {
                stepStatus = '<i class="bi bi-check-circle text-success me-2"></i>';
            } else if (step.status === 'in_progress') {
                stepStatus = '<div class="spinner-border spinner-border-sm text-primary me-2" role="status"><span class="visually-hidden">Loading...</span></div>';
            } else if (step.status === 'failed') {
                stepStatus = '<i class="bi bi-exclamation-circle text-danger me-2"></i>';
            } else {
                stepStatus = '<i class="bi bi-circle text-secondary me-2"></i>';
            }
            
            let stepProgress = '';
            if (step.percent !== undefined) {
                stepProgress = `<div class="ms-auto small">${step.percent}%</div>`;
            }
            
            listItem.innerHTML = `
                <div class="d-flex align-items-center">
                    ${stepStatus}
                    <div class="step-name flex-grow-1">${step.name}</div>
                    ${stepProgress}
                </div>
                ${step.message ? `<div class="step-message small text-muted ms-4">${step.message}</div>` : ''}
            `;
            
            this.progressStepsList.appendChild(listItem);
        });
    }
    
    updateTimeInfo() {
        if (this.status === 'idle') {
            this.elapsedTimeContainer.classList.add('d-none');
            this.estimatedTimeContainer.classList.add('d-none');
            return;
        }
        
        // Update elapsed time if enabled
        if (this.options.showElapsedTime && this.startTime) {
            const elapsedMs = Date.now() - this.startTime;
            this.elapsedTimeContainer.classList.remove('d-none');
            this.elapsedTimeValue.textContent = this.formatTime(elapsedMs);
        } else {
            this.elapsedTimeContainer.classList.add('d-none');
        }
        
        // Update estimated time if enabled and we have enough progress
        if (this.options.showEstimatedTime && this.progressData.current > 0 && this.status === 'running') {
            const elapsedMs = Date.now() - this.startTime;
            const percentComplete = this.calculatePercentage() / 100;
            
            if (percentComplete > 0.05) { // Only start estimating after 5% progress
                const totalEstimatedMs = elapsedMs / percentComplete;
                const remainingMs = totalEstimatedMs - elapsedMs;
                
                if (remainingMs > 0) {
                    this.estimatedTimeContainer.classList.remove('d-none');
                    this.estimatedTimeValue.textContent = this.formatTime(remainingMs);
                }
            }
        } else {
            this.estimatedTimeContainer.classList.add('d-none');
        }
    }
    
    formatTime(ms) {
        const seconds = Math.floor(ms / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        
        if (hours > 0) {
            return `${hours}h ${minutes % 60}m`;
        } else if (minutes > 0) {
            return `${minutes}m ${seconds % 60}s`;
        } else {
            return `${seconds}s`;
        }
    }
    
    calculatePercentage() {
        if (!this.progressData.total) return 0;
        
        const percent = Math.round((this.progressData.current / this.progressData.total) * 100);
        return Math.min(Math.max(percent, 0), 100); // Clamp between 0-100
    }
    
    startPolling() {
        if (!this.taskId) {
            console.error('No task ID to poll');
            return;
        }
        
        // Clear any existing interval
        this.stopPolling();
        
        // Start new polling interval
        this.pollTaskStatus(); // Immediate first poll
        this.pollingInterval = setInterval(this.pollTaskStatus, this.pollingDelay);
        
        console.log(`Started polling task ${this.taskId} every ${this.pollingDelay}ms`);
    }
    
    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }
    
    async pollTaskStatus() {
        if (!this.taskId) return;
        
        try {
            const endpoint = `${this.options.statusEndpoint}${this.taskId}`;
            const response = await fetch(endpoint);
            
            if (!response.ok) {
                this.retryCount++;
                console.warn(`Error polling task status (attempt ${this.retryCount}/${this.maxRetries}):`, response.status);
                
                if (this.retryCount >= this.maxRetries) {
                    this.handleError(new Error(`Failed to fetch task status after ${this.maxRetries} attempts`));
                }
                
                return;
            }
            
            // Reset retry counter on success
            this.retryCount = 0;
            
            const data = await response.json();
            
            // Process response data
            this.processStatusUpdate(data);
            
        } catch (error) {
            this.retryCount++;
            console.error(`Error polling task status (attempt ${this.retryCount}/${this.maxRetries}):`, error);
            
            if (this.retryCount >= this.maxRetries) {
                this.handleError(error);
            }
        }
    }
    
    processStatusUpdate(data) {
        if (!data) return;
        
        // Map backend status to our status
        let status = 'running';
        
        if (data.status === 'SUCCESS') {
            status = 'success';
            this.stopPolling(); // No need to poll a completed task
        } else if (data.status === 'FAILURE') {
            status = 'failed';
            this.stopPolling(); // No need to poll a failed task
        } else if (data.status === 'PENDING') {
            status = 'pending';
        } else if (data.status === 'STARTED' || data.status === 'PROGRESS') {
            status = 'running';
        }
        
        // Extract progress data
        const progressUpdate = {
            status: status,
            message: data.message || this.progressData.message
        };
        
        // Extract progress info
        if (data.result && data.result.progress) {
            progressUpdate.current = data.result.progress.current || 0;
            progressUpdate.total = data.result.progress.total || 100;
        }
        
        // Extract steps information if available
        if (data.result && data.result.steps) {
            progressUpdate.steps = data.result.steps;
        }
        
        // Handle error information
        if (status === 'failed' && data.result && data.result.error) {
            this.showError(data.result.error, data.result.traceback);
        }
        
        // Update our state
        this.updateProgress(progressUpdate);
    }
    
    handleStatusChange(oldStatus, newStatus) {
        console.log(`Task status changed: ${oldStatus} -> ${newStatus}`);
        
        // Handle completion
        if (newStatus === 'success') {
            if (this.options.autoHide) {
                setTimeout(() => {
                    this.container.classList.add('progress-tracker-fade-out');
                    setTimeout(() => {
                        this.container.style.display = 'none';
                    }, 1000);
                }, 2000);
            }
            
            // Call onComplete callback if provided
            if (typeof this.options.onComplete === 'function') {
                this.options.onComplete(this.taskId, true);
            }
        }
        
        // Handle failure
        if (newStatus === 'failed') {
            // Call onComplete callback with failed=true if provided
            if (typeof this.options.onComplete === 'function') {
                this.options.onComplete(this.taskId, false);
            }
        }
        
        // Call onStatusChange callback if provided
        if (typeof this.options.onStatusChange === 'function') {
            this.options.onStatusChange(this.taskId, newStatus, oldStatus);
        }
    }
    
    handleError(error) {
        console.error('Task tracking error:', error);
        
        this.showError({
            message: 'Failed to communicate with the server',
            type: 'network_error'
        }, error.toString());
        
        this.status = 'failed';
        this.updateUI();
        this.stopPolling();
    }
    
    showError(error, stackTrace = null) {
        this.errorContainer.classList.remove('d-none');
        
        if (typeof error === 'string') {
            this.errorMessage.textContent = error;
        } else {
            this.errorMessage.textContent = error.message || 'Unknown error occurred';
        }
        
        if (stackTrace) {
            this.errorStack.textContent = stackTrace;
        } else {
            this.container.querySelector('.error-details').classList.add('d-none');
        }
    }
    
    hideError() {
        this.errorContainer.classList.add('d-none');
    }
    
    connectWebSocket() {
        // Check if WebSocket is already connected
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.close();
        }
        
        // Create WebSocket connection
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/tasks/${this.taskId}/`;
        
        this.socket = new WebSocket(wsUrl);
        
        // Set up event handlers
        this.socket.onopen = () => {
            console.log(`WebSocket connected for task ${this.taskId}`);
        };
        
        this.socket.onmessage = this.handleWebSocketMessage;
        
        this.socket.onerror = (error) => {
            console.error('WebSocket error:', error);
            // Fall back to polling if WebSocket fails
            this.startPolling();
        };
        
        this.socket.onclose = () => {
            console.log(`WebSocket closed for task ${this.taskId}`);
            this.socket = null;
        };
    }
    
    handleWebSocketMessage(event) {
        try {
            const data = JSON.parse(event.data);
            this.processStatusUpdate(data);
        } catch (error) {
            console.error('Error processing WebSocket message:', error);
        }
    }
    
    async cancelTask() {
        if (!this.taskId || !['pending', 'running'].includes(this.status)) {
            return;
        }
        
        try {
            const response = await fetch(`/api/tasks/cancel/${this.taskId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`Failed to cancel task: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.status = 'cancelled';
                this.progressData.message = 'Task cancelled';
                this.updateUI();
                this.stopPolling();
                
                // Call status change callback
                this.handleStatusChange('running', 'cancelled');
            } else {
                console.error('Failed to cancel task:', data.error);
            }
        } catch (error) {
            console.error('Error cancelling task:', error);
        }
    }
    
    // Public API methods
    reset() {
        this.taskId = null;
        this.status = 'idle';
        this.startTime = null;
        this.progressData = {
            current: 0,
            total: 100,
            message: '',
            steps: []
        };
        
        this.stopPolling();
        
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
        
        this.updateUI();
        this.hideError();
    }
    
    getTaskId() {
        return this.taskId;
    }
    
    getStatus() {
        return this.status;
    }
    
    getProgress() {
        return {
            current: this.progressData.current,
            total: this.progressData.total,
            percent: this.calculatePercentage(),
            message: this.progressData.message,
            steps: [...this.progressData.steps]
        };
    }
}

// Export the class for use in other modules
window.ProgressTracker = ProgressTracker; 
window.ProgressTracker = ProgressTracker; 
window.ProgressTracker = ProgressTracker; 