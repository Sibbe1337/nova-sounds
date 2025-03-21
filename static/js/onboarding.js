/**
 * Onboarding Experience
 * Interactive walkthrough for new users
 */

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', () => {
  // Initialize onboarding if it's the user's first visit
  initOnboarding();
});

/**
 * Initialize the onboarding experience
 */
function initOnboarding() {
  // Get onboarding elements
  const onboardingModal = document.getElementById('onboardingModal');
  
  // Check if onboarding has been completed before
  const onboardingCompleted = localStorage.getItem('onboardingCompleted') === 'true';
  
  // Only show onboarding if it's a new user
  if (!onboardingCompleted && onboardingModal) {
    // Show the modal after a short delay
    setTimeout(() => {
      openOnboarding();
    }, 1000);
  }
  
  // Set up event listeners for manual triggers
  const onboardingTriggers = document.querySelectorAll('[data-trigger="onboarding"]');
  onboardingTriggers.forEach(trigger => {
    trigger.addEventListener('click', (e) => {
      e.preventDefault();
      openOnboarding();
    });
  });
}

/**
 * Open the onboarding modal
 */
function openOnboarding() {
  const onboardingModal = document.getElementById('onboardingModal');
  if (!onboardingModal) return;
  
  // Make modal visible
  onboardingModal.classList.add('active');
  
  // Initialize the slides
  initializeSlides();
  
  // Add event listener to close button
  const closeButton = onboardingModal.querySelector('.onboarding-close');
  if (closeButton) {
    closeButton.addEventListener('click', closeOnboarding);
  }
  
  // Add event listeners to navigation buttons
  const prevButton = onboardingModal.querySelector('.prev-slide');
  const nextButton = onboardingModal.querySelector('.next-slide');
  
  if (prevButton) {
    prevButton.addEventListener('click', prevSlide);
  }
  
  if (nextButton) {
    nextButton.addEventListener('click', nextSlide);
  }
  
  // Add keyboard navigation
  document.addEventListener('keydown', handleKeyDown);
  
  // Add event listener to skip link
  const skipLink = onboardingModal.querySelector('.skip-link');
  if (skipLink) {
    skipLink.addEventListener('click', (e) => {
      e.preventDefault();
      closeOnboarding();
    });
  }
  
  // Update button states for the first slide
  updateButtonStates();
}

/**
 * Close the onboarding modal
 */
function closeOnboarding() {
  const onboardingModal = document.getElementById('onboardingModal');
  if (!onboardingModal) return;
  
  // Hide modal with animation
  onboardingModal.classList.remove('active');
  
  // Mark onboarding as completed in localStorage
  localStorage.setItem('onboardingCompleted', 'true');
  
  // Remove keyboard listener
  document.removeEventListener('keydown', handleKeyDown);
}

/**
 * Handle keyboard navigation
 */
function handleKeyDown(e) {
  if (e.key === 'Escape') {
    closeOnboarding();
  } else if (e.key === 'ArrowRight') {
    nextSlide();
  } else if (e.key === 'ArrowLeft') {
    prevSlide();
  }
}

/**
 * Initialize the slides
 */
function initializeSlides() {
  const onboardingModal = document.getElementById('onboardingModal');
  if (!onboardingModal) return;
  
  // Get all slides
  const slides = onboardingModal.querySelectorAll('.onboarding-slide');
  
  // Set the first slide as active
  if (slides.length > 0) {
    slides[0].classList.add('active');
  }
  
  // Initialize slide indicators
  const slideIndicators = onboardingModal.querySelector('.slide-indicators');
  if (slideIndicators) {
    // Clear any existing indicators
    slideIndicators.innerHTML = '';
    
    // Create indicators for each slide
    slides.forEach((slide, index) => {
      const indicator = document.createElement('div');
      indicator.classList.add('slide-indicator');
      if (index === 0) {
        indicator.classList.add('active');
      }
      
      // Add click event to jump to slide
      indicator.addEventListener('click', () => {
        goToSlide(index);
      });
      
      slideIndicators.appendChild(indicator);
    });
  }
}

