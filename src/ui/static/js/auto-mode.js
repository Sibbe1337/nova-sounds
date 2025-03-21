/**
 * Auto Mode UI Component
 * Provides a UI for the automatic video generation feature
 */

// Check if window.__scriptExecuted already exists for this file
if (window.__scriptExecuted && window.__scriptExecuted['auto-mode.js']) {
  console.log('auto-mode.js already executed, skipping duplicate execution');
} else {
  // Mark this script as executed
  window.__scriptExecuted = window.__scriptExecuted || {};
  window.__scriptExecuted['auto-mode.js'] = true;
  
  // Main implementation wrapped in an IIFE
  (function(window) {
    // Skip if already defined
    if (window.AutoMode) {
      console.log('AutoMode already defined, skipping redefinition');
      return;
    }
    
    /**
     * Auto Mode UI Implementation
     */
    class AutoModeUI {
      constructor(options = {}) {
        this.options = {
          containerSelector: '#autoModeContainer',
          uploadFormSelector: '#uploadForm',
          imageUploadSelector: '#imageUpload',
          enabledByDefault: false,
          ...options
        };
        
        this.isEnabled = this.options.enabledByDefault;
        this.settings = {
          enable_music_sync: true,
          use_smart_transitions: true,
          enable_captions: false
        };
        
        this.initialize();
      }
      
      /**
       * Initialize the UI
       */
      initialize() {
        // Find container element
        this.container = document.querySelector(this.options.containerSelector);
        if (!this.container) {
          console.error(`Auto Mode container not found: ${this.options.containerSelector}`);
          return;
        }
        
        // Create the UI
        this.render();
        
        // Setup event listeners
        this.setupEventListeners();
        
        console.log('Auto Mode UI initialized');
      }
      
      /**
       * Render the Auto Mode UI
       */
      render() {
        this.container.innerHTML = `
          <div class="auto-mode-widget">
            <div class="auto-mode-header">
              <h3 class="feature-title">
                <i class="fas fa-magic"></i> Auto Mode
              </h3>
              <div class="feature-toggle">
                <label class="switch">
                  <input type="checkbox" id="autoModeToggle" ${this.isEnabled ? 'checked' : ''}>
                  <span class="slider round"></span>
                </label>
              </div>
            </div>
            
            <div class="auto-mode-description">
              <p>Let AI automatically create your video with intelligent music, style, and transition selection.</p>
            </div>
            
            <div class="auto-mode-settings ${this.isEnabled ? '' : 'hidden'}">
              <div class="setting-group">
                <h4>Auto Mode Settings</h4>
                
                <div class="setting-item">
                  <label class="checkbox-label">
                    <input type="checkbox" id="musicSyncToggle" ${this.settings.enable_music_sync ? 'checked' : ''}>
                    <span>Music-Responsive Effects</span>
                  </label>
                  <span class="setting-description">Automatically sync visual effects to music beats</span>
                </div>
                
                <div class="setting-item">
                  <label class="checkbox-label">
                    <input type="checkbox" id="smartTransitionsToggle" ${this.settings.use_smart_transitions ? 'checked' : ''}>
                    <span>Smart Transitions</span>
                  </label>
                  <span class="setting-description">Use AI to select transitions based on content</span>
                </div>
                
                <div class="setting-item">
                  <label class="checkbox-label">
                    <input type="checkbox" id="captionsToggle" ${this.settings.enable_captions ? 'checked' : ''}>
                    <span>Auto Captions</span>
                  </label>
                  <span class="setting-description">Generate captions for your video</span>
                </div>
              </div>
            </div>
          </div>
        `;
      }
      
      /**
       * Set up event listeners
       */
      setupEventListeners() {
        // Toggle Auto Mode on/off
        const autoModeToggle = document.getElementById('autoModeToggle');
        if (autoModeToggle) {
          autoModeToggle.addEventListener('change', (e) => {
            this.isEnabled = e.target.checked;
            this.updateUI();
            this.updateFormHandler();
          });
        }
        
        // Settings toggles
        const musicSyncToggle = document.getElementById('musicSyncToggle');
        if (musicSyncToggle) {
          musicSyncToggle.addEventListener('change', (e) => {
            this.settings.enable_music_sync = e.target.checked;
          });
        }
        
        const smartTransitionsToggle = document.getElementById('smartTransitionsToggle');
        if (smartTransitionsToggle) {
          smartTransitionsToggle.addEventListener('change', (e) => {
            this.settings.use_smart_transitions = e.target.checked;
          });
        }
        
        const captionsToggle = document.getElementById('captionsToggle');
        if (captionsToggle) {
          captionsToggle.addEventListener('change', (e) => {
            this.settings.enable_captions = e.target.checked;
          });
        }
        
        // Modify the form submission to handle Auto Mode
        this.updateFormHandler();
      }
      
      /**
       * Update UI based on current state
       */
      updateUI() {
        const settingsPanel = this.container.querySelector('.auto-mode-settings');
        if (settingsPanel) {
          if (this.isEnabled) {
            settingsPanel.classList.remove('hidden');
          } else {
            settingsPanel.classList.add('hidden');
          }
        }
        
        // Update other dependent UI elements
        const uploadForm = document.querySelector(this.options.uploadFormSelector);
        if (uploadForm) {
          if (this.isEnabled) {
            uploadForm.classList.add('auto-mode-enabled');
          } else {
            uploadForm.classList.remove('auto-mode-enabled');
          }
        }
      }
      
      /**
       * Modify the form submission to handle Auto Mode
       */
      updateFormHandler() {
        const uploadForm = document.querySelector(this.options.uploadFormSelector);
        if (!uploadForm) return;
        
        // Remove previous listener if exists
        if (this._originalSubmitHandler) {
          uploadForm.removeEventListener('submit', this._formSubmitHandler);
        }
        
        // Store original submit handler
        if (!this._originalSubmitHandler) {
          this._originalSubmitHandler = uploadForm.onsubmit;
        }
        
        // Create new submit handler
        this._formSubmitHandler = (e) => {
          e.preventDefault();
          
          // Create FormData
          const formData = new FormData(uploadForm);
          
          // Set Auto Mode settings
          if (this.isEnabled) {
            formData.append('auto_mode_settings', JSON.stringify(this.settings));
            
            // Change endpoint to auto-mode
            fetch('/api/videos/auto-mode', {
              method: 'POST',
              body: formData
            })
            .then(response => response.json())
            .then(data => {
              if (data.status === 'success') {
                this.showSuccessMessage(`Auto Mode video creation started with ID: ${data.video_id}`);
                
                // If live preview is available, initialize it
                if (window.livePreview) {
                  window.livePreview.startProcessing(data.video_id);
                }
              } else {
                this.showErrorMessage(`Error: ${data.message || 'Unknown error'}`);
              }
            })
            .catch(error => {
              this.showErrorMessage(`Error: ${error.message}`);
            });
          } else {
            // Use original submission
            if (this._originalSubmitHandler) {
              // Restore original handler temporarily
              uploadForm.onsubmit = this._originalSubmitHandler;
              uploadForm.submit();
              uploadForm.onsubmit = null; // Clear it again
            } else {
              uploadForm.submit();
            }
          }
        };
        
        // Attach the handler
        uploadForm.addEventListener('submit', this._formSubmitHandler);
      }
      
      /**
       * Show success message
       */
      showSuccessMessage(message) {
        // Use toast notification if available
        if (window.UIFeedback && window.UIFeedback.showToast) {
          window.UIFeedback.showToast('Auto Mode', message, 'success');
        } else {
          alert(message);
        }
      }
      
      /**
       * Show error message
       */
      showErrorMessage(message) {
        // Use toast notification if available
        if (window.UIFeedback && window.UIFeedback.showToast) {
          window.UIFeedback.showToast('Error', message, 'error');
        } else {
          alert(`Error: ${message}`);
        }
      }
      
      /**
       * Enable Auto Mode
       */
      enable() {
        this.isEnabled = true;
        const toggle = document.getElementById('autoModeToggle');
        if (toggle) toggle.checked = true;
        this.updateUI();
        this.updateFormHandler();
      }
      
      /**
       * Disable Auto Mode
       */
      disable() {
        this.isEnabled = false;
        const toggle = document.getElementById('autoModeToggle');
        if (toggle) toggle.checked = false;
        this.updateUI();
        this.updateFormHandler();
      }
    }
    
    // Expose to global scope
    window.AutoMode = {
      init: function(options) {
        return new AutoModeUI(options);
      }
    };
    
    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', () => {
      // Check if auto mode container exists
      const container = document.querySelector('#autoModeContainer');
      if (container) {
        window.autoModeUI = window.AutoMode.init();
      }
    });
    
  })(window);
} 