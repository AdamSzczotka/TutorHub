# Development Roadmap - System "Na Piątkę"

## Kompletny Plan Implementacji CMS Szkoły Korepetycyjnej (Django + HTMX)

> **CRITICAL**: Ten plan jest mapą drogową całego projektu.
> Każdy task musi być wykonany zgodnie z ImplementationGuidelines.md
> Używamy TYLKO technologii z TechnologyStack.md
> **Stack**: Django 5.1 + HTMX + Alpine.js + Tailwind CSS + PostgreSQL
> Data utworzenia: Grudzień 2025
> Czas realizacji: 4 miesiące (17 tygodni)

---

## PODSUMOWANIE PROJEKTU

- **Całkowita liczba tasków**: ~165
- **Czas realizacji**: 17 tygodni
- **Liczba faz**: 14 (Faza 0-13)
- **Liczba sprintów**: ~26
- **Pokrycie funkcjonalności**: 100%

---

## FAZA 0: SETUP PROJEKTU

**Czas trwania**: 3 dni
**Cel**: Przygotowanie środowiska deweloperskiego Django

### Sprint 0.1: Inicjalizacja projektu (Dzień 1-2)

#### Task 001: Setup Django 5.1

```bash
mkdir napiatke && cd napiatke
python -m venv venv
source venv/bin/activate  # lub venv\Scripts\activate na Windows
pip install django
django-admin startproject napiatke .
```

- Konfiguracja struktury settings/ (base, development, production)
- Weryfikacja wersji zgodnie z TechnologyStack.md

#### Task 002: Konfiguracja django-environ

```bash
pip install django-environ
```

- Setup .env i .env.example
- Konfiguracja zmiennych środowiskowych

#### Task 003: Setup PostgreSQL z Docker

```yaml
# docker-compose.yml
version: '3.8'
services:
  postgres:
    image: postgres:17
    environment:
      POSTGRES_DB: napiatke
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: admin123
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  adminer:
    image: adminer:latest
    ports:
      - "8080:8080"

volumes:
  postgres_data:
```

#### Task 004: Konfiguracja psycopg2

```bash
pip install psycopg2-binary
```

- Konfiguracja DATABASES w settings
- Test połączenia

#### Task 005: Ruff + pre-commit setup

```bash
pip install ruff pre-commit mypy django-stubs
```

- pyproject.toml z konfiguracją Ruff
- .pre-commit-config.yaml
- Pierwszy commit

#### Task 006: Struktura folderów apps/

```bash
mkdir apps
python manage.py startapp core apps/core
python manage.py startapp accounts apps/accounts
```

Utworzenie struktury według ImplementationGuidelines sekcja 1.1

#### Task 007: Git + Husky hooks

- .gitignore dla Python/Django
- Pre-commit hooks (ruff, mypy)
- Konfiguracja commit message format

### Sprint 0.2: Podstawowa konfiguracja (Dzień 2-3)

#### Task 008: Tailwind CSS setup

```bash
npm init -y
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init
```

- tailwind.config.js z Django templates path
- static/css/input.css i output.css
- daisyUI installation

#### Task 009: HTMX i Alpine.js setup

```bash
# Pobranie do static/js/
curl -o static/js/htmx.min.js https://unpkg.com/htmx.org@2.0.0
curl -o static/js/alpine.min.js https://unpkg.com/alpinejs@3.14.0/dist/cdn.min.js
```

- Instalacja django-htmx
- Konfiguracja middleware

#### Task 010: Custom User model

```python
# apps/accounts/models.py
from django.contrib.auth.models import AbstractUser
import uuid

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=20, choices=Role.choices)
    phone = models.CharField(max_length=20, blank=True)
    first_login = models.BooleanField(default=True)
```

- AUTH_USER_MODEL w settings
- Początkowa migracja

#### Task 011: Zmienne środowiskowe

Utworzenie .env.example według TechnologyStack.md:

- DJANGO_SECRET_KEY
- DATABASE_URL
- REDIS_URL
- EMAIL_* variables

#### Task 012: Base templates

