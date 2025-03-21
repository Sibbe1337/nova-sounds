/**
 * Interactive Cards - Behavior for card interactions and animations
 */

document.addEventListener('DOMContentLoaded', function() {
  initCardComponents();
});

function initCardComponents() {
  // Initialize card menus
  initCardMenus();
  
  // Initialize card actions
  initCardActions();
  
  // Lazy load card images
  initLazyLoading();
}

function initCardMenus() {
  // Setup card menu toggles
  document.querySelectorAll('.card-menu-button').forEach(button => {
    button.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      
      const menu = this.closest('.card-menu');
      
      // Close all other menus first
      document.querySelectorAll('.card-menu.active').forEach(activeMenu => {
        if (activeMenu !== menu) activeMenu.classList.remove('active');
      });
      
      // Toggle this menu
      menu.classList.toggle('active');
    });
  });
  
  // Close menus when clicking outside
  document.addEventListener('click', function(e) {
    if (!e.target.closest('.card-menu')) {
      document.querySelectorAll('.card-menu.active').forEach(menu => {
        menu.classList.remove('active');
      });
    }
  });
  
  // Initialize menu item actions
  document.querySelectorAll('.card-menu-item').forEach(item => {
    item.addEventListener('click', function() {
      const action = this.dataset.action;
      const cardId = this.closest('.interactive-card').dataset.id;
      
      if (!action) return;
      
      // Close the menu
      this.closest('.card-menu').classList.remove('active');
      
      // Process actions based on type
      switch(action) {
        case 'edit':
          if (window.showInfo) window.showInfo(`Editing item ${cardId}`);
          break;
          
        case 'delete':
          confirmDelete(cardId, this.closest('.interactive-card'));
          break;
          
        case 'share':
          shareContent(cardId);
          break;
          
        case 'favorite':
          toggleFavorite(cardId, this);
          break;
      }
    });
  });
}

function confirmDelete(cardId, cardElement) {
  if (window.showWarning) {
    window.showWarning('Are you sure you want to delete this item?', {
      autoHide: false,
      onClick: () => deleteItem(cardId, cardElement)
    });
  } else if (confirm('Are you sure you want to delete this item?')) {
    deleteItem(cardId, cardElement);
  }
}

function deleteItem(cardId, cardElement) {
  if (cardElement) {
    cardElement.style.opacity = '0';
    cardElement.style.transform = 'scale(0.9)';
    
    setTimeout(() => {
      cardElement.remove();
      if (window.showSuccess) window.showSuccess('Item deleted successfully');
    }, 300);
  }
}

function shareContent(cardId) {
  const shareUrl = window.location.origin + window.location.pathname + '?id=' + cardId;
  
  if (navigator.share) {
    navigator.share({
      title: 'Check out this content',
      url: shareUrl
    })
    .then(() => {
      if (window.showSuccess) window.showSuccess('Shared successfully');
    })
    .catch(() => {
      copyToClipboard(shareUrl);
    });
  } else {
    copyToClipboard(shareUrl);
  }
}

function copyToClipboard(text) {
  const input = document.createElement('input');
  input.value = text;
  document.body.appendChild(input);
  input.select();
  
  try {
    document.execCommand('copy');
    if (window.showSuccess) window.showSuccess('Link copied to clipboard');
  } catch (err) {
    if (window.showError) window.showError('Failed to copy link');
  }
  
  document.body.removeChild(input);
}

function toggleFavorite(cardId, element) {
  const isFavorite = element.classList.contains('favorited');
  
  if (isFavorite) {
    element.classList.remove('favorited');
    if (element.querySelector('i')) {
      element.querySelector('i').classList.replace('fas', 'far');
    }
    if (window.showInfo) window.showInfo('Removed from favorites');
  } else {
    element.classList.add('favorited');
    if (element.querySelector('i')) {
      element.querySelector('i').classList.replace('far', 'fas');
    }
    if (window.showSuccess) window.showSuccess('Added to favorites');
  }
}

function initCardActions() {
  // Play buttons for media cards
  document.querySelectorAll('.action-card-button[data-action="play"]').forEach(button => {
    button.addEventListener('click', function() {
      const cardId = this.closest('.interactive-card').dataset.id;
      if (window.showInfo) window.showInfo('Playing media...');
    });
  });
  
  // Make cards with href clickable
  document.querySelectorAll('.interactive-card[data-href]').forEach(card => {
    card.addEventListener('click', function(e) {
      // Don't navigate if clicking on a button or menu
      if (e.target.closest('.card-action-button') || 
          e.target.closest('.card-menu') ||
          e.target.closest('a')) {
        return;
      }
      
      const href = this.dataset.href;
      if (href) window.location.href = href;
    });
    
    // Add visual cue that card is clickable
    card.classList.add('clickable');
    card.style.cursor = 'pointer';
  });
}

function initLazyLoading() {
  if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target;
          const src = img.dataset.src;
          
          if (src) {
            img.src = src;
            img.removeAttribute('data-src');
            img.addEventListener('load', () => {
              img.classList.remove('image-placeholder');
            });
            imageObserver.unobserve(img);
          }
        }
      });
    });
    
    // Observe all lazy images
    document.querySelectorAll('.card-header-image[data-src]').forEach(img => {
      imageObserver.observe(img);
      img.classList.add('image-placeholder');
    });
  } else {
    // Fallback for browsers without IntersectionObserver
    document.querySelectorAll('.card-header-image[data-src]').forEach(img => {
      img.src = img.dataset.src;
      img.removeAttribute('data-src');
    });
  }
}

// Public API
window.InteractiveCards = {
  refresh: initCardComponents,
  
  animate: function() {
    document.querySelectorAll('.interactive-card').forEach((card, index) => {
      // Reset animation
      card.style.animation = 'none';
      card.offsetHeight; // Trigger reflow
      card.style.animation = `card-appear 0.5s ease ${index * 0.1}s forwards`;
      card.style.opacity = '0';
      card.style.transform = 'translateY(20px)';
    });
  },
  
  updateProgress: function(cardId, percentage, status) {
    const card = document.querySelector(`.interactive-card[data-id="${cardId}"]`);
    if (!card) return;
    
    const progressBar = card.querySelector('.card-status-bar');
    if (!progressBar) return;
    
    // Remove existing status classes
    progressBar.classList.remove('success', 'warning', 'danger');
    
    // Update progress
    progressBar.style.width = `${percentage}%`;
    
    // Add status class if provided
    if (status) progressBar.classList.add(status);
  }
}; 