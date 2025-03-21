// Video Style Preset Selector
// Displays visual tiles for selecting video styles

class StylePresetSelector {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.selectedPreset = null;
        
        // Default options
        this.options = {
            onSelect: null,
            initialPreset: null,
            showDescription: true,
            tileSize: 'medium', // small, medium, large
            ...options
        };
        
        // Define standard presets
        this.presets = [
            {
                id: 'vlog',
                name: 'Vlog',
                description: 'Casual, authentic style with quick cuts and simple transitions',
                color: '#FF6B6B',
                icon: '<i class="bi bi-camera-video"></i>',
                features: ['Quick cuts', 'Natural lighting', 'Face-focused'],
                defaultTransition: 'cut',
                settings: {
                    style: 'vlog',
                    transitionSpeed: 'fast',
                    colorGrading: 'natural',
                    textOverlay: true
                }
            },
            {
                id: 'hype',
                name: 'Hype',
                description: 'High-energy with fast cuts, zoom effects, and bold text',
                color: '#FF9966',
                icon: '<i class="bi bi-lightning-charge"></i>',
                features: ['Fast cuts', 'Zoom effects', 'Bold text'],
                defaultTransition: 'whip',
                settings: {
                    style: 'hype',
                    transitionSpeed: 'very_fast',
                    colorGrading: 'vibrant',
                    textOverlay: true
                }
            },
            {
                id: 'chill',
                name: 'Chill',
                description: 'Smooth fades with relaxed pacing and soft color grading',
                color: '#6B76FF',
                icon: '<i class="bi bi-cloud"></i>',
                features: ['Slow fades', 'Gentle pace', 'Soft colors'],
                defaultTransition: 'fade',
                settings: {
                    style: 'chill',
                    transitionSpeed: 'slow',
                    colorGrading: 'soft',
                    textOverlay: false
                }
            },
            {
                id: 'cinematic',
                name: 'Cinematic',
                description: 'Dramatic pacing with film-like color grading and letterboxing',
                color: '#66BFFF',
                icon: '<i class="bi bi-film"></i>',
                features: ['Letterbox', 'Dramatic', 'Film look'],
                defaultTransition: 'dissolve',
                settings: {
                    style: 'cinematic',
                    transitionSpeed: 'medium',
                    colorGrading: 'film',
                    textOverlay: false
                }
            }
        ];
        
