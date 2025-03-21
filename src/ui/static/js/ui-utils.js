/**
 * UI Utilities
 * Common utility functions for UI interactions and animations
 */

// Constants for consistent behavior
const UI_CONSTANTS = {
    ANIMATION_DURATION: 300, // ms
    TOAST_DURATION: 5000,    // ms
    DEBOUNCE_DELAY: 200,     // ms
    MOBILE_BREAKPOINT: 768,  // px
    TABLET_BREAKPOINT: 1024, // px
};

/**
 * Creates and shows a toast notification
 * @param {string} message - The message to display
 * @param {string} type - Type of notification: 'success', 'error', 'warning', 'info'
 * @param {number} duration - How long to show the notification in ms
 */
function showToast(message, type = 'info', duration = UI_CONSTANTS.TOAST_DURATION) {
    // Check if notification system is available
    if (typeof createNotification === 'function') {
        createNotification({
            message: message,
            type: type,
            duration: duration
        });
        return;
    }
    
    // Fallback implementation if notification system isn't loaded
    const toast = document.createElement('div');
    toast.className = `ui-toast ui-toast-${type}`;
    toast.textContent = message;
    
    // Add to body and position with CSS
    document.body.appendChild(toast);
    
    // Animate in
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);
    
    // Remove after duration
    setTimeout(() => {
        toast.classList.remove('show');
        // Remove from DOM after animation completes
        setTimeout(() => {
            toast.remove();
        }, UI_CONSTANTS.ANIMATION_DURATION);
    }, duration);
}

/**
 * Debounce function to limit how often a function can be called
 * @param {Function} func - The function to debounce
 * @param {number} wait - Time to wait between calls in ms
 * @return {Function} - Debounced function
 */
function debounce(func, wait = UI_CONSTANTS.DEBOUNCE_DELAY) {
    let timeout;
    
    return function(...args) {
        const context = this;
        clearTimeout(timeout);
        
        timeout = setTimeout(() => {
            func.apply(context, args);
        }, wait);
    };
}

/**
 * Throttle function to limit how often a function can be called
 * @param {Function} func - The function to throttle
 * @param {number} limit - Minimum time between calls in ms
 * @return {Function} - Throttled function
 */
