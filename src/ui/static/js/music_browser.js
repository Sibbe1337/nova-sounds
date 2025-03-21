// Music Browser Component
// Handles fetching, filtering and displaying music tracks

class MusicBrowser {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.selectedTrack = null;
        this.tracks = [];
        this.filteredTracks = [];
        this.audioPlayer = new Audio();
        this.currentlyPlaying = null;
        
        // Default options
        this.options = {
            onSelectTrack: null,
            initialGenre: null,
            initialMood: null,
            initialBpm: null,
            maxItems: 20,
            showWaveform: true,
            showLicensing: true,
            enablePlayback: true,
            ...options
        };
        
        // Filter state
        this.filters = {
            genre: this.options.initialGenre,
            mood: this.options.initialMood,
            minBpm: this.options.initialBpm ? this.options.initialBpm[0] : null,
            maxBpm: this.options.initialBpm ? this.options.initialBpm[1] : null,
            searchTerm: '',
            licenseType: null
        };
        
        // Initialize UI
        this.initialize();
        
        // Bind event handlers
        this.handlePlayPause = this.handlePlayPause.bind(this);
        this.handleTrackSelect = this.handleTrackSelect.bind(this);
        this.handleFilterChange = this.handleFilterChange.bind(this);
        this.audioPlayer.addEventListener('ended', () => {
            this.currentlyPlaying = null;
            this.updatePlaybackUI();
        });
    }
    
    async initialize() {
        if (!this.container) {
            console.error(`Container element with ID "${this.containerId}" not found`);
            return;
        }
        
        // Create filter UI
        this.createFilterUI();
        
        // Create tracks container
        this.tracksContainer = document.createElement('div');
        this.tracksContainer.className = 'music-tracks-container mt-3';
        this.container.appendChild(this.tracksContainer);
        
        // Initial loading message
        this.tracksContainer.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading tracks...</span>
                </div>
                <p class="mt-2">Loading music tracks...</p>
            </div>
        `;
        
        // Load tracks
        await this.loadTracks();
    }
    
    createFilterUI() {
        const filterContainer = document.createElement('div');
        filterContainer.className = 'music-filter-container bg-light p-3 rounded mb-3';
        
        filterContainer.innerHTML = `
            <div class="row g-3 align-items-end">
                <div class="col-md-4">
                    <label for="music-search" class="form-label">Search</label>
                    <div class="input-group">
                        <input type="text" class="form-control" id="music-search" placeholder="Search tracks..." aria-label="Search tracks">
                        <button class="btn btn-outline-secondary" type="button" id="clear-search">
                            <i class="bi bi-x-circle"></i>
                        </button>
                    </div>
                </div>
                <div class="col-md-2">
                    <label for="genre-filter" class="form-label">Genre</label>
                    <select class="form-select" id="genre-filter">
                        <option value="">All Genres</option>
                    </select>
                </div>
                <div class="col-md-2">
                    <label for="mood-filter" class="form-label">Mood</label>
                    <select class="form-select" id="mood-filter">
                        <option value="">All Moods</option>
                    </select>
                </div>
                <div class="col-md-2">
                    <label for="bpm-range" class="form-label">BPM Range</label>
                    <div class="input-group">
                        <input type="number" class="form-control" id="min-bpm" placeholder="Min" min="40" max="200">
                        <span class="input-group-text">-</span>
                        <input type="number" class="form-control" id="max-bpm" placeholder="Max" min="40" max="200">
                    </div>
                </div>
                <div class="col-md-2">
                    <label for="license-filter" class="form-label">License</label>
                    <select class="form-select" id="license-filter">
                        <option value="">All Licenses</option>
                        <option value="royalty-free">Royalty Free</option>
                        <option value="premium">Premium</option>
                        <option value="creative-commons">Creative Commons</option>
                    </select>
                </div>
            </div>
            <div class="d-flex justify-content-end mt-3">
                <button id="reset-filters" class="btn btn-outline-secondary me-2">
                    <i class="bi bi-arrow-counterclockwise"></i> Reset Filters
                </button>
                <button id="apply-filters" class="btn btn-primary">
                    <i class="bi bi-filter"></i> Apply Filters
                </button>
            </div>
        `;
        
        this.container.appendChild(filterContainer);
        
        // Set up event listeners for filters
        this.searchInput = filterContainer.querySelector('#music-search');
        this.genreSelect = filterContainer.querySelector('#genre-filter');
        this.moodSelect = filterContainer.querySelector('#mood-filter');
        this.minBpmInput = filterContainer.querySelector('#min-bpm');
        this.maxBpmInput = filterContainer.querySelector('#max-bpm');
        this.licenseSelect = filterContainer.querySelector('#license-filter');
        
        // Bind event listeners
        this.searchInput.addEventListener('input', this.handleFilterChange);
        this.genreSelect.addEventListener('change', this.handleFilterChange);
        this.moodSelect.addEventListener('change', this.handleFilterChange);
        this.minBpmInput.addEventListener('input', this.handleFilterChange);
        this.maxBpmInput.addEventListener('input', this.handleFilterChange);
        this.licenseSelect.addEventListener('change', this.handleFilterChange);
        
        filterContainer.querySelector('#reset-filters').addEventListener('click', () => this.resetFilters());
        filterContainer.querySelector('#apply-filters').addEventListener('click', () => this.applyFilters());
        filterContainer.querySelector('#clear-search').addEventListener('click', () => {
            this.searchInput.value = '';
            this.handleFilterChange();
        });
    }
    
    async loadTracks() {
        try {
            // Fetch tracks from API
            const response = await fetch('/api/music-tracks');
            if (!response.ok) throw new Error('Failed to load music tracks');
            
            const data = await response.json();
            this.tracks = data.tracks || [];
            
            // Populate filter options
            this.populateFilterOptions();
            
            // Initial filter application
            this.applyFilters();
        } catch (error) {
            console.error('Error loading tracks:', error);
            this.tracksContainer.innerHTML = `
                <div class="alert alert-danger" role="alert">
                    <i class="bi bi-exclamation-triangle-fill"></i> Failed to load music tracks.
                    <button class="btn btn-sm btn-outline-danger ms-2" onclick="this.loadTracks()">Retry</button>
                </div>
            `;
        }
    }
    
    populateFilterOptions() {
        // Extract unique values for filters
        const genres = [...new Set(this.tracks.map(track => track.genre))];
        const moods = [...new Set(this.tracks.map(track => track.mood))];
        const licenses = [...new Set(this.tracks.map(track => track.licenseType))];
        
        // Populate genre options
        genres.forEach(genre => {
            if (genre) {
                const option = document.createElement('option');
                option.value = genre;
                option.textContent = genre;
                this.genreSelect.appendChild(option);
            }
        });
        
        // Populate mood options
        moods.forEach(mood => {
            if (mood) {
                const option = document.createElement('option');
                option.value = mood;
                option.textContent = mood;
                this.moodSelect.appendChild(option);
            }
        });
        
        // Populate license options if not already defined in HTML
        if (licenses.length > 0 && this.licenseSelect.querySelectorAll('option').length <= 1) {
            licenses.forEach(license => {
                if (license) {
                    const option = document.createElement('option');
                    option.value = license;
                    option.textContent = license;
                    this.licenseSelect.appendChild(option);
                }
            });
        }
        
        // Set initial values if provided
        if (this.filters.genre) this.genreSelect.value = this.filters.genre;
        if (this.filters.mood) this.moodSelect.value = this.filters.mood;
        if (this.filters.minBpm) this.minBpmInput.value = this.filters.minBpm;
        if (this.filters.maxBpm) this.maxBpmInput.value = this.filters.maxBpm;
    }
    
    handleFilterChange(event) {
        // Update filter values from inputs
        this.filters.searchTerm = this.searchInput.value.trim().toLowerCase();
        this.filters.genre = this.genreSelect.value;
        this.filters.mood = this.moodSelect.value;
        this.filters.minBpm = this.minBpmInput.value ? parseInt(this.minBpmInput.value) : null;
        this.filters.maxBpm = this.maxBpmInput.value ? parseInt(this.maxBpmInput.value) : null;
        this.filters.licenseType = this.licenseSelect.value;
    }
    
    resetFilters() {
        // Reset all filter inputs
        this.searchInput.value = '';
        this.genreSelect.value = '';
        this.moodSelect.value = '';
        this.minBpmInput.value = '';
        this.maxBpmInput.value = '';
        this.licenseSelect.value = '';
        
        // Reset filter state
        this.filters = {
            genre: null,
            mood: null,
            minBpm: null,
            maxBpm: null,
            searchTerm: '',
            licenseType: null
        };
        
        // Apply filters
        this.applyFilters();
    }
    
    applyFilters() {
        // Apply current filters to tracks
        this.filteredTracks = this.tracks.filter(track => {
            // Search term filter (title, artist, description)
            if (this.filters.searchTerm) {
                const searchable = `${track.title} ${track.artist} ${track.description || ''}`.toLowerCase();
                if (!searchable.includes(this.filters.searchTerm)) return false;
            }
            
            // Genre filter
            if (this.filters.genre && track.genre !== this.filters.genre) return false;
            
            // Mood filter
            if (this.filters.mood && track.mood !== this.filters.mood) return false;
            
            // BPM range filter
            if (this.filters.minBpm && track.bpm < this.filters.minBpm) return false;
            if (this.filters.maxBpm && track.bpm > this.filters.maxBpm) return false;
            
            // License filter
            if (this.filters.licenseType && track.licenseType !== this.filters.licenseType) return false;
            
            return true;
        });
        
        // Limit to max items if specified
        if (this.options.maxItems > 0) {
            this.filteredTracks = this.filteredTracks.slice(0, this.options.maxItems);
        }
        
        // Render filtered tracks
        this.renderTracks();
    }
    
    renderTracks() {
        if (this.filteredTracks.length === 0) {
            this.tracksContainer.innerHTML = `
                <div class="alert alert-info" role="alert">
                    <i class="bi bi-info-circle-fill"></i> No tracks match your filters.
                </div>
            `;
            return;
        }
        
        // Create track list
        const tracksList = document.createElement('div');
        tracksList.className = 'music-tracks-list';
        
        this.filteredTracks.forEach(track => {
            const trackCard = document.createElement('div');
            trackCard.className = 'track-card p-3 mb-3 border rounded';
            trackCard.dataset.trackId = track.id;
            
            if (this.selectedTrack && this.selectedTrack.id === track.id) {
                trackCard.classList.add('selected');
            }
            
            const isPlaying = this.currentlyPlaying === track.id;
            
            // Create HTML for track
            trackCard.innerHTML = `
                <div class="row align-items-center">
                    <div class="col-md-7">
                        <div class="d-flex align-items-center">
                            <button class="btn btn-play-pause me-3 ${isPlaying ? 'playing' : ''}" data-track-id="${track.id}" aria-label="${isPlaying ? 'Pause' : 'Play'} ${track.title}">
                                <i class="bi ${isPlaying ? 'bi-pause-fill' : 'bi-play-fill'}"></i>
                            </button>
                            <div>
                                <h5 class="track-title mb-0">${track.title}</h5>
                                <div class="track-artist text-muted">${track.artist}</div>
                                <div class="track-meta text-muted small">
                                    <span class="me-2">${track.bpm} BPM</span>
                                    <span class="me-2">${track.duration}</span>
                                    <span class="badge ${this.getLicenseClass(track.licenseType)}">${track.licenseType}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        ${this.options.showWaveform ? `
                        <div class="track-waveform" id="waveform-${track.id}">
                            <img src="${track.waveformUrl || this.generateWaveformPlaceholder(track.id)}" 
                                 alt="Audio waveform for ${track.title}" 
                                 class="img-fluid" 
                                 width="100%" 
                                 loading="lazy">
                        </div>
                        ` : ''}
                    </div>
                    <div class="col-md-1">
                        <button class="btn btn-sm btn-outline-primary btn-select-track" data-track-id="${track.id}">
                            ${this.selectedTrack && this.selectedTrack.id === track.id ? 
                                '<i class="bi bi-check2-circle"></i> Selected' : 
                                '<i class="bi bi-check-circle"></i> Select'}
                        </button>
                    </div>
                </div>
                ${this.options.showLicensing && track.licenseDetails ? `
                <div class="track-license-details mt-2 small">
                    <button class="btn btn-sm btn-link p-0" type="button" data-bs-toggle="collapse" 
                            data-bs-target="#license-${track.id}" aria-expanded="false" 
                            aria-controls="license-${track.id}">
                        License Details <i class="bi bi-chevron-down"></i>
                    </button>
                    <div class="collapse" id="license-${track.id}">
                        <div class="card card-body mt-2 bg-light">
                            <p class="mb-1"><strong>License:</strong> ${track.licenseType}</p>
                            <p class="mb-1"><strong>Usage:</strong> ${track.licenseDetails.usage}</p>
                            <p class="mb-0"><small>${track.licenseDetails.terms}</small></p>
                        </div>
                    </div>
                </div>
                ` : ''}
            `;
            
            tracksList.appendChild(trackCard);
        });
        
        // Replace current tracks container content
        this.tracksContainer.innerHTML = '';
        this.tracksContainer.appendChild(tracksList);
        
        // Add event listeners
        this.tracksContainer.querySelectorAll('.btn-play-pause').forEach(button => {
            button.addEventListener('click', this.handlePlayPause);
        });
        
        this.tracksContainer.querySelectorAll('.btn-select-track').forEach(button => {
            button.addEventListener('click', this.handleTrackSelect);
        });
    }
    
    getLicenseClass(licenseType) {
        switch (licenseType && licenseType.toLowerCase()) {
            case 'royalty-free': return 'bg-success';
            case 'premium': return 'bg-primary';
            case 'creative-commons': return 'bg-info';
            default: return 'bg-secondary';
        }
    }
    
    generateWaveformPlaceholder(trackId) {
        // This would be replaced with actual waveform URL from backend
        // For now return a placeholder SVG
        const colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'];
        const color = colors[trackId.charCodeAt(0) % colors.length];
        
        return `data:image/svg+xml;charset=UTF-8,<svg xmlns="http://www.w3.org/2000/svg" width="800" height="100" viewBox="0 0 800 100">
            <rect width="800" height="100" fill="white" />
            <path d="M0,50 Q20,30 40,50 T80,50 T120,50 T160,50 T200,50 T240,50 T280,50 T320,50 T360,50 T400,50 T440,50 T480,50 T520,50 T560,50 T600,50 T640,50 T680,50 T720,50 T760,50 T800,50" stroke="${color}" stroke-width="2" fill="none" />
            <path d="M0,50 Q20,70 40,50 T80,50 T120,50 T160,50 T200,50 T240,50 T280,50 T320,50 T360,50 T400,50 T440,50 T480,50 T520,50 T560,50 T600,50 T640,50 T680,50 T720,50 T760,50 T800,50" stroke="${color}" stroke-width="2" fill="none" />
        </svg>`;
    }
    
    handlePlayPause(event) {
        const button = event.currentTarget;
        const trackId = button.dataset.trackId;
        const track = this.tracks.find(t => t.id === trackId);
        
        if (!track || !track.audioUrl) {
            console.error('Track or audio URL not found');
            return;
        }
        
        if (this.currentlyPlaying === trackId) {
            // Pause current track
            this.audioPlayer.pause();
            this.currentlyPlaying = null;
        } else {
            // Stop any currently playing track
            if (this.currentlyPlaying) {
                this.audioPlayer.pause();
            }
            
            // Play new track
            this.audioPlayer.src = track.audioUrl;
            this.audioPlayer.play().catch(error => {
                console.error('Error playing audio:', error);
            });
            this.currentlyPlaying = trackId;
        }
        
        // Update UI
        this.updatePlaybackUI();
    }
    
    updatePlaybackUI() {
        // Update all play/pause buttons
        this.tracksContainer.querySelectorAll('.btn-play-pause').forEach(button => {
            const isPlaying = this.currentlyPlaying === button.dataset.trackId;
            button.classList.toggle('playing', isPlaying);
            button.setAttribute('aria-label', `${isPlaying ? 'Pause' : 'Play'} track`);
            
            const icon = button.querySelector('i');
            icon.classList.remove('bi-play-fill', 'bi-pause-fill');
            icon.classList.add(isPlaying ? 'bi-pause-fill' : 'bi-play-fill');
        });
    }
    
    handleTrackSelect(event) {
        const button = event.currentTarget;
        const trackId = button.dataset.trackId;
        const track = this.tracks.find(t => t.id === trackId);
        
        if (!track) {
            console.error('Track not found');
            return;
        }
        
        // Update selected track
        this.selectedTrack = track;
        
        // Update UI
        this.tracksContainer.querySelectorAll('.track-card').forEach(card => {
            card.classList.toggle('selected', card.dataset.trackId === trackId);
        });
        
        this.tracksContainer.querySelectorAll('.btn-select-track').forEach(btn => {
            const isSelected = btn.dataset.trackId === trackId;
            btn.innerHTML = isSelected ? 
                '<i class="bi bi-check2-circle"></i> Selected' : 
                '<i class="bi bi-check-circle"></i> Select';
            
            if (isSelected) {
                btn.classList.remove('btn-outline-primary');
                btn.classList.add('btn-primary');
            } else {
                btn.classList.add('btn-outline-primary');
                btn.classList.remove('btn-primary');
            }
        });
        
        // Trigger callback if provided
        if (typeof this.options.onSelectTrack === 'function') {
            this.options.onSelectTrack(track);
        }
    }
    
    // Public methods
    getSelectedTrack() {
        return this.selectedTrack;
    }
    
    setSelectedTrack(trackId) {
        if (!trackId) {
            this.selectedTrack = null;
            // Update UI
            this.renderTracks();
            return;
        }
        
        const track = this.tracks.find(t => t.id === trackId);
        if (track) {
            this.selectedTrack = track;
            // Update UI
            this.renderTracks();
            
            // Trigger callback if provided
            if (typeof this.options.onSelectTrack === 'function') {
                this.options.onSelectTrack(track);
            }
        }
    }
    
    refresh() {
        this.loadTracks();
    }
}

// Export the class for use in other modules
window.MusicBrowser = MusicBrowser; 