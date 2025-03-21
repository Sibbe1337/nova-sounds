/**
 * Theme Switcher for YouTube Shorts Machine
 * Handles toggling between light and dark themes with smooth transitions
 */

(function() {
  // Theme constants
  const THEME_STORAGE_KEY = 'youtube-shorts-machine-theme';
  const DARK_THEME = 'dark-theme';
  const LIGHT_THEME = 'light-theme';
  
  // DOM Elements
  const themeToggle = document.getElementById('theme-toggle');
  const themeIcon = document.querySelector('.theme-toggle-icon');
  const themeFab = document.getElementById('theme-fab');
  
  // Initialize theme based on user preference
  function initTheme() {
    // Check if user has previously set a theme preference
    const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
    
    if (savedTheme) {
      // Apply saved theme
      setTheme(savedTheme);
    } else {
      // Check system preference
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      setTheme(prefersDark ? DARK_THEME : LIGHT_THEME);
    }
    
    // Update toggle state
    if (themeToggle) {
      themeToggle.checked = document.body.classList.contains(DARK_THEME);
      updateThemeIcon();
    }
  }
  
  // Set theme on body and save preference
  function setTheme(theme) {
    const previousTheme = document.body.classList.contains(DARK_THEME) ? DARK_THEME : LIGHT_THEME;
    
    // Remove all theme classes first to avoid conflicts
    document.body.classList.remove(DARK_THEME, LIGHT_THEME);
    
    // Add the appropriate theme class
    if (theme === DARK_THEME) {
      document.body.classList.add(DARK_THEME);
    } else {
      document.body.classList.add(LIGHT_THEME);
    }
    
    // Save preference
    localStorage.setItem(THEME_STORAGE_KEY, theme);
    
    // Show notification if theme has changed
    if (previousTheme !== theme && typeof window.showSuccess === 'function') {
      const themeName = theme === DARK_THEME ? 'Dark Mode' : 'Light Mode';
      window.showSuccess(`Switched to ${themeName}`, {
        duration: 2000,
        position: 'bottom-right'
      });
    }
    
    // Dispatch custom event for other components
    document.dispatchEvent(new CustomEvent('themeChanged', { 
      detail: { theme: theme }
    }));
    
    // Update meta theme-color for mobile browsers
    const metaThemeColor = document.querySelector('meta[name="theme-color"]');
    if (metaThemeColor) {
      metaThemeColor.setAttribute('content', 
        theme === DARK_THEME ? '#1A202C' : '#FFFFFF');
    }
  }
  
  // Toggle between themes
  function toggleTheme() {
    const currentTheme = document.body.classList.contains(DARK_THEME) ? DARK_THEME : LIGHT_THEME;
    const newTheme = currentTheme === DARK_THEME ? LIGHT_THEME : DARK_THEME;
    
    setTheme(newTheme);
    
    // Update toggle state if it exists
    if (themeToggle) {
      themeToggle.checked = newTheme === DARK_THEME;
      updateThemeIcon();
    }
  }
  
  // Update the icon in theme toggle
  function updateThemeIcon() {
    if (!themeIcon) return;
    
    if (document.body.classList.contains(DARK_THEME)) {
      themeIcon.classList.remove('fa-sun');
      themeIcon.classList.add('fa-moon');
    } else {
      themeIcon.classList.remove('fa-moon');
      themeIcon.classList.add('fa-sun');
    }
  }
  
  // Set up event listeners
  function setupEventListeners() {
    // Theme toggle checkbox
    if (themeToggle) {
      themeToggle.addEventListener('change', function() {
        setTheme(this.checked ? DARK_THEME : LIGHT_THEME);
        updateThemeIcon();
      });
    }
    
    // Theme FAB button (if present)
    if (themeFab) {
      themeFab.addEventListener('click', function(e) {
        e.preventDefault();
        toggleTheme();
      });
    }
    
    // Listen for system preference changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      // Only update if user hasn't set a preference
      if (!localStorage.getItem(THEME_STORAGE_KEY)) {
        setTheme(e.matches ? DARK_THEME : LIGHT_THEME);
        
        // Update toggle if it exists
        if (themeToggle) {
          themeToggle.checked = e.matches;
          updateThemeIcon();
        }
      }
    });
    
    // Keyboard shortcut: Shift+D to toggle theme
    document.addEventListener('keydown', function(e) {
      if (e.shiftKey && (e.key === 'D' || e.key === 'd')) {
        toggleTheme();
      }
    });
  }
  
  // Force re-apply theme
  function forceRefreshTheme() {
    const currentTheme = document.body.classList.contains(DARK_THEME) ? DARK_THEME : LIGHT_THEME;
    setTheme(currentTheme);
  }
  
  // Initialize on page load
  document.addEventListener('DOMContentLoaded', function() {
    initTheme();
    setupEventListeners();
    
    // Make functions globally available
    window.toggleTheme = toggleTheme;
    window.setTheme = setTheme;
    window.forceRefreshTheme = forceRefreshTheme;
  });
  
  // Expose functions globally for immediate use
  window.ThemeSwitcher = {
    toggleTheme: toggleTheme,
    setTheme: setTheme,
    forceRefreshTheme: forceRefreshTheme,
    init: initTheme
  };
  
  // Initialize immediately if document is already loaded
  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    initTheme();
    setupEventListeners();
  }
})(); 