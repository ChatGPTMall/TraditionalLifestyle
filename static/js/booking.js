/**
 * TraditionalLifestyle Booking System
 * Interactive multi-step booking form with real-time slot availability
 */

class BookingSystem {
    constructor(options = {}) {
        this.apiBaseUrl = options.apiBaseUrl || '/booking/api';
        this.currentStep = 1;
        this.totalSteps = 4;
        this.bookingData = {
            service: null,
            staff: null,
            date: null,
            time: null,
            slot_id: null
        };
        this.holdId = null;
        this.holdTimer = null;
        this.holdExpiry = null;

        // Calendar state
        this.currentMonth = new Date().getMonth();
        this.currentYear = new Date().getFullYear();
        this.availableDates = [];
        this.availableSlots = [];

        this.init();
    }

    init() {
        this.cacheElements();
        this.bindEvents();
        this.initFromUrlParams();
        this.updateUI();
    }

    cacheElements() {
        // Step indicators
        this.stepIndicators = document.querySelectorAll('.step-indicator');
        this.stepContents = document.querySelectorAll('.booking-step');

        // Service selection
        this.serviceCards = document.querySelectorAll('.service-card');

        // Staff selection
        this.staffCards = document.querySelectorAll('.staff-card');
        this.anyStaffOption = document.getElementById('any-staff-option');

        // Calendar
        this.calendarGrid = document.getElementById('calendar-grid');
        this.calendarMonth = document.getElementById('calendar-month');
        this.prevMonthBtn = document.getElementById('prev-month');
        this.nextMonthBtn = document.getElementById('next-month');

        // Time slots
        this.timeSlotsContainer = document.getElementById('time-slots');
        this.selectedDateDisplay = document.getElementById('selected-date-display');

        // Confirmation display
        this.confirmService = document.getElementById('confirm-service');
        this.confirmStaff = document.getElementById('confirm-staff');
        this.confirmDate = document.getElementById('confirm-date');
        this.confirmTime = document.getElementById('confirm-time');
        this.confirmPrice = document.getElementById('confirm-price');

        // Hold timer
        this.holdTimerDisplay = document.getElementById('hold-timer');

        // Hidden form fields
        this.serviceInput = document.getElementById('service-input');
        this.staffInput = document.getElementById('staff-input');
        this.slotInput = document.getElementById('slot-input');
        this.dateInput = document.getElementById('date-input');
        this.timeInput = document.getElementById('time-input');

        // Form container
        this.formContainer = document.querySelector('.booking-form-container');
    }

