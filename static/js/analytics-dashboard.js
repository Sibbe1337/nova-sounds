/**
 * Analytics Dashboard JavaScript
 * Handles data loading, charts, and interactive elements for the analytics dashboard
 */

// Global variables to store dashboard data and state
let dashboardData = null;          // Current dashboard data
let previousPeriodData = null;     // Previous period data for comparison
let videoAnalytics = {};           // Analytics data for specific videos
let platformChart = null;          // Platform comparison chart instance
let historicalChart = null;        // Historical data chart instance
let heatmapChart = null;           // Engagement heatmap chart instance
let comparisonEnabled = false;     // Whether comparison mode is enabled

// WebSocket related variables
let wsConnection = null;           // WebSocket connection
let wsConnected = false;           // Connection status
let wsPingInterval = null;         // Interval for sending ping messages
let wsReconnectAttempts = 0;       // Count of reconnection attempts

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the dashboard
    initializeDashboard();
    
    // Set up event listeners
    document.getElementById('date-range').addEventListener('change', handleDateRangeChange);
    document.getElementById('chart-metric').addEventListener('change', updatePlatformChart);
    document.getElementById('historical-metric').addEventListener('change', updateHistoricalChart);
    document.getElementById('top-content-sort').addEventListener('change', updateTopContent);
    document.getElementById('top-content-platform').addEventListener('change', updateTopContent);
    
    // Export functionality
    document.getElementById('export-button').addEventListener('click', toggleExportMenu);
    document.getElementById('export-csv').addEventListener('click', () => exportData('csv'));
    document.getElementById('export-pdf').addEventListener('click', () => exportData('pdf'));
    document.getElementById('export-image').addEventListener('click', () => exportData('image'));
    
    // Comparison toggle
    document.getElementById('enable-comparison').addEventListener('change', toggleComparison);
    
    // Close export menu when clicking outside
    document.addEventListener('click', function(event) {
        const exportButton = document.getElementById('export-button');
        const exportMenu = document.querySelector('.export-menu');
        
        if (!exportButton.contains(event.target) && !exportMenu.contains(event.target)) {
            exportMenu.classList.remove('visible');
        }
    });
    
    if (document.getElementById('apply-date-range')) {
        document.getElementById('apply-date-range').addEventListener('click', applyCustomDateRange);
    }
});

/**
 * Initialize the dashboard by loading data and setting up charts
 */
async function initializeDashboard() {
    try {
        // Get selected date range
        const dateRange = document.getElementById('date-range').value;
        
        // Fetch dashboard data with retry and fallback
        let response;
        try {
            // Try fetching from API first
            console.log('Fetching dashboard data from API...');
            response = await fetch(`/analytics/dashboard?days=${dateRange}`);
            
            if (!response.ok) {
                throw new Error(`API responded with status: ${response.status}`);
            }
            
            dashboardData = await response.json();
        } catch (apiError) {
            console.warn('API fetch failed, using mock data:', apiError);
            // If API fails, use mock data
            dashboardData = getMockDashboardData();
        }
        
        console.log('Dashboard data loaded:', dashboardData);
        
        // Update stats cards
        updateStatsCards(dashboardData);
        
        // Create platform comparison chart
        createPlatformChart(dashboardData.platform_comparison);
        
        // Populate video selector
        populateVideoSelector(dashboardData.videos);
        
        // Display top content
        displayTopContent(dashboardData.top_content);
        
        // Show recommendations
        displayRecommendations(dashboardData.recommendations);
        
        // Create historical chart
        if (dashboardData.videos && dashboardData.videos.length > 0) {
            const firstVideoId = dashboardData.videos[0].id;
            await loadVideoAnalytics(firstVideoId);
        }
        
        // Initialize WebSocket connection for real-time updates
        initializeWebSocket();
    } catch (error) {
        console.error('Error initializing dashboard:', error);
        showError('Failed to load dashboard data. Please try again later.');
        
        // Attempt to load mock data as a fallback
        try {
            dashboardData = getMockDashboardData();
            updateStatsCards(dashboardData);
            createPlatformChart(dashboardData.platform_comparison);
            populateVideoSelector(dashboardData.videos);
            displayTopContent(dashboardData.top_content);
            displayRecommendations(dashboardData.recommendations);
        } catch (fallbackError) {
            console.error('Even fallback failed:', fallbackError);
        }
    }
}

/**
 * Generate mock dashboard data for testing
 */
function getMockDashboardData() {
    return {
        "success": true,
        "total_views": 139011,
        "total_engagement": 19549,
        "engagement_rate": 0.14,
        "avg_watch_time": 14.35,
        "total_subscribers": 6677,
        "platform_comparison": {
            "platforms": ["YouTube", "TikTok", "Instagram", "Facebook"],
            "views": [14360, 36186, 49446, 39019],
            "engagement": [2666, 5373, 6104, 5406]
        },
        "top_content": [
            {
                "id": "video_4",
                "title": "Easy 10-Minute Healthy Breakfast",
                "thumbnail": "https://example.com/thumbnails/thumb_4.jpg",
                "total_views": 17431,
                "total_engagement": 2118,
                "platforms": [{"platform": "YouTube", "views": 14934, "engagement": 2354, "watch_time": 151798, "ctr": 0.038}],
                "created_at": "2025-02-22T11:32:48.430969"
            },
            {
                "id": "video_5",
                "title": "Top 3 Productivity Tips",
                "thumbnail": "https://example.com/thumbnails/thumb_5.jpg",
                "total_views": 16602,
                "total_engagement": 3251,
                "platforms": [{"platform": "YouTube", "views": 8346, "engagement": 1469, "watch_time": 64358, "ctr": 0.083}],
                "created_at": "2025-03-08T11:32:48.430972"
            },
            {
                "id": "video_2",
                "title": "5 Exercises for a Strong Core",
                "thumbnail": "https://example.com/thumbnails/thumb_2.jpg",
                "total_views": 14435,
                "total_engagement": 2507,
                "platforms": [
                    {"platform": "YouTube", "views": 14292, "engagement": 2302, "watch_time": 203250, "ctr": 0.049},
                    {"platform": "TikTok", "views": 14017, "engagement": 2735, "watch_time": 143554, "ctr": 0.024}
                ],
                "created_at": "2025-02-26T11:32:48.430960"
            }
        ],
        "videos": [
            {
                "id": "video_4",
                "title": "Easy 10-Minute Healthy Breakfast",
                "thumbnail": "https://example.com/thumbnails/thumb_4.jpg",
                "total_views": 17431,
                "total_engagement": 2118,
                "platforms": [{"platform": "YouTube", "views": 14934, "engagement": 2354, "watch_time": 151798, "ctr": 0.038}],
                "created_at": "2025-02-22T11:32:48.430969"
            },
            {
                "id": "video_5",
                "title": "Top 3 Productivity Tips",
                "thumbnail": "https://example.com/thumbnails/thumb_5.jpg",
                "total_views": 16602,
                "total_engagement": 3251,
                "platforms": [{"platform": "YouTube", "views": 8346, "engagement": 1469, "watch_time": 64358, "ctr": 0.083}],
                "created_at": "2025-03-08T11:32:48.430972"
            }
        ],
        "recommendations": [
            {
                "type": "platform_focus",
                "title": "Focus on TikTok",
                "description": "Your content performs best on TikTok. Consider prioritizing this platform.",
                "confidence": 0.85
            },
            {
                "type": "content_length",
                "title": "Optimize video length",
                "description": "Videos between 15-30 seconds have the highest completion rate.",
                "confidence": 0.75
            },
            {
                "type": "posting_time",
                "title": "Best posting times",
                "description": "Post between 6-8 PM for maximum reach and engagement.",
                "confidence": 0.82
            }
        ]
    };
}

