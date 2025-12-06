"""Views for accounts app."""

import csv
from datetime import datetime

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)
from django_filters.views import FilterView

from apps.core.mixins import AdminRequiredMixin, HTMXMixin
from apps.core.models import AuditLog
from apps.students.models import StudentProfile
from apps.tutors.models import TutorProfile

from .filters import UserFilter
from .forms import (
    AdminUserCreationForm,
    PasswordChangeForm,
    StudentProfileForm,
    TutorProfileForm,
    UserEditForm,
    generate_temp_password,
)
from .models import UserCreationLog
from .tasks import send_password_reset_email_task, send_welcome_email_task

User = get_user_model()


# =============================================================================
# User CRUD Views
# =============================================================================


class UserListView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, FilterView):
    """List all users with filtering and search."""

    model = User
    template_name = 'admin_panel/users/user_list.html'
    partial_template_name = 'admin_panel/users/partials/_user_table.html'
    context_object_name = 'users'
    filterset_class = UserFilter
    paginate_by = 20

    def get_queryset(self):
        """Get users with related profiles."""
        return User.objects.select_related(
            'tutor_profile',
            'student_profile',
        ).order_by('-date_joined')

    def get_context_data(self, **kwargs):
        """Add extra context."""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Użytkownicy'
        context['total_users'] = User.objects.count()
        context['active_users'] = User.objects.filter(is_active=True).count()
        context['admins_count'] = User.objects.filter(role='admin').count()
        context['tutors_count'] = User.objects.filter(role='tutor').count()
        context['students_count'] = User.objects.filter(role='student').count()
        return context


class UserCreateView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, CreateView):
    """View for admin to create new users."""

    model = User
    form_class = AdminUserCreationForm
    template_name = 'admin_panel/users/user_form.html'
    partial_template_name = 'admin_panel/users/partials/_user_form.html'
    success_url = reverse_lazy('accounts:user-list')

    def form_valid(self, form):
        """Handle valid form submission."""
        user, temp_password = form.save(created_by=self.request.user)

        # Send welcome email (async with Celery)
        send_welcome_email_task.delay(
            user_id=user.id,
            temp_password=temp_password,
        )

        # Log action
        AuditLog.objects.create(
            user=self.request.user,
            action='create',
            model_type='User',
            model_id=str(user.pk),
            new_values={
                'email': user.email,
                'role': user.role,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            ip_address=self.request.META.get('REMOTE_ADDR'),
        )

        messages.success(
            self.request,
            f'Użytkownik {user.get_full_name()} został utworzony. '
            'Hasło tymczasowe zostało wysłane na adres e-mail użytkownika.'
        )

        if self.request.htmx:
            response = HttpResponse()
            response['HX-Redirect'] = str(self.success_url)
            return response

        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        """Add extra context."""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Utwórz użytkownika'
        context['submit_text'] = 'Utwórz użytkownika'
        return context


class UserDetailView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, DetailView):
    """View user details."""

    model = User
    template_name = 'admin_panel/users/user_detail.html'
    partial_template_name = 'admin_panel/users/partials/_user_detail.html'
    context_object_name = 'user_obj'

    def get_queryset(self):
        """Get user with related profiles."""
        return User.objects.select_related(
            'tutor_profile',
            'student_profile',
        )

    def get_context_data(self, **kwargs):
        """Add extra context."""
        context = super().get_context_data(**kwargs)
        context['title'] = f'Szczegóły: {self.object.get_full_name()}'

        # Get creation log if exists
        context['creation_log'] = UserCreationLog.objects.filter(
            created_user=self.object
        ).first()

        # Get recent audit logs
        context['audit_logs'] = AuditLog.objects.filter(
            model_type='User',
            model_id=str(self.object.pk),
        ).order_by('-created_at')[:10]

        return context


class UserUpdateView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, UpdateView):
    """Update user details."""

    model = User
    form_class = UserEditForm
    template_name = 'admin_panel/users/user_form.html'
    partial_template_name = 'admin_panel/users/partials/_user_form.html'
    success_url = reverse_lazy('accounts:user-list')

    def get_context_data(self, **kwargs):
        """Add extra context."""
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edytuj: {self.object.get_full_name()}'
        context['submit_text'] = 'Zapisz zmiany'

        # Add profile forms based on role
        if self.object.is_student:
            profile, _ = StudentProfile.objects.get_or_create(user=self.object)
            context['profile_form'] = StudentProfileForm(instance=profile)
        elif self.object.is_tutor:
            profile, _ = TutorProfile.objects.get_or_create(user=self.object)
            context['profile_form'] = TutorProfileForm(instance=profile)

        return context

    def form_valid(self, form):
        """Handle valid form submission."""
        old_values = {
            'email': self.object.email,
            'role': self.object.role,
            'is_active': self.object.is_active,
        }

        response = super().form_valid(form)

        # Log changes
        new_values = {
            'email': self.object.email,
            'role': self.object.role,
            'is_active': self.object.is_active,
        }

        AuditLog.objects.create(
            user=self.request.user,
            action='update',
            model_type='User',
            model_id=str(self.object.pk),
            old_values=old_values,
            new_values=new_values,
            ip_address=self.request.META.get('REMOTE_ADDR'),
        )

        messages.success(self.request, f'Użytkownik {self.object.get_full_name()} został zaktualizowany.')

        if self.request.htmx:
            response = HttpResponse()
            response['HX-Redirect'] = str(self.success_url)
            return response

        return response


