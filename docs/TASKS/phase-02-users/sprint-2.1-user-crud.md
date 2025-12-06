# Phase 2 - Sprint 2.1: User CRUD Operations & Direct Creation System (Django)

## Tasks 021-032: User Management Foundation

> **Duration**: Week 3-4 of Phase 2 (10 working days)
> **Goal**: Complete user management with direct admin creation, profiles, and role-based access
> **Dependencies**: Phase 1 completed (Database & Authentication)

---

## SPRINT OVERVIEW

| Task ID | Description                               | Priority | Dependencies     |
| ------- | ----------------------------------------- | -------- | ---------------- |
| 021     | Direct user creation system (admin only)  | Critical | Phase 1 complete |
| 022     | User profile forms and validation         | Critical | Task 021         |
| 023     | Role-based permission system              | Critical | Task 022         |
| 024     | User status management (active/inactive)  | Critical | Task 023         |
| 025     | Password management & temporary passwords | Critical | Task 024         |
| 026     | User search and filtering                 | High     | Task 025         |
| 027     | User data export (RODO compliance)        | High     | Task 026         |
| 028     | User audit logging                        | High     | Task 027         |
| 029     | Bulk user operations                      | Medium   | Task 028         |
| 030     | User profile completion tracking          | Medium   | Task 029         |
| 031     | Parent contact management                 | High     | Task 030         |
| 032     | User analytics dashboard                  | Medium   | Task 031         |

---

## DETAILED TASK BREAKDOWN

### Task 021: Direct User Creation System (Admin Only)

**Files**: `apps/accounts/views.py`, `apps/accounts/forms.py`, `templates/admin_panel/users/`

#### User Creation Form

```python
# apps/accounts/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
import secrets
import string

from apps.students.models import StudentProfile
from apps.tutors.models import TutorProfile

User = get_user_model()


def generate_temp_password(length=12):
    """Generate a secure temporary password."""
    alphabet = string.ascii_letters + string.digits + '!@#$%'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class AdminUserCreationForm(forms.ModelForm):
    """Form for admin to create new users directly."""

    # Role selection
    role = forms.ChoiceField(
        choices=[
            ('student', 'Uczeń'),
            ('tutor', 'Korepetytor'),
            ('admin', 'Administrator'),
        ],
        widget=forms.Select(attrs={'class': 'select select-bordered w-full'}),
    )

    # Student-specific fields
    class_name = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'np. 7A, 3LO',
        }),
    )
    parent_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
    )
    parent_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'input input-bordered w-full'}),
    )
    parent_phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': '+48123456789',
        }),
    )

    # Tutor-specific fields
    education = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
    )
    experience_years = forms.IntegerField(
        min_value=0,
        max_value=50,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'input input-bordered w-full'}),
    )
    hourly_rate = forms.DecimalField(
        max_digits=8,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'input input-bordered w-full',
            'step': '0.01',
        }),
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone', 'role']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'input input-bordered w-full'}),
            'first_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'last_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'phone': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': '+48123456789',
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')

        # Validate student-specific fields
        if role == 'student':
            if not cleaned_data.get('parent_email'):
                self.add_error('parent_email', 'Email rodzica jest wymagany dla ucznia.')

        return cleaned_data

    def save(self, commit=True, created_by=None):
        user = super().save(commit=False)
        user.role = self.cleaned_data['role']

        # Generate temporary password
        temp_password = generate_temp_password()
        user.set_password(temp_password)
        user.first_login = True
        user.is_profile_completed = False

        if commit:
            user.save()

            # Create role-specific profile
            role = self.cleaned_data['role']

            if role == 'student':
                StudentProfile.objects.create(
                    user=user,
                    class_name=self.cleaned_data.get('class_name', ''),
                    parent_name=self.cleaned_data.get('parent_name', ''),
                    parent_email=self.cleaned_data.get('parent_email', ''),
                    parent_phone=self.cleaned_data.get('parent_phone', ''),
                )

            elif role == 'tutor':
                TutorProfile.objects.create(
                    user=user,
                    education=self.cleaned_data.get('education', ''),
                    experience_years=self.cleaned_data.get('experience_years'),
                    hourly_rate=self.cleaned_data.get('hourly_rate'),
                )

            # Log creation
            if created_by:
                from apps.accounts.models import UserCreationLog
                UserCreationLog.objects.create(
                    created_user=user,
                    created_by=created_by,
                    email_sent=False,
                )

        return user, temp_password
```

