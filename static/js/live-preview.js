/**
 * Live Preview and Progress Tracking
 * Real-time video preview and detailed processing progress indicators
 */

class LivePreview {
  /**
   * Initialize the live preview and progress tracking system
   * @param {Object} options - Configuration options
   * @param {string} options.previewContainerId - ID of the preview container element
   * @param {string} options.progressContainerId - ID of the progress container element
   * @param {Function} options.onComplete - Callback function when processing completes
   * @param {Function} options.onError - Callback function when an error occurs
   */
  constructor(options = {}) {
    this.options = {
      previewContainerId: 'previewContainer',
      progressContainerId: 'progressContainer',
      onComplete: () => {},
      onError: () => {},
      pollingInterval: 1000, // 1 second polling
      ...options
    };
    
    this.previewContainer = document.getElementById(this.options.previewContainerId);
    this.progressContainer = document.getElementById(this.options.progressContainerId);
    
    this.videoId = null;
    this.processingStatus = 'idle';
    this.progress = {
      overall: 0,
      steps: {}
    };
    
    this.pollingTimer = null;
    this.previewUpdateTimer = null;
    
    // Processing steps
    this.steps = [
      { id: 'uploading', name: 'Uploading Content', defaultDuration: 3 },
      { id: 'analyzing', name: 'Analyzing Content', defaultDuration: 5 },
      { id: 'generating', name: 'Generating Video', defaultDuration: 15 },
      { id: 'rendering', name: 'Rendering Final Video', defaultDuration: 7 },
      { id: 'finalizing', name: 'Finalizing', defaultDuration: 2 }
    ];
    
    // Initialize the UI only if containers exist
    if (this.previewContainer && this.progressContainer) {
      this.initializeUI();
    } else {
      console.warn('Live preview containers not found. UI initialization skipped.');
    }
  }
  
  /**
   * Initialize the preview and progress UI components
   */
  initializeUI() {
    // Create preview player container
    this.previewContainer.innerHTML = `
      <div class="preview-wrapper">
        <div class="preview-player">
          <div class="preview-placeholder">
            <i class="fas fa-film"></i>
            <span>Preview will appear here</span>
          </div>
          <video id="previewVideo" controls playsinline class="hidden">
            Your browser does not support the video tag.
          </video>
        </div>
        <div class="preview-controls">
          <button class="btn btn-sm btn-outline-primary refresh-preview-btn">
            <i class="fas fa-sync-alt"></i> Refresh Preview
          </button>
          <div class="preview-status">
            <span class="status-dot"></span>
            <span class="status-text">Ready</span>
          </div>
        </div>
      </div>
    `;
    
    // Create progress tracking UI
    this.progressContainer.innerHTML = `
      <div class="progress-wrapper">
        <div class="overall-progress">
          <div class="progress-info">
            <span class="progress-label">Overall Progress</span>
            <span class="progress-percentage" id="overallProgressPercentage">0%</span>
          </div>
          <div class="progress-bar animated">
            <div class="progress-bar-fill" id="overallProgressBar" style="width: 0%"></div>
          </div>
        </div>
        
        <div class="steps-progress" id="stepsProgress">
          ${this.steps.map((step, index) => `
            <div class="step-item" data-step="${step.id}">
              <div class="step-indicator ${index === 0 ? 'current' : ''}">
                <span class="step-number">${index + 1}</span>
                <i class="fas fa-check step-check"></i>
              </div>
              <div class="step-content">
                <div class="step-header">
                  <span class="step-name">${step.name}</span>
                  <span class="step-time" id="${step.id}Time">--:--</span>
                </div>
                <div class="progress-bar step-progress">
                  <div class="progress-bar-fill" id="${step.id}Progress" style="width: 0%"></div>
                </div>
              </div>
            </div>
          `).join('')}
        </div>
        
        <div class="processing-info">
          <div class="info-item">
            <span class="info-label">Status:</span>
            <span class="info-value" id="processingStatus">Waiting to start</span>
          </div>
          <div class="info-item">
            <span class="info-label">Estimated time:</span>
            <span class="info-value" id="estimatedTime">--:--</span>
          </div>
          <div class="info-item">
            <span class="info-label">Video ID:</span>
            <span class="info-value" id="videoId">--</span>
          </div>
        </div>
      </div>
    `;
    
    // Set up event listeners
    const refreshBtn = this.previewContainer.querySelector('.refresh-preview-btn');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', () => this.refreshPreview());
    }
    
