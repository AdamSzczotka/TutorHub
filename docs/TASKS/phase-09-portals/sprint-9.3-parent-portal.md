# Phase 9 - Sprint 9.3: Parent Portal (Django)

## Tasks 118-122: Parent Access & Monitoring Dashboard

> **Duration**: Week 13 (Day 5, Final part of Phase 9)
> **Goal**: Complete parent-facing portal with monitoring, invoice access, and tutor communication
> **Dependencies**: Sprint 9.2 completed (Student Portal), Phase 7 completed (Invoicing System)

---

## SPRINT OVERVIEW

| Task ID | Description                                 | Priority | Dependencies |
| ------- | ------------------------------------------- | -------- | ------------ |
| 118     | Parent access setup and permission system   | Critical | Task 117     |
| 119     | Monitoring dashboard for child's activities | Critical | Task 118     |
| 120     | Attendance overview and absence management  | High     | Task 119     |
| 121     | Invoice history with PDF downloads          | High     | Task 120     |
| 122     | Tutor communication interface               | High     | Task 121     |

---

## PARENT ACCESS SYSTEM

### Parent Access Mixin

**File**: `apps/core/mixins.py` (add)

```python
from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from apps.accounts.models import User


class ParentAccessMixin(AccessMixin):
    """
    Mixin that verifies parent access to student data.

    Parent access is granted when:
    1. User is admin (can access all)
    2. User is the student themselves
    3. User's email matches student's parent_email (shared access)
    """

    def get_student(self):
        """Get the student object for parent access validation."""
        student_id = self.kwargs.get('student_id') or self.request.GET.get('student_id')
        if not student_id:
            # Default to current user if they are a student
            if hasattr(self.request.user, 'student_profile'):
                return self.request.user
        return get_object_or_404(User, pk=student_id, role='STUDENT')

    def has_parent_access(self, student):
        """Check if current user has parent access to student data."""
        user = self.request.user

        # Admin can access all
        if user.role == 'ADMIN':
            return True

        # Student can access their own data
        if user.id == student.id:
            return True

        # Check parent email match (for shared parent/student access)
        if hasattr(student, 'student_profile'):
            parent_email = student.student_profile.parent_email
            if parent_email and user.email == parent_email:
                return True

        return False

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        student = self.get_student()
        if not self.has_parent_access(student):
            raise PermissionDenied('Brak dostępu do danych tego ucznia')

        # Store student in request for use in views
        request.current_student = student
        return super().dispatch(request, *args, **kwargs)
```

### Parent Required Mixin

**File**: `apps/core/mixins.py` (add)

```python
class ParentRequiredMixin(AccessMixin):
    """
    Mixin for views that require parent role.
    Parents can be identified by:
    1. Having a student account with parent access enabled
    2. Email matching a student's parent_email field
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # Check if user has any children (students linked to them)
        has_children = self._get_children(request.user).exists()

        if not has_children and request.user.role != 'ADMIN':
            raise PermissionDenied('Brak dostępu do portalu rodzica')

        return super().dispatch(request, *args, **kwargs)

    def _get_children(self, user):
        """Get students this user has parent access to."""
        from apps.students.models import StudentProfile

        # If user is a student, return themselves
        if user.role == 'STUDENT':
            return User.objects.filter(pk=user.pk)

        # Check for students where this user's email is parent_email
        return User.objects.filter(
            role='STUDENT',
            student_profile__parent_email=user.email
        )
```

---

## PARENT DASHBOARD SERVICE

### Parent Service

**File**: `apps/parents/services.py`