/**
 * Update the stats cards with the latest data
 */
function updateStatsCards(data) {
    // Format numbers for display
    const totalViewsEl = document.getElementById('total-views');
    const engagementRateEl = document.getElementById('engagement-rate');
    const avgWatchTimeEl = document.getElementById('avg-watch-time');
    const subscribersEl = document.getElementById('subscribers');
    
    // Clear skeleton loaders
    totalViewsEl.innerHTML = formatNumber(data.total_views);
    engagementRateEl.innerHTML = formatPercentage(data.engagement_rate);
    avgWatchTimeEl.innerHTML = formatTime(data.avg_watch_time);
    subscribersEl.innerHTML = formatNumber(data.total_subscribers);
    
    // Set trend indicators
    // In a real implementation, this would compare to previous period
    setTrendIndicator('views-trend', 0.15, '+15.2%');
    setTrendIndicator('engagement-trend', -0.02, '-2.3%');
    setTrendIndicator('watch-time-trend', 0.05, '+4.7%');
    setTrendIndicator('subscribers-trend', 0.08, '+8.1%');
}

/**
 * Create the platform comparison chart
 */
function createPlatformChart(platformData) {
    // Get the chart canvas
    const ctx = document.getElementById('platform-chart').getContext('2d');
    
    // Hide the loading skeleton
    const loadingEl = document.getElementById('platform-chart-loading');
    if (loadingEl) {
        loadingEl.style.display = 'none';
    }
    
    // Destroy existing chart if it exists
    if (platformChart) {
        platformChart.destroy();
    }
    
    // Apple-inspired color palette
    const colors = {
        blue: {
            primary: 'rgba(0, 122, 255, 0.8)',
            secondary: 'rgba(0, 122, 255, 0.2)'
        },
        green: {
            primary: 'rgba(52, 199, 89, 0.8)', 
            secondary: 'rgba(52, 199, 89, 0.2)'
        },
        orange: {
            primary: 'rgba(255, 149, 0, 0.8)',
            secondary: 'rgba(255, 149, 0, 0.2)'
        },
        purple: {
            primary: 'rgba(175, 82, 222, 0.8)',
            secondary: 'rgba(175, 82, 222, 0.2)'
        }
    };
    
    // Show the canvas
    document.getElementById('platform-chart').style.display = 'block';
    
    // Create the chart
    platformChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: platformData.platforms,
            datasets: [
                {
                    label: 'Views',
                    data: platformData.views,
                    backgroundColor: [
                        colors.blue.secondary,
                        colors.green.secondary,
                        colors.orange.secondary,
                        colors.purple.secondary
                    ],
                    borderColor: [
                        colors.blue.primary,
                        colors.green.primary,
                        colors.orange.primary,
                        colors.purple.primary
                    ],
                    borderWidth: 2,
                    borderRadius: 6,
                    barPercentage: 0.7,
                    categoryPercentage: 0.8
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleFont: {
                        size: 14,
                        weight: 'bold',
                        family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
                    },
                    bodyFont: {
                        size: 13,
                        family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
                    },
                    padding: 12,
                    cornerRadius: 8,
                    displayColors: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)',
                        drawBorder: false
                    },
                    border: {
                        display: false
                    },
                    ticks: {
                        font: {
                            family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
                            size: 12
                        },
                        color: 'rgba(0, 0, 0, 0.6)',
                        padding: 8,
                        callback: function(value) {
                            return formatNumber(value);
                        }
                    }
                },
                x: {
                    grid: {
                        display: false,
                        drawBorder: false
                    },
                    border: {
                        display: false
                    },
                    ticks: {
                        font: {
                            family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
                            size: 12
                        },
                        color: 'rgba(0, 0, 0, 0.6)',
                        padding: 8
                    }
                }
            },
            animation: {
                duration: 1500,
                easing: 'easeOutQuart'
            }
        }
    });
}

/**
 * Update the platform chart based on the selected metric
 */
function updatePlatformChart() {
    if (!dashboardData || !dashboardData.platform_comparison) return;
    
    const metric = document.getElementById('chart-metric').value;
    const platforms = dashboardData.platform_comparison.platforms;
    
    let chartData;
    let label;
    let color;
    
    switch (metric) {
        case 'views':
            chartData = dashboardData.platform_comparison.views;
            label = 'Views';
            color = 'rgba(54, 162, 235, 0.5)';
            borderColor = 'rgba(54, 162, 235, 1)';
            break;
        case 'engagement':
            chartData = dashboardData.platform_comparison.engagement;
            label = 'Engagement';
            color = 'rgba(255, 99, 132, 0.5)';
            borderColor = 'rgba(255, 99, 132, 1)';
            break;
        case 'watch_time':
            // In a real implementation, this would use actual watch time data
            chartData = dashboardData.platform_comparison.views.map(v => v * Math.random() * 10);
            label = 'Watch Time (mins)';
            color = 'rgba(75, 192, 192, 0.5)';
            borderColor = 'rgba(75, 192, 192, 1)';
            break;
        case 'growth':
            // In a real implementation, this would use actual growth data
            chartData = platforms.map(() => Math.random() * 20 - 5);
            label = 'Growth (%)';
            color = 'rgba(153, 102, 255, 0.5)';
            borderColor = 'rgba(153, 102, 255, 1)';
            break;
    }
    
    // Update chart data
    platformChart.data.datasets = [{
        label: label,
        data: chartData,
        backgroundColor: color,
        borderColor: borderColor,
        borderWidth: 1
    }];
    
    platformChart.update();
}

/**
 * Populate the video selector dropdown
 */
function populateVideoSelector(videos) {
    const selector = document.getElementById('heatmap-video-selector');
    
    // Clear existing options
    selector.innerHTML = '<option value="">Select a video</option>';
    
    // Add options for each video
    videos.forEach(video => {
        const option = document.createElement('option');
        option.value = video.id;
        option.textContent = video.title;
        selector.appendChild(option);
    });
    
    // Add event listener
    selector.addEventListener('change', handleVideoSelection);
}

/**
 * Handle video selection for the heatmap
 */
async function handleVideoSelection() {
    const videoId = document.getElementById('heatmap-video-selector').value;
    const platform = document.getElementById('heatmap-platform-selector').value;
    
    if (!videoId) return;
    
    try {
        // Load video analytics if not already loaded
        if (!videoAnalytics[videoId]) {
            await loadVideoAnalytics(videoId);
        }
        
        // Get heatmap data
        let heatmapData;
        try {
            // Try to fetch from API first
            const url = platform ? 
                `/analytics/engagement/${videoId}?platform=${platform}` : 
                `/analytics/engagement/${videoId}`;
                
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`API responded with status: ${response.status}`);
            }
            
            const data = await response.json();
            heatmapData = data.heatmap;
        } catch (apiError) {
            console.warn('API fetch failed for heatmap, using data from video analytics:', apiError);
            // If API fails, use data from video analytics
            heatmapData = videoAnalytics[videoId].heatmap;
        }
        
        // Create heatmap
        createHeatmap(heatmapData);
    } catch (error) {
        console.error('Error loading video analytics:', error);
        showError('Failed to load video analytics. Please try again later.');
        
        // Try to create a basic heatmap with mock data
        const mockHeatmap = {
            timestamps: Array.from({ length: 120 }, (_, i) => i),
            engagement: Array.from({ length: 120 }, () => Math.random() * 0.5 + 0.5)
        };
        createHeatmap(mockHeatmap);
    }
}

