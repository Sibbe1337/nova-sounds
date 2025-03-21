/**
 * Service Worker for Offline Support
 * Provides caching for critical assets and API responses
 */

const CACHE_NAME = 'app-cache-v1';
const OFFLINE_PAGE = '/offline.html';

// Resources to cache on install
const PRECACHE_RESOURCES = [
  '/',
  '/offline.html',
  '/auth',
  '/static/css/main.css',
  '/static/css/variables.css',
  '/static/css/a11y.css',
  '/static/css/grid-system.css',
  '/static/js/theme-manager.js',
  '/static/js/offline-handler.js',
  '/static/css/ui-states.css',
  '/static/css/buttons.css',
  '/static/css/interactive-cards.css',
  '/static/images/logo.png',
  '/static/images/offline.svg'
];

// API routes to cache on use
const API_ROUTES = [
  '/api/music',
  '/api/styles',
  '/api/videos'
];

// Install event - precache critical resources
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(PRECACHE_RESOURCES))
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames
            .filter(cacheName => cacheName !== CACHE_NAME)
            .map(cacheName => caches.delete(cacheName))
        );
      })
      .then(() => self.clients.claim())
  );
});

// Fetch event - return cached responses when offline
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Only handle GET requests
  if (request.method !== 'GET') return;
  
  // Handle API requests
  if (API_ROUTES.some(route => url.pathname.startsWith(route))) {
    event.respondWith(handleApiRequest(request));
    return;
  }
  
  // Handle asset requests
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(handleAssetRequest(request));
    return;
  }
  
  // Handle navigation requests
  if (request.mode === 'navigate') {
    event.respondWith(handleNavigationRequest(request));
    return;
  }
  
  // Default strategy - network first, falling back to cache
  event.respondWith(
    fetch(request)
      .catch(() => caches.match(request))
  );
});

/**
 * Handle API requests with stale-while-revalidate strategy
 * @param {Request} request - The fetch request
 * @returns {Promise<Response>} The response
 */
async function handleApiRequest(request) {
  const cache = await caches.open(CACHE_NAME);
  
  // Try to get a cached response
  const cachedResponse = await cache.match(request);
  
  // Clone the request (because it's a stream and can only be consumed once)
  const fetchPromise = fetch(request)
    .then(response => {
      // Don't cache error responses
      if (!response.ok) return response;
      
      // Clone the response (it's a stream too)
      const responseToCache = response.clone();
      
      // Store the fresh response in cache
      cache.put(request, responseToCache);
      
      return response;
    })
    .catch(error => {
      console.error('Fetch failed for API request:', error);
      // If we have a cached response, return it
      if (cachedResponse) {
        return cachedResponse;
      }
      
      // If it's a data API, return empty data with offline indicator
      return new Response(JSON.stringify({
        error: 'You are offline',
        offline: true,
        data: []
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    });
  
  // Return the cached response if we have one, otherwise wait for the network
  return cachedResponse || fetchPromise;
}

/**
 * Handle static asset requests with cache-first strategy
 * @param {Request} request - The fetch request
 * @returns {Promise<Response>} The response
 */
async function handleAssetRequest(request) {
  const cache = await caches.open(CACHE_NAME);
  
  // Try to get the resource from the cache
  const cachedResponse = await cache.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }
  
  // If not in cache, try to fetch it
  try {
    const response = await fetch(request);
    
    // Don't cache error responses
    if (!response.ok) return response;
    
    // Cache the new response
    cache.put(request, response.clone());
    
    return response;
  } catch (error) {
    console.error('Failed to fetch asset:', error);
    
    // For image requests, we could return a placeholder
    if (request.destination === 'image') {
      return caches.match('/static/images/offline.svg');
    }
    
    // For other assets, we don't have a fallback
    return new Response('Resource not available offline', { 
      status: 503,
      headers: { 'Content-Type': 'text/plain' }
    });
  }
}

/**
 * Handle navigation requests (HTML pages)
 * @param {Request} request - The fetch request
 * @returns {Promise<Response>} The response
 */
async function handleNavigationRequest(request) {
  try {
    // Always try network first for navigation
    const response = await fetch(request);
    
    // Cache the page if successful
    const cache = await caches.open(CACHE_NAME);
    cache.put(request, response.clone());
    
    return response;
  } catch (error) {
    console.error('Navigation fetch failed:', error);
    
    // Try to get the page from cache
    const cache = await caches.open(CACHE_NAME);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // If not in cache, return the offline page
    return cache.match(OFFLINE_PAGE);
  }
}

// Listen for messages from clients
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
}); 