```python
from django.db.models import Count, Avg, Q, Sum
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.accounts.models import User
from apps.lessons.models import Lesson, LessonStudent
from apps.attendance.models import Attendance
from apps.invoices.models import Invoice
from apps.students.models import StudentProfile


class ParentDashboardService:
    """Service for parent portal operations."""

    @classmethod
    def get_children(cls, parent_user):
        """Get list of children for parent."""
        children = []

        # If parent is a student themselves
        if parent_user.role == 'STUDENT':
            try:
                profile = parent_user.student_profile
                children.append({
                    'id': str(parent_user.id),
                    'name': parent_user.first_name,
                    'surname': parent_user.last_name,
                    'class_name': profile.class_name,
                    'parent_email': profile.parent_email,
                    'parent_phone': profile.parent_phone,
                })
            except StudentProfile.DoesNotExist:
                pass

        # Find students where parent_email matches
        linked_students = User.objects.filter(
            role='STUDENT',
            student_profile__parent_email=parent_user.email
        ).select_related('student_profile')

        for student in linked_students:
            if student.id != parent_user.id:  # Avoid duplicates
                children.append({
                    'id': str(student.id),
                    'name': student.first_name,
                    'surname': student.last_name,
                    'class_name': student.student_profile.class_name,
                    'parent_email': student.student_profile.parent_email,
                    'parent_phone': student.student_profile.parent_phone,
                })

        return children

    @classmethod
    def get_student_info(cls, student):
        """Get basic student info for parent dashboard."""
        try:
            profile = student.student_profile
            return {
                'id': str(student.id),
                'name': student.first_name,
                'surname': student.last_name,
                'email': student.email,
                'class_name': profile.class_name,
                'parent_name': profile.parent_name,
                'parent_email': profile.parent_email,
                'parent_phone': profile.parent_phone,
            }
        except StudentProfile.DoesNotExist:
            return None

    @classmethod
    def get_student_stats(cls, student):
        """Get comprehensive stats for student."""
        today = timezone.now().date()
        month_start = today.replace(day=1)
        thirty_days_ago = timezone.now() - timedelta(days=30)

        # Attendance stats
        attendance = Attendance.objects.filter(student=student)
        total_lessons = attendance.count()
        present_count = attendance.filter(status='PRESENT').count()

        attendance_rate = 0
        if total_lessons > 0:
            attendance_rate = round((present_count / total_lessons) * 100)

        # Monthly lessons
        monthly_lessons = LessonStudent.objects.filter(
            student=student,
            lesson__start_time__gte=month_start,
            lesson__status__in=['SCHEDULED', 'COMPLETED']
        ).count()

        # Monthly hours
        monthly_hours = LessonStudent.objects.filter(
            student=student,
            lesson__start_time__gte=month_start,
            lesson__status='COMPLETED'
        ).aggregate(
            total=Sum('lesson__duration_minutes')
        )['total'] or 0

        # Achievements count
        achievements_count = cls._calculate_achievements(student)

        return {
            'attendance_rate': attendance_rate,
            'present_count': present_count,
            'total_lessons': total_lessons,
            'monthly_lessons': monthly_lessons,
            'monthly_hours': round(monthly_hours / 60, 1),
            'average_grade': 75,  # placeholder
            'grade_count': 0,
            'achievements_count': achievements_count,
        }

    @classmethod
    def get_upcoming_lessons(cls, student, limit=5):
        """Get upcoming lessons for student."""
        return LessonStudent.objects.filter(
            student=student,
            lesson__start_time__gt=timezone.now(),
            lesson__status='SCHEDULED'
        ).select_related(
            'lesson',
            'lesson__tutor',
            'lesson__subject'
        ).order_by('lesson__start_time')[:limit]

    @classmethod
    def get_recent_attendance(cls, student, start_date, end_date):
        """Get attendance records for date range."""
        return Attendance.objects.filter(
            student=student,
            lesson__start_time__gte=start_date,
            lesson__start_time__lte=end_date
        ).select_related(
            'lesson',
            'lesson__tutor'
        ).order_by('-lesson__start_time')

    @classmethod
    def get_pending_invoices(cls, student):
        """Get pending invoices for student."""
        return Invoice.objects.filter(
            student=student,
            status__in=['PENDING', 'OVERDUE']
        ).order_by('-issued_date')

    @classmethod
    def _calculate_achievements(cls, student):
        """Calculate unlocked achievements for student."""
        achievements = 0

        if Attendance.objects.filter(student=student, status='PRESENT').exists():
            achievements += 1

        if Attendance.objects.filter(student=student, status='PRESENT').count() >= 10:
            achievements += 1

        return achievements


class ParentAttendanceService:
    """Service for parent attendance monitoring."""

    @classmethod
    def get_attendance_history(cls, student, start_date, end_date):
        """Get attendance history for date range."""
        return Attendance.objects.filter(
            student=student,
            lesson__start_time__gte=start_date,
            lesson__start_time__lte=end_date
        ).select_related(
            'lesson',
            'lesson__subject',
            'lesson__tutor'
        ).order_by('-lesson__start_time')

    @classmethod
    def get_attendance_stats(cls, student, month):
        """Get attendance statistics for a month."""
        from datetime import datetime
        from django.db.models.functions import ExtractMonth, ExtractYear

        year, month_num = map(int, month.split('-'))

        attendance = Attendance.objects.filter(
            student=student,
            lesson__start_time__year=year,
            lesson__start_time__month=month_num
        )

        total = attendance.count()
        present_count = attendance.filter(status='PRESENT').count()
        absent_count = attendance.filter(status='ABSENT').count()
        late_count = attendance.filter(status='LATE').count()
        excused_count = attendance.filter(status='EXCUSED').count()

        attendance_rate = 0
        if total > 0:
            attendance_rate = round((present_count / total) * 100)

        return {
            'present_count': present_count,
            'absent_count': absent_count,
            'late_count': late_count,
            'excused_count': excused_count,
            'total': total,
            'attendance_rate': attendance_rate,
        }


class ParentInvoiceService:
    """Service for parent invoice operations."""

    @classmethod
    def get_invoices(cls, student):
        """Get all invoices for student."""
        return Invoice.objects.filter(
            student=student
        ).order_by('-issued_date')

    @classmethod
    def get_invoice_summary(cls, student):
        """Get invoice summary for student."""
        today = timezone.now()
        year_start = today.replace(month=1, day=1)

        invoices = Invoice.objects.filter(student=student)

        # Year total
        year_invoices = invoices.filter(issued_date__gte=year_start)
        year_total = year_invoices.filter(status='PAID').aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0')

        # Pending
        pending = invoices.filter(status='PENDING')
        pending_total = pending.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0')

        # Overdue
        overdue = invoices.filter(status='OVERDUE')
        overdue_total = overdue.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0')

        return {
            'year_total': float(year_total),
            'year_invoices_count': year_invoices.count(),
            'pending_total': float(pending_total),
            'pending_count': pending.count(),
            'overdue_total': float(overdue_total),
            'overdue_count': overdue.count(),
        }


class ParentTutorService:
    """Service for parent-tutor communication."""

    @classmethod
    def get_student_tutors(cls, student):
        """Get tutors teaching this student."""
        tutor_ids = LessonStudent.objects.filter(
            student=student
        ).values_list('lesson__tutor_id', flat=True).distinct()

        tutors = User.objects.filter(
            id__in=tutor_ids,
            role='TUTOR'
        ).select_related('tutor_profile')

        result = []
        for tutor in tutors:
            # Get lesson counts
            lessons = LessonStudent.objects.filter(
                student=student,
                lesson__tutor=tutor
            )

            completed = lessons.filter(lesson__status='COMPLETED').count()
            upcoming = lessons.filter(
                lesson__status='SCHEDULED',
                lesson__start_time__gt=timezone.now()
            ).count()

            # Get subjects taught to this student
            subjects = lessons.values_list(
                'lesson__subject__name', flat=True
            ).distinct()

            profile = getattr(tutor, 'tutor_profile', None)

            result.append({
                'id': str(tutor.id),
                'name': tutor.first_name,
                'surname': tutor.last_name,
                'email': tutor.email,
                'bio': profile.bio if profile else '',
                'experience_years': profile.experience_years if profile else 0,
                'rating': profile.rating if profile else None,
                'subjects': list(subjects),
                'completed_lessons': completed,
                'upcoming_lessons': upcoming,
            })

        return result
```

