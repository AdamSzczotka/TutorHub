from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.core.mixins import AdminRequiredMixin, HTMXMixin

from .forms import LevelForm, SubjectForm
from .models import Level, Subject


class SubjectListView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, ListView):
    """List all subjects with lesson counts."""

    model = Subject
    template_name = 'admin_panel/subjects/list.html'
    partial_template_name = 'admin_panel/subjects/partials/_subject_list.html'
    context_object_name = 'subjects'

    def get_queryset(self):
        """Return subjects with lesson counts."""
        return Subject.objects.annotate(
            lesson_count=Count('lessons')
        ).order_by('name')

    def get_context_data(self, **kwargs):
        """Add page title to context."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Przedmioty'
        return context


class SubjectCreateView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, CreateView):
    """Create a new subject."""

    model = Subject
    form_class = SubjectForm
    template_name = 'admin_panel/subjects/partials/_subject_form.html'
    success_url = reverse_lazy('subjects:list')

    def get_context_data(self, **kwargs):
        """Add form title to context."""
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Dodaj przedmiot'
        return context

    def form_valid(self, form):
        """Handle successful form submission."""
        form.save()

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
    """Update an existing subject."""

    model = Subject
    form_class = SubjectForm
    template_name = 'admin_panel/subjects/partials/_subject_form.html'
    success_url = reverse_lazy('subjects:list')

    def get_context_data(self, **kwargs):
        """Add form title to context."""
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Edytuj przedmiot'
        return context

    def form_valid(self, form):
        """Handle successful form submission."""
        form.save()

        if self.request.htmx:
            return HttpResponse(
                status=204,
                headers={
                    'HX-Trigger': 'subjectUpdated',
                    'HX-Reswap': 'none',
                }
            )
        return super().form_valid(form)


class SubjectDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    """Delete a subject."""

    model = Subject
    success_url = reverse_lazy('subjects:list')

    def delete(self, request, *args, **kwargs):
        """Handle subject deletion with lesson check."""
        self.object = self.get_object()

        if self.object.lessons.exists():
            return HttpResponse(
                '<div class="alert alert-error">'
                'Nie mozna usunac - przedmiot ma przypisane lekcje.</div>',
                status=400
            )

        self.object.delete()

        if request.htmx:
            return HttpResponse(
                status=204,
                headers={'HX-Trigger': 'subjectDeleted'}
            )

        return redirect(self.success_url)


class LevelListView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, ListView):
    """List all education levels."""

    model = Level
    template_name = 'admin_panel/levels/list.html'
    partial_template_name = 'admin_panel/levels/partials/_level_list.html'
    context_object_name = 'levels'

    def get_queryset(self):
        """Return levels ordered by order_index."""
        return Level.objects.order_by('order_index')

    def get_context_data(self, **kwargs):
        """Add page title to context."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Poziomy'
        return context


class LevelCreateView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, CreateView):
    """Create a new education level."""

    model = Level
    form_class = LevelForm
    template_name = 'admin_panel/levels/partials/_level_form.html'
    success_url = reverse_lazy('subjects:level-list')

    def get_context_data(self, **kwargs):
        """Add form title to context."""
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Dodaj poziom'
        return context

    def form_valid(self, form):
        """Handle successful form submission."""
        form.save()

        if self.request.htmx:
            return HttpResponse(
                status=204,
                headers={
                    'HX-Trigger': 'levelCreated',
                    'HX-Reswap': 'none',
                }
            )
        return super().form_valid(form)


class LevelUpdateView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, UpdateView):
    """Update an existing education level."""

    model = Level
    form_class = LevelForm
    template_name = 'admin_panel/levels/partials/_level_form.html'
    success_url = reverse_lazy('subjects:level-list')

    def get_context_data(self, **kwargs):
        """Add form title to context."""
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Edytuj poziom'
        return context

    def form_valid(self, form):
        """Handle successful form submission."""
        form.save()

        if self.request.htmx:
            return HttpResponse(
                status=204,
                headers={
                    'HX-Trigger': 'levelUpdated',
                    'HX-Reswap': 'none',
                }
            )
        return super().form_valid(form)


class LevelDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    """Delete an education level."""

    model = Level
    success_url = reverse_lazy('subjects:level-list')

    def delete(self, request, *args, **kwargs):
        """Handle level deletion."""
        self.object = self.get_object()
        self.object.delete()

        if request.htmx:
            return HttpResponse(
                status=204,
                headers={'HX-Trigger': 'levelDeleted'}
            )

        return redirect(self.success_url)
