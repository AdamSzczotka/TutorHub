# Phase 3 - Sprint 3.2: System Configuration (Django)

## Tasks 057-068: System Settings & Management

> **Duration**: Week 9-10 (10 working days)
> **Goal**: System configuration, subjects, rooms, and audit logging
> **Dependencies**: Sprint 3.1 completed

---

## SPRINT OVERVIEW

| Task ID | Description                  | Priority | Dependencies        |
| ------- | ---------------------------- | -------- | ------------------- |
| 057     | Subject management           | Critical | Sprint 3.1 complete |
| 058     | Room management              | Critical | Task 057            |
| 059     | System settings panel        | Critical | Task 058            |
| 060     | Email template management    | High     | Task 059            |
| 061     | Audit log viewer             | High     | Task 060            |
| 062     | Backup and restore           | High     | Task 061            |

---

## SUBJECT MANAGEMENT

### Subject Views

**File**: `apps/subjects/views.py`

```python
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import HttpResponse

from apps.core.mixins import AdminRequiredMixin, HTMXMixin
from .models import Subject, Level
from .forms import SubjectForm, LevelForm


class SubjectListView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, ListView):
    model = Subject
    template_name = 'admin_panel/subjects/list.html'
    partial_template_name = 'admin_panel/subjects/partials/_subject_list.html'
    context_object_name = 'subjects'

    def get_queryset(self):
        return Subject.objects.annotate(
            lesson_count=Count('lessons')
        ).order_by('name')


class SubjectCreateView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, CreateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'admin_panel/subjects/partials/_subject_form.html'
    success_url = reverse_lazy('subjects:list')

    def form_valid(self, form):
        subject = form.save()

        if self.request.htmx:
            return HttpResponse(
                status=204,
                headers={
                    'HX-Trigger': 'subjectCreated',
                    'HX-Reswap': 'none',
                }
            )
        return super().form_valid(form)


class SubjectUpdateView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, UpdateView):
    model = Subject
    form_class = SubjectForm
    template_name = 'admin_panel/subjects/partials/_subject_form.html'
    success_url = reverse_lazy('subjects:list')


class SubjectDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Subject
    success_url = reverse_lazy('subjects:list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.lessons.exists():
            return HttpResponse(
                '<div class="alert alert-error">Nie można usunąć - przedmiot ma przypisane lekcje.</div>',
                status=400
            )

        self.object.delete()

        if request.htmx:
            return HttpResponse(status=204, headers={'HX-Trigger': 'subjectDeleted'})

        return redirect(self.success_url)
```

### Subject Templates

**File**: `templates/admin_panel/subjects/list.html`

```html
{% extends "admin_panel/base.html" %}

{% block content %}
<div class="space-y-6">
    <div class="flex items-center justify-between">
        <h1 class="text-2xl font-bold">Przedmioty</h1>
        <button class="btn btn-primary"
                hx-get="{% url 'subjects:create' %}"
                hx-target="#modal-content"
                hx-swap="innerHTML"
                onclick="document.getElementById('modal').showModal()">
            + Dodaj przedmiot
        </button>
    </div>

    <div id="subject-list"
         hx-get="{% url 'subjects:list' %}"
         hx-trigger="subjectCreated from:body, subjectDeleted from:body"
         hx-swap="innerHTML">
        {% include "admin_panel/subjects/partials/_subject_list.html" %}
    </div>
</div>

<!-- Modal -->
<dialog id="modal" class="modal">
    <div class="modal-box">
        <div id="modal-content"></div>
    </div>
    <form method="dialog" class="modal-backdrop">
        <button>close</button>
    </form>
</dialog>
{% endblock %}
```

---

## ROOM MANAGEMENT

### Room Views

**File**: `apps/rooms/views.py`

```python
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from apps.core.mixins import AdminRequiredMixin, HTMXMixin
from .models import Room
from .forms import RoomForm


class RoomListView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, ListView):
    model = Room
    template_name = 'admin_panel/rooms/list.html'
    partial_template_name = 'admin_panel/rooms/partials/_room_list.html'
    context_object_name = 'rooms'

    def get_queryset(self):
        return Room.objects.annotate(
            lesson_count=Count('lessons')
        ).order_by('name')


class RoomCreateView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, CreateView):
    model = Room
    form_class = RoomForm
    template_name = 'admin_panel/rooms/partials/_room_form.html'
    success_url = reverse_lazy('rooms:list')

    def form_valid(self, form):
        room = form.save()

        if self.request.htmx:
            return HttpResponse(
                status=204,
                headers={'HX-Trigger': 'roomCreated'}
            )
        return super().form_valid(form)
```

