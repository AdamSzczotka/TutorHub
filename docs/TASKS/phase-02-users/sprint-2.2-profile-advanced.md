# Phase 2 - Sprint 2.2: Profile Management & Advanced Features (Django)

## Tasks 033-044: Advanced User Operations & Management

> **Duration**: Week 5-6 of Phase 2 (10 working days)
> **Goal**: Complete advanced user management features including bulk operations, analytics, and profile completion
> **Dependencies**: Sprint 2.1 completed (User CRUD & Direct Creation)

---

## SPRINT OVERVIEW

| Task ID | Description                    | Priority | Dependencies        |
| ------- | ------------------------------ | -------- | ------------------- |
| 033     | Profile completion wizard      | High     | Sprint 2.1 complete |
| 034     | Avatar upload and management   | Medium   | Task 033            |
| 035     | User import from CSV/Excel     | High     | Task 034            |
| 036     | User notification preferences  | High     | Task 035            |
| 037     | Advanced user filtering        | High     | Task 036            |
| 038     | User relationship mapping      | Medium   | Task 037            |
| 039     | User activity tracking         | Medium   | Task 038            |
| 040     | Bulk user operations interface | High     | Task 039            |
| 041     | User data archiving system     | Medium   | Task 040            |
| 042     | User verification workflow     | High     | Task 041            |
| 043     | Parent portal access setup     | High     | Task 042            |
| 044     | User management analytics      | Medium   | Task 043            |

---

## DETAILED TASK BREAKDOWN

### Task 033: Profile Completion Wizard

**Files**: `apps/accounts/services.py`, `apps/accounts/views.py`, `templates/accounts/profile_wizard.html`

#### Profile Completion Service

```python
# apps/accounts/services.py
from dataclasses import dataclass
from typing import List, Optional
from django.contrib.auth import get_user_model

User = get_user_model()


@dataclass
class ProfileStep:
    id: str
    title: str
    required_fields: List[str]
    is_complete: bool


class ProfileCompletionService:
    """Service for calculating profile completion."""

    def __init__(self, user: User):
        self.user = user
        self.steps = self._get_steps()

    def _get_steps(self) -> List[ProfileStep]:
        """Get profile completion steps based on user role."""
        base_steps = [
            ProfileStep(
                id='basic-info',
                title='Podstawowe informacje',
                required_fields=['first_name', 'last_name', 'phone'],
                is_complete=bool(
                    self.user.first_name and
                    self.user.last_name and
                    self.user.phone
                ),
            ),
            ProfileStep(
                id='password-changed',
                title='Zmiana hasła',
                required_fields=['password'],
                is_complete=not self.user.first_login,
            ),
        ]

        if self.user.is_student:
            profile = getattr(self.user, 'student_profile', None)
            base_steps.extend([
                ProfileStep(
                    id='parent-info',
                    title='Dane rodzica/opiekuna',
                    required_fields=['parent_name', 'parent_email', 'parent_phone'],
                    is_complete=bool(
                        profile and
                        profile.parent_name and
                        profile.parent_email and
                        profile.parent_phone
                    ),
                ),
                ProfileStep(
                    id='academic-info',
                    title='Informacje szkolne',
                    required_fields=['class_name', 'learning_goals'],
                    is_complete=bool(
                        profile and
                        profile.class_name and
                        profile.learning_goals
                    ),
                ),
            ])

        elif self.user.is_tutor:
            profile = getattr(self.user, 'tutor_profile', None)
            base_steps.extend([
                ProfileStep(
                    id='professional-info',
                    title='Informacje zawodowe',
                    required_fields=['education', 'experience_years'],
                    is_complete=bool(
                        profile and
                        profile.education and
                        profile.experience_years is not None
                    ),
                ),
                ProfileStep(
                    id='teaching-info',
                    title='Informacje o nauczaniu',
                    required_fields=['bio', 'hourly_rate'],
                    is_complete=bool(
                        profile and
                        profile.bio and
                        profile.hourly_rate
                    ),
                ),
            ])

        return base_steps

    @property
    def percentage(self) -> int:
        """Calculate completion percentage."""
        if not self.steps:
            return 100
        completed = sum(1 for step in self.steps if step.is_complete)
        return int((completed / len(self.steps)) * 100)

    @property
    def completed_steps(self) -> int:
        return sum(1 for step in self.steps if step.is_complete)

    @property
    def total_steps(self) -> int:
        return len(self.steps)

    @property
    def next_step(self) -> Optional[ProfileStep]:
        """Get next incomplete step."""
        for step in self.steps:
            if not step.is_complete:
                return step
        return None

    @property
    def missing_fields(self) -> List[str]:
        """Get all missing required fields."""
        fields = []
        for step in self.steps:
            if not step.is_complete:
                fields.extend(step.required_fields)
        return fields
```

