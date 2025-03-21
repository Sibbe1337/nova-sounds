/**
 * YouTube Shorts Machine - Advanced Video Editor with Drag & Drop
 */

class VideoEditor {
    constructor(options = {}) {
        // Set defaults
        this.options = Object.assign({
            timelineSelector: '#timeline',
            previewSelector: '#preview',
            trackHeight: 80,
            secondWidth: 100,  // pixels per second
            maxDuration: 60,   // max duration in seconds
            snapTolerance: 10, // snap to grid tolerance in pixels
            onChange: null,    // callback when timeline changes
            onReady: null,     // callback when editor is ready
        }, options);
        
        // Initialize state
        this.tracks = [];
        this.clips = [];
        this.selectedClipId = null;
        this.draggedClipId = null;
        this.dragStartX = 0;
        this.dragStartY = 0;
        this.clipStartLeft = 0;
        this.clipStartTop = 0;
        this.isDragging = false;
        this.isResizing = false;
        this.resizeStartX = 0;
        this.resizeStartWidth = 0;
        this.resizeEdge = null;
        this.timelineWidth = 0;
        this.timelineScrollLeft = 0;
        this.currentTime = 0;
        this.isPlaying = false;
        this.playbackTimer = null;
        
        // Initialize containers
        this.timelineContainer = document.querySelector(this.options.timelineSelector);
        this.previewContainer = document.querySelector(this.options.previewSelector);
        
        if (!this.timelineContainer) {
            console.error('Timeline container not found:', this.options.timelineSelector);
            return;
        }
        
        // Initialize UI
        this.initializeTimeline();
        this.attachListeners();
        
        // Initialize default tracks
        this.createTrack({ name: 'Video', type: 'video' });
        this.createTrack({ name: 'Audio', type: 'audio' });
        this.createTrack({ name: 'Overlays', type: 'overlay' });
        
        // Notify ready
        if (typeof this.options.onReady === 'function') {
            this.options.onReady(this);
        }
    }
    
    /**
     * Initialize the timeline interface
     */
    initializeTimeline() {
        // Create timeline elements
        this.timelineContainer.innerHTML = '';
        this.timelineContainer.className = 'video-timeline';
        
        // Create tracks container
        this.tracksContainer = document.createElement('div');
        this.tracksContainer.className = 'timeline-tracks';
        this.timelineContainer.appendChild(this.tracksContainer);
        
        // Create time marker
        this.timeMarker = document.createElement('div');
        this.timeMarker.className = 'time-marker';
        this.timelineContainer.appendChild(this.timeMarker);
        
        // Create time ruler
        this.timeRuler = document.createElement('div');
        this.timeRuler.className = 'time-ruler';
        this.timelineContainer.appendChild(this.timeRuler);
        
        // Create ruler markers (1-second intervals)
        const secondMarkers = Math.ceil(this.options.maxDuration);
        this.timelineWidth = secondMarkers * this.options.secondWidth;
        
        for (let i = 0; i <= secondMarkers; i++) {
            const marker = document.createElement('div');
            marker.className = 'ruler-marker';
            marker.style.left = `${i * this.options.secondWidth}px`;
            marker.innerHTML = `<span>${this.formatTime(i)}</span>`;
            this.timeRuler.appendChild(marker);
        }
        
        // Create playback controls
        this.createPlaybackControls();
        
        // Set width
        this.tracksContainer.style.width = `${this.timelineWidth}px`;
        this.timeRuler.style.width = `${this.timelineWidth}px`;
    }
    
    /**
     * Create playback controls
     */
    createPlaybackControls() {
        const controls = document.createElement('div');
        controls.className = 'playback-controls';
        
        // Play/Pause button
        const playButton = document.createElement('button');
        playButton.className = 'btn btn-primary play-button';
        playButton.innerHTML = '<i class="fas fa-play"></i>';
        playButton.addEventListener('click', () => this.togglePlayback());
        controls.appendChild(playButton);
        this.playButton = playButton;
        
        // Stop button
        const stopButton = document.createElement('button');
        stopButton.className = 'btn btn-secondary stop-button';
        stopButton.innerHTML = '<i class="fas fa-stop"></i>';
        stopButton.addEventListener('click', () => this.stopPlayback());
        controls.appendChild(stopButton);
        
        // Time display
        const timeDisplay = document.createElement('div');
        timeDisplay.className = 'time-display';
        timeDisplay.innerHTML = '00:00.000';
        controls.appendChild(timeDisplay);
        this.timeDisplay = timeDisplay;
        
        // Append to timeline
        this.timelineContainer.parentNode.insertBefore(controls, this.timelineContainer);
    }
    
