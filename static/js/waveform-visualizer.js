/**
 * Waveform Visualizer
 * 
 * A JavaScript module for visualizing audio waveforms based on amplitude data.
 * Supports multiple visualization styles and interactive features.
 */

class WaveformVisualizer {
    /**
     * Create a new waveform visualizer
     * @param {string} containerId - ID of the container element
     * @param {Object} options - Configuration options
     */
    constructor(containerId, options = {}) {
        // Store container reference
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`Container with ID "${containerId}" not found`);
            return;
        }
        
        // Default options
        this.options = {
            width: this.container.clientWidth || 600,
            height: 100,
            barWidth: 3,
            barSpacing: 1,
            barColor: '#3b82f6', // Blue
            barGradient: true,
            gradientColors: ['#60a5fa', '#3b82f6', '#1d4ed8'],
            backgroundColor: 'transparent',
            responsive: true,
            showPlayhead: true,
            playheadColor: '#ef4444', // Red
            playheadWidth: 2,
            interactionEnabled: true,
            ...options
        };
        
        // Initialize state
        this.amplitudeData = [];
        this.isPlaying = false;
        this.playbackProgress = 0;
        this.progressInterval = null;
        
        // Create canvas
        this.createCanvas();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Initial render
        this.render();
    }
    
    /**
     * Create the canvas element
     */
    createCanvas() {
        // Create canvas element
        this.canvas = document.createElement('canvas');
        this.canvas.width = this.options.width;
        this.canvas.height = this.options.height;
        this.canvas.className = 'waveform-canvas';
        
        // Add canvas to container
        this.container.appendChild(this.canvas);
        
        // Get drawing context
        this.ctx = this.canvas.getContext('2d');
        
        // Handle responsive layout
        if (this.options.responsive) {
            this.setupResponsive();
        }
    }
    
    /**
     * Set up responsive behavior
     */
    setupResponsive() {
        window.addEventListener('resize', () => {
            // Update canvas dimensions based on container
            const newWidth = this.container.clientWidth;
            if (newWidth !== this.canvas.width) {
                this.canvas.width = newWidth;
                this.options.width = newWidth;
                this.render();
            }
        });
    }
    
    /**
     * Set up event listeners for interaction
     */
    setupEventListeners() {
        if (!this.options.interactionEnabled) return;
        
        // Click to seek
        this.canvas.addEventListener('click', (e) => {
            if (!this.amplitudeData.length) return;
            
            const rect = this.canvas.getBoundingClientRect();
            const clickX = e.clientX - rect.left;
            const progress = clickX / this.canvas.width;
            
            // Update playback progress
            this.setProgress(progress);
            
            // Emit seek event
            this.emitEvent('seek', { progress });
        });
    }
    
    /**
     * Set waveform data from API
     * @param {string} trackName - Name of the track
     * @param {number} points - Number of points to request (default: calculated based on canvas width)
     */
    async loadFromAPI(trackName, points = null) {
        // Calculate optimal number of points if not provided
        if (!points) {
            // Use 2x the visible width for smooth rendering
            points = Math.round(this.canvas.width / (this.options.barWidth + this.options.barSpacing) * 2);
        }
        
        try {
            const response = await fetch(`/api/music/waveform/${encodeURIComponent(trackName)}?points=${points}`);
            if (!response.ok) {
                throw new Error(`Failed to load waveform: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.setAmplitudeData(data.points);
            
            return data;
        } catch (error) {
            console.error('Error loading waveform data:', error);
            // Set empty data
            this.setAmplitudeData([]);
            throw error;
        }
    }
    
    /**
     * Set amplitude data directly
     * @param {Array} data - Array of amplitude values (0-1)
     */
    setAmplitudeData(data) {
        this.amplitudeData = data;
        this.render();
    }
    
    /**
     * Start playback simulation
     * @param {number} duration - Duration in seconds
     */
    startPlayback(duration = 30) {
        if (this.isPlaying) return;
        
        this.isPlaying = true;
        
        // Clear any existing interval
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
        }
        
        // Update progress at 30fps
        const updateFrequency = 1000 / 30; // ~33ms
        const progressIncrement = updateFrequency / (duration * 1000);
        
        this.progressInterval = setInterval(() => {
            this.playbackProgress += progressIncrement;
            
            // Loop back to start when reaching the end
            if (this.playbackProgress >= 1) {
                if (this.options.loop) {
                    this.playbackProgress = 0;
                } else {
                    this.stopPlayback();
                    this.emitEvent('ended');
                    return;
                }
            }
            
            this.render();
            this.emitEvent('timeupdate', { 
                progress: this.playbackProgress,
                currentTime: this.playbackProgress * duration
            });
        }, updateFrequency);
        
        this.emitEvent('play');
    }
    
    /**
     * Stop playback simulation
     */
    stopPlayback() {
        this.isPlaying = false;
        
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
        
        this.emitEvent('pause');
    }
    
    /**
     * Toggle playback
     * @param {number} duration - Duration in seconds (for playback)
     */
    togglePlayback(duration = 30) {
        if (this.isPlaying) {
            this.stopPlayback();
        } else {
            this.startPlayback(duration);
        }
    }
    
    /**
     * Set the playback progress
     * @param {number} progress - Progress value from 0 to 1
     */
    setProgress(progress) {
        this.playbackProgress = Math.min(Math.max(progress, 0), 1);
        this.render();
    }
    
    /**
     * Render the waveform
     */
    render() {
        if (!this.ctx) return;
        
        const { width, height } = this.canvas;
        const { barWidth, barSpacing, backgroundColor } = this.options;
        
        // Clear canvas
        this.ctx.fillStyle = backgroundColor;
        this.ctx.fillRect(0, 0, width, height);
        
        // Calculate total width of bars and spacing
        const totalBarWidth = barWidth + barSpacing;
        
        // If no data, render empty waveform
        if (!this.amplitudeData.length) {
            this.renderEmptyWaveform();
            return;
        }
        
        // Set up gradient if enabled
        let gradient = null;
        if (this.options.barGradient) {
            gradient = this.ctx.createLinearGradient(0, height, 0, 0);
            const colors = this.options.gradientColors;
            
            // Add color stops
            for (let i = 0; i < colors.length; i++) {
                gradient.addColorStop(i / (colors.length - 1), colors[i]);
            }
        }
        
        // Determine how many bars to show based on available width
        const maxBars = Math.floor(width / totalBarWidth);
        const step = this.amplitudeData.length / maxBars;
        
        // Draw bars
        for (let i = 0; i < maxBars; i++) {
            // Get amplitude from data, or use 0 if out of bounds
            const dataIndex = Math.min(Math.floor(i * step), this.amplitudeData.length - 1);
            const amplitude = this.amplitudeData[dataIndex] || 0;
            
            // Calculate bar height (minimum 1px)
            const barHeight = Math.max(amplitude * height, 1);
            
            // Calculate bar position
            const x = i * totalBarWidth;
            const y = (height - barHeight) / 2;
            
            // Set bar color
            this.ctx.fillStyle = gradient || this.options.barColor;
            
            // Draw bar
            this.ctx.fillRect(x, y, barWidth, barHeight);
        }
        
        // Draw playhead if enabled and playing
        if (this.options.showPlayhead) {
            this.drawPlayhead();
        }
    }
    
    /**
     * Render an empty waveform (placeholder)
     */
    renderEmptyWaveform() {
        const { width, height } = this.canvas;
        
        // Draw a flat line in the middle
        this.ctx.beginPath();
        this.ctx.moveTo(0, height / 2);
        this.ctx.lineTo(width, height / 2);
        this.ctx.strokeStyle = this.options.barColor;
        this.ctx.lineWidth = 1;
        this.ctx.stroke();
    }
    
    /**
     * Draw the playhead at the current position
     */
    drawPlayhead() {
        const { width, height } = this.canvas;
        const x = width * this.playbackProgress;
        
        // Draw vertical line
        this.ctx.beginPath();
        this.ctx.moveTo(x, 0);
        this.ctx.lineTo(x, height);
        this.ctx.strokeStyle = this.options.playheadColor;
        this.ctx.lineWidth = this.options.playheadWidth;
        this.ctx.stroke();
    }
    
    /**
     * Emit a custom event
     * @param {string} eventName - Name of the event
     * @param {Object} detail - Event details
     */
    emitEvent(eventName, detail = {}) {
        const event = new CustomEvent(`waveform:${eventName}`, {
            bubbles: true,
            detail: {
                waveform: this,
                ...detail
            }
        });
        
        this.container.dispatchEvent(event);
    }
    
    /**
     * Add event listener for waveform events
     * @param {string} eventName - Name of the event (without 'waveform:' prefix)
     * @param {Function} callback - Event callback
     */
    on(eventName, callback) {
        this.container.addEventListener(`waveform:${eventName}`, callback);
    }
    
    /**
     * Remove event listener
     * @param {string} eventName - Name of the event (without 'waveform:' prefix)
     * @param {Function} callback - Event callback
     */
    off(eventName, callback) {
        this.container.removeEventListener(`waveform:${eventName}`, callback);
    }
    
    /**
     * Update visualizer options
     * @param {Object} newOptions - New options to apply
     */
    updateOptions(newOptions) {
        this.options = {
            ...this.options,
            ...newOptions
        };
        
        this.render();
    }
    
    /**
     * Destroy the visualizer and clean up
     */
    destroy() {
        // Stop playback if active
        if (this.isPlaying) {
            this.stopPlayback();
        }
        
        // Remove event listeners
        window.removeEventListener('resize', this.resizeHandler);
        
        // Remove canvas
        if (this.canvas && this.canvas.parentNode) {
            this.canvas.parentNode.removeChild(this.canvas);
        }
        
        // Clear references
        this.canvas = null;
        this.ctx = null;
        this.container = null;
    }
}

// Export the class
window.WaveformVisualizer = WaveformVisualizer; 