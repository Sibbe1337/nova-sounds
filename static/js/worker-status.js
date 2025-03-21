/**
 * Worker Status Module
 * Provides real-time monitoring of Celery workers and tasks
 */
class WorkerStatus {
    /**
     * Initialize worker status monitor
     * @param {Object} options Configuration options
     * @param {string} options.containerId ID of container element (optional)
     * @param {string} options.apiUrl Base API URL (optional)
     * @param {Function} options.onStatusUpdate Callback for status updates (optional)
     */
    constructor(options = {}) {
        // Configuration
        this.containerId = options.containerId || 'worker-status-container';
        this.apiUrl = options.apiUrl || '/api/worker-status';
        this.wsUrl = options.wsUrl || this._getWebSocketUrl('/worker-status/ws');
        this.refreshInterval = options.refreshInterval || 5000;
        this.onStatusUpdate = options.onStatusUpdate || null;
        
        // State
        this.workers = [];
        this.tasks = {
            active: [],
            scheduled: [],
            reserved: []
        };
        this.isConnected = false;
        this.useWebSocket = true;
        this.socket = null;
        this.pollTimer = null;
        
        // Cache DOM elements
        this.container = document.getElementById(this.containerId);
        
        // Initialize
        this._init();
    }
    
    /**
     * Initialize the worker status monitor
     * @private
     */
    _init() {
        // Check if container exists
        if (!this.container) {
            console.warn(`Worker status container #${this.containerId} not found, creating one`);
            this.container = document.createElement('div');
            this.container.id = this.containerId;
            document.body.appendChild(this.container);
        }
        
        // Create container structure if empty
        if (this.container.children.length === 0) {
            this._createContainerStructure();
        }
        
        // Try WebSocket connection first
        this._initWebSocket();
        
        // Fallback to polling if WebSocket fails
        setTimeout(() => {
            if (!this.isConnected) {
                console.log('WebSocket connection failed, falling back to polling');
                this.useWebSocket = false;
                this._startPolling();
            }
        }, 3000);
    }
    
    /**
     * Initialize WebSocket connection
     * @private
     */
    _initWebSocket() {
        try {
            this.socket = new WebSocket(this.wsUrl);
            
            this.socket.onopen = () => {
                console.log('Connected to worker status WebSocket');
                this.isConnected = true;
                this._updateConnectionStatus(true);
                
                // Send ping every 30 seconds to keep connection alive
                setInterval(() => {
                    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                        this.socket.send(JSON.stringify({ type: 'ping' }));
                    }
                }, 30000);
            };
            
            this.socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this._processStatusUpdate(data);
            };
            
            this.socket.onclose = () => {
                console.log('Worker status WebSocket connection closed');
                this.isConnected = false;
                this._updateConnectionStatus(false);
                
                // Try to reconnect after a delay
                setTimeout(() => {
                    if (this.useWebSocket) {
                        this._initWebSocket();
                    }
                }, 5000);
            };
            