    /**
     * Attach event listeners
     */
    attachListeners() {
        // Timeline click for positioning
        this.timelineContainer.addEventListener('click', (e) => {
            if (e.target === this.timelineContainer || 
                e.target === this.tracksContainer || 
                e.target.classList.contains('track-content')) {
                const rect = this.tracksContainer.getBoundingClientRect();
                const x = e.clientX - rect.left + this.timelineScrollLeft;
                this.setCurrentTime(this.pixelsToSeconds(x));
            }
        });
        
        // Drag and scroll handling
        this.timelineContainer.addEventListener('mousedown', (e) => {
            if (e.target.classList.contains('clip')) {
                this.handleClipMouseDown(e);
            } else if (e.target.classList.contains('clip-resize-handle')) {
                this.handleResizeMouseDown(e);
            }
        });
        
        // Global mouse move and up for dragging
        document.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        document.addEventListener('mouseup', (e) => this.handleMouseUp(e));
        
        // Timeline scroll
        this.timelineContainer.addEventListener('scroll', (e) => {
            this.timelineScrollLeft = this.timelineContainer.scrollLeft;
            this.updateTimeMarker();
        });
        
        // Add clip on double-click
        this.tracksContainer.addEventListener('dblclick', (e) => {
            if (e.target.classList.contains('track-content')) {
                const trackId = e.target.parentNode.dataset.trackId;
                const track = this.getTrackById(trackId);
                
                if (track) {
                    const rect = e.target.getBoundingClientRect();
                    const x = e.clientX - rect.left + this.timelineScrollLeft;
                    const time = this.pixelsToSeconds(x);
                    
                    // Add a test clip
                    this.addClip({
                        trackId: trackId,
                        startTime: Math.max(0, time - 2), // Start 2 seconds before click point
                        duration: 4, // 4 seconds long
                        type: track.type,
                        name: `New ${track.type} clip`,
                        color: this.getRandomColor()
                    });
                }
            }
        });
        
        // Handle window resize
        window.addEventListener('resize', () => this.updateLayout());
    }
    
    /**
     * Handle mouse down on clip for dragging
     */
    handleClipMouseDown(e) {
        const clipElement = e.target;
        const clipId = clipElement.dataset.clipId;
        
        this.selectClip(clipId);
        this.draggedClipId = clipId;
        
        const rect = clipElement.getBoundingClientRect();
        this.dragStartX = e.clientX;
        this.dragStartY = e.clientY;
        this.clipStartLeft = rect.left - this.tracksContainer.getBoundingClientRect().left + this.timelineScrollLeft;
        this.clipStartTop = clipElement.offsetTop;
        
        this.isDragging = true;
        e.preventDefault();
    }
    
    /**
     * Handle mouse down on resize handle
     */
    handleResizeMouseDown(e) {
        const handleElement = e.target;
        const clipElement = handleElement.parentNode;
        const clipId = clipElement.dataset.clipId;
        
        this.selectClip(clipId);
        this.resizeStartX = e.clientX;
        this.resizeStartWidth = clipElement.offsetWidth;
        this.resizeEdge = handleElement.classList.contains('left-handle') ? 'left' : 'right';
        
        this.isResizing = true;
        e.preventDefault();
    }
    
    /**
     * Handle mouse move for dragging or resizing
     */
    handleMouseMove(e) {
        if (this.isDragging) {
            this.handleClipDrag(e);
        } else if (this.isResizing) {
            this.handleClipResize(e);
        }
    }
    