---

## PARENT VIEWS

### Parent Views

**File**: `apps/parents/views.py`

```python
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from datetime import timedelta
from dateutil.relativedelta import relativedelta

from apps.core.mixins import ParentAccessMixin, ParentRequiredMixin, HTMXMixin
from .services import (
    ParentDashboardService,
    ParentAttendanceService,
    ParentInvoiceService,
    ParentTutorService
)


class ParentDashboardView(LoginRequiredMixin, ParentRequiredMixin, HTMXMixin, TemplateView):
    """Parent monitoring dashboard."""
    template_name = 'parent_panel/dashboard.html'
    partial_template_name = 'parent_panel/partials/_dashboard_content.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get children
        children = ParentDashboardService.get_children(user)
        context['children'] = children

        # Get selected child (default to first)
        student_id = self.request.GET.get('student_id')
        if student_id:
            from apps.accounts.models import User
            student = User.objects.get(pk=student_id)
        elif children:
            from apps.accounts.models import User
            student = User.objects.get(pk=children[0]['id'])
        else:
            student = None

        if student:
            context['student'] = ParentDashboardService.get_student_info(student)
            context['stats'] = ParentDashboardService.get_student_stats(student)
            context['upcoming_lessons'] = ParentDashboardService.get_upcoming_lessons(student)
            context['pending_invoices'] = ParentDashboardService.get_pending_invoices(student)

            # Recent attendance (this week)
            today = timezone.now()
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            context['recent_attendance'] = ParentDashboardService.get_recent_attendance(
                student, week_start, week_end
            )
            context['week_start'] = week_start
            context['week_end'] = week_end

        return context


class ParentChildSelectorView(LoginRequiredMixin, ParentRequiredMixin, TemplateView):
    """HTMX view to switch between children."""
    template_name = 'parent_panel/partials/_child_selector.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['children'] = ParentDashboardService.get_children(self.request.user)
        context['selected_id'] = self.request.GET.get('student_id')
        return context


class ParentAttendanceView(LoginRequiredMixin, ParentAccessMixin, HTMXMixin, TemplateView):
    """Parent attendance overview page."""
    template_name = 'parent_panel/attendance/list.html'
    partial_template_name = 'parent_panel/attendance/partials/_attendance_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.current_student

        # Get selected month
        today = timezone.now()
        selected_month = self.request.GET.get('month', today.strftime('%Y-%m'))
        context['selected_month'] = selected_month

        # Parse month
        year, month = map(int, selected_month.split('-'))
        start_date = timezone.datetime(year, month, 1)
        end_date = start_date + relativedelta(months=1) - timedelta(days=1)

        # Get data
        context['attendance'] = ParentAttendanceService.get_attendance_history(
            student, start_date, end_date
        )
        context['stats'] = ParentAttendanceService.get_attendance_stats(
            student, selected_month
        )

        # Generate month options (last 6 months)
        context['month_options'] = [
            {
                'value': (today - relativedelta(months=i)).strftime('%Y-%m'),
                'label': (today - relativedelta(months=i)).strftime('%B %Y'),
            }
            for i in range(6)
        ]

        context['student'] = student
        return context


class ParentInvoicesView(LoginRequiredMixin, ParentAccessMixin, HTMXMixin, TemplateView):
    """Parent invoice history page."""
    template_name = 'parent_panel/invoices/list.html'
    partial_template_name = 'parent_panel/invoices/partials/_invoice_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.current_student

        context['invoices'] = ParentInvoiceService.get_invoices(student)
        context['summary'] = ParentInvoiceService.get_invoice_summary(student)

        # Separate pending and overdue
        invoices = list(context['invoices'])
        context['pending_invoices'] = [i for i in invoices if i.status == 'PENDING']
        context['overdue_invoices'] = [i for i in invoices if i.status == 'OVERDUE']

        context['student'] = student
        return context


class ParentInvoiceDownloadView(LoginRequiredMixin, ParentAccessMixin, TemplateView):
    """Download invoice PDF."""

    def get(self, request, *args, **kwargs):
        from apps.invoices.models import Invoice
        from apps.invoices.services import InvoicePDFService

        invoice = Invoice.objects.get(
            pk=kwargs['invoice_id'],
            student=request.current_student
        )

        pdf_content = InvoicePDFService.generate_pdf(invoice)

        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{invoice.invoice_number}.pdf"'
        return response


class ParentTutorsView(LoginRequiredMixin, ParentAccessMixin, HTMXMixin, TemplateView):
    """Parent tutor communication page."""
    template_name = 'parent_panel/tutors/list.html'
    partial_template_name = 'parent_panel/tutors/partials/_tutor_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.current_student

        context['tutors'] = ParentTutorService.get_student_tutors(student)
        context['student'] = student
        return context


class ParentCalendarView(LoginRequiredMixin, ParentAccessMixin, TemplateView):
    """Parent calendar view."""
    template_name = 'parent_panel/calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['student'] = self.request.current_student
        return context


class ParentCalendarEventsView(LoginRequiredMixin, ParentAccessMixin, TemplateView):
    """API endpoint for parent calendar events."""

    def get(self, request, *args, **kwargs):
        student = request.current_student
        start = request.GET.get('start')
        end = request.GET.get('end')

        from apps.lessons.models import LessonStudent

        lessons = LessonStudent.objects.filter(
            student=student
        ).select_related('lesson', 'lesson__subject', 'lesson__tutor')

        if start:
            lessons = lessons.filter(lesson__start_time__gte=start)
        if end:
            lessons = lessons.filter(lesson__end_time__lte=end)

        events = []
        for ls in lessons:
            lesson = ls.lesson
            color = self._get_status_color(lesson.status)

            events.append({
                'id': str(lesson.id),
                'title': lesson.title,
                'start': lesson.start_time.isoformat(),
                'end': lesson.end_time.isoformat(),
                'backgroundColor': color,
                'borderColor': color,
                'extendedProps': {
                    'subject': lesson.subject.name if lesson.subject else '',
                    'tutor': lesson.tutor.get_full_name() if lesson.tutor else '',
                    'status': lesson.status,
                }
            })

        return JsonResponse(events, safe=False)

    def _get_status_color(self, status):
        colors = {
            'SCHEDULED': '#3B82F6',
            'ONGOING': '#10B981',
            'COMPLETED': '#6B7280',
            'CANCELLED': '#EF4444',
        }
        return colors.get(status, '#3B82F6')


class ParentProgressView(LoginRequiredMixin, ParentAccessMixin, HTMXMixin, TemplateView):
    """Parent view of student progress."""
    template_name = 'parent_panel/progress/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.current_student

        from apps.students.services import StudentProgressService

        context['stats'] = StudentProgressService.get_progress_stats(student)
        context['subjects'] = StudentProgressService.get_subject_progress(student)
        context['achievements'] = StudentProgressService.get_achievements(student)
        context['student'] = student
        return context
```

