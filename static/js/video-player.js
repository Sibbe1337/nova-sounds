/**
 * Video Player Component
 * 
 * A lightweight, accessible video player with custom controls
 * and support for multiple video formats.
 */
class VideoPlayer {
  /**
   * Creates a new video player instance
   * 
   * @param {Object} options - Configuration options
   * @param {string} options.containerId - ID of the container element
   * @param {string} options.videoUrl - URL of the video
   * @param {string} options.posterUrl - Optional poster image URL
   * @param {boolean} options.autoplay - Whether to autoplay (default: false)
   * @param {boolean} options.loop - Whether to loop playback (default: false)
   * @param {boolean} options.muted - Whether to start muted (default: false)
   * @param {Function} options.onPlay - Callback when playback starts
   * @param {Function} options.onPause - Callback when playback pauses
   * @param {Function} options.onEnded - Callback when playback ends
   */
  constructor(options) {
    // Store options with defaults
    this.options = {
      autoplay: false,
      loop: false,
      muted: false,
      ...options
    };
    
    // Find container
    this.container = document.getElementById(options.containerId);
    if (!this.container) {
      console.error(`Container #${options.containerId} not found`);
      return;
    }
    
    // Build the player UI
    this._buildInterface();
    
    // Connect event listeners
    this._connectEvents();
  }
  
  /**
   * Builds the player UI
   */
  _buildInterface() {
    // Create player container
    this.playerContainer = document.createElement('div');
    this.playerContainer.className = 'video-player';
    
    // Create video element
    this.video = document.createElement('video');
    this.video.className = 'video-element';
    this.video.src = this.options.videoUrl;
    
    if (this.options.posterUrl) {
      this.video.poster = this.options.posterUrl;
    }
    
    this.video.autoplay = this.options.autoplay;
    this.video.loop = this.options.loop;
    this.video.muted = this.options.muted;
    this.video.playsInline = true;
    this.video.preload = 'metadata';
    
    // Accessibility attributes
    this.video.setAttribute('aria-label', 'Video player');
    this.video.setAttribute('tabindex', '0');
    
    // Create custom controls container
    this.controls = document.createElement('div');
    this.controls.className = 'video-controls';
    
    // Play/pause button
    this.playButton = document.createElement('button');
    this.playButton.className = 'video-play-button';
    this.playButton.innerHTML = '<i class="fas fa-play"></i>';
    this.playButton.setAttribute('aria-label', 'Play');
    
    // Progress bar
    this.progressContainer = document.createElement('div');
    this.progressContainer.className = 'video-progress';
    
    this.progressBar = document.createElement('div');
    this.progressBar.className = 'video-progress-bar';
    
    this.progressFill = document.createElement('div');
    this.progressFill.className = 'video-progress-fill';
    
    this.progressThumb = document.createElement('div');
    this.progressThumb.className = 'video-progress-thumb';
    
    // Time display
    this.timeDisplay = document.createElement('div');
    this.timeDisplay.className = 'video-time';
    this.timeDisplay.textContent = '0:00 / 0:00';
    
    // Volume control
    this.volumeControl = document.createElement('div');
    this.volumeControl.className = 'video-volume';
    
    this.volumeButton = document.createElement('button');
    this.volumeButton.className = 'video-volume-button';
    this.volumeButton.innerHTML = '<i class="fas fa-volume-up"></i>';
    this.volumeButton.setAttribute('aria-label', 'Toggle mute');
    
    this.volumeSlider = document.createElement('input');
    this.volumeSlider.type = 'range';
    this.volumeSlider.min = '0';
    this.volumeSlider.max = '1';
    this.volumeSlider.step = '0.1';
    this.volumeSlider.value = this.options.muted ? '0' : '1';
    this.volumeSlider.className = 'video-volume-slider';
    this.volumeSlider.setAttribute('aria-label', 'Volume');
    
    // Fullscreen button
    this.fullscreenButton = document.createElement('button');
    this.fullscreenButton.className = 'video-fullscreen-button';
    this.fullscreenButton.innerHTML = '<i class="fas fa-expand"></i>';
    this.fullscreenButton.setAttribute('aria-label', 'Toggle fullscreen');
    
    // Assemble the UI
    this.progressBar.appendChild(this.progressFill);
    this.progressBar.appendChild(this.progressThumb);
    this.progressContainer.appendChild(this.progressBar);
    
    this.volumeControl.appendChild(this.volumeButton);
    this.volumeControl.appendChild(this.volumeSlider);
    
    this.controls.appendChild(this.playButton);
    this.controls.appendChild(this.progressContainer);
    this.controls.appendChild(this.timeDisplay);
    this.controls.appendChild(this.volumeControl);
    this.controls.appendChild(this.fullscreenButton);
    
    this.playerContainer.appendChild(this.video);
    this.playerContainer.appendChild(this.controls);
    
    // Clear and append to container
    this.container.innerHTML = '';
    this.container.appendChild(this.playerContainer);
    
    // Initial volume
    this.setVolume(this.options.muted ? 0 : 1);
  }
  