    /**
     * Handle clip dragging
     */
    handleClipDrag(e) {
        const deltaX = e.clientX - this.dragStartX;
        const deltaY = e.clientY - this.dragStartY;
        
        // Get the clip and element
        const clip = this.getClipById(this.draggedClipId);
        const clipElement = document.querySelector(`.clip[data-clip-id="${this.draggedClipId}"]`);
        
        if (!clip || !clipElement) return;
        
        // Calculate new position
        let newLeft = this.clipStartLeft + deltaX;
        
        // Snap to grid
        const snapPoints = this.getSnapPoints(clip.id);
        const seconds = this.pixelsToSeconds(newLeft);
        const snapSeconds = this.findNearestSnapPoint(seconds, snapPoints);
        
        if (snapSeconds !== null) {
            newLeft = this.secondsToPixels(snapSeconds);
        }
        
        // Ensure clip stays within bounds
        newLeft = Math.max(0, newLeft);
        if (newLeft + clipElement.offsetWidth > this.timelineWidth) {
            newLeft = this.timelineWidth - clipElement.offsetWidth;
        }
        
        clipElement.style.left = `${newLeft}px`;
        
        // Check for track change
        if (Math.abs(deltaY) > this.options.trackHeight / 2) {
            // Find track at this position
            const trackIndex = Math.floor((this.clipStartTop + deltaY) / this.options.trackHeight);
            if (trackIndex >= 0 && trackIndex < this.tracks.length) {
                const targetTrack = this.tracks[trackIndex];
                
                // Only allow moving to compatible tracks
                if (this.isTrackCompatible(clip, targetTrack)) {
                    clipElement.parentNode.removeChild(clipElement);
                    const trackElement = document.querySelector(`.track[data-track-id="${targetTrack.id}"] .track-content`);
                    trackElement.appendChild(clipElement);
                    
                    // Update clip data
                    clip.trackId = targetTrack.id;
                }
            }
        }
        
        // Update clip data
        clip.startTime = this.pixelsToSeconds(newLeft);
    }
    
    /**
     * Handle clip resizing
     */
    handleClipResize(e) {
        const deltaX = e.clientX - this.resizeStartX;
        const clip = this.getClipById(this.selectedClipId);
        const clipElement = document.querySelector(`.clip[data-clip-id="${this.selectedClipId}"]`);
        
        if (!clip || !clipElement) return;
        
        let newWidth, newLeft, newStartTime, newDuration;
        
        if (this.resizeEdge === 'right') {
            // Resizing the right edge (changing duration)
            newWidth = Math.max(50, this.resizeStartWidth + deltaX);
            newDuration = this.pixelsToSeconds(newWidth);
            
            // Apply the changes
            clipElement.style.width = `${newWidth}px`;
            clip.duration = newDuration;
        } else {
            // Resizing the left edge (changing start time and duration)
            newWidth = Math.max(50, this.resizeStartWidth - deltaX);
            newLeft = clipElement.offsetLeft + (this.resizeStartWidth - newWidth);
            
            // Ensure clip stays within bounds
            newLeft = Math.max(0, newLeft);
            
            // Calculate new times
            newStartTime = this.pixelsToSeconds(newLeft);
            newDuration = clip.duration + (clip.startTime - newStartTime);
            
            // Apply the changes
            clipElement.style.width = `${newWidth}px`;
            clipElement.style.left = `${newLeft}px`;
            clip.startTime = newStartTime;
            clip.duration = newDuration;
        }
    }
    
    /**
     * Handle mouse up to end drag or resize
     */
    handleMouseUp(e) {
        if (this.isDragging || this.isResizing) {
            // Trigger change event
            if (typeof this.options.onChange === 'function') {
                this.options.onChange(this.getTimelineData());
            }
            
            this.isDragging = false;
            this.isResizing = false;
        }
    }
    
