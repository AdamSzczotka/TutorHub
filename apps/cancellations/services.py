from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import CancellationRequest, CancellationStatus, MakeupLesson, MakeupStatus


class CancellationService:
    """Service for handling lesson cancellations."""

    CANCELLATION_HOURS_BEFORE = 24
    MAKEUP_EXPIRY_DAYS = 30
    MONTHLY_LIMIT = 2

    def validate_24h_rule(self, lesson):
        """Check if lesson can be cancelled (24h rule)."""
        hours_until = (lesson.start_time - timezone.now()).total_seconds() / 3600

        return {
            'valid': hours_until >= self.CANCELLATION_HOURS_BEFORE,
            'hours_until': int(hours_until),
        }

    def check_monthly_limit(self, student, month=None):
        """Check monthly cancellation limit (max 2 per month)."""
        if month is None:
            month = timezone.now()

        start_of_month = month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if month.month == 12:
            end_of_month = month.replace(year=month.year + 1, month=1, day=1)
        else:
            end_of_month = month.replace(month=month.month + 1, day=1)

        approved_count = CancellationRequest.objects.filter(
            student=student,
            status=CancellationStatus.APPROVED,
            reviewed_at__gte=start_of_month,
            reviewed_at__lt=end_of_month,
        ).count()

        return {
            'allowed': approved_count < self.MONTHLY_LIMIT,
            'count': approved_count,
            'limit': self.MONTHLY_LIMIT,
        }

    def create_request(self, lesson, student, reason):
        """Create a cancellation request."""
        # Validate 24h rule
        validation = self.validate_24h_rule(lesson)
        if not validation['valid']:
            raise ValidationError(
                f"Nie mozna anulowac zajec krocej niz 24h przed rozpoczeciem. "
                f"Pozostalo {validation['hours_until']}h."
            )

        # Check if student is enrolled
        if not lesson.lesson_students.filter(student=student).exists():
            raise ValidationError('Nie jestes zapisany na te zajecia.')

        # Check for existing pending request
        existing = CancellationRequest.objects.filter(
            lesson=lesson,
            student=student,
            status=CancellationStatus.PENDING,
        ).exists()

        if existing:
            raise ValidationError('Prosba o anulowanie tych zajec juz istnieje.')

        # Create request
        request = CancellationRequest.objects.create(
            lesson=lesson,
            student=student,
            reason=reason,
        )

        # Send notification to admins
        self._notify_admins_new_request(request)

        return request

    @transaction.atomic
    def approve_request(self, request, admin, notes=''):
        """Approve a cancellation request."""
        if request.status != CancellationStatus.PENDING:
            raise ValidationError('Prosba zostala juz rozpatrzona.')

        # Update request
        request.status = CancellationStatus.APPROVED
        request.reviewed_by = admin
        request.reviewed_at = timezone.now()
        request.admin_notes = notes
        request.save()

        # Update lesson status
        from apps.lessons.models import LessonStatus
        request.lesson.status = LessonStatus.CANCELLED
        request.lesson.save()

        # Create makeup lesson with 30-day expiry
        expires_at = timezone.now() + timedelta(days=self.MAKEUP_EXPIRY_DAYS)

        makeup = MakeupLesson.objects.create(
            student=request.student,
            original_lesson=request.lesson,
            expires_at=expires_at,
            notes=f'Anulowano: {request.reason}',
        )

        # Send notifications
        self._notify_student_approved(request, makeup)

        return request, makeup

    @transaction.atomic
    def reject_request(self, request, admin, reason):
        """Reject a cancellation request."""
        if request.status != CancellationStatus.PENDING:
            raise ValidationError('Prosba zostala juz rozpatrzona.')

        if not reason:
            raise ValidationError('Powod odrzucenia jest wymagany.')

        request.status = CancellationStatus.REJECTED
        request.reviewed_by = admin
        request.reviewed_at = timezone.now()
        request.admin_notes = reason
        request.save()

        # Send notification
        self._notify_student_rejected(request)

        return request

    def get_student_stats(self, student):
        """Get cancellation statistics for a student."""
        total = CancellationRequest.objects.filter(student=student).count()
        approved = CancellationRequest.objects.filter(
            student=student, status=CancellationStatus.APPROVED
        ).count()
        rejected = CancellationRequest.objects.filter(
            student=student, status=CancellationStatus.REJECTED
        ).count()
        pending = CancellationRequest.objects.filter(
            student=student, status=CancellationStatus.PENDING
        ).count()

        monthly = self.check_monthly_limit(student)

        return {
            'total': total,
            'approved': approved,
            'rejected': rejected,
            'pending': pending,
            'monthly_used': monthly['count'],
            'monthly_limit': monthly['limit'],
            'monthly_remaining': monthly['limit'] - monthly['count'],
        }

    def get_pending_makeups(self, student):
        """Get pending makeup lessons for a student."""
        return MakeupLesson.objects.filter(
            student=student,
            status=MakeupStatus.PENDING,
            expires_at__gt=timezone.now(),
        ).select_related('original_lesson', 'original_lesson__subject')

    def expire_old_makeups(self):
        """Mark expired makeup lessons."""
        expired_count = MakeupLesson.objects.filter(
            status=MakeupStatus.PENDING,
            expires_at__lt=timezone.now(),
        ).update(status=MakeupStatus.EXPIRED)
        return expired_count

    def _notify_admins_new_request(self, request):
        """Notify admins about new cancellation request."""
        from apps.accounts.models import User, UserRole
        from apps.notifications.models import Notification, NotificationType

        admins = User.objects.filter(role=UserRole.ADMIN, is_active=True)

        for admin in admins:
            Notification.objects.create(
                user=admin,
                type=NotificationType.SYSTEM,
                title='Nowa prosba o anulowanie',
                message=(
                    f'{request.student.get_full_name()} prosi o anulowanie '
                    f'zajec "{request.lesson.title}"'
                ),
                data={'cancellation_request_id': request.id},
                action_url='/panel/cancellations/',
            )

    def _notify_student_approved(self, request, makeup):
        """Notify student about approved cancellation."""
        from apps.notifications.models import Notification, NotificationType

        Notification.objects.create(
            user=request.student,
            type=NotificationType.LESSON_CANCELLED,
            title='Anulowanie zaakceptowane',
            message=(
                f'Twoja prosba o anulowanie zajec "{request.lesson.title}" '
                f'zostala zaakceptowana. Masz 30 dni na umowienie zajec zastepczych.'
            ),
            data={
                'cancellation_request_id': request.id,
                'makeup_lesson_id': makeup.id,
            },
        )

    def _notify_student_rejected(self, request):
        """Notify student about rejected cancellation."""
        from apps.notifications.models import Notification, NotificationType

        Notification.objects.create(
            user=request.student,
            type=NotificationType.SYSTEM,
            title='Anulowanie odrzucone',
            message=(
                f'Twoja prosba o anulowanie zajec "{request.lesson.title}" '
                f'zostala odrzucona. Powod: {request.admin_notes}'
            ),
            data={'cancellation_request_id': request.id},
        )