  /**
   * Adds event listeners for interactive elements
   */
  _connectEvents() {
    // Video events
    this.video.addEventListener('loadedmetadata', () => {
      this._updateTimeDisplay();
    });
    
    this.video.addEventListener('timeupdate', () => {
      this._updateTimeDisplay();
      this._updateProgressBar();
    });
    
    this.video.addEventListener('play', () => {
      this.playButton.innerHTML = '<i class="fas fa-pause"></i>';
      this.playButton.setAttribute('aria-label', 'Pause');
      
      if (typeof this.options.onPlay === 'function') {
        this.options.onPlay();
      }
    });
    
    this.video.addEventListener('pause', () => {
      this.playButton.innerHTML = '<i class="fas fa-play"></i>';
      this.playButton.setAttribute('aria-label', 'Play');
      
      if (typeof this.options.onPause === 'function') {
        this.options.onPause();
      }
    });
    
    this.video.addEventListener('ended', () => {
      this.playButton.innerHTML = '<i class="fas fa-play"></i>';
      this.playButton.setAttribute('aria-label', 'Play');
      
      if (typeof this.options.onEnded === 'function') {
        this.options.onEnded();
      }
    });
    
    // Click on video to toggle play/pause
    this.video.addEventListener('click', () => {
      this.togglePlayback();
    });
    
    // Control events
    this.playButton.addEventListener('click', () => {
      this.togglePlayback();
    });
    
    this.progressContainer.addEventListener('click', (e) => {
      const rect = this.progressContainer.getBoundingClientRect();
      const position = (e.clientX - rect.left) / rect.width;
      this.seek(position * this.video.duration);
    });
    
    this.volumeButton.addEventListener('click', () => {
      this.toggleMute();
    });
    
    this.volumeSlider.addEventListener('input', () => {
      this.setVolume(parseFloat(this.volumeSlider.value));
    });
    
    this.fullscreenButton.addEventListener('click', () => {
      this.toggleFullscreen();
    });
    
    // Add keyboard support
    this.playerContainer.addEventListener('keydown', (e) => {
      // Space or K to toggle play/pause
      if (e.key === ' ' || e.key === 'k' || e.key === 'K') {
        e.preventDefault();
        this.togglePlayback();
      }
      
      // Left arrow to seek backward
      if (e.key === 'ArrowLeft') {
        e.preventDefault();
        this.seek(Math.max(0, this.video.currentTime - 5));
      }
      
      // Right arrow to seek forward
      if (e.key === 'ArrowRight') {
        e.preventDefault();
        this.seek(Math.min(this.video.duration, this.video.currentTime + 5));
      }
      
      // M to toggle mute
      if (e.key === 'm' || e.key === 'M') {
        e.preventDefault();
        this.toggleMute();
      }
      
      // F to toggle fullscreen
      if (e.key === 'f' || e.key === 'F') {
        e.preventDefault();
        this.toggleFullscreen();
      }
    });
    
    // Show controls on hover or focus
    this.playerContainer.addEventListener('mouseenter', () => {
      this.playerContainer.classList.add('controls-visible');
    });
    
    this.playerContainer.addEventListener('mouseleave', () => {
      if (!this.video.paused) {
        this.playerContainer.classList.remove('controls-visible');
      }
    });
    
    this.playerContainer.addEventListener('focus', () => {
      this.playerContainer.classList.add('controls-visible');
    }, true);
    
    this.playerContainer.addEventListener('blur', () => {
      this.playerContainer.classList.remove('controls-visible');
    }, true);
  }
  
