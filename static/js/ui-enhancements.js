// UI enhancement functions
document.addEventListener('DOMContentLoaded', function() {
    // Fix theme toggle button
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.checked = document.documentElement.classList.contains('dark-theme');
        
        themeToggle.addEventListener('change', function() {
            if (this.checked) {
                document.documentElement.classList.add('dark-theme');
                document.documentElement.classList.remove('light-theme');
                document.body.classList.add('dark-theme');
                document.body.classList.remove('light-theme');
                localStorage.setItem('youtube-shorts-machine-theme', 'dark-theme');
            } else {
                document.documentElement.classList.remove('dark-theme');
                document.documentElement.classList.add('light-theme');
                document.body.classList.remove('dark-theme');
                document.body.classList.add('light-theme');
                localStorage.setItem('youtube-shorts-machine-theme', 'light-theme');
            }
            
            // Update theme icon
            const icon = document.querySelector('.theme-toggle-icon');
            if (icon) {
                if (this.checked) {
                    icon.classList.remove('fa-sun');
                    icon.classList.add('fa-moon');
                } else {
                    icon.classList.remove('fa-moon');
                    icon.classList.add('fa-sun');
                }
            }
        });
    }
    
    // Interactive Waveform Visualization
    initAudioWaveform();
    
    // Mobile menu functionality
    const mobileMenuButton = document.querySelector('.mobile-menu-button');
    const mainNav = document.querySelector('.main-nav');
    
    if (mobileMenuButton && mainNav) {
        mobileMenuButton.addEventListener('click', function() {
            mainNav.classList.toggle('active');
            this.classList.toggle('active');
            
            // Add accessibility attributes
            if (mainNav.classList.contains('active')) {
                mobileMenuButton.setAttribute('aria-expanded', 'true');
            } else {
                mobileMenuButton.setAttribute('aria-expanded', 'false');
            }
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            if (!event.target.closest('.mobile-menu-button') && 
                !event.target.closest('.main-nav') && 
                mainNav.classList.contains('active')) {
                mainNav.classList.remove('active');
                mobileMenuButton.classList.remove('active');
                mobileMenuButton.setAttribute('aria-expanded', 'false');
            }
        });
        
        // Initialize accessibility attributes
        mobileMenuButton.setAttribute('aria-expanded', 'false');
        mobileMenuButton.setAttribute('aria-controls', 'main-nav');
        mobileMenuButton.setAttribute('aria-label', 'Toggle navigation menu');
    }
    
    // Dropdown menu functionality
    const dropdownToggles = document.querySelectorAll('.dropdown-toggle');
    
    dropdownToggles.forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Close all other dropdowns first
            document.querySelectorAll('.dropdown').forEach(dropdown => {
                if (dropdown !== this.closest('.dropdown') && dropdown.classList.contains('active')) {
                    dropdown.classList.remove('active');
                    const otherToggle = dropdown.querySelector('.dropdown-toggle');
                    if (otherToggle) otherToggle.setAttribute('aria-expanded', 'false');
                }
            });
            
            // Toggle current dropdown
            const dropdown = this.closest('.dropdown');
            dropdown.classList.toggle('active');
            
            // Set accessibility attributes
            if (dropdown.classList.contains('active')) {
                this.setAttribute('aria-expanded', 'true');
            } else {
                this.setAttribute('aria-expanded', 'false');
            }
        });
        
        // Initialize accessibility attributes
        toggle.setAttribute('aria-expanded', 'false');
        toggle.setAttribute('aria-haspopup', 'true');
        
        const dropdownMenu = toggle.nextElementSibling;
        if (dropdownMenu && dropdownMenu.classList.contains('dropdown-menu')) {
            const menuId = 'dropdown-menu-' + Math.random().toString(36).substr(2, 9);
            dropdownMenu.id = menuId;
            toggle.setAttribute('aria-controls', menuId);
        }
    });
    
    // Close dropdowns when clicking outside
    document.addEventListener('click', function(event) {
        if (!event.target.closest('.dropdown')) {
            document.querySelectorAll('.dropdown.active').forEach(dropdown => {
                dropdown.classList.remove('active');
                const toggle = dropdown.querySelector('.dropdown-toggle');
                if (toggle) toggle.setAttribute('aria-expanded', 'false');
            });
        }
    });
    
    // Add active class to current nav link
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPath || (href !== '/' && currentPath.startsWith(href))) {
            link.classList.add('active');
        }
    });
    
    // Fix header on scroll
    const header = document.querySelector('.app-header');
    let lastScrollTop = 0;
    
    window.addEventListener('scroll', function() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        if (scrollTop > 10) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
        
        lastScrollTop = scrollTop;
    });
});

