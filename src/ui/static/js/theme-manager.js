/**
 * Theme Manager
 * Handles theme preference, dark/light mode toggle, and a11y preferences
 */

class ThemeManager {
    constructor() {
        // Theme state
        this.isDarkMode = false;
        this.isHighContrast = false;
        this.prefersReducedMotion = false;
        this.currentPrimaryColor = '#0071e3';

        // DOM Elements
        this.themeToggle = null;
        this.themeSettings = null;
        this.themeSettingsToggle = null;
        this.contrastToggle = null;
        this.colorOptions = null;

        // Initialize on DOM load
        document.addEventListener('DOMContentLoaded', () => this.init());
    }

    /**
     * Initialize theme manager
     */
    init() {
        // Create and append theme toggle if it doesn't exist
        this.createThemeToggle();
        // Create theme settings panel
        this.createThemeSettings();
        
        // Check user preferences
        this.checkSystemPreferences();
        this.loadSavedPreferences();
        
        // Apply initial theme
        this.applyTheme();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Initialize focus-visible polyfill
        this.initFocusVisible();
        
        // Initialize live announcer for screen readers
        this.initLiveAnnouncer();
    }

    /**
     * Create theme toggle button
     */
    createThemeToggle() {
        if (document.querySelector('.theme-toggle')) {
            this.themeToggle = document.querySelector('.theme-toggle');
            return;
        }
        
        this.themeToggle = document.createElement('button');
        this.themeToggle.className = 'theme-toggle';
        this.themeToggle.setAttribute('aria-label', 'Toggle dark mode');
        this.themeToggle.setAttribute('type', 'button');
        
        const sunIcon = document.createElement('span');
        sunIcon.className = 'theme-toggle-icon sun';
        sunIcon.innerHTML = '☀️';
        
        const moonIcon = document.createElement('span');
        moonIcon.className = 'theme-toggle-icon moon';
        moonIcon.innerHTML = '🌙';
        
        const handle = document.createElement('span');
        handle.className = 'theme-toggle-handle';
        
        this.themeToggle.appendChild(sunIcon);
        this.themeToggle.appendChild(moonIcon);
        this.themeToggle.appendChild(handle);
        
        // Find a good place to append the toggle
        const header = document.querySelector('header');
        if (header) {
            // Check if there's a profile or user menu to append before/after
            const userMenu = header.querySelector('.user-menu') || header.querySelector('.profile');
            if (userMenu) {
                userMenu.parentNode.insertBefore(this.themeToggle, userMenu);
            } else {
                // Append to the end of the header
                header.appendChild(this.themeToggle);
            }
        } else {
            // If no header, append to body
            document.body.appendChild(this.themeToggle);
        }
    }

    /**
     * Create theme settings panel
     */
    createThemeSettings() {
        if (document.querySelector('.theme-settings')) {
            this.themeSettings = document.querySelector('.theme-settings');
            this.themeSettingsToggle = document.querySelector('.theme-settings-toggle');
            return;
        }
        
        // Create settings toggle button
        this.themeSettingsToggle = document.createElement('button');
        this.themeSettingsToggle.className = 'theme-settings-toggle';
        this.themeSettingsToggle.setAttribute('aria-label', 'Theme settings');
        this.themeSettingsToggle.setAttribute('aria-expanded', 'false');
        this.themeSettingsToggle.setAttribute('aria-controls', 'theme-settings-panel');
        this.themeSettingsToggle.innerHTML = '⚙️';
        
        // Create settings panel
        this.themeSettings = document.createElement('div');
        this.themeSettings.className = 'theme-settings';
        this.themeSettings.id = 'theme-settings-panel';
        this.themeSettings.setAttribute('role', 'dialog');
        this.themeSettings.setAttribute('aria-labelledby', 'theme-settings-title');
        
        // Panel content
        const title = document.createElement('h4');
        title.id = 'theme-settings-title';
        title.textContent = 'Appearance Settings';
        
        // Theme color options
        const colorSection = document.createElement('div');
        colorSection.className = 'theme-option';
        
        const colorLabel = document.createElement('span');
        colorLabel.className = 'theme-option-label';
        colorLabel.textContent = 'Primary Color';
        
        const colorOptions = document.createElement('div');
        colorOptions.className = 'theme-color-options';
        
        // Color options 
        const colors = [
            { name: 'blue', value: '#0071e3' },
            { name: 'green', value: '#2dd36f' },
            { name: 'purple', value: '#5856d6' },
            { name: 'orange', value: '#ff9f0a' },
            { name: 'red', value: '#ff453a' }
        ];
        
        colors.forEach(color => {
            const option = document.createElement('span');
            option.className = `theme-color-option primary-${color.name}`;
            option.setAttribute('data-color', color.value);
            option.setAttribute('role', 'button');
            option.setAttribute('tabindex', '0');
            option.setAttribute('aria-label', `Set ${color.name} as primary color`);
            
            if (color.value === this.currentPrimaryColor) {
                option.classList.add('active');
            }
            
            colorOptions.appendChild(option);
        });
        
        colorSection.appendChild(colorLabel);
        colorSection.appendChild(colorOptions);
        
        // Contrast mode toggle
        const contrastSection = document.createElement('div');
        contrastSection.className = 'contrast-toggle';
        
        this.contrastToggle = document.createElement('input');
        this.contrastToggle.type = 'checkbox';
        this.contrastToggle.id = 'contrast-toggle';
        
        const contrastLabel = document.createElement('label');
        contrastLabel.className = 'contrast-toggle-label';
        contrastLabel.htmlFor = 'contrast-toggle';
        contrastLabel.textContent = 'High contrast mode';
        
        contrastSection.appendChild(this.contrastToggle);
        contrastSection.appendChild(contrastLabel);
        
        // Assemble the panel
        this.themeSettings.appendChild(title);
        this.themeSettings.appendChild(colorSection);
        this.themeSettings.appendChild(contrastSection);
        
        // Add to the DOM
        document.body.appendChild(this.themeSettingsToggle);
        document.body.appendChild(this.themeSettings);
        
        // Store reference to color options
        this.colorOptions = colorOptions.querySelectorAll('.theme-color-option');
    }