#### Profile Wizard View

```python
# apps/accounts/views.py (continued)
from django.views.generic import TemplateView, FormView
from .services import ProfileCompletionService


class ProfileWizardView(LoginRequiredMixin, TemplateView):
    """Profile completion wizard view."""

    template_name = 'accounts/profile_wizard.html'

    def get_context_data(self, **kwargs):
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

    partial_template_name = 'accounts/partials/_profile_step_form.html'

    def get_form_class(self):
        step_id = self.kwargs.get('step_id')
        user = self.request.user

        if step_id == 'basic-info':
            return UserProfileForm
        elif step_id == 'parent-info' and user.is_student:
            return StudentProfileForm
        elif step_id in ('professional-info', 'teaching-info') and user.is_tutor:
            return TutorProfileForm

        return UserProfileForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        step_id = self.kwargs.get('step_id')
        user = self.request.user

        if step_id == 'basic-info':
            kwargs['instance'] = user
        elif step_id == 'parent-info' and user.is_student:
            kwargs['instance'] = getattr(user, 'student_profile', None)
        elif step_id in ('professional-info', 'teaching-info') and user.is_tutor:
            kwargs['instance'] = getattr(user, 'tutor_profile', None)

        return kwargs

    def form_valid(self, form):
        form.save()

        # Check if profile is now complete
        completion = ProfileCompletionService(self.request.user)
        if completion.percentage == 100:
            self.request.user.is_profile_completed = True
            self.request.user.save(update_fields=['is_profile_completed'])
            messages.success(self.request, 'Profil został uzupełniony!')

        if self.request.htmx:
            # Return updated wizard state
            return render(self.request, 'accounts/partials/_wizard_progress.html', {
                'completion': completion,
            })

        return redirect('accounts:profile-wizard')
```

#### Profile Wizard Template

```html
<!-- templates/accounts/profile_wizard.html -->
{% extends "base.html" %}

{% block content %}
<div class="max-w-2xl mx-auto">
    <div class="card bg-base-100 shadow-xl">
        <div class="card-body">
            <h2 class="card-title text-2xl flex items-center gap-2">
                <svg class="w-6 h-6 text-warning" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
                </svg>
                Uzupełnij swój profil
                <span class="text-sm font-normal text-base-content/60">
                    ({{ completion.completed_steps }}/{{ completion.total_steps }})
                </span>
            </h2>

            <!-- Progress Bar -->
            <div class="w-full bg-base-200 rounded-full h-4 mb-6">
                <div class="bg-primary h-4 rounded-full transition-all duration-500"
                     style="width: {{ percentage }}%"></div>
            </div>

            <!-- Steps List -->
            <div class="space-y-4" id="wizard-steps">
                {% for step in steps %}
                <div class="flex items-center gap-4 p-4 rounded-lg cursor-pointer transition-colors
                            {% if step.is_complete %}bg-success/10{% else %}bg-base-200 hover:bg-base-300{% endif %}"
                     hx-get="{% url 'accounts:profile-step' step.id %}"
                     hx-target="#step-form-container"
                     hx-swap="innerHTML">

                    <!-- Status Icon -->
                    {% if step.is_complete %}
                        <div class="w-8 h-8 rounded-full bg-success flex items-center justify-center">
                            <svg class="w-5 h-5 text-success-content" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
                            </svg>
                        </div>
                    {% else %}
                        <div class="w-8 h-8 rounded-full border-2 border-base-300"></div>
                    {% endif %}

                    <!-- Step Info -->
                    <div class="flex-1">
                        <h3 class="font-medium {% if step.is_complete %}text-success{% endif %}">
                            {{ step.title }}
                        </h3>
                        {% if not step.is_complete %}
                            <p class="text-sm text-base-content/60">
                                Wymagane: {{ step.required_fields|join:", " }}
                            </p>
                        {% endif %}
                    </div>

                    <!-- Action Button -->
                    {% if not step.is_complete %}
                        <button class="btn btn-sm btn-primary">
                            Uzupełnij
                        </button>
                    {% endif %}
                </div>
                {% endfor %}
            </div>

            <!-- Step Form Container -->
            <div id="step-form-container" class="mt-6"></div>

            {% if next_step %}
                <div class="card-actions justify-end mt-6">
                    <button class="btn btn-primary w-full"
                            hx-get="{% url 'accounts:profile-step' next_step.id %}"
                            hx-target="#step-form-container"
                            hx-swap="innerHTML">
                        Kontynuuj uzupełnianie profilu
                    </button>
                </div>
            {% endif %}
        </div>
    </div>
</div>
{% endblock %}
```

