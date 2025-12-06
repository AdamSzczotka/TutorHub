# TASKS Directory - System "Na Piątkę"

## Comprehensive Task Breakdown for CMS School Management System

> **CRITICAL**: This directory contains the complete task breakdown for the 3-month development project.
> All tasks are derived from RULES analysis and must be executed following ImplementationGuidelines.md
> Total: 165 tasks across 13 phases and 26 sprints

---

## PROJECT OVERVIEW

| Metryka | Wartość |
|---------|---------|
| **Total Tasks** | 165 |
| **Development Time** | 17 weeks (3 months) |
| **Phases** | 13 (Phase 0-12) |
| **Sprints** | 26 (2 per phase average) |
| **Functionality Coverage** | 100% |

---

## TECHNOLOGY STACK (Django + HTMX)

### Technology Stack Compliance

Every task MUST use:

| Kategoria | Technologia | Wersja |
|-----------|-------------|--------|
| **Framework** | Django | 5.1.x |
| **Database ORM** | Django ORM | Built-in |
| **Database** | PostgreSQL | 17.x |
| **Interactivity** | HTMX | 2.0.x |
| **UI Reactivity** | Alpine.js | 3.x |
| **Styling** | Tailwind CSS | 3.4.x |
| **Components** | daisyUI | 4.x |
| **Background Tasks** | Celery + Redis | Latest |
| **Testing** | pytest-django | Latest |
| **Linting** | Ruff | Latest |

### Implementation Guidelines Compliance

Every task MUST follow:

- **Proper file organization** (apps/, templates/, static/)
- **Django best practices** (CBV, mixins, managers)
- **Django Forms/Serializers** for all inputs validation
- **Error handling** patterns (try/except, messages framework)
- **Security best practices** (CSRF, XSS protection)
- **Performance optimization** (select_related, prefetch_related)
- **Testing requirements** (>80% coverage with pytest)

---

## TASK ORGANIZATION

### Phase-based Structure

```
TASKS/
├── README.md                    # This file
├── phase-00-setup/              # Project setup (3 days)
│   └── sprint-0.1-initialization.md
├── phase-01-foundation/         # Authentication & database (2 weeks)
│   └── sprint-1.1-database-models.md
├── phase-02-users/              # User management (2 weeks)
│   ├── sprint-2.1-user-crud.md
│   ├── sprint-2.2-profile-advanced.md
│   ├── sprint-2.3-landing-page.md
│   └── sprint-2.4-cms-admin.md
├── phase-03-admin/              # Admin panel (2 weeks)
│   ├── sprint-3.1-admin-dashboard.md
│   └── sprint-3.2-system-config.md
├── phase-04-calendar/           # Calendar & lessons (2 weeks)
│   ├── sprint-4.1-calendar-integration.md
│   └── sprint-4.2-lesson-management.md
├── phase-05-attendance/         # Attendance system (1 week)
│   ├── sprint-5.1-attendance-marking.md
│   └── sprint-5.2-stats-reports.md
├── phase-06-cancellations/      # Cancellation & makeup (1 week)
│   ├── sprint-6.1-cancellation-system.md
│   └── sprint-6.2-makeup-lessons.md
├── phase-07-invoicing/          # Billing system (1 week)
│   ├── sprint-7.1-invoice-basics.md
│   └── sprint-7.2-billing-cycle.md
├── phase-08-communication/      # Messages & notifications (1 week)
│   ├── sprint-8.1-messaging-system.md
│   └── sprint-8.2-notifications.md
├── phase-09-portals/            # User portals (1 week)
│   ├── sprint-9.1-tutor-portal.md
│   ├── sprint-9.2-student-portal.md
│   └── sprint-9.3-parent-portal.md
├── phase-10-filters/            # Filtering & export (1 week)
│   ├── sprint-10.1-real-time-filtering.md
│   └── sprint-10.2-data-export.md
├── phase-11-optimization/       # Performance & security (1 week)
│   ├── sprint-11.1-performance.md
│   └── sprint-11.2-security.md
├── phase-12-testing/            # Testing & documentation (1 week)
│   ├── sprint-12.1-testing-suite.md
│   └── sprint-12.2-documentation.md
└── phase-13-deployment/         # Production deployment (1 week)
    ├── sprint-13.1-production-prep.md
    └── sprint-13.2-go-live.md
```

### Functional Areas

| Area | Tasks |
|------|-------|
| Authentication & Authorization | 22 |
| User Management | 18 |
| Calendar & Lessons | 25 |
| Attendance System | 12 |
| Invoicing & Billing | 16 |
| Communication | 14 |
| Admin Dashboard | 15 |
| User Portals | 13 |
| Data Export & Filtering | 10 |
| Performance & Security | 8 |
| Testing & Deployment | 12 |

---

## DJANGO PROJECT STRUCTURE

```
napiatke/
├── manage.py
├── napiatke/                    # Main Django project
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py              # Common settings
│   │   ├── development.py       # Dev settings
│   │   └── production.py        # Prod settings
│   ├── urls.py                  # Root URL configuration
│   ├── wsgi.py
│   ├── asgi.py
│   └── celery.py                # Celery configuration
├── apps/
│   ├── accounts/                # User authentication & profiles
│   ├── tutors/                  # Tutor-specific features
│   ├── students/                # Student-specific features
│   ├── lessons/                 # Lesson management
│   ├── rooms/                   # Room management
│   ├── subjects/                # Subjects & levels
│   ├── attendance/              # Attendance tracking
│   ├── cancellations/           # Cancellations & makeup
│   ├── invoices/                # Billing & invoices
│   ├── messages/                # Internal messaging
│   ├── notifications/           # Notification system
│   ├── reports/                 # Reports & statistics
│   ├── landing/                 # Public landing page
│   └── core/                    # Shared utilities
├── templates/
│   ├── base.html                # Base template
│   ├── components/              # Reusable UI components
│   ├── partials/                # HTMX partial responses
│   ├── admin_panel/             # Admin templates
│   ├── tutor_panel/             # Tutor templates
│   └── student_panel/           # Student templates
├── static/
│   ├── css/                     # Compiled CSS
│   ├── js/                      # JavaScript (HTMX, Alpine)
│   └── img/                     # Images
├── media/                       # User uploads
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
├── docker-compose.yml
├── Dockerfile
├── pytest.ini
├── pyproject.toml               # Ruff config
└── .env.example
```

