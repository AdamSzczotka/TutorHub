# Phase 3 - Sprint 3.1: Admin Dashboard & Core Interfaces (Django)

## Tasks 045-056: Administrative Foundation

> **Duration**: Week 7-8 (10 working days)
> **Goal**: Complete admin dashboard with statistics and user management
> **Dependencies**: Phase 2 completed

---

## SPRINT OVERVIEW

| Task ID | Description                       | Priority | Dependencies     |
| ------- | --------------------------------- | -------- | ---------------- |
| 045     | Admin dashboard layout            | Critical | Phase 2 complete |
| 046     | Real-time statistics widgets      | Critical | Task 045         |
| 047     | User management interface         | Critical | Task 046         |
| 048     | System settings panel             | Critical | Task 047         |
| 049     | Admin activity monitoring         | High     | Task 048         |
| 050     | System health monitoring          | High     | Task 049         |

---

## ADMIN DASHBOARD

### Admin Layout Base

**File**: `templates/admin_panel/base.html`

```html
{% extends "base.html" %}

{% block body %}
<div class="drawer lg:drawer-open">
    <input id="drawer" type="checkbox" class="drawer-toggle">

    <div class="drawer-content flex flex-col">
        <!-- Navbar -->
        <div class="navbar bg-base-100 border-b">
            <div class="flex-none lg:hidden">
                <label for="drawer" class="btn btn-square btn-ghost">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
                    </svg>
                </label>
            </div>
            <div class="flex-1 px-2">
                <span class="text-lg font-semibold">{{ page_title|default:"Panel Administracyjny" }}</span>
            </div>
            <div class="flex-none gap-2">
                {% include "admin_panel/partials/_notifications_dropdown.html" %}
                {% include "admin_panel/partials/_user_menu.html" %}
            </div>
        </div>

        <!-- Main content -->
        <main class="flex-1 p-6">
            {% block content %}{% endblock %}
        </main>
    </div>

    <!-- Sidebar -->
    <div class="drawer-side">
        <label for="drawer" class="drawer-overlay"></label>
        {% include "admin_panel/partials/_sidebar.html" %}
    </div>
</div>
{% endblock %}
```

### Sidebar Navigation

**File**: `templates/admin_panel/partials/_sidebar.html`

```html
<ul class="menu p-4 w-64 min-h-full bg-base-200 text-base-content">
    <li class="mb-4">
        <a href="{% url 'admin_panel:dashboard' %}" class="text-xl font-bold">
            Na Piątkę
        </a>
    </li>

    <li>
        <a href="{% url 'admin_panel:dashboard' %}" class="{% if request.resolver_match.url_name == 'dashboard' %}active{% endif %}">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
            </svg>
            Dashboard
        </a>
    </li>

    <li>
        <details {% if 'users' in request.path %}open{% endif %}>
            <summary>
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/>
                </svg>
                Użytkownicy
            </summary>
            <ul>
                <li><a href="{% url 'accounts:user-list' %}">Wszyscy</a></li>
                <li><a href="{% url 'accounts:user-create' %}">Nowy użytkownik</a></li>
                <li><a href="{% url 'accounts:user-import' %}">Import</a></li>
            </ul>
        </details>
    </li>

    <li>
        <details {% if 'calendar' in request.path %}open{% endif %}>
            <summary>
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                </svg>
                Kalendarz
            </summary>
            <ul>
                <li><a href="{% url 'lessons:calendar' %}">Kalendarz</a></li>
                <li><a href="{% url 'rooms:list' %}">Sale</a></li>
                <li><a href="{% url 'subjects:list' %}">Przedmioty</a></li>
            </ul>
        </details>
    </li>

    <li>
        <a href="{% url 'invoices:list' %}">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
            Faktury
        </a>
    </li>

    <li>
        <a href="{% url 'reports:overview' %}">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
            </svg>
            Raporty
        </a>
    </li>

    <li class="mt-auto">
        <a href="{% url 'admin_panel:settings' %}">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
            </svg>
            Ustawienia
        </a>
    </li>
</ul>
```

---

## DASHBOARD VIEW

**File**: `apps/admin_panel/views.py`