/**
 * Load analytics for a specific video
 */
async function loadVideoAnalytics(videoId) {
    try {
        let data;
        try {
            // Try fetching from API first
            console.log(`Fetching analytics for video ${videoId}`);
            const response = await fetch(`/analytics/videos/${videoId}`);
            
            if (!response.ok) {
                throw new Error(`API responded with status: ${response.status}`);
            }
            
            data = await response.json();
        } catch (apiError) {
            console.warn('API fetch failed for video analytics, using mock data:', apiError);
            // If API fails, use mock data
            data = getMockVideoAnalytics(videoId);
        }
        
        videoAnalytics[videoId] = data;
        
        // Create historical chart for the first video
        if (Object.keys(videoAnalytics).length === 1) {
            createHistoricalChart(data.historical_data);
        }
        
        return data;
    } catch (error) {
        console.error(`Error loading video analytics for ${videoId}:`, error);
        // Generate mock data as a fallback
        const mockData = getMockVideoAnalytics(videoId);
        videoAnalytics[videoId] = mockData;
        
        if (Object.keys(videoAnalytics).length === 1) {
            createHistoricalChart(mockData.historical_data);
        }
        
        return mockData;
    }
}

/**
 * Generate mock video analytics data for testing
 */
function getMockVideoAnalytics(videoId) {
    const now = new Date();
    const thirtyDaysAgo = new Date(now);
    thirtyDaysAgo.setDate(now.getDate() - 30);
    
    const historicalData = [];
    for (let i = 0; i < 30; i++) {
        const date = new Date(thirtyDaysAgo);
        date.setDate(thirtyDaysAgo.getDate() + i);
        
        historicalData.push({
            date: date.toISOString(),
            platform: 'YouTube',
            views: Math.floor(Math.random() * 1000) + 500,
            likes: Math.floor(Math.random() * 200) + 50,
            comments: Math.floor(Math.random() * 50) + 10,
            shares: Math.floor(Math.random() * 30) + 5,
            watch_time: Math.floor(Math.random() * 5000) + 2000
        });
        
        // Add some data for other platforms too
        if (i % 3 === 0) {
            historicalData.push({
                date: date.toISOString(),
                platform: 'TikTok',
                views: Math.floor(Math.random() * 1500) + 800,
                likes: Math.floor(Math.random() * 300) + 100,
                comments: Math.floor(Math.random() * 80) + 20,
                shares: Math.floor(Math.random() * 50) + 10,
                watch_time: Math.floor(Math.random() * 4000) + 1500
            });
        }
    }
    
    return {
        success: true,
        video: {
            id: videoId,
            title: `Sample Video ${videoId}`,
            thumbnail: 'https://example.com/thumbnails/sample.jpg',
            created_at: thirtyDaysAgo.toISOString(),
            duration: 120
        },
        platforms: [
            {
                platform: 'YouTube',
                views: 12500,
                likes: 2000,
                comments: 350,
                shares: 180,
                watch_time: 45000,
                ctr: 0.052,
                retention: { 
                    '0': 1.0, 
                    '30': 0.85, 
                    '60': 0.72, 
                    '90': 0.60, 
                    '120': 0.45 
                }
            },
            {
                platform: 'TikTok',
                views: 18500,
                likes: 3200,
                comments: 520,
                shares: 420,
                watch_time: 37000,
                ctr: 0.068,
                retention: { 
                    '0': 1.0, 
                    '30': 0.88, 
                    '60': 0.76, 
                    '90': 0.65, 
                    '120': 0.48 
                }
            }
        ],
        heatmap: {
            timestamps: Array.from({ length: 120 }, (_, i) => i),
            engagement: Array.from({ length: 120 }, () => Math.random() * 0.5 + 0.5)
        },
        historical_data: historicalData
    };
}

/**
 * Create the engagement heatmap visualization
 */
function createHeatmap(heatmapData) {
    const container = document.getElementById('heatmap-container');
    
    // Clear previous heatmap, including any skeleton loaders
    container.innerHTML = '';
    
    if (!heatmapData || !heatmapData.timestamps || !heatmapData.engagement) {
        container.innerHTML = '<div class="error-message">No heatmap data available</div>';
        return;
    }
    
    // Create the heatmap visualization
    const heatmapEl = document.createElement('div');
    heatmapEl.className = 'heatmap';
    
    const maxEngagement = Math.max(...heatmapData.engagement);
    
    heatmapData.timestamps.forEach((timestamp, index) => {
        const engagementValue = heatmapData.engagement[index];
        const intensity = engagementValue / maxEngagement;
        
        const bar = document.createElement('div');
        bar.className = 'heatmap-bar';
        
        // Start with height 0 and animate to full height
        bar.style.height = '0px';
        bar.style.backgroundColor = getHeatColor(intensity);
        
        // Add tooltip
        bar.title = `Time: ${formatTime(timestamp)} - Engagement: ${engagementValue.toFixed(2)}`;
        
        heatmapEl.appendChild(bar);
    });
    
    container.appendChild(heatmapEl);
    
    // Add labels and axis
    const labelsEl = document.createElement('div');
    labelsEl.className = 'heatmap-labels';
    
    // Add timestamp labels every 15 seconds
    const totalDuration = heatmapData.timestamps[heatmapData.timestamps.length - 1];
    const labelInterval = Math.ceil(totalDuration / 8);
    
    for (let i = 0; i <= totalDuration; i += labelInterval) {
        if (i <= totalDuration) {
            const label = document.createElement('span');
            label.className = 'timestamp-label';
            label.textContent = formatTime(i);
            label.style.left = `${(i / totalDuration) * 100}%`;
            labelsEl.appendChild(label);
        }
    }
    
    container.appendChild(labelsEl);
    
    // Animate bars to full height
    const bars = heatmapEl.querySelectorAll('.heatmap-bar');
    bars.forEach((bar, index) => {
        setTimeout(() => {
            const targetHeight = `${heatmapData.engagement[index] * 100}px`;
            bar.style.transition = 'height 0.6s cubic-bezier(0.2, 0.8, 0.2, 1)';
            bar.style.height = targetHeight;
        }, index * 15); // Stagger animation
    });
}

/**
 * Create historical performance chart
 */
