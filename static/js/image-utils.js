/**
 * Utility functions for image handling
 */

/**
 * Creates a placeholder for missing images
 * @param {HTMLImageElement} img - The image element that failed to load
 */
function createImagePlaceholder(img) {
    const parent = img.parentElement;
    if (!parent) return;
    
    // Create placeholder div
    const placeholder = document.createElement('div');
    placeholder.className = 'image-placeholder';
    
    // Set dimensions based on original image if available
    placeholder.style.width = img.width ? `${img.width}px` : '100%';
    placeholder.style.height = img.height ? `${img.height}px` : '100%';
    
    // Add icon and text
    const content = document.createElement('div');
    content.className = 'placeholder-content';
    content.innerHTML = `
        <i class="fas fa-image"></i>
        <span>Image not found</span>
    `;
    placeholder.appendChild(content);
    
    // Replace the image with the placeholder
    parent.replaceChild(placeholder, img);
}

/**
 * Generate a canvas-based placeholder for development
 * @param {HTMLImageElement} img - The image element to create a placeholder for
 */
function generateCanvasPlaceholder(img) {
    // Extract image name from path
    const path = img.src.split('/');
    const filename = path[path.length - 1].replace(/\.[^/.]+$/, "");
    
    // Create a canvas
    const canvas = document.createElement('canvas');
    canvas.width = img.width || 800;
    canvas.height = img.height || 600;
    
    // Get context
    const ctx = canvas.getContext('2d');
    
    // Fill background with gradient
    const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
    gradient.addColorStop(0, getRandomPastelColor(0.7));
    gradient.addColorStop(1, getRandomPastelColor(0.7));
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Draw pattern
    drawRandomPattern(ctx, canvas.width, canvas.height);
    
    // Add image name text
    ctx.font = 'bold 28px -apple-system, BlinkMacSystemFont, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = '#333';
    ctx.fillText(formatImageName(filename), canvas.width / 2, canvas.height / 2);
    
    // Set the image source to the canvas data URL
    img.src = canvas.toDataURL('image/jpeg');
    
    // Make sure the onerror handler doesn't fire again
    img.onerror = null;
}

/**
 * Format image name for display
 */
function formatImageName(name) {
    // Convert kebab/snake case to spaces
    let formatted = name.replace(/[-_]/g, ' ');
    
    // Capitalize first letter of each word
    formatted = formatted.replace(/\b\w/g, l => l.toUpperCase());
    
    return formatted;
}

/**
 * Get a random pastel color
 */
function getRandomPastelColor(alpha = 1) {
    const h = Math.floor(Math.random() * 360);
    const s = Math.floor(Math.random() * 30) + 70; // 70-100%
    const l = Math.floor(Math.random() * 20) + 70; // 70-90%
    
    return `hsla(${h}, ${s}%, ${l}%, ${alpha})`;
}

/**
 * Draw a random pattern on the canvas
 */
function drawRandomPattern(ctx, width, height) {
    const patterns = [
        drawDots,
        drawGrid,
        drawCircles,
        drawTriangles
    ];
    
    // Pick a random pattern
    const randomPattern = patterns[Math.floor(Math.random() * patterns.length)];
    randomPattern(ctx, width, height);
}

function drawDots(ctx, width, height) {
    const dotSize = 2;
    const spacing = 20;
    const color = 'rgba(255, 255, 255, 0.3)';
    
    ctx.fillStyle = color;
    
    for (let x = spacing; x < width; x += spacing) {
        for (let y = spacing; y < height; y += spacing) {
            ctx.beginPath();
            ctx.arc(x, y, dotSize, 0, Math.PI * 2);
            ctx.fill();
        }
    }
}

function drawGrid(ctx, width, height) {
    const lineWidth = 1;
    const spacing = 30;
    const color = 'rgba(255, 255, 255, 0.2)';
    
    ctx.strokeStyle = color;
    ctx.lineWidth = lineWidth;
    
    // Draw vertical lines
    for (let x = spacing; x < width; x += spacing) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
    }
    
    // Draw horizontal lines
    for (let y = spacing; y < height; y += spacing) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
    }
}

function drawCircles(ctx, width, height) {
    const color = 'rgba(255, 255, 255, 0.2)';
    const maxRadius = Math.min(width, height) / 4;
    
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    
    for (let i = 0; i < 5; i++) {
        const x = Math.random() * width;
        const y = Math.random() * height;
        const radius = Math.random() * maxRadius + 20;
        
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        ctx.stroke();
    }
}

function drawTriangles(ctx, width, height) {
    const color = 'rgba(255, 255, 255, 0.2)';
    const size = 50;
    
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    
    for (let i = 0; i < 7; i++) {
        const x = Math.random() * width;
        const y = Math.random() * height;
        
        ctx.beginPath();
        ctx.moveTo(x, y - size);
        ctx.lineTo(x + size, y + size);
        ctx.lineTo(x - size, y + size);
        ctx.closePath();
        ctx.stroke();
    }
}

// Initialize on document load
document.addEventListener('DOMContentLoaded', function() {
    // Find all images with development placeholders
    if (window.__DEBUG_MODE) {
        const landingImages = document.querySelectorAll('.landing-page img');
        
        landingImages.forEach(img => {
            // If image is not loaded yet, set up an error handler
            if (!img.complete || img.naturalWidth === 0) {
                img.onerror = function() {
                    generateCanvasPlaceholder(this);
                };
            }
        });
    }
});

// Make functions globally available
window.createImagePlaceholder = createImagePlaceholder;
window.generateCanvasPlaceholder = generateCanvasPlaceholder; 