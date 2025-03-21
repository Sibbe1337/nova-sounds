/**
 * Theme Switcher
 * Handles switching between light and dark themes
 */

// Theme settings
const ThemeSwitcher = {
    // Theme storage key
    storageKey: 'darkMode',
    
    // Current theme state
    isDarkMode: false,
    
    // Default themes (can be extended via init options)
    themes: {
        light: {
            '--primary-color': '#0071e3',
            '--primary-color-rgb': '0, 113, 227',
            '--background-color': '#f5f5f7',
            '--card-bg': '#ffffff',
            '--text-color': '#333333',
            '--text-color-light': '#86868b',
            '--border-color': '#d2d2d7',
            '--success-color': '#28a745',
            '--error-color': '#dc3545',
            '--warning-color': '#ffc107',
            '--info-color': '#17a2b8'
        },
        dark: {
            '--primary-color': '#0a84ff',
            '--primary-color-rgb': '10, 132, 255',
            '--background-color': '#1c1c1e',
            '--card-bg': '#2c2c2e',
            '--text-color': '#f5f5f7',
            '--text-color-light': '#98989d',
            '--border-color': '#3a3a3c',
            '--success-color': '#2dd36f',
            '--error-color': '#ff453a',
            '--warning-color': '#ffd60a',
            '--info-color': '#64d2ff'
        }
    },
    
    /**
     * Initialize theme switcher
     * @param {Object} options - Configuration options
     */
    init(options = {}) {
        // Merge options
        if (options.themes) {
            if (options.themes.light) {
                Object.assign(this.themes.light, options.themes.light);
            }
            if (options.themes.dark) {
                Object.assign(this.themes.dark, options.themes.dark);
            }
        }
        
        this.storageKey = options.storageKey || this.storageKey;
        
        // Get initial theme setting
        this.setInitialTheme();
        
        // Set up theme toggle listeners
        this.setupListeners();
        
        // Apply initial theme
        this.applyTheme();
    },
    
    /**
     * Set initial theme based on user preference or system setting
     */
    setInitialTheme() {
        // Check for stored preference
        const storedTheme = localStorage.getItem(this.storageKey);
        
        if (storedTheme !== null) {
            this.isDarkMode = storedTheme === 'true';
        } else {
            // Check system preference
            this.isDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
        }
    },
    
    /**
     * Setup event listeners for theme toggles
     */
    setupListeners() {
        // Listen for OS theme changes if no stored preference
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (localStorage.getItem(this.storageKey) === null) {
                this.isDarkMode = e.matches;
                this.applyTheme();
            }
        });
        
        // Setup theme toggle buttons
        document.querySelectorAll('[data-theme-toggle]').forEach(toggle => {
            // Set initial state
            if (toggle.tagName === 'INPUT' && toggle.type === 'checkbox') {
                toggle.checked = this.isDarkMode;
            }
            
            // Add click handler
            toggle.addEventListener('click', () => {
                this.toggleTheme();
            });
        });
    },
    
    /**
     * Apply the current theme
     */
    applyTheme() {
        // Add/remove theme classes
        if (this.isDarkMode) {
            document.documentElement.classList.add('dark-theme');
            document.documentElement.classList.remove('light-theme');
        } else {
            document.documentElement.classList.add('light-theme');
            document.documentElement.classList.remove('dark-theme');
        }
        
        // Apply CSS variables
        const theme = this.isDarkMode ? this.themes.dark : this.themes.light;
        Object.entries(theme).forEach(([property, value]) => {
            document.documentElement.style.setProperty(property, value);
        });
        
        // Store preference
        localStorage.setItem(this.storageKey, this.isDarkMode.toString());
        
        // Update theme color meta tag
        const metaThemeColor = document.querySelector('meta[name="theme-color"]');
        if (metaThemeColor) {
            metaThemeColor.setAttribute('content', theme['--background-color']);
        }
        
        // Update theme toggle states
        document.querySelectorAll('[data-theme-toggle]').forEach(toggle => {
            if (toggle.tagName === 'INPUT' && toggle.type === 'checkbox') {
                toggle.checked = this.isDarkMode;
            }
        });
        
        // Dispatch theme change event
        document.dispatchEvent(new CustomEvent('themechange', {
            detail: {
                theme: this.isDarkMode ? 'dark' : 'light',
                variables: theme
            }
        }));
    },
    
    /**
     * Toggle between light and dark theme
     */
    toggleTheme() {
        this.isDarkMode = !this.isDarkMode;
        this.applyTheme();
    },
    
    /**
     * Set theme directly
     * @param {string} theme - 'light' or 'dark'
     */
    setTheme(theme) {
        this.isDarkMode = theme === 'dark';
        this.applyTheme();
    },
    
    /**
     * Get current theme
     * @return {string} - 'light' or 'dark'
     */
    getTheme() {
        return this.isDarkMode ? 'dark' : 'light';
    }
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    ThemeSwitcher.init();
    
    // Expose globally
    window.ThemeSwitcher = ThemeSwitcher;
}); 