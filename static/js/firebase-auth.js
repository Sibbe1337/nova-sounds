// Firebase Authentication Module
import firebaseConfig from './firebase-config.js';

// Initialize Firebase
let app;
let auth;
let analytics;

// State to track if user is authenticated
let isAuthenticated = false;
let currentUser = null;

// Initialize Firebase when the DOM is loaded
document.addEventListener('DOMContentLoaded', async () => {
  try {
    // Dynamically import Firebase modules
    const { initializeApp } = await import('https://www.gstatic.com/firebasejs/9.22.0/firebase-app.js');
    const { getAuth, signInWithPopup, GoogleAuthProvider, onAuthStateChanged, signOut } 
      = await import('https://www.gstatic.com/firebasejs/9.22.0/firebase-auth.js');
    const { getAnalytics } = await import('https://www.gstatic.com/firebasejs/9.22.0/firebase-analytics.js');
    
    // Initialize Firebase
    app = initializeApp(firebaseConfig);
    auth = getAuth(app);
    analytics = getAnalytics(app);
    
    // Set up auth state listener
    onAuthStateChanged(auth, (user) => {
      if (user) {
        // User is signed in
        isAuthenticated = true;
        currentUser = user;
        updateUIForSignedInUser(user);
        
        // Dispatch custom event for signed in
        window.dispatchEvent(new CustomEvent('firebaseUserSignedIn', { detail: user }));
      } else {
        // User is signed out
        isAuthenticated = false;
        currentUser = null;
        updateUIForSignedOutUser();
        
        // Dispatch custom event for signed out
        window.dispatchEvent(new CustomEvent('firebaseUserSignedOut'));
      }
    });
    
    // Set up event listeners for auth buttons
    setupAuthButtons(GoogleAuthProvider, signInWithPopup, signOut);
    
    console.log('Firebase Auth initialized successfully');
  } catch (error) {
    console.error('Error initializing Firebase:', error);
  }
});

// Set up event listeners for authentication buttons
function setupAuthButtons(GoogleAuthProvider, signInWithPopup, signOut) {
  // Google Sign In buttons
  const googleButtons = document.querySelectorAll('.btn-google');
  googleButtons.forEach(button => {
    button.addEventListener('click', async (e) => {
      e.preventDefault();
      try {
        const provider = new GoogleAuthProvider();
        provider.addScope('profile');
        provider.addScope('email');
        
        // Display loading state
        button.classList.add('is-loading');
        button.disabled = true;
        
        // Sign in with Google
        const result = await signInWithPopup(auth, provider);
        
        // This gives you a Google Access Token
        const credential = GoogleAuthProvider.credentialFromResult(result);
        const token = credential.accessToken;
        
        // Send the token to your backend
        await sendTokenToBackend(token, result.user);
        
        // Show success notification
        showNotification('Successfully signed in with Google', 'success');
        
        // Redirect to home page or dashboard
        setTimeout(() => {
          window.location.href = '/';
        }, 1000);
      } catch (error) {
        console.error('Google sign in error:', error);
        showNotification('Failed to sign in with Google: ' + error.message, 'error');
      } finally {
        // Remove loading state
        button.classList.remove('is-loading');
        button.disabled = false;
      }
    });
  });
  
  // Sign out buttons
  const signOutButtons = document.querySelectorAll('.btn-sign-out');
  signOutButtons.forEach(button => {
    button.addEventListener('click', async (e) => {
      e.preventDefault();
      try {
        // Sign out
        await signOut(auth);
        
        // Show success notification
        showNotification('Successfully signed out', 'success');
        
        // Redirect to home page
        window.location.href = '/';
      } catch (error) {
        console.error('Sign out error:', error);
        showNotification('Failed to sign out: ' + error.message, 'error');
      }
    });
  });
}

// Update UI for signed in user
function updateUIForSignedInUser(user) {
  // Update all auth-related UI elements
  const userDisplayNames = document.querySelectorAll('.user-display-name');
  const userAvatars = document.querySelectorAll('.user-avatar');
  const authContainers = document.querySelectorAll('.auth-container');
  const signedInContainers = document.querySelectorAll('.signed-in-container');
  const signedOutContainers = document.querySelectorAll('.signed-out-container');
  
  // Update user name displays
  userDisplayNames.forEach(element => {
    element.textContent = user.displayName || 'User';
  });
  
  // Update user avatars
  userAvatars.forEach(element => {
    if (user.photoURL) {
      element.src = user.photoURL;
      element.alt = user.displayName || 'User Avatar';
    }
  });
  
  // Update visibility of auth-related containers
  authContainers.forEach(container => {
    container.classList.add('is-authenticated');
  });
  
  // Show signed-in containers
  signedInContainers.forEach(container => {
    container.style.display = 'block';
  });
  
  // Hide signed-out containers
  signedOutContainers.forEach(container => {
    container.style.display = 'none';
  });
}

// Update UI for signed out user
function updateUIForSignedOutUser() {
  // Update all auth-related UI elements
  const authContainers = document.querySelectorAll('.auth-container');
  const signedInContainers = document.querySelectorAll('.signed-in-container');
  const signedOutContainers = document.querySelectorAll('.signed-out-container');
  
  // Update visibility of auth-related containers
  authContainers.forEach(container => {
    container.classList.remove('is-authenticated');
  });
  
  // Hide signed-in containers
  signedInContainers.forEach(container => {
    container.style.display = 'none';
  });
  
  // Show signed-out containers
  signedOutContainers.forEach(container => {
    container.style.display = 'block';
  });
}

// Send token to backend for verification and session creation
async function sendTokenToBackend(token, user) {
  try {
    // Get CSRF token from cookie or meta tag if your app uses it
    const csrfToken = getCsrfToken();
    
    // Send token to backend
    const response = await fetch('/api/auth/firebase-login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
      },
      body: JSON.stringify({
        idToken: token,
        user: {
          uid: user.uid,
          email: user.email,
          displayName: user.displayName,
          photoURL: user.photoURL
        }
      })
    });
    
    if (!response.ok) {
      throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error sending token to backend:', error);
    throw error;
  }
}

// Helper function to get CSRF token
function getCsrfToken() {
  // Try to get from meta tag
  const metaTag = document.querySelector('meta[name="csrf-token"]');
  if (metaTag) {
    return metaTag.getAttribute('content');
  }
  
  // Try to get from cookie
  const cookies = document.cookie.split(';');
  for (const cookie of cookies) {
    const [name, value] = cookie.trim().split('=');
    if (name === 'csrftoken') {
      return value;
    }
  }
  
  return '';
}

// Show notification (uses the notifications.js module if available)
function showNotification(message, type = 'info') {
  if (window.Notifications && typeof window.Notifications.show === 'function') {
    window.Notifications.show(message, type);
  } else {
    console.log(`Notification (${type}): ${message}`);
    alert(message);
  }
}

// Export functions and objects for use in other modules
const FirebaseAuth = {
  isAuthenticated: () => isAuthenticated,
  getCurrentUser: () => currentUser,
  getIdToken: async () => {
    if (!isAuthenticated || !currentUser) return null;
    try {
      return await currentUser.getIdToken(true);
    } catch (error) {
      console.error('Error getting ID token:', error);
      return null;
    }
  }
};

// Make Firebase Auth available globally
window.FirebaseAuth = FirebaseAuth;

export default FirebaseAuth; 