class UserDeleteView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, DeleteView):
    """Delete user (soft delete by deactivating)."""

    model = User
    template_name = 'admin_panel/users/user_confirm_delete.html'
    partial_template_name = 'admin_panel/users/partials/_user_confirm_delete.html'
    success_url = reverse_lazy('accounts:user-list')

    def form_valid(self, form):
        """Soft delete - deactivate user instead of hard delete."""
        user = self.get_object()

        # Log deletion
        AuditLog.objects.create(
            user=self.request.user,
            action='delete',
            model_type='User',
            model_id=str(user.pk),
            old_values={
                'email': user.email,
                'is_active': True,
            },
            new_values={
                'is_active': False,
            },
            ip_address=self.request.META.get('REMOTE_ADDR'),
        )

        # Soft delete
        user.is_active = False
        user.save(update_fields=['is_active'])

        messages.success(self.request, f'Użytkownik {user.get_full_name()} został dezaktywowany.')

        if self.request.htmx:
            response = HttpResponse()
            response['HX-Redirect'] = str(self.success_url)
            return response

        return redirect(self.success_url)


# =============================================================================
# User Status Management
# =============================================================================


class UserStatusToggleView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Toggle user active/inactive status via HTMX."""

    def post(self, request, pk):
        """Toggle user status."""
        user = get_object_or_404(User, pk=pk)
        old_status = user.is_active

        # Toggle status
        user.is_active = not user.is_active
        user.save(update_fields=['is_active'])

        # Log the change
        AuditLog.objects.create(
            user=request.user,
            action='update',
            model_type='User',
            model_id=str(user.pk),
            old_values={'is_active': old_status},
            new_values={'is_active': user.is_active},
            ip_address=request.META.get('REMOTE_ADDR'),
        )

        # Return updated badge
        status = 'aktywny' if user.is_active else 'nieaktywny'
        badge_class = 'badge-success' if user.is_active else 'badge-error'

        return HttpResponse(f'''
            <span class="badge {badge_class}">{status}</span>
        ''')


# =============================================================================
# Password Management
# =============================================================================


class PasswordResetView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Reset user password and send email with new temp password."""

    def post(self, request, pk):
        """Reset password."""
        user = get_object_or_404(User, pk=pk)

        # Generate new temp password
        temp_password = generate_temp_password()
        user.set_password(temp_password)
        user.first_login = True
        user.save(update_fields=['password', 'first_login'])

        # Send email with new password
        send_password_reset_email_task.delay(
            user_id=user.id,
            temp_password=temp_password,
        )

        # Log action
        AuditLog.objects.create(
            user=request.user,
            action='update',
            model_type='User',
            model_id=str(user.pk),
            old_values={},
            new_values={'password': 'reset'},
            ip_address=request.META.get('REMOTE_ADDR'),
        )

        messages.success(
            request,
            f'Hasło dla {user.get_full_name()} zostało zresetowane. '
            'Nowe hasło tymczasowe zostało wysłane na adres e-mail użytkownika.'
        )

        if request.htmx:
            response = HttpResponse()
            response['HX-Redirect'] = reverse_lazy('accounts:user-detail', kwargs={'pk': pk})
            return response

        return redirect('accounts:user-detail', pk=pk)


class FirstLoginPasswordChangeView(LoginRequiredMixin, HTMXMixin, View):
    """View for changing password on first login."""

    template_name = 'accounts/first_login_password.html'

    def get(self, request):
        """Show password change form."""
        if not request.user.first_login:
            return redirect('accounts:user-list')

        form = PasswordChangeForm()
        return self.render_form(request, form)

    def post(self, request):
        """Handle password change."""
        form = PasswordChangeForm(request.POST)

        if form.is_valid():
            request.user.set_password(form.cleaned_data['new_password'])
            request.user.first_login = False
            request.user.save(update_fields=['password', 'first_login'])

            # Update creation log
            UserCreationLog.objects.filter(
                created_user=request.user
            ).update(first_login_at=timezone.now())

            messages.success(request, 'Hasło zostało zmienione. Zaloguj się ponownie.')
            return redirect('login')

        return self.render_form(request, form)

    def render_form(self, request, form):
        """Render the form."""
        from django.shortcuts import render
        return render(request, self.template_name, {'form': form})