    /**
     * Create a new track
     */
    createTrack(trackData) {
        const id = trackData.id || `track-${Date.now()}-${this.tracks.length}`;
        const track = {
            id,
            name: trackData.name || `Track ${this.tracks.length + 1}`,
            type: trackData.type || 'video',
            index: this.tracks.length
        };
        
        this.tracks.push(track);
        
        // Create track element
        const trackElement = document.createElement('div');
        trackElement.className = `track track-${track.type}`;
        trackElement.dataset.trackId = track.id;
        
        // Track label
        const trackLabel = document.createElement('div');
        trackLabel.className = 'track-label';
        trackLabel.textContent = track.name;
        trackElement.appendChild(trackLabel);
        
        // Track content
        const trackContent = document.createElement('div');
        trackContent.className = 'track-content';
        trackElement.appendChild(trackContent);
        
        // Set height
        trackElement.style.height = `${this.options.trackHeight}px`;
        
        // Add to container
        this.tracksContainer.appendChild(trackElement);
        
        return track;
    }
    
    /**
     * Add a clip to the timeline
     */
    addClip(clipData) {
        const id = clipData.id || `clip-${Date.now()}-${this.clips.length}`;
        const clip = {
            id,
            trackId: clipData.trackId,
            startTime: clipData.startTime || 0,
            duration: clipData.duration || 5,
            type: clipData.type || 'video',
            name: clipData.name || 'Untitled Clip',
            url: clipData.url || '',
            color: clipData.color || this.getRandomColor(),
            metadata: clipData.metadata || {}
        };
        
        this.clips.push(clip);
        this.renderClip(clip);
        
        // Select the new clip
        this.selectClip(clip.id);
        
        // Trigger change event
        if (typeof this.options.onChange === 'function') {
            this.options.onChange(this.getTimelineData());
        }
        
        return clip;
    }
    
    /**
     * Render a clip on the timeline
     */
    renderClip(clip) {
        const trackElement = document.querySelector(`.track[data-track-id="${clip.trackId}"] .track-content`);
        if (!trackElement) return;
        
        // Create clip element
        const clipElement = document.createElement('div');
        clipElement.className = `clip clip-${clip.type}`;
        clipElement.dataset.clipId = clip.id;
        clipElement.style.left = `${this.secondsToPixels(clip.startTime)}px`;
        clipElement.style.width = `${this.secondsToPixels(clip.duration)}px`;
        clipElement.style.backgroundColor = clip.color;
        
        // Clip content
        const clipContent = document.createElement('div');
        clipContent.className = 'clip-content';
        clipContent.textContent = clip.name;
        clipElement.appendChild(clipContent);
        
        // Resize handles
        const leftHandle = document.createElement('div');
        leftHandle.className = 'clip-resize-handle left-handle';
        clipElement.appendChild(leftHandle);
        
        const rightHandle = document.createElement('div');
        rightHandle.className = 'clip-resize-handle right-handle';
        clipElement.appendChild(rightHandle);
        
        // Add to track
        trackElement.appendChild(clipElement);
    }
    
    /**
     * Remove a clip from the timeline
     */
    removeClip(clipId) {
        const index = this.clips.findIndex(c => c.id === clipId);
        if (index === -1) return;
        
        // Remove element
        const clipElement = document.querySelector(`.clip[data-clip-id="${clipId}"]`);
        if (clipElement) {
            clipElement.parentNode.removeChild(clipElement);
        }
        
        // Remove from array
        this.clips.splice(index, 1);
        
        // Clear selection if this was the selected clip
        if (this.selectedClipId === clipId) {
            this.selectedClipId = null;
        }
        
        // Trigger change event
        if (typeof this.options.onChange === 'function') {
            this.options.onChange(this.getTimelineData());
        }
    }
    
    /**
     * Select a clip
     */
    selectClip(clipId) {
        // Deselect previous
        if (this.selectedClipId) {
            const prevElement = document.querySelector(`.clip[data-clip-id="${this.selectedClipId}"]`);
            if (prevElement) {
                prevElement.classList.remove('selected');
            }
        }
        
        // Set new selection
        this.selectedClipId = clipId;
        
        // Highlight selected
        const clipElement = document.querySelector(`.clip[data-clip-id="${clipId}"]`);
        if (clipElement) {
            clipElement.classList.add('selected');
        }
    }
    
    /**
     * Get a track by ID
     */
    getTrackById(trackId) {
        return this.tracks.find(t => t.id === trackId);
    }
    
