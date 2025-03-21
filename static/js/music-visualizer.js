/**
 * Enhanced Music Visualizer Component
 * 
 * A reusable music visualization component that displays an interactive
 * waveform with playback controls.
 */
class MusicVisualizer {
    /**
     * Creates a new music visualizer
     * 
     * @param {Object} options - Configuration options
     * @param {string} options.containerId - ID of the container element
     * @param {string} options.audioUrl - URL of the audio file
     * @param {Object} options.waveformData - Optional pre-computed waveform data
     * @param {number} options.barCount - Number of bars to display (default: 64)
     * @param {boolean} options.autoPlay - Whether to autoplay the audio (default: false)
     * @param {Function} options.onPlay - Callback when playback starts
     * @param {Function} options.onPause - Callback when playback pauses
     * @param {Function} options.onEnded - Callback when playback ends
     */
    constructor(options) {
        // Store options
        this.options = {
            barCount: 64,
            autoPlay: false,
            ...options
        };
        
        // Find container
        this.container = document.getElementById(options.containerId);
        if (!this.container) {
            console.error(`Container #${options.containerId} not found`);
            return;
        }
        
        // Create audio element
        this.audio = new Audio(options.audioUrl);
        this.audio.preload = 'auto';
        
        // Initialize state
        this.isPlaying = false;
        this.volume = 0.8;
        this.duration = 0;
        this.currentTime = 0;
        
        // Build UI
        this._buildInterface();
        
        // Connect event listeners
        this._connectEvents();
        
        // Use pre-computed waveform data or generate random placeholder
        if (options.waveformData) {
            this.setWaveformData(options.waveformData);
        } else {
            this._generateRandomWaveform();
        }
    }
    
    /**
     * Builds the visualizer UI
     */
    _buildInterface() {
        // Create music visualizer container
        this.visualizer = document.createElement('div');
        this.visualizer.className = 'music-visualizer';
        
        // Create waveform container
        this.waveformContainer = document.createElement('div');
        this.waveformContainer.className = 'waveform-container';
        
        // Create waveform bars container
        this.waveformBars = document.createElement('div');
        this.waveformBars.className = 'waveform-bars';
        
        // Create progress overlay
        this.waveformProgress = document.createElement('div');
        this.waveformProgress.className = 'waveform-progress';
        
        // Create controls
        this.controls = document.createElement('div');
        this.controls.className = 'music-visualizer-controls';
        
        // Play button
        this.playButton = document.createElement('button');
        this.playButton.className = 'visualizer-play-button';
        this.playButton.innerHTML = '<i class="fas fa-play"></i>';
        this.playButton.setAttribute('aria-label', 'Play');
        
        // Time display
        this.timeDisplay = document.createElement('div');
        this.timeDisplay.className = 'visualizer-time';
        this.timeDisplay.textContent = '0:00 / 0:00';
        
        // Volume control
        this.volumeControl = document.createElement('div');
        this.volumeControl.className = 'visualizer-volume';
        
        this.volumeIcon = document.createElement('i');
        this.volumeIcon.className = 'fas fa-volume-up';
        
        this.volumeSlider = document.createElement('input');
        this.volumeSlider.type = 'range';
        this.volumeSlider.min = '0';
        this.volumeSlider.max = '1';
        this.volumeSlider.step = '0.1';
        this.volumeSlider.value = this.volume.toString();
        this.volumeSlider.className = 'visualizer-volume-slider';
        this.volumeSlider.setAttribute('aria-label', 'Volume');
        
        // Assemble the UI
        this.volumeControl.appendChild(this.volumeIcon);
        this.volumeControl.appendChild(this.volumeSlider);
        
        this.controls.appendChild(this.playButton);
        this.controls.appendChild(this.timeDisplay);
        this.controls.appendChild(this.volumeControl);
        
        this.waveformContainer.appendChild(this.waveformBars);
        this.waveformContainer.appendChild(this.waveformProgress);
        
        this.visualizer.appendChild(this.waveformContainer);
        this.visualizer.appendChild(this.controls);
        
        // Clear and append to container
        this.container.innerHTML = '';
        this.container.appendChild(this.visualizer);
    }
    