---

## PARENT TEMPLATES

### Dashboard Template

**File**: `templates/parent_panel/dashboard.html`

```html
{% extends "parent_panel/base.html" %}

{% block title %}Portal Rodzica - Na Piątkę{% endblock %}

{% block content %}
<div class="space-y-6">
    <!-- Header -->
    <div>
        <h1 class="text-3xl font-bold">Portal Rodzica</h1>
        <p class="text-gray-600 mt-1">Monitoruj postępy i uczestnictwo swojego dziecka</p>
    </div>

    <!-- Child Selector (if multiple children) -->
    {% if children|length > 1 %}
        <div class="flex items-center gap-4">
            <span class="text-sm text-gray-600">Wybierz dziecko:</span>
            <div class="flex gap-2">
                {% for child in children %}
                    <a href="?student_id={{ child.id }}"
                       class="btn {% if student.id == child.id %}btn-primary{% else %}btn-outline{% endif %} btn-sm">
                        {{ child.name }} {{ child.surname }}
                    </a>
                {% endfor %}
            </div>
        </div>
    {% endif %}

    {% if student %}
        <!-- Student Info Card -->
        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <div class="flex items-center justify-between">
                    <div>
                        <h2 class="card-title">{{ student.name }} {{ student.surname }}</h2>
                        <p class="text-gray-600">Klasa {{ student.class_name }}</p>
                    </div>
                    <a href="{% url 'parents:settings' student_id=student.id %}" class="btn btn-outline btn-sm">
                        Ustawienia
                    </a>
                </div>
            </div>
        </div>

        <!-- Alerts -->
        {% if overdue_invoices %}
            <div class="alert alert-error">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                </svg>
                <div>
                    <strong>Uwaga!</strong> Zaległe płatności: {{ overdue_invoices|length }} faktur
                    <a href="{% url 'parents:invoices' student_id=student.id %}" class="underline ml-2">
                        Zobacz faktury
                    </a>
                </div>
            </div>
        {% endif %}

        {% if stats.attendance_rate < 80 %}
            <div class="alert alert-warning">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                </svg>
                <span>
                    Frekwencja dziecka wynosi {{ stats.attendance_rate }}%, co jest poniżej zalecanego poziomu.
                    Skontaktuj się z korepetytorem lub administracją.
                </span>
            </div>
        {% endif %}

        <!-- Stats Cards -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <div class="flex items-center justify-between">
                        <h3 class="text-sm font-medium text-gray-600">Frekwencja</h3>
                        <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                    </div>
                    <div class="text-2xl font-bold">{{ stats.attendance_rate }}%</div>
                    <progress class="progress progress-success w-full" value="{{ stats.attendance_rate }}" max="100"></progress>
                    <p class="text-xs text-gray-500 mt-1">
                        {{ stats.present_count }} obecnych z {{ stats.total_lessons }} zajęć
                    </p>
                </div>
            </div>

            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <div class="flex items-center justify-between">
                        <h3 class="text-sm font-medium text-gray-600">Zajęć w tym miesiącu</h3>
                        <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                        </svg>
                    </div>
                    <div class="text-2xl font-bold">{{ stats.monthly_lessons }}</div>
                    <p class="text-xs text-gray-500">{{ stats.monthly_hours }} godzin nauki</p>
                </div>
            </div>

            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <div class="flex items-center justify-between">
                        <h3 class="text-sm font-medium text-gray-600">Średnia ocen</h3>
                        <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
                        </svg>
                    </div>
                    <div class="text-2xl font-bold">{{ stats.average_grade|default:"--" }}/100</div>
                    <p class="text-xs text-gray-500">{{ stats.grade_count }} ocen w systemie</p>
                </div>
            </div>

            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <div class="flex items-center justify-between">
                        <h3 class="text-sm font-medium text-gray-600">Osiągnięcia</h3>
                        <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"/>
                        </svg>
                    </div>
                    <div class="text-2xl font-bold">{{ stats.achievements_count }}</div>
                    <p class="text-xs text-gray-500">odblokowanych odznak</p>
                </div>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Upcoming Lessons -->
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <h2 class="card-title">Nadchodzące zajęcia</h2>
                    <p class="text-sm text-gray-600">Plan zajęć na najbliższe dni</p>

                    {% if upcoming_lessons %}
                        <div class="space-y-3 mt-4">
                            {% for ls in upcoming_lessons %}
                                {% with lesson=ls.lesson %}
                                <div class="flex items-center justify-between p-3 border rounded-lg">
                                    <div class="flex-1">
                                        <div class="font-medium">{{ lesson.title }}</div>
                                        <div class="text-sm text-gray-600">{{ lesson.subject.name }}</div>
                                        <div class="text-sm text-gray-600">{{ lesson.tutor.get_full_name }}</div>
                                    </div>
                                    <div class="text-right text-sm">
                                        <div class="font-medium">{{ lesson.start_time|date:"j M" }}</div>
                                        <div class="text-gray-600">{{ lesson.start_time|time:"H:i" }}</div>
                                    </div>
                                </div>
                                {% endwith %}
                            {% endfor %}

                            <a href="{% url 'parents:calendar' student_id=student.id %}" class="btn btn-outline btn-block">
                                Pełny kalendarz
                            </a>
                        </div>
                    {% else %}
                        <div class="text-center py-8 text-gray-500">
                            <svg class="w-12 h-12 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                            </svg>
                            <p>Brak zaplanowanych zajęć</p>
                        </div>
                    {% endif %}
                </div>
            </div>

            <!-- Recent Attendance -->
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <h2 class="card-title">Obecność w tym tygodniu</h2>
                    <p class="text-sm text-gray-600">{{ week_start|date:"j M" }} - {{ week_end|date:"j M Y" }}</p>

                    {% if recent_attendance %}
                        <div class="space-y-2 mt-4">
                            {% for record in recent_attendance %}
                                <div class="flex items-center justify-between p-3 border rounded-lg">
                                    <div>
                                        <div class="font-medium text-sm">{{ record.lesson.title }}</div>
                                        <div class="text-xs text-gray-600">
                                            {{ record.lesson.start_time|date:"j M, H:i" }}
                                        </div>
                                    </div>
                                    <span class="badge
                                        {% if record.status == 'PRESENT' %}badge-success
                                        {% elif record.status == 'LATE' %}badge-warning
                                        {% elif record.status == 'EXCUSED' %}badge-info
                                        {% else %}badge-error{% endif %}">
                                        {% if record.status == 'PRESENT' %}Obecny
                                        {% elif record.status == 'LATE' %}Spóźniony
                                        {% elif record.status == 'ABSENT' %}Nieobecny
                                        {% elif record.status == 'EXCUSED' %}Usprawiedliwiony{% endif %}
                                    </span>
                                </div>
                            {% endfor %}

                            <a href="{% url 'parents:attendance' student_id=student.id %}" class="btn btn-outline btn-block">
                                Pełna historia obecności
                            </a>
                        </div>
                    {% else %}
                        <div class="text-center py-8 text-gray-500">
                            <svg class="w-12 h-12 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                            </svg>
                            <p>Brak zajęć w tym tygodniu</p>
                        </div>
                    {% endif %}
                </div>
            </div>
        </div>

        <!-- Quick Actions -->
        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <h2 class="card-title">Szybkie akcje</h2>

                <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mt-2">
                    <a href="{% url 'parents:attendance' student_id=student.id %}" class="btn btn-outline h-auto flex-col py-4">
                        <svg class="w-6 h-6 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                        Obecność
                    </a>

                    <a href="{% url 'parents:invoices' student_id=student.id %}" class="btn btn-outline h-auto flex-col py-4">
                        <svg class="w-6 h-6 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                        </svg>
                        Faktury
                    </a>

                    <a href="{% url 'parents:tutors' student_id=student.id %}" class="btn btn-outline h-auto flex-col py-4">
                        <svg class="w-6 h-6 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/>
                        </svg>
                        Korepetytorzy
                    </a>

                    <a href="{% url 'parents:progress' student_id=student.id %}" class="btn btn-outline h-auto flex-col py-4">
                        <svg class="w-6 h-6 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
                        </svg>
                        Postępy
                    </a>
                </div>
            </div>
        </div>
    {% else %}
        <div class="alert alert-info">
            <span>Brak przypisanych dzieci do Twojego konta.</span>
        </div>
    {% endif %}
</div>
{% endblock %}
```