    /**
     * Get a clip by ID
     */
    getClipById(clipId) {
        return this.clips.find(c => c.id === clipId);
    }
    
    /**
     * Check if a track is compatible with a clip
     */
    isTrackCompatible(clip, track) {
        // Simple compatibility check by type
        return clip.type === track.type;
    }
    
    /**
     * Get snap points for alignment
     */
    getSnapPoints(excludeClipId) {
        const snapPoints = [0]; // Always snap to timeline start
        
        // Add clip edges as snap points
        this.clips.forEach(clip => {
            if (clip.id !== excludeClipId) {
                snapPoints.push(clip.startTime);
                snapPoints.push(clip.startTime + clip.duration);
            }
        });
        
        // Add whole-second marks
        for (let i = 1; i <= this.options.maxDuration; i++) {
            snapPoints.push(i);
        }
        
        return snapPoints;
    }
    
    /**
     * Find nearest snap point if within tolerance
     */
    findNearestSnapPoint(time, snapPoints) {
        const toleranceSeconds = this.pixelsToSeconds(this.options.snapTolerance);
        
        let closest = null;
        let minDiff = Number.MAX_VALUE;
        
        snapPoints.forEach(snapTime => {
            const diff = Math.abs(time - snapTime);
            if (diff < toleranceSeconds && diff < minDiff) {
                minDiff = diff;
                closest = snapTime;
            }
        });
        
        return closest;
    }
    
    /**
     * Convert seconds to pixels
     */
    secondsToPixels(seconds) {
        return seconds * this.options.secondWidth;
    }
    
    /**
     * Convert pixels to seconds
     */
    pixelsToSeconds(pixels) {
        return pixels / this.options.secondWidth;
    }
    