```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="pl">
<head>
    <link href="{% static 'css/output.css' %}" rel="stylesheet">
    <script src="{% static 'js/htmx.min.js' %}" defer></script>
    <script src="{% static 'js/alpine.min.js' %}" defer></script>
</head>
<body hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>
    {% block content %}{% endblock %}
</body>
</html>
```

---

## FAZA 1: FUNDAMENT SYSTEMU

**Czas trwania**: Tydzień 1-2
**Cel**: Baza danych, modele, autoryzacja

### Sprint 1.1: Baza danych i modele (Tydzień 1)

#### Task 013: Django models - tabele główne

```python
# apps/accounts/models.py - User (rozszerzony)
# apps/tutors/models.py - TutorProfile
# apps/students/models.py - StudentProfile
# apps/lessons/models.py - Lesson, LessonStudent
# apps/rooms/models.py - Room
# apps/subjects/models.py - Subject, Level
```

#### Task 014: Django models - tabele powiązań

- TutorSubject (ManyToMany through)
- SubjectLevel (ManyToMany through)

#### Task 015: Django models - tabele systemowe

```python
# apps/attendance/models.py - AttendanceRecord
# apps/cancellations/models.py - Cancellation, MakeupLesson
# apps/invoices/models.py - Invoice, InvoiceItem
# apps/messages/models.py - Message, Conversation
# apps/notifications/models.py - Notification
```

#### Task 016: Model choices i TextChoices

```python
class UserRole(models.TextChoices):
    ADMIN = 'admin', 'Administrator'
    TUTOR = 'tutor', 'Korepetytor'
    STUDENT = 'student', 'Uczeń'

class LessonStatus(models.TextChoices):
    SCHEDULED = 'scheduled', 'Zaplanowana'
    ONGOING = 'ongoing', 'W trakcie'
    COMPLETED = 'completed', 'Zakończona'
    CANCELLED = 'cancelled', 'Anulowana'
```

#### Task 017: Relacje między modelami

- User -> TutorProfile/StudentProfile (1:1)
- Lesson -> User (tutor) (ForeignKey)
- Lesson -> Room (ForeignKey)
- Lesson -> Student (ManyToMany przez LessonStudent)

#### Task 018: Indeksy bazodanowe

```python
class Meta:
    indexes = [
        models.Index(fields=['email']),
        models.Index(fields=['role', 'is_active']),
        models.Index(fields=['start_time', 'end_time']),
    ]
```

#### Task 019: Migracje początkowe

```bash
python manage.py makemigrations
python manage.py migrate
```

#### Task 020: Fixtures i seed data

```python
# apps/accounts/management/commands/seed_db.py
class Command(BaseCommand):
    def handle(self, *args, **options):
        # Create admin user
        # Create subjects and levels
        # Create test users (dev only)
```

### Sprint 1.2: System autoryzacji (Tydzień 2)

#### Task 021: Django Auth konfiguracja

- Custom authentication backend
- Session configuration (Redis)
- Login/Logout views

#### Task 022: Login view z HTMX

```python
# apps/accounts/views.py
class LoginView(View):
    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(...)
            login(request, user)
            if request.htmx:
                return HttpResponse(
                    headers={'HX-Redirect': '/dashboard/'}
                )
        return render(request, 'accounts/login.html', {'form': form})
```

#### Task 023: Email service (Django + Celery)

```python
# apps/core/tasks.py
from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_welcome_email(user_id):
    user = User.objects.get(pk=user_id)
    send_mail(
        'Witamy w Na Piątkę!',
        render_to_string('emails/welcome.html', {'user': user}),
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
    )
```

#### Task 024: Login page z Django Forms

```python
# apps/accounts/forms.py
class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'input input-bordered w-full',
        'placeholder': 'email@example.com',
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'input input-bordered w-full',
    }))
```

#### Task 025: First login flow

```python
# apps/accounts/middleware.py
class FirstLoginMiddleware:
    def __call__(self, request):
        if request.user.is_authenticated and request.user.first_login:
            if not request.path.startswith('/auth/first-login/'):
                return redirect('accounts:first_login')
        return self.get_response(request)
```

#### Task 026: Session management

