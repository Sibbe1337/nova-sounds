/**
 * API Client
 * Standardized API interaction with error handling, loading states, and automatic retries
 */

// Default configuration for API requests
const DEFAULT_CONFIG = {
    baseUrl: '', // Will be auto-detected if empty
    timeout: 30000, // 30 seconds
    retries: 1,
    retryDelay: 1000,
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
};

// Initialize state
let config = {...DEFAULT_CONFIG};
let pendingRequests = {};
let requestId = 0;

/**
 * Initialize the API client with configuration
 * @param {Object} customConfig - Configuration to override defaults
 */
function init(customConfig = {}) {
    config = {...DEFAULT_CONFIG, ...customConfig};
    
    // Auto-detect baseUrl if not provided
    if (!config.baseUrl) {
        config.baseUrl = window.location.origin;
    }
    
    // Normalize baseUrl (ensure it doesn't end with a slash)
    config.baseUrl = config.baseUrl.replace(/\/$/, '');
    
    console.log('API Client initialized with baseUrl:', config.baseUrl);
}

/**
 * Make an API request
 * @param {string} endpoint - API endpoint (with leading slash)
 * @param {Object} options - Request options
 * @returns {Promise} - Promise resolving to the response data
 */
async function request(endpoint, options = {}) {
    const {
        method = 'GET',
        body = null,
        params = null,
        headers = {},
        timeout = config.timeout,
        retries = config.retries,
        retryDelay = config.retryDelay,
        loadingElement = null,
        loadingMessage = 'Loading...',
        errorElement = null
    } = options;
    
    // Create a unique ID for this request
    const id = ++requestId;
    
    // Show loading indicator if element provided
    let loader = null;
    if (loadingElement) {
        if (typeof UIUtils !== 'undefined' && typeof UIUtils.createLoader === 'function') {
            loader = UIUtils.createLoader(loadingElement, loadingMessage);
            loader.show();
        } else {
            // Simple fallback if UIUtils not available
            if (typeof loadingElement === 'string') {
                loadingElement = document.querySelector(loadingElement);
            }
            if (loadingElement) {
                loadingElement.classList.add('loading');
            }
        }
    }
    
    // Prepare URL with query parameters
    let url = `${config.baseUrl}${endpoint}`;
    if (params) {
        const queryParams = new URLSearchParams();
        Object.entries(params).forEach(([key, value]) => {
            if (value !== null && value !== undefined) {
                queryParams.append(key, value);
            }
        });
        const queryString = queryParams.toString();
        if (queryString) {
            url += `?${queryString}`;
        }
    }
    
    // Prepare fetch options
    const fetchOptions = {
        method,
        headers: {...config.headers, ...headers},
        credentials: 'same-origin'
    };
    
    // Add body for non-GET requests
    if (method !== 'GET' && body !== null) {
        if (body instanceof FormData) {
            // Don't set Content-Type for FormData, browser will set it automatically
            delete fetchOptions.headers['Content-Type'];
            fetchOptions.body = body;
        } else if (typeof body === 'object') {
            fetchOptions.body = JSON.stringify(body);
        } else {
            fetchOptions.body = body;
        }
    }
    
    // Store request in pending requests
    pendingRequests[id] = { url, options: fetchOptions };
    
    // Helper function for retry logic
    const performFetch = async (retriesLeft) => {
        try {
            // Create AbortController for timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), timeout);
            
            fetchOptions.signal = controller.signal;
            
            const response = await fetch(url, fetchOptions);
            clearTimeout(timeoutId);
            
            // Always parse JSON responses if possible
            let data;
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                data = await response.json();
            } else {
                data = await response.text();
            }
            
            // Handle HTTP error status
            if (!response.ok) {
                const error = new Error(data.message || response.statusText || 'API request failed');
                error.status = response.status;
                error.data = data;
                
                // Check if we should retry
                if (retriesLeft > 0 && shouldRetry(response.status)) {
                    console.warn(`API request failed with status ${response.status}, retrying (${retriesLeft} left)...`);
                    await new Promise(resolve => setTimeout(resolve, retryDelay));
                    return performFetch(retriesLeft - 1);
                }
                
                throw error;
            }
            
            return data;
        } catch (error) {
            // Check if we can retry network errors
            if (retriesLeft > 0 && (error.name === 'AbortError' || error.name === 'TypeError')) {
                console.warn(`API request failed with ${error.name}, retrying (${retriesLeft} left)...`);
                await new Promise(resolve => setTimeout(resolve, retryDelay));
                return performFetch(retriesLeft - 1);
            }
            
            throw error;
        }
    };
    
    try {
        const data = await performFetch(retries);
        
        // Clean up
        delete pendingRequests[id];
        if (loader) {
            loader.hide();
        } else if (loadingElement && typeof loadingElement !== 'string') {
            loadingElement.classList.remove('loading');
        }
        
        return data;
    } catch (error) {
        // Clean up
        delete pendingRequests[id];
        if (loader) {
            loader.hide();
        } else if (loadingElement && typeof loadingElement !== 'string') {
            loadingElement.classList.remove('loading');
        }
        
        // Handle error display
        handleError(error, errorElement);
        
        throw error;
    }
}

