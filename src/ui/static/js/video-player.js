/**
 * VideoPlayer Class
 * Handles video player functionality and UI interaction
 */
class VideoPlayer {
    /**
     * Initialize the video player
     * @param {Object} options Configuration options
     * @param {string} options.containerId ID of the container element
     * @param {string} options.videoUrl URL of the video file
     * @param {string} options.posterUrl URL of the poster image (optional)
     * @param {boolean} options.autoplay Whether to autoplay the video (default: false)
     * @param {boolean} options.muted Whether to mute the video (default: false)
     * @param {boolean} options.controls Whether to show native controls (default: false)
     * @param {boolean} options.loop Whether to loop the video (default: false)
     * @param {function} options.onPlay Callback when video starts playing
     * @param {function} options.onPause Callback when video is paused
     * @param {function} options.onEnd Callback when video ends
     */
    constructor(options) {
        this.options = Object.assign({
            containerId: null,
            videoUrl: null,
            posterUrl: null,
            autoplay: false,
            muted: false,
            controls: false,
            loop: false,
            onPlay: null,
            onPause: null,
            onEnd: null,
        }, options);

        // Validate required options
        if (!this.options.containerId) {
            console.error('VideoPlayer: containerId is required');
            return;
        }

        if (!this.options.videoUrl) {
            console.error('VideoPlayer: videoUrl is required');
            return;
        }

        // Get container element
        this.container = document.getElementById(this.options.containerId);
        if (!this.container) {
            console.error(`VideoPlayer: container with ID '${this.options.containerId}' not found`);
            return;
        }

        // Initialize the player
        this.init();
    }

    /**
     * Initialize the video player
     */
    init() {
        // Create player elements
        this.createPlayerElements();

        // Set up event listeners
        this.setupEventListeners();

        // Initialize state
        this.isPlaying = false;
        this.isMuted = this.options.muted;
        this.volume = 1.0;

        // Apply initial state
        if (this.isMuted) {
            this.video.muted = true;
            if (this.volumeControl) {
                this.volumeControl.querySelector('input').value = 0;
            }
        }

        // Auto play if specified
        if (this.options.autoplay) {
            // Try to autoplay with sound
            this.video.play()
                .catch(error => {
                    // If autoplay with sound fails, try muted autoplay
                    this.video.muted = true;
                    this.isMuted = true;
                    if (this.volumeControl) {
                        this.volumeControl.querySelector('input').value = 0;
                    }
                    this.video.play()
                        .catch(e => console.error('Autoplay failed:', e));
                });
        }
    }

    /**
     * Create player HTML elements
     */
    createPlayerElements() {
        // Create and set up video element
        this.video = document.createElement('video');
        this.video.src = this.options.videoUrl;
        this.video.classList.add('video-element');
        this.video.playsInline = true;
        this.video.loop = this.options.loop;
        this.video.muted = this.options.muted;
        
        if (this.options.posterUrl) {
            this.video.poster = this.options.posterUrl;
        }

        if (this.options.controls) {
            this.video.controls = true;
        } else {
            // Create custom controls if native controls are disabled
            this.createCustomControls();
        }

        // Add video element to container
        this.container.appendChild(this.video);
        this.container.classList.add('video-player');
    }

    /**
     * Create custom video controls
     */
    createCustomControls() {
        // Create controls container
        this.controls = document.createElement('div');
        this.controls.classList.add('video-controls');

        // Play/pause button
        this.playPauseButton = document.createElement('button');
        this.playPauseButton.classList.add('play-pause');
        this.playPauseButton.innerHTML = '<i class="fas fa-play"></i>';
        this.playPauseButton.setAttribute('aria-label', 'Play');

        // Progress bar
        this.progressBar = document.createElement('div');
        this.progressBar.classList.add('progress-bar');
        this.progressFill = document.createElement('div');
        this.progressFill.classList.add('progress-fill');
        this.progressBar.appendChild(this.progressFill);

        // Volume control
        this.volumeControl = document.createElement('div');
        this.volumeControl.classList.add('volume-control');

        this.volumeButton = document.createElement('button');
        this.volumeButton.classList.add('volume-icon');
        this.volumeButton.innerHTML = this.options.muted ? 
            '<i class="fas fa-volume-mute"></i>' : 
            '<i class="fas fa-volume-up"></i>';
        this.volumeButton.setAttribute('aria-label', this.options.muted ? 'Unmute' : 'Mute');

        this.volumeSlider = document.createElement('input');
        this.volumeSlider.type = 'range';
        this.volumeSlider.min = 0;
        this.volumeSlider.max = 1;
        this.volumeSlider.step = 0.1;
        this.volumeSlider.value = this.options.muted ? 0 : 1;
        this.volumeSlider.classList.add('volume-slider');

        this.volumeControl.appendChild(this.volumeButton);
        this.volumeControl.appendChild(this.volumeSlider);

        // Fullscreen button
        this.fullscreenButton = document.createElement('button');
        this.fullscreenButton.classList.add('fullscreen-button');
        this.fullscreenButton.innerHTML = '<i class="fas fa-expand"></i>';
        this.fullscreenButton.setAttribute('aria-label', 'Fullscreen');

        // Add all controls to the container
        this.controls.appendChild(this.playPauseButton);
        this.controls.appendChild(this.progressBar);
        this.controls.appendChild(this.volumeControl);
        this.controls.appendChild(this.fullscreenButton);

        // Add controls to player
        this.container.appendChild(this.controls);
    }