    // Initialize the preview video element
    this.previewVideo = document.getElementById('previewVideo');
  }
  
  /**
   * Start processing a video and tracking progress
   * @param {string} videoId - ID of the video being processed
   */
  startProcessing(videoId) {
    if (!videoId) {
      console.error('No video ID provided');
      return;
    }
    
    this.videoId = videoId;
    this.processingStatus = 'processing';
    
    // Update UI with video ID
    const videoIdElement = document.getElementById('videoId');
    if (videoIdElement) {
      videoIdElement.textContent = this.videoId;
    }
    
    // Reset progress
    this.progress = {
      overall: 0,
      steps: {}
    };
    
    this.steps.forEach(step => {
      this.progress.steps[step.id] = {
        progress: 0,
        status: 'pending',
        startTime: null,
        endTime: null
      };
    });
    
    // Set first step as active
    this.setCurrentStep(this.steps[0].id);
    
    // Update UI
    this.updateProgressUI();
    
    // Start polling for updates
    this.startPolling();
    
    // Update preview periodically
    this.startPreviewUpdates();
    
    // For demo, simulate progress
    if (typeof window.simulateProgress === 'undefined' || window.simulateProgress) {
      this.simulateProgress();
    }
  }
  
  /**
   * Stop processing tracking
   */
  stopProcessing() {
    this.processingStatus = 'idle';
    
    // Clear timers
    if (this.pollingTimer) {
      clearInterval(this.pollingTimer);
      this.pollingTimer = null;
    }
    
    if (this.previewUpdateTimer) {
      clearInterval(this.previewUpdateTimer);
      this.previewUpdateTimer = null;
    }
    
    // Update UI
    const statusElement = document.getElementById('processingStatus');
    if (statusElement) {
      statusElement.textContent = 'Processing stopped';
    }
  }
  
  /**
   * Set the current processing step
   * @param {string} stepId - ID of the current step
   */
  setCurrentStep(stepId) {
    const stepItems = document.querySelectorAll('.step-item');
    stepItems.forEach(item => {
      const isCurrentStep = item.dataset.step === stepId;
      item.classList.toggle('current', isCurrentStep);
      
      // Also mark previous steps as completed
      const stepIndex = this.steps.findIndex(s => s.id === stepId);
      const itemIndex = this.steps.findIndex(s => s.id === item.dataset.step);
      
      if (itemIndex < stepIndex) {
        item.classList.add('completed');
        item.classList.remove('current');
      } else if (itemIndex > stepIndex) {
        item.classList.remove('completed', 'current');
      }
    });
    
    // If step is being activated, set start time
    if (this.progress.steps[stepId].status === 'pending') {
      this.progress.steps[stepId].status = 'active';
      this.progress.steps[stepId].startTime = new Date();
    }
    
    // Update processing status text
    const statusElement = document.getElementById('processingStatus');
    if (statusElement) {
      const step = this.steps.find(s => s.id === stepId);
      statusElement.textContent = step ? `${step.name}...` : 'Processing';
    }
  }
  
  /**
   * Complete a processing step
   * @param {string} stepId - ID of the completed step
   */
  completeStep(stepId) {
    // Update step progress
    this.progress.steps[stepId].progress = 100;
    this.progress.steps[stepId].status = 'completed';
    this.progress.steps[stepId].endTime = new Date();
    
    // Mark step as completed in UI
    const stepItem = document.querySelector(`.step-item[data-step="${stepId}"]`);
    if (stepItem) {
      stepItem.classList.add('completed');
      stepItem.classList.remove('current');
    }
    
    // Update step progress bar
    const progressBar = document.getElementById(`${stepId}Progress`);
    if (progressBar) {
      progressBar.style.width = '100%';
    }
    
    // Update step time
    const timeElement = document.getElementById(`${stepId}Time`);
    if (timeElement) {
      const duration = this.calculateStepDuration(stepId);
      timeElement.textContent = this.formatDuration(duration);
    }
    
    // Move to next step
    const currentIndex = this.steps.findIndex(s => s.id === stepId);
    if (currentIndex < this.steps.length - 1) {
      this.setCurrentStep(this.steps[currentIndex + 1].id);
    } else {
      // All steps completed
      this.completeProcessing();
    }
    
    // Update overall progress
    this.updateOverallProgress();
  }
  
  /**
   * Complete the entire processing
   */
  completeProcessing() {
    this.processingStatus = 'completed';
    
    // Update UI
    const statusElement = document.getElementById('processingStatus');
    if (statusElement) {
      statusElement.textContent = 'Processing complete';
    }
    
    // Stop polling
    this.stopPolling();
    
    // Final preview update
    this.refreshPreview(true);
    
    // Call completion callback
    if (typeof this.options.onComplete === 'function') {
      this.options.onComplete(this.videoId);
    }
    
    // Show notification if available
    if (window.showSuccess) {
      window.showSuccess('Video processing complete!');
    }
  }
  
  /**
   * Update progress for a specific step
   * @param {string} stepId - ID of the step to update
   * @param {number} progress - Progress percentage (0-100)
   */
  updateStepProgress(stepId, progress) {
    // Validate progress
    const validProgress = Math.min(100, Math.max(0, progress));
    
    // Update progress data
    if (this.progress.steps[stepId]) {
      this.progress.steps[stepId].progress = validProgress;
    }
    
    // Update progress bar
    const progressBar = document.getElementById(`${stepId}Progress`);
    if (progressBar) {
      progressBar.style.width = `${validProgress}%`;
    }
    
    // If step reaches 100%, complete it
    if (validProgress >= 100 && this.progress.steps[stepId].status === 'active') {
      this.completeStep(stepId);
    }
    
    // Update overall progress
    this.updateOverallProgress();
  }
  
  /**
   * Update the overall progress based on all steps
   */
  updateOverallProgress() {
    // Calculate overall progress as the average of step progress, weighted by their durations
    let totalDuration = 0;
    let weightedProgress = 0;
    
    this.steps.forEach(step => {
      const duration = step.defaultDuration;
      totalDuration += duration;
      weightedProgress += (this.progress.steps[step.id]?.progress || 0) * duration;
    });
    
    const overallProgress = Math.round(weightedProgress / totalDuration);
    this.progress.overall = overallProgress;
    
    // Update progress bar
    const progressBar = document.getElementById('overallProgressBar');
    if (progressBar) {
      progressBar.style.width = `${overallProgress}%`;
    }
    
    // Update percentage text
    const percentageElement = document.getElementById('overallProgressPercentage');
    if (percentageElement) {
      percentageElement.textContent = `${overallProgress}%`;
    }
    
    // Update estimated time
    this.updateEstimatedTime();
  }
  
  /**
   * Update the estimated remaining time
   */
  updateEstimatedTime() {
    if (this.processingStatus !== 'processing') return;
    
    // Find the current active step
    const activeStep = Object.keys(this.progress.steps).find(
      stepId => this.progress.steps[stepId].status === 'active'
    );
    
    if (!activeStep) return;
    
    // Calculate how much time is left for the current step
    const currentStepInfo = this.progress.steps[activeStep];
    const currentStepDef = this.steps.find(s => s.id === activeStep);
    
    if (!currentStepInfo || !currentStepDef) return;
    
    const currentProgress = currentStepInfo.progress;
    const remainingInStep = (100 - currentProgress) / 100 * currentStepDef.defaultDuration;
    
    // Add time for all remaining steps
    let totalRemaining = remainingInStep;
    let foundCurrent = false;
    
    this.steps.forEach(step => {
      if (step.id === activeStep) {
        foundCurrent = true;
        return;
      }
      
      if (foundCurrent) {
        // This is a future step
        totalRemaining += step.defaultDuration;
      }
    });
    
    // Update UI
    const timeElement = document.getElementById('estimatedTime');
    if (timeElement) {
      timeElement.textContent = `~${this.formatDuration(totalRemaining)}`;
    }
  }
  
  /**
   * Calculate the actual duration of a step
   * @param {string} stepId - ID of the step
   * @returns {number} Duration in seconds
   */
  calculateStepDuration(stepId) {
    const stepInfo = this.progress.steps[stepId];
    
    if (stepInfo && stepInfo.startTime && stepInfo.endTime) {
      return (stepInfo.endTime - stepInfo.startTime) / 1000;
    }
    
    // Return default duration if actual not available
    const stepDef = this.steps.find(s => s.id === stepId);
    return stepDef ? stepDef.defaultDuration : 0;
  }
  
  /**
   * Format a duration in seconds to a human-readable string
   * @param {number} seconds - Duration in seconds
   * @returns {string} Formatted duration
   */
  formatDuration(seconds) {
    if (seconds < 60) {
      return `${Math.round(seconds)}s`;
    }
    
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
  }
  
  /**
   * Start polling for progress updates
   */
  startPolling() {
    // Clear existing timer
    if (this.pollingTimer) {
      clearInterval(this.pollingTimer);
    }
    
    // Set up new polling timer
    this.pollingTimer = setInterval(() => {
      this.fetchProgress();
    }, this.options.pollingInterval);
  }
  
  /**
   * Stop polling for updates
   */
  stopPolling() {
    if (this.pollingTimer) {
      clearInterval(this.pollingTimer);
      this.pollingTimer = null;
    }
  }
  
  /**
   * Fetch progress from the server
   */
  fetchProgress() {
    if (!this.videoId || this.processingStatus !== 'processing') return;
    
    // In a real implementation, this would be an API call
    // For demo purposes, we're using simulated progress
    
    // Example API call (commented out)
    /*
    fetch(`/api/videos/${this.videoId}/progress`)
      .then(response => response.json())
      .then(data => {
        // Update progress based on API response
        this.updateProgressFromData(data);
      })
      .catch(error => {
        console.error('Error fetching progress:', error);
        if (typeof this.options.onError === 'function') {
          this.options.onError(error);
        }
      });
    */
  }
  
  /**
   * Update the progress UI
   */
  updateProgressUI() {
    // Update all step progress bars
    Object.keys(this.progress.steps).forEach(stepId => {
      const progress = this.progress.steps[stepId].progress;
      const progressBar = document.getElementById(`${stepId}Progress`);
      if (progressBar) {
        progressBar.style.width = `${progress}%`;
      }
    });
    
    // Update overall progress
    this.updateOverallProgress();
  }
  
  /**
   * Start periodic preview updates
   */
  startPreviewUpdates() {
    // Clear existing timer
    if (this.previewUpdateTimer) {
      clearInterval(this.previewUpdateTimer);
    }
    
    // Set up new timer
    this.previewUpdateTimer = setInterval(() => {
      // Only refresh preview occasionally to avoid too many requests
      if (Math.random() < 0.3) { // ~30% chance each interval
        this.refreshPreview();
      }
    }, 5000); // Check every 5 seconds
  }
  
  /**
   * Refresh the video preview
   * @param {boolean} forceShow - Force showing the video preview
   */
  refreshPreview(forceShow = false) {
    if (!this.videoId) return;
    
    // In a real implementation, this would fetch a preview from the server
    // For demo purposes, we'll simulate preview generation
    
    const previewStatus = document.querySelector('.preview-status');
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-text');
    const previewPlaceholder = document.querySelector('.preview-placeholder');
    
    if (previewStatus && statusDot && statusText) {
      statusDot.className = 'status-dot loading';
      statusText.textContent = 'Loading preview...';
    }
    
    // Show loading animation on button
    const refreshBtn = document.querySelector('.refresh-preview-btn');
    if (refreshBtn) {
      refreshBtn.classList.add('loading');
    }
    
    // Simulated preview loading delay
    setTimeout(() => {
      // Determine if preview should be available based on progress
      const showPreview = forceShow || this.progress.overall > 30;
      
      if (showPreview) {
        // In a real implementation, this would be the actual preview URL
        const previewUrl = `/static/videos/previews/${this.videoId}_preview.mp4`;
        
        // Placeholder for demo (would be a real video in production)
        if (this.previewVideo) {
          // Set up a dummy source if needed for the demo
          if (!this.previewVideo.src) {
            this.previewVideo.src = 'https://storage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4';
          }
          
          this.previewVideo.classList.remove('hidden');
          if (previewPlaceholder) {
            previewPlaceholder.classList.add('hidden');
          }
        }
        
        if (previewStatus && statusDot && statusText) {
          statusDot.className = 'status-dot success';
          statusText.textContent = 'Preview available';
        }
      } else {
        if (previewStatus && statusDot && statusText) {
          statusDot.className = 'status-dot neutral';
          statusText.textContent = 'Preview not yet available';
        }
      }
      
      // Remove loading animation from button
      if (refreshBtn) {
        refreshBtn.classList.remove('loading');
      }
    }, 1500);
  }
  
  /**
   * Simulate progress for demonstration purposes
   */
  simulateProgress() {
    let currentStepIndex = 0;
    let currentProgress = 0;
    
    const interval = setInterval(() => {
      if (this.processingStatus !== 'processing') {
        clearInterval(interval);
        return;
      }
      
      // Get current step
      const currentStep = this.steps[currentStepIndex];
      
      // Increment progress
      currentProgress += Math.random() * 5 + 1;
      if (currentProgress >= 100) {
        // Step complete
        this.updateStepProgress(currentStep.id, 100);
        
        // Move to next step
        currentStepIndex++;
        currentProgress = 0;
        
        // Check if all steps are complete
        if (currentStepIndex >= this.steps.length) {
          clearInterval(interval);
          return;
        }
      } else {
        // Update current step progress
        this.updateStepProgress(currentStep.id, currentProgress);
      }
    }, 800);
  }
}

// Initialize global instance when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  // Only initialize if the required containers exist
  const previewContainer = document.getElementById('previewContainer');
  const progressContainer = document.getElementById('progressContainer');
  
  if (previewContainer && progressContainer) {
    window.livePreview = new LivePreview({
      onComplete: (videoId) => {
        console.log(`Processing completed for video: ${videoId}`);
        
        // In a real application, you might redirect to the video view page
        // location.href = `/videos/${videoId}`;
      }
    });
    
    // For demo purposes, start processing automatically after a delay
    if (window.autoStartPreview !== false) {
      setTimeout(() => {
        window.livePreview.startProcessing('demo-123456');
      }, 1500);
    }
  }
}); 