/**
 * Determine if a request should be retried based on HTTP status
 * @param {number} status - HTTP status code
 * @returns {boolean} - Whether the request should be retried
 */
function shouldRetry(status) {
    // Retry server errors and specific client errors
    return status >= 500 || status === 429 || status === 408;
}

/**
 * Handle API errors consistently
 * @param {Error} error - Error object
 * @param {Element|string} element - Optional element to display error in
 */
function handleError(error, element = null) {
    // Log error to console
    console.error('API Error:', error);
    
    // Display error in UI if element provided
    if (element) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        
        if (element) {
            // Check if UI Utils is available for nice error display
            if (typeof UIUtils !== 'undefined' && typeof UIUtils.showToast === 'function') {
                // For notifications
                UIUtils.showToast(
                    error.message || 'An error occurred',
                    'error'
                );
            } else {
                // Fallback error display
                element.innerHTML = `
                    <div class="ui-error-state">
                        <div class="ui-error-icon">
                            <i class="fas fa-exclamation-triangle"></i>
                        </div>
                        <h3 class="ui-error-title">Error</h3>
                        <p class="ui-error-message">${error.message || 'An error occurred. Please try again.'}</p>
                        <div class="ui-error-actions">
                            <button class="btn btn-primary retry-button">Try Again</button>
                        </div>
                    </div>
                `;
                
                // Add retry handler
                const retryButton = element.querySelector('.retry-button');
                if (retryButton) {
                    retryButton.addEventListener('click', () => {
                        window.location.reload();
                    });
                }
            }
        }
    }
}

/**
 * Cancel all pending requests
 */
function cancelAll() {
    Object.values(pendingRequests).forEach(request => {
        if (request.controller && request.controller.abort) {
            request.controller.abort();
        }
    });
    pendingRequests = {};
}

/**
 * Shortcut for GET requests
 * @param {string} endpoint - API endpoint
 * @param {Object} options - Request options
 * @returns {Promise} - Promise resolving to the response data
 */
function get(endpoint, options = {}) {
    return request(endpoint, {...options, method: 'GET'});
}

/**
 * Shortcut for POST requests
 * @param {string} endpoint - API endpoint
 * @param {Object} body - Request body
 * @param {Object} options - Additional request options
 * @returns {Promise} - Promise resolving to the response data
 */
function post(endpoint, body = null, options = {}) {
    return request(endpoint, {...options, method: 'POST', body});
}

/**
 * Shortcut for PUT requests
 * @param {string} endpoint - API endpoint
 * @param {Object} body - Request body
 * @param {Object} options - Additional request options
 * @returns {Promise} - Promise resolving to the response data
 */
function put(endpoint, body = null, options = {}) {
    return request(endpoint, {...options, method: 'PUT', body});
}

/**
 * Shortcut for DELETE requests
 * @param {string} endpoint - API endpoint
 * @param {Object} options - Request options
 * @returns {Promise} - Promise resolving to the response data
 */
function del(endpoint, options = {}) {
    return request(endpoint, {...options, method: 'DELETE'});
}

/**
 * Upload a file or files
 * @param {string} endpoint - API endpoint
 * @param {Object} files - Files object (either a single File or an object of {fieldName: File})
 * @param {Object} data - Additional form data fields
 * @param {Object} options - Additional request options
 * @returns {Promise} - Promise resolving to the response data
 */
function upload(endpoint, files, data = {}, options = {}) {
    const formData = new FormData();
    
    // Add files to FormData
    if (files instanceof File) {
        formData.append('file', files);
    } else if (Array.isArray(files)) {
        files.forEach((file, index) => {
            formData.append(`file${index}`, file);
        });
    } else {
        Object.entries(files).forEach(([key, value]) => {
            if (Array.isArray(value)) {
                value.forEach(file => {
                    formData.append(key, file);
                });
            } else {
                formData.append(key, value);
            }
        });
    }
    
    // Add additional data
    Object.entries(data).forEach(([key, value]) => {
        if (value !== null && value !== undefined) {
            formData.append(key, value);
        }
    });
    
    return post(endpoint, formData, options);
}

// Initialize on load with auto-detection
document.addEventListener('DOMContentLoaded', () => {
    init();
});

// Export the API client
window.APIClient = {
    init,
    request,
    get,
    post,
    put,
    delete: del,
    upload,
    cancelAll
}; 