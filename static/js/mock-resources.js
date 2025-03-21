/**
 * Mock Resources Handler
 * Provides placeholder resources for development and debugging
 */

(function() {
    // Only run in development/debug mode
    if (!window.isDebugMode) {
        const inDebugMode = document.querySelector('.debug-mode-indicator') !== null;
        // Check for any debug mode indicator
        if (!inDebugMode) {
            return;
        }
        window.isDebugMode = true;
    }

    // Initialize after DOM is loaded
    document.addEventListener('DOMContentLoaded', function() {
        createPlaceholders();
        injectMockData();
        handlePlaceholderEvents();
    });

    /**
     * Create placeholder elements for missing resources
     */
    function createPlaceholders() {
        // Check for missing images and create placeholders
        document.querySelectorAll('img').forEach(img => {
            img.onerror = function() {
                createImagePlaceholder(this);
            };
            
            // Check if image is already broken
            if (img.complete && (img.naturalWidth === 0 || img.naturalHeight === 0)) {
                createImagePlaceholder(img);
            }
        });
    }

    /**
     * Create an image placeholder for a broken image
     */
    function createImagePlaceholder(img) {
        // Prevent recursion
        if (img.classList.contains('placeholder-applied')) {
            return;
        }
        
        // Mark as placeholder applied
        img.classList.add('placeholder-applied');
        
        // Get dimensions from the image or set defaults
        const width = img.width || img.getAttribute('width') || 150;
        const height = img.height || img.getAttribute('height') || 100;
        
        // Store path for debugging
        const path = img.src || img.getAttribute('src') || '';
        
        // Check if this is an onboarding image (they're loaded but not displayed yet)
        const isOnboardingImage = path.includes('/onboarding/') && 
            (img.closest('.onboarding-slide') || path.includes('welcome.png') || 
             path.includes('music.png') || path.includes('style.png') || 
             path.includes('preview.png') || path.includes('upload.png'));
        
        // If it's an onboarding image, just log it but don't try to replace
        if (isOnboardingImage) {
            console.warn(`Onboarding image not loaded: ${path} - Will be handled when modal opens`);
            return;
        }
        
        // Create placeholder element
        const placeholder = document.createElement('div');
        placeholder.className = 'img-placeholder';
        placeholder.style.width = width + 'px';
        placeholder.style.height = height + 'px';
        
        // Extract filename from path
        const filename = path.split('/').pop();
        
        // Create filename text
        const filenameSpan = document.createElement('span');
        filenameSpan.className = 'placeholder-filename';
        filenameSpan.textContent = filename;
        placeholder.appendChild(filenameSpan);
        
        // Add placeholder icon
        const icon = document.createElement('i');
        icon.className = 'fas fa-image placeholder-icon';
        placeholder.appendChild(icon);
        
        // Add placeholder element and hide original img - add null check for parentNode
        if (img.parentNode) {
            img.parentNode.insertBefore(placeholder, img);
            img.style.display = 'none';
        } else {
            console.warn(`Cannot create placeholder: parent node is null for image ${path}`);
        }
        
        // Log missing resource
        console.warn(`Missing image: ${path}`);
    }

    /**
     * Inject mock data for development testing
     */
    function injectMockData() {
        // Check if mock data is available in localStorage
        const mockTracks = localStorage.getItem('mockTracks');
        if (mockTracks) {
            injectMockTracks(JSON.parse(mockTracks));
        }
        
        // Inject other types of mock data as needed
    }

    /**
     * Inject mock music tracks into the UI
     */
    function injectMockTracks(tracks) {
        const musicTrackGrid = document.querySelector('.music-track-grid');
        if (!musicTrackGrid || !tracks || !tracks.length) {
            return;
        }
        
        // Clear "no tracks" message if it exists
        const noTracksMessage = musicTrackGrid.querySelector('.no-tracks-message');
        if (noTracksMessage) {
            noTracksMessage.remove();
        }
        
        // Create track cards
        tracks.forEach(track => {
            // Create track card element
            const trackCard = document.createElement('div');
            trackCard.className = 'music-track-card';
            trackCard.dataset.trackId = track.id;
            
            // Build track card HTML
            trackCard.innerHTML = `
                <div class="music-info">
                    <div class="track-image">
                        <img src="${track.image_url}" alt="${track.title}" onerror="this.onerror=null; createImagePlaceholder(this);">
                    </div>
                    <div class="track-details">
                        <h3 class="track-title">${track.title}</h3>
                        <p class="track-artist">${track.artist}</p>
                        <div class="track-meta">
                            <span class="track-genre">${track.genre}</span>
                            <span class="track-duration">${track.duration}</span>
                            <span class="track-bpm">${track.bpm} BPM</span>
                        </div>
                    </div>
                </div>
                
                <div id="visualizer-${track.id}" class="music-preview-container"></div>
                
                <div class="track-actions">
                    <button 
                        type="button"
                        class="btn secondary preview-btn" 
                        data-track="${track.id}"
                        data-url="${track.url}"
                        data-title="${track.title}"
                        data-artist="${track.artist}"
                        data-waveform='${JSON.stringify(track.waveform_data)}'
                        aria-label="Preview ${track.title}"
                    >
                        <i class="fas fa-play"></i> Preview
                    </button>
                    <button 
                        type="button"
                        class="btn primary select-btn" 
                        data-track="${track.track_name}" 
                        aria-label="Select ${track.title}"
                    >
                        <i class="fas fa-check"></i> Select
                    </button>
                </div>
            `;
            
            // Add to music track grid
            musicTrackGrid.appendChild(trackCard);
        });
        
        // Add debug message
        const debugNotice = document.createElement('div');
        debugNotice.className = 'debug-notice';
        debugNotice.innerHTML = `
            <i class="fas fa-info-circle"></i>
            <span>Showing ${tracks.length} mock tracks from debug data</span>
        `;
        musicTrackGrid.parentNode.insertBefore(debugNotice, musicTrackGrid.nextSibling);
    }

    /**
     * Handle events for placeholder elements
     */
    function handlePlaceholderEvents() {
        // Use event delegation to handle potential dynamically added elements
        document.addEventListener('click', function(e) {
            // Handle placeholder image clicks to display more info
            if (e.target.closest('.img-placeholder')) {
                const placeholder = e.target.closest('.img-placeholder');
                const path = placeholder.getAttribute('data-original-src') || 'Unknown path';
                
                // Display debug information
                alert(`Missing image: ${path}\n\nThis is a placeholder for a missing image file.`);
            }
        });
    }

    /**
     * Create image placeholder (global function for onerror handlers)
     */
    window.createImagePlaceholder = createImagePlaceholder;
})();