---

### Task 034: Avatar Upload and Management

**Files**: `apps/accounts/views.py`, `apps/accounts/forms.py`

```python
# apps/accounts/forms.py (continued)
from django.core.validators import FileExtensionValidator
from PIL import Image
import io


class AvatarUploadForm(forms.Form):
    """Form for avatar upload with validation."""

    avatar = forms.ImageField(
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp']),
        ],
        widget=forms.FileInput(attrs={
            'class': 'file-input file-input-bordered w-full',
            'accept': 'image/*',
        }),
    )

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')

        if avatar:
            # Check file size (max 5MB)
            if avatar.size > 5 * 1024 * 1024:
                raise forms.ValidationError('Plik jest za duży. Maksymalny rozmiar to 5MB.')

            # Validate image dimensions
            try:
                img = Image.open(avatar)
                if img.width < 100 or img.height < 100:
                    raise forms.ValidationError('Obraz musi mieć minimum 100x100 pikseli.')
            except Exception:
                raise forms.ValidationError('Nieprawidłowy plik obrazu.')

        return avatar
```

```python
# apps/accounts/views.py (continued)
from django.core.files.base import ContentFile
from PIL import Image
import io


class AvatarUploadView(LoginRequiredMixin, HTMXMixin, FormView):
    """Handle avatar upload with image processing."""

    form_class = AvatarUploadForm
    template_name = 'accounts/partials/_avatar_upload.html'

    def form_valid(self, form):
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
            return render(self.request, 'accounts/partials/_avatar_preview.html', {
                'user': user,
            })

        return redirect('accounts:profile')


class AvatarDeleteView(LoginRequiredMixin, View):
    """Delete user avatar."""

    def post(self, request):
        user = request.user

        if user.avatar:
            user.avatar.delete(save=True)
            messages.success(request, 'Avatar został usunięty.')

        if request.htmx:
            return render(request, 'accounts/partials/_avatar_preview.html', {
                'user': user,
            })

        return redirect('accounts:profile')
```

```html
<!-- templates/accounts/partials/_avatar_upload.html -->
<div class="flex flex-col items-center gap-4"
     x-data="{ preview: null }">

    <!-- Current Avatar -->
    <div class="avatar">
        <div class="w-24 rounded-full ring ring-primary ring-offset-base-100 ring-offset-2">
            {% if user.avatar %}
                <img src="{{ user.avatar.url }}" alt="Avatar"
                     x-show="!preview">
            {% else %}
                <div class="bg-neutral text-neutral-content w-24 h-24 flex items-center justify-center text-3xl font-bold"
                     x-show="!preview">
                    {{ user.first_name.0 }}{{ user.last_name.0 }}
                </div>
            {% endif %}
            <img :src="preview" alt="Preview" x-show="preview" x-cloak>
        </div>
    </div>

    <!-- Upload Form -->
    <form method="post"
          enctype="multipart/form-data"
          hx-post="{% url 'accounts:avatar-upload' %}"
          hx-target="#avatar-container"
          hx-swap="innerHTML"
          hx-encoding="multipart/form-data">
        {% csrf_token %}

        <input type="file"
               name="avatar"
               accept="image/*"
               class="file-input file-input-bordered file-input-sm"
               @change="
                   const file = $event.target.files[0];
                   if (file) {
                       const reader = new FileReader();
                       reader.onload = (e) => preview = e.target.result;
                       reader.readAsDataURL(file);
                   }
               ">

        <div class="flex gap-2 mt-4" x-show="preview">
            <button type="submit" class="btn btn-primary btn-sm">
                Zapisz
            </button>
            <button type="button"
                    class="btn btn-ghost btn-sm"
                    @click="preview = null; $el.closest('form').reset()">
                Anuluj
            </button>
        </div>
    </form>

    {% if user.avatar %}
        <button class="btn btn-error btn-sm btn-outline"
                hx-post="{% url 'accounts:avatar-delete' %}"
                hx-target="#avatar-container"
                hx-swap="innerHTML"
                hx-confirm="Czy na pewno chcesz usunąć avatar?">
            Usuń avatar
        </button>
    {% endif %}
</div>
```