```python
# settings/base.py
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 7200  # 2 hours
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
```

#### Task 027: Remember me feature

```python
def login_view(request):
    if form.is_valid():
        if form.cleaned_data.get('remember_me'):
            request.session.set_expiry(2592000)  # 30 days
        else:
            request.session.set_expiry(0)
```

#### Task 028: Role-based mixins

```python
# apps/core/mixins.py
class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin

class TutorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.is_tutor or self.request.user.is_admin
        )
```

---

## FAZA 2: ZARZĄDZANIE UŻYTKOWNIKAMI

**Czas trwania**: Tydzień 3-4
**Cel**: System bezpośredniego tworzenia użytkowników, CRUD

### Sprint 2.1: System tworzenia użytkowników (Tydzień 3)

#### Task 029: UserService

```python
# apps/accounts/services.py
class UserService:
    def create_user(self, data: dict, created_by: User) -> User:
        temp_password = self.generate_temp_password()
        user = User.objects.create_user(
            username=data['email'],
            email=data['email'],
            password=temp_password,
            **data
        )
        send_welcome_email.delay(user.id, temp_password)
        return user

    def generate_temp_password(self) -> str:
        return get_random_string(12)
```

#### Task 030: User CRUD views

```python
# apps/accounts/views.py
class UserListView(AdminRequiredMixin, HTMXMixin, ListView):
    model = User
    template_name = 'accounts/user_list.html'
    partial_template_name = 'partials/accounts/_user_list.html'
    paginate_by = 20

class UserCreateView(AdminRequiredMixin, CreateView):
    model = User
    form_class = CreateUserForm
    template_name = 'accounts/user_form.html'
```

#### Task 031: Email templates

```html
<!-- templates/emails/welcome.html -->
{% extends 'emails/base.html' %}
{% block content %}
<h1>Witaj {{ user.first_name }}!</h1>
<p>Twoje tymczasowe hasło: {{ temp_password }}</p>
<a href="{{ login_url }}">Zaloguj się</a>
{% endblock %}
```

#### Task 032: First login wizard

- Multi-step form z Alpine.js
- Walidacja po każdym kroku
- Progress indicator

#### Task 033: Profile completion - uczniowie

```python
# apps/students/forms.py
class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['class_name', 'parent_name', 'parent_phone', 'parent_email']
```

#### Task 034: Profile completion - korepetytorzy

```python
# apps/tutors/forms.py
class TutorProfileForm(forms.ModelForm):
    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all(),
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = TutorProfile
        fields = ['bio', 'hourly_rate', 'experience_years']
```

#### Task 035: Audit logging

```python
# apps/core/models.py
class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100)
    object_id = models.UUIDField()
    changes = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True)
```

### Sprint 2.2: CRUD użytkowników (Tydzień 4)

#### Task 036: User ListView z HTMX

```html
<!-- templates/accounts/user_list.html -->
<input type="search"
       name="search"
       hx-get="{% url 'accounts:user_list' %}"
       hx-trigger="keyup changed delay:300ms"
       hx-target="#user-table"
       class="input input-bordered w-full">

<div id="user-table">
    {% include 'partials/accounts/_user_table.html' %}
</div>
```

#### Task 037: User filtering

```python
class UserListView(ListView):
    def get_queryset(self):
        queryset = super().get_queryset()
        if search := self.request.GET.get('search'):
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        if role := self.request.GET.get('role'):
            queryset = queryset.filter(role=role)
        return queryset
```

#### Task 038: Alpine.js filtering UI

```html
<div x-data="{ filters: { role: '', status: '' } }">
    <select x-model="filters.role"
            @change="$refs.filterForm.submit()">
        <option value="">Wszystkie role</option>
        <option value="admin">Administratorzy</option>
        <option value="tutor">Korepetytorzy</option>
        <option value="student">Uczniowie</option>
    </select>
</div>
```

#### Task 039: Create user modal

```html
<button hx-get="{% url 'accounts:user_create' %}"
        hx-target="#modal-content"
        onclick="modal.showModal()">
    Dodaj użytkownika
</button>

<dialog id="modal" class="modal">
    <div class="modal-box" id="modal-content"></div>
</dialog>
```

