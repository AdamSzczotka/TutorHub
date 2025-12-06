# ViewPlan.md - Szczegółowy Plan Widoków

## System CMS Szkoły Korepetycyjnej "Na Piątkę" (Django + HTMX)

> **WAŻNE**: Ten dokument definiuje wszystkie widoki i interfejsy użytkownika w systemie.
> Każdy widok jest zgodny z TechnologyStack.md i ImplementationGuidelines.md
> **Stack**: Django Templates + HTMX + Alpine.js + daisyUI/Tailwind CSS
> Data utworzenia: Grudzień 2025
> Wersja: 2.0.0

---

## SPIS TREŚCI

1. [Struktura Templates](#struktura-templates)
2. [Przepływ Użytkowników](#przepływ-użytkowników)
3. [Widoki Publiczne](#widoki-publiczne)
4. [Panel Administratora](#panel-administratora)
5. [Panel Korepetytora](#panel-korepetytora)
6. [Panel Ucznia/Rodzica](#panel-uczniarodzica)
7. [Komponenty Współdzielone](#komponenty-współdzielone)
8. [HTMX Patterns](#htmx-patterns)
9. [Formularze Django](#formularze-django)
10. [Responsywność](#responsywność)

---

## STRUKTURA TEMPLATES

### Organizacja folderów

```
templates/
├── base.html                    # Bazowy template
├── layouts/                     # Layouty per rola
│   ├── admin.html
│   ├── tutor.html
│   ├── student.html
│   ├── _admin_sidebar.html
│   ├── _tutor_nav.html
│   └── _student_nav.html
├── components/                  # Reużywalne komponenty
│   ├── _button.html
│   ├── _modal.html
│   ├── _table.html
│   ├── _card.html
│   ├── _form_field.html
│   ├── _pagination.html
│   ├── _alert.html
│   ├── _dropdown.html
│   ├── _loading.html
│   ├── _stat_card.html
│   ├── _avatar.html
│   └── _badge.html
├── partials/                    # HTMX partial responses
│   ├── accounts/
│   │   ├── _user_row.html
│   │   ├── _user_list.html
│   │   └── _user_form.html
│   ├── lessons/
│   │   ├── _lesson_row.html
│   │   ├── _lesson_card.html
│   │   └── _lesson_form.html
│   └── ...
├── emails/                      # Email templates
│   ├── base_email.html
│   ├── welcome.html
│   └── password_reset.html
├── errors/                      # Error pages
│   ├── 400.html
│   ├── 403.html
│   ├── 404.html
│   └── 500.html
└── [app_name]/                  # Templates per app
    ├── accounts/
    ├── admin_panel/
    ├── tutor_panel/
    └── student_panel/
```

### Base Template

```html
<!-- templates/base.html -->
{% load static %}
<!DOCTYPE html>
<html lang="pl" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Na Piątkę{% endblock %}</title>

    <!-- Tailwind CSS (compiled with daisyUI) -->
    <link href="{% static 'css/output.css' %}" rel="stylesheet">

    <!-- HTMX -->
    <script src="{% static 'js/htmx.min.js' %}" defer></script>

    <!-- Alpine.js -->
    <script src="{% static 'js/alpine.min.js' %}" defer></script>

    {% block extra_head %}{% endblock %}
</head>
<body class="min-h-screen bg-base-200"
      hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>

    {% block body %}
    <main>
        {% block content %}{% endblock %}
    </main>
    {% endblock %}

    <!-- Toast notifications container -->
    <div id="toast-container" class="toast toast-end z-50">
        {% if messages %}
            {% for message in messages %}
            <div class="alert alert-{{ message.tags }}"
                 x-data="{ show: true }"
                 x-show="show"
                 x-init="setTimeout(() => show = false, 5000)">
                <span>{{ message }}</span>
            </div>
            {% endfor %}
        {% endif %}
    </div>

    <!-- Global modal container -->
    <dialog id="modal" class="modal">
        <div class="modal-box" id="modal-content">
            <!-- Content loaded via HTMX -->
        </div>
        <form method="dialog" class="modal-backdrop">
            <button>close</button>
        </form>
    </dialog>

    {% block extra_js %}{% endblock %}
</body>
</html>
```

---

## PRZEPŁYW UŻYTKOWNIKÓW

### Tworzenie konta (PRZEPŁYW BEZ ZAPROSZEŃ)

```
1. Admin tworzy konto bezpośrednio w systemie
2. Wprowadza: imię, nazwisko, email, telefon, rolę
3. System generuje tymczasowe hasło
4. Email z danymi logowania wysyłany automatycznie (Celery)
5. Użytkownik loguje się pierwszy raz
6. Middleware wymusza uzupełnienie profilu
7. Zmiana hasła tymczasowego
8. Konto aktywne - pełny dostęp
```

### Role w systemie

- **Admin**: Pełna kontrola, zarządzanie użytkownikami, fakturowanie
- **Korepetytor**: Zarządzanie własnymi lekcjami, obecność
- **Uczeń/Rodzic**: Jedno konto, rodzic ma dostęp do panelu ucznia

---

## WIDOKI PUBLICZNE

### 1. Landing Page `/`

**Template**: `templates/landing/index.html`
**View**: `apps.landing.views.IndexView`

**Sekcje**:

```html
{% extends 'base.html' %}

{% block content %}
<!-- Hero Section -->
<section class="hero min-h-screen bg-base-200">
    <div class="hero-content text-center">
        <div class="max-w-md">
            <h1 class="text-5xl font-bold">Korepetycje, które prowadzą do sukcesu</h1>
            <p class="py-6">Profesjonalne korepetycje dla uczniów szkół podstawowych i średnich</p>
            <a href="#contact" class="btn btn-primary">Zapytaj o wolne terminy</a>
        </div>
    </div>
</section>

<!-- O nas -->
<section id="about" class="py-16">
    {% include 'landing/_about_section.html' %}
</section>

<!-- Oferta - przedmioty -->
<section id="subjects" class="py-16 bg-base-100">
    {% include 'landing/_subjects_grid.html' %}
</section>

<!-- Zespół -->
<section id="team" class="py-16">
    {% include 'landing/_team_carousel.html' %}
</section>

<!-- Cennik -->
<section id="pricing" class="py-16 bg-base-100">
    {% include 'landing/_pricing_table.html' %}
</section>

<!-- FAQ -->
<section id="faq" class="py-16">
    {% include 'landing/_faq_accordion.html' %}
</section>

<!-- Kontakt -->
<section id="contact" class="py-16 bg-base-100">
    {% include 'landing/_contact_form.html' %}
</section>
{% endblock %}
```

### 2. Strona logowania `/auth/login/`

**Template**: `templates/accounts/login.html`
**View**: `apps.accounts.views.LoginView`

```html
{% extends 'base.html' %}

{% block content %}
<div class="min-h-screen flex items-center justify-center">
    <div class="card w-96 bg-base-100 shadow-xl">
        <div class="card-body">
            <h2 class="card-title justify-center mb-4">Zaloguj się</h2>

            <form method="post"
                  hx-post="{% url 'accounts:login' %}"
                  hx-target="#login-errors"
                  hx-swap="innerHTML">
                {% csrf_token %}

                <div class="form-control">
                    <label class="label">
                        <span class="label-text">Email</span>
                    </label>
                    <input type="email" name="email"
                           class="input input-bordered"
                           placeholder="email@example.com" required>
                </div>

                <div class="form-control mt-4">
                    <label class="label">
                        <span class="label-text">Hasło</span>
                    </label>
                    <input type="password" name="password"
                           class="input input-bordered" required>
                </div>

                <div class="form-control mt-2">
                    <label class="label cursor-pointer justify-start gap-2">
                        <input type="checkbox" name="remember"
                               class="checkbox checkbox-sm">
                        <span class="label-text">Zapamiętaj mnie</span>
                    </label>
                </div>

                <div id="login-errors" class="mt-2"></div>

                <div class="form-control mt-6">
                    <button type="submit" class="btn btn-primary">
                        <span class="htmx-indicator loading loading-spinner loading-sm"></span>
                        Zaloguj
                    </button>
                </div>

                <div class="text-center mt-4">
                    <a href="{% url 'accounts:password_reset' %}"
                       class="link link-hover text-sm">
                        Zapomniałeś hasła?
                    </a>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}
```

### 3. Reset hasła `/auth/reset-password/`

**Templates**:
- `templates/accounts/password_reset.html` - żądanie resetu
- `templates/accounts/password_reset_confirm.html` - nowe hasło

### 4. Pierwsze logowanie `/auth/first-login/`

**Template**: `templates/accounts/first_login.html`
**View**: `apps.accounts.views.FirstLoginView`

Multi-step wizard z Alpine.js:

```html
{% extends 'base.html' %}

{% block content %}
<div class="min-h-screen flex items-center justify-center p-4"
     x-data="{ step: 1, maxSteps: {{ max_steps }} }">

    <div class="card w-full max-w-2xl bg-base-100 shadow-xl">
        <div class="card-body">
            <!-- Progress -->
            <ul class="steps w-full mb-8">
                <li class="step" :class="{ 'step-primary': step >= 1 }">Dane</li>
                <li class="step" :class="{ 'step-primary': step >= 2 }">
                    {% if user.is_tutor %}Kwalifikacje{% else %}Kontakt{% endif %}
                </li>
                <li class="step" :class="{ 'step-primary': step >= 3 }">Hasło</li>
                <li class="step" :class="{ 'step-primary': step >= 4 }">Koniec</li>
            </ul>

            <form method="post"
                  hx-post="{% url 'accounts:first_login' %}"
                  hx-target="#form-content"
                  hx-swap="innerHTML">
                {% csrf_token %}

                <div id="form-content">
                    {% include 'accounts/_first_login_step1.html' %}
                </div>

                <div class="flex justify-between mt-6">
                    <button type="button"
                            class="btn"
                            x-show="step > 1"
                            @click="step--">
                        Wstecz
                    </button>
                    <button type="button"
                            class="btn btn-primary"
                            x-show="step < maxSteps"
                            @click="step++">
                        Dalej
                    </button>
                    <button type="submit"
                            class="btn btn-success"
                            x-show="step === maxSteps">
                        Zakończ
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}
```

---

## PANEL ADMINISTRATORA

### Layout Admin

**Template**: `templates/layouts/admin.html`

```html
{% extends 'base.html' %}

{% block body %}
<div class="drawer lg:drawer-open">
    <input id="admin-drawer" type="checkbox" class="drawer-toggle">

    <!-- Main content -->
    <div class="drawer-content flex flex-col">
        <!-- Navbar (mobile) -->
        <nav class="navbar bg-base-100 shadow-lg lg:hidden">
            <div class="flex-none">
                <label for="admin-drawer" class="btn btn-square btn-ghost">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none"
                         viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round"
                              stroke-width="2" d="M4 6h16M4 12h16M4 18h7"/>
                    </svg>
                </label>
            </div>
            <div class="flex-1">
                <span class="text-xl font-bold">Na Piątkę</span>
            </div>
            <div class="flex-none">
                {% include 'components/_notification_bell.html' %}
            </div>
        </nav>

        <!-- Page content -->
        <main class="flex-1 p-4 lg:p-6">
            <!-- Breadcrumbs -->
            <div class="text-sm breadcrumbs mb-4">
                <ul>
                    <li><a href="{% url 'admin_panel:dashboard' %}">Panel</a></li>
                    {% block breadcrumbs %}{% endblock %}
                </ul>
            </div>

            {% block content %}{% endblock %}
        </main>
    </div>

    <!-- Sidebar -->
    <div class="drawer-side z-40">
        <label for="admin-drawer" class="drawer-overlay"></label>
        {% include 'layouts/_admin_sidebar.html' %}
    </div>
</div>
{% endblock %}
```

### Admin Sidebar

**Template**: `templates/layouts/_admin_sidebar.html`

```html
<aside class="bg-base-200 w-64 min-h-full">
    <div class="p-4">
        <a href="{% url 'admin_panel:dashboard' %}" class="text-2xl font-bold">
            Na Piątkę
        </a>
    </div>

    <ul class="menu p-4 gap-1">
        <li>
            <a href="{% url 'admin_panel:dashboard' %}"
               class="{% if request.resolver_match.url_name == 'dashboard' %}active{% endif %}">
                <svg class="w-5 h-5"><!-- dashboard icon --></svg>
                Dashboard
            </a>
        </li>
        <li>
            <a href="{% url 'admin_panel:users' %}"
               class="{% if 'users' in request.path %}active{% endif %}">
                <svg class="w-5 h-5"><!-- users icon --></svg>
                Użytkownicy
            </a>
        </li>
        <li>
            <a href="{% url 'admin_panel:calendar' %}"
               class="{% if 'calendar' in request.path %}active{% endif %}">
                <svg class="w-5 h-5"><!-- calendar icon --></svg>
                Kalendarz
            </a>
        </li>
        <li>
            <a href="{% url 'admin_panel:cancellations' %}"
               class="{% if 'cancellations' in request.path %}active{% endif %}">
                <svg class="w-5 h-5"><!-- cancel icon --></svg>
                Anulowania
                {% if pending_cancellations > 0 %}
                <span class="badge badge-warning">{{ pending_cancellations }}</span>
                {% endif %}
            </a>
        </li>
        <li>
            <a href="{% url 'admin_panel:rooms' %}">
                <svg class="w-5 h-5"><!-- room icon --></svg>
                Sale
            </a>
        </li>
        <li>
            <a href="{% url 'admin_panel:subjects' %}">
                <svg class="w-5 h-5"><!-- subject icon --></svg>
                Przedmioty
            </a>
        </li>
        <li>
            <a href="{% url 'admin_panel:invoices' %}">
                <svg class="w-5 h-5"><!-- invoice icon --></svg>
                Faktury
            </a>
        </li>
        <li>
            <a href="{% url 'admin_panel:reports' %}">
                <svg class="w-5 h-5"><!-- reports icon --></svg>
                Raporty
            </a>
        </li>
    </ul>

    <!-- User menu -->
    <div class="absolute bottom-0 w-full p-4 border-t border-base-300">
        <div class="dropdown dropdown-top w-full">
            <label tabindex="0" class="btn btn-ghost w-full justify-start">
                {% include 'components/_avatar.html' with user=request.user size='sm' %}
                <span class="ml-2">{{ request.user.get_full_name }}</span>
            </label>
            <ul tabindex="0" class="dropdown-content menu p-2 shadow bg-base-100 rounded-box w-52">
                <li><a href="{% url 'accounts:profile' %}">Profil</a></li>
                <li><a href="{% url 'accounts:logout' %}">Wyloguj</a></li>
            </ul>
        </div>
    </div>
</aside>
```

### 1. Dashboard `/admin/`

**Template**: `templates/admin_panel/dashboard.html`
**View**: `apps.admin_panel.views.DashboardView`

```html
{% extends 'layouts/admin.html' %}

{% block content %}
<h1 class="text-2xl font-bold mb-6">Dashboard</h1>

<!-- Stats Grid -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
    {% include 'components/_stat_card.html' with title="Użytkownicy" value=stats.users_count icon="users" color="primary" %}
    {% include 'components/_stat_card.html' with title="Lekcje dziś" value=stats.lessons_today icon="calendar" color="secondary" %}
    {% include 'components/_stat_card.html' with title="Przychód (mies.)" value=stats.revenue_month|currency icon="money" color="success" %}
    {% include 'components/_stat_card.html' with title="Frekwencja" value=stats.attendance_avg|percentage icon="chart" color="info" %}
</div>

<!-- Charts Row -->
<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
    <!-- Revenue Chart -->
    <div class="card bg-base-100 shadow"
         hx-get="{% url 'admin_panel:revenue_chart_data' %}"
         hx-trigger="load"
         hx-swap="innerHTML">
        <div class="card-body">
            <h2 class="card-title">Przychody</h2>
            <div class="h-64 flex items-center justify-center">
                <span class="loading loading-spinner loading-lg"></span>
            </div>
        </div>
    </div>

    <!-- Attendance Chart -->
    <div class="card bg-base-100 shadow"
         hx-get="{% url 'admin_panel:attendance_chart_data' %}"
         hx-trigger="load"
         hx-swap="innerHTML">
        <div class="card-body">
            <h2 class="card-title">Frekwencja</h2>
            <div class="h-64 flex items-center justify-center">
                <span class="loading loading-spinner loading-lg"></span>
            </div>
        </div>
    </div>
</div>

<!-- Quick Actions + Alerts -->
<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <!-- Quick Actions -->
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <h2 class="card-title">Szybkie akcje</h2>
            <div class="flex flex-wrap gap-2">
                <button class="btn btn-primary btn-sm"
                        hx-get="{% url 'admin_panel:user_create' %}"
                        hx-target="#modal-content"
                        onclick="modal.showModal()">
                    Dodaj użytkownika
                </button>
                <button class="btn btn-secondary btn-sm"
                        hx-get="{% url 'admin_panel:lesson_create' %}"
                        hx-target="#modal-content"
                        onclick="modal.showModal()">
                    Dodaj lekcję
                </button>
                <a href="{% url 'admin_panel:invoices_generate' %}" class="btn btn-accent btn-sm">
                    Generuj faktury
                </a>
            </div>
        </div>
    </div>

    <!-- Alerts -->
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <h2 class="card-title">Wymagają uwagi</h2>
            <ul class="space-y-2">
                {% for alert in alerts %}
                <li class="flex items-center gap-2">
                    <span class="badge badge-{{ alert.type }}"></span>
                    <span>{{ alert.message }}</span>
                </li>
                {% empty %}
                <li class="text-base-content/60">Brak alertów</li>
                {% endfor %}
            </ul>
        </div>
    </div>
</div>
{% endblock %}
```

### 2. Lista użytkowników `/admin/users/`

**Template**: `templates/admin_panel/users/list.html`
**View**: `apps.admin_panel.views.UserListView`

```html
{% extends 'layouts/admin.html' %}

{% block breadcrumbs %}
<li>Użytkownicy</li>
{% endblock %}

{% block content %}
<div class="flex justify-between items-center mb-6">
    <h1 class="text-2xl font-bold">Użytkownicy</h1>
    <button class="btn btn-primary"
            hx-get="{% url 'admin_panel:user_create' %}"
            hx-target="#modal-content"
            onclick="modal.showModal()">
        Dodaj użytkownika
    </button>
</div>

<!-- Filters -->
<div class="card bg-base-100 shadow mb-6">
    <div class="card-body py-4">
        <div class="flex flex-wrap gap-4">
            <input type="search"
                   name="search"
                   placeholder="Szukaj..."
                   class="input input-bordered w-full max-w-xs"
                   hx-get="{% url 'admin_panel:users' %}"
                   hx-trigger="keyup changed delay:300ms"
                   hx-target="#users-table"
                   hx-include="[name='role'], [name='status']">

            <select name="role"
                    class="select select-bordered"
                    hx-get="{% url 'admin_panel:users' %}"
                    hx-trigger="change"
                    hx-target="#users-table"
                    hx-include="[name='search'], [name='status']">
                <option value="">Wszystkie role</option>
                <option value="admin">Administratorzy</option>
                <option value="tutor">Korepetytorzy</option>
                <option value="student">Uczniowie</option>
            </select>

            <select name="status"
                    class="select select-bordered"
                    hx-get="{% url 'admin_panel:users' %}"
                    hx-trigger="change"
                    hx-target="#users-table"
                    hx-include="[name='search'], [name='role']">
                <option value="">Wszystkie statusy</option>
                <option value="active">Aktywni</option>
                <option value="inactive">Nieaktywni</option>
            </select>

            <a href="{% url 'admin_panel:users_export' %}" class="btn btn-ghost">
                Eksport CSV
            </a>
        </div>
    </div>
</div>

<!-- Table -->
<div class="card bg-base-100 shadow">
    <div class="card-body p-0">
        <div id="users-table">
            {% include 'partials/admin_panel/_users_table.html' %}
        </div>
    </div>
</div>
{% endblock %}
```

### Users Table Partial

**Template**: `templates/partials/admin_panel/_users_table.html`

```html
<div class="overflow-x-auto">
    <table class="table">
        <thead>
            <tr>
                <th>Użytkownik</th>
                <th>Email</th>
                <th>Rola</th>
                <th>Status</th>
                <th>Ostatnie logowanie</th>
                <th></th>
            </tr>
        </thead>
        <tbody>
            {% for user in users %}
            <tr id="user-{{ user.pk }}" class="hover">
                <td>
                    <div class="flex items-center gap-3">
                        {% include 'components/_avatar.html' with user=user size='sm' %}
                        <div>
                            <div class="font-bold">{{ user.get_full_name }}</div>
                            <div class="text-sm opacity-50">{{ user.phone }}</div>
                        </div>
                    </div>
                </td>
                <td>{{ user.email }}</td>
                <td>
                    <span class="badge badge-{{ user.role }}">{{ user.get_role_display }}</span>
                </td>
                <td>
                    {% if user.is_active %}
                    <span class="badge badge-success">Aktywny</span>
                    {% else %}
                    <span class="badge badge-error">Nieaktywny</span>
                    {% endif %}
                </td>
                <td>{{ user.last_login|date:"d.m.Y H:i"|default:"Nigdy" }}</td>
                <td>
                    <div class="dropdown dropdown-end">
                        <label tabindex="0" class="btn btn-ghost btn-sm">
                            <svg class="w-5 h-5"><!-- dots icon --></svg>
                        </label>
                        <ul tabindex="0" class="dropdown-content menu p-2 shadow bg-base-100 rounded-box w-52">
                            <li>
                                <a hx-get="{% url 'admin_panel:user_edit' user.pk %}"
                                   hx-target="#modal-content"
                                   onclick="modal.showModal()">
                                    Edytuj
                                </a>
                            </li>
                            <li>
                                <a hx-post="{% url 'admin_panel:user_reset_password' user.pk %}"
                                   hx-confirm="Zresetować hasło dla {{ user.email }}?">
                                    Reset hasła
                                </a>
                            </li>
                            <li>
                                <a hx-post="{% url 'admin_panel:user_toggle_active' user.pk %}"
                                   hx-target="#user-{{ user.pk }}"
                                   hx-swap="outerHTML">
                                    {% if user.is_active %}Dezaktywuj{% else %}Aktywuj{% endif %}
                                </a>
                            </li>
                        </ul>
                    </div>
                </td>
            </tr>
            {% empty %}
            <tr>
                <td colspan="6" class="text-center py-8 text-base-content/60">
                    Brak użytkowników
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>

{% if page_obj.has_other_pages %}
<div class="flex justify-center p-4">
    {% include 'components/_pagination.html' %}
</div>
{% endif %}
```

### 3. Tworzenie użytkownika (Modal)

**Template**: `templates/partials/admin_panel/_user_form.html`

```html
<h3 class="font-bold text-lg mb-4">
    {% if user %}Edytuj użytkownika{% else %}Nowy użytkownik{% endif %}
</h3>

<form method="post"
      hx-post="{% if user %}{% url 'admin_panel:user_edit' user.pk %}{% else %}{% url 'admin_panel:user_create' %}{% endif %}"
      hx-target="#modal-content"
      hx-swap="innerHTML">
    {% csrf_token %}

    <div class="grid grid-cols-2 gap-4">
        {% include 'components/_form_field.html' with field=form.first_name %}
        {% include 'components/_form_field.html' with field=form.last_name %}
    </div>

    {% include 'components/_form_field.html' with field=form.email %}
    {% include 'components/_form_field.html' with field=form.phone %}
    {% include 'components/_form_field.html' with field=form.role %}

    <!-- Conditional fields for students -->
    <div x-data="{ role: '{{ form.role.value|default:"" }}' }">
        <div x-show="role === 'student'">
            {% include 'components/_form_field.html' with field=form.class_name %}
            {% include 'components/_form_field.html' with field=form.parent_name %}
            {% include 'components/_form_field.html' with field=form.parent_phone %}
        </div>
    </div>

    <div class="modal-action">
        <button type="button" class="btn" onclick="modal.close()">Anuluj</button>
        <button type="submit" class="btn btn-primary">
            <span class="htmx-indicator loading loading-spinner loading-sm"></span>
            Zapisz
        </button>
    </div>
</form>
```

### 4. Kalendarz `/admin/calendar/`

**Template**: `templates/admin_panel/calendar.html`
**View**: `apps.admin_panel.views.CalendarView`

```html
{% extends 'layouts/admin.html' %}

{% block extra_head %}
<link href="https://cdn.jsdelivr.net/npm/fullcalendar@6.1/main.min.css" rel="stylesheet">
{% endblock %}

{% block content %}
<div class="flex justify-between items-center mb-6">
    <h1 class="text-2xl font-bold">Kalendarz</h1>
    <button class="btn btn-primary"
            hx-get="{% url 'admin_panel:lesson_create' %}"
            hx-target="#modal-content"
            onclick="modal.showModal()">
        Nowa lekcja
    </button>
</div>

<div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
    <!-- Filters Sidebar -->
    <div class="lg:col-span-1">
        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <h3 class="card-title text-sm">Filtry</h3>

                <div class="form-control">
                    <label class="label">
                        <span class="label-text">Korepetytor</span>
                    </label>
                    <select id="tutor-filter" class="select select-bordered select-sm">
                        <option value="">Wszyscy</option>
                        {% for tutor in tutors %}
                        <option value="{{ tutor.pk }}">{{ tutor.get_full_name }}</option>
                        {% endfor %}
                    </select>
                </div>

                <div class="form-control">
                    <label class="label">
                        <span class="label-text">Sala</span>
                    </label>
                    <select id="room-filter" class="select select-bordered select-sm">
                        <option value="">Wszystkie</option>
                        {% for room in rooms %}
                        <option value="{{ room.pk }}">{{ room.name }}</option>
                        {% endfor %}
                    </select>
                </div>

                <div class="form-control">
                    <label class="label">
                        <span class="label-text">Przedmiot</span>
                    </label>
                    {% for subject in subjects %}
                    <label class="label cursor-pointer justify-start gap-2">
                        <input type="checkbox" class="checkbox checkbox-sm subject-filter"
                               value="{{ subject.pk }}" checked>
                        <span class="label-text">{{ subject.name }}</span>
                    </label>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>

    <!-- Calendar -->
    <div class="lg:col-span-3">
        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <div id="calendar"></div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="https://cdn.jsdelivr.net/npm/fullcalendar@6.1/index.global.min.js"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {
    var calendarEl = document.getElementById('calendar');

    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'timeGridWeek',
        locale: 'pl',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        events: '{% url "lessons:calendar_events" %}',
        editable: true,
        selectable: true,

        eventClick: function(info) {
            htmx.ajax('GET', `/admin/lessons/${info.event.id}/`, {
                target: '#modal-content'
            });
            document.getElementById('modal').showModal();
        },

        select: function(info) {
            htmx.ajax('GET', '{% url "admin_panel:lesson_create" %}?start=' + info.startStr, {
                target: '#modal-content'
            });
            document.getElementById('modal').showModal();
        },

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
    });

    calendar.render();

    // Filter handlers
    document.getElementById('tutor-filter').addEventListener('change', function() {
        calendar.refetchEvents();
    });
    document.getElementById('room-filter').addEventListener('change', function() {
        calendar.refetchEvents();
    });
});
</script>
{% endblock %}
```

---

## PANEL KOREPETYTORA

### Layout Tutor

**Template**: `templates/layouts/tutor.html`

```html
{% extends 'base.html' %}

{% block body %}
<div class="min-h-screen flex flex-col">
    <!-- Top Navigation -->
    <nav class="navbar bg-base-100 shadow-lg">
        <div class="navbar-start">
            <a href="{% url 'tutor_panel:dashboard' %}" class="btn btn-ghost text-xl">
                Na Piątkę
            </a>
        </div>

        <div class="navbar-center hidden lg:flex">
            <ul class="menu menu-horizontal px-1">
                <li><a href="{% url 'tutor_panel:dashboard' %}"
                       class="{% if request.resolver_match.url_name == 'dashboard' %}active{% endif %}">
                    Dashboard
                </a></li>
                <li><a href="{% url 'tutor_panel:calendar' %}"
                       class="{% if 'calendar' in request.path %}active{% endif %}">
                    Kalendarz
                </a></li>
                <li><a href="{% url 'tutor_panel:students' %}"
                       class="{% if 'students' in request.path %}active{% endif %}">
                    Uczniowie
                </a></li>
                <li><a href="{% url 'tutor_panel:attendance' %}"
                       class="{% if 'attendance' in request.path %}active{% endif %}">
                    Obecność
                </a></li>
                <li><a href="{% url 'tutor_panel:messages' %}"
                       class="{% if 'messages' in request.path %}active{% endif %}">
                    Wiadomości
                    {% if unread_messages > 0 %}
                    <span class="badge badge-sm badge-primary">{{ unread_messages }}</span>
                    {% endif %}
                </a></li>
            </ul>
        </div>

        <div class="navbar-end">
            {% include 'components/_notification_bell.html' %}
            {% include 'components/_user_dropdown.html' %}
        </div>
    </nav>

    <!-- Mobile bottom navigation -->
    <div class="btm-nav lg:hidden">
        <a href="{% url 'tutor_panel:dashboard' %}"
           class="{% if request.resolver_match.url_name == 'dashboard' %}active{% endif %}">
            <svg class="w-5 h-5"><!-- home icon --></svg>
        </a>
        <a href="{% url 'tutor_panel:calendar' %}"
           class="{% if 'calendar' in request.path %}active{% endif %}">
            <svg class="w-5 h-5"><!-- calendar icon --></svg>
        </a>
        <a href="{% url 'tutor_panel:students' %}"
           class="{% if 'students' in request.path %}active{% endif %}">
            <svg class="w-5 h-5"><!-- users icon --></svg>
        </a>
        <a href="{% url 'tutor_panel:messages' %}"
           class="{% if 'messages' in request.path %}active{% endif %} indicator">
            <svg class="w-5 h-5"><!-- message icon --></svg>
            {% if unread_messages > 0 %}
            <span class="indicator-item badge badge-primary badge-xs"></span>
            {% endif %}
        </a>
    </div>

    <!-- Content -->
    <main class="flex-1 p-4 lg:p-6 pb-20 lg:pb-6">
        {% block content %}{% endblock %}
    </main>
</div>
{% endblock %}
```

### Tutor Dashboard

**Template**: `templates/tutor_panel/dashboard.html`

```html
{% extends 'layouts/tutor.html' %}

{% block content %}
<h1 class="text-2xl font-bold mb-6">Witaj, {{ request.user.first_name }}!</h1>

<!-- Today's lessons -->
<div class="card bg-base-100 shadow mb-6">
    <div class="card-body">
        <h2 class="card-title">Dzisiejsze lekcje</h2>

        <ul class="timeline timeline-vertical">
            {% for lesson in todays_lessons %}
            <li>
                <div class="timeline-start">{{ lesson.start_time|time:"H:i" }}</div>
                <div class="timeline-middle">
                    <svg class="w-5 h-5"><!-- clock icon --></svg>
                </div>
                <div class="timeline-end timeline-box">
                    <div class="font-bold">{{ lesson.subject.name }}</div>
                    <div class="text-sm">
                        {{ lesson.students.all|join:", " }}
                    </div>
                    <div class="text-sm text-base-content/60">
                        {{ lesson.room.name }}
                    </div>
                    <a href="{% url 'tutor_panel:attendance_mark' lesson.pk %}"
                       class="btn btn-sm btn-primary mt-2">
                        Oznacz obecność
                    </a>
                </div>
                <hr/>
            </li>
            {% empty %}
            <li class="text-base-content/60">Brak lekcji na dziś</li>
            {% endfor %}
        </ul>
    </div>
</div>

<!-- Stats -->
<div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
    {% include 'components/_stat_card.html' with title="Lekcji w tym miesiącu" value=stats.lessons_count %}
    {% include 'components/_stat_card.html' with title="Godzin" value=stats.hours %}
    {% include 'components/_stat_card.html' with title="Zarobki" value=stats.earnings|currency %}
    {% include 'components/_stat_card.html' with title="Frekwencja" value=stats.attendance|percentage %}
</div>

<!-- Upcoming lessons -->
<div class="card bg-base-100 shadow">
    <div class="card-body">
        <h2 class="card-title">Nadchodzące lekcje</h2>
        <div class="overflow-x-auto">
            <table class="table">
                <tbody>
                    {% for lesson in upcoming_lessons %}
                    <tr class="hover">
                        <td>{{ lesson.start_time|date:"D, d.m" }}</td>
                        <td>{{ lesson.start_time|time:"H:i" }} - {{ lesson.end_time|time:"H:i" }}</td>
                        <td>{{ lesson.subject.name }}</td>
                        <td>{{ lesson.students.first.get_full_name }}</td>
                        <td>{{ lesson.room.name }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endblock %}
```

---

## PANEL UCZNIA/RODZICA

### Layout Student

**Template**: `templates/layouts/student.html`

(Podobny do tutor.html, ale z innymi linkami menu)

### Student Dashboard

**Template**: `templates/student_panel/dashboard.html`

```html
{% extends 'layouts/student.html' %}

{% block content %}
<h1 class="text-2xl font-bold mb-6">Panel ucznia</h1>

<!-- Today's schedule -->
<div class="card bg-base-100 shadow mb-6">
    <div class="card-body">
        <h2 class="card-title">Plan na dziś</h2>
        {% for lesson in todays_lessons %}
        <div class="flex items-center gap-4 p-3 bg-base-200 rounded-lg">
            <div class="text-lg font-mono">{{ lesson.start_time|time:"H:i" }}</div>
            <div class="flex-1">
                <div class="font-bold">{{ lesson.subject.name }}</div>
                <div class="text-sm">{{ lesson.tutor.get_full_name }}</div>
            </div>
            <div class="badge">{{ lesson.room.name }}</div>
        </div>
        {% empty %}
        <p class="text-base-content/60">Brak lekcji na dziś</p>
        {% endfor %}
    </div>
</div>

<!-- Makeup lessons alert -->
{% if makeup_lessons %}
<div class="alert alert-warning mb-6">
    <svg class="w-6 h-6"><!-- warning icon --></svg>
    <div>
        <h3 class="font-bold">Masz {{ makeup_lessons|length }} zajęcia do odrobienia</h3>
        <div class="text-sm">Najstarsze wygasa za {{ makeup_lessons.0.days_left }} dni</div>
    </div>
    <a href="{% url 'student_panel:makeup' %}" class="btn btn-sm">Zobacz</a>
</div>
{% endif %}

<!-- Attendance stats -->
<div class="grid grid-cols-2 gap-4 mb-6">
    <div class="card bg-base-100 shadow">
        <div class="card-body items-center text-center">
            <div class="radial-progress text-primary"
                 style="--value:{{ attendance_percentage }}; --size:8rem;">
                {{ attendance_percentage }}%
            </div>
            <h3 class="card-title">Frekwencja</h3>
        </div>
    </div>

    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <h3 class="card-title">Statystyki</h3>
            <div class="stat p-0">
                <div class="stat-title">Lekcji łącznie</div>
                <div class="stat-value">{{ total_lessons }}</div>
            </div>
        </div>
    </div>
</div>

<!-- Recent invoices -->
<div class="card bg-base-100 shadow">
    <div class="card-body">
        <h2 class="card-title">Ostatnie faktury</h2>
        <div class="overflow-x-auto">
            <table class="table">
                <tbody>
                    {% for invoice in recent_invoices %}
                    <tr class="hover">
                        <td>{{ invoice.number }}</td>
                        <td>{{ invoice.month|date:"F Y" }}</td>
                        <td>{{ invoice.total_amount|currency }}</td>
                        <td>
                            <span class="badge badge-{{ invoice.status }}">
                                {{ invoice.get_status_display }}
                            </span>
                        </td>
                        <td>
                            <a href="{{ invoice.pdf_url }}" class="btn btn-ghost btn-sm">
                                PDF
                            </a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endblock %}
```

---

## KOMPONENTY WSPÓŁDZIELONE

### Form Field Component

**Template**: `templates/components/_form_field.html`

```html
<div class="form-control w-full">
    <label class="label" for="{{ field.id_for_label }}">
        <span class="label-text">
            {{ field.label }}
            {% if field.field.required %}<span class="text-error">*</span>{% endif %}
        </span>
    </label>

    {% if field.field.widget.input_type == 'select' %}
    <select name="{{ field.name }}"
            id="{{ field.id_for_label }}"
            class="select select-bordered w-full {% if field.errors %}select-error{% endif %}"
            {% if field.field.required %}required{% endif %}>
        {% for value, label in field.field.choices %}
        <option value="{{ value }}" {% if field.value == value|stringformat:'s' %}selected{% endif %}>
            {{ label }}
        </option>
        {% endfor %}
    </select>
    {% elif field.field.widget.input_type == 'textarea' %}
    <textarea name="{{ field.name }}"
              id="{{ field.id_for_label }}"
              class="textarea textarea-bordered {% if field.errors %}textarea-error{% endif %}"
              placeholder="{{ field.field.widget.attrs.placeholder|default:'' }}"
              {% if field.field.required %}required{% endif %}>{{ field.value|default:'' }}</textarea>
    {% else %}
    <input type="{{ field.field.widget.input_type|default:'text' }}"
           name="{{ field.name }}"
           id="{{ field.id_for_label }}"
           value="{{ field.value|default:'' }}"
           class="input input-bordered w-full {% if field.errors %}input-error{% endif %}"
           placeholder="{{ field.field.widget.attrs.placeholder|default:'' }}"
           {% if field.field.required %}required{% endif %}>
    {% endif %}

    {% if field.help_text %}
    <label class="label">
        <span class="label-text-alt">{{ field.help_text }}</span>
    </label>
    {% endif %}

    {% if field.errors %}
    <label class="label">
        <span class="label-text-alt text-error">{{ field.errors.0 }}</span>
    </label>
    {% endif %}
</div>
```

### Stat Card Component

**Template**: `templates/components/_stat_card.html`

```html
<div class="stat bg-base-100 shadow rounded-box">
    <div class="stat-figure text-{{ color|default:'primary' }}">
        {% if icon %}
        <svg class="w-8 h-8"><!-- {{ icon }} --></svg>
        {% endif %}
    </div>
    <div class="stat-title">{{ title }}</div>
    <div class="stat-value text-{{ color|default:'primary' }}">{{ value }}</div>
    {% if trend %}
    <div class="stat-desc {% if trend.startswith '+' %}text-success{% else %}text-error{% endif %}">
        {{ trend }}
    </div>
    {% endif %}
</div>
```

### Avatar Component

**Template**: `templates/components/_avatar.html`

```html
{% with size=size|default:'md' %}
<div class="avatar {% if not user.avatar %}placeholder{% endif %}">
    <div class="{% if size == 'sm' %}w-8{% elif size == 'lg' %}w-16{% else %}w-12{% endif %}
                rounded-full bg-neutral text-neutral-content">
        {% if user.avatar %}
        <img src="{{ user.avatar.url }}" alt="{{ user.get_full_name }}">
        {% else %}
        <span class="{% if size == 'sm' %}text-xs{% elif size == 'lg' %}text-xl{% else %}text-base{% endif %}">
            {{ user.first_name.0 }}{{ user.last_name.0 }}
        </span>
        {% endif %}
    </div>
</div>
{% endwith %}
```

### Pagination Component

**Template**: `templates/components/_pagination.html`

```html
<div class="join">
    {% if page_obj.has_previous %}
    <a href="?page=1"
       hx-get="?page=1"
       hx-target="#{{ target|default:'content' }}"
       class="join-item btn btn-sm">
        &laquo;
    </a>
    <a href="?page={{ page_obj.previous_page_number }}"
       hx-get="?page={{ page_obj.previous_page_number }}"
       hx-target="#{{ target|default:'content' }}"
       class="join-item btn btn-sm">
        &lsaquo;
    </a>
    {% endif %}

    <span class="join-item btn btn-sm btn-disabled">
        {{ page_obj.number }} / {{ page_obj.paginator.num_pages }}
    </span>

    {% if page_obj.has_next %}
    <a href="?page={{ page_obj.next_page_number }}"
       hx-get="?page={{ page_obj.next_page_number }}"
       hx-target="#{{ target|default:'content' }}"
       class="join-item btn btn-sm">
        &rsaquo;
    </a>
    <a href="?page={{ page_obj.paginator.num_pages }}"
       hx-get="?page={{ page_obj.paginator.num_pages }}"
       hx-target="#{{ target|default:'content' }}"
       class="join-item btn btn-sm">
        &raquo;
    </a>
    {% endif %}
</div>
```

---

## HTMX PATTERNS

### 1. Search z debounce

```html
<input type="search"
       name="search"
       placeholder="Szukaj..."
       class="input input-bordered"
       hx-get="{% url 'users:list' %}"
       hx-trigger="keyup changed delay:300ms"
       hx-target="#results"
       hx-indicator="#search-spinner"
       hx-include="[name='role']">

<span id="search-spinner" class="htmx-indicator loading loading-spinner"></span>

<div id="results">
    {% include 'partials/_user_list.html' %}
</div>
```

### 2. Modal z formularzem

```html
<!-- Trigger -->
<button class="btn btn-primary"
        hx-get="{% url 'users:create' %}"
        hx-target="#modal-content"
        onclick="modal.showModal()">
    Dodaj
</button>

<!-- Modal (w base.html) -->
<dialog id="modal" class="modal">
    <div class="modal-box" id="modal-content">
        <!-- Zawartość ładowana przez HTMX -->
    </div>
    <form method="dialog" class="modal-backdrop">
        <button>close</button>
    </form>
</dialog>
```

### 3. Inline edit

```html
<!-- View mode -->
<div id="user-name-{{ user.pk }}"
     hx-get="{% url 'users:edit_name' user.pk %}"
     hx-target="this"
     hx-swap="outerHTML"
     class="cursor-pointer hover:bg-base-200 p-2 rounded">
    {{ user.get_full_name }}
</div>

<!-- Edit mode (partial) -->
<form id="user-name-{{ user.pk }}"
      hx-post="{% url 'users:edit_name' user.pk %}"
      hx-target="this"
      hx-swap="outerHTML"
      class="flex gap-2">
    <input type="text" name="name" value="{{ user.first_name }}" class="input input-sm input-bordered">
    <input type="text" name="surname" value="{{ user.last_name }}" class="input input-sm input-bordered">
    <button type="submit" class="btn btn-sm btn-primary">OK</button>
    <button type="button" class="btn btn-sm"
            hx-get="{% url 'users:name_view' user.pk %}"
            hx-target="#user-name-{{ user.pk }}"
            hx-swap="outerHTML">
        Anuluj
    </button>
</form>
```

### 4. Delete z potwierdzeniem

```html
<button class="btn btn-error btn-sm"
        hx-delete="{% url 'users:delete' user.pk %}"
        hx-confirm="Czy na pewno chcesz usunąć {{ user.get_full_name }}?"
        hx-target="closest tr"
        hx-swap="outerHTML swap:1s">
    Usuń
</button>
```

### 5. Infinite scroll

```html
<div id="lessons-list">
    {% for lesson in lessons %}
    <div class="card">{{ lesson.title }}</div>
    {% endfor %}

    {% if page_obj.has_next %}
    <div hx-get="?page={{ page_obj.next_page_number }}"
         hx-trigger="revealed"
         hx-target="this"
         hx-swap="outerHTML">
        <span class="loading loading-spinner"></span>
    </div>
    {% endif %}
</div>
```

### 6. Live validation

```html
<input type="email"
       name="email"
       class="input input-bordered"
       hx-post="{% url 'accounts:validate_email' %}"
       hx-trigger="blur"
       hx-target="next .error"
       hx-swap="innerHTML">
<span class="error label-text-alt text-error"></span>
```

### 7. Polling dla notyfikacji

```html
<div hx-get="{% url 'notifications:count' %}"
     hx-trigger="every 30s"
     hx-swap="innerHTML">
    {% include 'components/_notification_badge.html' %}
</div>
```

---

## FORMULARZE DJANGO

### Przykładowy Form z klasami Tailwind/daisyUI

```python
# apps/accounts/forms.py
from django import forms
from .models import User


class CreateUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'role']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Imię',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Nazwisko',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'email@example.com',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': '+48 123 456 789',
            }),
            'role': forms.Select(attrs={
                'class': 'select select-bordered w-full',
            }),
        }

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Użytkownik z tym emailem już istnieje.')
        return email
```

### Renderowanie formularza

```html
<form method="post" hx-post="{% url 'accounts:create' %}">
    {% csrf_token %}

    {% for field in form %}
    {% include 'components/_form_field.html' %}
    {% endfor %}

    {% if form.non_field_errors %}
    <div class="alert alert-error mb-4">
        {% for error in form.non_field_errors %}
        <span>{{ error }}</span>
        {% endfor %}
    </div>
    {% endif %}

    <button type="submit" class="btn btn-primary">Zapisz</button>
</form>
```

---

## RESPONSYWNOŚĆ

### Breakpoints (Tailwind)

- `sm`: 640px (telefony landscape)
- `md`: 768px (tablety)
- `lg`: 1024px (laptopy)
- `xl`: 1280px (desktopy)
- `2xl`: 1536px (duże monitory)

### Mobile-first patterns

#### Navigation

```html
<!-- Desktop: Sidebar -->
<aside class="hidden lg:block w-64">
    {% include '_sidebar.html' %}
</aside>

<!-- Mobile: Bottom nav -->
<nav class="btm-nav lg:hidden">
    <!-- ... -->
</nav>
```

#### Tables → Cards

```html
<!-- Desktop: Table -->
<table class="table hidden lg:table">
    <!-- ... -->
</table>

<!-- Mobile: Cards -->
<div class="lg:hidden space-y-4">
    {% for item in items %}
    <div class="card bg-base-100 shadow">
        <!-- ... -->
    </div>
    {% endfor %}
</div>
```

#### Calendar views

```html
<!-- Desktop: Week view default -->
<div class="hidden lg:block" id="calendar-week"></div>

<!-- Mobile: Day view or list -->
<div class="lg:hidden" id="calendar-day"></div>
```

---

## DESIGN TOKENS (daisyUI)

### Kolory

```css
/* daisyUI theme colors - używaj przez klasy */
.text-primary     /* Główny kolor */
.bg-secondary     /* Drugorzędny */
.badge-success    /* Sukces */
.alert-warning    /* Ostrzeżenie */
.btn-error        /* Błąd/danger */
.text-info        /* Informacja */

/* Neutral */
.bg-base-100      /* Tło karty */
.bg-base-200      /* Tło strony */
.bg-base-300      /* Tło sidebar */
.text-base-content /* Tekst główny */
```

### Komponenty daisyUI

- `btn`, `btn-primary`, `btn-ghost`, `btn-sm`
- `card`, `card-body`, `card-title`
- `badge`, `badge-success`, `badge-warning`
- `alert`, `alert-info`, `alert-error`
- `modal`, `modal-box`, `modal-action`
- `table`, `table-zebra`
- `navbar`, `drawer`, `btm-nav`
- `stat`, `stat-value`, `stat-desc`
- `timeline`, `timeline-item`
- `form-control`, `input`, `select`, `textarea`

---

## ZABEZPIECZENIA PER WIDOK

### Django View Mixins

```python
# apps/core/mixins.py
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_admin


class TutorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_tutor or self.request.user.is_admin


class StudentRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_student or self.request.user.is_admin
```

### Template conditionals

```html
{% if request.user.is_admin %}
<button class="btn btn-error">Usuń użytkownika</button>
{% endif %}

{% if request.user.is_tutor %}
<a href="{% url 'tutor_panel:attendance' %}">Oznacz obecność</a>
{% endif %}
```

---

**Ten dokument jest mapą wszystkich interfejsów użytkownika.**
**Każdy widok musi być zgodny z tym planem.**
**Aktualizuj po każdej znaczącej zmianie UI.**

**Data utworzenia**: Grudzień 2025
**Wersja**: 2.0.0 (Django + HTMX)
**Następna rewizja**: Po implementacji pierwszego modułu