#### User Creation View

```python
# apps/accounts/views.py
from django.views.generic import CreateView, ListView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import HttpResponse

from apps.core.mixins import AdminRequiredMixin, HTMXMixin
from .forms import AdminUserCreationForm
from .models import User, UserCreationLog
from .tasks import send_welcome_email_task


class UserCreateView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, CreateView):
    """View for admin to create new users."""

    model = User
    form_class = AdminUserCreationForm
    template_name = 'admin_panel/users/user_form.html'
    partial_template_name = 'admin_panel/users/partials/_user_form.html'
    success_url = reverse_lazy('accounts:user-list')

    def form_valid(self, form):
        user, temp_password = form.save(created_by=self.request.user)

        # Send welcome email (async with Celery)
        send_welcome_email_task.delay(
            user_id=user.id,
            temp_password=temp_password,
        )

        # Update creation log
        UserCreationLog.objects.filter(
            created_user=user
        ).update(email_sent=True)

        messages.success(
            self.request,
            f'Użytkownik {user.get_full_name()} został utworzony. '
            f'Hasło tymczasowe: {temp_password}'
        )

        if self.request.htmx:
            response = HttpResponse()
            response['HX-Redirect'] = str(self.success_url)
            return response

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Utwórz użytkownika'
        return context
```

#### User Creation Template with HTMX

```html
<!-- templates/admin_panel/users/user_form.html -->
{% extends "admin_panel/base.html" %}
{% load crispy_forms_tags %}

{% block title %}{{ title }}{% endblock %}

{% block content %}
<div class="max-w-4xl mx-auto">
    <div class="card bg-base-100 shadow-xl">
        <div class="card-body">
            <h2 class="card-title text-2xl mb-6">{{ title }}</h2>

            <form method="post"
                  hx-post="{{ request.path }}"
                  hx-target="#form-container"
                  hx-swap="innerHTML"
                  id="form-container">
                {% csrf_token %}

                <!-- Basic Fields -->
                <div class="grid md:grid-cols-2 gap-4 mb-6">
                    <div class="form-control">
                        <label class="label">
                            <span class="label-text">Imię *</span>
                        </label>
                        {{ form.first_name }}
                        {% if form.first_name.errors %}
                            <label class="label">
                                <span class="label-text-alt text-error">{{ form.first_name.errors.0 }}</span>
                            </label>
                        {% endif %}
                    </div>

                    <div class="form-control">
                        <label class="label">
                            <span class="label-text">Nazwisko *</span>
                        </label>
                        {{ form.last_name }}
                        {% if form.last_name.errors %}
                            <label class="label">
                                <span class="label-text-alt text-error">{{ form.last_name.errors.0 }}</span>
                            </label>
                        {% endif %}
                    </div>
                </div>

                <div class="grid md:grid-cols-2 gap-4 mb-6">
                    <div class="form-control">
                        <label class="label">
                            <span class="label-text">Email *</span>
                        </label>
                        {{ form.email }}
                    </div>

                    <div class="form-control">
                        <label class="label">
                            <span class="label-text">Rola *</span>
                        </label>
                        <select name="role"
                                class="select select-bordered w-full"
                                x-data="{ role: '{{ form.role.value|default:'student' }}' }"
                                x-model="role"
                                @change="$dispatch('role-changed', { role: $event.target.value })">
                            <option value="student">Uczeń</option>
                            <option value="tutor">Korepetytor</option>
                            <option value="admin">Administrator</option>
                        </select>
                    </div>
                </div>

                <!-- Student-specific fields -->
                <div x-data="{ showStudent: true }"
                     @role-changed.window="showStudent = $event.detail.role === 'student'"
                     x-show="showStudent"
                     x-transition
                     class="p-4 bg-info/10 rounded-lg mb-6">
                    <h3 class="font-semibold mb-4">Dane ucznia</h3>

                    <div class="form-control mb-4">
                        <label class="label">
                            <span class="label-text">Klasa</span>
                        </label>
                        {{ form.class_name }}
                    </div>

                    <h4 class="font-medium mt-4 mb-2">Dane rodzica/opiekuna *</h4>
                    <div class="grid md:grid-cols-2 gap-4">
                        <div class="form-control">
                            <label class="label">
                                <span class="label-text">Imię i nazwisko rodzica</span>
                            </label>
                            {{ form.parent_name }}
                        </div>

                        <div class="form-control">
                            <label class="label">
                                <span class="label-text">Email rodzica *</span>
                            </label>
                            {{ form.parent_email }}
                        </div>

                        <div class="form-control">
                            <label class="label">
                                <span class="label-text">Telefon rodzica</span>
                            </label>
                            {{ form.parent_phone }}
                        </div>
                    </div>
                </div>

                <!-- Tutor-specific fields -->
                <div x-data="{ showTutor: false }"
                     @role-changed.window="showTutor = $event.detail.role === 'tutor'"
                     x-show="showTutor"
                     x-transition
                     class="p-4 bg-success/10 rounded-lg mb-6">
                    <h3 class="font-semibold mb-4">Dane korepetytora</h3>

                    <div class="form-control mb-4">
                        <label class="label">
                            <span class="label-text">Wykształcenie</span>
                        </label>
                        {{ form.education }}
                    </div>

                    <div class="grid md:grid-cols-2 gap-4">
                        <div class="form-control">
                            <label class="label">
                                <span class="label-text">Lata doświadczenia</span>
                            </label>
                            {{ form.experience_years }}
                        </div>

                        <div class="form-control">
                            <label class="label">
                                <span class="label-text">Stawka godzinowa (zł)</span>
                            </label>
                            {{ form.hourly_rate }}
                        </div>
                    </div>
                </div>

                <!-- Form actions -->
                <div class="flex justify-end gap-4 mt-6">
                    <a href="{% url 'accounts:user-list' %}" class="btn btn-ghost">
                        Anuluj
                    </a>
                    <button type="submit" class="btn btn-primary">
                        <span class="loading loading-spinner htmx-indicator"></span>
                        Utwórz użytkownika
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}
```