```python
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta

from apps.core.mixins import AdminRequiredMixin
from apps.accounts.models import User
from apps.lessons.models import Lesson
from apps.invoices.models import Invoice


class DashboardView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    template_name = 'admin_panel/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # Quick stats
        context['stats'] = {
            'total_users': User.objects.filter(is_active=True).count(),
            'total_tutors': User.objects.filter(role='tutor', is_active=True).count(),
            'total_students': User.objects.filter(role='student', is_active=True).count(),
            'lessons_this_week': Lesson.objects.filter(
                start_time__gte=week_ago,
                status__in=['scheduled', 'completed']
            ).count(),
            'pending_invoices': Invoice.objects.filter(
                status__in=['generated', 'sent']
            ).count(),
            'monthly_revenue': Invoice.objects.filter(
                status='paid',
                paid_at__gte=month_ago
            ).aggregate(total=Sum('total_amount'))['total'] or 0,
        }

        # Recent activity
        context['recent_users'] = User.objects.order_by('-date_joined')[:5]
        context['upcoming_lessons'] = Lesson.objects.filter(
            start_time__gte=now,
            status='scheduled'
        ).select_related('tutor', 'subject', 'room').order_by('start_time')[:5]

        return context
```

---

## DASHBOARD TEMPLATE

**File**: `templates/admin_panel/dashboard.html`

```html
{% extends "admin_panel/base.html" %}

{% block content %}
<div class="space-y-6">
    <h1 class="text-2xl font-bold">Dashboard</h1>

    <!-- Stats Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
         hx-get="{% url 'admin_panel:stats' %}"
         hx-trigger="every 60s"
         hx-swap="innerHTML">
        {% include "admin_panel/partials/_stats_cards.html" %}
    </div>

    <!-- Main Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Recent Users -->
        <div class="lg:col-span-2">
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <h2 class="card-title">Ostatnio dodani użytkownicy</h2>
                    <div class="overflow-x-auto">
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>Użytkownik</th>
                                    <th>Rola</th>
                                    <th>Data</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for user in recent_users %}
                                <tr>
                                    <td>
                                        <div class="flex items-center gap-2">
                                            <div class="avatar placeholder">
                                                <div class="bg-neutral text-neutral-content w-8 rounded-full">
                                                    <span class="text-xs">{{ user.first_name.0 }}{{ user.last_name.0 }}</span>
                                                </div>
                                            </div>
                                            <div>
                                                <div class="font-medium">{{ user.get_full_name }}</div>
                                                <div class="text-xs opacity-50">{{ user.email }}</div>
                                            </div>
                                        </div>
                                    </td>
                                    <td>
                                        <span class="badge badge-sm">{{ user.get_role_display }}</span>
                                    </td>
                                    <td class="text-sm">{{ user.date_joined|date:"d.m.Y" }}</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <!-- Upcoming Lessons -->
        <div>
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <h2 class="card-title">Nadchodzące zajęcia</h2>
                    <ul class="space-y-3">
                        {% for lesson in upcoming_lessons %}
                        <li class="flex items-center gap-3 p-2 rounded-lg hover:bg-base-200">
                            <div class="w-2 h-2 rounded-full" style="background-color: {{ lesson.subject.color|default:'#3B82F6' }}"></div>
                            <div class="flex-1 min-w-0">
                                <div class="font-medium truncate">{{ lesson.title }}</div>
                                <div class="text-xs opacity-60">
                                    {{ lesson.start_time|date:"d.m H:i" }} • {{ lesson.tutor.get_full_name }}
                                </div>
                            </div>
                        </li>
                        {% empty %}
                        <li class="text-center py-4 text-base-content/50">
                            Brak nadchodzących zajęć
                        </li>
                        {% endfor %}
                    </ul>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

---

## STATS CARDS PARTIAL

**File**: `templates/admin_panel/partials/_stats_cards.html`

```html
<div class="stat bg-base-100 rounded-lg shadow">
    <div class="stat-title">Użytkownicy</div>
    <div class="stat-value text-primary">{{ stats.total_users }}</div>
    <div class="stat-desc">{{ stats.total_tutors }} korepetytorów, {{ stats.total_students }} uczniów</div>
</div>

<div class="stat bg-base-100 rounded-lg shadow">
    <div class="stat-title">Zajęcia w tym tygodniu</div>
    <div class="stat-value text-secondary">{{ stats.lessons_this_week }}</div>
</div>

<div class="stat bg-base-100 rounded-lg shadow">
    <div class="stat-title">Faktury do zapłaty</div>
    <div class="stat-value text-warning">{{ stats.pending_invoices }}</div>
</div>

<div class="stat bg-base-100 rounded-lg shadow">
    <div class="stat-title">Przychód (miesiąc)</div>
    <div class="stat-value text-success">{{ stats.monthly_revenue|floatformat:0 }} zł</div>
</div>
```

---

## URL CONFIGURATION

**File**: `apps/admin_panel/urls.py`

```python
from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('stats/', views.StatsView.as_view(), name='stats'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
]
```

---

## COMPLETION CHECKLIST

- [ ] Admin layout with sidebar navigation
- [ ] Dashboard with real-time statistics
- [ ] User management integration
- [ ] System settings panel
- [ ] Activity monitoring
- [ ] Health monitoring

---

**Next Sprint**: 3.2 - System Configuration
