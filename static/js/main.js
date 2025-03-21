/**
 * YouTube Shorts Machine - Main JavaScript
 * Handles UI interactions, animations, and form functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all interactive components
    initCards();
    initUploadArea();
    initProgressBars();
    initMusicSelection();
    initCreateForm();
    
    // Set up navbar highlighting
    highlightActiveNavItem();
});

/**
 * Initialize interactive cards
 */
function initCards() {
    const cards = document.querySelectorAll('.interactive-card');
    
    cards.forEach(card => {
        // If the card has a data-href attribute, make it clickable
        if (card.dataset.href) {
            card.addEventListener('click', function(e) {
                // Don't navigate if clicking on a button or link inside the card
                if (e.target.tagName !== 'BUTTON' && e.target.tagName !== 'A' && !e.target.closest('button') && !e.target.closest('a')) {
                    window.location.href = this.dataset.href;
                }
            });
            
            // Add keyboard accessibility
            card.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    window.location.href = this.dataset.href;
                    e.preventDefault();
                }
            });
            
            // Add tabindex for keyboard focus
            if (!card.hasAttribute('tabindex')) {
                card.setAttribute('tabindex', '0');
            }
        }
    });
}

/**
 * Initialize drag and drop upload area
 */
function initUploadArea() {
    const uploadArea = document.querySelector('.upload-area') || document.querySelector('.upload-zone');
    const fileInput = document.getElementById('imageUpload');
    const filePreview = document.getElementById('filePreview');
    
    if (!uploadArea || !fileInput) return;
    
    uploadArea.addEventListener('click', function() {
        fileInput.click();
    });
    
    // Drag and drop events
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight() {
        uploadArea.classList.add('dragover');
    }
    
    function unhighlight() {
        uploadArea.classList.remove('dragover');
    }
    
    // Handle dropped files
    uploadArea.addEventListener('drop', handleDrop, false);
    fileInput.addEventListener('change', handleFiles, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles({ target: { files } });
    }
    
    function handleFiles(e) {
        const files = e.target.files;
        if (!files || files.length === 0) return;
        
        // Update upload area text
        const uploadText = uploadArea.querySelector('.upload-area-text') || uploadArea.querySelector('.upload-zone-text');
        if (uploadText) {
            uploadText.textContent = `${files.length} image${files.length > 1 ? 's' : ''} selected`;
        }
        
        // Enable continue button if needed
        const nextButton = document.getElementById('next-step-btn');
        if (nextButton) {
            nextButton.disabled = false;
        }
        
        // Update file previews
        if (filePreview) {
            filePreview.innerHTML = '';
            Array.from(files).forEach(file => {
                if (!file.type.match('image.*')) return;
                
                const reader = new FileReader();
                reader.onload = function(e) {
                    const previewItem = document.createElement('div');
                    previewItem.className = 'file-preview-item';
                    
                    const img = document.createElement('img');
                    img.className = 'file-preview-image';
                    img.src = e.target.result;
                    img.alt = file.name;
                    
                    const removeBtn = document.createElement('button');
                    removeBtn.className = 'file-preview-remove';
                    removeBtn.innerHTML = '<i class="fas fa-times"></i>';
                    removeBtn.setAttribute('type', 'button');
                    
                    previewItem.appendChild(img);
                    previewItem.appendChild(removeBtn);
                    filePreview.appendChild(previewItem);
                    
                    // Handle remove button
                    removeBtn.addEventListener('click', function() {
                        previewItem.remove();
                        // We can't actually remove a file from FileList, so we'll handle this on form submit
                    });
                };
                reader.readAsDataURL(file);
            });
        }
    }
}

/**
 * Initialize progress bars
 */
function initProgressBars() {
    const progressBars = document.querySelectorAll('.progress-bar-fill');
    
    progressBars.forEach(bar => {
        const container = bar.closest('.progress-container');
        if (container && container.dataset.progress) {
            const progress = container.dataset.progress;
            bar.style.width = `${progress}%`;
        }
    });
}