/**
 * Navigate to the next slide
 */
function nextSlide() {
  const onboardingModal = document.getElementById('onboardingModal');
  if (!onboardingModal) return;
  
  // Get current slide
  const currentSlide = onboardingModal.querySelector('.onboarding-slide.active');
  if (!currentSlide) return;
  
  // Get next slide
  const nextSlide = currentSlide.nextElementSibling;
  if (!nextSlide || !nextSlide.classList.contains('onboarding-slide')) {
    // If last slide, close the onboarding
    closeOnboarding();
    return;
  }
  
  // Get current slide index
  const slides = onboardingModal.querySelectorAll('.onboarding-slide');
  const currentIndex = Array.from(slides).indexOf(currentSlide);
  
  // Go to next slide
  goToSlide(currentIndex + 1);
}

/**
 * Navigate to the previous slide
 */
function prevSlide() {
  const onboardingModal = document.getElementById('onboardingModal');
  if (!onboardingModal) return;
  
  // Get current slide
  const currentSlide = onboardingModal.querySelector('.onboarding-slide.active');
  if (!currentSlide) return;
  
  // Get prev slide
  const prevSlide = currentSlide.previousElementSibling;
  if (!prevSlide || !prevSlide.classList.contains('onboarding-slide')) return;
  
  // Get current slide index
  const slides = onboardingModal.querySelectorAll('.onboarding-slide');
  const currentIndex = Array.from(slides).indexOf(currentSlide);
  
  // Go to previous slide
  goToSlide(currentIndex - 1);
}

/**
 * Go to a specific slide
 */
function goToSlide(index) {
  const onboardingModal = document.getElementById('onboardingModal');
  if (!onboardingModal) return;
  
  // Get all slides
  const slides = onboardingModal.querySelectorAll('.onboarding-slide');
  if (index < 0 || index >= slides.length) return;
  
  // Remove active class from all slides
  slides.forEach(slide => {
    slide.classList.remove('active');
  });
  
  // Add active class to target slide
  slides[index].classList.add('active');
  
  // Update indicators
  const indicators = onboardingModal.querySelectorAll('.slide-indicator');
  indicators.forEach((indicator, i) => {
    indicator.classList.toggle('active', i === index);
  });
  
  // Update slide container transform
  const slidesContainer = onboardingModal.querySelector('.onboarding-slides');
  if (slidesContainer) {
    slidesContainer.style.transform = `translateX(-${index * 100}%)`;
  }
  
  // Update button states
  updateButtonStates();
  
  // Update the Next button text on the last slide
  const nextButton = onboardingModal.querySelector('.next-slide');
  if (nextButton) {
    const isLastSlide = index === slides.length - 1;
    nextButton.textContent = isLastSlide ? 'Get Started' : 'Next';
    nextButton.classList.toggle('btn-primary', isLastSlide);
    nextButton.classList.toggle('btn-secondary', !isLastSlide);
  }
}

/**
 * Update button states based on current slide
 */
function updateButtonStates() {
  const onboardingModal = document.getElementById('onboardingModal');
  if (!onboardingModal) return;
  
  // Get all slides
  const slides = onboardingModal.querySelectorAll('.onboarding-slide');
  
  // Get current slide
  const currentSlide = onboardingModal.querySelector('.onboarding-slide.active');
  if (!currentSlide) return;
  
  // Get current slide index
  const currentIndex = Array.from(slides).indexOf(currentSlide);
  
  // Update prev button state
  const prevButton = onboardingModal.querySelector('.prev-slide');
  if (prevButton) {
    prevButton.disabled = currentIndex === 0;
    prevButton.classList.toggle('btn-disabled', currentIndex === 0);
  }
}

/**
 * Reset onboarding (for testing)
 */
function resetOnboarding() {
  localStorage.removeItem('onboardingCompleted');
  console.log('Onboarding reset. Refresh the page to see it again.');
}

// Expose some functions to the global scope
window.Onboarding = {
  open: openOnboarding,
  close: closeOnboarding,
  reset: resetOnboarding
}; 