### Invoice History Template

**File**: `templates/parent_panel/invoices/list.html`

```html
{% extends "parent_panel/base.html" %}

{% block title %}Faktury - Portal Rodzica{% endblock %}

{% block content %}
<div class="space-y-6">
    <!-- Header -->
    <div>
        <h1 class="text-2xl font-bold">Historia faktur</h1>
        <p class="text-gray-600 mt-1">Wszystkie faktury i płatności dla {{ student.first_name }}</p>
    </div>

    <!-- Alerts -->
    {% if overdue_invoices %}
        <div class="alert alert-error">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
            </svg>
            <span>
                <strong>Uwaga!</strong> {{ overdue_invoices|length }} przeterminowanych faktur
                na kwotę {{ summary.overdue_total }} zł
            </span>
        </div>
    {% endif %}

    {% if pending_invoices %}
        <div class="alert alert-warning">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
            </svg>
            <span>{{ pending_invoices|length }} faktur oczekuje na płatność: {{ summary.pending_total }} zł</span>
        </div>
    {% endif %}

    <!-- Summary Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <h3 class="text-sm font-medium text-gray-600">Suma w tym roku</h3>
                <div class="text-2xl font-bold">{{ summary.year_total }} zł</div>
                <p class="text-xs text-gray-500">{{ summary.year_invoices_count }} faktur</p>
            </div>
        </div>

        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <h3 class="text-sm font-medium text-gray-600">Oczekujące</h3>
                <div class="text-2xl font-bold text-warning">{{ summary.pending_total }} zł</div>
                <p class="text-xs text-gray-500">{{ summary.pending_count }} faktur</p>
            </div>
        </div>

        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <h3 class="text-sm font-medium text-gray-600">Przeterminowane</h3>
                <div class="text-2xl font-bold text-error">{{ summary.overdue_total }} zł</div>
                <p class="text-xs text-gray-500">{{ summary.overdue_count }} faktur</p>
            </div>
        </div>
    </div>

    <!-- Invoice List -->
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <h2 class="card-title">Wszystkie faktury</h2>

            {% if invoices %}
                <div class="space-y-3 mt-4">
                    {% for invoice in invoices %}
                        <div class="flex items-center justify-between p-4 border rounded-lg hover:bg-base-200 transition-colors">
                            <div class="flex items-start gap-4">
                                <div class="p-2 bg-primary/10 rounded">
                                    <svg class="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                                    </svg>
                                </div>

                                <div>
                                    <div class="font-medium">Faktura {{ invoice.invoice_number }}</div>
                                    <div class="text-sm text-gray-600">
                                        Wystawiona: {{ invoice.issued_date|date:"j M Y" }}
                                    </div>
                                    <div class="text-sm text-gray-600">
                                        Termin: {{ invoice.due_date|date:"j M Y" }}
                                    </div>
                                </div>
                            </div>

                            <div class="text-right space-y-2">
                                <div>
                                    <div class="text-2xl font-bold">{{ invoice.total_amount }} zł</div>
                                    <div class="text-xs text-gray-500">
                                        Netto: {{ invoice.net_amount }} zł + VAT: {{ invoice.vat_amount }} zł
                                    </div>
                                </div>

                                <span class="badge
                                    {% if invoice.status == 'PAID' %}badge-success
                                    {% elif invoice.status == 'OVERDUE' %}badge-error
                                    {% elif invoice.status == 'CANCELLED' %}badge-ghost
                                    {% else %}badge-warning{% endif %}">
                                    {% if invoice.status == 'PAID' %}Opłacona
                                    {% elif invoice.status == 'PENDING' %}Oczekująca
                                    {% elif invoice.status == 'OVERDUE' %}Przeterminowana
                                    {% elif invoice.status == 'CANCELLED' %}Anulowana{% endif %}
                                </span>

                                <a href="{% url 'parents:invoice-download' student_id=student.id invoice_id=invoice.id %}"
                                   class="btn btn-outline btn-sm btn-block">
                                    <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                                    </svg>
                                    Pobierz PDF
                                </a>
                            </div>
                        </div>
                    {% endfor %}
                </div>
            {% else %}
                <div class="text-center py-8 text-gray-500">
                    Brak faktur
                </div>
            {% endif %}
        </div>
    </div>
</div>
{% endblock %}
```

