/**
 * Image utilities for YouTube Shorts Machine
 */

// Mark the script as loaded
window.markScriptAsLoaded('image-utils');

// Handle image loading errors by showing placeholders
document.addEventListener('DOMContentLoaded', () => {
    // Select all images
    const images = document.querySelectorAll('img');
    
    // Add error handlers to all images
    images.forEach(img => {
        // Skip if already processed
        if (img.dataset.errorHandled) return;
        
        // Mark as processed
        img.dataset.errorHandled = 'true';
        
        // Add error handler
        img.addEventListener('error', function(e) {
            handleImageError(this);
        });
    });
});

/**
 * Handle image loading errors
 * @param {HTMLImageElement} img - The image element that failed to load
 */
function handleImageError(img) {
    if (!img) return;
    
    // Get image dimensions
    const width = img.width || 300;
    const height = img.height || 200;
    
    // Create a canvas as placeholder
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    
    // Set canvas styles to match image styles
    canvas.style.width = img.style.width;
    canvas.style.height = img.style.height;
    canvas.className = img.className;
    canvas.alt = img.alt || 'Image placeholder';
    
    // Get the context and draw a placeholder background
    const ctx = canvas.getContext('2d');
    
    // Background color based on image alt or src
    const text = img.alt || img.src.split('/').pop() || 'Image';
    const colorHash = hashStringToColor(text);
    
    // Fill background with a light color
    ctx.fillStyle = colorHash;
    ctx.fillRect(0, 0, width, height);
    
    // Draw text
    ctx.fillStyle = getContrastColor(colorHash);
    ctx.font = `${Math.max(14, Math.floor(width / 20))}px sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    
    // Format image name to fit
    let displayText = text;
    if (displayText.length > 20) {
        displayText = displayText.substring(0, 18) + '...';
    }
    
    // Draw text in the center
    ctx.fillText(displayText, width / 2, height / 2);
    
    // Replace the image with the canvas
    if (img.parentNode) {
        img.parentNode.replaceChild(canvas, img);
    }
    
    // Log error for debugging
    console.warn(`Image failed to load: ${img.src}`);
}

/**
 * Generate a color from a string hash
 * @param {string} str - String to hash
 * @returns {string} - Hex color
 */
function hashStringToColor(str) {
    // Default color for empty strings
    if (!str) return '#e0e0e0';
    
    // Simple hash function
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    
    // Convert to hex color
    let color = '#';
    for (let i = 0; i < 3; i++) {
        const value = (hash >> (i * 8)) & 0xFF;
        // Make colors lighter by adding 127 (half of 255)
        const lighterValue = Math.min(255, value + 127);
        color += ('00' + lighterValue.toString(16)).substr(-2);
    }
    
    return color;
}

/**
 * Get a contrasting color for text on a background
 * @param {string} hexcolor - Background color in hex
 * @returns {string} - Contrasting color (#000000 or #ffffff)
 */
function getContrastColor(hexcolor) {
    // Convert hex to RGB
    const r = parseInt(hexcolor.substr(1, 2), 16);
    const g = parseInt(hexcolor.substr(3, 2), 16);
    const b = parseInt(hexcolor.substr(5, 2), 16);
    
    // Calculate luminance (perceived brightness)
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
    
    // Use white text on dark backgrounds, black text on light backgrounds
    return luminance > 0.5 ? '#000000' : '#ffffff';
}

// Add global method to create placeholder images
window.createPlaceholderImage = function(width, height, text, container) {
    // Create canvas
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    
    // Get context and draw placeholder
    const ctx = canvas.getContext('2d');
    const colorHash = hashStringToColor(text);
    
    // Fill background
    ctx.fillStyle = colorHash;
    ctx.fillRect(0, 0, width, height);
    
    // Draw text
    ctx.fillStyle = getContrastColor(colorHash);
    ctx.font = `${Math.max(14, Math.floor(width / 20))}px sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, width / 2, height / 2);
    
    // Add to container if provided
    if (container) {
        container.appendChild(canvas);
    }
    
    return canvas;
}; 