#### Celery Task for Email

```python
# apps/accounts/tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


@shared_task
def send_welcome_email_task(user_id: int, temp_password: str):
    """Send welcome email with temporary password."""
    from apps.accounts.models import User

    try:
        user = User.objects.get(id=user_id)

        subject = 'Witamy w Na Piątkę - Twoje dane logowania'
        html_message = render_to_string('emails/welcome.html', {
            'user': user,
            'temp_password': temp_password,
            'login_url': f"{settings.SITE_URL}/login/",
        })

        send_mail(
            subject=subject,
            message='',  # Plain text version
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
        )

        return True
    except User.DoesNotExist:
        return False
```

---

### Task 022: User Profile Forms and Validation

**Files**: `apps/accounts/forms.py`, `apps/accounts/views.py`

```python
# apps/accounts/forms.py (continued)
from django.core.validators import RegexValidator

phone_validator = RegexValidator(
    regex=r'^\+48\d{9}$',
    message='Numer telefonu musi być w formacie +48XXXXXXXXX',
)


class UserProfileForm(forms.ModelForm):
    """Form for users to update their profile."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'avatar']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'last_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'phone': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': '+48123456789',
            }),
            'avatar': forms.FileInput(attrs={'class': 'file-input file-input-bordered w-full'}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            phone_validator(phone)
        return phone


class StudentProfileForm(forms.ModelForm):
    """Form for student-specific profile fields."""

    class Meta:
        model = StudentProfile
        fields = [
            'class_name', 'current_level', 'learning_goals',
            'parent_name', 'parent_phone', 'parent_email',
            'secondary_parent_name', 'secondary_parent_phone',
            'emergency_contact', 'notes',
        ]
        widgets = {
            'class_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'current_level': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'learning_goals': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3,
            }),
            'parent_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'parent_phone': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'parent_email': forms.EmailInput(attrs={'class': 'input input-bordered w-full'}),
            'secondary_parent_name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'secondary_parent_phone': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'notes': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3,
            }),
        }


class TutorProfileForm(forms.ModelForm):
    """Form for tutor-specific profile fields."""

    class Meta:
        model = TutorProfile
        fields = [
            'bio', 'education', 'experience_years',
            'hourly_rate', 'certifications', 'availability_hours',
        ]
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 4,
            }),
            'education': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'experience_years': forms.NumberInput(attrs={'class': 'input input-bordered w-full'}),
            'hourly_rate': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'step': '0.01',
            }),
        }
```

---

