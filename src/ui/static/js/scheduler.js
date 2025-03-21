// Scheduling Calendar UI
// Allows users to schedule their Shorts for publishing

class SchedulerCalendar {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.events = [];
        this.selectedDate = null;
        this.selectedTime = null;
        this.selectedPlatforms = [];
        this.calendarInstance = null;
        
        // Default options
        this.options = {
            minDate: new Date(),
            maxDaysAhead: 90,
            defaultView: 'dayGridMonth',
            timeSlots: [
                '08:00', '09:00', '10:00', '11:00', '12:00',
                '13:00', '14:00', '15:00', '16:00', '17:00',
                '18:00', '19:00', '20:00', '21:00', '22:00'
            ],
            platforms: [
                { id: 'tiktok', name: 'TikTok', icon: 'bi-tiktok', color: '#000000' },
                { id: 'youtube', name: 'YouTube', icon: 'bi-youtube', color: '#FF0000' },
                { id: 'instagram', name: 'Instagram', icon: 'bi-instagram', color: '#E1306C' },
                { id: 'facebook', name: 'Facebook', icon: 'bi-facebook', color: '#4267B2' }
            ],
            onScheduleSelect: null,
            onScheduleSave: null,
            apiEndpoint: '/api/publishing/schedule',
            timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            ...options
        };
        