# =============================================================================
# User Data Export (RODO)
# =============================================================================


class UserExportView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Export user data to CSV (RODO compliance)."""

    def get(self, request):
        """Export all users to CSV."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = (
            f'attachment; filename="users_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        )

        # Use Polish locale for CSV
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Email', 'Imię', 'Nazwisko', 'Telefon', 'Rola',
            'Aktywny', 'Profil uzupełniony', 'Data rejestracji',
        ])

        users = User.objects.all().order_by('id')
        for user in users:
            writer.writerow([
                user.id,
                user.email,
                user.first_name,
                user.last_name,
                user.phone,
                user.get_role_display(),
                'Tak' if user.is_active else 'Nie',
                'Tak' if user.is_profile_completed else 'Nie',
                user.date_joined.strftime('%Y-%m-%d %H:%M'),
            ])

        # Log export action
        AuditLog.objects.create(
            user=request.user,
            action='export',
            model_type='User',
            model_id='all',
            new_values={'exported_count': users.count()},
            ip_address=request.META.get('REMOTE_ADDR'),
        )

        return response


class UserDataExportView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Export single user data (RODO request)."""

    def get(self, request, pk):
        """Export user data as JSON."""
        user = get_object_or_404(User, pk=pk)

        data = {
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': user.phone,
                'role': user.role,
                'date_joined': user.date_joined.isoformat(),
            }
        }

        # Add profile data
        if user.is_student and hasattr(user, 'student_profile'):
            profile = user.student_profile
            data['student_profile'] = {
                'class_name': profile.class_name,
                'current_level': profile.current_level,
                'learning_goals': profile.learning_goals,
                'parent_name': profile.parent_name,
                'parent_phone': profile.parent_phone,
                'parent_email': profile.parent_email,
            }
        elif user.is_tutor and hasattr(user, 'tutor_profile'):
            profile = user.tutor_profile
            data['tutor_profile'] = {
                'bio': profile.bio,
                'education': profile.education,
                'experience_years': profile.experience_years,
                'hourly_rate': str(profile.hourly_rate) if profile.hourly_rate else None,
            }

        # Log export
        AuditLog.objects.create(
            user=request.user,
            action='export',
            model_type='User',
            model_id=str(pk),
            new_values={'exported_fields': list(data.keys())},
            ip_address=request.META.get('REMOTE_ADDR'),
        )

        return JsonResponse(data)


# =============================================================================
# Bulk Operations
# =============================================================================


class UserBulkActionView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Handle bulk user operations."""

    def post(self, request):
        """Process bulk action."""
        action = request.POST.get('action')
        user_ids = request.POST.getlist('user_ids')

        if not user_ids:
            messages.error(request, 'Nie wybrano żadnych użytkowników.')
            return redirect('accounts:user-list')

        users = User.objects.filter(pk__in=user_ids)

        if action == 'activate':
            users.update(is_active=True)
            messages.success(request, f'Aktywowano {users.count()} użytkowników.')

        elif action == 'deactivate':
            users.update(is_active=False)
            messages.success(request, f'Dezaktywowano {users.count()} użytkowników.')

        elif action == 'delete':
            count = users.count()
            users.update(is_active=False)  # Soft delete
            messages.success(request, f'Usunięto {count} użytkowników.')

        # Log bulk action
        AuditLog.objects.create(
            user=request.user,
            action='bulk_update',
            model_type='User',
            model_id=','.join(user_ids),
            new_values={'action': action, 'count': len(user_ids)},
            ip_address=request.META.get('REMOTE_ADDR'),
        )

        if request.htmx:
            response = HttpResponse()
            response['HX-Redirect'] = reverse_lazy('accounts:user-list')
            return response

        return redirect('accounts:user-list')


# =============================================================================
# Profile Completion Tracking
# =============================================================================


class ProfileCompletionView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, ListView):
    """View users with incomplete profiles."""

    model = User
    template_name = 'admin_panel/users/profile_completion.html'
    partial_template_name = 'admin_panel/users/partials/_profile_completion_table.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        """Get users with incomplete profiles."""
        return User.objects.filter(
            is_profile_completed=False,
            is_active=True,
        ).select_related(
            'tutor_profile',
            'student_profile',
        ).order_by('-date_joined')

    def get_context_data(self, **kwargs):
        """Add extra context."""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Niekompletne profile'
        context['incomplete_count'] = self.get_queryset().count()
        return context


