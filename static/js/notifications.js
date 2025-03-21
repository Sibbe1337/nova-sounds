/**
 * Notification System
 * 
 * A lightweight, accessible notification system that displays
 * toast messages for user feedback.
 */

// Check if window.__scriptExecuted already exists for this file
if (window.__scriptExecuted && window.__scriptExecuted['notifications.js']) {
  console.log('notifications.js already executed, skipping duplicate execution');
} else {
  // Mark this script as executed
  window.__scriptExecuted = window.__scriptExecuted || {};
  window.__scriptExecuted['notifications.js'] = true;
  
  // Main implementation wrapped in an IIFE
  (function(window) {
    // Skip if already defined
    if (window.NotificationSystem) {
      console.log('NotificationSystem already defined, skipping redefinition');
      return;
    }
    
    /**
     * Notification System implementation
     */
    class NotificationSystemClass {
      constructor(options = {}) {
        this.options = {
          position: 'top-right', // top-right, top-center, top-left, bottom-right, bottom-center, bottom-left
          duration: 5000, // Default duration in milliseconds
          maxVisible: 5, // Maximum number of visible notifications
          animationDuration: 300, // Animation duration in milliseconds
          container: null, // Custom container element
          ...options
        };
        
        // Create container if not provided
        if (!this.options.container) {
          this.container = document.createElement('div');
          this.container.className = `notification-container ${this.options.position}`;
          document.body.appendChild(this.container);
        } else {
          this.container = this.options.container;
        }
        
        // Queue of pending notifications
        this.queue = [];
        
        // Currently visible notifications
        this.activeNotifications = [];
      }
      
      /**
       * Creates and shows a notification
       */
      show(options) {
        const id = `notification-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
        
        const notification = {
          id,
          type: options.type || 'info',
          message: options.message || '',
          title: options.title || '',
          duration: options.duration || this.options.duration,
          dismissible: options.dismissible !== undefined ? options.dismissible : true,
          onDismiss: options.onDismiss || null,
          onClick: options.onClick || null,
          element: null,
          timer: null
        };
        
        // Create DOM element
        notification.element = this.createNotificationElement(notification);
        
        // Check if we can show it immediately
        if (this.activeNotifications.length < this.options.maxVisible) {
          this.showNotification(notification);
        } else {
          this.queue.push(notification);
        }
        
        return {
          id,
          dismiss: () => this.dismiss(id)
        };
      }
      
      /**
       * Shows a success notification
       */
      success(message, options = {}) {
        return this.show({
          type: 'success',
          message,
          ...options
        });
      }
      
      /**
       * Shows an error notification
       */
      error(message, options = {}) {
        return this.show({
          type: 'error',
          message,
          ...options
        });
      }
      
      /**
       * Shows a warning notification
       */
      warning(message, options = {}) {
        return this.show({
          type: 'warning',
          message,
          ...options
        });
      }
      
      /**
       * Shows an info notification
       */
      info(message, options = {}) {
        return this.show({
          type: 'info',
          message,
          ...options
        });
      }
      
      /**
       * Creates the notification DOM element
       */
      createNotificationElement(notification) {
        const element = document.createElement('div');
        element.className = `notification notification-${notification.type}`;
        element.setAttribute('role', 'alert');
        element.id = notification.id;
        
        // Add animation classes
        element.classList.add('notification-enter');
        
        // Icon based on type
        const iconMap = {
          success: 'check-circle',
          error: 'exclamation-circle',
          warning: 'exclamation-triangle',
          info: 'info-circle'
        };
        
        const icon = iconMap[notification.type] || 'info-circle';
        
        // Create content
        let html = `
          <div class="notification-icon">
            <i class="fas fa-${icon}"></i>
          </div>
          <div class="notification-content">`;
        
        if (notification.title) {
          html += `<h4 class="notification-title">${notification.title}</h4>`;
        }
        
        html += `<div class="notification-message">${notification.message}</div>
          </div>`;
        
        if (notification.dismissible) {
          html += `
            <button class="notification-close" aria-label="Dismiss notification">
              <i class="fas fa-times"></i>
            </button>`;
        }
        
        // Add progress bar if duration is set
        if (notification.duration > 0) {
          html += `
            <div class="notification-progress">
              <div class="notification-progress-bar"></div>
            </div>`;
        }
        
        element.innerHTML = html;
        
        // Add event listeners
        if (notification.dismissible) {
          const closeButton = element.querySelector('.notification-close');
          if (closeButton) {
            closeButton.addEventListener('click', (e) => {
              e.stopPropagation();
              this.dismiss(notification.id);
            });
          }
        }
        
        // Click handler for the notification
        element.addEventListener('click', () => {
          if (notification.onClick && typeof notification.onClick === 'function') {
            notification.onClick();
          }
        });
        
        return element;
      }
      
      /**
       * Shows a notification
       */
      showNotification(notification) {
        // Add to active notifications
        this.activeNotifications.push(notification);
        
        // Add to DOM
        this.container.appendChild(notification.element);
        
        // Force reflow to trigger animation
        notification.element.offsetHeight;
        
        // Start animation
        notification.element.classList.remove('notification-enter');
        notification.element.classList.add('notification-visible');
        
        // Start progress bar animation if applicable
        if (notification.duration > 0) {
          const progressBar = notification.element.querySelector('.notification-progress-bar');
          if (progressBar) {
            progressBar.style.transition = `width ${notification.duration}ms linear`;
            progressBar.style.width = '0%';
          }
          
          // Set auto-dismiss timer
          notification.timer = setTimeout(() => {
            this.dismiss(notification.id);
          }, notification.duration);
        }
      }
      
      /**
       * Dismisses a notification
       */
      dismiss(id) {
        // Find notification by ID
        const index = this.activeNotifications.findIndex(n => n.id === id);
        
        if (index !== -1) {
          const notification = this.activeNotifications[index];
          
          // Clear timer if it exists
          if (notification.timer) {
            clearTimeout(notification.timer);
          }
          
          // Start exit animation
          notification.element.classList.remove('notification-visible');
          notification.element.classList.add('notification-exit');
          
          // Remove after animation
          setTimeout(() => {
            if (notification.element.parentNode) {
              notification.element.parentNode.removeChild(notification.element);
            }
            
            // Remove from active notifications
            this.activeNotifications.splice(index, 1);
            
            // Call onDismiss callback if provided
            if (notification.onDismiss && typeof notification.onDismiss === 'function') {
              notification.onDismiss();
            }
            
            // Show next notification from queue if available
            if (this.queue.length > 0) {
              const nextNotification = this.queue.shift();
              this.showNotification(nextNotification);
            }
          }, this.options.animationDuration);
        }
      }
      
      /**
       * Dismisses all active notifications
       */
      dismissAll() {
        // Copy the array to avoid modification during iteration
        const notifications = [...this.activeNotifications];
        
        // Dismiss each notification
        notifications.forEach(notification => {
          this.dismiss(notification.id);
        });
        
        // Clear the queue
        this.queue = [];
      }
    }
    
    // Export to window
    window.NotificationSystem = function(options) {
      return new NotificationSystemClass(options);
    };
    
    // Create a global instance - only if it doesn't already exist
    window.notificationSystem = window.notificationSystem || new NotificationSystemClass();
    
    // Define global helper functions - only if they don't already exist
    if (typeof window.showNotification !== 'function') {
      window.showNotification = function(type, message, options = {}) {
        return window.notificationSystem.show({type, message, ...options});
      };
    }
    
    if (typeof window.showSuccess !== 'function') {
      window.showSuccess = function(message, options = {}) {
        return window.showNotification('success', message, options);
      };
    }
    
    if (typeof window.showError !== 'function') {
      window.showError = function(message, options = {}) {
        return window.showNotification('error', message, options);
      };
    }
    
    if (typeof window.showWarning !== 'function') {
      window.showWarning = function(message, options = {}) {
        return window.showNotification('warning', message, options);
      };
    }
    
    if (typeof window.showInfo !== 'function') {
      window.showInfo = function(message, options = {}) {
        return window.showNotification('info', message, options);
      };
    }
    
    console.log('NotificationSystem initialized and global functions registered');
  })(window);
  
  // If script loading tracker is available, mark this script as loaded
  if (typeof window.markScriptAsLoaded === 'function') {
    window.markScriptAsLoaded('notifications');
  }
} 