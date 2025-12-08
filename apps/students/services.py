"""Services for student portal operations."""

from datetime import timedelta
from decimal import Decimal
from typing import Any

from django.db.models import Count, Q, Sum
from django.utils import timezone

from apps.cancellations.models import CancellationRequest, MakeupLesson
from apps.lessons.models import Lesson, LessonStudent


class StudentDashboardService:
    """Service for student dashboard operations."""

    @classmethod
    def get_dashboard_stats(cls, student) -> dict[str, Any]:
        """Get comprehensive dashboard statistics for student."""
        today = timezone.now().date()
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = timezone.now().replace(hour=23, minute=59, second=59, microsecond=999999)

        # Today's lessons
        today_lessons = LessonStudent.objects.filter(
            student=student,
            lesson__start_time__gte=today_start,
            lesson__start_time__lte=today_end,
            lesson__status__in=['scheduled', 'ongoing'],
        ).select_related('lesson')

        # Next lesson time
        next_lesson = (
            LessonStudent.objects.filter(
                student=student,
                lesson__start_time__gt=timezone.now(),
                lesson__status='scheduled',
            )
            .select_related('lesson')
            .order_by('lesson__start_time')
            .first()
        )

        # Attendance rate (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        attendance_stats = LessonStudent.objects.filter(
            student=student,
            lesson__start_time__gte=thirty_days_ago,
            lesson__status='completed',
        ).aggregate(
            total=Count('id'),
            present=Count('id', filter=Q(attendance_status='PRESENT')),
        )

        attendance_rate = 0
        if attendance_stats['total'] and attendance_stats['total'] > 0:
            attendance_rate = round(
                (attendance_stats['present'] / attendance_stats['total']) * 100
            )

        # Makeup lessons count
        makeup_count = MakeupLesson.objects.filter(
            student=student,
            status='PENDING',
            expires_at__gt=timezone.now(),
        ).count()

        # Achievements count
        achievements_count = cls._calculate_achievements(student)

        return {
            'today_lessons_count': today_lessons.count(),
            'next_lesson_time': next_lesson.lesson.start_time.strftime('%H:%M')
            if next_lesson
            else None,
            'attendance_rate': attendance_rate,
            'makeup_count': makeup_count,
            'achievements_count': achievements_count,
        }

    @classmethod
    def get_today_lessons(cls, student):
        """Get today's lessons for student."""
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = timezone.now().replace(hour=23, minute=59, second=59, microsecond=999999)

        return (
            LessonStudent.objects.filter(
                student=student,
                lesson__start_time__gte=today_start,
                lesson__start_time__lte=today_end,
            )
            .select_related('lesson', 'lesson__tutor', 'lesson__subject', 'lesson__room')
            .order_by('lesson__start_time')
        )

    @classmethod
    def get_upcoming_lessons(cls, student, limit: int = 5):
        """Get upcoming lessons for student."""
        return (
            LessonStudent.objects.filter(
                student=student,
                lesson__start_time__gt=timezone.now(),
                lesson__status='scheduled',
            )
            .select_related('lesson', 'lesson__tutor', 'lesson__subject', 'lesson__room')
            .order_by('lesson__start_time')[:limit]
        )

    @classmethod
    def get_makeup_lessons(cls, student):
        """Get pending makeup lessons for student."""
        return (
            MakeupLesson.objects.filter(
                student=student,
                status='PENDING',
                expires_at__gt=timezone.now(),
            )
            .select_related(
                'original_lesson', 'original_lesson__subject', 'original_lesson__tutor'
            )
            .order_by('expires_at')
        )

    @classmethod
    def get_recent_progress(cls, student, limit: int = 3):
        """Get recent lessons with notes for student."""
        return (
            LessonStudent.objects.filter(
                student=student,
                lesson__status='completed',
                attendance_notes__isnull=False,
            )
            .exclude(attendance_notes='')
            .select_related('lesson', 'lesson__subject')
            .order_by('-lesson__start_time')[:limit]
        )

    @classmethod
    def _calculate_achievements(cls, student) -> int:
        """Calculate unlocked achievements for student."""
        achievements = 0

        # Achievement: First lesson attended
        if LessonStudent.objects.filter(
            student=student, attendance_status='PRESENT'
        ).exists():
            achievements += 1

        # Achievement: 10 lessons completed
        if (
            LessonStudent.objects.filter(
                student=student, attendance_status='PRESENT'
            ).count()
            >= 10
        ):
            achievements += 1

        # Achievement: 100% attendance in a month (simplified check)
        achievements += 1  # placeholder

        return achievements


