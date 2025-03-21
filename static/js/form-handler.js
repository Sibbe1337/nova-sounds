/**
 * Form Handler
 * Handles form submissions, loading states, and validation
 */

document.addEventListener('DOMContentLoaded', function() {
  // Initialize form handlers
  initFormSubmit();
  
  // Initialize preview button
  initPreviewButton();
});

/**
 * Initialize form submission handler
 */
function initFormSubmit() {
  const form = document.getElementById('videoForm');
  if (!form) return;
  
  const submitBtn = document.getElementById('submitBtn');
  const processingIndicator = document.querySelector('.processing-indicator');
  const progressBar = document.getElementById('processingProgressBar');
  const progressText = document.getElementById('processingProgress');
  
  form.addEventListener('submit', function(e) {
    // Check if form is valid
    if (!validateForm(form)) {
      e.preventDefault();
      if (window.showError) {
        window.showError('Please complete all required fields');
      }
      return false;
    }
    
    // Show loading state
    if (submitBtn) {
      submitBtn.classList.add('loading');
      submitBtn.disabled = true;
    }
    
    // For demo purposes, we'll simulate the upload progress
    // In a real application, this would use fetch API with progress events
    if (processingIndicator) {
      setTimeout(() => {
        // Hide the button and show progress
        processingIndicator.style.display = 'block';
        
        // Simulate progress
        let progress = 0;
        const interval = setInterval(() => {
          progress += Math.random() * 15;
          if (progress >= 100) {
            progress = 100;
            clearInterval(interval);
            
            // In a real app, you would redirect after successful upload
            // window.location.href = '/videos/' + response.video_id;
          }
          
          // Update progress bar
          if (progressBar) {
            progressBar.style.width = progress + '%';
          }
          
          // Update progress text
          if (progressText) {
            progressText.textContent = Math.round(progress) + '%';
          }
        }, 800);
      }, 1500);
    }
    
    // Return true to submit form normally
    // For simulation, we're preventing real submission
    e.preventDefault();
    return false;
  });
}

/**
 * Initialize preview button
 */
function initPreviewButton() {
  const previewBtn = document.getElementById('previewBtn');
  if (!previewBtn) return;
  
  previewBtn.addEventListener('click', function() {
    // Validate form first
    const form = document.getElementById('videoForm');
    if (!form || !validateForm(form)) {
      if (window.showError) {
        window.showError('Please complete all required fields to preview');
      }
      return;
    }
    
    // Show loading state
    previewBtn.classList.add('loading');
    
    // Simulate preview generation
    setTimeout(() => {
      previewBtn.classList.remove('loading');
      
      // In a real application, you would display a preview
      if (window.showInfo) {
        window.showInfo('Preview generated! Check it out below.');
      }
      
      // Simulate showing a preview section
      const previewSection = document.querySelector('.preview-section');
      if (previewSection) {
        previewSection.style.display = 'block';
      }
    }, 2000);
  });
}

/**
 * Validate the form
 * 
 * @param {HTMLFormElement} form - The form to validate
 * @return {boolean} Whether the form is valid
 */
function validateForm(form) {
  let isValid = true;
  
  // Check all required inputs
  const requiredInputs = form.querySelectorAll('[required]');
  requiredInputs.forEach(input => {
    if (!input.value.trim()) {
      isValid = false;
      highlightInvalidField(input);
    } else {
      removeInvalidHighlight(input);
    }
  });
  
  // Check if music track is selected
  const musicTrackInput = document.getElementById('selected_track');
  if (musicTrackInput && !musicTrackInput.value) {
    isValid = false;
    const musicSection = document.querySelector('.music-selection');
    if (musicSection) {
      highlightInvalidField(musicSection);
    }
  }
  
  return isValid;
}

/**
 * Highlight an invalid form field
 * 
 * @param {HTMLElement} field - The field to highlight
 */
function highlightInvalidField(field) {
  field.classList.add('invalid');
  
  // Add error message if it doesn't exist
  const parent = field.closest('.form-group');
  if (parent && !parent.querySelector('.error-message')) {
    const errorMessage = document.createElement('div');
    errorMessage.className = 'error-message';
    errorMessage.textContent = 'This field is required';
    parent.appendChild(errorMessage);
  }
  
  // Add event listener to clear error when user corrects
  field.addEventListener('input', function onInput() {
    if (field.value.trim()) {
      removeInvalidHighlight(field);
      field.removeEventListener('input', onInput);
    }
  }, { once: false });
}

/**
 * Remove invalid highlight from a field
 * 
 * @param {HTMLElement} field - The field to remove highlight from
 */
function removeInvalidHighlight(field) {
  field.classList.remove('invalid');
  
  // Remove error message if it exists
  const parent = field.closest('.form-group');
  if (parent) {
    const errorMessage = parent.querySelector('.error-message');
    if (errorMessage) {
      parent.removeChild(errorMessage);
    }
  }
}

/**
 * Show notification when track is selected
 * 
 * @param {string} trackName - The name of the selected track
 */
function notifyTrackSelection(trackName) {
  if (window.showSuccess) {
    window.showSuccess(`Selected music track: ${trackName}`);
  }
}

// Expose public API
window.FormHandler = {
  validateForm,
  notifyTrackSelection
}; 