            this.socket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.isConnected = false;
                this._updateConnectionStatus(false);
            };
        } catch (error) {
            console.error('Error initializing WebSocket:', error);
            this.useWebSocket = false;
            this._startPolling();
        }
    }
    
    /**
     * Start polling for updates
     * @private
     */
    _startPolling() {
        // Clear existing timer
        if (this.pollTimer) {
            clearInterval(this.pollTimer);
        }
        
        // Get initial status
        this._fetchStatus();
        
        // Set up regular polling
        this.pollTimer = setInterval(() => {
            this._fetchStatus();
        }, this.refreshInterval);
    }
    
    /**
     * Fetch worker status via API
     * @private
     */
    _fetchStatus() {
        fetch(`${this.apiUrl}`)
            .then(response => response.json())
            .then(data => {
                this._processStatusUpdate(data);
            })
            .catch(error => {
                console.error('Error fetching worker status:', error);
                this._updateConnectionStatus(false);
            });
    }
    
    /**
     * Process status update data
     * @param {Object} data Status data
     * @private
     */
    _processStatusUpdate(data) {
        if (data.status === 'success') {
            // Update workers
            if (data.workers) {
                this.workers = data.workers;
                this._updateWorkersDisplay();
            }
            
            // Update tasks
            if (data.active || data.scheduled || data.reserved) {
                this.tasks = {
                    active: data.active || [],
                    scheduled: data.scheduled || [],
                    reserved: data.reserved || []
                };
                this._updateTasksDisplay();
            }
            
            // Call user callback if provided
            if (typeof this.onStatusUpdate === 'function') {
                this.onStatusUpdate(data);
            }
            
            this._updateConnectionStatus(true);
        } else {
            console.error('Error in worker status data:', data.message || 'Unknown error');
            this._updateConnectionStatus(false);
        }
    }
    
    /**
     * Create container structure
     * @private
     */
    _createContainerStructure() {
        this.container.innerHTML = `
            <div class="worker-status-panel">
                <div class="status-header">
                    <h3>Worker Status</h3>
                    <div class="connection-status">
                        <span class="status-dot"></span>
                        <span class="status-text">Connecting...</span>
                    </div>
                </div>
                <div class="worker-list">
                    <div class="no-workers-message">No active workers found</div>
                </div>
                <div class="task-summary">
                    <div class="summary-item">
                        <div class="summary-label">Active Tasks</div>
                        <div class="summary-value" id="active-tasks-count">0</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-label">Scheduled</div>
                        <div class="summary-value" id="scheduled-tasks-count">0</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-label">Reserved</div>
                        <div class="summary-value" id="reserved-tasks-count">0</div>
                    </div>
                </div>
                <div class="task-details">
                    <h4>Task Details</h4>
                    <div class="task-tabs">
                        <button class="task-tab active" data-tab="active">Active</button>
                        <button class="task-tab" data-tab="scheduled">Scheduled</button>
                        <button class="task-tab" data-tab="reserved">Reserved</button>
                    </div>
                    <div class="task-list" id="task-list-container">
                        <div class="no-tasks-message">No active tasks</div>
                    </div>
                </div>
            </div>
        `;
        
        // Add event listeners for tabs
        const tabButtons = this.container.querySelectorAll('.task-tab');
        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const tab = button.getAttribute('data-tab');
                this._switchTaskTab(tab);
            });
        });
    }
    
    /**
     * Update connection status indicator
     * @param {boolean} isConnected Connection status
     * @private
     */
    _updateConnectionStatus(isConnected) {
        const statusDot = this.container.querySelector('.connection-status .status-dot');
        const statusText = this.container.querySelector('.connection-status .status-text');
        
        if (statusDot && statusText) {
            if (isConnected) {
                statusDot.className = 'status-dot connected';
                statusText.textContent = this.useWebSocket ? 'Live' : 'Connected';
            } else {
                statusDot.className = 'status-dot disconnected';
                statusText.textContent = 'Disconnected';
            }
        }
    }
    
    /**
     * Update workers display
     * @private
     */
    _updateWorkersDisplay() {
        const workerList = this.container.querySelector('.worker-list');
        
        if (!workerList) return;
        
        if (this.workers.length === 0) {
            workerList.innerHTML = '<div class="no-workers-message">No active workers found</div>';
            return;
        }
        
        let html = '';
        
        this.workers.forEach(worker => {
            const totalTasks = worker.active_tasks + worker.scheduled_tasks + worker.reserved_tasks;
            
            html += `
                <div class="worker-item">
                    <div class="worker-header">
                        <div class="worker-name">${worker.name}</div>
                        <div class="worker-status ${worker.status}">${worker.status}</div>
                    </div>
                    <div class="worker-details">
                        <div class="worker-stats">
                            <div class="stat-item">
                                <span class="stat-label">PID:</span>
                                <span class="stat-value">${worker.pid}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Concurrency:</span>
                                <span class="stat-value">${worker.concurrency}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Uptime:</span>
                                <span class="stat-value">${worker.uptime}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Tasks:</span>
                                <span class="stat-value">${totalTasks} (${worker.processed} processed)</span>
                            </div>
                        </div>
                        <div class="worker-task-breakdown">
                            <div class="breakdown-item">
                                <div class="breakdown-label">Active</div>
                                <div class="breakdown-value">${worker.active_tasks}</div>
                            </div>
                            <div class="breakdown-item">
                                <div class="breakdown-label">Scheduled</div>
                                <div class="breakdown-value">${worker.scheduled_tasks}</div>
                            </div>
                            <div class="breakdown-item">
                                <div class="breakdown-label">Reserved</div>
                                <div class="breakdown-value">${worker.reserved_tasks}</div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        workerList.innerHTML = html;
    }
    
    /**
     * Update tasks display
     * @private
     */
    _updateTasksDisplay() {
        // Update summary counts
        const activeCount = this.container.querySelector('#active-tasks-count');
        const scheduledCount = this.container.querySelector('#scheduled-tasks-count');
        const reservedCount = this.container.querySelector('#reserved-tasks-count');
        
        if (activeCount) activeCount.textContent = this.tasks.active.length;
        if (scheduledCount) scheduledCount.textContent = this.tasks.scheduled.length;
        if (reservedCount) reservedCount.textContent = this.tasks.reserved.length;
        
        // Get active tab
        const activeTab = this.container.querySelector('.task-tab.active');
        if (activeTab) {
            const tabName = activeTab.getAttribute('data-tab');
            this._renderTaskList(tabName);
        } else {
            this._renderTaskList('active');
        }
    }
    
    /**
     * Switch task tab
     * @param {string} tabName Tab name
     * @private
     */
    _switchTaskTab(tabName) {
        // Update tab buttons
        const tabButtons = this.container.querySelectorAll('.task-tab');
        tabButtons.forEach(button => {
            if (button.getAttribute('data-tab') === tabName) {
                button.classList.add('active');
            } else {
                button.classList.remove('active');
            }
        });
        
        // Render selected tab
        this._renderTaskList(tabName);
    }
    
    /**
     * Render task list for selected tab
     * @param {string} tabName Tab name
     * @private
     */
    _renderTaskList(tabName) {
        const taskList = this.container.querySelector('#task-list-container');
        
        if (!taskList) return;
        
        const tasks = this.tasks[tabName] || [];
        
        if (tasks.length === 0) {
            taskList.innerHTML = `<div class="no-tasks-message">No ${tabName} tasks</div>`;
            return;
        }
        
        let html = '';
        
        tasks.forEach(task => {
            const taskName = task.name || 'Unknown Task';
            const taskId = task.id || 'unknown-id';
            const taskArgs = JSON.stringify(task.args || []).slice(0, 50);
            
            html += `
                <div class="task-item" data-id="${taskId}">
                    <div class="task-header">
                        <div class="task-name">${taskName}</div>
                        <div class="task-status ${task.status}">${task.status}</div>
                    </div>
                    <div class="task-details">
                        <div class="task-id">${taskId}</div>
                        <div class="task-args">${taskArgs}</div>
                        <div class="task-worker">${task.worker || 'Unknown Worker'}</div>
                    </div>
                </div>
            `;
        });
        
        taskList.innerHTML = html;
        
        // Add click event for task details
        const taskItems = taskList.querySelectorAll('.task-item');
        taskItems.forEach(item => {
            item.addEventListener('click', () => {
                const taskId = item.getAttribute('data-id');
                this._showTaskDetails(taskId);
            });
        });
    }
    
    /**
     * Show detailed information for a task
     * @param {string} taskId Task ID
     * @private
     */
    _showTaskDetails(taskId) {
        fetch(`${this.apiUrl}/task/${taskId}`)
            .then(response => response.json())
            .then(data => {
                // Create modal for task details
                const modal = document.createElement('div');
                modal.className = 'task-detail-modal';
                
                const contents = `
                    <div class="task-detail-content">
                        <button class="close-button">&times;</button>
                        <h3>Task Details</h3>
                        <div class="detail-grid">
                            <div class="detail-label">ID:</div>
                            <div class="detail-value">${data.id}</div>
                            
                            <div class="detail-label">Status:</div>
                            <div class="detail-value status-${data.status}">${data.status}</div>
                            
                            ${data.result ? `
                                <div class="detail-label">Result:</div>
                                <div class="detail-value">${JSON.stringify(data.result)}</div>
                            ` : ''}
                            
                            ${data.error ? `
                                <div class="detail-label">Error:</div>
                                <div class="detail-value error">${data.error}</div>
                            ` : ''}
                            
                            ${data.info ? `
                                <div class="detail-label">Info:</div>
                                <div class="detail-value">${data.info}</div>
                            ` : ''}
                            
                            ${data.traceback ? `
                                <div class="detail-label">Traceback:</div>
                                <div class="detail-value traceback">${data.traceback}</div>
                            ` : ''}
                        </div>
                    </div>
                `;
                
                modal.innerHTML = contents;
                document.body.appendChild(modal);
                
                // Add close button event
                const closeButton = modal.querySelector('.close-button');
                closeButton.addEventListener('click', () => {
                    document.body.removeChild(modal);
                });
                
                // Close on click outside
                modal.addEventListener('click', (event) => {
                    if (event.target === modal) {
                        document.body.removeChild(modal);
                    }
                });
            })
            .catch(error => {
                console.error('Error fetching task details:', error);
            });
    }
    
    /**
     * Get WebSocket URL from API URL
     * @param {string} path WebSocket path
     * @returns {string} WebSocket URL
     * @private
     */
    _getWebSocketUrl(path) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        return `${protocol}//${host}${path}`;
    }
    
    /**
     * Format a date string
     * @param {string} dateString ISO date string
     * @returns {string} Formatted date
     * @private
     */
    _formatDate(dateString) {
        if (!dateString) return 'N/A';
        
        try {
            const date = new Date(dateString);
            return date.toLocaleString();
        } catch (e) {
            return dateString;
        }
    }
    
    /**
     * Refresh status data
     * @public
     */
    refresh() {
        this._fetchStatus();
    }
    
    /**
     * Disconnect and clean up
     * @public
     */
    disconnect() {
        // Clear polling timer
        if (this.pollTimer) {
            clearInterval(this.pollTimer);
            this.pollTimer = null;
        }
        
        // Close WebSocket
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
        
        this.isConnected = false;
        this._updateConnectionStatus(false);
    }
}

// Export as global or module
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WorkerStatus;
} else {
    window.WorkerStatus = WorkerStatus;
} 