class MarkProfileCompleteView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Mark user profile as complete."""

    def post(self, request, pk):
        """Mark profile complete."""
        user = get_object_or_404(User, pk=pk)
        user.is_profile_completed = True
        user.save(update_fields=['is_profile_completed'])

        # Update creation log
        UserCreationLog.objects.filter(
            created_user=user
        ).update(profile_completed_at=timezone.now())

        # Log action
        AuditLog.objects.create(
            user=request.user,
            action='update',
            model_type='User',
            model_id=str(user.pk),
            old_values={'is_profile_completed': False},
            new_values={'is_profile_completed': True},
            ip_address=request.META.get('REMOTE_ADDR'),
        )

        messages.success(request, f'Profil {user.get_full_name()} oznaczono jako kompletny.')

        if request.htmx:
            return HttpResponse('<span class="badge badge-success">Uzupełniony</span>')

        return redirect('accounts:user-detail', pk=pk)


# =============================================================================
# Parent Contact Management
# =============================================================================


class ParentContactListView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, ListView):
    """List students with their parent contacts."""

    template_name = 'admin_panel/users/parent_contacts.html'
    partial_template_name = 'admin_panel/users/partials/_parent_contacts_table.html'
    context_object_name = 'students'
    paginate_by = 20

    def get_queryset(self):
        """Get students with parent info."""
        return StudentProfile.objects.select_related(
            'user'
        ).filter(
            user__is_active=True
        ).order_by('user__last_name', 'user__first_name')

    def get_context_data(self, **kwargs):
        """Add extra context."""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Kontakty rodziców'

        # Count students without parent contact
        context['missing_parent_count'] = StudentProfile.objects.filter(
            user__is_active=True,
            parent_email='',
        ).count()

        return context


class ParentContactUpdateView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, UpdateView):
    """Update parent contact for a student."""

    model = StudentProfile
    form_class = StudentProfileForm
    template_name = 'admin_panel/users/parent_contact_form.html'
    partial_template_name = 'admin_panel/users/partials/_parent_contact_form.html'
    success_url = reverse_lazy('accounts:parent-contact-list')

    def get_object(self, queryset=None):
        """Get student profile by user pk."""
        user_pk = self.kwargs.get('pk')
        return get_object_or_404(StudentProfile, user__pk=user_pk)

    def form_valid(self, form):
        """Handle valid form."""
        response = super().form_valid(form)

        # Log changes
        AuditLog.objects.create(
            user=self.request.user,
            action='update',
            model_type='StudentProfile',
            model_id=str(self.object.pk),
            new_values={
                'parent_name': self.object.parent_name,
                'parent_email': self.object.parent_email,
                'parent_phone': self.object.parent_phone,
            },
            ip_address=self.request.META.get('REMOTE_ADDR'),
        )

        messages.success(
            self.request,
            f'Kontakt rodzica dla {self.object.user.get_full_name()} został zaktualizowany.'
        )

        if self.request.htmx:
            response = HttpResponse()
            response['HX-Redirect'] = str(self.success_url)
            return response

        return response

    def get_context_data(self, **kwargs):
        """Add extra context."""
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edytuj kontakt rodzica: {self.object.user.get_full_name()}'
        context['student'] = self.object.user
        return context


# =============================================================================
# User Analytics Dashboard
# =============================================================================


class UserAnalyticsDashboardView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, TemplateView):
    """User analytics dashboard."""

    template_name = 'admin_panel/users/analytics_dashboard.html'

    def get_context_data(self, **kwargs):
        """Add analytics data."""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Analityka użytkowników'

        # User counts by role
        context['role_counts'] = {
            'admin': User.objects.filter(role='admin').count(),
            'tutor': User.objects.filter(role='tutor').count(),
            'student': User.objects.filter(role='student').count(),
        }

        # Active vs inactive
        context['status_counts'] = {
            'active': User.objects.filter(is_active=True).count(),
            'inactive': User.objects.filter(is_active=False).count(),
        }

        # Profile completion
        context['profile_counts'] = {
            'completed': User.objects.filter(is_profile_completed=True).count(),
            'incomplete': User.objects.filter(is_profile_completed=False).count(),
        }

        # Recent registrations (last 30 days)
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        context['recent_registrations'] = User.objects.filter(
            date_joined__gte=thirty_days_ago
        ).count()

        # Users created per month (last 6 months)
        six_months_ago = timezone.now() - timezone.timedelta(days=180)
        context['monthly_registrations'] = (
            User.objects.filter(date_joined__gte=six_months_ago)
            .annotate(month=TruncMonth('date_joined'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )

        # First login completion rate
        total_with_logs = UserCreationLog.objects.count()
        completed_first_login = UserCreationLog.objects.filter(
            first_login_at__isnull=False
        ).count()
        context['first_login_rate'] = (
            (completed_first_login / total_with_logs * 100) if total_with_logs > 0 else 0
        )

        return context