---

### Task 035: User Import from CSV/Excel

**Files**: `apps/accounts/views.py`, `apps/accounts/forms.py`, `apps/accounts/services.py`

```python
# apps/accounts/services.py (continued)
import csv
import io
from typing import Dict, List, Tuple
from django.db import transaction


class UserImportService:
    """Service for importing users from CSV."""

    REQUIRED_COLUMNS = ['email', 'first_name', 'last_name', 'role']
    OPTIONAL_COLUMNS = ['phone', 'class_name', 'parent_name', 'parent_email', 'parent_phone']

    def __init__(self, csv_content: str, created_by: User):
        self.csv_content = csv_content
        self.created_by = created_by
        self.errors = []
        self.valid_rows = []

    def validate(self) -> Tuple[int, int, List[Dict]]:
        """Validate CSV and return (total, valid, errors)."""
        try:
            reader = csv.DictReader(io.StringIO(self.csv_content))

            # Check columns
            missing_cols = set(self.REQUIRED_COLUMNS) - set(reader.fieldnames or [])
            if missing_cols:
                self.errors.append({
                    'row': 0,
                    'errors': [f'Brakujące kolumny: {", ".join(missing_cols)}'],
                })
                return 0, 0, self.errors

            for idx, row in enumerate(reader, start=2):
                row_errors = self._validate_row(row, idx)
                if row_errors:
                    self.errors.append({
                        'row': idx,
                        'errors': row_errors,
                    })
                else:
                    self.valid_rows.append(row)

            return len(self.valid_rows) + len(self.errors), len(self.valid_rows), self.errors

        except Exception as e:
            self.errors.append({'row': 0, 'errors': [f'Błąd parsowania CSV: {str(e)}']})
            return 0, 0, self.errors

    def _validate_row(self, row: Dict, idx: int) -> List[str]:
        """Validate single row."""
        errors = []

        # Required fields
        if not row.get('email'):
            errors.append('Email jest wymagany')
        elif not self._is_valid_email(row['email']):
            errors.append('Nieprawidłowy format email')

        if not row.get('first_name'):
            errors.append('Imię jest wymagane')

        if not row.get('last_name'):
            errors.append('Nazwisko jest wymagane')

        if row.get('role') not in ('student', 'tutor', 'admin'):
            errors.append('Rola musi być: student, tutor lub admin')

        # Check for existing email
        if row.get('email') and User.objects.filter(email=row['email']).exists():
            errors.append('Użytkownik o tym email już istnieje')

        return errors

    def _is_valid_email(self, email: str) -> bool:
        import re
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return bool(re.match(pattern, email))

    @transaction.atomic
    def execute(self, send_emails: bool = True) -> Tuple[List[Dict], List[Dict]]:
        """Execute import and return (results, errors)."""
        from .forms import generate_temp_password
        from .tasks import send_welcome_email_task

        results = []

        for row in self.valid_rows:
            try:
                temp_password = generate_temp_password()

                user = User.objects.create(
                    email=row['email'],
                    first_name=row['first_name'],
                    last_name=row['last_name'],
                    phone=row.get('phone', ''),
                    role=row['role'],
                    first_login=True,
                    is_profile_completed=False,
                )
                user.set_password(temp_password)
                user.save()

                # Create role-specific profile
                if row['role'] == 'student':
                    from apps.students.models import StudentProfile
                    StudentProfile.objects.create(
                        user=user,
                        class_name=row.get('class_name', ''),
                        parent_name=row.get('parent_name', ''),
                        parent_email=row.get('parent_email', ''),
                        parent_phone=row.get('parent_phone', ''),
                    )
                elif row['role'] == 'tutor':
                    from apps.tutors.models import TutorProfile
                    TutorProfile.objects.create(user=user)

                # Log creation
                from .models import UserCreationLog
                UserCreationLog.objects.create(
                    created_user=user,
                    created_by=self.created_by,
                    email_sent=send_emails,
                )

                # Send email
                if send_emails:
                    send_welcome_email_task.delay(user.id, temp_password)

                results.append({
                    'email': user.email,
                    'user_id': user.id,
                    'temp_password': temp_password if not send_emails else None,
                })

            except Exception as e:
                self.errors.append({
                    'row': row.get('email', 'unknown'),
                    'errors': [str(e)],
                })

        return results, self.errors
```

