"""Views for accounts app."""

import csv
import io
from datetime import datetime

from django.contrib import messages
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.base import ContentFile
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
)
from django_filters.views import FilterView
from PIL import Image

from apps.core.mixins import AdminRequiredMixin, HTMXMixin
from apps.core.models import AuditLog
from apps.students.models import StudentProfile
from apps.tutors.models import TutorProfile

from .filters import UserFilter
from .forms import (
    AdminUserCreationForm,
    AvatarUploadForm,
    NotificationPreferenceForm,
    ParentAccessForm,
    ParentInvitationForm,
    PasswordChangeForm,
    StudentProfileForm,
    TutorProfileForm,
    UserEditForm,
    UserProfileForm,
    UserRelationshipForm,
    generate_temp_password,
)
from .models import (
    NotificationPreference,
    ParentAccess,
    UserActivity,
    UserArchive,
    UserCreationLog,
    UserRelationship,
    UserVerification,
)
from .services import ProfileCompletionService, UserArchiveService, UserImportService
from .tasks import (
    send_parent_invitation_email_task,
    send_password_reset_email_task,
    send_verification_email_task,
    send_welcome_email_task,
)

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

        # Return updated button
        status = 'aktywny' if user.is_active else 'nieaktywny'
        badge_class = 'badge-success' if user.is_active else 'badge-error'
        aria_pressed = 'true' if user.is_active else 'false'
        toggle_url = reverse_lazy('accounts:user-toggle-status', kwargs={'pk': pk})

        return HttpResponse(f'''
            <button type="button"
                    hx-post="{toggle_url}"
                    hx-swap="outerHTML"
                    class="badge {badge_class} cursor-pointer hover:opacity-80 focus:outline focus:outline-2 focus:outline-offset-2 focus:outline-primary"
                    title="Kliknij aby zmienić status"
                    aria-pressed="{aria_pressed}">
                {status}
            </button>
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
            return redirect('admin:login')

        return self.render_form(request, form)

    def render_form(self, request, form):
        """Render the form."""
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
        valid_actions = [
            'activate',
            'deactivate',
            'delete',
            'send_password_reset',
            'export',
        ]
        user_ids = request.POST.getlist('user_ids')

        if not action or action not in valid_actions:
            messages.error(request, 'Nieprawidłowa akcja.')
            return redirect('accounts:user-list')

        if not user_ids:
            messages.error(request, 'Nie wybrano żadnych użytkowników.')
            return redirect('accounts:user-list')

        users = User.objects.filter(pk__in=user_ids)
        count = users.count()

        if action == 'activate':
            users.update(is_active=True)
            messages.success(request, f'Aktywowano {count} użytkowników.')

        elif action == 'deactivate':
            users.update(is_active=False)
            messages.success(request, f'Dezaktywowano {count} użytkowników.')

        elif action == 'delete':
            users.update(is_active=False)  # Soft delete
            messages.success(request, f'Usunięto {count} użytkowników.')

        elif action == 'send_password_reset':
            for user in users:
                temp_password = generate_temp_password()
                user.set_password(temp_password)
                user.first_login = True
                user.save(update_fields=['password', 'first_login'])
                send_password_reset_email_task.delay(user.id, temp_password)
            messages.success(request, f'Wysłano reset hasła do {count} użytkowników.')

        elif action == 'export':
            return self._export_users(users)

        # Log bulk action
        AuditLog.objects.create(
            user=request.user,
            action='bulk_update',
            model_type='User',
            model_id=','.join(str(u.pk) for u in users),
            new_values={'action': action, 'count': count},
            ip_address=request.META.get('REMOTE_ADDR'),
        )

        if request.htmx:
            response = HttpResponse()
            response['HX-Redirect'] = reverse_lazy('accounts:user-list')
            return response

        return redirect('accounts:user-list')

    def _export_users(self, users):
        """Export selected users to CSV."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = (
            f'attachment; filename="users_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        )

        writer = csv.writer(response)
        writer.writerow([
            'Email',
            'Imię',
            'Nazwisko',
            'Rola',
            'Telefon',
            'Status',
            'Data rejestracji',
        ])

        for user in users:
            writer.writerow([
                user.email,
                user.first_name,
                user.last_name,
                user.get_role_display(),
                user.phone,
                'Aktywny' if user.is_active else 'Nieaktywny',
                user.date_joined.strftime('%Y-%m-%d'),
            ])

        return response


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


class LoginRedirectView(LoginRequiredMixin, View):
    """Redirect user based on role after login."""

    def get(self, request):
        """Redirect to appropriate dashboard based on user role."""
        user = request.user

        if user.is_admin:
            return redirect('admin_panel:dashboard')
        elif user.is_tutor:
            return redirect('lessons:calendar')
        elif user.is_student:
            return redirect('lessons:calendar')
        else:
            return redirect('landing:home')


class LogoutView(View):
    """Custom logout view."""

    def get(self, request):
        """Log out the user and redirect to landing page."""
        logout(request)
        messages.success(request, 'Zostałeś wylogowany.')
        return redirect('landing:home')

    def post(self, request):
        """Log out the user and redirect to landing page."""
        logout(request)
        messages.success(request, 'Zostałeś wylogowany.')
        return redirect('landing:home')


class UserAnalyticsDashboardView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, TemplateView):
    """User analytics dashboard."""

    template_name = 'admin_panel/users/analytics_dashboard.html'

    def get_context_data(self, **kwargs):
        """Add analytics data."""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Analityka użytkowników'

        # User counts by role
        role_counts = {
            'admin': User.objects.filter(role='admin').count(),
            'tutor': User.objects.filter(role='tutor').count(),
            'student': User.objects.filter(role='student').count(),
        }
        context['role_counts'] = role_counts
        context['total_users'] = (
            role_counts['admin'] + role_counts['tutor'] + role_counts['student']
        )

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
            (completed_first_login / total_with_logs * 100) if total_with_logs else 0
        )

        return context


# =============================================================================
# Profile Wizard Views
# =============================================================================


class ProfileWizardView(LoginRequiredMixin, TemplateView):
    """Profile completion wizard view."""

    template_name = 'accounts/profile_wizard.html'

    def get_context_data(self, **kwargs):
        """Add profile completion context."""
        context = super().get_context_data(**kwargs)
        completion = ProfileCompletionService(self.request.user)

        context.update({
            'completion': completion,
            'steps': completion.steps,
            'percentage': completion.percentage,
            'next_step': completion.next_step,
        })
        return context


class ProfileStepView(LoginRequiredMixin, HTMXMixin, FormView):
    """Handle individual profile step completion."""

    template_name = 'accounts/profile_step.html'
    partial_template_name = 'accounts/partials/_profile_step_form.html'

    def get_form_class(self):
        """Get form class based on step ID."""
        step_id = self.kwargs.get('step_id')
        user = self.request.user

        if step_id == 'basic-info':
            return UserProfileForm
        elif step_id == 'parent-info' and user.is_student:
            return StudentProfileForm
        elif step_id == 'academic-info' and user.is_student:
            return StudentProfileForm
        elif step_id in ('professional-info', 'teaching-info') and user.is_tutor:
            return TutorProfileForm

        return UserProfileForm

    def get_template_names(self):
        """Return template based on request type."""
        if self.request.htmx:
            return [self.partial_template_name]
        return [self.template_name]

    def get_form_kwargs(self):
        """Get form kwargs with proper instance."""
        kwargs = super().get_form_kwargs()
        step_id = self.kwargs.get('step_id')
        user = self.request.user

        if step_id == 'basic-info':
            kwargs['instance'] = user
        elif step_id in ('parent-info', 'academic-info') and user.is_student:
            profile, _ = StudentProfile.objects.get_or_create(user=user)
            kwargs['instance'] = profile
        elif step_id in ('professional-info', 'teaching-info') and user.is_tutor:
            profile, _ = TutorProfile.objects.get_or_create(user=user)
            kwargs['instance'] = profile

        return kwargs

    def get_context_data(self, **kwargs):
        """Add step context."""
        context = super().get_context_data(**kwargs)
        step_id = self.kwargs.get('step_id')
        completion = ProfileCompletionService(self.request.user)
        step = completion.get_step_by_id(step_id)

        context['step'] = step
        context['step_id'] = step_id
        context['completion'] = completion
        return context

    def form_valid(self, form):
        """Handle form submission."""
        form.save()

        # Check if profile is now complete
        completion = ProfileCompletionService(self.request.user)
        if completion.percentage == 100:
            self.request.user.is_profile_completed = True
            self.request.user.save(update_fields=['is_profile_completed'])

            # Update creation log
            UserCreationLog.objects.filter(
                created_user=self.request.user
            ).update(profile_completed_at=timezone.now())

            messages.success(self.request, 'Profil został uzupełniony!')

        if self.request.htmx:
            return render(
                self.request,
                'accounts/partials/_wizard_progress.html',
                {'completion': completion, 'steps': completion.steps},
            )

        return redirect('accounts:profile-wizard')


# =============================================================================
# Avatar Upload Views
# =============================================================================


class AvatarUploadView(LoginRequiredMixin, HTMXMixin, FormView):
    """Handle avatar upload with image processing."""

    form_class = AvatarUploadForm
    template_name = 'accounts/partials/_avatar_upload.html'

    def form_valid(self, form):
        """Process and save avatar."""
        avatar = form.cleaned_data['avatar']
        user = self.request.user

        # Process image with Pillow
        img = Image.open(avatar)

        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        # Resize to 200x200 with center crop
        img.thumbnail((200, 200), Image.Resampling.LANCZOS)

        # Save to buffer
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=90)
        buffer.seek(0)

        # Generate filename
        filename = f'avatar_{user.id}.jpg'

        # Delete old avatar if exists
        if user.avatar:
            user.avatar.delete(save=False)

        # Save new avatar
        user.avatar.save(filename, ContentFile(buffer.read()), save=True)

        messages.success(self.request, 'Avatar został zaktualizowany.')

        if self.request.htmx:
            return render(
                self.request, 'accounts/partials/_avatar_preview.html', {'user': user}
            )

        return redirect('accounts:profile-wizard')

    def form_invalid(self, form):
        """Handle invalid form."""
        if self.request.htmx:
            return render(
                self.request,
                'accounts/partials/_avatar_upload.html',
                {'form': form, 'user': self.request.user},
            )
        return super().form_invalid(form)


class AvatarDeleteView(LoginRequiredMixin, View):
    """Delete user avatar."""

    def post(self, request):
        """Delete avatar."""
        user = request.user

        if user.avatar:
            user.avatar.delete(save=True)
            messages.success(request, 'Avatar został usunięty.')

        if request.htmx:
            return render(
                request, 'accounts/partials/_avatar_preview.html', {'user': user}
            )

        return redirect('accounts:profile-wizard')


# =============================================================================
# User Import Views
# =============================================================================


class UserImportView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """View for importing users from CSV."""

    template_name = 'admin_panel/users/import.html'

    def get_context_data(self, **kwargs):
        """Add context."""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Import użytkowników'
        context['required_columns'] = UserImportService.REQUIRED_COLUMNS
        context['optional_columns'] = UserImportService.OPTIONAL_COLUMNS
        return context

    def post(self, request):
        """Handle CSV upload."""
        csv_file = request.FILES.get('csv_file')

        if not csv_file:
            messages.error(request, 'Wybierz plik CSV.')
            return redirect('accounts:user-import')

        # Read CSV content
        try:
            csv_content = csv_file.read().decode('utf-8')
        except UnicodeDecodeError:
            try:
                csv_file.seek(0)
                csv_content = csv_file.read().decode('cp1250')  # Polish Windows encoding
            except Exception:
                messages.error(request, 'Nie można odczytać pliku. Sprawdź kodowanie.')
                return redirect('accounts:user-import')

        # Validate
        service = UserImportService(csv_content, request.user)
        total, valid, errors = service.validate()

        if 'validate_only' in request.POST:
            return render(
                request,
                'admin_panel/users/partials/_import_preview.html',
                {
                    'total': total,
                    'valid': valid,
                    'errors': errors,
                    'preview': service.valid_rows[:5],
                },
            )

        # Execute import
        send_emails = 'send_emails' in request.POST
        results, import_errors = service.execute(send_emails)

        if results:
            messages.success(
                request,
                f'Zaimportowano {len(results)} użytkowników. Błędy: {len(import_errors)}.',
            )
        else:
            messages.error(
                request, f'Nie zaimportowano żadnych użytkowników. Błędy: {len(import_errors)}.'
            )

        return redirect('accounts:user-list')


# =============================================================================
# Notification Preferences Views (Task 036)
# =============================================================================


class NotificationPreferencesView(LoginRequiredMixin, HTMXMixin, UpdateView):
    """View for managing user notification preferences."""

    model = NotificationPreference
    form_class = NotificationPreferenceForm
    template_name = 'accounts/notification_preferences.html'
    partial_template_name = 'accounts/partials/_notification_preferences_form.html'

    def get_object(self, queryset=None):
        """Get or create notification preferences for current user."""
        prefs, _ = NotificationPreference.objects.get_or_create(user=self.request.user)
        return prefs

    def form_valid(self, form):
        """Handle valid form submission."""
        form.save()

        # Log activity
        UserActivity.log(
            user=self.request.user,
            activity_type=UserActivity.ActivityType.SETTINGS_CHANGE,
            description='Zmiana preferencji powiadomień',
            request=self.request,
        )

        messages.success(self.request, 'Preferencje powiadomień zostały zapisane.')

        if self.request.htmx:
            return render(
                self.request,
                self.partial_template_name,
                {'form': form, 'saved': True},
            )

        return redirect('accounts:notification-preferences')

    def get_context_data(self, **kwargs):
        """Add context."""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Preferencje powiadomień'
        return context


# =============================================================================
# User Relationship Views (Task 038)
# =============================================================================


class UserRelationshipListView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, ListView):
    """List all user relationships."""

    model = UserRelationship
    template_name = 'admin_panel/users/relationships/relationship_list.html'
    partial_template_name = 'admin_panel/users/relationships/partials/_relationship_table.html'
    context_object_name = 'relationships'
    paginate_by = 20

    def get_queryset(self):
        """Get relationships with related users."""
        qs = UserRelationship.objects.select_related(
            'from_user', 'to_user'
        ).order_by('-created_at')

        # Filter by relationship type
        rel_type = self.request.GET.get('type')
        if rel_type:
            qs = qs.filter(relationship_type=rel_type)

        # Filter by active status
        is_active = self.request.GET.get('is_active')
        if is_active == 'true':
            qs = qs.filter(is_active=True)
        elif is_active == 'false':
            qs = qs.filter(is_active=False)

        return qs

    def get_context_data(self, **kwargs):
        """Add context."""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Relacje użytkowników'
        context['relationship_types'] = UserRelationship.RelationshipType.choices
        return context


class UserRelationshipCreateView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, CreateView):
    """Create a new user relationship."""

    model = UserRelationship
    form_class = UserRelationshipForm
    template_name = 'admin_panel/users/relationships/relationship_form.html'
    partial_template_name = 'admin_panel/users/relationships/partials/_relationship_form.html'
    success_url = reverse_lazy('accounts:relationship-list')

    def form_valid(self, form):
        """Handle valid form."""
        response = super().form_valid(form)
        messages.success(self.request, 'Relacja została utworzona.')

        if self.request.htmx:
            response = HttpResponse()
            response['HX-Redirect'] = str(self.success_url)
            return response

        return response

    def get_context_data(self, **kwargs):
        """Add context."""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nowa relacja'
        context['submit_text'] = 'Utwórz relację'
        return context


class UserRelationshipUpdateView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, UpdateView):
    """Update an existing relationship."""

    model = UserRelationship
    form_class = UserRelationshipForm
    template_name = 'admin_panel/users/relationships/relationship_form.html'
    partial_template_name = 'admin_panel/users/relationships/partials/_relationship_form.html'
    success_url = reverse_lazy('accounts:relationship-list')

    def form_valid(self, form):
        """Handle valid form."""
        response = super().form_valid(form)
        messages.success(self.request, 'Relacja została zaktualizowana.')

        if self.request.htmx:
            response = HttpResponse()
            response['HX-Redirect'] = str(self.success_url)
            return response

        return response

    def get_context_data(self, **kwargs):
        """Add context."""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edytuj relację'
        context['submit_text'] = 'Zapisz zmiany'
        return context


class UserRelationshipDeleteView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Delete (deactivate) a relationship."""

    def post(self, request, pk):
        """Deactivate relationship."""
        relationship = get_object_or_404(UserRelationship, pk=pk)
        relationship.is_active = False
        relationship.ended_at = timezone.now().date()
        relationship.save(update_fields=['is_active', 'ended_at'])

        messages.success(request, 'Relacja została zakończona.')

        if request.htmx:
            return HttpResponse(status=200)

        return redirect('accounts:relationship-list')


class TutorStudentsView(LoginRequiredMixin, HTMXMixin, ListView):
    """View for tutor to see their students."""

    template_name = 'tutor/my_students.html'
    partial_template_name = 'tutor/partials/_my_students_list.html'
    context_object_name = 'relationships'

    def get_queryset(self):
        """Get students for current tutor."""
        return UserRelationship.get_students_for_tutor(self.request.user)

    def get_context_data(self, **kwargs):
        """Add context."""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Moi uczniowie'
        return context


# =============================================================================
# User Activity Views (Task 039)
# =============================================================================


class UserActivityListView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, ListView):
    """View user activity logs."""

    model = UserActivity
    template_name = 'admin_panel/users/activity/activity_list.html'
    partial_template_name = 'admin_panel/users/activity/partials/_activity_table.html'
    context_object_name = 'activities'
    paginate_by = 50

    def get_queryset(self):
        """Get activities with filtering."""
        qs = UserActivity.objects.select_related('user').order_by('-created_at')

        # Filter by user
        user_id = self.request.GET.get('user_id')
        if user_id:
            qs = qs.filter(user_id=user_id)

        # Filter by activity type
        activity_type = self.request.GET.get('type')
        if activity_type:
            qs = qs.filter(activity_type=activity_type)

        # Filter by date range
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)

        return qs

    def get_context_data(self, **kwargs):
        """Add context."""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Aktywność użytkowników'
        context['activity_types'] = UserActivity.ActivityType.choices
        context['users'] = User.objects.filter(is_active=True).order_by('last_name')
        return context


class UserActivityDetailView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, ListView):
    """View activity for a specific user."""

    model = UserActivity
    template_name = 'admin_panel/users/activity/user_activity.html'
    partial_template_name = 'admin_panel/users/activity/partials/_user_activity_table.html'
    context_object_name = 'activities'
    paginate_by = 30

    def get_queryset(self):
        """Get activities for specific user."""
        return UserActivity.objects.filter(
            user_id=self.kwargs['pk']
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        """Add context."""
        context = super().get_context_data(**kwargs)
        context['user_obj'] = get_object_or_404(User, pk=self.kwargs['pk'])
        context['title'] = f'Aktywność: {context["user_obj"].get_full_name()}'
        return context


class MyActivityView(LoginRequiredMixin, HTMXMixin, ListView):
    """View for users to see their own activity."""

    model = UserActivity
    template_name = 'accounts/my_activity.html'
    partial_template_name = 'accounts/partials/_my_activity_table.html'
    context_object_name = 'activities'
    paginate_by = 20

    def get_queryset(self):
        """Get current user's activities."""
        return UserActivity.objects.filter(
            user=self.request.user
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        """Add context."""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Moja aktywność'
        return context


# =============================================================================
# User Archive Views (Task 041)
# =============================================================================


class UserArchiveListView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, ListView):
    """List archived users."""

    model = UserArchive
    template_name = 'admin_panel/users/archive/archive_list.html'
    partial_template_name = 'admin_panel/users/archive/partials/_archive_table.html'
    context_object_name = 'archives'
    paginate_by = 20

    def get_queryset(self):
        """Get archives with filtering."""
        qs = UserArchive.objects.select_related('archived_by').order_by('-created_at')

        # Filter by reason
        reason = self.request.GET.get('reason')
        if reason:
            qs = qs.filter(reason=reason)

        # Filter by anonymized status
        is_anonymized = self.request.GET.get('is_anonymized')
        if is_anonymized == 'true':
            qs = qs.filter(is_anonymized=True)
        elif is_anonymized == 'false':
            qs = qs.filter(is_anonymized=False)

        return qs

    def get_context_data(self, **kwargs):
        """Add context."""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Archiwum użytkowników'
        context['archive_reasons'] = UserArchive.ArchiveReason.choices
        return context


class UserArchiveCreateView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Archive a user."""

    def post(self, request, pk):
        """Archive user data."""
        user = get_object_or_404(User, pk=pk)

        reason = request.POST.get('reason', UserArchive.ArchiveReason.ADMIN_ACTION)
        notes = request.POST.get('notes', '')

        # Use archive service
        service = UserArchiveService()
        archive = service.archive_user(
            user=user,
            reason=reason,
            archived_by=request.user,
            notes=notes,
        )

        if archive:
            messages.success(request, f'Użytkownik {user.get_full_name()} został zarchiwizowany.')
        else:
            messages.error(request, 'Nie udało się zarchiwizować użytkownika.')

        if request.htmx:
            response = HttpResponse()
            response['HX-Redirect'] = reverse_lazy('accounts:user-list')
            return response

        return redirect('accounts:user-list')


class UserArchiveDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    """View archived user details."""

    model = UserArchive
    template_name = 'admin_panel/users/archive/archive_detail.html'
    context_object_name = 'archive'

    def get_context_data(self, **kwargs):
        """Add context."""
        context = super().get_context_data(**kwargs)
        context['title'] = f'Archiwum #{self.object.original_user_id}'
        return context


class UserArchiveAnonymizeView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Anonymize archived user data (GDPR compliance)."""

    def post(self, request, pk):
        """Anonymize archive."""
        archive = get_object_or_404(UserArchive, pk=pk)

        if archive.is_anonymized:
            messages.warning(request, 'To archiwum jest już zanonimizowane.')
        else:
            service = UserArchiveService()
            service.anonymize_archive(archive)
            messages.success(request, 'Dane zostały zanonimizowane.')

        if request.htmx:
            return HttpResponse(status=200)

        return redirect('accounts:archive-detail', pk=pk)


# =============================================================================
# User Verification Views (Task 042)
# =============================================================================


class SendVerificationView(LoginRequiredMixin, View):
    """Send verification email/SMS to user."""

    def post(self, request):
        """Send verification."""
        verification_type = request.POST.get('type', 'email')

        if verification_type == 'email':
            value = request.user.email
        else:
            value = request.user.phone

        if not value:
            messages.error(request, 'Brak danych do weryfikacji.')
            return redirect('accounts:profile-wizard')

        # Create verification
        verification = UserVerification.create_for_user(
            user=request.user,
            verification_type=verification_type,
            value=value,
        )

        # Send verification email/SMS
        if verification_type == 'email':
            send_verification_email_task.delay(verification.id)
            messages.success(request, 'Link weryfikacyjny został wysłany na Twój adres email.')
        else:
            # TODO: Implement SMS sending
            messages.info(request, 'Weryfikacja SMS zostanie dodana wkrótce.')

        if request.htmx:
            return HttpResponse('<span class="badge badge-warning">Oczekuje na weryfikację</span>')

        return redirect('accounts:profile-wizard')


class VerifyTokenView(View):
    """Verify token from email/SMS."""

    def get(self, request, token):
        """Verify the token."""
        verification = get_object_or_404(
            UserVerification,
            token=token,
            status=UserVerification.VerificationStatus.PENDING,
        )

        if verification.is_expired:
            messages.error(request, 'Link weryfikacyjny wygasł. Poproś o nowy.')
            return redirect('admin:login')

        if verification.verify(token):
            messages.success(request, 'Weryfikacja zakończona pomyślnie!')

            # Update user verification status if email verified
            if verification.verification_type == UserVerification.VerificationType.EMAIL:
                # Could add email_verified field to User model
                pass

            # Log activity
            UserActivity.log(
                user=verification.user,
                activity_type=UserActivity.ActivityType.SETTINGS_CHANGE,
                description=f'Weryfikacja {verification.get_verification_type_display()}',
                request=request,
            )
        else:
            messages.error(request, 'Nieprawidłowy link weryfikacyjny.')

        return redirect('admin:login')


class VerificationStatusView(LoginRequiredMixin, HTMXMixin, TemplateView):
    """View verification status for current user."""

    template_name = 'accounts/verification_status.html'

    def get_context_data(self, **kwargs):
        """Add context."""
        context = super().get_context_data(**kwargs)

        # Get latest verifications
        context['email_verification'] = UserVerification.objects.filter(
            user=self.request.user,
            verification_type=UserVerification.VerificationType.EMAIL,
        ).order_by('-created_at').first()

        context['phone_verification'] = UserVerification.objects.filter(
            user=self.request.user,
            verification_type=UserVerification.VerificationType.PHONE,
        ).order_by('-created_at').first()

        return context


# =============================================================================
# Parent Portal Access Views (Task 043)
# =============================================================================


class ParentAccessListView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, ListView):
    """List all parent access configurations."""

    model = ParentAccess
    template_name = 'admin_panel/users/parent_access/access_list.html'
    partial_template_name = 'admin_panel/users/parent_access/partials/_access_table.html'
    context_object_name = 'accesses'
    paginate_by = 20

    def get_queryset(self):
        """Get parent accesses with related users."""
        return ParentAccess.objects.select_related(
            'parent', 'student'
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        """Add context."""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Dostępy rodziców'
        context['pending_count'] = ParentAccess.objects.filter(
            invitation_accepted_at__isnull=True,
            is_active=False,
        ).count()
        return context


class ParentAccessCreateView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, FormView):
    """Create parent access invitation."""

    form_class = ParentInvitationForm
    template_name = 'admin_panel/users/parent_access/access_form.html'
    partial_template_name = 'admin_panel/users/parent_access/partials/_access_form.html'

    def get_form_kwargs(self):
        """Add student to form."""
        kwargs = super().get_form_kwargs()
        student_id = self.kwargs.get('student_id') or self.request.GET.get('student_id')
        if student_id:
            kwargs['student'] = get_object_or_404(User, pk=student_id, role='student')
        return kwargs

    def form_valid(self, form):
        """Handle valid form."""
        student_id = self.kwargs.get('student_id') or self.request.POST.get('student_id')
        student = get_object_or_404(User, pk=student_id, role='student')

        access = ParentAccess.create_invitation(
            student=student,
            parent_email=form.cleaned_data['parent_email'],
            access_level=form.cleaned_data['access_level'],
            created_by=self.request.user,
        )

        # Send invitation email
        if not access.invitation_accepted_at:
            send_parent_invitation_email_task.delay(access.id)
            messages.success(
                self.request,
                f'Zaproszenie zostało wysłane na adres {form.cleaned_data["parent_email"]}.'
            )
        else:
            messages.success(
                self.request,
                'Dostęp został przyznany (rodzic ma już konto w systemie).'
            )

        if self.request.htmx:
            response = HttpResponse()
            response['HX-Redirect'] = reverse_lazy('accounts:parent-access-list')
            return response

        return redirect('accounts:parent-access-list')

    def get_context_data(self, **kwargs):
        """Add context."""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Zaproś rodzica'
        context['students'] = User.objects.filter(role='student', is_active=True)

        student_id = self.kwargs.get('student_id') or self.request.GET.get('student_id')
        if student_id:
            context['selected_student'] = get_object_or_404(User, pk=student_id)

        return context


class ParentAccessUpdateView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, UpdateView):
    """Update parent access configuration."""

    model = ParentAccess
    form_class = ParentAccessForm
    template_name = 'admin_panel/users/parent_access/access_edit.html'
    partial_template_name = 'admin_panel/users/parent_access/partials/_access_edit_form.html'
    success_url = reverse_lazy('accounts:parent-access-list')

    def form_valid(self, form):
        """Handle valid form."""
        response = super().form_valid(form)
        messages.success(self.request, 'Dostęp został zaktualizowany.')

        if self.request.htmx:
            response = HttpResponse()
            response['HX-Redirect'] = str(self.success_url)
            return response

        return response

    def get_context_data(self, **kwargs):
        """Add context."""
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edytuj dostęp: {self.object.student.get_full_name()}'
        return context


class ParentAccessRevokeView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Revoke parent access."""

    def post(self, request, pk):
        """Revoke access."""
        access = get_object_or_404(ParentAccess, pk=pk)
        access.is_active = False
        access.save(update_fields=['is_active'])

        messages.success(request, 'Dostęp rodzica został cofnięty.')

        if request.htmx:
            return HttpResponse(status=200)

        return redirect('accounts:parent-access-list')


class ParentAccessResendInvitationView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Resend parent invitation email."""

    def post(self, request, pk):
        """Resend invitation."""
        access = get_object_or_404(ParentAccess, pk=pk)

        if access.invitation_accepted_at:
            messages.warning(request, 'To zaproszenie zostało już zaakceptowane.')
        else:
            # Generate new token
            import secrets
            access.invitation_token = secrets.token_urlsafe(32)
            access.invitation_sent_at = timezone.now()
            access.save(update_fields=['invitation_token', 'invitation_sent_at'])

            send_parent_invitation_email_task.delay(access.id)
            messages.success(request, 'Zaproszenie zostało wysłane ponownie.')

        if request.htmx:
            return HttpResponse(status=200)

        return redirect('accounts:parent-access-list')


class AcceptParentInvitationView(View):
    """Accept parent invitation and create/login account."""

    def get(self, request, token):
        """Show invitation acceptance page."""
        access = get_object_or_404(
            ParentAccess,
            invitation_token=token,
            invitation_accepted_at__isnull=True,
        )

        return render(request, 'accounts/accept_parent_invitation.html', {
            'access': access,
            'student': access.student,
        })

    def post(self, request, token):
        """Accept invitation."""
        access = get_object_or_404(
            ParentAccess,
            invitation_token=token,
            invitation_accepted_at__isnull=True,
        )

        # Check if user is logged in or needs to create account
        if request.user.is_authenticated:
            parent = request.user
        else:
            # Check if account exists
            parent = User.objects.filter(email=access.invited_email).first()
            if not parent:
                # Redirect to registration
                messages.info(request, 'Utwórz konto, aby zaakceptować zaproszenie.')
                return redirect('admin:login')

        # Accept invitation
        access.accept_invitation(parent)
        messages.success(
            request,
            f'Dostęp do danych ucznia {access.student.get_full_name()} został przyznany.'
        )

        return redirect('accounts:my-children')


class MyChildrenView(LoginRequiredMixin, HTMXMixin, ListView):
    """View for parents to see their children."""

    template_name = 'parent/my_children.html'
    partial_template_name = 'parent/partials/_my_children_list.html'
    context_object_name = 'accesses'

    def get_queryset(self):
        """Get children for current parent."""
        return ParentAccess.objects.filter(
            parent=self.request.user,
            is_active=True,
        ).select_related('student', 'student__student_profile')

    def get_context_data(self, **kwargs):
        """Add context."""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Moje dzieci'
        return context


class ChildDetailView(LoginRequiredMixin, HTMXMixin, DetailView):
    """View child details for parent."""

    template_name = 'parent/child_detail.html'
    context_object_name = 'access'

    def get_object(self, queryset=None):
        """Get parent access for this child."""
        return get_object_or_404(
            ParentAccess,
            parent=self.request.user,
            student_id=self.kwargs['pk'],
            is_active=True,
        )

    def get_context_data(self, **kwargs):
        """Add context."""
        context = super().get_context_data(**kwargs)
        access = self.object
        context['student'] = access.student
        context['title'] = access.student.get_full_name()

        # Add data based on permissions
        if access.can_view_lessons:
            # TODO: Add lessons
            context['upcoming_lessons'] = []

        if access.can_view_attendance:
            # TODO: Add attendance
            context['attendance_summary'] = {}

        return context