#### Task 040: Edit profile view

```python
class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileForm
    template_name = 'accounts/profile.html'

    def get_object(self):
        return self.request.user
```

#### Task 041: Avatar upload

```python
# apps/accounts/views.py
class AvatarUploadView(LoginRequiredMixin, View):
    def post(self, request):
        if 'avatar' in request.FILES:
            request.user.avatar = request.FILES['avatar']
            request.user.save()
            if request.htmx:
                return render(request, 'partials/accounts/_avatar.html')
        return redirect('accounts:profile')
```

#### Task 042: RODO export

```python
class GDPRExportView(LoginRequiredMixin, View):
    def get(self, request):
        user_data = {
            'personal': UserSerializer(request.user).data,
            'lessons': LessonSerializer(request.user.lessons.all(), many=True).data,
            'invoices': InvoiceSerializer(request.user.invoices.all(), many=True).data,
        }
        response = JsonResponse(user_data)
        response['Content-Disposition'] = 'attachment; filename="my_data.json"'
        return response
```

---

## FAZA 3: PANEL ADMINISTRATORA

**Czas trwania**: Tydzień 5-6
**Cel**: Dashboard, zarządzanie podstawowe

### Sprint 3.1: Dashboard i nawigacja (Tydzień 5)

#### Task 043: Admin layout

```html
<!-- templates/layouts/admin.html -->
{% extends 'base.html' %}

{% block body %}
<div class="drawer lg:drawer-open">
    <input id="drawer" type="checkbox" class="drawer-toggle">
    <div class="drawer-content">
        <nav class="navbar bg-base-100 shadow lg:hidden">
            <label for="drawer" class="btn btn-ghost">
                <svg><!-- menu icon --></svg>
            </label>
        </nav>
        <main class="p-6">
            {% block content %}{% endblock %}
        </main>
    </div>
    <div class="drawer-side">
        {% include 'layouts/_admin_sidebar.html' %}
    </div>
</div>
{% endblock %}
```

#### Task 044: Admin middleware (opcjonalnie IP whitelist)

```python
class AdminIPWhitelistMiddleware:
    def __call__(self, request):
        if request.path.startswith('/admin/'):
            allowed_ips = settings.ADMIN_ALLOWED_IPS
            client_ip = get_client_ip(request)
            if allowed_ips and client_ip not in allowed_ips:
                return HttpResponseForbidden()
        return self.get_response(request)
```

#### Task 045: Dashboard widgets

```python
class AdminDashboardView(AdminRequiredMixin, TemplateView):
    template_name = 'admin_panel/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = {
            'users_count': User.objects.count(),
            'lessons_today': Lesson.objects.filter(
                start_time__date=timezone.now().date()
            ).count(),
            'revenue_month': Invoice.objects.filter(
                created_at__month=timezone.now().month
            ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
        }
        return context
```

#### Task 046: Statistics service

```python
# apps/reports/services.py
class StatisticsService:
    def get_dashboard_stats(self) -> dict:
        return {
            'users': self._get_user_stats(),
            'lessons': self._get_lesson_stats(),
            'revenue': self._get_revenue_stats(),
            'attendance': self._get_attendance_stats(),
        }

    def _get_user_stats(self) -> dict:
        return {
            'total': User.objects.count(),
            'by_role': User.objects.values('role').annotate(count=Count('id')),
            'new_this_month': User.objects.filter(
                created_at__month=timezone.now().month
            ).count(),
        }
```

#### Task 047: Charts (Chart.js lub ApexCharts)

```html
<!-- templates/admin_panel/_revenue_chart.html -->
<div x-data="revenueChart()"
     x-init="init()"
     hx-get="{% url 'admin:revenue_data' %}"
     hx-trigger="load"
     hx-swap="none">
    <canvas id="revenueChart"></canvas>
</div>

<script>
function revenueChart() {
    return {
        init() {
            document.body.addEventListener('htmx:afterRequest', (e) => {
                const data = JSON.parse(e.detail.xhr.response);
                new Chart(document.getElementById('revenueChart'), {
                    type: 'line',
                    data: data,
                });
            });
        }
    }
}
</script>
```

