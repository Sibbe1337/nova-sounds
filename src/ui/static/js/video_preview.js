// Video Preview Player
// Provides a preview player for generated videos with platform-specific aspect ratio simulations

class VideoPreviewPlayer {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.videoSrc = null;
        this.currentPlatform = 'tiktok'; // default platform
        this.videoMetadata = null;
        
        // Platform specifications
        this.platforms = {
            tiktok: {
                name: 'TikTok',
                ratio: '9:16',
                width: 1080,
                height: 1920,
                bgColor: '#000000',
                icon: '<i class="bi bi-tiktok"></i>',
                maxDuration: 180 // 3 minutes in seconds
            },
            youtube: {
                name: 'YouTube Shorts',
                ratio: '9:16',
                width: 1080,
                height: 1920,
                bgColor: '#0F0F0F',
                icon: '<i class="bi bi-youtube"></i>',
                maxDuration: 60 // 1 minute in seconds
            },
            instagram: {
                name: 'Instagram Reels',
                ratio: '9:16',
                width: 1080,
                height: 1920,
                bgColor: '#121212',
                icon: '<i class="bi bi-instagram"></i>',
                maxDuration: 90 // 1.5 minutes in seconds
            },
            standard: {
                name: 'Standard Player',
                ratio: '16:9',
                width: 1920,
                height: 1080,
                bgColor: '#000000',
                icon: '<i class="bi bi-play-circle"></i>',
                maxDuration: 600 // 10 minutes in seconds
            },
            square: {
                name: 'Square',
                ratio: '1:1',
                width: 1080,
                height: 1080,
                bgColor: '#000000',
                icon: '<i class="bi bi-square"></i>',
                maxDuration: 90 // 1.5 minutes in seconds
            }
        };
        
        // Default options
        this.options = {
            onPlatformChange: null,
            autoPlay: false,
            showControls: true,
            showInfo: true,
            enableDownload: true,
            enableSharing: true,
            ...options
        };
        
