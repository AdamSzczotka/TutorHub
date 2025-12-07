// static/js/calendar/calendar-component.js

function calendarApp() {
    return {
        calendar: null,
        currentView: 'timeGridWeek',
        isLoading: false,
        selectedEvent: null,

        init() {
            this.initCalendar();
            this.setupHTMXListeners();
        },

        initCalendar() {
            const calendarEl = document.getElementById('calendar');

            this.calendar = new FullCalendar.Calendar(calendarEl, {
                initialView: this.currentView,
                locale: 'pl',
                timeZone: 'local',
                firstDay: 1,
                slotMinTime: '08:00:00',
                slotMaxTime: '20:00:00',
                height: 'auto',

                headerToolbar: {
                    left: 'prev,next today',
                    center: 'title',
                    right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek'
                },

                businessHours: {
                    daysOfWeek: [1, 2, 3, 4, 5, 6],
                    startTime: '08:00',
                    endTime: '18:00',
                },

                // Event source - fetch from Django
                events: {
                    url: '/panel/lessons/api/events/',
                    method: 'GET',
                    extraParams: () => {
                        return {
                            view: this.currentView,
                        };
                    },
                    failure: () => {
                        this.showError('Błąd ładowania wydarzeń');
                    },
                },

                // Enable drag & drop
                editable: true,
                selectable: true,
                selectMirror: true,
                dayMaxEvents: true,

                // Event handlers
                eventClick: (info) => this.handleEventClick(info),
                select: (info) => this.handleDateSelect(info),
                eventDrop: (info) => this.handleEventDrop(info),
                eventResize: (info) => this.handleEventResize(info),

                // Custom event rendering
                eventDidMount: (info) => this.renderEventTooltip(info),

                // View change
                viewDidMount: (info) => {
                    this.currentView = info.view.type;
                },
            });

            this.calendar.render();
        },

        setupHTMXListeners() {
            // Refresh calendar after HTMX operations
            document.body.addEventListener('eventCreated', () => {
                this.calendar.refetchEvents();
                this.closeModal();
            });

            document.body.addEventListener('eventUpdated', () => {
                this.calendar.refetchEvents();
                this.closeModal();
            });

            document.body.addEventListener('eventDeleted', () => {
                this.calendar.refetchEvents();
                this.closeModal();
            });
        },

        handleEventClick(info) {
            this.selectedEvent = info.event;

            // Load event details via HTMX
            htmx.ajax('GET', `/panel/lessons/${info.event.id}/`, {
                target: '#modal-content',
                swap: 'innerHTML'
            });

            document.getElementById('event-modal').showModal();
        },

        handleDateSelect(info) {
            // Open create form with pre-filled dates
            const startTime = info.startStr;
            const endTime = info.endStr;

            htmx.ajax('GET', `/panel/lessons/create/?start=${startTime}&end=${endTime}`, {
                target: '#modal-content',
                swap: 'innerHTML'
            });

            document.getElementById('event-modal').showModal();
        },

        formatDateTimeForBackend(date) {
            // Format as local datetime WITHOUT timezone offset
            // Django will interpret this as TIME_ZONE (Europe/Warsaw)
            const pad = (n) => n.toString().padStart(2, '0');
            const year = date.getFullYear();
            const month = pad(date.getMonth() + 1);
            const day = pad(date.getDate());
            const hours = pad(date.getHours());
            const minutes = pad(date.getMinutes());
            const seconds = pad(date.getSeconds());
            return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}`;
        },

        async handleEventDrop(info) {
            const { event, revert } = info;

            // Show loading state
            const originalColor = event.backgroundColor;
            event.setProp('backgroundColor', '#94A3B8');

            try {
                const response = await fetch(`/panel/lessons/api/events/${event.id}/move/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCSRFToken(),
                    },
                    body: JSON.stringify({
                        start_time: this.formatDateTimeForBackend(event.start),
                        end_time: this.formatDateTimeForBackend(event.end),
                    }),
                });

                const data = await response.json();

                if (!response.ok) {
                    revert();
                    this.showError(data.error || 'Nie udało się przesunąć zajęć');
                    return;
                }

                // Restore color and show success
                this.calendar.refetchEvents();
                this.showSuccess('Zajęcia zostały przesunięte');

            } catch (error) {
                revert();
                this.showError('Błąd połączenia z serwerem');
            }
        },

        async handleEventResize(info) {
            const { event, revert } = info;

            try {
                const response = await fetch(`/panel/lessons/api/events/${event.id}/resize/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCSRFToken(),
                    },
                    body: JSON.stringify({
                        end_time: this.formatDateTimeForBackend(event.end),
                    }),
                });

                if (!response.ok) {
                    revert();
                    const data = await response.json();
                    this.showError(data.error || 'Nie udało się zmienić czasu trwania');
                    return;
                }

                this.showSuccess('Czas trwania został zmieniony');

            } catch (error) {
                revert();
                this.showError('Błąd połączenia z serwerem');
            }
        },

        renderEventTooltip(info) {
            const props = info.event.extendedProps;

            if (typeof tippy !== 'undefined') {
                tippy(info.el, {
                    content: `
                        <div class="p-2 text-sm">
                            <div class="font-semibold">${info.event.title}</div>
                            <div>Przedmiot: ${props.subject || 'N/A'}</div>
                            <div>Korepetytor: ${props.tutor || 'N/A'}</div>
                            <div>Sala: ${props.room || 'Online'}</div>
                            <div>Uczniów: ${props.student_count || 0}</div>
                        </div>
                    `,
                    allowHTML: true,
                    theme: 'light-border',
                });
            }
        },

        changeView(view) {
            this.currentView = view;
            this.calendar.changeView(view);
        },

        goToToday() {
            this.calendar.today();
        },

        closeModal() {
            document.getElementById('event-modal').close();
            this.selectedEvent = null;
        },

        getCSRFToken() {
            return document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                   document.cookie.match(/csrftoken=([^;]+)/)?.[1];
        },

        showSuccess(message) {
            // Use toast notification
            const toast = document.createElement('div');
            toast.className = 'toast toast-end';
            toast.innerHTML = `<div class="alert alert-success"><span>${message}</span></div>`;
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 3000);
        },

        showError(message) {
            const toast = document.createElement('div');
            toast.className = 'toast toast-end';
            toast.innerHTML = `<div class="alert alert-error"><span>${message}</span></div>`;
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 5000);
        },
    };
}