### Sprint 3.2: Zarządzanie podstawowe (Tydzień 6)

#### Task 048: Users management page

- Pełna strona z CRUD
- Bulk actions (deactivate, delete)
- Export CSV

#### Task 049: Subjects CRUD

```python
# apps/subjects/views.py
class SubjectListView(AdminRequiredMixin, ListView):
    model = Subject
    template_name = 'subjects/list.html'

class SubjectCreateView(AdminRequiredMixin, CreateView):
    model = Subject
    fields = ['name', 'description', 'is_active']
```

#### Task 050: Levels CRUD

```python
class Level(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
```

#### Task 051: Subject-Level relationships

```html
<!-- Checkbox matrix dla przedmiot-poziom -->
<table class="table">
    <thead>
        <tr>
            <th>Poziom</th>
            {% for subject in subjects %}
            <th>{{ subject.name }}</th>
            {% endfor %}
        </tr>
    </thead>
    <tbody>
        {% for level in levels %}
        <tr>
            <td>{{ level.name }}</td>
            {% for subject in subjects %}
            <td>
                <input type="checkbox"
                       name="relations"
                       value="{{ subject.id }}-{{ level.id }}"
                       {% if level in subject.levels.all %}checked{% endif %}>
            </td>
            {% endfor %}
        </tr>
        {% endfor %}
    </tbody>
</table>
```

#### Task 052: Rooms management

```python
class Room(models.Model):
    name = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField(default=10)
    location = models.CharField(max_length=200, blank=True)
    equipment = models.JSONField(default=list)  # ['projector', 'whiteboard']
    is_active = models.BooleanField(default=True)
```

#### Task 053: Room availability calendar

- FullCalendar dla sal
- Booking conflicts visualization
- Maintenance periods

---

## FAZA 4: KALENDARZ I LEKCJE

**Czas trwania**: Tydzień 7-8
**Cel**: Pełny system kalendarza z zarządzaniem lekcjami

### Sprint 4.1: Integracja kalendarza (Tydzień 7)

#### Task 054: FullCalendar setup

```html
<!-- templates/lessons/calendar.html -->
<link href="https://cdn.jsdelivr.net/npm/fullcalendar@6.1/main.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/fullcalendar@6.1/main.min.js"></script>

<div id="calendar"></div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    var calendar = new FullCalendar.Calendar(document.getElementById('calendar'), {
        initialView: 'timeGridWeek',
        locale: 'pl',
        events: '{% url "lessons:calendar_events" %}',
        eventClick: function(info) {
            htmx.ajax('GET', `/lessons/${info.event.id}/`, {
                target: '#modal-content'
            });
            document.getElementById('modal').showModal();
        },
        dateClick: function(info) {
            htmx.ajax('GET', `{% url "lessons:create" %}?date=${info.dateStr}`, {
                target: '#modal-content'
            });
            document.getElementById('modal').showModal();
        }
    });
    calendar.render();
});
</script>
```

#### Task 055: Calendar events API

```python
# apps/lessons/views.py
def calendar_events(request):
    start = request.GET.get('start')
    end = request.GET.get('end')

    lessons = Lesson.objects.filter(
        start_time__gte=start,
        end_time__lte=end
    ).select_related('tutor', 'room', 'subject')

    events = [{
        'id': str(lesson.id),
        'title': lesson.title,
        'start': lesson.start_time.isoformat(),
        'end': lesson.end_time.isoformat(),
        'color': lesson.subject.color,
        'extendedProps': {
            'tutor': lesson.tutor.get_full_name(),
            'room': lesson.room.name,
        }
    } for lesson in lessons]

    return JsonResponse(events, safe=False)
```

#### Task 056: Drag & drop events

```javascript
// FullCalendar config
editable: true,
eventDrop: function(info) {
    htmx.ajax('PATCH', `/api/lessons/${info.event.id}/move/`, {
        values: {
            start: info.event.start.toISOString(),
            end: info.event.end.toISOString()
        }
    });
},
eventResize: function(info) {
    htmx.ajax('PATCH', `/api/lessons/${info.event.id}/resize/`, {
        values: {
            end: info.event.end.toISOString()
        }
    });
}
```

