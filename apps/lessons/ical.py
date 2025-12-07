from django.http import HttpResponse
from django.utils import timezone

from icalendar import Calendar, Event


class ICalExporter:
    """Export lessons to iCal format."""

    def generate_calendar(
        self,
        lessons,
        calendar_name: str = 'Zajecia - Na Piatke',
    ) -> Calendar:
        """Generate iCal calendar from lessons."""
        cal = Calendar()
        cal.add('prodid', '-//Na Piatke//Tutoring CMS//PL')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('x-wr-calname', calendar_name)
        cal.add('x-wr-timezone', 'Europe/Warsaw')

        for lesson in lessons:
            event = Event()
            event.add('uid', f'{lesson.id}@napiatke.pl')
            event.add('summary', lesson.title)
            event.add('dtstart', lesson.start_time)
            event.add('dtend', lesson.end_time)
            event.add('dtstamp', timezone.now())

            # Description
            description_parts = []
            if lesson.description:
                description_parts.append(lesson.description)
            if lesson.subject:
                description_parts.append(f'Przedmiot: {lesson.subject.name}')
            if lesson.level:
                description_parts.append(f'Poziom: {lesson.level.name}')
            if lesson.tutor:
                description_parts.append(f'Korepetytor: {lesson.tutor.get_full_name()}')

            event.add('description', '\n'.join(description_parts))

            # Location
            if lesson.room:
                event.add('location', lesson.room.name)
            else:
                event.add('location', 'Online')

            # Status
            if lesson.status == 'cancelled':
                event.add('status', 'CANCELLED')
            else:
                event.add('status', 'CONFIRMED')

            # Organizer
            if lesson.tutor:
                event.add('organizer', f'mailto:{lesson.tutor.email}')

            cal.add_component(event)

        return cal

    def to_response(self, lessons, filename: str = 'calendar.ics') -> HttpResponse:
        """Generate HTTP response with iCal file."""
        cal = self.generate_calendar(lessons)

        response = HttpResponse(
            cal.to_ical(),
            content_type='text/calendar',
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response
