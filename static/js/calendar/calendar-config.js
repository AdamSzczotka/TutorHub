// static/js/calendar/calendar-config.js

// Polish localization
const polishLocale = {
    code: 'pl',
    week: {
        dow: 1, // Monday
        doy: 4,
    },
    buttonText: {
        prev: 'Poprzedni',
        next: 'Następny',
        today: 'Dziś',
        month: 'Miesiąc',
        week: 'Tydzień',
        day: 'Dzień',
        list: 'Lista',
    },
    weekText: 'Tyg',
    allDayText: 'Cały dzień',
    moreLinkText: 'więcej',
    noEventsText: 'Brak zajęć do wyświetlenia',
};

// Subject colors
const SUBJECT_COLORS = {
    'Matematyka': '#EF4444',
    'Język Polski': '#3B82F6',
    'Język Angielski': '#10B981',
    'Fizyka': '#8B5CF6',
    'Chemia': '#F59E0B',
    'Biologia': '#06B6D4',
    'Historia': '#84CC16',
    'Geografia': '#F97316',
};

// Status colors
const STATUS_COLORS = {
    'scheduled': '#3B82F6',
    'ongoing': '#10B981',
    'completed': '#6B7280',
    'cancelled': '#EF4444',
};

function getEventColor(subject, status, customColor) {
    if (customColor) return customColor;
    if (status === 'cancelled') return STATUS_COLORS.cancelled;
    if (status === 'completed') return STATUS_COLORS.completed;
    if (status === 'ongoing') return STATUS_COLORS.ongoing;
    return SUBJECT_COLORS[subject] || STATUS_COLORS.scheduled;
}