    bindEvents() {
        // Use event delegation for navigation buttons
        if (this.formContainer) {
            this.formContainer.addEventListener('click', (e) => {
                // Check for navigation buttons using classes
                if (e.target.closest('.btn-primary') && e.target.closest('.booking-nav')) {
                    const btn = e.target.closest('.btn-primary');
                    if (btn.id === 'submit-btn') {
                        // Let form submit naturally
                        return;
                    }
                    e.preventDefault();
                    this.nextStep();
                }

                if (e.target.closest('.btn-secondary') && e.target.closest('.booking-nav')) {
                    e.preventDefault();
                    this.prevStep();
                }
            });
        }

        // Service selection
        this.serviceCards.forEach(card => {
            card.addEventListener('click', () => this.selectService(card));
        });

        // Staff selection
        this.staffCards.forEach(card => {
            card.addEventListener('click', () => this.selectStaff(card));
        });
        if (this.anyStaffOption) {
            this.anyStaffOption.addEventListener('click', () => this.selectAnyStaff());
        }

        // Calendar navigation
        if (this.prevMonthBtn) {
            this.prevMonthBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.changeMonth(-1);
            });
        }
        if (this.nextMonthBtn) {
            this.nextMonthBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.changeMonth(1);
            });
        }

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.holdId) {
                this.releaseHold();
            }
        });

        // Page unload - release hold
        window.addEventListener('beforeunload', () => {
            if (this.holdId) {
                this.releaseHold();
            }
        });
    }

    initFromUrlParams() {
        const params = new URLSearchParams(window.location.search);

        // Pre-select service from URL
        const serviceId = params.get('service');
        if (serviceId) {
            const serviceCard = document.querySelector(`.service-card[data-service-id="${serviceId}"]`);
            if (serviceCard) {
                this.selectService(serviceCard, false);
            }
        }

        // Pre-select staff from URL
        const staffId = params.get('staff');
        if (staffId) {
            const staffCard = document.querySelector(`.staff-card[data-staff-id="${staffId}"]`);
            if (staffCard) {
                this.selectStaff(staffCard, false);
            }
        }

        // Auto-advance if both are pre-selected
        if (serviceId && staffId) {
            this.currentStep = 3;
            this.loadAvailableDates();
        } else if (serviceId) {
            this.currentStep = 2;
        }
    }

    // Step Navigation
    prevStep() {
        if (this.currentStep > 1) {
            // Release hold when going back from confirmation
            if (this.currentStep === 4 && this.holdId) {
                this.releaseHold();
            }
            this.currentStep--;
            this.updateUI();
        }
    }

    async nextStep() {
        if (!this.validateCurrentStep()) {
            return;
        }

        if (this.currentStep < this.totalSteps) {
            this.currentStep++;

            // Load data for next step
            if (this.currentStep === 3) {
                await this.loadAvailableDates();
            } else if (this.currentStep === 4) {
                await this.holdSlot();
                this.updateConfirmation();
            }

            this.updateUI();
        }
    }

    validateCurrentStep() {
        switch (this.currentStep) {
            case 1:
                if (!this.bookingData.service) {
                    this.showError('Please select a service');
                    return false;
                }
                break;
            case 2:
                // Staff is optional - "any available" is valid
                break;
            case 3:
                if (!this.bookingData.date || !this.bookingData.time) {
                    this.showError('Please select a date and time');
                    return false;
                }
                break;
        }
        return true;
    }

    updateUI() {
        // Update step indicators
        this.stepIndicators.forEach((indicator, index) => {
            const stepNum = index + 1;
            indicator.classList.remove('active', 'completed');

            if (stepNum === this.currentStep) {
                indicator.classList.add('active');
            } else if (stepNum < this.currentStep) {
                indicator.classList.add('completed');
            }
        });

        // Show/hide step content
        this.stepContents.forEach((content, index) => {
            const stepNum = index + 1;
            if (stepNum === this.currentStep) {
                content.classList.add('active');
                content.style.display = 'block';
            } else {
                content.classList.remove('active');
                content.style.display = 'none';
            }
        });

        // Scroll to top of form
        if (this.formContainer) {
            this.formContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    // Service Selection
    selectService(card, advance = true) {
        // Remove selection from other cards
        this.serviceCards.forEach(c => c.classList.remove('selected'));

        // Add selection to clicked card
        card.classList.add('selected');

        // Store service data
        this.bookingData.service = {
            id: card.dataset.serviceId,
            name: card.dataset.serviceName,
            duration: card.dataset.serviceDuration,
            price: card.dataset.servicePrice
        };

        // Update hidden input
        if (this.serviceInput) {
            this.serviceInput.value = this.bookingData.service.id;
        }

        // Filter staff by service capability
        this.filterStaffByService(this.bookingData.service.id);

        // Auto-advance
        if (advance) {
            setTimeout(() => this.nextStep(), 300);
        }
    }

    filterStaffByService(serviceId) {
        this.staffCards.forEach(card => {
            const services = card.dataset.staffServices?.split(',') || [];
            if (services.includes(serviceId) || services.length === 0 || services[0] === '') {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
                card.classList.remove('selected');
            }
        });
    }

    // Staff Selection
    selectStaff(card, advance = true) {
        // Remove selection from other cards
        this.staffCards.forEach(c => c.classList.remove('selected'));
        if (this.anyStaffOption) {
            this.anyStaffOption.classList.remove('selected');
        }

        // Add selection to clicked card
        card.classList.add('selected');

        // Store staff data
        this.bookingData.staff = {
            id: card.dataset.staffId,
            name: card.dataset.staffName
        };

        // Update hidden input
        if (this.staffInput) {
            this.staffInput.value = this.bookingData.staff.id;
        }

        // Auto-advance
        if (advance) {
            setTimeout(() => this.nextStep(), 300);
        }
    }

    selectAnyStaff() {
        // Remove selection from staff cards
        this.staffCards.forEach(c => c.classList.remove('selected'));

        // Add selection to any option
        if (this.anyStaffOption) {
            this.anyStaffOption.classList.add('selected');
        }

        // Clear staff data
        this.bookingData.staff = null;

        // Update hidden input
        if (this.staffInput) {
            this.staffInput.value = '';
        }

        // Auto-advance
        setTimeout(() => this.nextStep(), 300);
    }

    // Calendar & Date Selection
    async loadAvailableDates() {
        this.showLoading(this.calendarGrid);

        try {
            const params = new URLSearchParams({
                service: this.bookingData.service.id,
                month: this.currentMonth + 1,
                year: this.currentYear
            });

            if (this.bookingData.staff) {
                params.append('staff', this.bookingData.staff.id);
            }

            const response = await fetch(`${this.apiBaseUrl}/available-dates/?${params}`);
            const data = await response.json();

            if (data.success) {
                this.availableDates = data.dates || [];
            } else {
                this.availableDates = [];
            }
        } catch (error) {
            console.error('Error loading available dates:', error);
            this.availableDates = [];
        }

        this.renderCalendar();
    }

    changeMonth(delta) {
        this.currentMonth += delta;

        if (this.currentMonth > 11) {
            this.currentMonth = 0;
            this.currentYear++;
        } else if (this.currentMonth < 0) {
            this.currentMonth = 11;
            this.currentYear--;
        }

        // Don't allow past months
        const now = new Date();
        if (this.currentYear < now.getFullYear() ||
            (this.currentYear === now.getFullYear() && this.currentMonth < now.getMonth())) {
            this.currentMonth = now.getMonth();
            this.currentYear = now.getFullYear();
            return;
        }

        this.loadAvailableDates();
    }

    renderCalendar() {
        const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
                          'July', 'August', 'September', 'October', 'November', 'December'];

        // Update month display
        if (this.calendarMonth) {
            this.calendarMonth.textContent = `${monthNames[this.currentMonth]} ${this.currentYear}`;
        }

        // Get first day of month and total days
        const firstDay = new Date(this.currentYear, this.currentMonth, 1).getDay();
        const daysInMonth = new Date(this.currentYear, this.currentMonth + 1, 0).getDate();
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        let html = '';

        // Day headers
        const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        dayNames.forEach(day => {
            html += `<div class="calendar-header-day">${day}</div>`;
        });

        // Empty cells before first day
        for (let i = 0; i < firstDay; i++) {
            html += '<div class="calendar-day empty"></div>';
        }

        // Days of month
        for (let day = 1; day <= daysInMonth; day++) {
            const date = new Date(this.currentYear, this.currentMonth, day);
            const dateStr = this.formatDate(date);
            const isPast = date < today;
            const isAvailable = this.availableDates.includes(dateStr);
            const isSelected = this.bookingData.date === dateStr;

            let classes = 'calendar-day';
            if (isPast) classes += ' past';
            else if (!isAvailable) classes += ' unavailable';
            else classes += ' available';
            if (isSelected) classes += ' selected';

            const clickHandler = (!isPast && isAvailable) ?
                `onclick="bookingSystem.selectDate('${dateStr}')"` : '';

            html += `<div class="${classes}" ${clickHandler}>${day}</div>`;
        }

        if (this.calendarGrid) {
            this.calendarGrid.innerHTML = html;
        }
    }

    formatDate(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    async selectDate(dateStr) {
        this.bookingData.date = dateStr;
        this.bookingData.time = null;
        this.bookingData.slot_id = null;

        // Update hidden input
        if (this.dateInput) {
            this.dateInput.value = dateStr;
        }

        // Update calendar selection
        document.querySelectorAll('.calendar-day').forEach(day => {
            day.classList.remove('selected');
        });
        event.target.classList.add('selected');

        // Show selected date
        if (this.selectedDateDisplay) {
            const date = new Date(dateStr + 'T00:00:00');
            const options = { weekday: 'long', month: 'long', day: 'numeric' };
            this.selectedDateDisplay.textContent = date.toLocaleDateString('en-US', options);
            this.selectedDateDisplay.style.display = 'block';
        }

        // Load time slots
        await this.loadTimeSlots(dateStr);
    }

    async loadTimeSlots(dateStr) {
        if (!this.timeSlotsContainer) return;

        this.showLoading(this.timeSlotsContainer);

        try {
            const params = new URLSearchParams({
                service: this.bookingData.service.id,
                date: dateStr
            });

            if (this.bookingData.staff) {
                params.append('staff', this.bookingData.staff.id);
            }

            const response = await fetch(`${this.apiBaseUrl}/available-slots/?${params}`);
            const data = await response.json();

            if (data.success && data.slots && data.slots.length > 0) {
                this.availableSlots = data.slots;
                this.renderTimeSlots();
            } else {
                this.timeSlotsContainer.innerHTML = `
                    <div class="no-slots-message">
                        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <circle cx="12" cy="12" r="10"/>
                            <path d="M12 6v6l4 2"/>
                        </svg>
                        <p>No available time slots for this date.</p>
                        <p class="text-muted">Please select another date.</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error loading time slots:', error);
            this.timeSlotsContainer.innerHTML = `
                <div class="error-message">
                    <p>Failed to load time slots. Please try again.</p>
                </div>
            `;
        }
    }

    renderTimeSlots() {
        if (!this.timeSlotsContainer) return;

        // Group slots by period (morning, afternoon, evening)
        const morning = [];
        const afternoon = [];
        const evening = [];

        this.availableSlots.forEach(slot => {
            const hour = parseInt(slot.time.split(':')[0]);
            if (hour < 12) morning.push(slot);
            else if (hour < 17) afternoon.push(slot);
            else evening.push(slot);
        });

        let html = '';

        if (morning.length) {
            html += this.renderSlotGroup('Morning', morning);
        }
        if (afternoon.length) {
            html += this.renderSlotGroup('Afternoon', afternoon);
        }
        if (evening.length) {
            html += this.renderSlotGroup('Evening', evening);
        }

        this.timeSlotsContainer.innerHTML = html;
    }

    renderSlotGroup(label, slots) {
        let html = `
            <div class="slot-group">
                <h4 class="slot-group-label">${label}</h4>
                <div class="slot-grid">
        `;

        slots.forEach(slot => {
            const isSelected = this.bookingData.slot_id === slot.id;
            const time12 = this.formatTime12(slot.time);

            html += `
                <button type="button"
                        class="time-slot ${isSelected ? 'selected' : ''}"
                        onclick="bookingSystem.selectTimeSlot('${slot.id}', '${slot.time}', '${slot.staff_id || ''}', '${slot.staff_name || ''}')"
                        ${!slot.available ? 'disabled' : ''}>
                    ${time12}
                    ${slot.staff_name ? `<span class="slot-staff">${slot.staff_name}</span>` : ''}
                </button>
            `;
        });

        html += '</div></div>';
        return html;
    }

    formatTime12(time24) {
        const [hours, minutes] = time24.split(':');
        const hour = parseInt(hours);
        const ampm = hour >= 12 ? 'PM' : 'AM';
        const hour12 = hour % 12 || 12;
        return `${hour12}:${minutes} ${ampm}`;
    }

    selectTimeSlot(slotId, time, staffId, staffName) {
        this.bookingData.time = time;
        this.bookingData.slot_id = slotId;

        // If we selected "any staff" before, now we know which staff
        if (!this.bookingData.staff && staffId && staffName) {
            this.bookingData.staff = {
                id: staffId,
                name: staffName
            };
            // Update staff hidden input
            if (this.staffInput) {
                this.staffInput.value = staffId;
            }
        }

        // Update UI
        document.querySelectorAll('.time-slot').forEach(slot => {
            slot.classList.remove('selected');
        });
        event.target.closest('.time-slot').classList.add('selected');

        // Update hidden inputs
        if (this.slotInput) {
            this.slotInput.value = slotId;
        }
        if (this.timeInput) {
            this.timeInput.value = time;
        }
    }

    // Slot Hold Management
    async holdSlot() {
        if (!this.bookingData.slot_id) return;

        try {
            const response = await fetch(`${this.apiBaseUrl}/hold-slot/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    slot_id: this.bookingData.slot_id,
                    service_id: this.bookingData.service.id
                })
            });

            const data = await response.json();

            if (data.success) {
                this.holdId = data.hold_id;
                this.holdExpiry = new Date(data.expires_at);
                this.startHoldTimer();
            } else {
                this.showError(data.message || 'Failed to hold the slot. It may have been taken.');
                this.currentStep = 3;
                this.loadAvailableDates();
                this.updateUI();
            }
        } catch (error) {
            console.error('Error holding slot:', error);
            this.showError('Failed to hold the slot. Please try again.');
        }
    }

    async releaseHold() {
        if (!this.holdId) return;

        try {
            await fetch(`${this.apiBaseUrl}/release-hold/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    hold_id: this.holdId
                })
            });
        } catch (error) {
            console.error('Error releasing hold:', error);
        }

        this.holdId = null;
        this.stopHoldTimer();
    }

    startHoldTimer() {
        this.stopHoldTimer();

        this.holdTimer = setInterval(() => {
            const now = new Date();
            const remaining = Math.max(0, Math.floor((this.holdExpiry - now) / 1000));

            if (remaining <= 0) {
                this.handleHoldExpired();
                return;
            }

            const minutes = Math.floor(remaining / 60);
            const seconds = remaining % 60;

            if (this.holdTimerDisplay) {
                this.holdTimerDisplay.textContent =
                    `${minutes}:${seconds.toString().padStart(2, '0')}`;

                // Warning when under 1 minute
                if (remaining < 60) {
                    this.holdTimerDisplay.classList.add('warning');
                }
            }
        }, 1000);
    }

    stopHoldTimer() {
        if (this.holdTimer) {
            clearInterval(this.holdTimer);
            this.holdTimer = null;
        }
        if (this.holdTimerDisplay) {
            this.holdTimerDisplay.classList.remove('warning');
        }
    }

    handleHoldExpired() {
        this.stopHoldTimer();
        this.holdId = null;

        this.showError('Your slot hold has expired. Please select a new time.');

        this.bookingData.time = null;
        this.bookingData.slot_id = null;
        this.currentStep = 3;
        this.loadAvailableDates();
        this.updateUI();
    }

    // Confirmation
    updateConfirmation() {
        if (this.confirmService) {
            this.confirmService.textContent = this.bookingData.service?.name || '-';
        }
        if (this.confirmStaff) {
            this.confirmStaff.textContent = this.bookingData.staff?.name || 'Any Available';
        }
        if (this.confirmDate && this.bookingData.date) {
            const date = new Date(this.bookingData.date + 'T00:00:00');
            this.confirmDate.textContent = date.toLocaleDateString('en-US', {
                weekday: 'long',
                month: 'long',
                day: 'numeric',
                year: 'numeric'
            });
        }
        if (this.confirmTime && this.bookingData.time) {
            this.confirmTime.textContent = this.formatTime12(this.bookingData.time);
        }
        if (this.confirmPrice) {
            this.confirmPrice.textContent = `$${this.bookingData.service?.price || '0'}`;
        }
    }

    // Utilities
    getCsrfToken() {
        const cookie = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='));
        return cookie ? cookie.split('=')[1] : '';
    }

    showLoading(container) {
        if (container) {
            container.innerHTML = `
                <div class="loading-spinner">
                    <div class="spinner"></div>
                    <p>Loading...</p>
                </div>
            `;
        }
    }

    showError(message) {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = 'toast toast-error';
        toast.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="15" y1="9" x2="9" y2="15"/>
                <line x1="9" y1="9" x2="15" y2="15"/>
            </svg>
            <span>${message}</span>
        `;

        document.body.appendChild(toast);

        // Animate in
        setTimeout(() => toast.classList.add('show'), 10);

        // Remove after delay
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }

    showSuccess(message) {
        const toast = document.createElement('div');
        toast.className = 'toast toast-success';
        toast.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
            <span>${message}</span>
        `;

        document.body.appendChild(toast);
        setTimeout(() => toast.classList.add('show'), 10);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }
}

// Initialize booking system when DOM is ready
let bookingSystem;

document.addEventListener('DOMContentLoaded', () => {
    const bookingForm = document.querySelector('.booking-form-container');
    if (bookingForm) {
        bookingSystem = new BookingSystem();
    }
});

// Add booking-specific styles
const bookingStyles = document.createElement('style');
bookingStyles.textContent = `
    /* Toast Notifications */
    .toast {
        position: fixed;
        bottom: var(--spacing-xl, 24px);
        right: var(--spacing-xl, 24px);
        display: flex;
        align-items: center;
        gap: var(--spacing-sm, 8px);
        padding: var(--spacing-md, 16px) var(--spacing-lg, 20px);
        background: var(--color-bg-card, #fff);
        border-radius: var(--radius-md, 8px);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        transform: translateY(100px);
        opacity: 0;
        transition: all 0.3s ease;
        z-index: 10000;
    }

    .toast.show {
        transform: translateY(0);
        opacity: 1;
    }

    .toast-error {
        border-left: 4px solid var(--color-error, #ef4444);
    }

    .toast-error svg {
        color: var(--color-error, #ef4444);
    }

    .toast-success {
        border-left: 4px solid var(--color-success, #22c55e);
    }

    .toast-success svg {
        color: var(--color-success, #22c55e);
    }

    /* Loading Spinner */
    .loading-spinner {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: var(--spacing-3xl, 48px);
        color: var(--color-text-muted, #888);
    }

    .spinner {
        width: 40px;
        height: 40px;
        border: 3px solid var(--color-border, #e5e5e5);
        border-top-color: var(--color-accent, #d4af37);
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: var(--spacing-md, 16px);
    }

    @keyframes spin {
        to { transform: rotate(360deg); }
    }

    /* No Slots Message */
    .no-slots-message {
        text-align: center;
        padding: var(--spacing-3xl, 48px);
        color: var(--color-text-muted, #888);
    }

    .no-slots-message svg {
        margin-bottom: var(--spacing-md, 16px);
        opacity: 0.5;
    }

    /* Calendar Header Day */
    .calendar-header-day {
        text-align: center;
        font-size: var(--font-size-xs, 12px);
        text-transform: uppercase;
        color: var(--color-text-muted, #888);
        padding: var(--spacing-sm, 8px);
        font-weight: 600;
    }

    /* Time Slots - Ensure visibility on all themes */
    .slot-group {
        margin-bottom: 24px;
    }

    .slot-group-label {
        font-size: 12px;
        font-weight: 600;
        color: var(--color-text-muted, #888);
        margin-bottom: 12px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .slot-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
        gap: 8px;
    }

    .time-slot {
        padding: 12px 8px;
        border: 1px solid var(--color-border, #333);
        border-radius: 8px;
        background: var(--color-bg-secondary, #1a1a1a);
        color: var(--color-text, #ffffff);
        cursor: pointer;
        transition: all 0.2s ease;
        text-align: center;
        font-weight: 500;
        font-size: 14px;
    }

    .time-slot:hover:not(:disabled) {
        border-color: var(--color-accent, #d4af37);
        background: rgba(212, 175, 55, 0.15);
    }

    .time-slot.selected {
        border-color: var(--color-accent, #d4af37);
        background: var(--color-accent, #d4af37);
        color: #000000;
    }

    .time-slot:disabled {
        opacity: 0.4;
        cursor: not-allowed;
    }

    .time-slot .slot-staff {
        display: block;
        font-size: 11px;
        opacity: 0.7;
        margin-top: 4px;
    }

    /* Light theme overrides for women */
    [data-theme="women"] .time-slot {
        background: #ffffff;
        color: #333333;
        border-color: #e5e5e5;
    }

    [data-theme="women"] .time-slot:hover:not(:disabled) {
        background: rgba(135, 215, 98, 0.15);
        border-color: #87d762;
    }

    [data-theme="women"] .time-slot.selected {
        background: #87d762;
        color: #ffffff;
        border-color: #87d762;
    }
`;

document.head.appendChild(bookingStyles);