cancellation_service = CancellationService()


class MakeupLessonService:
    """Service for handling makeup lessons."""

    def get_student_makeup_lessons(self, student, status=None):
        """Get makeup lessons for a student."""
        queryset = MakeupLesson.objects.filter(student=student).select_related(
            'original_lesson',
            'original_lesson__subject',
            'original_lesson__tutor',
            'new_lesson',
            'new_lesson__subject',
            'new_lesson__tutor',
        )

        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('expires_at')

    def get_countdown_info(self, makeup_lesson):
        """Calculate countdown information for a makeup lesson."""
        now = timezone.now()
        expires_at = makeup_lesson.expires_at

        if expires_at < now:
            return {
                'text': 'Wygaslo',
                'variant': 'expired',
                'progress': 0,
                'days_left': 0,
                'hours_left': 0,
            }

        delta = expires_at - now
        days_left = delta.days
        hours_left = delta.seconds // 3600

        # Calculate progress (percentage of 30 days remaining)
        total_seconds = 30 * 24 * 3600
        remaining_seconds = delta.total_seconds()
        progress = (remaining_seconds / total_seconds) * 100

        if days_left <= 7:
            variant = 'urgent'
        else:
            variant = 'normal'

        return {
            'text': f'{days_left}d {hours_left}h' if days_left <= 7 else f'{days_left} dni',
            'variant': variant,
            'progress': min(100, max(0, progress)),
            'days_left': days_left,
            'hours_left': hours_left,
        }

    def get_available_slots(self, makeup_lesson):
        """Get available lesson slots for makeup."""
        from django.db.models import Count

        from apps.lessons.models import Lesson, LessonStatus

        original = makeup_lesson.original_lesson

        # Find future lessons with same subject/tutor
        available = (
            Lesson.objects.filter(
                subject=original.subject,
                tutor=original.tutor,
                start_time__gte=timezone.now(),
                status=LessonStatus.SCHEDULED,
            )
            .exclude(lesson_students__student=makeup_lesson.student)
            .select_related('subject', 'tutor', 'room')
            .annotate(student_count=Count('lesson_students'))
            .order_by('start_time')[:20]
        )

        # Filter by capacity
        slots = []
        for lesson in available:
            if not lesson.is_group_lesson:
                # Individual lesson - must be empty
                if lesson.student_count == 0:
                    slots.append(lesson)
            else:
                # Group lesson - check capacity
                if lesson.max_participants and lesson.student_count < lesson.max_participants:
                    slots.append(lesson)

        return slots

    @transaction.atomic
    def schedule_makeup(self, makeup_lesson, new_lesson, user):
        """Schedule a makeup lesson."""
        from apps.lessons.models import LessonStudent

        # Validate not expired
        if makeup_lesson.expires_at < timezone.now():
            raise ValidationError('Termin odrobienia zajec wygasl.')

        # Validate status
        if makeup_lesson.status != MakeupStatus.PENDING:
            raise ValidationError('Zajecia zostaly juz zaplanowane.')

        # Validate permission
        if makeup_lesson.student != user and not user.is_admin:
            raise ValidationError('Brak uprawnien.')

        # Check slot availability
        current_count = new_lesson.lesson_students.count()
        if new_lesson.is_group_lesson:
            if new_lesson.max_participants:
                if current_count >= new_lesson.max_participants:
                    raise ValidationError('Brak wolnych miejsc na tych zajeciach.')
        else:
            if current_count > 0:
                raise ValidationError('Te zajecia sa juz zajete.')

        # Assign student to new lesson
        LessonStudent.objects.create(lesson=new_lesson, student=makeup_lesson.student)

        # Update makeup lesson
        makeup_lesson.new_lesson = new_lesson
        makeup_lesson.status = MakeupStatus.SCHEDULED
        makeup_lesson.save()

        # Send notification
        self._notify_makeup_scheduled(makeup_lesson)

        return makeup_lesson

    @transaction.atomic
    def extend_deadline(self, makeup_lesson, new_expires_at, reason, admin):
        """Extend makeup lesson deadline (admin only)."""
        if new_expires_at <= makeup_lesson.expires_at:
            raise ValidationError('Nowy termin musi byc pozniejszy niz obecny.')

        old_expires = makeup_lesson.expires_at

        makeup_lesson.expires_at = new_expires_at
        makeup_lesson.notes = (
            f"{makeup_lesson.notes or ''}\n\n"
            f"Przedluzono do {new_expires_at.strftime('%d.%m.%Y %H:%M')}. "
            f"Powod: {reason}"
        )
        makeup_lesson.save()

        # Notify student
        self._notify_deadline_extended(makeup_lesson, old_expires, new_expires_at, reason)

        return makeup_lesson

    def _notify_makeup_scheduled(self, makeup_lesson):
        """Notify student about scheduled makeup lesson."""
        from apps.notifications.models import Notification, NotificationType

        Notification.objects.create(
            user=makeup_lesson.student,
            type=NotificationType.LESSON_RESCHEDULED,
            title='Zajecia zastepcze umowione',
            message=(
                f'Zajecia zastepcze zostaly zaplanowane na '
                f'{makeup_lesson.new_lesson.start_time.strftime("%d.%m.%Y, %H:%M")}'
            ),
            data={'makeup_lesson_id': makeup_lesson.id},
        )

    def _notify_deadline_extended(self, makeup_lesson, old_expires, new_expires, reason):
        """Notify student about extended deadline."""
        from apps.notifications.models import Notification, NotificationType

        Notification.objects.create(
            user=makeup_lesson.student,
            type=NotificationType.SYSTEM,
            title='Termin odrobienia przedluzony',
            message=(
                f'Termin odrobienia zajec "{makeup_lesson.original_lesson.title}" '
                f'zostal przedluzony do {new_expires.strftime("%d.%m.%Y, %H:%M")}. '
                f'Powod: {reason}'
            ),
            data={'makeup_lesson_id': makeup_lesson.id},
        )