function createHistoricalChart(historicalData) {
    // Get the chart canvas
    const ctx = document.getElementById('historical-chart').getContext('2d');
    
    // Hide the loading skeleton
    const loadingEl = document.getElementById('historical-chart-loading');
    if (loadingEl) {
        loadingEl.style.display = 'none';
    }
    
    // Show the canvas
    document.getElementById('historical-chart').style.display = 'block';
    
    // Destroy existing chart if it exists
    if (historicalChart) {
        historicalChart.destroy();
    }
    
    // Process and group data by platform
    const platforms = [...new Set(historicalData.map(item => item.platform))];
    const datasets = [];
    const colors = {
        YouTube: {
            line: 'rgba(255, 0, 0, 0.8)',
            fill: 'rgba(255, 0, 0, 0.1)'
        },
        TikTok: {
            line: 'rgba(0, 122, 255, 0.8)',
            fill: 'rgba(0, 122, 255, 0.1)'
        },
        Instagram: {
            line: 'rgba(138, 58, 185, 0.8)',
            fill: 'rgba(138, 58, 185, 0.1)'
        },
        Facebook: {
            line: 'rgba(66, 103, 178, 0.8)',
            fill: 'rgba(66, 103, 178, 0.1)'
        }
    };
    
    // Extract dates for labels
    const dates = [...new Set(historicalData.map(item => item.date))].sort();
    
    // Create datasets for each platform
    platforms.forEach(platform => {
        const platformData = historicalData.filter(item => item.platform === platform);
        const data = [];
        
        // Fill in data points for each date
        dates.forEach(date => {
            const dataPoint = platformData.find(item => item.date === date);
            data.push(dataPoint ? dataPoint.views : null);
        });
        
        datasets.push({
            label: platform,
            data: data,
            borderColor: colors[platform] ? colors[platform].line : 'rgba(52, 199, 89, 0.8)',
            backgroundColor: colors[platform] ? colors[platform].fill : 'rgba(52, 199, 89, 0.1)',
            borderWidth: 2,
            fill: true,
            tension: 0.4,
            pointRadius: 3,
            pointHoverRadius: 5,
            pointBackgroundColor: '#ffffff',
            pointHoverBackgroundColor: '#ffffff',
            pointBorderWidth: 2
        });
    });
    
    // Create the chart
    historicalChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    align: 'end',
                    labels: {
                        boxWidth: 12,
                        usePointStyle: true,
                        pointStyle: 'circle',
                        padding: 20,
                        font: {
                            family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
                            size: 12
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleFont: {
                        size: 14,
                        weight: 'bold',
                        family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
                    },
                    bodyFont: {
                        size: 13,
                        family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
                    },
                    padding: 12,
                    cornerRadius: 8,
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'day',
                        tooltipFormat: 'MMM D, YYYY',
                        displayFormats: {
                            day: 'MMM D'
                        }
                    },
                    grid: {
                        display: false,
                        drawBorder: false
                    },
                    border: {
                        display: false
                    },
                    ticks: {
                        maxRotation: 0,
                        autoSkip: true,
                        maxTicksLimit: 7,
                        font: {
                            family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
                            size: 12
                        },
                        color: 'rgba(0, 0, 0, 0.6)'
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)',
                        drawBorder: false
                    },
                    border: {
                        display: false
                    },
                    ticks: {
                        font: {
                            family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
                            size: 12
                        },
                        color: 'rgba(0, 0, 0, 0.6)',
                        padding: 8,
                        callback: function(value) {
                            return formatNumber(value);
                        }
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                intersect: false,
                axis: 'x'
            },
            animation: {
                duration: 1500,
                easing: 'easeOutQuart'
            }
        }
    });
}

/**
 * Update historical chart based on the selected metric
 */
function updateHistoricalChart() {
    if (!historicalChart || !Object.keys(videoAnalytics).length) return;
    
    const metric = document.getElementById('historical-metric').value;
    const videoId = Object.keys(videoAnalytics)[0]; // Use first loaded video
    const historicalData = videoAnalytics[videoId].historical_data;
    
    let chartData;
    let label;
    let color;
    
    switch (metric) {
        case 'views':
            chartData = historicalData.map(data => data.views);
            label = 'Views';
            color = 'rgba(54, 162, 235, 1)';
            backgroundColor = 'rgba(54, 162, 235, 0.1)';
            break;
        case 'engagement':
            chartData = historicalData.map(data => data.engagement);
            label = 'Engagement';
            color = 'rgba(255, 99, 132, 1)';
            backgroundColor = 'rgba(255, 99, 132, 0.1)';
            break;
        case 'watch_time':
            chartData = historicalData.map(data => data.watch_time);
            label = 'Watch Time (mins)';
            color = 'rgba(75, 192, 192, 1)';
            backgroundColor = 'rgba(75, 192, 192, 0.1)';
            break;
    }
    
    // Update chart data
    historicalChart.data.datasets[0].label = label;
    historicalChart.data.datasets[0].data = chartData;
    historicalChart.data.datasets[0].borderColor = color;
    historicalChart.data.datasets[0].backgroundColor = backgroundColor;
    
    // Update y-axis title
    historicalChart.options.scales.y.title.text = label;
    
    historicalChart.update();
}

/**
 * Display top performing content in the table
 */
function displayTopContent(content) {
    const tableBody = document.getElementById('top-content-table-body');
    
    // Clear any existing content (including skeleton loaders)
    tableBody.innerHTML = '';
    
    // If no content, show no data message
    if (!content || content.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = `<td colspan="7" class="no-data">No content data available</td>`;
        tableBody.appendChild(row);
        return;
    }
    
    // Add rows for each content item
    content.forEach(video => {
        const row = document.createElement('tr');
        
        // Video info cell
        const videoCell = document.createElement('td');
        videoCell.className = 'video-info';
        videoCell.innerHTML = `
            <img class="video-thumbnail" src="${video.thumbnail}" alt="${video.title}" />
            <div>
                <div class="video-title">${video.title}</div>
                <div class="video-date">${formatDate(video.created_at)}</div>
            </div>
        `;
        
        // Platforms
        const platformsMarkup = video.platforms.map(p => `<span class="platform-badge ${p.platform.toLowerCase()}">${p.platform}</span>`).join('');
        const platformCell = document.createElement('td');
        platformCell.innerHTML = platformsMarkup;
        
        // Views
        const viewsCell = document.createElement('td');
        viewsCell.textContent = formatNumber(video.total_views);
        
        // Engagement
        const engagementCell = document.createElement('td');
        engagementCell.textContent = formatNumber(video.total_engagement);
        
        // CTR (click-through rate)
        const ctrCell = document.createElement('td');
        const avgCTR = video.platforms.reduce((sum, p) => sum + (p.ctr || 0), 0) / video.platforms.length;
        ctrCell.textContent = formatPercentage(avgCTR);
        
        // Average watch time
        const watchTimeCell = document.createElement('td');
        const totalWatchTime = video.platforms.reduce((sum, p) => sum + (p.watch_time || 0), 0);
        const avgWatchTime = totalWatchTime / video.total_views;
        watchTimeCell.textContent = formatTime(avgWatchTime);
        
        // Actions
        const actionsCell = document.createElement('td');
        actionsCell.className = 'action-buttons';
        actionsCell.innerHTML = `
            <button class="view-details-btn" data-video-id="${video.id}">Details</button>
            <button class="share-btn" data-video-id="${video.id}">Share</button>
        `;
        
        // Add all cells to the row
        row.appendChild(videoCell);
        row.appendChild(platformCell);
        row.appendChild(viewsCell);
        row.appendChild(engagementCell);
        row.appendChild(ctrCell);
        row.appendChild(watchTimeCell);
        row.appendChild(actionsCell);
        
        // Add hover animation
        row.style.opacity = '0';
        row.style.transform = 'translateY(10px)';
        
        tableBody.appendChild(row);
        
        // Trigger animation after a small delay based on index
        setTimeout(() => {
            row.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            row.style.opacity = '1';
            row.style.transform = 'translateY(0)';
        }, 50 * tableBody.children.length);
    });
    
    // Add event listeners
    const detailButtons = document.querySelectorAll('.view-details-btn');
    detailButtons.forEach(btn => {
        btn.addEventListener('click', handleViewDetails);
    });
    
    const shareButtons = document.querySelectorAll('.share-btn');
    shareButtons.forEach(btn => {
        btn.addEventListener('click', handleShare);
    });
}