---

## TASK STATUS TRACKING

### Status Types

| Status | Description |
|--------|-------------|
| `pending` | Not started |
| `in_progress` | Currently being worked on |
| `completed` | Finished and tested |
| `blocked` | Waiting for dependencies |
| `review` | Ready for code review |

### Priority Levels

| Priority | Description |
|----------|-------------|
| `critical` | Must be completed for MVP |
| `high` | Important for full functionality |
| `medium` | Nice to have features |
| `low` | Future enhancements |

---

## DEPENDENCIES

### Cross-Phase Dependencies

```
Phase 0 (Setup) → Phase 1 (Foundation)
     ↓
Phase 1 (Foundation) → All other phases
     ↓
Phase 2 (Users) → Phase 3 (Admin)
     ↓
Phase 3 (Admin) → Phase 4 (Calendar)
     ↓
Phase 4 (Calendar) → Phase 5 (Attendance)
     ↓
Phase 5 (Attendance) → Phase 6 (Cancellations)
     ↓
Phase 6 (Cancellations) → Phase 7 (Invoicing)
```

### External Dependencies

| Dependency | Required By |
|------------|-------------|
| PostgreSQL Database | Phase 0+ |
| Redis Server | Phase 0+ |
| Django Settings | Phase 0+ |
| Custom User Model | Phase 1+ |
| Authentication System | Phase 1+ |

---

## QUICK START

### For Developers

1. **Read complete task file** for your assigned phase
2. **Check dependencies** and prerequisites
3. **Activate virtual environment**:
   ```bash
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```
4. **Run migrations** if needed:
   ```bash
   python manage.py migrate
   ```
5. **Follow implementation guidelines** from `docs/RULES/ImplementationGuidelines.md`
6. **Test thoroughly**:
   ```bash
   pytest apps/your_app/tests/
   ```
7. **Check code quality**:
   ```bash
   ruff check .
   ruff format .
   ```

### For Project Managers

1. Monitor task progress through sprint files
2. Check dependency chains
3. Validate deliverables against requirements
4. Ensure compliance with Django guidelines
5. Track timeline adherence

---

## DJANGO COMMANDS REFERENCE

### Development Commands

```bash
# Run development server
python manage.py runserver

# Create new app
python manage.py startapp app_name apps/app_name

# Database operations
python manage.py makemigrations
python manage.py migrate
python manage.py dbshell

# Create superuser
python manage.py createsuperuser

# Django shell
python manage.py shell_plus  # (with django-extensions)

# Collect static files
python manage.py collectstatic
```

### Testing Commands

```bash
# Run all tests
pytest

# Run specific app tests
pytest apps/accounts/tests/

# Run with coverage
pytest --cov=apps --cov-report=html

# Run specific test
pytest apps/accounts/tests/test_views.py::TestLoginView
```

### Background Tasks

```bash
# Start Celery worker
celery -A napiatke worker -l info

# Start Celery beat (scheduler)
celery -A napiatke beat -l info

# Start both (development)
celery -A napiatke worker -B -l info
```

---

## SUCCESS METRICS

### Technical KPIs

| Metric | Target |
|--------|--------|
| All tasks completed | On time |
| Test coverage | > 80% |
| Security vulnerabilities | Zero |
| Code quality (Ruff) | No errors |
| Django Debug Toolbar | <50ms avg response |

### Business KPIs

| Metric | Target |
|--------|--------|
| MVP delivered | 2 months |
| Full system | 3 months |
| Functional coverage | 100% |
| RODO/GDPR compliance | Achieved |

---

## QUALITY GATES

### Before Task Completion

- [ ] Code follows `ImplementationGuidelines.md`
- [ ] All Django migrations created and applied
- [ ] HTMX patterns correctly implemented
- [ ] All pytest tests pass
- [ ] Security review completed (CSRF, XSS)
- [ ] No Ruff errors
- [ ] Documentation updated

### Before Phase Completion

- [ ] All phase tasks completed
- [ ] Integration tests pass
- [ ] Code review completed
- [ ] Docker build successful
- [ ] Metrics collected

---

## HTMX INTEGRATION PATTERNS

### Standard Patterns Used

| Pattern | HTMX Attributes |
|---------|-----------------|
| Search with debounce | `hx-get`, `hx-trigger="keyup changed delay:300ms"` |
| Modal forms | `hx-get`, `hx-target="#modal-content"` |
| Inline edit | `hx-post`, `hx-swap="outerHTML"` |
| Delete with confirm | `hx-delete`, `hx-confirm` |
| Infinite scroll | `hx-get`, `hx-trigger="revealed"` |
| Live validation | `hx-post`, `hx-trigger="blur"` |
| Polling | `hx-get`, `hx-trigger="every 30s"` |

### Response Patterns

```python
# Django view returning partial
def list_view(request):
    items = Model.objects.all()
    if request.htmx:
        return render(request, 'partials/_list.html', {'items': items})
    return render(request, 'full_page.html', {'items': items})
```

---

**Created**: December 2025
**Version**: 2.0.0 (Django + HTMX)
**Next Review**: After each sprint completion