```python
# apps/accounts/views.py (continued)
class UserImportView(LoginRequiredMixin, AdminRequiredMixin, FormView):
    """View for importing users from CSV."""

    template_name = 'admin_panel/users/import.html'
    form_class = forms.Form  # Simple form with file field

    def post(self, request):
        csv_file = request.FILES.get('csv_file')

        if not csv_file:
            messages.error(request, 'Wybierz plik CSV.')
            return redirect('accounts:user-import')

        # Read CSV content
        try:
            csv_content = csv_file.read().decode('utf-8')
        except UnicodeDecodeError:
            csv_content = csv_file.read().decode('cp1250')  # Polish Windows encoding

        # Validate
        service = UserImportService(csv_content, request.user)
        total, valid, errors = service.validate()

        if 'validate_only' in request.POST:
            return render(request, 'admin_panel/users/partials/_import_preview.html', {
                'total': total,
                'valid': valid,
                'errors': errors,
                'preview': service.valid_rows[:5],
            })

        # Execute import
        send_emails = 'send_emails' in request.POST
        results, import_errors = service.execute(send_emails)

        messages.success(
            request,
            f'Zaimportowano {len(results)} użytkowników. Błędy: {len(import_errors)}.'
        )

        return redirect('accounts:user-list')
```

---

### Task 040: Bulk User Operations Interface

**Files**: `apps/accounts/views.py`, `templates/admin_panel/users/`

```python
# apps/accounts/views.py (continued)
class BulkUserActionView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Handle bulk operations on users."""

    def post(self, request):
        action = request.POST.get('action')
        user_ids = request.POST.getlist('user_ids')

        if not user_ids:
            messages.warning(request, 'Nie wybrano żadnych użytkowników.')
            return redirect('accounts:user-list')

        users = User.objects.filter(id__in=user_ids)
        count = users.count()

        if action == 'activate':
            users.update(is_active=True)
            messages.success(request, f'Aktywowano {count} użytkowników.')

        elif action == 'deactivate':
            users.update(is_active=False)
            messages.success(request, f'Dezaktywowano {count} użytkowników.')

        elif action == 'send_password_reset':
            from .tasks import send_password_reset_task
            for user in users:
                send_password_reset_task.delay(user.id)
            messages.success(request, f'Wysłano reset hasła do {count} użytkowników.')

        elif action == 'export':
            return self._export_users(users)

        elif action == 'delete':
            if not request.user.is_superuser:
                messages.error(request, 'Tylko superuser może usuwać użytkowników.')
            else:
                users.delete()
                messages.success(request, f'Usunięto {count} użytkowników.')

        return redirect('accounts:user-list')

    def _export_users(self, users):
        """Export users to CSV."""
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="users_export.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Email', 'Imię', 'Nazwisko', 'Rola', 'Telefon',
            'Status', 'Data rejestracji'
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
```

