/**
 * Offline Handler
 * Manages online/offline state detection and user notifications
 */

class OfflineHandler {
    constructor() {
        // Initialize state
        this.isOnline = navigator.onLine;
        this.offlineIndicator = null;
        this.pendingRequests = [];
        this.retryTimers = new Map();
        
        // Initialize on DOM load
        document.addEventListener('DOMContentLoaded', () => this.init());
    }
    
    /**
     * Initialize the offline handler
     */
    init() {
        // Create offline indicator
        this.createOfflineIndicator();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Initialize service worker if supported
        this.initServiceWorker();
    }
    
    /**
     * Create the offline indicator element
     */
    createOfflineIndicator() {
        if (document.querySelector('.offline-indicator')) {
            this.offlineIndicator = document.querySelector('.offline-indicator');
            return;
        }
        
        this.offlineIndicator = document.createElement('div');
        this.offlineIndicator.className = 'offline-indicator';
        this.offlineIndicator.setAttribute('role', 'status');
        this.offlineIndicator.setAttribute('aria-live', 'polite');
        
        const icon = document.createElement('span');
        icon.className = 'offline-icon';
        icon.textContent = '📶';
        
        const text = document.createElement('span');
        text.className = 'offline-text';
        text.textContent = 'You are offline';
        
        this.offlineIndicator.appendChild(icon);
        this.offlineIndicator.appendChild(text);
        
        document.body.appendChild(this.offlineIndicator);
    }
    
    /**
     * Set up event listeners for online/offline events
     */
    setupEventListeners() {
        // Online event
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.updateOfflineIndicator(false);
            this.retryPendingRequests();
            this.dispatchCustomEvent('app:online');
        });
        
        // Offline event
        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.updateOfflineIndicator(true);
            this.dispatchCustomEvent('app:offline');
        });
        
        // Setup beforeunload event to warn when offline
        window.addEventListener('beforeunload', (event) => {
            if (!this.isOnline && document.querySelectorAll('form[data-unsaved]').length > 0) {
                const message = 'You are currently offline. Unsaved changes may be lost if you leave the page.';
                event.returnValue = message;
                return message;
            }
        });
        
        // Add fetch listeners to detect network failures
        this.monkeyPatchFetch();
    }
    
    /**
     * Show or hide the offline indicator
     * @param {boolean} show - Whether to show the indicator
     */
    updateOfflineIndicator(show) {
        if (!this.offlineIndicator) return;
        
        if (show) {
            this.offlineIndicator.classList.add('visible');
            this.offlineIndicator.setAttribute('aria-hidden', 'false');
            this.offlineIndicator.querySelector('.offline-text').textContent = 'You are offline';
        } else {
            // Update text first, then start hiding after a delay
            this.offlineIndicator.querySelector('.offline-text').textContent = 'You are back online';
            
            setTimeout(() => {
                this.offlineIndicator.classList.remove('visible');
                this.offlineIndicator.setAttribute('aria-hidden', 'true');
            }, 3000);
        }
    }
    
    /**
     * Initialize service worker for offline support
     */
    initServiceWorker() {
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/sw.js')
                    .then(registration => {
                        console.log('ServiceWorker registration successful with scope: ', registration.scope);
                    })
                    .catch(error => {
                        console.log('ServiceWorker registration failed: ', error);
                    });
            });
        }
    }
    
    /**
     * Monkey patch the fetch API to track network requests
     */
    monkeyPatchFetch() {
        const originalFetch = window.fetch;
        const self = this;
        
        window.fetch = function(...args) {
            const request = args[0];
            const requestUrl = typeof request === 'string' ? request : request.url;
            const requestMethod = typeof request === 'string' ? 'GET' : request.method || 'GET';
            const requestId = `${requestMethod}:${requestUrl}:${Date.now()}`;
            
            // Only track API requests (not assets)
            if (requestUrl.includes('/api/') || requestUrl.includes('/auth/')) {
                self.pendingRequests.push({
                    id: requestId,
                    url: requestUrl,
                    method: requestMethod,
                    args: args,
                    timestamp: Date.now()
                });
            }
            
            return originalFetch.apply(this, args)
                .then(response => {
                    // Remove from pending requests on success
                    self.removePendingRequest(requestId);
                    return response;
                })
                .catch(error => {
                    // If the error is due to network connectivity
                    if (!navigator.onLine || error.name === 'TypeError') {
                        // Keep in pending requests for retry
                        self.updateOfflineIndicator(true);
                        
                        // Show user feedback
                        self.dispatchCustomEvent('app:request-failed', {
                            url: requestUrl,
                            method: requestMethod,
                            error: error
                        });
                        
                        // Schedule retry if we're not already retrying this request
                        if (!self.retryTimers.has(requestId)) {
                            const retryTimer = setTimeout(() => {
                                if (navigator.onLine) {
                                    self.retryRequest(requestId);
                                }
                                self.retryTimers.delete(requestId);
                            }, 5000);
                            
                            self.retryTimers.set(requestId, retryTimer);
                        }
                    } else {
                        // Not a network error, remove from pending
                        self.removePendingRequest(requestId);
                    }
                    
                    throw error;
                });
        };
    }
    
    /**
     * Remove a request from the pending requests list
     * @param {string} requestId - The ID of the request to remove
     */
    removePendingRequest(requestId) {
        this.pendingRequests = this.pendingRequests.filter(req => req.id !== requestId);
    }
    
    /**
     * Retry a specific pending request
     * @param {string} requestId - The ID of the request to retry
     */
    retryRequest(requestId) {
        const request = this.pendingRequests.find(req => req.id === requestId);
        if (!request) return;
        
        // Remove from pending requests list
        this.removePendingRequest(requestId);
        
        // Dispatch event for UI feedback
        this.dispatchCustomEvent('app:request-retry', {
            url: request.url,
            method: request.method
        });
        
        // Retry the request
        window.fetch.apply(window, request.args)
            .catch(() => {
                // If it fails again, do nothing - it will be auto-retried if needed
            });
    }
    
    /**
     * Retry all pending requests when coming back online
     */
    retryPendingRequests() {
        // Clone the array to avoid modification during iteration
        const requestsToRetry = [...this.pendingRequests];
        
        // Process each request
        requestsToRetry.forEach(request => {
            this.retryRequest(request.id);
        });
    }
    
    /**
     * Dispatch a custom event
     * @param {string} eventName - Name of the event
     * @param {Object} detail - Event details
     */
    dispatchCustomEvent(eventName, detail = {}) {
        const event = new CustomEvent(eventName, {
            detail: detail,
            bubbles: true
        });
        document.dispatchEvent(event);
    }
    
    /**
     * Check if the browser is currently online
     * @returns {boolean} Online status
     */
    checkOnlineStatus() {
        return navigator.onLine;
    }
    
    /**
     * Manually show the offline indicator
     */
    showOfflineIndicator() {
        this.updateOfflineIndicator(true);
    }
    
    /**
     * Manually hide the offline indicator
     */
    hideOfflineIndicator() {
        this.updateOfflineIndicator(false);
    }
}

// Initialize the offline handler
const offlineHandler = new OfflineHandler();

// Export for module use
if (typeof module !== 'undefined') {
    module.exports = offlineHandler;
} 