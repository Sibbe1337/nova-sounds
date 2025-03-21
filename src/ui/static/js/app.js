/**
 * Main Application Script
 * Initializes all components and handles common functionality
 */

// Global app state
const App = {
    // App state
    state: {
        darkMode: false,
        userAuthenticated: false,
        apiAvailable: false,
        currentPage: '',
        debugMode: false,
        networkStatus: 'online',
        mediaType: 'desktop',
        pendingNotifications: []
    },
    
    // Configuration
    config: {
        apiUrl: '',
        debugEnabled: false,
        darkModeStorageKey: 'darkMode',
        breakpoints: {
            mobile: 576,
            tablet: 992,
            desktop: 1200
        },
        themes: {
            light: {
                '--primary-color': '#0071e3',
                '--primary-color-rgb': '0, 113, 227',
                '--background-color': '#f5f5f7',
                '--card-bg': '#ffffff',
                '--text-color': '#333333',
                '--text-color-light': '#86868b',
                '--border-color': '#d2d2d7'
            },
            dark: {
                '--primary-color': '#0a84ff',
                '--primary-color-rgb': '10, 132, 255',
                '--background-color': '#1c1c1e',
                '--card-bg': '#2c2c2e',
                '--text-color': '#f5f5f7',
                '--text-color-light': '#98989d',
                '--border-color': '#3a3a3c'
            }
        }
    },
    
    /**
     * Initialize the app
     * @param {Object} options - Initialization options
     */
    init(options = {}) {
        // Merge options with config
        Object.assign(this.config, options);
        
        // Set initial API URL if not provided
        if (!this.config.apiUrl) {
            this.config.apiUrl = `${window.location.protocol}//${window.location.hostname}${window.location.port ? ':' + window.location.port : ''}/api`;
        }
        
        // Initialize API client if available
        if (window.APIClient) {
            window.APIClient.init({
                baseUrl: this.config.apiUrl
            });
        }
        
        // Set current page from the window location
        this.state.currentPage = window.location.pathname;
        
        // Check if debug mode is enabled
        this.state.debugMode = window.__DEBUG_MODE || this.config.debugEnabled;
        
        // Init user auth status
        this.initAuthStatus();
        
        // Setup theme mode (light/dark)
        this.initThemeMode();
        
        // Setup responsive handlers
        this.initResponsive();
        
        // Setup network status monitoring
        this.initNetworkMonitor();
        
        // Initialize interactive elements
        this.initInteractive();
        
        // Setup event handlers
        this.setupEventHandlers();
        
        // Ready! Log initialization in debug mode
        if (this.state.debugMode) {
            console.log('App initialized with config:', this.config);
            console.log('Initial state:', this.state);
        }
        
        // Dispatch app ready event
        window.dispatchEvent(new CustomEvent('app:ready', { detail: this }));
    },
    
    /**
     * Initialize authentication status
     */
    async initAuthStatus() {
        try {
            // Check if auth API is available
            const response = await fetch('/auth/status', {
                method: 'GET',
                headers: {
                    'Accept': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.state.userAuthenticated = data.authenticated || false;
                this.state.apiAvailable = true;
            } else {
                this.state.apiAvailable = false;
            }
        } catch (error) {
            console.warn('Failed to check auth status:', error);
            this.state.apiAvailable = false;
        }
        
        // Update UI based on auth status
        this.updateAuthUI();
        
        // Dispatch auth status event
        window.dispatchEvent(new CustomEvent('auth:status', { 
            detail: {
                authenticated: this.state.userAuthenticated,
                apiAvailable: this.state.apiAvailable
            }
        }));
    },
    
    /**
     * Initialize theme mode (light/dark)
     */
    initThemeMode() {
        // Check for stored preference
        const storedMode = localStorage.getItem(this.config.darkModeStorageKey);
        
        if (storedMode !== null) {
            // Use stored preference
            this.state.darkMode = storedMode === 'true';
        } else {
            // Check system preference
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            this.state.darkMode = prefersDark;
        }
        
        // Apply theme
        this.applyTheme();
        
        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)')
            .addEventListener('change', (e) => {
                // Only auto-switch if user has no preference stored
                if (localStorage.getItem(this.config.darkModeStorageKey) === null) {
                    this.state.darkMode = e.matches;
                    this.applyTheme();
                }
            });
    },
    
    /**
     * Initialize responsive behavior
     */
    initResponsive() {
        // Set initial media type
        this.updateMediaType();
        
        // Listen for window resize events
        window.addEventListener('resize', this.debounce(() => {
            this.updateMediaType();
        }, 250));
    },
    
    /**
     * Initialize network status monitoring
     */
    initNetworkMonitor() {
        // Set initial network status
        this.state.networkStatus = navigator.onLine ? 'online' : 'offline';
        
        // Listen for network status changes
        window.addEventListener('online', () => {
            this.state.networkStatus = 'online';
            this.handleNetworkStatusChange();
        });
        
        window.addEventListener('offline', () => {
            this.state.networkStatus = 'offline';
            this.handleNetworkStatusChange();
        });
    },
    
    /**
     * Initialize interactive elements
     */
    initInteractive() {
        // Theme toggle
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            themeToggle.checked = this.state.darkMode;
            themeToggle.addEventListener('change', () => {
                this.toggleTheme();
            });
        }
        
        // Mobile menu toggle
        const mobileMenuToggle = document.getElementById('mobileMenuToggle');
        const mobileMenu = document.getElementById('mobileMenu');
        if (mobileMenuToggle && mobileMenu) {
            mobileMenuToggle.addEventListener('click', () => {
                mobileMenu.classList.toggle('active');
                mobileMenuToggle.setAttribute('aria-expanded', 
                    mobileMenu.classList.contains('active').toString());
            });
        }
        
        // Setup dismissible elements
        document.querySelectorAll('[data-dismissible]').forEach(element => {
            const dismissBtn = element.querySelector('[data-dismiss]');
            if (dismissBtn) {
                dismissBtn.addEventListener('click', () => {
                    element.classList.add('dismissed');
                    // If the element has a data-dismiss-key, store the dismissed state
                    const dismissKey = element.getAttribute('data-dismissible');
                    if (dismissKey) {
                        localStorage.setItem(`dismissed_${dismissKey}`, 'true');
                    }
                    // Remove after animation completes
                    setTimeout(() => {
                        element.style.display = 'none';
                    }, 300);
                });
            }
            
            // Check if element should be hidden based on stored preference
            const dismissKey = element.getAttribute('data-dismissible');
            if (dismissKey && localStorage.getItem(`dismissed_${dismissKey}`) === 'true') {
                element.style.display = 'none';
            }
        });
    },
    
    /**
     * Setup global event handlers
     */
    setupEventHandlers() {
        // Handle link clicks for app-internal navigation
        document.addEventListener('click', (event) => {
            // Find the nearest link ancestor
            let target = event.target;
            while (target && target.tagName !== 'A') {
                target = target.parentElement;
            }
            
            // If no link found or link has certain attributes, allow default behavior
            if (!target || target.hasAttribute('target') || target.hasAttribute('download') || 
                target.hasAttribute('data-external') || target.getAttribute('rel') === 'external') {
                return;
            }
            
            // Check if it's an internal link
            const href = target.getAttribute('href');
            if (href && !href.startsWith('http') && !href.startsWith('//') && !href.startsWith('#')) {
                // It's an internal link, we could implement SPA-like navigation here
                // For now, just let the browser handle it normally
            }
        });
        
        // Listen for form submissions to enhance them
        document.addEventListener('submit', (event) => {
            const form = event.target;
            
            // Skip forms with data-native attribute (no enhancement)
            if (form.hasAttribute('data-native')) {
                return;
            }
            
            // Check if the form has data-ajax attribute for AJAX submission
            if (form.hasAttribute('data-ajax')) {
                event.preventDefault();
                this.handleAjaxFormSubmit(form);
            }
        });
    },
    
    /**
     * Apply the current theme
     */
    applyTheme() {
        // Add/remove dark theme class on the document element
        if (this.state.darkMode) {
            document.documentElement.classList.add('dark-theme');
            document.documentElement.classList.remove('light-theme');
        } else {
            document.documentElement.classList.add('light-theme');
            document.documentElement.classList.remove('dark-theme');
        }
        
        // Apply theme variables
        const themeVars = this.state.darkMode ? 
            this.config.themes.dark : 
            this.config.themes.light;
        
        Object.entries(themeVars).forEach(([property, value]) => {
            document.documentElement.style.setProperty(property, value);
        });
        
        // Store preference
        localStorage.setItem(this.config.darkModeStorageKey, this.state.darkMode.toString());
        
        // Update theme color meta tag for mobile browsers
        const metaThemeColor = document.querySelector('meta[name="theme-color"]');
        if (metaThemeColor) {
            metaThemeColor.setAttribute('content', themeVars['--background-color']);
        }
        
        // Dispatch theme change event
        window.dispatchEvent(new CustomEvent('theme:change', { 
            detail: { 
                darkMode: this.state.darkMode 
            } 
        }));
    },
    
    /**
     * Toggle between light and dark theme
     */
    toggleTheme() {
        this.state.darkMode = !this.state.darkMode;
        this.applyTheme();
    },
    
    /**
     * Update UI based on authentication status
     */
    updateAuthUI() {
        // Update login/logout buttons
        document.querySelectorAll('[data-auth-logged-in]').forEach(element => {
            element.style.display = this.state.userAuthenticated ? 'block' : 'none';
        });
        
        document.querySelectorAll('[data-auth-logged-out]').forEach(element => {
            element.style.display = this.state.userAuthenticated ? 'none' : 'block';
        });
        
        // Update API status indicators
        document.querySelectorAll('[data-api-status]').forEach(element => {
            element.style.display = this.state.apiAvailable ? 'none' : 'block';
        });
    },
    
    /**
     * Update media type based on window size
     */
    updateMediaType() {
        const width = window.innerWidth;
        let mediaType = 'desktop';
        
        if (width < this.config.breakpoints.mobile) {
            mediaType = 'mobile';
        } else if (width < this.config.breakpoints.tablet) {
            mediaType = 'tablet';
        }
        
        // Only update if changed
        if (mediaType !== this.state.mediaType) {
            const oldMediaType = this.state.mediaType;
            this.state.mediaType = mediaType;
            
            // Dispatch event
            window.dispatchEvent(new CustomEvent('media:change', { 
                detail: { 
                    oldMediaType, 
                    newMediaType: mediaType 
                } 
            }));
        }
    },
    
    /**
     * Handle network status changes
     */
    handleNetworkStatusChange() {
        // Show notification
        if (window.UIUtils && typeof window.UIUtils.showToast === 'function') {
            if (this.state.networkStatus === 'online') {
                window.UIUtils.showToast('You are back online', 'success');
            } else {
                window.UIUtils.showToast('You are offline. Some features may be unavailable.', 'warning');
            }
        }
        
        // Dispatch event
        window.dispatchEvent(new CustomEvent('network:change', { 
            detail: { 
                status: this.state.networkStatus 
            } 
        }));
    },
    
    /**
     * Handle AJAX form submissions
     * @param {HTMLFormElement} form - The form element
     */
    async handleAjaxFormSubmit(form) {
        // Create FormData from the form
        const formData = new FormData(form);
        
        // Show loading state
        const submitButton = form.querySelector('[type="submit"]');
        if (submitButton) {
            const originalText = submitButton.textContent;
            submitButton.disabled = true;
            submitButton.classList.add('loading');
            submitButton.textContent = 'Submitting...';
        }
        
        try {
            // Get the action URL
            const action = form.getAttribute('action') || window.location.pathname;
            
            // Make the request
            const response = await fetch(action, {
                method: form.getAttribute('method') || 'POST',
                body: formData,
                headers: {
                    'Accept': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`Form submission failed: ${response.status}`);
            }
            
            // Parse response
            const data = await response.json();
            
            // Show success message
            if (window.UIUtils && typeof window.UIUtils.showToast === 'function') {
                window.UIUtils.showToast(data.message || 'Form submitted successfully', 'success');
            }
            
            // Reset form if needed
            if (form.hasAttribute('data-reset-on-success')) {
                form.reset();
            }
            
            // Redirect if response includes a redirect_url
            if (data.redirect_url) {
                window.location.href = data.redirect_url;
                return;
            }
            
            // Execute success callback if defined
            const successCallback = form.getAttribute('data-success-callback');
            if (successCallback && typeof window[successCallback] === 'function') {
                window[successCallback](data);
            }
            
            // Dispatch form:success event
            form.dispatchEvent(new CustomEvent('form:success', { detail: data }));
        } catch (error) {
            console.error('Form submission error:', error);
            
            // Show error message
            if (window.UIUtils && typeof window.UIUtils.showToast === 'function') {
                window.UIUtils.showToast(error.message || 'An error occurred while submitting the form', 'error');
            }
            
            // Execute error callback if defined
            const errorCallback = form.getAttribute('data-error-callback');
            if (errorCallback && typeof window[errorCallback] === 'function') {
                window[errorCallback](error);
            }
            
            // Dispatch form:error event
            form.dispatchEvent(new CustomEvent('form:error', { detail: error }));
        } finally {
            // Restore button state
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.classList.remove('loading');
                submitButton.textContent = submitButton.getAttribute('data-original-text') || 'Submit';
            }
        }
    },
    
    /**
     * Show a notification to the user
     * @param {string} message - Notification message
     * @param {string} type - Notification type (info, success, warning, error)
     * @param {number} duration - Duration in milliseconds
     */
    notify(message, type = 'info', duration = 5000) {
        if (window.UIUtils && typeof window.UIUtils.showToast === 'function') {
            window.UIUtils.showToast(message, type, duration);
        } else {
            console.log(`Notification (${type}): ${message}`);
            // Queue notifications if toast system not ready
            this.state.pendingNotifications.push({
                message,
                type,
                duration
            });
        }
    },
    
    /**
     * Show pending notifications
     */
    showPendingNotifications() {
        if (window.UIUtils && typeof window.UIUtils.showToast === 'function' && this.state.pendingNotifications.length > 0) {
            // Show pending notifications with a slight delay between each
            this.state.pendingNotifications.forEach((notification, index) => {
                setTimeout(() => {
                    window.UIUtils.showToast(
                        notification.message,
                        notification.type,
                        notification.duration
                    );
                }, index * 300);
            });
            
            // Clear pending notifications
            this.state.pendingNotifications = [];
        }
    },
    
    /**
     * Simple debounce function
     * @param {Function} func - Function to debounce
     * @param {number} wait - Wait time in milliseconds
     * @return {Function} - Debounced function
     */
    debounce(func, wait = 100) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }
};

