/**
 * Waveform Audio Player Component
 * Provides a waveform visualization for audio playback with interactive timeline
 */
class WaveformPlayer {
    /**
     * Initialize the waveform player
     * @param {Object} options - Configuration options
     * @param {string} options.containerId - ID of the container element
     * @param {string} options.audioId - ID of the audio element
     * @param {string} options.trackId - ID of the track to play
     * @param {string} options.apiEndpoint - API endpoint for waveform data
     */
    constructor(options) {
        // Default options
        this.options = Object.assign({
            containerId: 'waveform-container',
            audioId: 'audio-player',
            trackId: null,
            apiEndpoint: '/music',
            waveformResolution: 1000,
            waveformColor: '#1DB954',
            backgroundColor: 'rgba(200, 200, 200, 0.2)',
            progressColor: '#1DB954'
        }, options);
        
        // Element references
        this.container = document.getElementById(this.options.containerId);
        this.audio = document.getElementById(this.options.audioId);
        
        if (!this.container || !this.audio) {
            console.error('Waveform player: container or audio element not found');
            return;
        }
        
        // Create waveform canvas
        this.createCanvases();
        
        // Bind events
        this.bindEvents();
        
        // Load track if provided
        if (this.options.trackId) {
            this.loadTrack(this.options.trackId);
        }
    }
    
    /**
     * Create canvas elements for waveform rendering
     */
    createCanvases() {
        // Clear container
        this.container.innerHTML = '';
        
        // Create main canvas
        this.canvas = document.createElement('canvas');
        this.canvas.className = 'waveform-background';
        this.container.appendChild(this.canvas);
        
        // Create progress overlay canvas
        this.progressCanvas = document.createElement('canvas');
        this.progressCanvas.className = 'waveform-progress';
        this.container.appendChild(this.progressCanvas);
        
        // Create time markers (track current time and duration)
        this.timeContainer = document.createElement('div');
        this.timeContainer.className = 'waveform-time';
        
        this.currentTimeEl = document.createElement('span');
        this.currentTimeEl.className = 'current-time';
        this.currentTimeEl.textContent = '0:00';
        
        this.durationEl = document.createElement('span');
        this.durationEl.className = 'duration';
        this.durationEl.textContent = '0:00';
        
        this.timeContainer.appendChild(this.currentTimeEl);
        this.timeContainer.appendChild(document.createTextNode(' / '));
        this.timeContainer.appendChild(this.durationEl);
        
        this.container.appendChild(this.timeContainer);
        
        // Set context
        this.ctx = this.canvas.getContext('2d');
        this.progressCtx = this.progressCanvas.getContext('2d');
        
        // Resize canvases
        this.resizeCanvases();
    }
    
    /**
     * Resize canvases to match container dimensions
     */
    resizeCanvases() {
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        
        this.canvas.width = width;
        this.canvas.height = height;
        
        this.progressCanvas.width = width;
        this.progressCanvas.height = height;
        
        // Redraw if waveform data exists
        if (this.waveformData) {
            this.drawWaveform();
            this.updateProgress();
        }
    }
    
    /**
     * Bind event listeners
     */
    bindEvents() {
        // Seek when clicking on waveform
        this.container.addEventListener('click', this.handleClick.bind(this));
        
        // Update progress during playback
        this.audio.addEventListener('timeupdate', this.updateProgress.bind(this));
        
        // Update duration when metadata is loaded
        this.audio.addEventListener('loadedmetadata', () => {
            this.durationEl.textContent = this.formatTime(this.audio.duration);
        });
        
        // Handle window resize
        window.addEventListener('resize', this.resizeCanvases.bind(this));
    }
    
    /**
     * Handle click on waveform to seek
     * @param {Event} e - Click event
     */
    handleClick(e) {
        const rect = this.container.getBoundingClientRect();
        const clickPosition = (e.clientX - rect.left) / rect.width;
        
        // Set audio position
        if (this.audio.duration) {
            this.audio.currentTime = clickPosition * this.audio.duration;
        }
    }
    