/**
 * Initialize music track selection
 */
function initMusicSelection() {
    const trackButtons = document.querySelectorAll('.select-btn');
    const previewButtons = document.querySelectorAll('.preview-btn');
    const selectedTrackInput = document.getElementById('selected_track');
    
    if (trackButtons.length === 0) return;
    
    // Handle track selection
    trackButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove selected class from all buttons
            trackButtons.forEach(btn => btn.classList.remove('selected'));
            
            // Add selected class to clicked button
            this.classList.add('selected');
            
            // Update hidden input value
            if (selectedTrackInput) {
                selectedTrackInput.value = this.dataset.track;
            }
            
            // Enable continue button
            const nextButton = document.getElementById('next-step-btn');
            if (nextButton) {
                nextButton.disabled = false;
            }
        });
    });
    
    // Handle music preview
    let currentAudio = null;
    
    previewButtons.forEach(button => {
        button.addEventListener('click', function() {
            const trackUrl = this.dataset.url;
            const trackId = this.dataset.track;
            const waveformData = JSON.parse(this.dataset.waveform || '[]');
            
            // Stop currently playing audio
            if (currentAudio) {
                currentAudio.pause();
                currentAudio = null;
                
                // Reset all preview buttons
                previewButtons.forEach(btn => {
                    btn.innerHTML = '<i class="fas fa-play"></i> Preview';
                });
            }
            
            // Play the new audio
            if (trackUrl && this.innerHTML.includes('fa-play')) {
                currentAudio = new Audio(trackUrl);
                currentAudio.play();
                
                // Update button
                this.innerHTML = '<i class="fas fa-pause"></i> Playing';
                
                // When audio ends
                currentAudio.onended = () => {
                    this.innerHTML = '<i class="fas fa-play"></i> Preview';
                    currentAudio = null;
                };
                
                // Display waveform if data exists
                if (waveformData.length > 0) {
                    const visualizer = document.getElementById(`visualizer-${trackId}`);
                    if (visualizer) {
                        renderWaveform(visualizer, waveformData);
                    }
                }
            }
        });
    });
}

/**
 * Render audio waveform
 */
function renderWaveform(container, data) {
    container.innerHTML = '';
    
    const maxValue = Math.max(...data);
    const waveformContainer = document.createElement('div');
    waveformContainer.className = 'waveform';
    
    data.forEach(value => {
        const bar = document.createElement('div');
        bar.className = 'waveform-bar';
        bar.style.height = `${(value / maxValue) * 100}%`;
        waveformContainer.appendChild(bar);
    });
    
    container.appendChild(waveformContainer);
}

/**
 * Initialize create form submission
 */
function initCreateForm() {
    const form = document.getElementById('videoForm');
    const submitBtn = document.getElementById('submitBtn');
    const processingIndicator = document.querySelector('.processing-indicator');
    const progressBar = document.getElementById('processingProgressBar');
    
    if (!form || !submitBtn) return;
    
    form.addEventListener('submit', function(e) {
        // Show processing UI
        if (submitBtn && processingIndicator) {
            submitBtn.disabled = true;
            submitBtn.classList.add('loading');
            processingIndicator.style.display = 'block';
        }
        
        // Simulate progress (in a real app, this would come from server events)
        if (progressBar) {
            simulateProgress(progressBar);
        }
    });
}

/**
 * Simulate progress for demo purposes
 */
function simulateProgress(progressBar) {
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 5;
        if (progress > 100) {
            progress = 100;
            clearInterval(interval);
        }
        
        progressBar.style.width = `${progress}%`;
        
        const progressText = document.getElementById('processingProgress');
        if (progressText) {
            progressText.textContent = `${Math.floor(progress)}%`;
        }
    }, 500);
}

/**
 * Highlight active navigation item
 */
function highlightActiveNavItem() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPath || (href === '/' && currentPath === '/index.html')) {
            link.classList.add('active');
        }
    });
}

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

// Make function globally available
window.createImagePlaceholder = createImagePlaceholder; 