    /**
     * Set up event listeners for video and controls
     */
    setupEventListeners() {
        // Video events
        this.video.addEventListener('timeupdate', this.handleTimeUpdate.bind(this));
        this.video.addEventListener('ended', this.handleVideoEnded.bind(this));
        this.video.addEventListener('click', this.togglePlay.bind(this));

        // Only set up custom control events if we have custom controls
        if (!this.options.controls && this.controls) {
            // Play/pause button
            this.playPauseButton.addEventListener('click', (e) => {
                e.stopPropagation();
                this.togglePlay();
            });

            // Progress bar
            this.progressBar.addEventListener('click', this.handleProgressBarClick.bind(this));

            // Volume controls
            if (this.volumeButton) {
                this.volumeButton.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.toggleMute();
                });
            }

            if (this.volumeSlider) {
                this.volumeSlider.addEventListener('input', (e) => {
                    e.stopPropagation();
                    this.setVolume(parseFloat(e.target.value));
                });
            }

            // Fullscreen button
            if (this.fullscreenButton) {
                this.fullscreenButton.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.toggleFullscreen();
                });
            }
        }
    }

    /**
     * Handle time update event to update progress bar
     */
    handleTimeUpdate() {
        if (this.progressFill && this.video.duration) {
            const percentage = (this.video.currentTime / this.video.duration) * 100;
            this.progressFill.style.width = `${percentage}%`;
        }
    }

    /**
     * Handle video ended event
     */
    handleVideoEnded() {
        this.isPlaying = false;
        if (this.playPauseButton) {
            this.playPauseButton.innerHTML = '<i class="fas fa-play"></i>';
            this.playPauseButton.setAttribute('aria-label', 'Play');
        }

        // Call onEnd callback if provided
        if (typeof this.options.onEnd === 'function') {
            this.options.onEnd();
        }
    }

    /**
     * Handle progress bar click to seek
     * @param {Event} e Click event
     */
    handleProgressBarClick(e) {
        const rect = this.progressBar.getBoundingClientRect();
        const pos = (e.clientX - rect.left) / rect.width;
        this.video.currentTime = pos * this.video.duration;
    }

    /**
     * Toggle play/pause
     */
    togglePlay() {
        if (this.video.paused) {
            this.play();
        } else {
            this.pause();
        }
    }

    /**
     * Play the video
     */
    play() {
        this.video.play()
            .then(() => {
                this.isPlaying = true;
                if (this.playPauseButton) {
                    this.playPauseButton.innerHTML = '<i class="fas fa-pause"></i>';
                    this.playPauseButton.setAttribute('aria-label', 'Pause');
                }
                
                // Call onPlay callback if provided
                if (typeof this.options.onPlay === 'function') {
                    this.options.onPlay();
                }
            })
            .catch(error => {
                console.error('Error playing video:', error);
                // Try muted play as fallback for autoplay restrictions
                if (!this.video.muted) {
                    this.video.muted = true;
                    this.isMuted = true;
                    if (this.volumeControl) {
                        this.volumeControl.querySelector('input').value = 0;
                        this.volumeButton.innerHTML = '<i class="fas fa-volume-mute"></i>';
                    }
                    this.video.play()
                        .catch(e => console.error('Muted play also failed:', e));
                }
            });
    }

    /**
     * Pause the video
     */
    pause() {
        this.video.pause();
        this.isPlaying = false;
        if (this.playPauseButton) {
            this.playPauseButton.innerHTML = '<i class="fas fa-play"></i>';
            this.playPauseButton.setAttribute('aria-label', 'Play');
        }
        
        // Call onPause callback if provided
        if (typeof this.options.onPause === 'function') {
            this.options.onPause();
        }
    }

    /**
     * Toggle mute
     */
    toggleMute() {
        this.isMuted = !this.isMuted;
        this.video.muted = this.isMuted;
        
        if (this.volumeButton) {
            this.volumeButton.innerHTML = this.isMuted ? 
                '<i class="fas fa-volume-mute"></i>' : 
                '<i class="fas fa-volume-up"></i>';
            this.volumeButton.setAttribute('aria-label', this.isMuted ? 'Unmute' : 'Mute');
        }
        
        if (this.volumeSlider) {
            this.volumeSlider.value = this.isMuted ? 0 : this.volume;
        }
    }

    /**
     * Set volume level
     * @param {number} level Volume level (0-1)
     */
    setVolume(level) {
        this.volume = level;
        this.video.volume = level;
        
        this.isMuted = level === 0;
        this.video.muted = this.isMuted;
        
        if (this.volumeButton) {
            if (level === 0) {
                this.volumeButton.innerHTML = '<i class="fas fa-volume-mute"></i>';
                this.volumeButton.setAttribute('aria-label', 'Unmute');
            } else if (level < 0.5) {
                this.volumeButton.innerHTML = '<i class="fas fa-volume-down"></i>';
                this.volumeButton.setAttribute('aria-label', 'Mute');
            } else {
                this.volumeButton.innerHTML = '<i class="fas fa-volume-up"></i>';
                this.volumeButton.setAttribute('aria-label', 'Mute');
            }
        }
    }

    /**
     * Toggle fullscreen mode
     */
    toggleFullscreen() {
        if (!document.fullscreenElement) {
            this.container.requestFullscreen().catch(err => {
                console.error(`Error attempting to enable full-screen mode: ${err.message}`);
            });
        } else {
            document.exitFullscreen();
        }
    }
}

// Make VideoPlayer available globally
window.VideoPlayer = VideoPlayer; 