/**
 * Display content recommendations
 */
function displayRecommendations(recommendations) {
    const container = document.getElementById('recommendations-list');
    
    // Clear the container (including skeleton loaders)
    container.innerHTML = '';
    
    // If no recommendations, show empty state
    if (!recommendations || recommendations.length === 0) {
        container.innerHTML = '<div class="no-recommendations">No recommendations available at this time</div>';
        return;
    }
    
    // Add recommendations
    recommendations.forEach((recommendation, index) => {
        const confidenceLevel = recommendation.confidence >= 0.8 ? 'high' : 
                                recommendation.confidence >= 0.6 ? 'medium' : 'low';
        
        const card = document.createElement('div');
        card.className = `recommendation-card ${confidenceLevel}`;
        card.innerHTML = `
            <div class="recommendation-title">
                ${recommendation.title}
                <span class="recommendation-confidence">${Math.round(recommendation.confidence * 100)}% confidence</span>
            </div>
            <div class="recommendation-description">${recommendation.description}</div>
        `;
        
        // Add animation
        card.style.opacity = '0';
        card.style.transform = 'translateY(10px)';
        
        container.appendChild(card);
        
        // Trigger animation after a small delay based on index
        setTimeout(() => {
            card.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 100 * index);
    });
}

/**
 * Handle view details button click
 */
function handleViewDetails(event) {
    const videoId = event.target.getAttribute('data-video-id');
    // In a real implementation, this would navigate to a details page or open a modal
    alert(`View details for video ${videoId}`);
}

/**
 * Handle share button click
 */
function handleShare(event) {
    const videoId = event.target.getAttribute('data-video-id');
    // In a real implementation, this would open a share dialog
    alert(`Share video ${videoId}`);
}

/**
 * Update the top content based on sort and filter selections
 */
function updateTopContent() {
    if (!dashboardData || !dashboardData.videos) return;
    
    const sortBy = document.getElementById('top-content-sort').value;
    const platform = document.getElementById('top-content-platform').value;
    
    // Filter videos by platform if selected
    let filteredVideos = [...dashboardData.videos];
    if (platform) {
        filteredVideos = filteredVideos.filter(video => {
            return video.platforms && video.platforms.some(p => p.platform.toLowerCase() === platform.toLowerCase());
        });
    }
    
    // Sort videos by selected metric
    switch (sortBy) {
        case 'views':
            filteredVideos.sort((a, b) => b.total_views - a.total_views);
            break;
        case 'engagement':
            filteredVideos.sort((a, b) => b.total_engagement - a.total_engagement);
            break;
        case 'ctr':
            filteredVideos.sort((a, b) => {
                const ctrA = a.total_views > 0 ? a.total_engagement / a.total_views : 0;
                const ctrB = b.total_views > 0 ? b.total_engagement / b.total_views : 0;
                return ctrB - ctrA;
            });
            break;
        case 'watch_time':
            filteredVideos.sort((a, b) => {
                const watchTimeA = getAverageWatchTimeValue(a);
                const watchTimeB = getAverageWatchTimeValue(b);
                return watchTimeB - watchTimeA;
            });
            break;
    }
    
    // Display top 5 videos
    displayTopContent(filteredVideos.slice(0, 5));
}

/**
 * Handle date range change
 */
function handleDateRangeChange() {
    const selectElement = document.getElementById('date-range');
    const selectedValue = selectElement.value;
    
    if (selectedValue === 'custom') {
        document.getElementById('custom-date-range').classList.remove('hidden');
    } else {
        document.getElementById('custom-date-range').classList.add('hidden');
        loadDashboardWithDays(parseInt(selectedValue, 10));
        
        // Update WebSocket subscription with new timeframe
        if (wsConnected && wsConnection && wsConnection.readyState === WebSocket.OPEN) {
            wsConnection.send(JSON.stringify({
                type: 'subscribe',
                topic: 'dashboard',
                days: parseInt(selectedValue, 10)
            }));
        }
    }
}

/**
 * Apply custom date range
 */
function applyCustomDateRange() {
    const fromDate = document.getElementById('date-from').value;
    const toDate = document.getElementById('date-to').value;
    
    if (!fromDate || !toDate) {
        alert('Please select both start and end dates');
        return;
    }
    
    // Calculate days
    const from = new Date(fromDate);
    const to = new Date(toDate);
    const days = Math.ceil((to - from) / (1000 * 60 * 60 * 24));
    
    if (days < 1) {
        alert('End date must be after start date');
        return;
    }
    
    // Reload dashboard with calculated days
    loadDashboardWithDays(days);
}

/**
 * Load dashboard with specified days
 */
async function loadDashboardWithDays(days) {
    try {
        // Show loading states
        setLoadingState(true);
        
        // Fetch dashboard data
        const response = await fetch(`/analytics/dashboard?days=${days}`);
        
        if (!response.ok) {
            throw new Error(`API responded with status: ${response.status}`);
        }
        
        dashboardData = await response.json();
        
        // Update all dashboard components
        updateStatsCards(dashboardData);
        createPlatformChart(dashboardData.platform_comparison);
        populateVideoSelector(dashboardData.videos);
        displayTopContent(dashboardData.top_content);
        displayRecommendations(dashboardData.recommendations);
        
        // Reset video analytics
        videoAnalytics = {};
        
        // Load first video analytics
        if (dashboardData.videos && dashboardData.videos.length > 0) {
            await loadVideoAnalytics(dashboardData.videos[0].id);
        }
        
        // Hide loading states
        setLoadingState(false);
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showError('Failed to load dashboard data. Please try again later.');
        setLoadingState(false);
    }
}

/**
 * Set loading state for dashboard components
 */
function setLoadingState(isLoading) {
    const loadingElements = [
        { id: 'total-views', text: 'Loading...' },
        { id: 'engagement-rate', text: 'Loading...' },
        { id: 'avg-watch-time', text: 'Loading...' },
        { id: 'subscribers', text: 'Loading...' }
    ];
    
    loadingElements.forEach(element => {
        const el = document.getElementById(element.id);
        if (el) {
            el.textContent = isLoading ? element.text : '';
        }
    });
    
    // Table loading state
    const tableBody = document.getElementById('top-content-table-body');
    if (tableBody && isLoading) {
        tableBody.innerHTML = '<tr class="loading-row"><td colspan="7">Loading content data...</td></tr>';
    }
    
    // Recommendations loading state
    const recommendationsList = document.getElementById('recommendations-list');
    if (recommendationsList && isLoading) {
        recommendationsList.innerHTML = '<div class="loading-recommendations">Loading recommendations...</div>';
    }
}

/**
 * Set trend indicator with proper icons and styling
 */
function setTrendIndicator(elementId, percentChange, displayText = null) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    // Clear previous content
    element.innerHTML = '';
    
    // Create the arrow icon
    const iconSpan = document.createElement('span');
    iconSpan.className = 'trend-icon';
    
    // Create the text span
    const textSpan = document.createElement('span');
    textSpan.className = 'trend-text';
    textSpan.textContent = displayText || `${Math.abs(percentChange * 100).toFixed(1)}%`;
    
    if (percentChange > 0) {
        element.className = 'trend-indicator up';
        iconSpan.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 4L20 12L17 12L17 20L7 20L7 12L4 12L12 4Z" fill="currentColor"/>
        </svg>`;
    } else if (percentChange < 0) {
        element.className = 'trend-indicator down';
        iconSpan.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 20L4 12L7 12L7 4L17 4L17 12L20 12L12 20Z" fill="currentColor"/>
        </svg>`;
    } else {
        element.className = 'trend-indicator neutral';
        iconSpan.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M4 12L8 12L16 12L20 12" stroke="currentColor" stroke-width="2"/>
        </svg>`;
        textSpan.textContent = 'No change';
    }
    
    // Append the elements
    element.appendChild(iconSpan);
    element.appendChild(textSpan);
    
    // Add animation
    element.style.animation = 'fadeIn 0.5s ease-out forwards';
}

/**
 * Get confidence class based on confidence value
 */
function getConfidenceClass(confidence) {
    if (confidence >= 0.8) {
        return 'high';
    } else if (confidence >= 0.6) {
        return 'medium';
    } else {
        return 'low';
    }
}

/**
 * Calculate average watch time for a video
 */
function getAverageWatchTime(video) {
    if (!video.platforms || video.platforms.length === 0) {
        return 'N/A';
    }
    
    let totalWatchTime = 0;
    let platformCount = 0;
    
    video.platforms.forEach(platform => {
        if (platform.watch_time) {
            totalWatchTime += platform.watch_time;
            platformCount++;
        }
    });
    
    if (platformCount === 0) {
        return 'N/A';
    }
    
    return formatTime(totalWatchTime / platformCount);
}

/**
 * Get average watch time value for sorting
 */
function getAverageWatchTimeValue(video) {
    if (!video.platforms || video.platforms.length === 0) {
        return 0;
    }
    
    let totalWatchTime = 0;
    let platformCount = 0;
    
    video.platforms.forEach(platform => {
        if (platform.watch_time) {
            totalWatchTime += platform.watch_time;
            platformCount++;
        }
    });
    
    return platformCount > 0 ? totalWatchTime / platformCount : 0;
}

/**
 * Show an error message
 */
function showError(message) {
    // You could implement a toast notification system here
    console.error(message);
    alert(message);
}

/**
 * Format a number for display
 */
function formatNumber(number) {
    if (number === undefined || number === null) return 'N/A';
    
    // Format with commas for thousands
    if (number >= 1000000) {
        return (number / 1000000).toFixed(1) + 'M';
    } else if (number >= 1000) {
        return (number / 1000).toFixed(1) + 'K';
    } else {
        return number.toString();
    }
}

/**
 * Format a percentage for display
 */
function formatPercentage(value) {
    if (value === undefined || value === null) return 'N/A';
    return (value * 100).toFixed(1) + '%';
}

/**
 * Format a time value for display
 */
function formatTime(seconds) {
    if (seconds === undefined || seconds === null) return 'N/A';
    
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

/**
 * Format a date for display
 */
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
    });
}

/**
 * Generate a color for the heatmap based on engagement intensity
 */
function getHeatColor(intensity) {
    // Generate a color from blue (low) to red (high)
    const hue = (1 - intensity) * 240; // 240 is blue, 0 is red
    return `hsl(${hue}, 80%, 60%)`;
}

/**
 * Toggle the export menu visibility
 */
function toggleExportMenu(event) {
    event.stopPropagation();
    const exportMenu = document.querySelector('.export-menu');
    exportMenu.classList.toggle('visible');
    
    if (!exportMenu.classList.contains('visible')) {
        exportMenu.classList.add('hidden');
    } else {
        exportMenu.classList.remove('hidden');
    }
}

/**
 * Export data in different formats
 */
async function exportData(format) {
    // Hide the export menu
    document.querySelector('.export-menu').classList.remove('visible');
    document.querySelector('.export-menu').classList.add('hidden');
    
    // Show loading state
    const exportButton = document.getElementById('export-button');
    const originalText = exportButton.innerHTML;
    exportButton.innerHTML = `<span class="loading-spinner"></span> Exporting...`;
    exportButton.disabled = true;
    
    try {
        switch (format) {
            case 'csv':
                await exportCSV();
                break;
            case 'pdf':
                await exportPDF();
                break;
            case 'image':
                await exportImage();
                break;
        }
        showNotification('Export successful!');
    } catch (error) {
        console.error('Export failed:', error);
        showNotification('Export failed. Please try again.', 'error');
    } finally {
        // Restore button state
        exportButton.innerHTML = originalText;
        exportButton.disabled = false;
    }
}

/**
 * Export data as CSV
 */
async function exportCSV() {
    const data = [];
    const header = ['Metric', 'Value'];
    
    // Add overall stats
    data.push(['Total Views', dashboardData.total_views]);
    data.push(['Engagement Rate', dashboardData.engagement_rate]);
    data.push(['Avg. Watch Time', dashboardData.avg_watch_time]);
    data.push(['Total Subscribers', dashboardData.total_subscribers]);
    
    // Add platform data
    data.push(['', '']); // Empty row as separator
    data.push(['Platform', 'Views', 'Engagement']);
    
    dashboardData.platform_comparison.platforms.forEach((platform, index) => {
        data.push([
            platform,
            dashboardData.platform_comparison.views[index],
            dashboardData.platform_comparison.engagement[index]
        ]);
    });
    
    // Add top videos
    data.push(['', '']); // Empty row as separator
    data.push(['Video Title', 'Views', 'Engagement', 'Platform']);
    
    dashboardData.top_content.forEach(video => {
        video.platforms.forEach(platform => {
            data.push([
                video.title,
                platform.views,
                platform.engagement,
                platform.platform
            ]);
        });
    });
    
    // Convert to CSV
    let csvContent = '';
    data.forEach(row => {
        csvContent += row.join(',') + '\n';
    });
    
    // Create and download file
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const filename = `analytics_dashboard_${new Date().toISOString().split('T')[0]}.csv`;
    
    if (navigator.msSaveBlob) { // IE 10+
        navigator.msSaveBlob(blob, filename);
    } else {
        const url = URL.createObjectURL(blob);
        link.href = url;
        link.setAttribute('download', filename);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

/**
 * Export dashboard as PDF
 */
async function exportPDF() {
    // Create a PDF document
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF('p', 'mm', 'a4');
    
    // Capture each section as image
    const dashboard = document.querySelector('.analytics-dashboard');
    const cards = document.querySelector('.stats-cards');
    const platformChart = document.getElementById('platform-chart-container');
    const topContent = document.querySelector('.table-container');
    
    // Add title
    doc.setFontSize(20);
    doc.text('Analytics Dashboard', 15, 15);
    doc.setFontSize(12);
    doc.text(`Generated on ${new Date().toLocaleDateString()}`, 15, 22);
    
    try {
        // Cards section
        const cardsCanvas = await html2canvas(cards, { scale: 2 });
        const cardsImgData = cardsCanvas.toDataURL('image/png');
        doc.addImage(cardsImgData, 'PNG', 15, 30, 180, 40);
        
        // Platform chart
        const chartCanvas = await html2canvas(platformChart, { scale: 2 });
        const chartImgData = chartCanvas.toDataURL('image/png');
        doc.addImage(chartImgData, 'PNG', 15, 75, 180, 70);
        
        // Save the PDF
        const filename = `analytics_dashboard_${new Date().toISOString().split('T')[0]}.pdf`;
        doc.save(filename);
    } catch (error) {
        console.error('PDF export error:', error);
        throw error;
    }
}

/**
 * Export dashboard as image
 */
async function exportImage() {
    try {
        const dashboard = document.querySelector('.analytics-dashboard');
        const canvas = await html2canvas(dashboard, { 
            scale: 2,
            logging: false,
            useCORS: true
        });
        
        const imgData = canvas.toDataURL('image/png');
        const link = document.createElement('a');
        link.href = imgData;
        link.download = `analytics_dashboard_${new Date().toISOString().split('T')[0]}.png`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    } catch (error) {
        console.error('Image export error:', error);
        throw error;
    }
}

/**
 * Toggle period comparison
 */
function toggleComparison(event) {
    comparisonEnabled = event.target.checked;
    const comparisonInfo = document.getElementById('comparison-info');
    
    if (comparisonEnabled) {
        comparisonInfo.classList.remove('hidden');
        fetchComparisonData();
    } else {
        comparisonInfo.classList.add('hidden');
        // Reset to single period display
        updateChartsForSinglePeriod();
    }
}

/**
 * Fetch data for the comparison period
 */
async function fetchComparisonData() {
    try {
        // Determine comparison period
        const currentPeriod = document.getElementById('date-range').value;
        let days = parseInt(currentPeriod);
        
        // Update labels
        document.getElementById('current-period-label').textContent = getPeriodLabel(days);
        document.getElementById('previous-period-label').textContent = `Previous ${days} days`;
        
        // In a real implementation, this would fetch from API
        // Here we'll use mock data for demo purposes
        previousPeriodData = await getPreviousPeriodData(days);
        
        // Update charts with comparison data
        updateChartsWithComparison();
    } catch (error) {
        console.error('Error fetching comparison data:', error);
        showNotification('Failed to load comparison data', 'error');
    }
}

/**
 * Get previous period data
 */
async function getPreviousPeriodData(days) {
    // In a real implementation, this would be an API call
    // Here we'll generate mock data based on current data
    
    // Apply a random factor to make previous period different
    const randomFactor = 0.7 + Math.random() * 0.6; // Between 0.7 and 1.3
    
    return {
        success: true,
        total_views: Math.floor(dashboardData.total_views * randomFactor),
        total_engagement: Math.floor(dashboardData.total_engagement * randomFactor),
        engagement_rate: dashboardData.engagement_rate * randomFactor,
        avg_watch_time: dashboardData.avg_watch_time * randomFactor,
        total_subscribers: Math.floor(dashboardData.total_subscribers * 0.9), // Assuming growth
        platform_comparison: {
            platforms: dashboardData.platform_comparison.platforms,
            views: dashboardData.platform_comparison.views.map(v => Math.floor(v * randomFactor)),
            engagement: dashboardData.platform_comparison.engagement.map(e => Math.floor(e * randomFactor))
        },
        top_content: dashboardData.top_content,
        videos: dashboardData.videos,
        recommendations: []
    };
}

/**
 * Update charts to include comparison data
 */
function updateChartsWithComparison() {
    // Update stats cards with comparison
    updateStatsCardsWithComparison();
    
    // Update platform chart
    updatePlatformChartWithComparison();
    
    // Update historical chart
    updateHistoricalChartWithComparison();
}

/**
 * Update stats cards to show comparison with previous period
 */
function updateStatsCardsWithComparison() {
    if (!dashboardData || !previousPeriodData) return;
    
    // Calculate percent changes
    const viewsChange = calculatePercentChange(
        dashboardData.total_views, 
        previousPeriodData.total_views
    );
    
    const engagementRateChange = calculatePercentChange(
        dashboardData.engagement_rate, 
        previousPeriodData.engagement_rate
    );
    
    const watchTimeChange = calculatePercentChange(
        dashboardData.avg_watch_time, 
        previousPeriodData.avg_watch_time
    );
    
    const subscribersChange = calculatePercentChange(
        dashboardData.total_subscribers, 
        previousPeriodData.total_subscribers
    );
    
    // Update trend indicators with actual data
    setTrendIndicator('views-trend', viewsChange);
    setTrendIndicator('engagement-trend', engagementRateChange);
    setTrendIndicator('watch-time-trend', watchTimeChange);
    setTrendIndicator('subscribers-trend', subscribersChange);
}

/**
 * Update platform chart to show comparison
 */
function updatePlatformChartWithComparison() {
    if (!platformChart || !previousPeriodData) return;
    
    const metric = document.getElementById('chart-metric').value;
    const platforms = dashboardData.platform_comparison.platforms;
    
    let currentData, previousData;
    let label = '';
    
    switch (metric) {
        case 'views':
            currentData = dashboardData.platform_comparison.views;
            previousData = previousPeriodData.platform_comparison.views;
            label = 'Views';
            break;
        case 'engagement':
            currentData = dashboardData.platform_comparison.engagement;
            previousData = previousPeriodData.platform_comparison.engagement;
            label = 'Engagement';
            break;
        // Add other metrics as needed
    }
    
    // Update chart with both datasets
    platformChart.data.datasets = [
        {
            label: `Current Period: ${label}`,
            data: currentData,
            backgroundColor: 'rgba(0, 122, 255, 0.2)',
            borderColor: 'rgba(0, 122, 255, 0.8)',
            borderWidth: 2,
            borderRadius: 6,
            barPercentage: 0.7,
            categoryPercentage: 0.8
        },
        {
            label: `Previous Period: ${label}`,
            data: previousData,
            backgroundColor: 'rgba(90, 200, 250, 0.2)',
            borderColor: 'rgba(90, 200, 250, 0.8)',
            borderWidth: 2,
            borderRadius: 6,
            barPercentage: 0.7,
            categoryPercentage: 0.8
        }
    ];
    
    platformChart.update();
}

/**
 * Update historical chart with comparison data
 */
function updateHistoricalChartWithComparison() {
    // In a real implementation, this would add previous period data
    // to the historical chart
    // For this demo, we're focusing on the platform chart comparison
}

/**
 * Calculate percent change between two values
 */
function calculatePercentChange(current, previous) {
    if (previous === 0) return 0;
    return (current - previous) / previous;
}

/**
 * Update charts to remove comparison data
 */
function updateChartsForSinglePeriod() {
    // Update the platform chart
    updatePlatformChart();
    
    // Update the historical chart
    if (dashboardData && dashboardData.videos && dashboardData.videos.length > 0) {
        const firstVideoId = dashboardData.videos[0].id;
        if (videoAnalytics[firstVideoId]) {
            createHistoricalChart(videoAnalytics[firstVideoId].historical_data);
        }
    }
    
    // Reset trend indicators to defaults
    setTrendIndicator('views-trend', 0.15, '+15.2%');
    setTrendIndicator('engagement-trend', -0.02, '-2.3%');
    setTrendIndicator('watch-time-trend', 0.05, '+4.7%');
    setTrendIndicator('subscribers-trend', 0.08, '+8.1%');
}

/**
 * Get a human-readable period label
 */
function getPeriodLabel(days) {
    switch (days) {
        case 7:
            return 'Last 7 days';
        case 30:
            return 'Last 30 days';
        case 90:
            return 'Last 90 days';
        default:
            return `Last ${days} days`;
    }
}

/**
 * Show a toast notification
 * 
 * @param {string} message - The message to display
 * @param {string} type - The notification type (success, error, info)
 */
function showNotification(message, type = 'success') {
    // Create notification container if it doesn't exist
    let notificationsContainer = document.getElementById('notifications-container');
    if (!notificationsContainer) {
        notificationsContainer = document.createElement('div');
        notificationsContainer.id = 'notifications-container';
        notificationsContainer.style.position = 'fixed';
        notificationsContainer.style.bottom = '24px';
        notificationsContainer.style.right = '24px';
        notificationsContainer.style.zIndex = '1000';
        document.body.appendChild(notificationsContainer);
    }
    
    // Create the notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    // Notification icon based on type
    let iconSvg;
    if (type === 'success') {
        iconSvg = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M20 6L9 17L4 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>`;
    } else if (type === 'error') {
        iconSvg = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 8V12M12 16H12.01M22 12C22 17.5228 17.5228 22 12 22C6.47715 22 2 17.5228 2 12C2 6.47715 6.47715 2 12 2C17.5228 2 22 6.47715 22 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>`;
    } else if (type === 'info') {
        iconSvg = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 16V12M12 8H12.01M22 12C22 17.5228 17.5228 22 12 22C6.47715 22 2 17.5228 2 12C2 6.47715 6.47715 2 12 2C17.5228 2 22 6.47715 22 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>`;
    }
    
    // Notification content
    notification.innerHTML = `
        <div class="notification-icon">${iconSvg}</div>
        <div class="notification-content">${message}</div>
        <div class="notification-close">×</div>
    `;
    
    // Add to container
    notificationsContainer.appendChild(notification);
    
    // Make visible after a brief delay (for animation)
    setTimeout(() => {
        notification.classList.add('visible');
    }, 10);
    
    // Close button event
    const closeButton = notification.querySelector('.notification-close');
    closeButton.addEventListener('click', () => {
        notification.classList.remove('visible');
        setTimeout(() => {
            notification.remove();
        }, 300);
    });
    
    // Auto-close after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.classList.remove('visible');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 300);
        }
    }, 5000);
}