    /**
     * Check system preferences
     */
    checkSystemPreferences() {
        // Check for dark mode preference
        this.isDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        // Check for reduced motion preference
        this.prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        
        // Check for contrast preference
        this.isHighContrast = window.matchMedia('(prefers-contrast: more)').matches;
    }

    /**
     * Load saved user preferences from localStorage
     */
    loadSavedPreferences() {
        // Load theme preference
        const savedTheme = localStorage.getItem('theme-preference');
        if (savedTheme) {
            this.isDarkMode = savedTheme === 'dark';
        }
        
        // Load contrast preference
        const savedContrast = localStorage.getItem('high-contrast');
        if (savedContrast) {
            this.isHighContrast = savedContrast === 'true';
        }
        
        // Load color preference
        const savedColor = localStorage.getItem('primary-color');
        if (savedColor) {
            this.currentPrimaryColor = savedColor;
        }
    }

    /**
     * Apply current theme settings
     */
    applyTheme() {
        // Apply dark/light mode
        if (this.isDarkMode) {
            document.body.classList.add('dark-theme');
            this.themeToggle?.classList.add('dark');
        } else {
            document.body.classList.remove('dark-theme');
            this.themeToggle?.classList.remove('dark');
        }
        
        // Apply contrast mode
        if (this.isHighContrast) {
            document.body.classList.add('high-contrast');
            if (this.contrastToggle) {
                this.contrastToggle.checked = true;
            }
        } else {
            document.body.classList.remove('high-contrast');
            if (this.contrastToggle) {
                this.contrastToggle.checked = false;
            }
        }
        
        // Apply primary color
        document.documentElement.style.setProperty('--primary-color', this.currentPrimaryColor);
        
        // Convert hex to RGB for CSS variables
        const hexToRgb = (hex) => {
            const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
            return result ? 
                `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}` : 
                '0, 113, 227'; // Default fallback
        };
        
        document.documentElement.style.setProperty('--primary-color-rgb', hexToRgb(this.currentPrimaryColor));
        
        // Update color option active state
        if (this.colorOptions) {
            this.colorOptions.forEach(option => {
                if (option.getAttribute('data-color') === this.currentPrimaryColor) {
                    option.classList.add('active');
                } else {
                    option.classList.remove('active');
                }
            });
        }
        
        // Also set as accent color
        document.documentElement.style.setProperty('--accent-color', this.currentPrimaryColor);
        document.documentElement.style.setProperty('--accent-color-rgb', hexToRgb(this.currentPrimaryColor));
        
        // Announce theme change to screen readers
        this.announce(`Theme changed to ${this.isDarkMode ? 'dark' : 'light'} mode.`);
    }

    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Theme toggle click
        this.themeToggle?.addEventListener('click', () => {
            this.isDarkMode = !this.isDarkMode;
            localStorage.setItem('theme-preference', this.isDarkMode ? 'dark' : 'light');
            this.applyTheme();
        });
        
