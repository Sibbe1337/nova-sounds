/**
 * Notification System
 * Handles the creation, display, and dismissal of notifications
 */

// Create notification container if it doesn't exist
function createNotificationContainer() {
    let container = document.querySelector('.notification-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'notification-container';
        document.body.appendChild(container);
    }
    return container;
}

// Create a notification
function createNotification(options) {
    const defaults = {
        title: '',
        message: '',
        type: 'info', // info, success, error, warning
        duration: 5000,
        dismissible: true,
        icon: null,
        onClose: null
    };

    const settings = { ...defaults, ...options };
    
    // Set icon based on type if not provided
    if (!settings.icon) {
        switch (settings.type) {
            case 'success':
                settings.icon = 'fas fa-check-circle';
                break;
            case 'error':
                settings.icon = 'fas fa-exclamation-circle';
                break;
            case 'warning':
                settings.icon = 'fas fa-exclamation-triangle';
                break;
            default:
                settings.icon = 'fas fa-info-circle';
                break;
        }
    }
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${settings.type}`;
    
    // Create notification content
    let notificationHTML = `
        <div class="notification-icon">
            <i class="${settings.icon}"></i>
        </div>
        <div class="notification-content">
    `;
    
    if (settings.title) {
        notificationHTML += `<h3 class="notification-title">${settings.title}</h3>`;
    }
    
    notificationHTML += `<p class="notification-message">${settings.message}</p>`;
    notificationHTML += `</div>`;
    
    if (settings.dismissible) {
        notificationHTML += `
            <button class="notification-close" aria-label="Close notification">
                <i class="fas fa-times"></i>
            </button>
        `;
    }
    
    // Add progress bar if duration is set
    if (settings.duration > 0) {
        notificationHTML += `<div class="notification-progress"></div>`;
    }
    
    notification.innerHTML = notificationHTML;
    
    // Add notification to container
    const container = createNotificationContainer();
    container.appendChild(notification);
    
    // Show notification with animation
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // Setup progress bar animation
    if (settings.duration > 0) {
        const progressBar = notification.querySelector('.notification-progress');
        progressBar.style.transition = `transform ${settings.duration / 1000}s linear`;
        progressBar.style.transform = 'scaleX(0)';
        
        // Trigger reflow to start the animation
        progressBar.getBoundingClientRect();
        progressBar.style.transformOrigin = 'right';
    }
    
    // Set timeout to remove notification
    let timeoutId;
    if (settings.duration > 0) {
        timeoutId = setTimeout(() => {
            dismissNotification(notification, settings.onClose);
        }, settings.duration);
    }
    
    // Add click event to close button
    if (settings.dismissible) {
        const closeButton = notification.querySelector('.notification-close');
        closeButton.addEventListener('click', () => {
            if (timeoutId) {
                clearTimeout(timeoutId);
            }
            dismissNotification(notification, settings.onClose);
        });
    }
    
    return notification;
}

// Dismiss notification with animation
function dismissNotification(notification, callback) {
    notification.classList.remove('show');
    notification.classList.add('removing');
    
    // Remove from DOM after animation completes
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
            
            // Call onClose callback if provided
            if (typeof callback === 'function') {
                callback();
            }
            
            // Remove container if empty
            const container = document.querySelector('.notification-container');
            if (container && container.children.length === 0) {
                container.parentNode.removeChild(container);
            }
        }
    }, 300);
}

// Shorthand functions for different notification types
function showSuccessNotification(message, options = {}) {
    return createNotification({
        message,
        type: 'success',
        ...options
    });
}

function showErrorNotification(message, options = {}) {
    return createNotification({
        message,
        type: 'error',
        ...options
    });
}

function showWarningNotification(message, options = {}) {
    return createNotification({
        message,
        type: 'warning',
        ...options
    });
}

function showInfoNotification(message, options = {}) {
    return createNotification({
        message,
        type: 'info',
        ...options
    });
}

// Dismiss all notifications
function dismissAllNotifications() {
    const notifications = document.querySelectorAll('.notification');
    notifications.forEach(notification => {
        dismissNotification(notification);
    });
}

// Export functions to global scope
window.Notifications = {
    create: createNotification,
    dismiss: dismissNotification,
    dismissAll: dismissAllNotifications,
    success: showSuccessNotification,
    error: showErrorNotification,
    warning: showWarningNotification,
    info: showInfoNotification
}; 