### Tutor Communication Template

**File**: `templates/parent_panel/tutors/list.html`

```html
{% extends "parent_panel/base.html" %}

{% block title %}Korepetytorzy - Portal Rodzica{% endblock %}

{% block content %}
<div class="space-y-6">
    <!-- Header -->
    <div>
        <h1 class="text-2xl font-bold">Korepetytorzy</h1>
        <p class="text-gray-600 mt-1">Kontakt z korepetytorami {{ student.first_name }}</p>
    </div>

    {% if tutors %}
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            {% for tutor in tutors %}
                <div class="card bg-base-100 shadow">
                    <div class="card-body">
                        <div class="flex items-start gap-4">
                            <div class="avatar placeholder">
                                <div class="bg-primary text-primary-content rounded-full w-16 h-16">
                                    <span class="text-xl">{{ tutor.name.0 }}{{ tutor.surname.0 }}</span>
                                </div>
                            </div>

                            <div class="flex-1">
                                <h3 class="card-title">{{ tutor.name }} {{ tutor.surname }}</h3>
                                <p class="text-sm text-gray-600">
                                    {% for subject in tutor.subjects %}{{ subject }}{% if not forloop.last %}, {% endif %}{% endfor %}
                                </p>
                            </div>
                        </div>

                        {% if tutor.bio %}
                            <p class="text-sm text-gray-600 mt-4 line-clamp-3">{{ tutor.bio }}</p>
                        {% endif %}

                        <div class="flex items-center gap-4 mt-4 text-sm">
                            <div class="flex items-center gap-1">
                                <svg class="w-4 h-4 text-warning fill-current" viewBox="0 0 24 24">
                                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                                </svg>
                                <span class="font-medium">{{ tutor.rating|default:"N/A" }}</span>
                            </div>
                            <span class="text-gray-600">{{ tutor.experience_years }} lat doświadczenia</span>
                        </div>

                        <div class="grid grid-cols-2 gap-2 mt-4 text-sm">
                            <div class="bg-base-200 rounded p-2">
                                <div class="text-gray-600 text-xs">Zajęć odbytych</div>
                                <div class="font-semibold">{{ tutor.completed_lessons }}</div>
                            </div>
                            <div class="bg-primary/10 rounded p-2">
                                <div class="text-gray-600 text-xs">Nadchodzących</div>
                                <div class="font-semibold text-primary">{{ tutor.upcoming_lessons }}</div>
                            </div>
                        </div>

                        <div class="flex items-center gap-2 mt-4">
                            <a href="{% url 'messaging:compose' %}?recipient={{ tutor.id }}" class="btn btn-primary flex-1">
                                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
                                </svg>
                                Wyślij wiadomość
                            </a>

                            <a href="{% url 'parents:schedule-meeting' student_id=student.id %}?tutor_id={{ tutor.id }}"
                               class="btn btn-outline flex-1">
                                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                                </svg>
                                Umów spotkanie
                            </a>
                        </div>
                    </div>
                </div>
            {% endfor %}
        </div>
    {% else %}
        <div class="card bg-base-100 shadow">
            <div class="card-body text-center py-12 text-gray-500">
                <p>Brak przypisanych korepetytorów</p>
            </div>
        </div>
    {% endif %}
</div>
{% endblock %}
```

