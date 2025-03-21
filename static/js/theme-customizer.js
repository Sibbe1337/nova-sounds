/**
 * Theme Customizer
 * 
 * A component that allows users to customize the UI theme,
 * including color schemes, font sizes, and accessibility options.
 */

// Check if window.__scriptExecuted already exists for this file
if (window.__scriptExecuted && window.__scriptExecuted['theme-customizer.js']) {
  console.log('theme-customizer.js already executed, skipping duplicate execution');
} else {
  // Mark this script as executed
  window.__scriptExecuted = window.__scriptExecuted || {};
  window.__scriptExecuted['theme-customizer.js'] = true;
  
  // Main implementation wrapped in an IIFE
  (function(window) {
    // Skip if already defined
    if (window.ThemeCustomizer) {
      console.log('ThemeCustomizer already defined, skipping redefinition');
      return;
    }
    
    /**
     * Theme Customizer implementation
     */
    class ThemeCustomizerClass {
      constructor(options = {}) {
        this.options = {
          // Default colors
          colors: {
            primary: '#0071e3',
            success: '#34c759',
            warning: '#ff9500',
            danger: '#ff3b30',
            info: '#5ac8fa'
          },
          // Default font sizes
          fontSizes: {
            small: '0.9rem',
            normal: '1rem',
            large: '1.1rem',
            xlarge: '1.2rem'
          },
          // Other options
          showResetButton: true,
          localStorageKey: 'theme-customizer',
          // Allow passing a callback function to run after theme changes
          onThemeChange: null,
          ...options
        };
        
        // Initialize class properties
        this.currentTheme = {
          mode: this.getSystemPreference(),
          primaryColor: this.options.colors.primary,
          fontSize: 'normal'
        };
        
        // Load saved preferences
        this.loadPreferences();
        
        // Apply initial theme
        this.applyTheme();
        
        // Set up the UI if container is provided
        if (options.container) {
          this.container = typeof options.container === 'string' 
            ? document.getElementById(options.container)
            : options.container;
          
          if (this.container) {
            this.renderUI();
          }
        }
      }
      
      /**
       * Get system color scheme preference
       */
      getSystemPreference() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      }
      
      /**
       * Load saved preferences from localStorage
       */
      loadPreferences() {
        try {
          const savedPrefs = localStorage.getItem(this.options.localStorageKey);
          if (savedPrefs) {
            const prefs = JSON.parse(savedPrefs);
            this.currentTheme = { ...this.currentTheme, ...prefs };
          }
        } catch (e) {
          console.error('Error loading theme preferences:', e);
        }
      }
      
      /**
       * Save current preferences to localStorage
       */
      savePreferences() {
        try {
          localStorage.setItem(
            this.options.localStorageKey, 
            JSON.stringify(this.currentTheme)
          );
        } catch (e) {
          console.error('Error saving theme preferences:', e);
        }
      }
      
      /**
       * Apply the current theme to the document
       */
      applyTheme() {
        // Apply dark/light mode
        document.body.classList.remove('dark-theme', 'light-theme');
        document.body.classList.add(`${this.currentTheme.mode}-theme`);
        
        // Apply font size
        document.body.classList.remove(
          'font-size-small',
          'font-size-normal',
          'font-size-large',
          'font-size-xlarge'
        );
        
        if (this.currentTheme.fontSize !== 'normal') {
          document.body.classList.add(`font-size-${this.currentTheme.fontSize}`);
        }
        
        // Apply colors using CSS variables
        this.applyColors();
        
        // Run callback if provided
        if (typeof this.options.onThemeChange === 'function') {
          this.options.onThemeChange(this.currentTheme);
        }
        
        // Save to localStorage
        this.savePreferences();
      }
      
      /**
       * Apply color CSS variables
       */
      applyColors() {
        // Create RGB representation of primary color for opacity variations
        const primaryRGB = this.hexToRgb(this.currentTheme.primaryColor);
        
        // Update CSS variables
        document.documentElement.style.setProperty('--primary-color', this.currentTheme.primaryColor);
        document.documentElement.style.setProperty('--primary-color-hover', this.adjustColor(this.currentTheme.primaryColor, 10));
        document.documentElement.style.setProperty('--primary-color-rgb', primaryRGB);
        
        // Also update all other colors if they're customized
        if (this.currentTheme.successColor) {
          document.documentElement.style.setProperty('--success-color', this.currentTheme.successColor);
        }
        if (this.currentTheme.warningColor) {
          document.documentElement.style.setProperty('--warning-color', this.currentTheme.warningColor);
        }
        if (this.currentTheme.dangerColor) {
          document.documentElement.style.setProperty('--danger-color', this.currentTheme.dangerColor);
        }
        if (this.currentTheme.infoColor) {
          document.documentElement.style.setProperty('--info-color', this.currentTheme.infoColor);
        }
      }
      
      /**
       * Convert hex color to RGB string
       */
      hexToRgb(hex) {
        // Expand shorthand form (e.g. "03F") to full form (e.g. "0033FF")
        const shorthandRegex = /^#?([a-f\d])([a-f\d])([a-f\d])$/i;
        hex = hex.replace(shorthandRegex, (m, r, g, b) => r + r + g + g + b + b);
      
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result
          ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}`
          : '0, 0, 0';
      }
      
      /**
       * Adjust a hex color by a percentage
       */
      adjustColor(color, percent) {
        let R = parseInt(color.substring(1, 3), 16);
        let G = parseInt(color.substring(3, 5), 16);
        let B = parseInt(color.substring(5, 7), 16);

        R = parseInt(R * (100 + percent) / 100);
        G = parseInt(G * (100 + percent) / 100);
        B = parseInt(B * (100 + percent) / 100);

        R = (R < 255) ? R : 255;
        G = (G < 255) ? G : 255;
        B = (B < 255) ? B : 255;

        const RR = ((R.toString(16).length === 1) ? `0${R.toString(16)}` : R.toString(16));
        const GG = ((G.toString(16).length === 1) ? `0${G.toString(16)}` : G.toString(16));
        const BB = ((B.toString(16).length === 1) ? `0${B.toString(16)}` : B.toString(16));

        return `#${RR}${GG}${BB}`;
      }
      
      /**
       * Set the theme mode
       */
      setThemeMode(mode) {
        if (mode === 'auto') {
          // Use system preference
          this.currentTheme.mode = this.getSystemPreference();
          // Remove from localStorage to follow system
          delete this.currentTheme.mode;
        } else if (mode === 'dark' || mode === 'light') {
          this.currentTheme.mode = mode;
        }
        
        this.applyTheme();
      }
      
      /**
       * Toggle between dark and light mode
       */
      toggleThemeMode() {
        this.setThemeMode(this.currentTheme.mode === 'dark' ? 'light' : 'dark');
      }
      
      /**
       * Set the primary color
       */
      setPrimaryColor(color) {
        if (/^#[0-9A-F]{6}$/i.test(color)) {
          this.currentTheme.primaryColor = color;
          this.applyTheme();
        }
      }
      
      /**
       * Set the font size
       */
      setFontSize(size) {
        if (['small', 'normal', 'large', 'xlarge'].includes(size)) {
          this.currentTheme.fontSize = size;
          this.applyTheme();
        }
      }
      
      /**
       * Reset all theme settings to defaults
       */
      resetTheme() {
        this.currentTheme = {
          mode: this.getSystemPreference(),
          primaryColor: this.options.colors.primary,
          fontSize: 'normal'
        };
        
        // Clear localStorage
        localStorage.removeItem(this.options.localStorageKey);
        
        // Apply the default theme
        this.applyTheme();
        
        // Update UI if it exists
        if (this.container) {
          this.updateUI();
        }
      }
      
      /**
       * Render the theme customizer UI
       */
      renderUI() {
        // Create the UI elements
        this.container.innerHTML = `
          <div class="theme-customizer">
            <h3 class="customizer-title">Customize Theme</h3>
            
            <div class="customizer-section">
              <h4 class="section-title">Theme Mode</h4>
              <div class="theme-mode-controls">
                <label class="mode-option">
                  <input type="radio" name="theme-mode" value="light" ${this.currentTheme.mode === 'light' ? 'checked' : ''}>
                  <span class="mode-label"><i class="fas fa-sun"></i> Light</span>
                </label>
                <label class="mode-option">
                  <input type="radio" name="theme-mode" value="dark" ${this.currentTheme.mode === 'dark' ? 'checked' : ''}>
                  <span class="mode-label"><i class="fas fa-moon"></i> Dark</span>
                </label>
                <label class="mode-option">
                  <input type="radio" name="theme-mode" value="auto">
                  <span class="mode-label"><i class="fas fa-sync-alt"></i> Auto</span>
                </label>
              </div>
            </div>
            
            <div class="customizer-section">
              <h4 class="section-title">Primary Color</h4>
              <div class="color-picker">
                <input type="color" id="primary-color-picker" value="${this.currentTheme.primaryColor}">
                <span class="color-value">${this.currentTheme.primaryColor}</span>
              </div>
            </div>
            
            <div class="customizer-section">
              <h4 class="section-title">Font Size</h4>
              <div class="font-size-controls">
                <button class="font-size-btn ${this.currentTheme.fontSize === 'small' ? 'active' : ''}" data-size="small">
                  <i class="fas fa-font"></i><span class="size-label">Small</span>
                </button>
                <button class="font-size-btn ${this.currentTheme.fontSize === 'normal' ? 'active' : ''}" data-size="normal">
                  <i class="fas fa-font"></i><span class="size-label">Normal</span>
                </button>
                <button class="font-size-btn ${this.currentTheme.fontSize === 'large' ? 'active' : ''}" data-size="large">
                  <i class="fas fa-font"></i><span class="size-label">Large</span>
                </button>
                <button class="font-size-btn ${this.currentTheme.fontSize === 'xlarge' ? 'active' : ''}" data-size="xlarge">
                  <i class="fas fa-font"></i><span class="size-label">XLarge</span>
                </button>
              </div>
            </div>
            
            ${this.options.showResetButton ? `
              <div class="customizer-footer">
                <button class="reset-theme-btn">
                  <i class="fas fa-undo"></i> Reset to Defaults
                </button>
              </div>
            ` : ''}
          </div>
        `;
        
        // Add event listeners
        this.setupEventListeners();
      }
      
      /**
       * Update the UI to reflect current theme settings
       */
      updateUI() {
        // Update theme mode radios
        const modeRadios = this.container.querySelectorAll('input[name="theme-mode"]');
        modeRadios.forEach(radio => {
          radio.checked = radio.value === this.currentTheme.mode;
        });
        
        // Update color picker
        const colorPicker = this.container.querySelector('#primary-color-picker');
        const colorValue = this.container.querySelector('.color-value');
        if (colorPicker && colorValue) {
          colorPicker.value = this.currentTheme.primaryColor;
          colorValue.textContent = this.currentTheme.primaryColor;
        }
        
        // Update font size buttons
        const fontSizeBtns = this.container.querySelectorAll('.font-size-btn');
        fontSizeBtns.forEach(btn => {
          btn.classList.toggle('active', btn.dataset.size === this.currentTheme.fontSize);
        });
      }
      
      /**
       * Set up event listeners for the UI
       */
      setupEventListeners() {
        // Theme mode radio buttons
        const modeRadios = this.container.querySelectorAll('input[name="theme-mode"]');
        modeRadios.forEach(radio => {
          radio.addEventListener('change', () => {
            if (radio.checked) {
              this.setThemeMode(radio.value);
            }
          });
        });
        
        // Primary color picker
        const colorPicker = this.container.querySelector('#primary-color-picker');
        const colorValue = this.container.querySelector('.color-value');
        if (colorPicker) {
          colorPicker.addEventListener('input', () => {
            if (colorValue) {
              colorValue.textContent = colorPicker.value;
            }
            this.setPrimaryColor(colorPicker.value);
          });
        }
        
        // Font size buttons
        const fontSizeBtns = this.container.querySelectorAll('.font-size-btn');
        fontSizeBtns.forEach(btn => {
          btn.addEventListener('click', () => {
            this.setFontSize(btn.dataset.size);
            fontSizeBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
          });
        });
        
        // Reset button
        const resetBtn = this.container.querySelector('.reset-theme-btn');
        if (resetBtn) {
          resetBtn.addEventListener('click', () => {
            if (confirm('Reset all theme customizations to defaults?')) {
              this.resetTheme();
            }
          });
        }
      }
    }
    
    // Export to window - factory function
    window.ThemeCustomizer = function(options) {
      return new ThemeCustomizerClass(options);
    };
    
    // Create a single instance for global use - only if not already created
    window.themeCustomizer = window.themeCustomizer || new ThemeCustomizerClass();
    
    console.log('ThemeCustomizer initialized and global instance created');
  })(window);
  
  // If script loading tracker is available, mark this script as loaded
  if (typeof window.markScriptAsLoaded === 'function') {
    window.markScriptAsLoaded('theme-customizer');
  }
} 