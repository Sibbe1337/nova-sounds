/**
 * UI Feedback System
 * Provides animated toast notifications and action feedback
 */

// Check if window.__scriptExecuted already exists for this file
if (window.__scriptExecuted && window.__scriptExecuted['ui-feedback.js']) {
  console.log('ui-feedback.js already executed, skipping duplicate execution');
} else {
  // Mark this script as executed
  window.__scriptExecuted = window.__scriptExecuted || {};
  window.__scriptExecuted['ui-feedback.js'] = true;
  
  // Main implementation wrapped in an IIFE
  (function(window) {
    // Skip if already defined
    if (window.UIFeedback) {
      console.log('UIFeedback already defined, skipping redefinition');
      return;
    }
    
    /**
     * UI Feedback System implementation
     */
    class UIFeedbackClass {
      constructor(options = {}) {
        this.options = {
          position: 'bottom-right',
          autoHide: true,
          autoHideDuration: 4000,
          maxNotifications: 3,
          newestOnTop: true,
          ...options
        };
        
        this.initialize();
        this.notificationQueue = [];
        this.activeNotifications = [];
      }
      
      initialize() {
        // Create container for notifications
        this.container = document.createElement('div');
        this.container.className = `toast-container ${this.options.position}`;
        document.body.appendChild(this.container);
      }
      
      showToast(message, type = 'info', options = {}) {
        const id = `toast-${Date.now()}`;
        const notificationOptions = {
          id,
          message,
          type,
          icon: this.getIconForType(type),
          autoHide: options.autoHide !== undefined ? options.autoHide : this.options.autoHide,
          autoHideDuration: options.duration || this.options.autoHideDuration,
          onClick: options.onClick || null,
          onClose: options.onClose || null
        };
        
        // Create toast element
        const toast = this.createToastElement(notificationOptions);
        
        // Check if we already have the maximum number of notifications
        if (this.activeNotifications.length >= this.options.maxNotifications) {
          // Queue this notification
          this.notificationQueue.push(notificationOptions);
        } else {
          // Show immediately
          this.showNotificationElement(toast, notificationOptions);
        }
        
        return id;
      }
      
      createToastElement(options) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${options.type}`;
        toast.id = options.id;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'polite');
        
        toast.innerHTML = `
          <div class="toast-icon">
            <i class="${options.icon}"></i>
          </div>
          <div class="toast-content">
            <p>${options.message}</p>
          </div>
          <button class="toast-close" aria-label="Close notification">
            <i class="fas fa-times"></i>
          </button>
          ${options.autoHide ? '<div class="toast-progress"><div class="toast-progress-bar"></div></div>' : ''}
        `;
        
        // Add click event
        if (options.onClick) {
          toast.addEventListener('click', (e) => {
            if (!e.target.closest('.toast-close')) {
              options.onClick();
            }
          });
        }
        
        // Add close button event
        const closeBtn = toast.querySelector('.toast-close');
        if (closeBtn) {
          closeBtn.addEventListener('click', () => {
            this.closeToast(options.id);
          });
        }
        
        return toast;
      }
      
      showNotificationElement(element, options) {
        // Add to tracking arrays
        this.activeNotifications.push(options);
        
        // Add to DOM
        if (this.options.newestOnTop) {
          this.container.prepend(element);
        } else {
          this.container.appendChild(element);
        }
        
        // Trigger animation after a brief delay for the DOM to update
        setTimeout(() => {
          element.classList.add('toast-visible');
          
          // Start progress bar animation if auto-hide is enabled
          if (options.autoHide) {
            const progressBar = element.querySelector('.toast-progress-bar');
            if (progressBar) {
              progressBar.style.transition = `width ${options.autoHideDuration}ms linear`;
              progressBar.style.width = '0%';
            }
            
            // Set timeout to close
            setTimeout(() => {
              this.closeToast(options.id);
            }, options.autoHideDuration);
          }
        }, 10);
      }
      
      closeToast(id) {
        const element = document.getElementById(id);
        if (!element) return;
        
        element.classList.remove('toast-visible');
        element.classList.add('toast-hiding');
        
        // Find the notification in our tracking array
        const index = this.activeNotifications.findIndex(n => n.id === id);
        if (index !== -1) {
          const notification = this.activeNotifications[index];
          
          // Remove after animation completes
          setTimeout(() => {
            if (element.parentNode) {
              element.parentNode.removeChild(element);
            }
            
            // Remove from active list
            this.activeNotifications.splice(index, 1);
            
            // Call onClose callback if provided
            if (notification.onClose) {
              notification.onClose();
            }
            
            // Show next notification from queue if any
            if (this.notificationQueue.length > 0) {
              const nextNotification = this.notificationQueue.shift();
              const nextElement = this.createToastElement(nextNotification);
              this.showNotificationElement(nextElement, nextNotification);
            }
          }, 300); // Animation duration
        }
      }
      
      closeAll() {
        // Close all active notifications
        this.activeNotifications.forEach(notification => {
          this.closeToast(notification.id);
        });
        
        // Clear the queue
        this.notificationQueue = [];
      }
      
      getIconForType(type) {
        switch (type) {
          case 'success': return 'fas fa-check-circle';
          case 'error': return 'fas fa-exclamation-circle';
          case 'warning': return 'fas fa-exclamation-triangle';
          case 'info': 
          default: return 'fas fa-info-circle';
        }
      }
      
      // Global shorthand methods
      success(message, options = {}) {
        return this.showToast(message, 'success', options);
      }
      
      error(message, options = {}) {
        return this.showToast(message, 'error', options);
      }
      
      warning(message, options = {}) {
        return this.showToast(message, 'warning', options);
      }
      
      info(message, options = {}) {
        return this.showToast(message, 'info', options);
      }
    }
    
    // Export to window
    window.UIFeedback = function(options) {
      return new UIFeedbackClass(options);
    };
    
    // Create a global instance - only if not already created
    window.uiFeedback = window.uiFeedback || new UIFeedbackClass();
    
    // Define global helper functions - only if they don't already exist
    if (typeof window.showSuccess !== 'function') {
      window.showSuccess = function(message, options = {}) {
        return window.uiFeedback.success(message, options);
      };
    }
    
    if (typeof window.showError !== 'function') {
      window.showError = function(message, options = {}) {
        return window.uiFeedback.error(message, options);
      };
    }
    
    if (typeof window.showWarning !== 'function') {
      window.showWarning = function(message, options = {}) {
        return window.uiFeedback.warning(message, options);
      };
    }
    
    if (typeof window.showInfo !== 'function') {
      window.showInfo = function(message, options = {}) {
        return window.uiFeedback.info(message, options);
      };
    }
    
    console.log('UIFeedback initialized and global functions registered');
  })(window);
  
  // If script loading tracker is available, mark this script as loaded
  if (typeof window.markScriptAsLoaded === 'function') {
    window.markScriptAsLoaded('ui-feedback');
  }
} 