// Initialize App on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    // Initialize App with any configuration from global settings
    const config = window.__APP_CONFIG || {};
    App.init(config);
    
    // If UIUtils is loaded later, process pending notifications
    if (window.UIUtils) {
        App.showPendingNotifications();
    } else {
        // Wait for UIUtils to be available
        window.addEventListener('load', () => {
            setTimeout(() => {
                if (window.UIUtils) {
                    App.showPendingNotifications();
                }
            }, 500);
        });
    }
    
    // Expose App globally
    window.App = App;
});

/**
 * Affiliate Dashboard Component
 * Displays referral program data and stats
 */
class AffiliateDashboard {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        
        // Default options
        this.options = {
            apiEndpoint: '/api/affiliate/stats',
            refreshInterval: 300000, // 5 minutes in ms
            showSampleData: true,
            onCopyLink: null,
            ...options
        };
        
        // Stats state
        this.stats = {
            referralCode: 'NSSHORTS' + Math.floor(1000 + Math.random() * 9000), // Mock referral code
            referralLink: `https://novasounds.app/r/${this.options.userId || 'demo'}`,
            earnings: {
                total: 0,
                today: 0,
                thisMonth: 0,
                pending: 0
            },
            metrics: {
                clicks: 0,
                signups: 0,
                conversionRate: 0,
                paidConversions: 0
            },
            recentReferrals: []
        };
        