        // Initialize UI
        this.initialize();
    }
    
    initialize() {
        if (!this.container) {
            console.error(`Container element with ID "${this.containerId}" not found`);
            return;
        }
        
        // Create UI
        this.createUI();
        
        // Add event listeners
        this.addEventListeners();
    }
    
    createUI() {
        // Create platform selector and video container
        const platform = this.platforms[this.currentPlatform];
        
        this.container.innerHTML = `
            <div class="video-preview-container">
                <div class="platform-selector mb-3">
                    <div class="d-flex align-items-center">
                        <label class="form-label me-2 mb-0">Preview As:</label>
                        <div class="btn-group" role="group" aria-label="Platform selector">
                            ${Object.keys(this.platforms).map(key => `
                                <button type="button" 
                                    class="btn btn-outline-primary ${key === this.currentPlatform ? 'active' : ''}" 
                                    data-platform="${key}"
                                    aria-pressed="${key === this.currentPlatform ? 'true' : 'false'}"
                                    title="${this.platforms[key].name}">
                                    ${this.platforms[key].icon} ${this.platforms[key].name}
                                </button>
                            `).join('')}
                        </div>
                    </div>
                </div>
                
                <div class="video-container-wrapper d-flex justify-content-center mb-3">
                    <div class="video-outer-container" style="background-color: ${platform.bgColor};">
                        <div class="video-inner-container" 
                            style="max-width: ${this.calculateAspectRatioWidth(platform)}px;
                                  max-height: 70vh;
                                  aspect-ratio: ${platform.width} / ${platform.height};">
                            <div class="video-placeholder d-flex flex-column align-items-center justify-content-center text-white p-4">
                                <i class="bi bi-film mb-2" style="font-size: 3rem;"></i>
                                <div class="text-center">
                                    <p>No video loaded</p>
                                    <small>Generated videos will appear here</small>
                                </div>
                            </div>
                            <video id="${this.containerId}-video" 
                                class="video-player w-100 h-100" 
                                style="display: none;"
                                ${this.options.showControls ? 'controls' : ''}
                                ${this.options.autoPlay ? 'autoplay' : ''}
                                preload="metadata">
                            </video>
                        </div>
                    </div>
                </div>
                
                <div class="video-metadata p-3 border rounded bg-light mb-3" style="display: none;">
                    <div class="row">
                        <div class="col-sm-8">
                            <h5 class="video-title mb-1"></h5>
                            <p class="video-description text-muted small mb-2"></p>
                            <div class="video-stats small d-flex flex-wrap">
                                <span class="me-3 mb-1"><i class="bi bi-clock"></i> <span class="video-duration"></span></span>
                                <span class="me-3 mb-1"><i class="bi bi-music-note"></i> <span class="video-track"></span></span>
                                <span class="me-3 mb-1"><i class="bi bi-tag"></i> <span class="video-style"></span></span>
                            </div>
                        </div>
                        <div class="col-sm-4 d-flex align-items-start justify-content-end">
                            <div class="btn-group" role="group" aria-label="Video actions">
                                ${this.options.enableDownload ? `
                                <button class="btn btn-sm btn-outline-primary download-btn" title="Download Video">
                                    <i class="bi bi-download"></i> Download
                                </button>` : ''}
                                ${this.options.enableSharing ? `
                                <button class="btn btn-sm btn-outline-primary share-btn" title="Share Video">
                                    <i class="bi bi-share"></i> Share
                                </button>` : ''}
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="video-alert alert alert-warning" style="display: none;" role="alert">
                    <i class="bi bi-exclamation-triangle"></i> <span class="alert-message"></span>
                </div>
            </div>
        `;
        
        // Cache DOM elements
        this.videoElement = document.getElementById(`${this.containerId}-video`);
        this.videoPlaceholder = this.container.querySelector('.video-placeholder');
        this.videoMetadata = this.container.querySelector('.video-metadata');
        this.videoAlert = this.container.querySelector('.video-alert');
        this.videoTitle = this.container.querySelector('.video-title');
        this.videoDescription = this.container.querySelector('.video-description');
        this.videoDuration = this.container.querySelector('.video-duration');
        this.videoTrack = this.container.querySelector('.video-track');
        this.videoStyle = this.container.querySelector('.video-style');
        this.downloadBtn = this.container.querySelector('.download-btn');
        this.shareBtn = this.container.querySelector('.share-btn');
        this.platformBtns = this.container.querySelectorAll('.platform-selector button');
    }
    
    addEventListeners() {
        // Platform selector buttons
        this.platformBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const platform = e.currentTarget.dataset.platform;
                this.changePlatform(platform);
            });
        });
        
        // Download button
        if (this.downloadBtn) {
            this.downloadBtn.addEventListener('click', () => this.downloadVideo());
        }
        
        // Share button
        if (this.shareBtn) {
            this.shareBtn.addEventListener('click', () => this.shareVideo());
        }
        
        // Video player events
        if (this.videoElement) {
            this.videoElement.addEventListener('loadedmetadata', () => {
                this.checkVideoDuration();
            });
            
            this.videoElement.addEventListener('error', (e) => {
                console.error('Video error:', e);
                this.showAlert('Error loading video. Please try again.');
            });
        }
    }
    
    calculateAspectRatioWidth(platform) {
        // Calculate width based on a fixed height of 500px
        const fixedHeight = 500;
        return (platform.width / platform.height) * fixedHeight;
    }
    
    changePlatform(platformKey) {
        if (!this.platforms[platformKey]) {
            console.error(`Platform "${platformKey}" not found`);
            return;
        }
        
        // Update current platform
        this.currentPlatform = platformKey;
        const platform = this.platforms[platformKey];
        
        // Update UI
        this.platformBtns.forEach(btn => {
            const isActive = btn.dataset.platform === platformKey;
            btn.classList.toggle('active', isActive);
            btn.setAttribute('aria-pressed', isActive ? 'true' : 'false');
        });
        
        // Update video container style
        const videoOuterContainer = this.container.querySelector('.video-outer-container');
        const videoInnerContainer = this.container.querySelector('.video-inner-container');
        
        videoOuterContainer.style.backgroundColor = platform.bgColor;
        videoInnerContainer.style.maxWidth = `${this.calculateAspectRatioWidth(platform)}px`;
        videoInnerContainer.style.aspectRatio = `${platform.width} / ${platform.height}`;
        
        // Check video duration against platform limits
        this.checkVideoDuration();
        
        // Trigger callback if provided
        if (typeof this.options.onPlatformChange === 'function') {
            this.options.onPlatformChange(platformKey, platform);
        }
    }
    
    loadVideo(videoData) {
        if (!videoData || !videoData.url) {
            console.error('Invalid video data');
            return;
        }
        
        this.videoSrc = videoData.url;
        this.videoData = videoData;
        
        if (this.videoElement) {
            // Set video source
            this.videoElement.src = this.videoSrc;
            this.videoElement.style.display = 'block';
            this.videoPlaceholder.style.display = 'none';
            
            // Load and play if autoplay is enabled
            this.videoElement.load();
            if (this.options.autoPlay) {
                this.videoElement.play().catch(error => {
                    console.warn('Autoplay prevented:', error);
                });
            }
            
            // Update metadata
            this.updateMetadata(videoData);
        }
    }
    
    updateMetadata(data) {
        if (!data) return;
        
        if (this.videoMetadata) {
            this.videoMetadata.style.display = 'block';
            
            // Update basic metadata
            if (this.videoTitle && data.title) {
                this.videoTitle.textContent = data.title;
            }
            
            if (this.videoDescription && data.description) {
                this.videoDescription.textContent = data.description;
            }
            
            if (this.videoDuration) {
                this.videoDuration.textContent = data.duration || this.formatDuration(this.videoElement.duration);
            }
            
            if (this.videoTrack && data.track) {
                this.videoTrack.textContent = typeof data.track === 'string' ? data.track : `${data.track.title} - ${data.track.artist}`;
            }
            
            if (this.videoStyle && data.style) {
                this.videoStyle.textContent = data.style;
            }
        }
    }
    
    formatDuration(seconds) {
        if (!seconds || isNaN(seconds)) return '00:00';
        
        seconds = Math.floor(seconds);
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        
        return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
    
    checkVideoDuration() {
        if (!this.videoElement || !this.videoElement.duration || isNaN(this.videoElement.duration)) {
            return;
        }
        
        const platform = this.platforms[this.currentPlatform];
        const videoDuration = this.videoElement.duration;
        
        if (platform.maxDuration && videoDuration > platform.maxDuration) {
            this.showAlert(`Warning: This video exceeds ${platform.name}'s maximum duration of ${this.formatDuration(platform.maxDuration)}.`);
        } else {
            this.hideAlert();
        }
    }
    
    showAlert(message) {
        if (this.videoAlert) {
            this.videoAlert.querySelector('.alert-message').textContent = message;
            this.videoAlert.style.display = 'block';
        }
    }
    
    hideAlert() {
        if (this.videoAlert) {
            this.videoAlert.style.display = 'none';
        }
    }
    
    downloadVideo() {
        if (!this.videoSrc) {
            this.showAlert('No video available to download.');
            return;
        }
        
        // Create a temporary anchor to trigger download
        const a = document.createElement('a');
        a.href = this.videoSrc;
        a.download = this.videoData.title ? `${this.videoData.title}.mp4` : 'video.mp4';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }
    
    shareVideo() {
        if (!this.videoSrc) {
            this.showAlert('No video available to share.');
            return;
        }
        
        if (navigator.share) {
            navigator.share({
                title: this.videoData.title || 'Music Responsive Video',
                text: this.videoData.description || 'Check out this music responsive video!',
                url: this.videoSrc
            }).catch(error => {
                console.error('Error sharing:', error);
            });
        } else {
            // Fallback: copy link to clipboard
            const tempInput = document.createElement('input');
            document.body.appendChild(tempInput);
            tempInput.value = this.videoSrc;
            tempInput.select();
            document.execCommand('copy');
            document.body.removeChild(tempInput);
            
            this.showAlert('Video link copied to clipboard!');
            setTimeout(() => this.hideAlert(), 3000);
        }
    }
    
    // Public methods
    play() {
        if (this.videoElement && this.videoSrc) {
            this.videoElement.play().catch(error => {
                console.error('Error playing video:', error);
            });
        }
    }
    
    pause() {
        if (this.videoElement) {
            this.videoElement.pause();
        }
    }
    
    getCurrentPlatform() {
        return {
            key: this.currentPlatform,
            ...this.platforms[this.currentPlatform]
        };
    }
    
    getVideoData() {
        return this.videoData;
    }
}

// Export the class for use in other modules
window.VideoPreviewPlayer = VideoPreviewPlayer; 
// Export the class for use in other modules
window.VideoPreviewPlayer = VideoPreviewPlayer; 