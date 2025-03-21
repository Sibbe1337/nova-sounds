// Metadata Generator Component
// Auto-generates SEO-optimized titles, descriptions, and hashtags for videos

class MetadataGenerator {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        
        // Default options
        this.options = {
            apiEndpoint: '/api/openai/generate-metadata',
            defaultStyle: 'standard',
            videoData: null,
            musicData: null,
            includeEmoji: true,
            maxHashtags: 8,
            aiModels: {
                default: 'gpt-3.5-turbo',
                premium: 'gpt-4'
            },
            styles: {
                standard: { name: 'Standard', description: 'Professional, balanced content' },
                casual: { name: 'Casual', description: 'Relaxed, conversational tone' },
                trendy: { name: 'Trendy', description: 'Viral, hashtag-optimized' },
                informative: { name: 'Informative', description: 'Educational, detailed' }
            },
            onGenerate: null,
            onChange: null,
            onSave: null,
            ...options
        };
        
        // Track state
        this.isGenerating = false;
        this.lastGeneratedData = null;
        this.currentStyle = this.options.defaultStyle;
        this.currentModel = this.options.aiModels.default;
        
        // Initialize UI
        this.initialize();
    }
    
    initialize() {
        if (!this.container) {
            console.error(`Container element with ID "${this.containerId}" not found`);
            return;
        }
        
        // Create UI elements
        this.createUI();
        
        // Add event listeners
        this.addEventListeners();
    }
    
    createUI() {
        this.container.innerHTML = `
            <div class="metadata-generator-container">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5 class="mb-0">
                            <i class="bi bi-hash me-2"></i>SEO & Metadata
                        </h5>
                        <div class="form-check form-switch">
                            <input class="form-check-input" type="checkbox" id="${this.containerId}-emoji-toggle" ${this.options.includeEmoji ? 'checked' : ''}>
                            <label class="form-check-label" for="${this.containerId}-emoji-toggle">Include Emojis</label>
                        </div>
                    </div>
                    
                    <div class="card-body">
                        <form id="${this.containerId}-form">
                            <div class="mb-3">
                                <label for="${this.containerId}-title" class="form-label">Title <span class="text-muted small">(60-70 characters recommended)</span></label>
                                <div class="input-group">
                                    <input type="text" class="form-control" id="${this.containerId}-title" placeholder="Enter an attention-grabbing title" maxlength="100">
                                    <span class="input-group-text char-counter" id="${this.containerId}-title-counter">0/100</span>
                                </div>
                            </div>
                            
                            <div class="mb-3">
                                <label for="${this.containerId}-description" class="form-label">Description <span class="text-muted small">(150-300 characters optimal)</span></label>
                                <div class="input-group">
                                    <textarea class="form-control" id="${this.containerId}-description" rows="3" placeholder="Describe your video with relevant keywords" maxlength="500"></textarea>
                                    <span class="input-group-text char-counter" id="${this.containerId}-desc-counter">0/500</span>
                                </div>
                            </div>
                            
                            <div class="mb-3">
                                <label for="${this.containerId}-hashtags" class="form-label">Hashtags <span class="text-muted small">(${this.options.maxHashtags} max recommended)</span></label>
                                <div class="input-group">
                                    <input type="text" class="form-control" id="${this.containerId}-hashtags" placeholder="Enter hashtags separated by spaces (without #)">
                                    <span class="input-group-text hashtag-counter" id="${this.containerId}-hashtag-counter">0/${this.options.maxHashtags}</span>
                                </div>
                                <div class="hashtag-chips mt-2" id="${this.containerId}-hashtag-chips"></div>
                            </div>
                            
                            <div class="mb-3">
                                <label for="${this.containerId}-keywords" class="form-label">Keywords <span class="text-muted small">(for AI generation)</span></label>
                                <input type="text" class="form-control" id="${this.containerId}-keywords" placeholder="Enter keywords to target (comma separated)">
                            </div>
                        </form>
                        
                        <div class="row mt-4">
                            <div class="col-md-6 mb-3 mb-md-0">
                                <div class="d-flex flex-column h-100">
                                    <label class="form-label mb-2">Generation Style</label>
                                    <div class="btn-group style-selector flex-grow-1" role="group" aria-label="Generation style">
                                        ${Object.entries(this.options.styles).map(([key, style]) => `
                                            <input type="radio" class="btn-check" name="style" id="${this.containerId}-style-${key}" 
                                                value="${key}" ${key === this.currentStyle ? 'checked' : ''}>
                                            <label class="btn btn-outline-primary d-flex flex-column justify-content-center" 
                                                for="${this.containerId}-style-${key}" title="${style.description}">
                                                <span>${style.name}</span>
                                                <small class="d-none d-lg-block">${style.description}</small>
                                            </label>
                                        `).join('')}
                                    </div>
                                </div>
                            </div>
                            
                            <div class="col-md-6">
                                <div class="d-flex flex-column h-100">
                                    <label class="form-label mb-2">Actions</label>
                                    <div class="d-grid gap-2 flex-grow-1">
                                        <button type="button" class="btn btn-primary generate-btn" id="${this.containerId}-generate-btn">
                                            <i class="bi bi-magic me-1"></i> Generate with AI
                                        </button>
                                        <button type="button" class="btn btn-outline-secondary save-btn" id="${this.containerId}-save-btn">
                                            <i class="bi bi-check2-circle me-1"></i> Save Metadata
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="ai-generation-status alert alert-info mt-3 d-none" role="alert">
                            <div class="d-flex align-items-center">
                                <div class="spinner-border spinner-border-sm me-2" role="status">
                                    <span class="visually-hidden">Generating...</span>
                                </div>
                                <div>Generating SEO-optimized metadata...</div>
                            </div>
                        </div>
                        
                        <div class="generation-error alert alert-danger mt-3 d-none" role="alert">
                            <i class="bi bi-exclamation-triangle-fill me-2"></i>
                            <span class="error-message">Error generating metadata</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Cache DOM elements
        this.titleInput = document.getElementById(`${this.containerId}-title`);
        this.descriptionInput = document.getElementById(`${this.containerId}-description`);
        this.hashtagsInput = document.getElementById(`${this.containerId}-hashtags`);
        this.keywordsInput = document.getElementById(`${this.containerId}-keywords`);
        this.hashtagChips = document.getElementById(`${this.containerId}-hashtag-chips`);
        this.emojiToggle = document.getElementById(`${this.containerId}-emoji-toggle`);
        this.generateBtn = document.getElementById(`${this.containerId}-generate-btn`);
        this.saveBtn = document.getElementById(`${this.containerId}-save-btn`);
        this.titleCounter = document.getElementById(`${this.containerId}-title-counter`);
        this.descCounter = document.getElementById(`${this.containerId}-desc-counter`);
        this.hashtagCounter = document.getElementById(`${this.containerId}-hashtag-counter`);
        this.generationStatus = this.container.querySelector('.ai-generation-status');
        this.generationError = this.container.querySelector('.generation-error');
        this.styleButtons = this.container.querySelectorAll('input[name="style"]');
    }
    
    addEventListeners() {
        // Add input listeners for character counters
        this.titleInput.addEventListener('input', () => {
            this.updateCharacterCounter(this.titleInput, this.titleCounter);
            this.triggerChangeEvent();
        });
        
        this.descriptionInput.addEventListener('input', () => {
            this.updateCharacterCounter(this.descriptionInput, this.descCounter);
            this.triggerChangeEvent();
        });
        
        // Handle hashtag input
        this.hashtagsInput.addEventListener('input', () => {
            this.updateHashtags();
            this.triggerChangeEvent();
        });
        
        this.hashtagsInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ',') {
                e.preventDefault();
                this.hashtagsInput.value = this.hashtagsInput.value.trim();
                if (this.hashtagsInput.value) {
                    this.updateHashtags();
                    this.triggerChangeEvent();
                }
            }
        });
        
        // Keywords input listener
        this.keywordsInput.addEventListener('input', () => {
            this.triggerChangeEvent();
        });
        
        // Emoji toggle listener
        this.emojiToggle.addEventListener('change', () => {
            this.options.includeEmoji = this.emojiToggle.checked;
        });
        
        // Generation style selection
        this.styleButtons.forEach(btn => {
            btn.addEventListener('change', (e) => {
                this.currentStyle = e.target.value;
            });
        });
        
        // Generate button
        this.generateBtn.addEventListener('click', () => {
            this.generateMetadata();
        });
        
        // Save button
        this.saveBtn.addEventListener('click', () => {
            this.saveMetadata();
        });
    }
    
    updateCharacterCounter(inputElement, counterElement) {
        const length = inputElement.value.length;
        const max = inputElement.getAttribute('maxlength');
        counterElement.textContent = `${length}/${max}`;
        
        // Add warning class if approaching limit
        if (length > max * 0.9) {
            counterElement.classList.add('text-danger');
        } else if (length > max * 0.7) {
            counterElement.classList.add('text-warning');
            counterElement.classList.remove('text-danger');
        } else {
            counterElement.classList.remove('text-warning', 'text-danger');
        }
    }
    
    updateHashtags() {
        // Get hashtags from input
        const hashtags = this.parseHashtags(this.hashtagsInput.value);
        
        // Update counter
        this.hashtagCounter.textContent = `${hashtags.length}/${this.options.maxHashtags}`;
        
        // Add warning class if approaching limit
        if (hashtags.length > this.options.maxHashtags) {
            this.hashtagCounter.classList.add('text-danger');
        } else if (hashtags.length === this.options.maxHashtags) {
            this.hashtagCounter.classList.add('text-warning');
            this.hashtagCounter.classList.remove('text-danger');
        } else {
            this.hashtagCounter.classList.remove('text-warning', 'text-danger');
        }
        
        // Update hashtag chips
        this.renderHashtagChips(hashtags);
    }
    
    parseHashtags(input) {
        if (!input) return [];
        
        // Remove existing # symbols
        input = input.replace(/#/g, '');
        
        // Split by spaces or commas
        let hashtags = input.split(/[\s,]+/).filter(tag => tag.trim() !== '');
        
        // Remove any invalid characters
        hashtags = hashtags.map(tag => tag.replace(/[^\w\u00C0-\u017F]/g, ''));
        
        // Remove duplicates
        return [...new Set(hashtags)];
    }
    
    renderHashtagChips(hashtags) {
        // Clear existing chips
        this.hashtagChips.innerHTML = '';
        
        // Add new chips
        hashtags.forEach((tag, index) => {
            if (!tag) return;
            
            const chip = document.createElement('span');
            chip.className = 'badge bg-primary me-1 mb-1 hashtag-chip';
            
            // Add warning class if over the limit
            if (index >= this.options.maxHashtags) {
                chip.classList.remove('bg-primary');
                chip.classList.add('bg-danger');
            }
            
            chip.innerHTML = `#${tag} <i class="bi bi-x-circle hashtag-remove" data-tag="${tag}"></i>`;
            this.hashtagChips.appendChild(chip);
            
            // Add remove event
            chip.querySelector('.hashtag-remove').addEventListener('click', () => {
                this.removeHashtag(tag);
            });
        });
    }
    
    removeHashtag(tagToRemove) {
        const hashtags = this.parseHashtags(this.hashtagsInput.value);
        const filteredTags = hashtags.filter(tag => tag !== tagToRemove);
        this.hashtagsInput.value = filteredTags.join(' ');
        this.updateHashtags();
        this.triggerChangeEvent();
    }
    
    async generateMetadata() {
        if (this.isGenerating) return;
        
        this.isGenerating = true;
        this.showGenerationStatus(true);
        this.hideGenerationError();
        
        try {
            // Build request data
            const requestData = {
                style: this.currentStyle,
                includeEmoji: this.options.includeEmoji,
                model: this.currentModel,
                keywords: this.keywordsInput.value,
                maxHashtags: this.options.maxHashtags
            };
            
            // Add video data if available
            if (this.options.videoData) {
                requestData.videoData = this.options.videoData;
            }
            
            // Add music data if available
            if (this.options.musicData) {
                requestData.musicData = this.options.musicData;
            }
            
            // Call the API endpoint
            const response = await fetch(this.options.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });
            
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (!data || !data.success) {
                throw new Error(data.error || 'Failed to generate metadata');
            }
            
            // Update form with generated metadata
            this.updateFormWithGeneratedData(data.metadata);
            
            // Store last generated data
            this.lastGeneratedData = data.metadata;
            
            // Trigger callback if provided
            if (typeof this.options.onGenerate === 'function') {
                this.options.onGenerate(data.metadata);
            }
            
        } catch (error) {
            console.error('Error generating metadata:', error);
            this.showGenerationError(error.message || 'Failed to generate metadata');
        } finally {
            this.isGenerating = false;
            this.showGenerationStatus(false);
        }
    }
    
    updateFormWithGeneratedData(metadata) {
        if (!metadata) return;
        
        // Update title
        if (metadata.title) {
            this.titleInput.value = metadata.title;
            this.updateCharacterCounter(this.titleInput, this.titleCounter);
        }
        
        // Update description
        if (metadata.description) {
            this.descriptionInput.value = metadata.description;
            this.updateCharacterCounter(this.descriptionInput, this.descCounter);
        }
        
        // Update hashtags
        if (metadata.hashtags) {
            // Format hashtags - remove # symbols if present
            const cleanedHashtags = Array.isArray(metadata.hashtags) ?
                metadata.hashtags.map(tag => tag.replace(/^#/, '')) :
                metadata.hashtags.split(/[\s,]+/).map(tag => tag.replace(/^#/, ''));
                
            this.hashtagsInput.value = cleanedHashtags.join(' ');
            this.updateHashtags();
        }
        
        // Trigger change event
        this.triggerChangeEvent();
    }
    
    saveMetadata() {
        const metadata = this.getMetadata();
        
        // Trigger callback if provided
        if (typeof this.options.onSave === 'function') {
            this.options.onSave(metadata);
        }
        
        return metadata;
    }
    
    getMetadata() {
        return {
            title: this.titleInput.value.trim(),
            description: this.descriptionInput.value.trim(),
            hashtags: this.parseHashtags(this.hashtagsInput.value),
            keywords: this.keywordsInput.value.split(',').map(k => k.trim()).filter(k => k),
            style: this.currentStyle,
            includeEmoji: this.options.includeEmoji
        };
    }
    
    setMetadata(metadata) {
        if (!metadata) return;
        
        // Update title
        if (metadata.title) {
            this.titleInput.value = metadata.title;
            this.updateCharacterCounter(this.titleInput, this.titleCounter);
        }
        
        // Update description
        if (metadata.description) {
            this.descriptionInput.value = metadata.description;
            this.updateCharacterCounter(this.descriptionInput, this.descCounter);
        }
        
        // Update hashtags
        if (metadata.hashtags) {
            const hashtagString = Array.isArray(metadata.hashtags) ? 
                metadata.hashtags.join(' ') : metadata.hashtags;
            this.hashtagsInput.value = hashtagString;
            this.updateHashtags();
        }
        
        // Update keywords
        if (metadata.keywords) {
            const keywordsString = Array.isArray(metadata.keywords) ? 
                metadata.keywords.join(', ') : metadata.keywords;
            this.keywordsInput.value = keywordsString;
        }
        
        // Update style if provided
        if (metadata.style && this.options.styles[metadata.style]) {
            this.currentStyle = metadata.style;
            
            // Update radio button
            const styleRadio = document.getElementById(`${this.containerId}-style-${metadata.style}`);
            if (styleRadio) {
                styleRadio.checked = true;
            }
        }
        
        // Update emoji toggle if provided
        if (metadata.includeEmoji !== undefined) {
            this.options.includeEmoji = metadata.includeEmoji;
            this.emojiToggle.checked = metadata.includeEmoji;
        }
    }
    
    showGenerationStatus(show) {
        if (show) {
            this.generationStatus.classList.remove('d-none');
            this.generateBtn.disabled = true;
            this.generateBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generating...';
        } else {
            this.generationStatus.classList.add('d-none');
            this.generateBtn.disabled = false;
            this.generateBtn.innerHTML = '<i class="bi bi-magic me-1"></i> Generate with AI';
        }
    }
    
    showGenerationError(message) {
        this.generationError.classList.remove('d-none');
        this.generationError.querySelector('.error-message').textContent = message || 'Error generating metadata';
    }
    
    hideGenerationError() {
        this.generationError.classList.add('d-none');
    }
    
    triggerChangeEvent() {
        if (typeof this.options.onChange === 'function') {
            this.options.onChange(this.getMetadata());
        }
    }
    
    setVideoData(videoData) {
        this.options.videoData = videoData;
    }
    
    setMusicData(musicData) {
        this.options.musicData = musicData;
    }
    
    reset() {
        this.titleInput.value = '';
        this.descriptionInput.value = '';
        this.hashtagsInput.value = '';
        this.keywordsInput.value = '';
        this.updateCharacterCounter(this.titleInput, this.titleCounter);
        this.updateCharacterCounter(this.descriptionInput, this.descCounter);
        this.updateHashtags();
        
        // Reset style to default
        this.currentStyle = this.options.defaultStyle;
        const defaultStyleRadio = document.getElementById(`${this.containerId}-style-${this.options.defaultStyle}`);
        if (defaultStyleRadio) {
            defaultStyleRadio.checked = true;
        }
        
        this.lastGeneratedData = null;
        this.hideGenerationError();
    }
}

// Initialize on page load if required
document.addEventListener('DOMContentLoaded', function() {
    // Check if there's a container with the default ID
    const container = document.getElementById('metadataGeneratorContainer');
    if (container) {
        window.metadataGenerator = new MetadataGenerator('metadataGeneratorContainer');
    }
}); 