function throttle(func, limit = UI_CONSTANTS.DEBOUNCE_DELAY) {
    let inThrottle;
    
    return function(...args) {
        const context = this;
        
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Creates a loading indicator and returns functions to control it
 * @param {string|Element} container - Container selector or element
 * @param {string} message - Message to display
 * @return {Object} Object with show, update, and hide methods
 */
function createLoader(container, message = 'Loading...') {
    // Convert selector to element if needed
    if (typeof container === 'string') {
        container = document.querySelector(container);
    }
    
    if (!container) {
        console.error('Invalid container for loader');
        return {
            show: () => {},
            update: () => {},
            hide: () => {}
        };
    }
    
    // Create loader elements
    const loaderEl = document.createElement('div');
    loaderEl.className = 'ui-loader';
    loaderEl.innerHTML = `
        <div class="ui-loader-spinner"></div>
        <div class="ui-loader-message">${message}</div>
    `;
    
    // Store original container styles to restore later
    const originalPosition = container.style.position;
    const originalOverflow = container.style.overflow;
    
    // Methods for controlling the loader
    const loader = {
        show: () => {
            // Add positioning if needed
            if (originalPosition !== 'relative' && originalPosition !== 'absolute') {
                container.style.position = 'relative';
            }
            container.style.overflow = 'hidden';
            container.appendChild(loaderEl);
            setTimeout(() => {
                loaderEl.classList.add('active');
            }, 10);
        },
        
        update: (newMessage) => {
            const messageEl = loaderEl.querySelector('.ui-loader-message');
            if (messageEl) {
                messageEl.textContent = newMessage;
            }
        },
        
        hide: () => {
            loaderEl.classList.remove('active');
            setTimeout(() => {
                if (loaderEl.parentNode === container) {
                    container.removeChild(loaderEl);
                }
                // Restore original styles
                container.style.position = originalPosition;
                container.style.overflow = originalOverflow;
            }, UI_CONSTANTS.ANIMATION_DURATION);
        }
    };
    
    return loader;
}

/**
 * Creates a modal dialog and returns functions to control it
 * @param {Object} options - Modal options
 * @param {string} options.title - Modal title
 * @param {string|Element} options.content - Modal content (HTML string or element)
 * @param {Array} options.buttons - Array of button configs {text, type, onClick}
 * @param {boolean} options.closeOnOverlayClick - Whether to close when clicking overlay
 * @return {Object} Object with open and close methods
 */
function createModal(options = {}) {
    const {
        title = '',
        content = '',
        buttons = [{text: 'Close', type: 'primary', onClick: null}],
        closeOnOverlayClick = true
    } = options;
    
    // Create modal elements
    const modalEl = document.createElement('div');
    modalEl.className = 'ui-modal';
    
    let modalContent = '';
    
    if (typeof content === 'string') {
        modalContent = content;
    } else if (content instanceof Element) {
        // We'll append the element later
        modalContent = '<div class="content-container"></div>';
    }
    
    // Create button HTML
    const buttonHtml = buttons.map((button, index) => {
        return `<button class="btn btn-${button.type || 'secondary'}" data-button-index="${index}">${button.text}</button>`;
    }).join('');
    
    modalEl.innerHTML = `
        <div class="ui-modal-overlay"></div>
        <div class="ui-modal-container">
            <div class="ui-modal-header">
                <h3>${title}</h3>
                <button class="ui-modal-close" aria-label="Close modal">×</button>
            </div>
            <div class="ui-modal-body">
                ${modalContent}
            </div>
            <div class="ui-modal-footer">
                ${buttonHtml}
            </div>
        </div>
    `;
    
    // If content is an element, append it
    if (content instanceof Element) {
        const contentContainer = modalEl.querySelector('.content-container');
        contentContainer.appendChild(content);
    }
    
    // Add event listeners
    const overlay = modalEl.querySelector('.ui-modal-overlay');
    const closeBtn = modalEl.querySelector('.ui-modal-close');
    const buttonEls = modalEl.querySelectorAll('[data-button-index]');
    
    // Close button handler
    closeBtn.addEventListener('click', () => {
        modal.close();
    });
    
    // Overlay click handler
    if (closeOnOverlayClick) {
        overlay.addEventListener('click', () => {
            modal.close();
        });
    }
    
    // Button click handlers
    buttonEls.forEach(buttonEl => {
        const index = parseInt(buttonEl.dataset.buttonIndex);
        buttonEl.addEventListener('click', (event) => {
            // Call the onClick handler if provided
            if (buttons[index].onClick) {
                buttons[index].onClick(event);
            } else {
                // Default to closing the modal
                modal.close();
            }
        });
    });
    
    // Modal control object
    const modal = {
        isOpen: false,
        
        open: () => {
            if (modal.isOpen) return;
            
            document.body.appendChild(modalEl);
            
            // Prevent body scrolling
            document.body.style.overflow = 'hidden';
            
            // Animate opening
            setTimeout(() => {
                modalEl.classList.add('active');
            }, 10);
            
            modal.isOpen = true;
        },
        
        close: () => {
            if (!modal.isOpen) return;
            
            modalEl.classList.remove('active');
            
            // Remove from DOM after animation completes
            setTimeout(() => {
                if (modalEl.parentNode) {
                    modalEl.parentNode.removeChild(modalEl);
                }
                
                // Restore body scrolling
                document.body.style.overflow = '';
            }, UI_CONSTANTS.ANIMATION_DURATION);
            
            modal.isOpen = false;
        }
    };
    
    return modal;
}

/**
 * Auto-initializes interactive elements
 */
function initializeInteractiveElements() {
    // Initialize tooltips
    document.querySelectorAll('[data-tooltip]').forEach(element => {
        // Tooltip logic here
    });
    
    // Initialize accordion elements
    document.querySelectorAll('.ui-accordion').forEach(accordion => {
        const headers = accordion.querySelectorAll('.ui-accordion-header');
        
        headers.forEach(header => {
            header.addEventListener('click', () => {
                const section = header.parentElement;
                const isOpen = section.classList.contains('open');
                
                // Close all other sections if this is an exclusive accordion
                if (!isOpen && accordion.classList.contains('exclusive')) {
                    accordion.querySelectorAll('.open').forEach(el => {
                        el.classList.remove('open');
                    });
                }
                
                // Toggle this section
                section.classList.toggle('open');
            });
        });
    });
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    initializeInteractiveElements();
    
    // Initialize spotlight effect for background if it exists
    const spotlight = document.getElementById('spotlight');
    if (spotlight) {
        document.addEventListener('mousemove', (e) => {
            spotlight.style.transform = `translate(${e.clientX}px, ${e.clientY}px)`;
        });
    }
});

// Export utilities for use in other scripts
window.UIUtils = {
    CONSTANTS: UI_CONSTANTS,
    showToast,
    debounce,
    throttle,
    createLoader,
    createModal
}; 