        // Initialize dashboard
        this.initialize();
    }
    
    initialize() {
        if (!this.container) {
            console.error(`Container element with ID "${this.containerId}" not found`);
            return;
        }
        
        // Create UI
        this.createUI();
        
        // Load data
        this.loadAffiliateStats();
        
        // Set up automatic refresh
        if (this.options.refreshInterval > 0) {
            this.refreshInterval = setInterval(() => {
                this.loadAffiliateStats();
            }, this.options.refreshInterval);
        }
    }
    
    createUI() {
        this.container.innerHTML = `
            <div class="affiliate-dashboard">
                <div class="row mb-4">
                    <div class="col-md-6 mb-3 mb-md-0">
                        <div class="card h-100">
                            <div class="card-header">
                                <h5 class="mb-0">Your Referral Link</h5>
                            </div>
                            <div class="card-body">
                                <div class="input-group mb-3">
                                    <input type="text" class="form-control" id="referral-link" value="${this.stats.referralLink}" readonly>
                                    <button class="btn btn-outline-primary" type="button" id="copy-link-btn">
                                        <i class="bi bi-clipboard"></i> Copy
                                    </button>
                                </div>
                                <div class="text-muted small">
                                    <i class="bi bi-info-circle"></i> Share this link with friends, followers, or on social media to earn commissions
                                </div>
                                <div class="mt-3">
                                    <div class="d-flex justify-content-between">
                                        <span>Your referral code:</span>
                                        <span class="fw-bold">${this.stats.referralCode}</span>
                                    </div>
                                </div>
                            </div>
                            <div class="card-footer bg-light d-flex justify-content-between">
                                <button class="btn btn-sm btn-outline-primary" id="social-share-btn">
                                    <i class="bi bi-share"></i> Share on Social
                                </button>
                                <button class="btn btn-sm btn-outline-secondary" id="marketing-materials-btn">
                                    <i class="bi bi-palette"></i> Marketing Materials
                                </button>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card h-100">
                            <div class="card-header">
                                <h5 class="mb-0">Commission Summary</h5>
                            </div>
                            <div class="card-body">
                                <div class="row">
                                    <div class="col-6 mb-3">
                                        <div class="text-muted small">Total Earnings</div>
                                        <div class="h4" id="total-earnings">$0.00</div>
                                    </div>
                                    <div class="col-6 mb-3">
                                        <div class="text-muted small">Today</div>
                                        <div class="h4" id="today-earnings">$0.00</div>
                                    </div>
                                    <div class="col-6">
                                        <div class="text-muted small">This Month</div>
                                        <div class="h4" id="month-earnings">$0.00</div>
                                    </div>
                                    <div class="col-6">
                                        <div class="text-muted small">Pending</div>
                                        <div class="h4" id="pending-earnings">$0.00</div>
                                    </div>
                                </div>
                            </div>
                            <div class="card-footer bg-light text-end">
                                <button class="btn btn-sm btn-primary" id="withdraw-btn">
                                    <i class="bi bi-wallet"></i> Withdraw Funds
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-md-8 mb-3 mb-md-0">
                        <div class="card h-100">
                            <div class="card-header d-flex justify-content-between align-items-center">
                                <h5 class="mb-0">Performance Metrics</h5>
                                <div class="btn-group btn-group-sm" role="group" aria-label="Time period">
                                    <button type="button" class="btn btn-outline-primary active" data-period="week">Week</button>
                                    <button type="button" class="btn btn-outline-primary" data-period="month">Month</button>
                                    <button type="button" class="btn btn-outline-primary" data-period="year">Year</button>
                                </div>
                            </div>
                            <div class="card-body">
                                <div class="chart-container" style="position: relative; height:250px;">
                                    <canvas id="performance-chart"></canvas>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card h-100">
                            <div class="card-header">
                                <h5 class="mb-0">Metrics</h5>
                            </div>
                            <div class="card-body p-0">
                                <ul class="list-group list-group-flush">
                                    <li class="list-group-item d-flex justify-content-between align-items-center">
                                        <div>
                                            <i class="bi bi-cursor-fill text-primary me-2"></i> Link Clicks
                                        </div>
                                        <span class="badge bg-primary rounded-pill" id="metric-clicks">0</span>
                                    </li>
                                    <li class="list-group-item d-flex justify-content-between align-items-center">
                                        <div>
                                            <i class="bi bi-person-plus-fill text-success me-2"></i> Signups
                                        </div>
                                        <span class="badge bg-success rounded-pill" id="metric-signups">0</span>
                                    </li>
                                    <li class="list-group-item d-flex justify-content-between align-items-center">
                                        <div>
                                            <i class="bi bi-coin text-warning me-2"></i> Paid Conversions
                                        </div>
                                        <span class="badge bg-warning text-dark rounded-pill" id="metric-conversions">0</span>
                                    </li>
                                    <li class="list-group-item d-flex justify-content-between align-items-center">
                                        <div>
                                            <i class="bi bi-percent text-info me-2"></i> Conversion Rate
                                        </div>
                                        <span class="badge bg-info text-dark rounded-pill" id="metric-rate">0%</span>
                                    </li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row mt-4">
                    <div class="col-12">
                        <div class="card">
                            <div class="card-header d-flex justify-content-between align-items-center">
                                <h5 class="mb-0">Recent Referrals</h5>
                                <button class="btn btn-sm btn-outline-primary" id="view-all-referrals">View All</button>
                            </div>
                            <div class="card-body p-0">
                                <div class="table-responsive">
                                    <table class="table table-hover mb-0">
                                        <thead>
                                            <tr>
                                                <th>User</th>
                                                <th>Date</th>
                                                <th>Plan</th>
                                                <th>Status</th>
                                                <th class="text-end">Commission</th>
                                            </tr>
                                        </thead>
                                        <tbody id="recent-referrals">
                                            <tr>
                                                <td colspan="5" class="text-center py-3">No referrals yet</td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Set up event listeners
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Copy referral link
        const copyLinkBtn = document.getElementById('copy-link-btn');
        if (copyLinkBtn) {
            copyLinkBtn.addEventListener('click', () => {
                this.copyReferralLink();
            });
        }
        
        // Social share button
        const socialShareBtn = document.getElementById('social-share-btn');
        if (socialShareBtn) {
            socialShareBtn.addEventListener('click', () => {
                this.showSocialShareModal();
            });
        }
        
        // Marketing materials button
        const marketingMaterialsBtn = document.getElementById('marketing-materials-btn');
        if (marketingMaterialsBtn) {
            marketingMaterialsBtn.addEventListener('click', () => {
                this.showMarketingMaterials();
            });
        }
        
        // Withdraw button
        const withdrawBtn = document.getElementById('withdraw-btn');
        if (withdrawBtn) {
            withdrawBtn.addEventListener('click', () => {
                this.showWithdrawModal();
            });
        }
        
        // Period selector buttons
        const periodButtons = document.querySelectorAll('[data-period]');
        periodButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                // Remove active class from all buttons
                periodButtons.forEach(btn => {
                    btn.classList.remove('active');
                });
                // Add active class to clicked button
                e.target.classList.add('active');
                // Update chart for selected period
                this.updateChart(e.target.dataset.period);
            });
        });
        
        // View all referrals button
        const viewAllBtn = document.getElementById('view-all-referrals');
        if (viewAllBtn) {
            viewAllBtn.addEventListener('click', () => {
                this.showAllReferrals();
            });
        }
    }
    
    async loadAffiliateStats() {
        try {
            if (this.options.showSampleData) {
                // Load sample data for demo purposes
                this.loadSampleData();
                return;
            }
            
            const response = await fetch(this.options.apiEndpoint);
            
            if (!response.ok) {
                throw new Error(`Failed to load affiliate stats: ${response.status}`);
            }
            
            const data = await response.json();
            this.stats = data;
            
            // Update UI with the loaded data
            this.updateStats();
            
        } catch (error) {
            console.error('Error loading affiliate stats:', error);
            
            // If API fails, load sample data as fallback
            this.loadSampleData();
        }
    }
    
    loadSampleData() {
        // Sample data for demo purposes
        this.stats = {
            referralCode: this.stats.referralCode,
            referralLink: this.stats.referralLink,
            earnings: {
                total: 527.75,
                today: 12.50,
                thisMonth: 89.25,
                pending: 45.00
            },
            metrics: {
                clicks: 842,
                signups: 53,
                conversionRate: 6.3,
                paidConversions: 21
            },
            recentReferrals: [
                {
                    user: 'john.d@example.com',
                    date: '2023-06-15',
                    plan: 'Pro Plan',
                    status: 'active',
                    commission: 15.00
                },
                {
                    user: 'maria82@example.com',
                    date: '2023-06-12',
                    plan: 'Premium Plan',
                    status: 'active',
                    commission: 25.00
                },
                {
                    user: 'alex.smith@example.com',
                    date: '2023-06-10',
                    plan: 'Basic Plan',
                    status: 'trial',
                    commission: 0.00
                },
                {
                    user: 'sarah.j@example.com',
                    date: '2023-06-05',
                    plan: 'Pro Plan',
                    status: 'active',
                    commission: 15.00
                },
                {
                    user: 'mike.thomas@example.com',
                    date: '2023-06-01',
                    plan: 'Pro Plan',
                    status: 'inactive',
                    commission: 0.00
                }
            ],
            chartData: {
                week: {
                    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    earnings: [5, 12, 0, 8, 15, 5, 12.5],
                    clicks: [45, 62, 75, 30, 54, 89, 120]
                },
                month: {
                    labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
                    earnings: [32, 18, 24, 15],
                    clicks: [210, 180, 250, 202]
                },
                year: {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                    earnings: [45, 38, 65, 27, 48, 89, 0, 0, 0, 0, 0, 0],
                    clicks: [320, 280, 450, 210, 390, 842, 0, 0, 0, 0, 0, 0]
                }
            }
        };
        
        // Update UI with sample data
        this.updateStats();
    }
    
    updateStats() {
        // Update earnings
        document.getElementById('total-earnings').textContent = `$${this.stats.earnings.total.toFixed(2)}`;
        document.getElementById('today-earnings').textContent = `$${this.stats.earnings.today.toFixed(2)}`;
        document.getElementById('month-earnings').textContent = `$${this.stats.earnings.thisMonth.toFixed(2)}`;
        document.getElementById('pending-earnings').textContent = `$${this.stats.earnings.pending.toFixed(2)}`;
        
        // Update metrics
        document.getElementById('metric-clicks').textContent = this.stats.metrics.clicks;
        document.getElementById('metric-signups').textContent = this.stats.metrics.signups;
        document.getElementById('metric-conversions').textContent = this.stats.metrics.paidConversions;
        document.getElementById('metric-rate').textContent = `${this.stats.metrics.conversionRate}%`;
        
        // Update recent referrals
        this.updateReferralsTable();
        
        // Update chart
        this.updateChart('week');
    }
    
    updateReferralsTable() {
        const tableBody = document.getElementById('recent-referrals');
        
        if (!tableBody) return;
        
        if (!this.stats.recentReferrals || this.stats.recentReferrals.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center py-3">No referrals yet</td>
                </tr>
            `;
            return;
        }
        
        tableBody.innerHTML = '';
        
        this.stats.recentReferrals.forEach(referral => {
            const tr = document.createElement('tr');
            
            // Format date
            const date = new Date(referral.date);
            const formattedDate = date.toLocaleDateString(undefined, {
                month: 'short',
                day: 'numeric',
                year: 'numeric'
            });
            
            // Determine status badge class
            let statusClass = 'bg-secondary';
            switch (referral.status) {
                case 'active':
                    statusClass = 'bg-success';
                    break;
                case 'trial':
                    statusClass = 'bg-info';
                    break;
                case 'inactive':
                    statusClass = 'bg-danger';
                    break;
            }
            
            tr.innerHTML = `
                <td>${referral.user}</td>
                <td>${formattedDate}</td>
                <td>${referral.plan}</td>
                <td><span class="badge ${statusClass}">${referral.status}</span></td>
                <td class="text-end">${referral.commission > 0 ? '$' + referral.commission.toFixed(2) : '-'}</td>
            `;
            
            tableBody.appendChild(tr);
        });
    }
    
    updateChart(period) {
        if (!this.stats.chartData || !this.stats.chartData[period]) return;
        
        const data = this.stats.chartData[period];
        const ctx = document.getElementById('performance-chart');
        
        if (!ctx) return;
        
        // Destroy existing chart if any
        if (this.chart) {
            this.chart.destroy();
        }
        
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [
                    {
                        label: 'Earnings ($)',
                        data: data.earnings,
                        borderColor: '#0d6efd',
                        backgroundColor: 'rgba(13, 110, 253, 0.1)',
                        tension: 0.4,
                        yAxisID: 'y',
                        fill: true
                    },
                    {
                        label: 'Clicks',
                        data: data.clicks,
                        borderColor: '#6f42c1',
                        backgroundColor: 'rgba(111, 66, 193, 0.1)',
                        tension: 0.4,
                        yAxisID: 'y1',
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Earnings ($)'
                        }
                    },
                    y1: {
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Clicks'
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        });
    }
    
    copyReferralLink() {
        const linkInput = document.getElementById('referral-link');
        
        if (!linkInput) return;
        
        // Select the text
        linkInput.select();
        linkInput.setSelectionRange(0, 99999); // For mobile devices
        
        // Copy to clipboard
        navigator.clipboard.writeText(linkInput.value).then(() => {
            // Show success message
            const originalText = document.getElementById('copy-link-btn').innerHTML;
            document.getElementById('copy-link-btn').innerHTML = '<i class="bi bi-check-lg"></i> Copied!';
            
            // Reset button text after 2 seconds
            setTimeout(() => {
                document.getElementById('copy-link-btn').innerHTML = originalText;
            }, 2000);
            
            // Call callback if provided
            if (typeof this.options.onCopyLink === 'function') {
                this.options.onCopyLink(linkInput.value);
            }
        }).catch(err => {
            console.error('Failed to copy link:', err);
        });
    }
    
    showSocialShareModal() {
        // Implementation for showing a social share modal
        alert('Share your referral link on social media: ' + this.stats.referralLink);
    }
    
    showMarketingMaterials() {
        // Implementation for showing marketing materials
        alert('Marketing materials will be available soon!');
    }
    
    showWithdrawModal() {
        // Implementation for showing withdraw modal
        if (this.stats.earnings.total < 50) {
            alert('You need at least $50 to withdraw funds. Current balance: $' + this.stats.earnings.total.toFixed(2));
        } else {
            alert('Withdraw $' + this.stats.earnings.total.toFixed(2) + ' to your connected payment method');
        }
    }
    
    showAllReferrals() {
        // Implementation for showing all referrals
        alert('View all your referrals in the full dashboard');
    }
}

// Export to global namespace
window.AffiliateDashboard = AffiliateDashboard; 