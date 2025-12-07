import json
from datetime import datetime, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect

from apps.accounts.models import User
from apps.core.mixins import AdminRequiredMixin
from apps.rooms.models import Room

from .models import Lesson
from .services import CalendarService


class CalendarEventsAPIView(LoginRequiredMixin, View):
    """API endpoint for FullCalendar events."""

    def get(self, request):
        start = request.GET.get('start')
        end = request.GET.get('end')
        tutor_id = request.GET.get('tutor_id')
        room_id = request.GET.get('room_id')

        filters = {}

        if start:
            filters['start_time__gte'] = datetime.fromisoformat(
                start.replace('Z', '+00:00')
            )
        if end:
            filters['end_time__lte'] = datetime.fromisoformat(
                end.replace('Z', '+00:00')
            )
        if tutor_id:
            filters['tutor_id'] = tutor_id
        if room_id:
            filters['room_id'] = room_id

        # Filter based on user role
        user = request.user
        if user.role == 'tutor':
            filters['tutor_id'] = user.id
            lessons = Lesson.objects.filter(**filters)
        elif user.role == 'student':
            lessons = Lesson.objects.filter(
                lesson_students__student_id=user.id, **filters
            )
        else:
            lessons = Lesson.objects.filter(**filters)

        lessons = lessons.select_related(
            'subject', 'level', 'tutor', 'room'
        ).prefetch_related('lesson_students__student')

        events = []
        for lesson in lessons:
            # Convert to local timezone for proper display
            start_local = timezone.localtime(lesson.start_time)
            end_local = timezone.localtime(lesson.end_time)
            events.append(
                {
                    'id': str(lesson.id),
                    'title': lesson.title,
                    'start': start_local.isoformat(),
                    'end': end_local.isoformat(),
                    'backgroundColor': self._get_color(lesson),
                    'borderColor': self._get_color(lesson),
                    'extendedProps': {
                        'subject': lesson.subject.name if lesson.subject else None,
                        'level': lesson.level.name if lesson.level else None,
                        'tutor': (
                            f'{lesson.tutor.first_name} {lesson.tutor.last_name}'
                            if lesson.tutor
                            else None
                        ),
                        'room': lesson.room.name if lesson.room else None,
                        'status': lesson.status,
                        'is_group_lesson': lesson.is_group_lesson,
                        'max_participants': lesson.max_participants,
                        'student_count': lesson.lesson_students.count(),
                    },
                }
            )

        return JsonResponse(events, safe=False)

    def _get_color(self, lesson):
        status_colors = {
            'scheduled': '#3B82F6',
            'ongoing': '#10B981',
            'completed': '#6B7280',
            'cancelled': '#EF4444',
        }

        subject_colors = {
            'Matematyka': '#EF4444',
            'Język Polski': '#3B82F6',
            'Język Angielski': '#10B981',
            'Fizyka': '#8B5CF6',
            'Chemia': '#F59E0B',
        }

        if lesson.color:
            return lesson.color
        if lesson.status in ['cancelled', 'completed']:
            return status_colors.get(lesson.status, '#3B82F6')
        if lesson.subject:
            return subject_colors.get(lesson.subject.name, '#3B82F6')
        return '#3B82F6'


def parse_datetime_from_fullcalendar(dt_string: str) -> datetime:
    """Parse datetime from FullCalendar and interpret as local timezone."""
    # FullCalendar sends ISO format without timezone info (local time)
    # or with Z suffix (UTC) or with offset
    if dt_string.endswith('Z'):
        dt_string = dt_string.replace('Z', '+00:00')
        dt = datetime.fromisoformat(dt_string)
        return timezone.localtime(dt)

    dt = datetime.fromisoformat(dt_string)

    # If naive datetime (no timezone info), assume it's local time
    if dt.tzinfo is None:
        dt = timezone.make_aware(dt)

    return dt


@method_decorator(csrf_protect, name='dispatch')
class EventMoveAPIView(LoginRequiredMixin, AdminRequiredMixin, View):
    """API endpoint for moving events (drag & drop)."""

    def post(self, request, pk):
        try:
            data = json.loads(request.body)
            start_time = parse_datetime_from_fullcalendar(data['start_time'])
            end_time = parse_datetime_from_fullcalendar(data['end_time'])

            lesson = Lesson.objects.get(pk=pk)

            # Check for conflicts
            calendar_service = CalendarService()
            conflicts = calendar_service.check_conflicts(
                tutor_id=lesson.tutor_id,
                room_id=lesson.room_id,
                start_time=start_time,
                end_time=end_time,
                exclude_lesson_id=lesson.id,
            )

            if conflicts:
                conflict_titles = [c.title for c in conflicts]
                return JsonResponse(
                    {'error': f'Konflikt z zajęciami: {", ".join(conflict_titles)}'},
                    status=400,
                )

            # Adjust for timezone offset issue (FullCalendar sends +1h)
            lesson.start_time = start_time - timedelta(hours=1)
            lesson.end_time = end_time - timedelta(hours=1)
            lesson.save()

            return JsonResponse({'success': True})

        except Lesson.DoesNotExist:
            return JsonResponse({'error': 'Zajęcia nie istnieją'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@method_decorator(csrf_protect, name='dispatch')
class EventResizeAPIView(LoginRequiredMixin, AdminRequiredMixin, View):
    """API endpoint for resizing events."""

    def post(self, request, pk):
        try:
            data = json.loads(request.body)
            end_time = parse_datetime_from_fullcalendar(data['end_time'])

            lesson = Lesson.objects.get(pk=pk)

            # Check for conflicts
            calendar_service = CalendarService()
            conflicts = calendar_service.check_conflicts(
                tutor_id=lesson.tutor_id,
                room_id=lesson.room_id,
                start_time=lesson.start_time,
                end_time=end_time,
                exclude_lesson_id=lesson.id,
            )

            if conflicts:
                return JsonResponse(
                    {'error': 'Konflikt z innymi zajęciami'}, status=400
                )

            # Adjust for timezone offset issue (FullCalendar sends +1h)
            lesson.end_time = end_time - timedelta(hours=1)
            lesson.save()

            return JsonResponse({'success': True})

        except Lesson.DoesNotExist:
            return JsonResponse({'error': 'Zajęcia nie istnieją'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


class ResourcesAPIView(LoginRequiredMixin, View):
    """API endpoint for FullCalendar resources (rooms/tutors)."""

    def get(self, request):
        resource_type = request.GET.get('type', 'rooms')

        resources = []

        if resource_type == 'rooms':
            rooms = Room.objects.filter(is_active=True)
            for room in rooms:
                resources.append(
                    {
                        'id': f'room_{room.id}',
                        'title': room.name,
                        'subtitle': room.location or '',
                        'extendedProps': {
                            'type': 'room',
                            'capacity': room.capacity,
                            'is_virtual': room.is_virtual,
                        },
                    }
                )
        elif resource_type == 'tutors':
            tutors = User.objects.filter(role='tutor', is_active=True)
            for tutor in tutors:
                resources.append(
                    {
                        'id': f'tutor_{tutor.id}',
                        'title': tutor.get_full_name(),
                        'subtitle': tutor.email,
                        'extendedProps': {
                            'type': 'tutor',
                            'hourly_rate': str(getattr(tutor, 'hourly_rate', 0) or 0),
                        },
                    }
                )

        return JsonResponse(resources, safe=False)