### Task 023: Role-Based Permission System

**Files**: `apps/core/permissions.py`, `apps/core/mixins.py`

```python
# apps/core/permissions.py
from enum import Enum
from typing import List


class Permission(str, Enum):
    # User management
    USER_CREATE = 'user:create'
    USER_READ = 'user:read'
    USER_UPDATE = 'user:update'
    USER_DELETE = 'user:delete'
    USER_EXPORT = 'user:export'

    # Lesson management
    LESSON_CREATE = 'lesson:create'
    LESSON_READ = 'lesson:read'
    LESSON_UPDATE = 'lesson:update'
    LESSON_DELETE = 'lesson:delete'

    # Administrative
    ADMIN_DASHBOARD = 'admin:dashboard'
    ADMIN_SETTINGS = 'admin:settings'
    ADMIN_AUDIT = 'admin:audit'

    # Billing
    INVOICE_CREATE = 'invoice:create'
    INVOICE_READ = 'invoice:read'
    INVOICE_SEND = 'invoice:send'


ROLE_PERMISSIONS = {
    'admin': [
        Permission.USER_CREATE,
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.USER_DELETE,
        Permission.USER_EXPORT,
        Permission.LESSON_CREATE,
        Permission.LESSON_READ,
        Permission.LESSON_UPDATE,
        Permission.LESSON_DELETE,
        Permission.ADMIN_DASHBOARD,
        Permission.ADMIN_SETTINGS,
        Permission.ADMIN_AUDIT,
        Permission.INVOICE_CREATE,
        Permission.INVOICE_READ,
        Permission.INVOICE_SEND,
    ],
    'tutor': [
        Permission.USER_READ,  # Own students only
        Permission.LESSON_READ,
        Permission.LESSON_UPDATE,  # Own lessons only
    ],
    'student': [
        Permission.LESSON_READ,  # Own lessons only
    ],
}


def has_permission(user, permission: Permission) -> bool:
    """Check if user has a specific permission."""
    if not user.is_authenticated:
        return False

    user_permissions = ROLE_PERMISSIONS.get(user.role, [])
    return permission in user_permissions


def has_any_permission(user, permissions: List[Permission]) -> bool:
    """Check if user has any of the specified permissions."""
    return any(has_permission(user, p) for p in permissions)


def has_all_permissions(user, permissions: List[Permission]) -> bool:
    """Check if user has all specified permissions."""
    return all(has_permission(user, p) for p in permissions)
```

```python
# apps/core/mixins.py
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied

from .permissions import Permission, has_permission


class PermissionRequiredMixin(UserPassesTestMixin):
    """Mixin that checks for specific permissions."""

    required_permissions: list = []

    def test_func(self):
        if not self.request.user.is_authenticated:
            return False

        for permission in self.required_permissions:
            if not has_permission(self.request.user, permission):
                return False
        return True

    def handle_no_permission(self):
        raise PermissionDenied('Brak uprawnień do tej akcji.')


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin requiring admin role."""

    def test_func(self):
        return (
            self.request.user.is_authenticated
            and self.request.user.is_admin
        )


class TutorRequiredMixin(UserPassesTestMixin):
    """Mixin requiring tutor or admin role."""

    def test_func(self):
        user = self.request.user
        return (
            user.is_authenticated
            and (user.is_tutor or user.is_admin)
        )


class StudentRequiredMixin(UserPassesTestMixin):
    """Mixin requiring student, tutor, or admin role."""

    def test_func(self):
        return self.request.user.is_authenticated
```

---

### Task 024: User Status Management

**Files**: `apps/accounts/views.py`

```python
# apps/accounts/views.py (continued)
from django.views import View
from django.shortcuts import get_object_or_404
from django.utils import timezone


class UserStatusToggleView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Toggle user active/inactive status via HTMX."""

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)

        # Toggle status
        user.is_active = not user.is_active
        user.save(update_fields=['is_active'])

        # Log the change
        from apps.core.models import AuditLog
        AuditLog.objects.create(
            user=request.user,
            action='update',
            model_type='User',
            model_id=str(user.pk),
            old_values={'is_active': not user.is_active},
            new_values={'is_active': user.is_active},
            ip_address=request.META.get('REMOTE_ADDR'),
        )

        # Return updated badge
        status = 'aktywny' if user.is_active else 'nieaktywny'
        badge_class = 'badge-success' if user.is_active else 'badge-error'

        return HttpResponse(f'''
            <span class="badge {badge_class}">{status}</span>
        ''')
```