  /**
   * Updates the time display
   */
  _updateTimeDisplay() {
    const currentTime = this.video.currentTime;
    const duration = this.video.duration || 0;
    
    const formatTime = (seconds) => {
      const minutes = Math.floor(seconds / 60);
      const secs = Math.floor(seconds % 60);
      return `${minutes}:${secs.toString().padStart(2, '0')}`;
    };
    
    this.timeDisplay.textContent = `${formatTime(currentTime)} / ${formatTime(duration)}`;
  }
  
  /**
   * Updates the progress bar
   */
  _updateProgressBar() {
    const progress = (this.video.currentTime / this.video.duration) * 100;
    this.progressFill.style.width = `${progress}%`;
    this.progressThumb.style.left = `${progress}%`;
  }
  
  /**
   * Toggles between play and pause
   */
  togglePlayback() {
    if (this.video.paused) {
      this.play();
    } else {
      this.pause();
    }
  }
  
  /**
   * Starts or resumes playback
   */
  play() {
    this.video.play().catch(error => {
      console.error('Error playing video:', error);
    });
  }
  
  /**
   * Pauses playback
   */
  pause() {
    this.video.pause();
  }
  
  /**
   * Seeks to a specific time in the video
   * 
   * @param {number} time - Time in seconds
   */
  seek(time) {
    this.video.currentTime = Math.max(0, Math.min(time, this.video.duration));
  }
  
  /**
   * Sets the video volume
   * 
   * @param {number} volume - Volume between 0 and 1
   */
  setVolume(volume) {
    this.video.volume = Math.max(0, Math.min(volume, 1));
    this.volumeSlider.value = this.video.volume;
    
    // Update volume icon
    if (this.video.volume === 0) {
      this.volumeButton.innerHTML = '<i class="fas fa-volume-mute"></i>';
    } else if (this.video.volume < 0.5) {
      this.volumeButton.innerHTML = '<i class="fas fa-volume-down"></i>';
    } else {
      this.volumeButton.innerHTML = '<i class="fas fa-volume-up"></i>';
    }
  }
  
  /**
   * Toggles mute state
   */
  toggleMute() {
    if (this.video.volume === 0) {
      // Unmute (restore previous volume)
      this.setVolume(this._previousVolume || 1);
    } else {
      // Mute (store current volume)
      this._previousVolume = this.video.volume;
      this.setVolume(0);
    }
  }
  
  /**
   * Toggles fullscreen mode
   */
  toggleFullscreen() {
    if (!document.fullscreenElement) {
      // Enter fullscreen
      if (this.playerContainer.requestFullscreen) {
        this.playerContainer.requestFullscreen();
      } else if (this.playerContainer.webkitRequestFullscreen) {
        this.playerContainer.webkitRequestFullscreen();
      } else if (this.playerContainer.msRequestFullscreen) {
        this.playerContainer.msRequestFullscreen();
      }
      this.fullscreenButton.innerHTML = '<i class="fas fa-compress"></i>';
    } else {
      // Exit fullscreen
      if (document.exitFullscreen) {
        document.exitFullscreen();
      } else if (document.webkitExitFullscreen) {
        document.webkitExitFullscreen();
      } else if (document.msExitFullscreen) {
        document.msExitFullscreen();
      }
      this.fullscreenButton.innerHTML = '<i class="fas fa-expand"></i>';
    }
  }
} 