        // Initialize UI
        this.initialize();
    }
    
    initialize() {
        if (!this.container) {
            console.error(`Container element with ID "${this.containerId}" not found`);
            return;
        }
        
        // Create UI
        this.createUI();
        
        // Load existing schedules
        this.loadSchedules();
    }
    
    createUI() {
        this.container.innerHTML = `
            <div class="publishing-scheduler-container">
                <div class="row">
                    <div class="col-md-8">
                        <div class="card mb-3">
                            <div class="card-header d-flex justify-content-between align-items-center">
                                <h5 class="mb-0">
                                    <i class="bi bi-calendar-event me-2"></i>Publishing Schedule
                                </h5>
                                <div class="form-check form-switch">
                                    <input class="form-check-input" type="checkbox" id="optimal-time-switch">
                                    <label class="form-check-label" for="optimal-time-switch">Use Optimal Times</label>
                                </div>
                            </div>
                            <div class="card-body">
                                <div id="publishing-calendar"></div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-header">
                                <h5 class="mb-0">Schedule Details</h5>
                            </div>
                            <div class="card-body">
                                <div class="selected-date-container mb-3">
                                    <label class="form-label">Selected Date</label>
                                    <div class="input-group">
                                        <span class="input-group-text"><i class="bi bi-calendar-date"></i></span>
                                        <input type="text" class="form-control" id="schedule-selected-date" 
                                               placeholder="Select a date" readonly>
                                    </div>
                                </div>
                                
                                <div class="time-slots-container mb-3">
                                    <label class="form-label">Time Slot</label>
                                    <div class="mb-2" id="schedule-time-slots"></div>
                                    
                                    <div class="custom-time-container mt-2 d-flex gap-2">
                                        <div class="input-group">
                                            <span class="input-group-text"><i class="bi bi-clock"></i></span>
                                            <input type="time" class="form-control" id="custom-time-input">
                                        </div>
                                        <button class="btn btn-outline-primary" id="custom-time-btn">
                                            Set
                                        </button>
                                    </div>
                                </div>
                                
                                <div class="platform-selection-container mb-3">
                                    <label class="form-label">Platforms</label>
                                    <div class="platform-options" id="schedule-platforms">
                                        ${this.options.platforms.map(platform => `
                                            <div class="form-check form-check-inline">
                                                <input class="form-check-input" type="checkbox" 
                                                       id="platform-${platform.id}" value="${platform.id}">
                                                <label class="form-check-label" for="platform-${platform.id}">
                                                    <i class="bi ${platform.icon} me-1" style="color: ${platform.color}"></i> ${platform.name}
                                                </label>
                                            </div>
                                        `).join('')}
                                    </div>
                                </div>
                                
                                <div class="optimal-time-recommendations d-none mb-3" id="optimal-time-recommendations">
                                    <div class="alert alert-info">
                                        <h6><i class="bi bi-lightning-charge"></i> Optimal Posting Times</h6>
                                        <div id="optimal-times-content"></div>
                                    </div>
                                </div>
                                
                                <button type="button" class="btn btn-primary w-100" id="schedule-save-btn" disabled>
                                    Schedule Publishing
                                </button>
                            </div>
                        </div>
                        
                        <div class="card mt-3">
                            <div class="card-header">
                                <h5 class="mb-0">Upcoming Publications</h5>
                            </div>
                            <div class="card-body p-0">
                                <ul class="list-group list-group-flush" id="upcoming-publications">
                                    <li class="list-group-item text-center text-muted py-3">
                                        Loading scheduled posts...
                                    </li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Store references to DOM elements - now using the new IDs
        this.selectedDateEl = document.getElementById('schedule-selected-date');
        this.timeSlotsContainer = document.getElementById('schedule-time-slots');
        this.platformsContainer = document.getElementById('schedule-platforms');
        this.saveScheduleBtn = document.getElementById('schedule-save-btn');
        this.optimalTimeSwitch = document.getElementById('optimal-time-switch');
        this.optimalTimeRecommendations = document.getElementById('optimal-time-recommendations');
        this.optimalTimesContent = document.getElementById('optimal-times-content');
        this.customTimeInput = document.getElementById('custom-time-input');
        this.customTimeBtn = document.getElementById('custom-time-btn');
        this.upcomingPublicationsList = document.getElementById('upcoming-publications');
        
        // Set up time slots
        this.createTimeSlots();
        
        // Initialize date picker using Flatpickr
        this.initDatePicker();
        
        // Initialize FullCalendar
        this.initCalendar();
        
        // Add event listeners
        this.addEventListeners();
    }
    
    initDatePicker() {
        const today = new Date();
        const maxDate = new Date();
        maxDate.setDate(today.getDate() + this.options.maxDaysAhead);
        
        this.datepicker = flatpickr(this.selectedDateEl, {
            minDate: today,
            maxDate: maxDate,
            dateFormat: "Y-m-d",
            onChange: (selectedDates, dateStr) => {
                this.selectedDate = selectedDates[0];
                this.updateTimeSlots();
                this.checkFormValidity();
                
                if (this.optimalTimeSwitch.checked) {
                    this.showOptimalTimes(this.selectedDate);
                }
            }
        });
    }
    
    initCalendar() {
        const calendarEl = document.getElementById('publishing-calendar');
        
        this.calendarInstance = new FullCalendar.Calendar(calendarEl, {
            initialView: this.options.defaultView,
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek'
            },
            height: 'auto',
            selectable: true,
            selectMirror: true,
            navLinks: true,
            timeZone: this.options.timeZone,
            businessHours: {
                daysOfWeek: [0, 1, 2, 3, 4, 5, 6],
                startTime: '08:00',
                endTime: '22:00',
            },
            select: (info) => {
                const selectedDate = info.start;
                if (selectedDate < new Date()) {
                    this.calendarInstance.unselect();
                    return;
                }
                
                this.datepicker.setDate(selectedDate);
                this.selectedDate = selectedDate;
                this.updateTimeSlots();
                this.checkFormValidity();
                
                if (this.optimalTimeSwitch.checked) {
                    this.showOptimalTimes(selectedDate);
                }
            },
            eventClick: (info) => {
                this.showEventDetails(info.event);
            },
            events: this.events,
            validRange: {
                start: new Date()
            }
        });
        
        this.calendarInstance.render();
    }
    
    createTimeSlots() {
        this.timeSlotsContainer.innerHTML = '';
        
        const timeSlotsList = document.createElement('div');
        timeSlotsList.className = 'time-slots-list d-flex flex-wrap gap-2';
        
        this.options.timeSlots.forEach(timeSlot => {
            const timeButton = document.createElement('button');
            timeButton.type = 'button';
            timeButton.className = 'btn btn-outline-secondary btn-sm time-slot-btn';
            timeButton.dataset.time = timeSlot;
            timeButton.textContent = this.formatTime(timeSlot);
            
            timeButton.addEventListener('click', () => {
                this.selectTimeSlot(timeSlot);
            });
            
            timeSlotsList.appendChild(timeButton);
        });
        
        this.timeSlotsContainer.appendChild(timeSlotsList);
    }
    
    formatTime(timeString) {
        const timeParts = timeString.split(':');
        const hour = parseInt(timeParts[0]);
        const minute = timeParts[1] || '00';
        
        const period = hour >= 12 ? 'PM' : 'AM';
        const displayHour = hour % 12 || 12;
        
        return `${displayHour}:${minute} ${period}`;
    }
    
    updateTimeSlots() {
        // Remove active class from all time slots
        const timeSlotBtns = this.timeSlotsContainer.querySelectorAll('.time-slot-btn');
        timeSlotBtns.forEach(btn => {
            btn.classList.remove('active');
            btn.classList.remove('btn-primary');
            btn.classList.add('btn-outline-secondary');
        });
        
        // Check for conflicts and disable time slots that are already scheduled
        if (this.selectedDate) {
            const selectedDateStr = this.selectedDate.toISOString().split('T')[0];
            
            timeSlotBtns.forEach(btn => {
                const timeSlot = btn.dataset.time;
                const isConflict = this.checkTimeConflict(selectedDateStr, timeSlot);
                
                if (isConflict) {
                    btn.disabled = true;
                    btn.title = 'Already scheduled';
                } else {
                    btn.disabled = false;
                    btn.title = '';
                }
            });
        }
    }
    
    selectTimeSlot(timeSlot) {
        // Clear any previous selection
        const timeSlotBtns = this.timeSlotsContainer.querySelectorAll('.time-slot-btn');
        timeSlotBtns.forEach(btn => {
            btn.classList.remove('active');
            btn.classList.remove('btn-primary');
            btn.classList.add('btn-outline-secondary');
        });
        
        // Set the new selection
        this.selectedTime = timeSlot;
        
        // Update UI
        const selectedBtn = this.timeSlotsContainer.querySelector(`.time-slot-btn[data-time="${timeSlot}"]`);
        if (selectedBtn) {
            selectedBtn.classList.add('active');
            selectedBtn.classList.add('btn-primary');
            selectedBtn.classList.remove('btn-outline-secondary');
        }
        
        // Reset custom time input
        this.customTimeInput.value = '';
        
        this.checkFormValidity();
    }
    
    addEventListeners() {
        // Optimal time switch
        this.optimalTimeSwitch.addEventListener('change', () => {
            if (this.optimalTimeSwitch.checked) {
                this.showOptimalTimes(this.selectedDate);
            } else {
                this.optimalTimeRecommendations.classList.add('d-none');
            }
        });
        
        // Custom time button
        this.customTimeBtn.addEventListener('click', () => {
            const customTime = this.customTimeInput.value;
            if (customTime) {
                this.selectTimeSlot(customTime);
            }
        });
        
        // Platform checkboxes
        const platformCheckboxes = this.platformsContainer.querySelectorAll('input[type="checkbox"]');
        platformCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.updateSelectedPlatforms();
                this.checkFormValidity();
            });
        });
        
        // Save button
        this.saveScheduleBtn.addEventListener('click', () => {
            this.saveSchedule();
        });
    }
    
    updateSelectedPlatforms() {
        this.selectedPlatforms = [];
        const platformCheckboxes = this.platformsContainer.querySelectorAll('input[type="checkbox"]:checked');
        
        platformCheckboxes.forEach(checkbox => {
            this.selectedPlatforms.push(checkbox.value);
        });
    }
    
    checkFormValidity() {
        const isValid = this.selectedDate && this.selectedTime && this.selectedPlatforms.length > 0;
        this.saveScheduleBtn.disabled = !isValid;
    }
    
    checkTimeConflict(date, time) {
        return this.events.some(event => {
            const eventDate = event.start.toISOString().split('T')[0];
            const eventTime = event.start.toISOString().split('T')[1].substring(0, 5);
            
            return eventDate === date && eventTime === time;
        });
    }
    
    async loadSchedules() {
        try {
            const response = await fetch('/api/publishing/schedules');
            
            if (!response.ok) {
                throw new Error(`Failed to load schedules: ${response.status}`);
            }
            
            const data = await response.json();
            this.events = data.schedules.map(schedule => this.formatEvent(schedule));
            
            // Update calendar with events
            this.calendarInstance.removeAllEvents();
            this.calendarInstance.addEventSource(this.events);
            
            // Update upcoming publications
            this.updateUpcomingPublications();
            
        } catch (error) {
            console.error('Error loading schedules:', error);
            this.upcomingPublicationsList.innerHTML = `
                <li class="list-group-item text-center text-danger py-3">
                    <i class="bi bi-exclamation-circle me-1"></i>
                    Failed to load scheduled posts
                </li>
            `;
        }
    }
    
    formatEvent(schedule) {
        const startTime = new Date(`${schedule.date}T${schedule.time}`);
        
        return {
            id: schedule.id,
            title: schedule.title || 'Scheduled Post',
            start: startTime,
            allDay: false,
            backgroundColor: this.getPlatformColor(schedule.platforms[0]),
            textColor: '#FFFFFF',
            borderColor: this.getPlatformColor(schedule.platforms[0]),
            extendedProps: {
                platforms: schedule.platforms,
                videoId: schedule.videoId,
                status: schedule.status || 'pending'
            }
        };
    }
    
    getPlatformColor(platformId) {
        const platform = this.options.platforms.find(p => p.id === platformId);
        return platform ? platform.color : '#6c757d';
    }
    
    getPlatformIcon(platformId) {
        const platform = this.options.platforms.find(p => p.id === platformId);
        return platform ? platform.icon : 'bi-question-circle';
    }
    
    updateUpcomingPublications() {
        // Sort events by date
        const sortedEvents = [...this.events].sort((a, b) => a.start - b.start);
        
        // Only show upcoming events
        const upcomingEvents = sortedEvents.filter(event => event.start >= new Date());
        
        if (upcomingEvents.length === 0) {
            this.upcomingPublicationsList.innerHTML = `
                <li class="list-group-item text-center text-muted py-3">
                    No upcoming scheduled posts
                </li>
            `;
            return;
        }
        
        // Show only the next 5 events
        const displayEvents = upcomingEvents.slice(0, 5);
        
        this.upcomingPublicationsList.innerHTML = '';
        
        displayEvents.forEach(event => {
            const eventDate = event.start;
            const formattedDate = eventDate.toLocaleDateString(undefined, { 
                weekday: 'short', 
                month: 'short', 
                day: 'numeric' 
            });
            const formattedTime = eventDate.toLocaleTimeString(undefined, { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
            
            const listItem = document.createElement('li');
            listItem.className = 'list-group-item py-2';
            
            const platformIcons = event.extendedProps.platforms.map(platformId => {
                return `<i class="bi ${this.getPlatformIcon(platformId)}" style="color: ${this.getPlatformColor(platformId)}"></i>`;
            }).join(' ');
            
            const statusBadge = `<span class="badge bg-${this.getStatusColor(event.extendedProps.status)}">${event.extendedProps.status}</span>`;
            
            listItem.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <div class="fw-bold">${event.title}</div>
                        <div class="small">
                            <i class="bi bi-calendar-event me-1"></i>${formattedDate} 
                            <i class="bi bi-clock ms-2 me-1"></i>${formattedTime}
                        </div>
                    </div>
                    <div>
                        <div class="platform-icons mb-1">${platformIcons}</div>
                        <div class="text-end">${statusBadge}</div>
                    </div>
                </div>
            `;
            
            listItem.addEventListener('click', () => {
                this.showEventDetails(event);
            });
            
            this.upcomingPublicationsList.appendChild(listItem);
        });
    }
    
    getStatusColor(status) {
        switch (status.toLowerCase()) {
            case 'published': return 'success';
            case 'pending': return 'warning';
            case 'failed': return 'danger';
            case 'scheduled': return 'info';
            default: return 'secondary';
        }
    }
    
    showEventDetails(event) {
        // Implementation for showing event details
        // Could display a modal with full details about the scheduled post
        const eventDate = event.start;
        const formattedDate = eventDate.toLocaleDateString(undefined, { 
            weekday: 'long', 
            year: 'numeric',
            month: 'long', 
            day: 'numeric' 
        });
        const formattedTime = eventDate.toLocaleTimeString(undefined, { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        const platformNames = event.extendedProps.platforms.map(platformId => {
            const platform = this.options.platforms.find(p => p.id === platformId);
            return platform ? platform.name : platformId;
        }).join(', ');
        
        // In a real implementation, this would display a modal with the details
        alert(`
Scheduled Post Details:
Title: ${event.title}
Date: ${formattedDate}
Time: ${formattedTime}
Platforms: ${platformNames}
Status: ${event.extendedProps.status}
        `);
    }
    
    showOptimalTimes(date) {
        if (!date) {
            this.optimalTimeRecommendations.classList.add('d-none');
            return;
        }
        
        // In a real implementation, this would call an API to get optimal posting times
        // For now, we'll simulate some recommendations
        
        const dayOfWeek = date.getDay();
        const recommendations = [
            { platform: 'instagram', times: ['12:00', '15:00', '18:00', '21:00'] },
            { platform: 'tiktok', times: ['09:00', '15:00', '19:00', '22:00'] },
            { platform: 'youtube', times: ['15:00', '18:00', '20:00'] },
            { platform: 'facebook', times: ['13:00', '16:00', '19:00'] }
        ];
        
        // Show recommendations
        this.optimalTimesContent.innerHTML = '';
        
        recommendations.forEach(rec => {
            const platform = this.options.platforms.find(p => p.id === rec.platform);
            if (!platform) return;
            
            const recElement = document.createElement('div');
            recElement.className = 'mb-2 small';
            
            const timeBadges = rec.times.map(time => {
                return `<span class="badge bg-light text-dark me-1 time-recommendation" data-time="${time}" style="border-left: 3px solid ${platform.color}; cursor: pointer;">${this.formatTime(time)}</span>`;
            }).join(' ');
            
            recElement.innerHTML = `
                <div><i class="bi ${platform.icon} me-1" style="color: ${platform.color}"></i> <strong>${platform.name}</strong></div>
                <div class="mt-1">${timeBadges}</div>
            `;
            
            this.optimalTimesContent.appendChild(recElement);
        });
        
        // Add event listeners to time recommendations
        const timeBadges = this.optimalTimesContent.querySelectorAll('.time-recommendation');
        timeBadges.forEach(badge => {
            badge.addEventListener('click', (e) => {
                const time = e.target.dataset.time;
                this.selectTimeSlot(time);
            });
        });
        
        this.optimalTimeRecommendations.classList.remove('d-none');
    }
    
    async saveSchedule() {
        if (!this.selectedDate || !this.selectedTime || this.selectedPlatforms.length === 0) {
            alert('Please select a date, time, and at least one platform');
            return;
        }
        
        // Format date and time for API
        const dateStr = this.selectedDate.toISOString().split('T')[0];
        const combinedDate = new Date(`${dateStr}T${this.selectedTime}`);
        
        // Get video data
        const videoId = window.currentVideoId || 'demo-video-id';
        const videoTitle = window.currentVideoTitle || 'My Awesome Video';
        
        // Prepare payload
        const scheduleData = {
            videoId: videoId,
            title: videoTitle,
            date: dateStr,
            time: this.selectedTime,
            platforms: this.selectedPlatforms,
            scheduled_at: combinedDate.toISOString(),
            timeZone: this.options.timeZone
        };
        
        try {
            // Show loading state
            this.saveScheduleBtn.disabled = true;
            this.saveScheduleBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Scheduling...';
            
            // Call API (or trigger callback)
            if (typeof this.options.onScheduleSave === 'function') {
                await this.options.onScheduleSave(scheduleData);
            } else {
                const response = await fetch(this.options.apiEndpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(scheduleData)
                });
                
                if (!response.ok) {
                    throw new Error(`Failed to schedule: ${response.status}`);
                }
                
                const data = await response.json();
                scheduleData.id = data.scheduleId || `schedule-${Date.now()}`;
                scheduleData.status = 'scheduled';
            }
            
            // Add new event
            const newEvent = this.formatEvent(scheduleData);
            this.events.push(newEvent);
            
            // Update calendar
            this.calendarInstance.addEvent(newEvent);
            
            // Update upcoming publications
            this.updateUpcomingPublications();
            
            // Reset form
            this.resetForm();
            
            // Show success message
            alert('Successfully scheduled for publishing!');
            
        } catch (error) {
            console.error('Error scheduling publication:', error);
            alert(`Failed to schedule publication: ${error.message}`);
        } finally {
            // Reset button state
            this.saveScheduleBtn.disabled = false;
            this.saveScheduleBtn.innerHTML = 'Schedule Publishing';
            
            // Check form validity
            this.checkFormValidity();
        }
    }
    
    resetForm() {
        // Clear date selection
        this.datepicker.clear();
        this.selectedDate = null;
        
        // Clear time selection
        this.selectedTime = null;
        this.updateTimeSlots();
        
        // Clear platform selection
        const platformCheckboxes = this.platformsContainer.querySelectorAll('input[type="checkbox"]:checked');
        platformCheckboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
        this.selectedPlatforms = [];
        
        // Disable save button
        this.saveScheduleBtn.disabled = true;
    }
}

// Export the class for use in other modules
window.SchedulerCalendar = SchedulerCalendar; 