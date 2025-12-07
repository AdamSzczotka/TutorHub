from datetime import timedelta
from typing import Any

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from apps.accounts.models import User
from apps.lessons.models import LessonStudent


class ParentNotificationService:
    """Service for parent notifications."""

    def send_absence_alert(self, student: User, lesson) -> bool:
        """Send immediate absence alert to parent."""
        profile = getattr(student, 'student_profile', None)

        if not profile or not profile.parent_email:
            return False

        context = {
            'parent_name': profile.parent_name or 'Szanowni Rodzice',
            'student_name': student.get_full_name(),
            'lesson_title': lesson.title,
            'lesson_date': lesson.start_time.strftime('%d %B %Y'),
            'lesson_time': lesson.start_time.strftime('%H:%M'),
            'subject': lesson.subject.name,
            'tutor': lesson.tutor.get_full_name(),
        }

        html_content = render_to_string(
            'emails/absence_alert.html',
            context,
        )

        send_mail(
            subject=f'Alert: Nieobecnosc - {student.get_full_name()}',
            message='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[profile.parent_email],
            html_message=html_content,
        )

        return True

    def send_weekly_summaries(self) -> int:
        """Send weekly attendance summaries to all parents."""
        week_start = timezone.now() - timedelta(days=7)
        week_end = timezone.now()

        students = (
            User.objects.filter(
                role='student',
                is_active=True,
                student_profile__parent_email__isnull=False,
            )
            .exclude(student_profile__parent_email='')
            .select_related('student_profile')
        )

        sent_count = 0

        for student in students:
            profile = student.student_profile

            # Get week's attendance
            records = LessonStudent.objects.filter(
                student=student,
                lesson__start_time__gte=week_start,
                lesson__start_time__lte=week_end,
            ).select_related('lesson', 'lesson__subject')

            if not records.exists():
                continue

            total = records.count()
            present = records.filter(attendance_status='PRESENT').count()
            late = records.filter(attendance_status='LATE').count()
            absent = records.filter(attendance_status='ABSENT').count()
            rate = round(((present + late) / total * 100), 1) if total > 0 else 0

            context = {
                'parent_name': profile.parent_name or 'Szanowni Rodzice',
                'student_name': student.get_full_name(),
                'week_start': week_start.strftime('%d %b'),
                'week_end': week_end.strftime('%d %b %Y'),
                'total_lessons': total,
                'present_count': present,
                'late_count': late,
                'absent_count': absent,
                'attendance_rate': rate,
                'lessons': [
                    {
                        'date': r.lesson.start_time.strftime('%d.%m.%Y'),
                        'subject': r.lesson.subject.name,
                        'status': self._get_status_label(r.attendance_status),
                    }
                    for r in records.order_by('lesson__start_time')
                ],
            }

            html_content = render_to_string(
                'emails/weekly_summary.html',
                context,
            )

            send_mail(
                subject=f'Podsumowanie tygodnia - {student.get_full_name()}',
                message='',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[profile.parent_email],
                html_message=html_content,
            )

            sent_count += 1

        return sent_count

    def _get_status_label(self, status: str) -> str:
        """Get Polish label for status."""
        labels = {
            'PRESENT': 'Obecny',
            'LATE': 'Spozniony',
            'ABSENT': 'Nieobecny',
            'EXCUSED': 'Usprawiedliwiony',
        }
        return labels.get(status, 'Oczekujace')


parent_notification_service = ParentNotificationService()