    /**
     * Update progress visualization
     */
    updateProgress() {
        if (!this.audio.duration) return;
        
        const progress = this.audio.currentTime / this.audio.duration;
        const width = this.progressCanvas.width;
        const height = this.progressCanvas.height;
        
        // Clear progress canvas
        this.progressCtx.clearRect(0, 0, width, height);
        
        // Only draw if we have data and progress
        if (this.waveformData && progress > 0) {
            // Calculate progress width
            const progressWidth = Math.floor(width * progress);
            
            // Draw progress waveform
            this.progressCtx.fillStyle = this.options.progressColor;
            
            for (let i = 0; i < this.waveformData.length; i++) {
                const x = i * (width / this.waveformData.length);
                
                // Only draw progress up to current position
                if (x > progressWidth) break;
                
                const barWidth = width / this.waveformData.length;
                const amplitude = this.waveformData[i] * height * 0.8;
                const y = (height / 2) - (amplitude / 2);
                
                this.progressCtx.fillRect(x, y, barWidth - 1, amplitude);
            }
        }
        
        // Update time display
        this.currentTimeEl.textContent = this.formatTime(this.audio.currentTime);
    }
    
    /**
     * Format time in MM:SS format
     * @param {number} seconds - Time in seconds
     * @returns {string} Formatted time
     */
    formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
    
    /**
     * Load track data and waveform
     * @param {string} trackId - Track ID
     */
    loadTrack(trackId) {
        this.options.trackId = trackId;
        
        // Fetch waveform data
        fetch(`${this.options.apiEndpoint}/${trackId}/waveform`)
            .then(response => response.json())
            .then(data => {
                this.waveformData = data;
                this.drawWaveform();
            })
            .catch(error => {
                console.error('Error loading waveform data:', error);
                // Generate dummy waveform if no data available
                this.generateDummyWaveform();
            });
            
        // Fetch track metadata
        fetch(`${this.options.apiEndpoint}/${trackId}/metadata`)
            .then(response => response.json())
            .then(metadata => {
                // Update audio source if URL is available
                if (metadata.url) {
                    this.audio.src = metadata.url;
                    this.audio.load();
                }
            })
            .catch(error => {
                console.error('Error loading track metadata:', error);
            });
    }
    
    /**
     * Draw waveform visualization
     */
    drawWaveform() {
        if (!this.waveformData) return;
        
        const width = this.canvas.width;
        const height = this.canvas.height;
        
        // Clear canvas
        this.ctx.clearRect(0, 0, width, height);
        
        // Draw background waveform
        this.ctx.fillStyle = this.options.backgroundColor;
        
        for (let i = 0; i < this.waveformData.length; i++) {
            const x = i * (width / this.waveformData.length);
            const barWidth = width / this.waveformData.length;
            const amplitude = this.waveformData[i] * height * 0.8;
            const y = (height / 2) - (amplitude / 2);
            
            this.ctx.fillRect(x, y, barWidth - 1, amplitude);
        }
        
        // Update progress display
        this.updateProgress();
    }
    
    /**
     * Generate a dummy waveform if no data is available
     */
    generateDummyWaveform() {
        const resolution = this.options.waveformResolution;
        this.waveformData = [];
        
        // Create a simple sine wave
        for (let i = 0; i < resolution; i++) {
            const value = 0.3 + 0.2 * Math.sin(i / resolution * Math.PI * 10);
            this.waveformData.push(value);
        }
        
        this.drawWaveform();
    }
}

// Auto-initialize waveform players when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Find all elements with data-waveform-player attribute
    const waveformElements = document.querySelectorAll('[data-waveform-player]');
    
    waveformElements.forEach(element => {
        const containerId = element.id;
        const audioId = element.dataset.audioPlayer;
        const trackId = element.dataset.trackId;
        const apiEndpoint = element.dataset.apiEndpoint || '/music';
        
        if (containerId && audioId) {
            new WaveformPlayer({
                containerId,
                audioId,
                trackId,
                apiEndpoint
            });
        }
    });
}); 