/**
 * Generate placeholder images for missing assets in development mode
 */
(function() {
  // Only run in development mode
  if (!window.__DEBUG_MODE) return;
  
  // List of image paths to generate placeholders for
  const placeholderImages = [
    '/static/images/hero-image.jpg',
    '/static/images/templates.jpg',
    '/static/images/analytics.jpg',
    '/static/images/testimonials/user1.jpg',
    '/static/images/testimonials/user2.jpg',
    '/static/images/testimonials/user3.jpg'
  ];
  
  // Generate a placeholder for each image
  placeholderImages.forEach(imagePath => {
    // Create a mock image element
    const img = new Image();
    img.src = imagePath;
    
    // If the image fails to load, generate a canvas placeholder
    img.onerror = function() {
      console.log(`Creating canvas placeholder for: ${imagePath}`);
      generateCanvasPlaceholder(imagePath);
    };
  });
  
  /**
   * Generate a canvas-based placeholder and save it as a data URL
   */
  function generateCanvasPlaceholder(imagePath) {
    // Extract image name from path
    const imageName = imagePath.split('/').pop().replace('.jpg', '');
    
    // Create a canvas
    const canvas = document.createElement('canvas');
    canvas.width = 800;
    canvas.height = 600;
    const ctx = canvas.getContext('2d');
    
    // Fill background
    ctx.fillStyle = getRandomColor(0.3);
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Add image name text
    ctx.font = 'bold 40px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = '#333';
    ctx.fillText(imageName, canvas.width / 2, canvas.height / 2);
    
    // Convert to data URL
    const dataUrl = canvas.toDataURL('image/jpeg');
    
    // Create storage if needed
    if (!window.__mockResources) {
      window.__mockResources = {};
    }
    if (!window.__mockResources.images) {
      window.__mockResources.images = {};
    }
    
    // Store the data URL
    window.__mockResources.images[imagePath] = dataUrl;
    
    // Replace the image sources in the DOM
    document.querySelectorAll(`img[src="${imagePath}"]`).forEach(img => {
      img.src = dataUrl;
    });
  }
  
  /**
   * Get a random pastel color
   */
  function getRandomColor(alpha = 1) {
    const r = Math.floor(Math.random() * 100) + 155; // 155-255
    const g = Math.floor(Math.random() * 100) + 155; // 155-255
    const b = Math.floor(Math.random() * 100) + 155; // 155-255
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }
  
  // Set up a MutationObserver to handle dynamically added images
  const observer = new MutationObserver(mutations => {
    mutations.forEach(mutation => {
      if (mutation.type === 'childList') {
        mutation.addedNodes.forEach(node => {
          if (node.tagName === 'IMG') {
            const src = node.getAttribute('src');
            if (placeholderImages.includes(src) && window.__mockResources?.images?.[src]) {
              node.src = window.__mockResources.images[src];
            }
          }
          
          // Also check child images
          if (node.querySelectorAll) {
            node.querySelectorAll('img').forEach(img => {
              const src = img.getAttribute('src');
              if (placeholderImages.includes(src) && window.__mockResources?.images?.[src]) {
                img.src = window.__mockResources.images[src];
              }
            });
          }
        });
      }
    });
  });
  
  // Start observing
  observer.observe(document.body, { childList: true, subtree: true });
})(); 