class StudentProgressService:
    """Service for student progress tracking."""

    @classmethod
    def get_progress_stats(cls, student) -> dict[str, Any]:
        """Get overall progress statistics."""
        thirty_days_ago = timezone.now() - timedelta(days=30)

        # Attendance stats
        attendance = LessonStudent.objects.filter(
            student=student, lesson__status='completed'
        )
        total_lessons = attendance.count()
        completed_lessons = attendance.filter(attendance_status='PRESENT').count()

        attendance_rate = 0
        if total_lessons > 0:
            attendance_rate = round((completed_lessons / total_lessons) * 100)

        # Hours calculation
        total_minutes = (
            LessonStudent.objects.filter(student=student, lesson__status='completed')
            .select_related('lesson')
            .aggregate(
                total=Sum(
                    (
                        models.F('lesson__end_time') - models.F('lesson__start_time')
                    ).seconds
                    // 60
                )
            )['total']
            or 0
        )

        monthly_lessons = LessonStudent.objects.filter(
            student=student,
            lesson__status='completed',
            lesson__start_time__gte=thirty_days_ago,
        ).select_related('lesson')

        monthly_minutes = 0
        for ls in monthly_lessons:
            duration = (ls.lesson.end_time - ls.lesson.start_time).seconds // 60
            monthly_minutes += duration

        total_hours = 0
        for ls in LessonStudent.objects.filter(
            student=student, lesson__status='completed'
        ).select_related('lesson'):
            duration = (ls.lesson.end_time - ls.lesson.start_time).seconds // 60
            total_hours += duration

        return {
            'attendance_rate': attendance_rate,
            'completed_lessons': completed_lessons,
            'total_lessons': total_lessons,
            'total_hours': round(total_hours / 60, 1),
            'monthly_hours': round(monthly_minutes / 60, 1),
        }

    @classmethod
    def get_subject_progress(cls, student) -> list[dict[str, Any]]:
        """Get progress breakdown by subject."""
        from apps.subjects.models import Subject

        subjects = Subject.objects.filter(
            lessons__lesson_students__student=student
        ).distinct()

        result = []
        for subject in subjects:
            lessons = LessonStudent.objects.filter(
                student=student, lesson__subject=subject
            )
            total = lessons.count()
            completed = lessons.filter(lesson__status='completed').count()

            # Average score from attendance notes (placeholder)
            avg_score = 75

            result.append(
                {
                    'id': str(subject.id),
                    'name': subject.name,
                    'color': getattr(subject, 'color', '#3B82F6'),
                    'total_lessons': total,
                    'completed_lessons': completed,
                    'avg_score': avg_score,
                }
            )

        return result

    @classmethod
    def get_achievements(cls, student) -> dict[str, Any]:
        """Get student achievements."""
        first_lesson = LessonStudent.objects.filter(
            student=student, attendance_status='PRESENT'
        ).first()

        badges = [
            {
                'id': 'first_lesson',
                'name': 'Pierwsza lekcja',
                'icon': '🎓',
                'unlocked': LessonStudent.objects.filter(
                    student=student, attendance_status='PRESENT'
                ).exists(),
                'unlocked_at': first_lesson.lesson.start_time if first_lesson else None,
            },
            {
                'id': 'ten_lessons',
                'name': '10 lekcji',
                'icon': '📚',
                'unlocked': LessonStudent.objects.filter(
                    student=student, attendance_status='PRESENT'
                ).count()
                >= 10,
                'unlocked_at': None,
            },
            {
                'id': 'perfect_month',
                'name': 'Idealny miesiąc',
                'icon': '⭐',
                'unlocked': False,
                'unlocked_at': None,
            },
            {
                'id': 'early_bird',
                'name': 'Ranny ptaszek',
                'icon': '🐦',
                'unlocked': False,
                'unlocked_at': None,
            },
        ]

        unlocked_count = sum(1 for b in badges if b['unlocked'])

        return {
            'unlocked': unlocked_count,
            'total': len(badges),
            'badges': badges,
        }