/**
 * Initialize WebSocket connection for real-time analytics updates
 */
function initializeWebSocket() {
    // Create WebSocket URL (handle http/https)
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/analytics`;
    
    // Close existing connection if any
    if (wsConnection) {
        wsConnection.close();
        clearInterval(wsPingInterval);
    }
    
    // Create WebSocket connection
    wsConnection = new WebSocket(wsUrl);
    
    // Connection opened
    wsConnection.addEventListener('open', (event) => {
        console.log('Connected to analytics WebSocket server');
        wsConnected = true;
        
        // Reset reconnection attempts on successful connection
        wsReconnectAttempts = 0;
        
        // Update UI to show connected status
        updateConnectionStatus(true);
        
        // Subscribe to dashboard updates with current timeframe
        const days = document.getElementById('date-range').value;
        wsConnection.send(JSON.stringify({
            type: 'subscribe',
            topic: 'dashboard',
            days: parseInt(days, 10)
        }));
        
        // Subscribe to recent data
        wsConnection.send(JSON.stringify({
            type: 'subscribe',
            topic: 'recent',
            limit: 5
        }));
        
        // Start ping interval to keep connection alive
        startWebSocketPing();
        
        // Show connection notification
        showNotification('Connected to real-time updates', 'success');
    });
    
    // Listen for messages from server
    wsConnection.addEventListener('message', (event) => {
        try {
            const message = JSON.parse(event.data);
            
            if (message.type === 'update') {
                handleWebSocketUpdate(message);
            } else if (message.type === 'error') {
                console.error('WebSocket error:', message.message);
                showNotification(message.message, 'error');
            } else if (message.type === 'pong') {
                // Pong received, connection is alive
                console.log('Heartbeat received', message.timestamp);
            }
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    });
    
    // Connection closed
    wsConnection.addEventListener('close', (event) => {
        console.log('Disconnected from WebSocket server');
        wsConnected = false;
        updateConnectionStatus(false);
        
        // Clear ping interval
        if (wsPingInterval) {
            clearInterval(wsPingInterval);
        }
        
        // Implement exponential backoff for reconnection
        const maxReconnectDelay = 30000; // 30 seconds max
        const baseReconnectDelay = 1000; // Start with 1 second
        wsReconnectAttempts++;
        
        // Calculate delay with exponential backoff and jitter
        const exponentialDelay = Math.min(
            maxReconnectDelay, 
            baseReconnectDelay * Math.pow(2, wsReconnectAttempts - 1)
        );
        
        // Add some random jitter (±20%)
        const jitter = exponentialDelay * 0.2 * (Math.random() * 2 - 1);
        const reconnectDelay = Math.max(1000, exponentialDelay + jitter);
        
        console.log(`Attempting to reconnect in ${Math.round(reconnectDelay/1000)} seconds (attempt ${wsReconnectAttempts})...`);
        
        // Show notification if this was an unexpected disconnect
        if (wsReconnectAttempts === 1) {
            showNotification('Connection lost. Attempting to reconnect...', 'error');
        }
        
        // Try to reconnect after calculated delay
        setTimeout(() => {
            console.log('Attempting to reconnect...');
            initializeWebSocket();
        }, reconnectDelay);
    });
    
    // Connection error
    wsConnection.addEventListener('error', (event) => {
        console.error('WebSocket error:', event);
        wsConnected = false;
        updateConnectionStatus(false);
    });
}

/**
 * Update connection status indicator
 */
function updateConnectionStatus(connected) {
    // Create or update connection status indicator
    let statusIndicator = document.getElementById('connection-status');
    
    if (!statusIndicator) {
        statusIndicator = document.createElement('div');
        statusIndicator.id = 'connection-status';
        statusIndicator.className = 'connection-status';
        
        // Add to dashboard header
        const dashboardControls = document.querySelector('.dashboard-controls');
        dashboardControls.appendChild(statusIndicator);
    }
    
    if (connected) {
        statusIndicator.className = 'connection-status connected';
        statusIndicator.innerHTML = '<div class="status-dot"></div><span>Live</span>';
        statusIndicator.title = 'Connected to real-time updates';
    } else {
        statusIndicator.className = 'connection-status disconnected';
        statusIndicator.innerHTML = '<div class="status-dot"></div><span>Offline</span>';
        statusIndicator.title = 'Disconnected from real-time updates';
    }
}

/**
 * Start sending periodic pings to keep the WebSocket connection alive
 */
function startWebSocketPing() {
    // Clear any existing interval
    if (wsPingInterval) {
        clearInterval(wsPingInterval);
    }
    
    // Send ping every 30 seconds
    wsPingInterval = setInterval(() => {
        if (wsConnected && wsConnection && wsConnection.readyState === WebSocket.OPEN) {
            wsConnection.send(JSON.stringify({
                type: 'ping',
                timestamp: new Date().toISOString()
            }));
        }
    }, 30000);
}

/**
 * Handle WebSocket update messages
 */
function handleWebSocketUpdate(message) {
    const { topic, data } = message;
    
    if (topic === 'dashboard') {
        console.log('Received dashboard update:', data);
        
        // Update dashboard data
        dashboardData = data;
        
        // Update UI components
        updateStatsCards(data);
        createPlatformChart(data.platform_comparison);
        displayTopContent(data.top_content);
        displayRecommendations(data.recommendations);
        
        // Show notification
        showNotification('Dashboard data updated', 'info');
    } 
    else if (topic === 'recent') {
        console.log('Received recent data update:', data);
        // Update recent data if implemented
        showNotification('Recent data updated', 'info');
    }
} 