### Room Form

**File**: `apps/rooms/forms.py`

```python
from django import forms
from .models import Room


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['name', 'capacity', 'location', 'description', 'equipment', 'is_active', 'is_virtual']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'capacity': forms.NumberInput(attrs={'class': 'input input-bordered w-full', 'min': 1}),
            'location': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'description': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 3}),
        }
```

---

## AUDIT LOG VIEWER

### Audit Log View

**File**: `apps/core/views.py`

```python
from django.views.generic import ListView
from django_filters.views import FilterView
from .models import AuditLog
from .filters import AuditLogFilter


class AuditLogListView(LoginRequiredMixin, AdminRequiredMixin, FilterView):
    model = AuditLog
    template_name = 'admin_panel/audit/list.html'
    context_object_name = 'logs'
    filterset_class = AuditLogFilter
    paginate_by = 50

    def get_queryset(self):
        return AuditLog.objects.select_related('user').order_by('-created_at')
```

### Audit Log Filter

**File**: `apps/core/filters.py`

```python
import django_filters
from .models import AuditLog


class AuditLogFilter(django_filters.FilterSet):
    action = django_filters.ChoiceFilter(choices=AuditLog.ACTION_CHOICES)
    model_type = django_filters.CharFilter(lookup_expr='icontains')
    user = django_filters.CharFilter(field_name='user__email', lookup_expr='icontains')
    date_from = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = AuditLog
        fields = ['action', 'model_type', 'user']
```

---

## SYSTEM SETTINGS

### Settings Model

**File**: `apps/core/models.py` (add)

```python
class SystemSetting(models.Model):
    """Key-value storage for system settings."""

    key = models.CharField('Klucz', max_length=100, unique=True)
    value = models.JSONField('Wartość', default=dict)
    description = models.TextField('Opis', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'system_settings'
        verbose_name = 'Ustawienie systemowe'
        verbose_name_plural = 'Ustawienia systemowe'

    def __str__(self):
        return self.key

    @classmethod
    def get(cls, key, default=None):
        try:
            setting = cls.objects.get(key=key)
            return setting.value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set(cls, key, value, description=''):
        setting, _ = cls.objects.update_or_create(
            key=key,
            defaults={'value': value, 'description': description}
        )
        return setting
```

### Settings View

**File**: `apps/admin_panel/views.py` (add)

```python
class SettingsView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    template_name = 'admin_panel/settings/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Load all settings
        context['settings'] = {
            'school_name': SystemSetting.get('school_name', 'Na Piątkę'),
            'default_lesson_duration': SystemSetting.get('default_lesson_duration', 60),
            'cancellation_notice_hours': SystemSetting.get('cancellation_notice_hours', 24),
            'makeup_lesson_expiry_days': SystemSetting.get('makeup_lesson_expiry_days', 30),
            'invoice_prefix': SystemSetting.get('invoice_prefix', 'FV'),
            'notification_email': SystemSetting.get('notification_email', ''),
        }

        return context

    def post(self, request):
        # Update settings from POST data
        for key in request.POST:
            if key.startswith('setting_'):
                setting_key = key.replace('setting_', '')
                value = request.POST[key]

                # Try to convert to appropriate type
                try:
                    value = int(value)
                except ValueError:
                    pass

                SystemSetting.set(setting_key, value)

        messages.success(request, 'Ustawienia zostały zapisane.')

        if request.htmx:
            return HttpResponse(status=204, headers={'HX-Trigger': 'settingsSaved'})

        return redirect('admin_panel:settings')
```

---

## COMPLETION CHECKLIST

- [ ] Subject CRUD with HTMX
- [ ] Level management
- [ ] Room CRUD with equipment
- [ ] System settings persistence
- [ ] Audit log viewer with filtering
- [ ] Email template management

---

**Next Phase**: Phase 4 - Calendar Integration