makeup_service = MakeupLessonService()


class MakeupExpirationService:
    """Service for handling makeup lesson expiration."""

    def expire_past_deadline(self):
        """Auto-expire makeup lessons past deadline."""
        from apps.notifications.models import Notification, NotificationType

        expired_lessons = MakeupLesson.objects.filter(
            status=MakeupStatus.PENDING,
            expires_at__lt=timezone.now(),
        ).select_related('original_lesson', 'student')

        count = 0
        for lesson in expired_lessons:
            lesson.status = MakeupStatus.EXPIRED
            lesson.save()

            # Notify student
            Notification.objects.create(
                user=lesson.student,
                type=NotificationType.SYSTEM,
                title='Zajecia zastepcze wygasly',
                message=(
                    f'Termin odrobienia zajec "{lesson.original_lesson.title}" wygasl. '
                    f'Skontaktuj sie z administratorem w sprawie przedluzenia.'
                ),
                data={'makeup_lesson_id': lesson.id},
            )

            count += 1

        return count

    def send_expiration_warnings(self):
        """Send warnings for lessons expiring in 7 days."""
        from apps.notifications.models import Notification, NotificationType

        seven_days = timezone.now() + timedelta(days=7)

        expiring_lessons = MakeupLesson.objects.filter(
            status=MakeupStatus.PENDING,
            expires_at__gte=timezone.now(),
            expires_at__lte=seven_days,
        ).select_related('original_lesson', 'student')

        count = 0
        for lesson in expiring_lessons:
            # Check if warning already sent today
            today = timezone.now().date()
            existing = Notification.objects.filter(
                user=lesson.student,
                title='Zajecia zastepcze wkrotce wygasna!',
                created_at__date=today,
            ).exists()

            if existing:
                continue

            days_left = (lesson.expires_at - timezone.now()).days

            Notification.objects.create(
                user=lesson.student,
                type=NotificationType.SYSTEM,
                title='Zajecia zastepcze wkrotce wygasna!',
                message=(
                    f'Zostalo tylko {days_left} dni na umowienie zajec zastepczych '
                    f'za "{lesson.original_lesson.title}". Umow termin jak najszybciej!'
                ),
                data={'makeup_lesson_id': lesson.id},
            )

            count += 1

        return count

    def get_statistics(self):
        """Get makeup lesson statistics."""
        pending = MakeupLesson.objects.filter(status=MakeupStatus.PENDING).count()
        scheduled = MakeupLesson.objects.filter(status=MakeupStatus.SCHEDULED).count()
        completed = MakeupLesson.objects.filter(status=MakeupStatus.COMPLETED).count()
        expired = MakeupLesson.objects.filter(status=MakeupStatus.EXPIRED).count()

        total = pending + scheduled + completed + expired

        if completed + expired > 0:
            utilization_rate = (completed / (completed + expired)) * 100
        else:
            utilization_rate = 0

        return {
            'pending': pending,
            'scheduled': scheduled,
            'completed': completed,
            'expired': expired,
            'total': total,
            'utilization_rate': round(utilization_rate),
        }


expiration_service = MakeupExpirationService()