        // Initialize UI
        this.initialize();
    }
    
    async initialize() {
        if (!this.container) {
            console.error(`Container element with ID "${this.containerId}" not found`);
            return;
        }
        
        // Create presets UI
        this.createPresetsUI();
        
        // Set initial selection if provided
        if (this.options.initialPreset) {
            this.selectPreset(this.options.initialPreset);
        }
        
        // Add keyboard navigation for accessibility
        this.addKeyboardNavigation();
    }
    
    createPresetsUI() {
        // Create heading
        const heading = document.createElement('h5');
        heading.className = 'mb-3';
        heading.textContent = 'Choose a Style Preset';
        this.container.appendChild(heading);
        
        // Create description
        const description = document.createElement('p');
        description.className = 'text-muted mb-3';
        description.textContent = 'Select a style preset to determine the look and feel of your video';
        this.container.appendChild(description);
        
        // Create presets grid
        const presetsGrid = document.createElement('div');
        presetsGrid.className = 'row g-3 presets-grid';
        
        // Generate preset tiles
        this.presets.forEach(preset => {
            const tileColClass = this.getTileColumnClass();
            const presetTile = document.createElement('div');
            presetTile.className = tileColClass;
            
            const tileContent = `
                <div class="preset-card h-100" 
                     data-preset-id="${preset.id}" 
                     role="button"
                     tabindex="0"
                     aria-pressed="false">
                    <div class="preset-header" style="background-color: ${preset.color}">
                        <span class="preset-icon">${preset.icon}</span>
                    </div>
                    <div class="preset-body">
                        <h6 class="preset-title">${preset.name}</h6>
                        ${this.options.showDescription ? 
                          `<p class="preset-description small text-muted">${preset.description}</p>` : ''}
                        <ul class="preset-features small">
                            ${preset.features.map(feature => `<li>${feature}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            `;
            
            presetTile.innerHTML = tileContent;
            presetsGrid.appendChild(presetTile);
            
            // Add click handler to the preset tile
            const card = presetTile.querySelector('.preset-card');
            card.addEventListener('click', () => this.selectPreset(preset.id));
        });
        
        this.container.appendChild(presetsGrid);
        
        // Add custom preset button
        const customPresetRow = document.createElement('div');
        customPresetRow.className = 'row mt-3';
        customPresetRow.innerHTML = `
            <div class="col-12 text-center">
                <button class="btn btn-outline-primary btn-sm custom-preset-btn">
                    <i class="bi bi-plus-circle"></i> Create Custom Preset
                </button>
            </div>
        `;
        this.container.appendChild(customPresetRow);
        
        // Add event listener for custom preset button
        const customBtn = customPresetRow.querySelector('.custom-preset-btn');
        customBtn.addEventListener('click', () => this.showCustomPresetDialog());
    }
    
    getTileColumnClass() {
        switch (this.options.tileSize) {
            case 'small': return 'col-6 col-md-3';
            case 'large': return 'col-12 col-md-6';
            case 'medium':
            default: return 'col-6 col-md-3';
        }
    }
    
    selectPreset(presetId) {
        // Find the preset by ID
        const preset = this.presets.find(p => p.id === presetId);
        if (!preset) {
            console.error(`Preset with ID "${presetId}" not found`);
            return;
        }
        
        // Update selected preset
        this.selectedPreset = preset;
        
        // Update UI
        const presetCards = this.container.querySelectorAll('.preset-card');
        presetCards.forEach(card => {
            const isSelected = card.dataset.presetId === presetId;
            card.classList.toggle('selected', isSelected);
            card.setAttribute('aria-pressed', isSelected ? 'true' : 'false');
        });
        
        // Trigger callback if provided
        if (typeof this.options.onSelect === 'function') {
            this.options.onSelect(preset);
        }
        
        // Dispatch custom event
        const event = new CustomEvent('presetSelected', {
            detail: preset,
            bubbles: true
        });
        this.container.dispatchEvent(event);
    }
    
    addKeyboardNavigation() {
        // Add keyboard navigation for accessibility
        const presetCards = this.container.querySelectorAll('.preset-card');
        
        presetCards.forEach(card => {
            card.addEventListener('keydown', event => {
                if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    card.click();
                }
            });
        });
    }
    
    showCustomPresetDialog() {
        // Create modal for custom preset
        const modalId = `${this.containerId}-custom-modal`;
        
        // Remove any existing modal with the same ID
        const existingModal = document.getElementById(modalId);
        if (existingModal) {
            existingModal.remove();
        }
        
        // Create modal HTML
        const modalHTML = `
            <div class="modal fade" id="${modalId}" tabindex="-1" aria-labelledby="${modalId}-label" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="${modalId}-label">Create Custom Style</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <form id="${modalId}-form">
                                <div class="mb-3">
                                    <label for="custom-name" class="form-label">Style Name</label>
                                    <input type="text" class="form-control" id="custom-name" required>
                                </div>
                                <div class="mb-3">
                                    <label for="custom-description" class="form-label">Description</label>
                                    <textarea class="form-control" id="custom-description" rows="2"></textarea>
                                </div>
                                <div class="mb-3">
                                    <label for="custom-color" class="form-label">Theme Color</label>
                                    <input type="color" class="form-control form-control-color" id="custom-color" value="#0d6efd">
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Transition Speed</label>
                                    <div class="btn-group w-100" role="group" aria-label="Transition speed">
                                        <input type="radio" class="btn-check" name="transition-speed" id="speed-slow" value="slow">
                                        <label class="btn btn-outline-primary" for="speed-slow">Slow</label>
                                        
                                        <input type="radio" class="btn-check" name="transition-speed" id="speed-medium" value="medium" checked>
                                        <label class="btn btn-outline-primary" for="speed-medium">Medium</label>
                                        
                                        <input type="radio" class="btn-check" name="transition-speed" id="speed-fast" value="fast">
                                        <label class="btn btn-outline-primary" for="speed-fast">Fast</label>
                                    </div>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Color Grading</label>
                                    <select class="form-select" id="color-grading">
                                        <option value="natural">Natural</option>
                                        <option value="vibrant">Vibrant</option>
                                        <option value="soft">Soft</option>
                                        <option value="film">Film</option>
                                        <option value="monochrome">Monochrome</option>
                                    </select>
                                </div>
                                <div class="form-check mb-3">
                                    <input class="form-check-input" type="checkbox" id="text-overlay" checked>
                                    <label class="form-check-label" for="text-overlay">
                                        Include Text Overlay
                                    </label>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="${modalId}-save">Save Preset</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Add modal to the DOM
        const modalContainer = document.createElement('div');
        modalContainer.innerHTML = modalHTML;
        document.body.appendChild(modalContainer.firstElementChild);
        
        // Initialize the modal
        const modal = new bootstrap.Modal(document.getElementById(modalId));
        modal.show();
        
        // Add event listener for save button
        document.getElementById(`${modalId}-save`).addEventListener('click', () => {
            const nameInput = document.getElementById('custom-name');
            if (!nameInput.value.trim()) {
                nameInput.classList.add('is-invalid');
                return;
            }
            
            // Create new custom preset
            const customPreset = {
                id: `custom-${Date.now()}`,
                name: document.getElementById('custom-name').value,
                description: document.getElementById('custom-description').value || 'Custom style preset',
                color: document.getElementById('custom-color').value,
                icon: '<i class="bi bi-stars"></i>',
                features: ['Custom', 'User defined'],
                defaultTransition: document.querySelector('input[name="transition-speed"]:checked').value || 'medium',
                settings: {
                    style: 'custom',
                    transitionSpeed: document.querySelector('input[name="transition-speed"]:checked').value || 'medium',
                    colorGrading: document.getElementById('color-grading').value,
                    textOverlay: document.getElementById('text-overlay').checked
                },
                isCustom: true
            };
            
            // Add the custom preset to the list
            this.presets.push(customPreset);
            
            // Update the UI
            this.refreshPresetsUI();
            
            // Select the new preset
            this.selectPreset(customPreset.id);
            
            // Hide the modal
            modal.hide();
        });
    }
    
    refreshPresetsUI() {
        // Clear existing content
        this.container.innerHTML = '';
        
        // Recreate UI
        this.createPresetsUI();
    }
    
    // Public methods
    getSelectedPreset() {
        return this.selectedPreset;
    }
    
    setPreset(presetId) {
        this.selectPreset(presetId);
    }
    
    getAvailablePresets() {
        return [...this.presets]; // Return a copy of the presets array
    }
    
    addCustomPreset(preset) {
        if (!preset || !preset.id || !preset.name) {
            console.error('Invalid preset data');
            return false;
        }
        
        // Check if a preset with the same ID already exists
        if (this.presets.find(p => p.id === preset.id)) {
            console.error(`A preset with ID "${preset.id}" already exists`);
            return false;
        }
        
        // Add custom marker
        preset.isCustom = true;
        
        // Add to presets array
        this.presets.push(preset);
        
        // Update UI
        this.refreshPresetsUI();
        
        return true;
    }
}

// Export the class for use in other modules
window.StylePresetSelector = StylePresetSelector; 