        // Theme toggle keyboard
        this.themeToggle?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.isDarkMode = !this.isDarkMode;
                localStorage.setItem('theme-preference', this.isDarkMode ? 'dark' : 'light');
                this.applyTheme();
            }
        });
        
        // Settings toggle click
        this.themeSettingsToggle?.addEventListener('click', () => {
            const isOpen = this.themeSettings.classList.contains('open');
            this.themeSettings.classList.toggle('open');
            this.themeSettingsToggle.setAttribute('aria-expanded', !isOpen);
            
            if (!isOpen) {
                // Set focus to the settings panel
                this.themeSettings.focus();
            }
        });
        
        // Color option click
        this.colorOptions?.forEach(option => {
            option.addEventListener('click', () => {
                const color = option.getAttribute('data-color');
                this.currentPrimaryColor = color;
                localStorage.setItem('primary-color', color);
                this.applyTheme();
            });
            
            // Keyboard support
            option.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    const color = option.getAttribute('data-color');
                    this.currentPrimaryColor = color;
                    localStorage.setItem('primary-color', color);
                    this.applyTheme();
                }
            });
        });
        
        // Contrast toggle
        this.contrastToggle?.addEventListener('change', () => {
            this.isHighContrast = this.contrastToggle.checked;
            localStorage.setItem('high-contrast', this.isHighContrast);
            this.applyTheme();
        });
        
        // Close settings when clicking outside
        document.addEventListener('click', (e) => {
            if (this.themeSettings?.classList.contains('open') && 
                !this.themeSettings.contains(e.target) && 
                e.target !== this.themeSettingsToggle) {
                this.themeSettings.classList.remove('open');
                this.themeSettingsToggle.setAttribute('aria-expanded', 'false');
            }
        });
        
        // Escape key to close settings
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.themeSettings?.classList.contains('open')) {
                this.themeSettings.classList.remove('open');
                this.themeSettingsToggle.setAttribute('aria-expanded', 'false');
                this.themeSettingsToggle.focus();
            }
        });
        
        // System preference changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            // Only update if user hasn't explicitly chosen a theme
            if (!localStorage.getItem('theme-preference')) {
                this.isDarkMode = e.matches;
                this.applyTheme();
            }
        });
        
        window.matchMedia('(prefers-contrast: more)').addEventListener('change', (e) => {
            // Only update if user hasn't explicitly chosen a contrast setting
            if (!localStorage.getItem('high-contrast')) {
                this.isHighContrast = e.matches;
                this.applyTheme();
            }
        });
    }

    /**
     * Initialize focus-visible polyfill
     */
    initFocusVisible() {
        // Add the js-focus-visible class to the body
        document.body.classList.add('js-focus-visible');
        
        // Track current input method (mouse vs keyboard)
        let hadKeyboardEvent = false;
        
        function handleKeyDown(e) {
            if (e.key === 'Tab' || (e.key >= 'a' && e.key <= 'z') || e.key === 'Enter' || e.key === ' ') {
                hadKeyboardEvent = true;
            }
        }
        
        function handlePointerDown() {
            hadKeyboardEvent = false;
        }
        
        function handleFocus(e) {
            if (hadKeyboardEvent) {
                e.target.classList.add('focus-visible');
            }
        }
        
        function handleBlur(e) {
            e.target.classList.remove('focus-visible');
        }
        
        document.addEventListener('keydown', handleKeyDown, true);
        document.addEventListener('mousedown', handlePointerDown, true);
        document.addEventListener('pointerdown', handlePointerDown, true);
        document.addEventListener('touchstart', handlePointerDown, true);
        document.addEventListener('focus', handleFocus, true);
        document.addEventListener('blur', handleBlur, true);
    }

    /**
     * Initialize live announcer for screen readers
     */
    initLiveAnnouncer() {
        if (document.getElementById('live-announcer')) {
            return;
        }
        
        const announcer = document.createElement('div');
        announcer.id = 'live-announcer';
        announcer.className = 'live-announcer';
        announcer.setAttribute('aria-live', 'polite');
        announcer.setAttribute('aria-atomic', 'true');
        
        document.body.appendChild(announcer);
    }

    /**
     * Announce message to screen readers
     * @param {string} message - Message to announce
     */
    announce(message) {
        const announcer = document.getElementById('live-announcer');
        if (!announcer) return;
        
        announcer.textContent = '';
        // Force browser to acknowledge the empty state before adding new content
        setTimeout(() => {
            announcer.textContent = message;
        }, 50);
    }
}

// Initialize the theme manager
const themeManager = new ThemeManager();

// Export for module use
if (typeof module !== 'undefined') {
    module.exports = themeManager;
} 