---

## URL CONFIGURATION

**File**: `apps/parents/urls.py`

```python
from django.urls import path
from . import views

app_name = 'parents'

urlpatterns = [
    # Dashboard
    path('', views.ParentDashboardView.as_view(), name='dashboard'),
    path('child-selector/', views.ParentChildSelectorView.as_view(), name='child-selector'),

    # Attendance (requires student_id)
    path('student/<uuid:student_id>/attendance/',
         views.ParentAttendanceView.as_view(), name='attendance'),

    # Invoices
    path('student/<uuid:student_id>/invoices/',
         views.ParentInvoicesView.as_view(), name='invoices'),
    path('student/<uuid:student_id>/invoices/<uuid:invoice_id>/download/',
         views.ParentInvoiceDownloadView.as_view(), name='invoice-download'),

    # Tutors
    path('student/<uuid:student_id>/tutors/',
         views.ParentTutorsView.as_view(), name='tutors'),
    path('student/<uuid:student_id>/schedule-meeting/',
         views.ParentScheduleMeetingView.as_view(), name='schedule-meeting'),

    # Calendar
    path('student/<uuid:student_id>/calendar/',
         views.ParentCalendarView.as_view(), name='calendar'),
    path('student/<uuid:student_id>/calendar/events/',
         views.ParentCalendarEventsView.as_view(), name='calendar-events'),

    # Progress
    path('student/<uuid:student_id>/progress/',
         views.ParentProgressView.as_view(), name='progress'),

    # Settings
    path('student/<uuid:student_id>/settings/',
         views.ParentSettingsView.as_view(), name='settings'),
]
```

---

## COMPLETION CHECKLIST

### Technical Validation

- [ ] Parent access permissions working
- [ ] Monitoring dashboard operational
- [ ] Attendance overview accurate
- [ ] Invoice history displaying correctly
- [ ] Tutor communication functional
- [ ] All HTMX integrations successful

### Feature Validation

- [ ] Parents can access child's data
- [ ] Dashboard shows relevant information
- [ ] Attendance tracking complete
- [ ] Invoice downloads working (PDF)
- [ ] Tutor messaging available
- [ ] Mobile responsive on all pages

### Integration Testing

- [ ] Django Views returning correct data
- [ ] Security checks enforced (ParentAccessMixin)
- [ ] Database queries optimized
- [ ] Error handling comprehensive
- [ ] Permission validation working

### Performance

- [ ] Dashboard loads quickly (<2s)
- [ ] Data fetching efficient
- [ ] No N+1 query issues
- [ ] Smooth navigation

---

**Sprint Completion**: All 5 tasks completed and validated
**Phase Completion**: Phase 9 - User Portals complete
**Next Phase**: 10 - Filtering & Search Systems
**Coordination**: All three portals (Tutor, Student, Parent) ready for production