class StudentCancellationService:
    """Service for student cancellation operations."""

    CANCELLATION_HOURS_BEFORE = 24
    MONTHLY_LIMIT = 3

    @classmethod
    def get_cancellation_limit(cls, student) -> dict[str, int]:
        """Get monthly cancellation limit and usage."""
        from apps.core.models import SystemSetting

        month_start = timezone.now().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        limit = int(SystemSetting.get('monthly_cancellation_limit', cls.MONTHLY_LIMIT))

        used = CancellationRequest.objects.filter(
            student=student,
            created_at__gte=month_start,
            status__in=['PENDING', 'APPROVED'],
        ).count()

        return {
            'limit': limit,
            'used': used,
            'remaining': max(0, limit - used),
        }

    @classmethod
    def can_cancel_lesson(cls, student, lesson) -> tuple[bool, str | None]:
        """Check if student can cancel a lesson."""
        # Check 24h rule
        hours_until = (lesson.start_time - timezone.now()).total_seconds() / 3600
        if hours_until < cls.CANCELLATION_HOURS_BEFORE:
            return False, 'Anulowanie możliwe minimum 24h przed zajęciami'

        # Check monthly limit
        limit_info = cls.get_cancellation_limit(student)
        if limit_info['remaining'] <= 0:
            return False, 'Przekroczono miesięczny limit anulowań'

        # Check if already has pending request
        existing = CancellationRequest.objects.filter(
            student=student,
            lesson=lesson,
            status='PENDING',
        ).exists()
        if existing:
            return False, 'Już złożono wniosek o anulowanie tych zajęć'

        return True, None

    @classmethod
    def create_cancellation_request(cls, student, lesson, reason: str):
        """Create a cancellation request."""
        can_cancel, error = cls.can_cancel_lesson(student, lesson)
        if not can_cancel:
            raise ValueError(error)

        request = CancellationRequest.objects.create(
            student=student,
            lesson=lesson,
            reason=reason,
            status='PENDING',
        )

        # Send notification to admin
        try:
            from apps.notifications.services import NotificationService

            NotificationService.notify_admins(
                title='Nowy wniosek o anulowanie',
                message=f'{student.get_full_name()} prosi o anulowanie zajęć: {lesson.title}',
                notification_type='CANCELLATION_REQUEST',
            )
        except Exception:
            pass  # Notification is not critical

        return request

    @classmethod
    def get_cancellable_lessons(cls, student):
        """Get lessons that can be cancelled."""
        min_time = timezone.now() + timedelta(hours=cls.CANCELLATION_HOURS_BEFORE)

        return (
            LessonStudent.objects.filter(
                student=student,
                lesson__start_time__gt=min_time,
                lesson__status='scheduled',
            )
            .select_related('lesson', 'lesson__subject', 'lesson__tutor')
            .order_by('lesson__start_time')
        )

    @classmethod
    def get_student_requests(cls, student, limit: int = 10):
        """Get recent cancellation requests for student."""
        return (
            CancellationRequest.objects.filter(student=student)
            .select_related('lesson', 'lesson__subject')
            .order_by('-created_at')[:limit]
        )


# Import models at module level to avoid issues
from django.db import models