```html
<!-- templates/admin_panel/users/partials/_bulk_actions.html -->
<div x-data="{ selectedUsers: [], selectAll: false }"
     x-init="$watch('selectAll', value => {
         selectedUsers = value ? [...document.querySelectorAll('[name=user_id]')].map(el => el.value) : []
     })">

    <!-- Bulk Action Bar -->
    <div class="bg-base-200 p-4 rounded-lg mb-4"
         x-show="selectedUsers.length > 0"
         x-transition>
        <form method="post" action="{% url 'accounts:bulk-action' %}">
            {% csrf_token %}

            <template x-for="id in selectedUsers" :key="id">
                <input type="hidden" name="user_ids" :value="id">
            </template>

            <div class="flex items-center gap-4">
                <span class="font-medium">
                    Wybrano: <span x-text="selectedUsers.length"></span> użytkowników
                </span>

                <select name="action" class="select select-bordered select-sm">
                    <option value="">Wybierz akcję...</option>
                    <option value="activate">Aktywuj</option>
                    <option value="deactivate">Dezaktywuj</option>
                    <option value="send_password_reset">Wyślij reset hasła</option>
                    <option value="export">Eksportuj do CSV</option>
                    <option value="delete">Usuń</option>
                </select>

                <button type="submit" class="btn btn-primary btn-sm">
                    Wykonaj
                </button>

                <button type="button"
                        class="btn btn-ghost btn-sm"
                        @click="selectedUsers = []; selectAll = false">
                    Anuluj
                </button>
            </div>
        </form>
    </div>

    <!-- User Table with Checkboxes -->
    <table class="table">
        <thead>
            <tr>
                <th>
                    <input type="checkbox"
                           class="checkbox"
                           x-model="selectAll">
                </th>
                <th>Użytkownik</th>
                <th>Rola</th>
                <th>Status</th>
                <th>Akcje</th>
            </tr>
        </thead>
        <tbody>
            {% for user in users %}
            <tr>
                <td>
                    <input type="checkbox"
                           name="user_id"
                           value="{{ user.id }}"
                           class="checkbox"
                           x-model="selectedUsers"
                           :checked="selectedUsers.includes('{{ user.id }}')">
                </td>
                <td>
                    <div class="flex items-center gap-3">
                        <div class="avatar">
                            <div class="w-10 rounded-full">
                                {% if user.avatar %}
                                    <img src="{{ user.avatar.url }}" alt="">
                                {% else %}
                                    <div class="bg-neutral text-neutral-content w-10 h-10 flex items-center justify-center">
                                        {{ user.first_name.0 }}{{ user.last_name.0 }}
                                    </div>
                                {% endif %}
                            </div>
                        </div>
                        <div>
                            <div class="font-bold">{{ user.get_full_name }}</div>
                            <div class="text-sm opacity-50">{{ user.email }}</div>
                        </div>
                    </div>
                </td>
                <td>
                    <span class="badge badge-outline">{{ user.get_role_display }}</span>
                </td>
                <td>
                    <span class="badge {% if user.is_active %}badge-success{% else %}badge-error{% endif %}">
                        {% if user.is_active %}Aktywny{% else %}Nieaktywny{% endif %}
                    </span>
                </td>
                <td>
                    <a href="{% url 'accounts:user-detail' user.id %}" class="btn btn-ghost btn-xs">
                        Szczegóły
                    </a>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
```

---

## COMPLETION CHECKLIST

### Technical Validation

- [ ] Profile completion wizard functional
- [ ] Avatar upload and processing working
- [ ] CSV import validates and executes properly
- [ ] Notification preferences saving
- [ ] Advanced filtering responsive
- [ ] Bulk operations interface functional
- [ ] User export working (CSV)

### Feature Validation

- [ ] Users guided through profile completion
- [ ] Avatars display correctly across application
- [ ] CSV imports create users successfully
- [ ] Notification settings affect delivery
- [ ] Filtering provides relevant results
- [ ] Bulk actions execute correctly

### HTMX Integration

- [ ] Profile wizard steps load dynamically
- [ ] Avatar preview updates without reload
- [ ] Import preview renders inline
- [ ] Bulk selection state managed

---

## SUCCESS METRICS

| Metric | Target |
|--------|--------|
| Profile Completion | 80%+ users complete profiles within 7 days |
| Import Efficiency | 1000+ users imported per minute |
| User Experience | <2s response times for all operations |
| Data Quality | <1% import error rate |

---

**Sprint Completion**: All 12 tasks completed and validated
**Next Phase**: Phase 3 - Admin Panel Development
