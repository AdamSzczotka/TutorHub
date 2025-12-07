from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.core.mixins import AdminRequiredMixin, HTMXMixin

from .forms import RoomForm
from .models import Room


class RoomListView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, ListView):
    """List all rooms with lesson counts."""

    model = Room
    template_name = 'admin_panel/rooms/list.html'
    partial_template_name = 'admin_panel/rooms/partials/_room_list.html'
    context_object_name = 'rooms'

    def get_queryset(self):
        """Return rooms with lesson counts."""
        return Room.objects.annotate(
            lesson_count=Count('lessons')
        ).order_by('name')

    def get_context_data(self, **kwargs):
        """Add page title to context."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Sale'
        return context


class RoomCreateView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, CreateView):
    """Create a new room."""

    model = Room
    form_class = RoomForm
    template_name = 'admin_panel/rooms/partials/_room_form.html'
    success_url = reverse_lazy('rooms:list')

    def get_context_data(self, **kwargs):
        """Add form title to context."""
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Dodaj sale'
        return context

    def form_valid(self, form):
        """Handle successful form submission."""
        form.save()

        if self.request.htmx:
            return HttpResponse(
                status=204,
                headers={
                    'HX-Trigger': 'roomCreated',
                    'HX-Reswap': 'none',
                }
            )
        return super().form_valid(form)


class RoomUpdateView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, UpdateView):
    """Update an existing room."""

    model = Room
    form_class = RoomForm
    template_name = 'admin_panel/rooms/partials/_room_form.html'
    success_url = reverse_lazy('rooms:list')

    def get_context_data(self, **kwargs):
        """Add form title to context."""
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Edytuj sale'
        return context

    def form_valid(self, form):
        """Handle successful form submission."""
        form.save()

        if self.request.htmx:
            return HttpResponse(
                status=204,
                headers={
                    'HX-Trigger': 'roomUpdated',
                    'HX-Reswap': 'none',
                }
            )
        return super().form_valid(form)


class RoomDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    """Delete a room."""

    model = Room
    success_url = reverse_lazy('rooms:list')

    def delete(self, request, *args, **kwargs):
        """Handle room deletion with lesson check."""
        self.object = self.get_object()

        if self.object.lessons.exists():
            return HttpResponse(
                '<div class="alert alert-error">'
                'Nie mozna usunac - sala ma przypisane lekcje.</div>',
                status=400
            )

        self.object.delete()

        if request.htmx:
            return HttpResponse(
                status=204,
                headers={'HX-Trigger': 'roomDeleted'}
            )

        return redirect(self.success_url)