    /**
     * Format time as MM:SS.mmm
     */
    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        const ms = Math.floor((seconds % 1) * 1000);
        
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(3, '0')}`;
    }
    
    /**
     * Set the current time position
     */
    setCurrentTime(seconds) {
        this.currentTime = Math.max(0, Math.min(seconds, this.options.maxDuration));
        this.updateTimeMarker();
        
        // Update preview
        this.updatePreview();
    }
    
    /**
     * Update the time marker position
     */
    updateTimeMarker() {
        const pixelPosition = this.secondsToPixels(this.currentTime);
        this.timeMarker.style.left = `${pixelPosition}px`;
        
        // Update time display
        if (this.timeDisplay) {
            this.timeDisplay.textContent = this.formatTime(this.currentTime);
        }
    }
    
    /**
     * Update preview display
     */
    updatePreview() {
        if (!this.previewContainer) return;
        
        // In a real implementation, this would seek the video player
        // For now, we'll just update a time display
        const previewTime = document.createElement('div');
        previewTime.textContent = `Preview: ${this.formatTime(this.currentTime)}`;
        
        this.previewContainer.innerHTML = '';
        this.previewContainer.appendChild(previewTime);
        
        // TODO: In a real implementation, this would render the current frame
        // by compositing all visible clips at the current time
    }
    
    /**
     * Toggle playback
     */
    togglePlayback() {
        if (this.isPlaying) {
            this.pausePlayback();
        } else {
            this.startPlayback();
        }
    }
    
    /**
     * Start playback
     */
    startPlayback() {
        if (this.isPlaying) return;
        
        this.isPlaying = true;
        this.updatePlayButton();
        
        const startTime = Date.now();
        const initialTime = this.currentTime;
        
        this.playbackTimer = setInterval(() => {
            const elapsedSeconds = (Date.now() - startTime) / 1000;
            const newTime = initialTime + elapsedSeconds;
            
            if (newTime >= this.options.maxDuration) {
                this.setCurrentTime(this.options.maxDuration);
                this.stopPlayback();
            } else {
                this.setCurrentTime(newTime);
            }
        }, 33); // ~30fps
    }
    
    /**
     * Pause playback
     */
    pausePlayback() {
        this.isPlaying = false;
        clearInterval(this.playbackTimer);
        this.updatePlayButton();
    }
    
    /**
     * Stop playback
     */
    stopPlayback() {
        this.isPlaying = false;
        clearInterval(this.playbackTimer);
        this.setCurrentTime(0);
        this.updatePlayButton();
    }
    
    /**
     * Update play button appearance
     */
    updatePlayButton() {
        if (!this.playButton) return;
        
        if (this.isPlaying) {
            this.playButton.innerHTML = '<i class="fas fa-pause"></i>';
        } else {
            this.playButton.innerHTML = '<i class="fas fa-play"></i>';
        }
    }
    
    /**
     * Update layout on resize
     */
    updateLayout() {
        this.updateTimeMarker();
    }
    
    /**
     * Get timeline data for saving
     */
    getTimelineData() {
        return {
            tracks: this.tracks,
            clips: this.clips,
            duration: this.options.maxDuration
        };
    }
    
    /**
     * Load timeline data
     */
    loadTimelineData(data) {
        // Clear existing
        this.tracks = [];
        this.clips = [];
        this.tracksContainer.innerHTML = '';
        
        // Load tracks
        data.tracks.forEach(trackData => this.createTrack(trackData));
        
        // Load clips
        data.clips.forEach(clipData => this.addClip(clipData));
        
        // Update timeline
        this.stopPlayback();
        this.setCurrentTime(0);
    }
    
    /**
     * Get a random color for clips
     */
    getRandomColor() {
        const colors = [
            '#3498db', '#2ecc71', '#e74c3c', '#f39c12', 
            '#9b59b6', '#1abc9c', '#d35400', '#c0392b',
            '#2980b9', '#27ae60', '#e67e22', '#8e44ad'
        ];
        return colors[Math.floor(Math.random() * colors.length)];
    }
}

// Initialize editor when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Check if editor container exists
    const editorContainer = document.getElementById('video-editor');
    if (!editorContainer) return;
    
    // Create the editor
    const editor = new VideoEditor({
        timelineSelector: '#timeline',
        previewSelector: '#preview',
        onChange: (data) => {
            console.log('Timeline changed:', data);
            // In a real app, this would save the timeline state or update the preview
        }
    });
    
    // Add test clips
    editor.addClip({
        trackId: editor.tracks[0].id,
        startTime: 1,
        duration: 5,
        type: 'video',
        name: 'Intro Clip'
    });
    
    editor.addClip({
        trackId: editor.tracks[0].id,
        startTime: 7,
        duration: 8,
        type: 'video',
        name: 'Main Content'
    });
    
    editor.addClip({
        trackId: editor.tracks[1].id,
        startTime: 0,
        duration: 15,
        type: 'audio',
        name: 'Background Music'
    });
    
    editor.addClip({
        trackId: editor.tracks[2].id,
        startTime: 3,
        duration: 4,
        type: 'overlay',
        name: 'Logo Overlay'
    });
    
    // Example of adding new track button
    const addTrackButton = document.createElement('button');
    addTrackButton.className = 'btn btn-sm btn-primary';
    addTrackButton.textContent = 'Add Track';
    addTrackButton.addEventListener('click', () => {
        const trackType = prompt('Enter track type (video, audio, overlay):', 'video');
        if (trackType) {
            editor.createTrack({
                name: `${trackType.charAt(0).toUpperCase() + trackType.slice(1)} Track`,
                type: trackType.toLowerCase()
            });
        }
    });
    
    // Add delete clip button
    const deleteClipButton = document.createElement('button');
    deleteClipButton.className = 'btn btn-sm btn-danger';
    deleteClipButton.textContent = 'Delete Selected Clip';
    deleteClipButton.addEventListener('click', () => {
        if (editor.selectedClipId) {
            editor.removeClip(editor.selectedClipId);
        } else {
            alert('Please select a clip first');
        }
    });
    
    // Add buttons to container
    const controlsContainer = document.createElement('div');
    controlsContainer.className = 'editor-controls';
    controlsContainer.appendChild(addTrackButton);
    controlsContainer.appendChild(deleteClipButton);
    editorContainer.insertBefore(controlsContainer, editorContainer.firstChild);
}); 