---

### Task 026: User Search and Filtering

**Files**: `apps/accounts/views.py`, `apps/accounts/filters.py`

```python
# apps/accounts/filters.py
import django_filters
from django.contrib.auth import get_user_model

User = get_user_model()


class UserFilter(django_filters.FilterSet):
    """Filter for user list."""

    search = django_filters.CharFilter(
        method='filter_search',
        label='Szukaj',
    )
    role = django_filters.ChoiceFilter(
        choices=[
            ('admin', 'Administrator'),
            ('tutor', 'Korepetytor'),
            ('student', 'Uczeń'),
        ],
    )
    is_active = django_filters.BooleanFilter()
    is_profile_completed = django_filters.BooleanFilter()

    class Meta:
        model = User
        fields = ['role', 'is_active', 'is_profile_completed']

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            models.Q(email__icontains=value) |
            models.Q(first_name__icontains=value) |
            models.Q(last_name__icontains=value)
        )
```

```python
# apps/accounts/views.py (continued)
from django_filters.views import FilterView


class UserListView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, FilterView):
    """List all users with filtering and search."""

    model = User
    template_name = 'admin_panel/users/user_list.html'
    partial_template_name = 'admin_panel/users/partials/_user_table.html'
    context_object_name = 'users'
    filterset_class = UserFilter
    paginate_by = 20

    def get_queryset(self):
        return User.objects.select_related(
            'tutor_profile',
            'student_profile',
        ).order_by('-date_joined')
```

```html
<!-- templates/admin_panel/users/partials/_user_search.html -->
<div class="flex gap-4 mb-6"
     hx-get="{% url 'accounts:user-list' %}"
     hx-trigger="input changed delay:300ms from:#search-input, change from:.filter-select"
     hx-target="#user-table"
     hx-swap="innerHTML"
     hx-include="[name='search'], [name='role'], [name='is_active']">

    <div class="form-control flex-1">
        <input type="text"
               id="search-input"
               name="search"
               placeholder="Szukaj po imieniu, nazwisku lub email..."
               class="input input-bordered w-full"
               value="{{ request.GET.search }}">
    </div>

    <select name="role" class="select select-bordered filter-select">
        <option value="">Wszystkie role</option>
        <option value="admin" {% if request.GET.role == 'admin' %}selected{% endif %}>Administrator</option>
        <option value="tutor" {% if request.GET.role == 'tutor' %}selected{% endif %}>Korepetytor</option>
        <option value="student" {% if request.GET.role == 'student' %}selected{% endif %}>Uczeń</option>
    </select>

    <select name="is_active" class="select select-bordered filter-select">
        <option value="">Wszystkie statusy</option>
        <option value="true" {% if request.GET.is_active == 'true' %}selected{% endif %}>Aktywni</option>
        <option value="false" {% if request.GET.is_active == 'false' %}selected{% endif %}>Nieaktywni</option>
    </select>
</div>
```

---

## COMPLETION CHECKLIST

### Technical Validation

- [ ] Direct user creation working (admin only)
- [ ] User profile forms functional for all roles
- [ ] Permission system enforced across application
- [ ] User status management operational
- [ ] Password management secure
- [ ] User search and filtering responsive
- [ ] Data export compliance with RODO
- [ ] Audit logging capturing all actions

### Feature Validation

- [ ] Admin can create users directly
- [ ] Temporary passwords generated and emailed
- [ ] Users must change password on first login
- [ ] Profile completion tracking accurate
- [ ] Role-specific fields display correctly
- [ ] User status affects system access
- [ ] Search/filter performance acceptable

### HTMX Integration

- [ ] Forms submit via HTMX
- [ ] Live search with debounce working
- [ ] Status toggle updates inline
- [ ] Modal forms functional
- [ ] Proper loading indicators

---

## SUCCESS METRICS

| Metric | Target |
|--------|--------|
| User Creation | Admin can create 100+ users efficiently |
| Security | 100% permission compliance |
| Performance | User operations <500ms |
| Compliance | RODO requirements met |
| User Experience | Intuitive forms and feedback |

---

**Sprint Completion**: All 12 tasks completed and validated
**Next Sprint**: 2.2 - Profile Management & Advanced Features