// Audio Waveform Visualization
function initAudioWaveform() {
    const audioPlayers = document.querySelectorAll('.audio-player-container');
    
    audioPlayers.forEach(container => {
        const audioElement = container.querySelector('audio');
        const waveformContainer = container.querySelector('.waveform-container');
        const progressBar = container.querySelector('.progress-bar');
        
        if (!audioElement || !waveformContainer) return;
        
        // Get track ID from the audio element
        const trackId = audioElement.dataset.trackId;
        if (!trackId) return;
        
        // Fetch waveform data
        fetch(`/api/music/${trackId}/waveform`)
            .then(response => response.json())
            .then(waveformData => {
                renderWaveform(waveformContainer, waveformData, audioElement);
            })
            .catch(error => {
                console.error('Error fetching waveform data:', error);
            });
            
        // Waveform interactive events
        if (waveformContainer) {
            waveformContainer.addEventListener('click', function(e) {
                const rect = waveformContainer.getBoundingClientRect();
                const position = (e.clientX - rect.left) / rect.width;
                
                // Set audio position
                audioElement.currentTime = position * audioElement.duration;
                
                // Update progress bar
                if (progressBar) {
                    progressBar.style.width = `${position * 100}%`;
                }
            });
        }
        
        // Update progress during playback
        audioElement.addEventListener('timeupdate', function() {
            const progress = (audioElement.currentTime / audioElement.duration) * 100;
            if (progressBar) {
                progressBar.style.width = `${progress}%`;
            }
        });
    });
}

function renderWaveform(container, waveformData, audioElement) {
    const canvas = document.createElement('canvas');
    container.appendChild(canvas);
    
    const ctx = canvas.getContext('2d');
    const containerWidth = container.clientWidth;
    const containerHeight = container.clientHeight;
    
    // Set canvas dimensions
    canvas.width = containerWidth;
    canvas.height = containerHeight;
    
    // Sample the waveform data to match the canvas width
    const sampleRate = Math.ceil(waveformData.length / containerWidth);
    const sampledData = [];
    
    for (let i = 0; i < containerWidth; i++) {
        const dataIndex = Math.min(Math.floor(i * sampleRate), waveformData.length - 1);
        sampledData.push(waveformData[dataIndex]);
    }
    
    // Render the waveform
    ctx.clearRect(0, 0, containerWidth, containerHeight);
    ctx.beginPath();
    
    // Background for unplayed portion
    ctx.fillStyle = 'rgba(200, 200, 200, 0.2)';
    
    for (let i = 0; i < sampledData.length; i++) {
        const x = i;
        const amplitude = sampledData[i] * containerHeight * 0.4;
        const y = (containerHeight / 2) - amplitude;
        
        ctx.rect(x, y, 1, amplitude * 2); // Draw bars instead of a line
    }
    
    ctx.fill();
    
    // Create progress overlay
    const progressCanvas = document.createElement('canvas');
    progressCanvas.className = 'waveform-progress';
    progressCanvas.width = containerWidth;
    progressCanvas.height = containerHeight;
    container.appendChild(progressCanvas);
    
    const progressCtx = progressCanvas.getContext('2d');
    
    // Update progress on timeupdate
    audioElement.addEventListener('timeupdate', function() {
        const progress = audioElement.currentTime / audioElement.duration;
        const progressWidth = Math.floor(containerWidth * progress);
        
        progressCtx.clearRect(0, 0, containerWidth, containerHeight);
        progressCtx.beginPath();
        progressCtx.fillStyle = 'rgba(66, 133, 244, 0.6)';
        
        for (let i = 0; i < progressWidth; i++) {
            const x = i;
            const amplitude = sampledData[i] * containerHeight * 0.4;
            const y = (containerHeight / 2) - amplitude;
            
            progressCtx.rect(x, y, 1, amplitude * 2);
        }
        
        progressCtx.fill();
    });
} 