#### Task 057: Event creation modal

```python
class LessonCreateView(AdminRequiredMixin, CreateView):
    model = Lesson
    form_class = LessonForm
    template_name = 'lessons/lesson_form.html'

    def get_initial(self):
        initial = super().get_initial()
        if date := self.request.GET.get('date'):
            initial['start_time'] = parse_datetime(date)
        return initial

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.htmx:
            return HttpResponse(
                headers={'HX-Trigger': 'lessonCreated'}
            )
        return response
```

### Sprint 4.2: Zarządzanie lekcjami (Tydzień 8)

#### Task 058-066: Pozostałe taski kalendarza

- Event colors per subject
- Resources view (per room/tutor)
- Lesson CRUD
- CalendarService (conflict detection)
- Student assignment
- Group lessons
- Recurring events
- Notifications (Celery)
- iCal export

---

## FAZY 5-13: POZOSTAŁE FUNKCJONALNOŚCI

### FAZA 5: System obecności (Tydzień 9)
- Attendance marking UI z HTMX
- Quick mark buttons
- Statystyki frekwencji
- Alerty <80%
- Raporty PDF (WeasyPrint)

### FAZA 6: Anulowania i odrabianie (Tydzień 10)
- Cancellation request workflow
- Admin approval
- 30-day makeup tracking
- Auto-expiration (Celery beat)

### FAZA 7: System fakturowania (Tydzień 11)
- Invoice models
- PDF generation (WeasyPrint)
- Monthly automation (Celery beat)
- Email delivery
- Payment tracking

### FAZA 8: Komunikacja (Tydzień 12)
- Internal messaging
- Notification center (HTMX polling)
- Email queue (Celery)
- User preferences

### FAZA 9: Portale użytkowników (Tydzień 13)
- Tutor portal (dashboard, calendar, students)
- Student portal (schedule, cancellations, invoices)
- Parent access

### FAZA 10: Filtry i eksport (Tydzień 14)
- HTMX live filtering
- URL persistence
- CSV export (StreamingHttpResponse)
- Excel export (openpyxl)
- PDF reports

### FAZA 11: Optymalizacja (Tydzień 15)
- Query optimization (select_related, prefetch_related)
- Redis caching
- Django Debug Toolbar
- Security audit
- Rate limiting (django-ratelimit)

### FAZA 12: Testy i dokumentacja (Tydzień 16)
- pytest-django unit tests
- Factory Boy fixtures
- Playwright E2E
- >80% coverage
- README i dokumentacja

### FAZA 13: Deployment (Tydzień 17)
- Docker production build
- Gunicorn + Nginx
- Railway/Render deployment
- SSL/HTTPS
- Sentry monitoring
- Backup configuration

---

## METRYKI SUKCESU

### Performance KPIs
- Response time <200ms (p95)
- Database queries <10 per request
- HTMX partial <100ms

### Business KPIs
- 100% feature coverage
- 90% user satisfaction
- 50% admin time saved

### Technical KPIs
- >80% test coverage
- 99.9% uptime
- Zero security vulnerabilities

---

## POMOCNE KOMENDY

```bash
# Development
python manage.py runserver     # Start dev server
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

# Tailwind
npx tailwindcss -i static/css/input.css -o static/css/output.css --watch

# Celery
celery -A napiatke worker -l info
celery -A napiatke beat -l info

# Testing
pytest
pytest --cov=apps
pytest -x -v  # Stop on first failure

# Linting
ruff check .
ruff format .
mypy apps/

# Production
python manage.py collectstatic
gunicorn napiatke.wsgi:application
```

---

**Ten roadmap jest żywym dokumentem.**
**Aktualizuj po każdym sprincie.**
**Sukces = przestrzeganie planu.**

**Data utworzenia**: Grudzień 2025
**Wersja**: 2.0.0 (Django + HTMX)
**Następna rewizja**: Po każdym sprincie