    /**
     * Adds event listeners for interactive elements
     */
    _connectEvents() {
        // Play/pause toggle
        this.playButton.addEventListener('click', () => this.togglePlayback());
        
        // Click on waveform to seek
        this.waveformContainer.addEventListener('click', (e) => {
            const rect = this.waveformContainer.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const percentage = x / rect.width;
            
            this.seek(percentage * this.duration);
        });
        
        // Volume control
        this.volumeSlider.addEventListener('input', () => {
            this.setVolume(parseFloat(this.volumeSlider.value));
        });
        
        // Audio events
        this.audio.addEventListener('loadedmetadata', () => {
            this.duration = this.audio.duration;
            this._updateTimeDisplay();
        });
        
        this.audio.addEventListener('timeupdate', () => {
            this.currentTime = this.audio.currentTime;
            this._updateTimeDisplay();
            this._updateProgress();
        });
        
        this.audio.addEventListener('ended', () => {
            this.pause();
            
            // Reset to beginning
            this.seek(0);
            
            // Call callback if provided
            if (typeof this.options.onEnded === 'function') {
                this.options.onEnded();
            }
        });
        
        // Keyboard accessibility
        this.playButton.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.togglePlayback();
            }
        });
        
        // Auto-play if enabled
        if (this.options.autoPlay) {
            this.play();
        }
    }
    
    /**
     * Generates random waveform data for visualization
     */
    _generateRandomWaveform() {
        this.waveformBars.innerHTML = '';
        
        for (let i = 0; i < this.options.barCount; i++) {
            const bar = document.createElement('div');
            bar.className = 'waveform-bar';
            
            // Generate random height between 1-3
            const randomHeight = (Math.random() * 2) + 1;
            bar.style.setProperty('--rand-height', randomHeight.toFixed(2));
            
            this.waveformBars.appendChild(bar);
        }
    }
    
    /**
     * Updates the time display
     */
    _updateTimeDisplay() {
        const formatTime = (seconds) => {
            const minutes = Math.floor(seconds / 60);
            const secs = Math.floor(seconds % 60);
            return `${minutes}:${secs.toString().padStart(2, '0')}`;
        };
        
        this.timeDisplay.textContent = `${formatTime(this.currentTime)} / ${formatTime(this.duration)}`;
    }
    
    /**
     * Updates the progress display
     */
    _updateProgress() {
        const progress = (this.currentTime / this.duration) * 100;
        this.waveformProgress.style.width = `${progress}%`;
    }
    
    /**
     * Starts or resumes playback
     */
    play() {
        this.audio.play().then(() => {
            this.isPlaying = true;
            this.playButton.innerHTML = '<i class="fas fa-pause"></i>';
            this.playButton.setAttribute('aria-label', 'Pause');
            this.visualizer.classList.add('playing');
            
            // Call callback if provided
            if (typeof this.options.onPlay === 'function') {
                this.options.onPlay();
            }
        }).catch(error => {
            console.error('Playback failed:', error);
        });
    }
    
    /**
     * Pauses playback
     */
    pause() {
        this.audio.pause();
        this.isPlaying = false;
        this.playButton.innerHTML = '<i class="fas fa-play"></i>';
        this.playButton.setAttribute('aria-label', 'Play');
        this.visualizer.classList.remove('playing');
        
        // Call callback if provided
        if (typeof this.options.onPause === 'function') {
            this.options.onPause();
        }
    }
    
    /**
     * Toggles between play and pause
     */
    togglePlayback() {
        if (this.isPlaying) {
            this.pause();
        } else {
            this.play();
        }
    }
    
    /**
     * Seeks to a specific time in the audio
     * 
     * @param {number} time - Time in seconds
     */
    seek(time) {
        this.audio.currentTime = Math.max(0, Math.min(time, this.duration));
        this._updateTimeDisplay();
        this._updateProgress();
    }
    
    /**
     * Sets the audio volume
     * 
     * @param {number} volume - Volume between 0 and 1
     */
    setVolume(volume) {
        this.volume = Math.max(0, Math.min(volume, 1));
        this.audio.volume = this.volume;
        this.volumeSlider.value = this.volume.toString();
        
        // Update volume icon
        if (this.volume === 0) {
            this.volumeIcon.className = 'fas fa-volume-mute';
        } else if (this.volume < 0.5) {
            this.volumeIcon.className = 'fas fa-volume-down';
        } else {
            this.volumeIcon.className = 'fas fa-volume-up';
        }
    }
    
    /**
     * Sets waveform data and updates the visualization
     * 
     * @param {Array<number>} data - Array of waveform amplitude values
     */
    setWaveformData(data) {
        this.waveformBars.innerHTML = '';
        
        // Normalize the data
        const maxAmplitude = Math.max(...data);
        
        // Create bars
        for (let i = 0; i < data.length; i++) {
            const bar = document.createElement('div');
            bar.className = 'waveform-bar';
            
            // Scale height based on amplitude
            const normalizedHeight = (data[i] / maxAmplitude) * 3;
            bar.style.setProperty('--rand-height', normalizedHeight.toFixed(2));
            
            this.waveformBars.appendChild(bar);
        }
    }
    
    /**
     * Destroys the visualizer and cleans up resources
     */
    destroy() {
        // Stop audio
        this.audio.pause();
        this.audio.src = '';
        
        // Remove DOM elements
        this.container.innerHTML = '';
        
        // Remove event listeners
        this.audio.removeEventListener('loadedmetadata', this._updateTimeDisplay);
        this.audio.removeEventListener('timeupdate', this._updateProgress);
        this.audio.removeEventListener('ended', this.pause);
    }
} 