"""Views for landing app."""

import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    TemplateView,
    UpdateView,
)

from apps.core.mixins import AdminRequiredMixin, HTMXMixin

from .forms import (
    ContactForm,
    EducationLevelForm,
    FAQItemForm,
    LandingStatisticForm,
    LeadStatusForm,
    LessonTypeForm,
    PageContentForm,
    PricingPackageForm,
    SchoolInfoForm,
    SubjectForm,
    TeamMemberForm,
    TestimonialForm,
    WhyUsCardForm,
)
from .models import (
    EducationLevel,
    FAQItem,
    LandingStatistic,
    LandingSubject,
    Lead,
    LessonType,
    PageContent,
    PricingPackage,
    SchoolInfo,
    TeamMember,
    Testimonial,
    WhyUsCard,
)


# =============================================================================
# Public Views
# =============================================================================


class LandingPageView(TemplateView):
    """Main landing page."""

    template_name = 'landing/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            'hero': PageContent.objects.filter(page_key='hero', is_active=True).first(),
            'about': PageContent.objects.filter(page_key='about', is_active=True).first(),
            'team': TeamMember.objects.filter(is_published=True),
            'testimonials': Testimonial.objects.filter(is_published=True),
            'faq_items': FAQItem.objects.filter(is_published=True),
            'school_info': SchoolInfo.objects.first(),
            'contact_form': ContactForm(),
            # New CMS data
            'statistics': LandingStatistic.objects.filter(is_published=True),
            'why_us_cards': WhyUsCard.objects.filter(is_published=True),
            'subjects': LandingSubject.objects.filter(is_published=True),
            'pricing_packages': PricingPackage.objects.filter(is_published=True),
            'education_levels': EducationLevel.objects.filter(is_published=True),
            'lesson_types': LessonType.objects.filter(is_published=True),
        })

        return context


class PrivacyPolicyView(TemplateView):
    """Privacy policy page."""

    template_name = 'landing/privacy_policy.html'


class ContactFormView(CreateView):
    """Handle contact form submission with HTMX."""

    model = Lead
    form_class = ContactForm
    template_name = 'landing/partials/_contact_form.html'

    def form_valid(self, form):
        form.save()

        from .tasks import notify_new_lead
        notify_new_lead.delay(form.instance.id)

        if self.request.headers.get('HX-Request'):
            return HttpResponse('''
                <div class="alert alert-success">
                    <span>Dziękujemy za wiadomość! Skontaktujemy się wkrótce.</span>
                </div>
            ''')

        messages.success(self.request, 'Wiadomość została wysłana.')
        return redirect('landing:home')

    def form_invalid(self, form):
        if self.request.headers.get('HX-Request'):
            return render(self.request, self.template_name, {'form': form})
        return super().form_invalid(form)


# =============================================================================
# CMS Admin Views - Dashboard
# =============================================================================


class CMSDashboardView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """CMS Dashboard with overview of all content."""

    template_name = 'admin_panel/cms/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Zarządzanie treścią',
            'page_contents_count': PageContent.objects.count(),
            'team_members_count': TeamMember.objects.count(),
            'testimonials_count': Testimonial.objects.count(),
            'testimonials_pending': Testimonial.objects.filter(is_published=False).count(),
            'faq_items_count': FAQItem.objects.count(),
            'leads_count': Lead.objects.count(),
            'leads_new': Lead.objects.filter(status='new').count(),
            'school_info': SchoolInfo.objects.first(),
        })
        return context


# =============================================================================
# CMS Admin Views - Page Content
# =============================================================================


class PageContentListView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, ListView):
    """List all page content sections."""

    model = PageContent
    template_name = 'admin_panel/cms/content/list.html'
    partial_template_name = 'admin_panel/cms/content/partials/_list.html'
    context_object_name = 'contents'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Treści strony'
        return context


class PageContentCreateView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, CreateView):
    """Create new page content section."""

    model = PageContent
    form_class = PageContentForm
    template_name = 'admin_panel/cms/content/form.html'
    success_url = reverse_lazy('landing:cms-content-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Dodaj sekcję'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Sekcja została dodana.')
        return super().form_valid(form)


class PageContentUpdateView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, UpdateView):
    """Edit page content section."""

    model = PageContent
    form_class = PageContentForm
    template_name = 'admin_panel/cms/content/form.html'
    success_url = reverse_lazy('landing:cms-content-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edytuj: {self.object.page_key}'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Sekcja została zaktualizowana.')
        return super().form_valid(form)


class PageContentDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    """Delete page content section."""

    model = PageContent
    success_url = reverse_lazy('landing:cms-content-list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()

        if request.headers.get('HX-Request'):
            return HttpResponse('')

        messages.success(request, 'Sekcja została usunięta.')
        return redirect(self.success_url)


class PageContentToggleView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Toggle page content active status."""

    def post(self, request, pk):
        content = get_object_or_404(PageContent, pk=pk)
        content.is_active = not content.is_active
        content.save()

        if request.headers.get('HX-Request'):
            return render(
                request,
                'admin_panel/cms/content/partials/_row.html',
                {'content': content}
            )

        messages.success(request, 'Status sekcji został zmieniony.')
        return redirect('landing:cms-content-list')


# =============================================================================
# CMS Admin Views - Team Members
# =============================================================================


class TeamMemberListView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, ListView):
    """List all team members."""

    model = TeamMember
    template_name = 'admin_panel/cms/team/list.html'
    partial_template_name = 'admin_panel/cms/team/partials/_list.html'
    context_object_name = 'members'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Zespół'
        return context


class TeamMemberCreateView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, CreateView):
    """Create new team member."""

    model = TeamMember
    form_class = TeamMemberForm
    template_name = 'admin_panel/cms/team/form.html'
    success_url = reverse_lazy('landing:cms-team-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Dodaj członka zespołu'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Członek zespołu został dodany.')
        return super().form_valid(form)


class TeamMemberUpdateView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, UpdateView):
    """Edit team member."""

    model = TeamMember
    form_class = TeamMemberForm
    template_name = 'admin_panel/cms/team/form.html'
    success_url = reverse_lazy('landing:cms-team-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edytuj: {self.object.name} {self.object.surname}'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Członek zespołu został zaktualizowany.')
        return super().form_valid(form)


class TeamMemberDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    """Delete team member."""

    model = TeamMember
    success_url = reverse_lazy('landing:cms-team-list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()

        if request.headers.get('HX-Request'):
            return HttpResponse('')

        messages.success(request, 'Członek zespołu został usunięty.')
        return redirect(self.success_url)


class TeamMemberToggleView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Toggle team member published status."""

    def post(self, request, pk):
        member = get_object_or_404(TeamMember, pk=pk)
        member.is_published = not member.is_published
        member.save()

        if request.headers.get('HX-Request'):
            return render(
                request,
                'admin_panel/cms/team/partials/_row.html',
                {'member': member}
            )

        messages.success(request, 'Status członka zespołu został zmieniony.')
        return redirect('landing:cms-team-list')


class TeamMemberReorderView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Reorder team members via AJAX."""

    def post(self, request):
        try:
            data = json.loads(request.body)
            order = data.get('order', [])

            for index, member_id in enumerate(order):
                TeamMember.objects.filter(pk=member_id).update(order_index=index)

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


# =============================================================================
# CMS Admin Views - Testimonials
# =============================================================================


class TestimonialListView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, ListView):
    """List all testimonials with moderation tabs."""

    model = Testimonial
    template_name = 'admin_panel/cms/testimonials/list.html'
    partial_template_name = 'admin_panel/cms/testimonials/partials/_list.html'
    context_object_name = 'testimonials'

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get('status', 'all')

        if status == 'pending':
            queryset = queryset.filter(is_published=False)
        elif status == 'published':
            queryset = queryset.filter(is_published=True)

        return queryset.order_by('display_order')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Opinie'
        context['current_status'] = self.request.GET.get('status', 'all')
        context['pending_count'] = Testimonial.objects.filter(is_published=False).count()
        context['published_count'] = Testimonial.objects.filter(is_published=True).count()
        return context


class TestimonialCreateView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, CreateView):
    """Create new testimonial."""

    model = Testimonial
    form_class = TestimonialForm
    template_name = 'admin_panel/cms/testimonials/form.html'
    success_url = reverse_lazy('landing:cms-testimonial-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Dodaj opinię'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Opinia została dodana.')
        return super().form_valid(form)


class TestimonialUpdateView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, UpdateView):
    """Edit testimonial."""

    model = Testimonial
    form_class = TestimonialForm
    template_name = 'admin_panel/cms/testimonials/form.html'
    success_url = reverse_lazy('landing:cms-testimonial-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edytuj opinię: {self.object.student_name}'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Opinia została zaktualizowana.')
        return super().form_valid(form)


class TestimonialDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    """Delete testimonial."""

    model = Testimonial
    success_url = reverse_lazy('landing:cms-testimonial-list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()

        if request.headers.get('HX-Request'):
            return HttpResponse('')

        messages.success(request, 'Opinia została usunięta.')
        return redirect(self.success_url)


class TestimonialApproveView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Approve and publish testimonial."""

    def post(self, request, pk):
        testimonial = get_object_or_404(Testimonial, pk=pk)
        publish = request.POST.get('publish', 'true') == 'true'

        testimonial.is_verified = True
        testimonial.is_published = publish
        testimonial.save()

        if request.headers.get('HX-Request'):
            return render(
                request,
                'admin_panel/cms/testimonials/partials/_row.html',
                {'testimonial': testimonial}
            )

        messages.success(request, 'Opinia została zatwierdzona.')
        return redirect('landing:cms-testimonial-list')


class TestimonialToggleView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Toggle testimonial published status."""

    def post(self, request, pk):
        testimonial = get_object_or_404(Testimonial, pk=pk)
        testimonial.is_published = not testimonial.is_published
        testimonial.save()

        if request.headers.get('HX-Request'):
            return render(
                request,
                'admin_panel/cms/testimonials/partials/_row.html',
                {'testimonial': testimonial}
            )

        messages.success(request, 'Status opinii został zmieniony.')
        return redirect('landing:cms-testimonial-list')


# =============================================================================
# CMS Admin Views - FAQ
# =============================================================================


class FAQListView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, ListView):
    """List all FAQ items."""

    model = FAQItem
    template_name = 'admin_panel/cms/faq/list.html'
    partial_template_name = 'admin_panel/cms/faq/partials/_list.html'
    context_object_name = 'faq_items'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'FAQ'
        return context


class FAQCreateView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, CreateView):
    """Create new FAQ item."""

    model = FAQItem
    form_class = FAQItemForm
    template_name = 'admin_panel/cms/faq/form.html'
    success_url = reverse_lazy('landing:cms-faq-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Dodaj pytanie'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Pytanie zostało dodane.')
        return super().form_valid(form)


class FAQUpdateView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, UpdateView):
    """Edit FAQ item."""

    model = FAQItem
    form_class = FAQItemForm
    template_name = 'admin_panel/cms/faq/form.html'
    success_url = reverse_lazy('landing:cms-faq-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edytuj pytanie'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Pytanie zostało zaktualizowane.')
        return super().form_valid(form)


class FAQDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    """Delete FAQ item."""

    model = FAQItem
    success_url = reverse_lazy('landing:cms-faq-list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()

        if request.headers.get('HX-Request'):
            return HttpResponse('')

        messages.success(request, 'Pytanie zostało usunięte.')
        return redirect(self.success_url)


class FAQToggleView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Toggle FAQ item published status."""

    def post(self, request, pk):
        faq = get_object_or_404(FAQItem, pk=pk)
        faq.is_published = not faq.is_published
        faq.save()

        if request.headers.get('HX-Request'):
            return render(
                request,
                'admin_panel/cms/faq/partials/_row.html',
                {'faq': faq}
            )

        messages.success(request, 'Status pytania został zmieniony.')
        return redirect('landing:cms-faq-list')


class FAQReorderView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Reorder FAQ items via AJAX."""

    def post(self, request):
        try:
            data = json.loads(request.body)
            order = data.get('order', [])

            for index, faq_id in enumerate(order):
                FAQItem.objects.filter(pk=faq_id).update(order_index=index)

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


# =============================================================================
# CMS Admin Views - School Settings
# =============================================================================


class SchoolSettingsView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, UpdateView):
    """Edit school information."""

    model = SchoolInfo
    form_class = SchoolInfoForm
    template_name = 'admin_panel/cms/settings/school.html'
    success_url = reverse_lazy('landing:cms-school-settings')

    def get_object(self, queryset=None):
        # Get or create the school info (singleton pattern)
        obj, created = SchoolInfo.objects.get_or_create(
            pk=1,
            defaults={'name': 'Na Piątkę'}
        )
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Ustawienia szkoły'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Ustawienia szkoły zostały zapisane.')
        return super().form_valid(form)


# =============================================================================
# CMS Admin Views - Leads
# =============================================================================


class LeadListView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, ListView):
    """List all leads/contact form submissions."""

    model = Lead
    template_name = 'admin_panel/cms/leads/list.html'
    partial_template_name = 'admin_panel/cms/leads/partials/_list.html'
    context_object_name = 'leads'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get('status')

        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Wiadomości kontaktowe'
        context['current_status'] = self.request.GET.get('status', '')
        context['status_choices'] = Lead.Status.choices
        context['new_count'] = Lead.objects.filter(status='new').count()
        return context


class LeadDetailView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, TemplateView):
    """View lead details."""

    template_name = 'admin_panel/cms/leads/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lead = get_object_or_404(Lead, pk=self.kwargs['pk'])
        context['lead'] = lead
        context['title'] = f'Wiadomość od: {lead.name}'
        context['status_form'] = LeadStatusForm(instance=lead)
        return context


class LeadStatusUpdateView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Update lead status."""

    def post(self, request, pk):
        lead = get_object_or_404(Lead, pk=pk)
        form = LeadStatusForm(request.POST, instance=lead)

        if form.is_valid():
            form.save()

            if request.headers.get('HX-Request'):
                return render(
                    request,
                    'admin_panel/cms/leads/partials/_status_badge.html',
                    {'lead': lead}
                )

            messages.success(request, 'Status został zaktualizowany.')

        return redirect('landing:cms-lead-detail', pk=pk)


class LeadDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    """Delete lead."""

    model = Lead
    success_url = reverse_lazy('landing:cms-lead-list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()

        if request.headers.get('HX-Request'):
            return HttpResponse('')

        messages.success(request, 'Wiadomość została usunięta.')
        return redirect(self.success_url)


# =============================================================================
# CMS Admin Views - Statistics
# =============================================================================


class StatisticListView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, ListView):
    """List all landing page statistics."""

    model = LandingStatistic
    template_name = 'admin_panel/cms/statistics/list.html'
    partial_template_name = 'admin_panel/cms/statistics/partials/_list.html'
    context_object_name = 'statistics'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Statystyki'
        return context


class StatisticCreateView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, CreateView):
    """Create new statistic."""

    model = LandingStatistic
    form_class = LandingStatisticForm
    template_name = 'admin_panel/cms/statistics/form.html'
    success_url = reverse_lazy('landing:cms-statistic-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Dodaj statystykę'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Statystyka została dodana.')
        return super().form_valid(form)


class StatisticUpdateView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, UpdateView):
    """Edit statistic."""

    model = LandingStatistic
    form_class = LandingStatisticForm
    template_name = 'admin_panel/cms/statistics/form.html'
    success_url = reverse_lazy('landing:cms-statistic-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edytuj: {self.object.value}'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Statystyka została zaktualizowana.')
        return super().form_valid(form)


class StatisticDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    """Delete statistic."""

    model = LandingStatistic
    success_url = reverse_lazy('landing:cms-statistic-list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        if request.headers.get('HX-Request'):
            return HttpResponse('')
        messages.success(request, 'Statystyka została usunięta.')
        return redirect(self.success_url)


# =============================================================================
# CMS Admin Views - Why Us Cards
# =============================================================================


class WhyUsCardListView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, ListView):
    """List all 'Why Us' cards."""

    model = WhyUsCard
    template_name = 'admin_panel/cms/whyus/list.html'
    partial_template_name = 'admin_panel/cms/whyus/partials/_list.html'
    context_object_name = 'cards'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Karty "Dlaczego my"'
        return context


class WhyUsCardCreateView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, CreateView):
    """Create new 'Why Us' card."""

    model = WhyUsCard
    form_class = WhyUsCardForm
    template_name = 'admin_panel/cms/whyus/form.html'
    success_url = reverse_lazy('landing:cms-whyus-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Dodaj kartę'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Karta została dodana.')
        return super().form_valid(form)


class WhyUsCardUpdateView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, UpdateView):
    """Edit 'Why Us' card."""

    model = WhyUsCard
    form_class = WhyUsCardForm
    template_name = 'admin_panel/cms/whyus/form.html'
    success_url = reverse_lazy('landing:cms-whyus-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edytuj: {self.object.title}'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Karta została zaktualizowana.')
        return super().form_valid(form)


class WhyUsCardDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    """Delete 'Why Us' card."""

    model = WhyUsCard
    success_url = reverse_lazy('landing:cms-whyus-list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        if request.headers.get('HX-Request'):
            return HttpResponse('')
        messages.success(request, 'Karta została usunięta.')
        return redirect(self.success_url)


class WhyUsCardReorderView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Reorder 'Why Us' cards via AJAX."""

    def post(self, request):
        try:
            data = json.loads(request.body)
            order = data.get('order', [])
            for index, card_id in enumerate(order):
                WhyUsCard.objects.filter(pk=card_id).update(order_index=index)
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


# =============================================================================
# CMS Admin Views - Subjects
# =============================================================================


class SubjectListView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, ListView):
    """List all subjects."""

    model = LandingSubject
    template_name = 'admin_panel/cms/subjects/list.html'
    partial_template_name = 'admin_panel/cms/subjects/partials/_list.html'
    context_object_name = 'subjects'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Przedmioty'
        return context


class SubjectCreateView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, CreateView):
    """Create new subject."""

    model = LandingSubject
    form_class = SubjectForm
    template_name = 'admin_panel/cms/subjects/form.html'
    success_url = reverse_lazy('landing:cms-subject-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Dodaj przedmiot'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Przedmiot został dodany.')
        return super().form_valid(form)


class SubjectUpdateView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, UpdateView):
    """Edit subject."""

    model = LandingSubject
    form_class = SubjectForm
    template_name = 'admin_panel/cms/subjects/form.html'
    success_url = reverse_lazy('landing:cms-subject-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edytuj: {self.object.name}'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Przedmiot został zaktualizowany.')
        return super().form_valid(form)


class SubjectDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    """Delete subject."""

    model = LandingSubject
    success_url = reverse_lazy('landing:cms-subject-list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        if request.headers.get('HX-Request'):
            return HttpResponse('')
        messages.success(request, 'Przedmiot został usunięty.')
        return redirect(self.success_url)


class SubjectReorderView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Reorder subjects via AJAX."""

    def post(self, request):
        try:
            data = json.loads(request.body)
            order = data.get('order', [])
            for index, subject_id in enumerate(order):
                LandingSubject.objects.filter(pk=subject_id).update(order_index=index)
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


# =============================================================================
# CMS Admin Views - Pricing Packages
# =============================================================================


class PricingPackageListView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, ListView):
    """List all pricing packages."""

    model = PricingPackage
    template_name = 'admin_panel/cms/pricing/list.html'
    partial_template_name = 'admin_panel/cms/pricing/partials/_list.html'
    context_object_name = 'packages'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Pakiety cenowe'
        return context


class PricingPackageCreateView(
    LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, CreateView
):
    """Create new pricing package."""

    model = PricingPackage
    form_class = PricingPackageForm
    template_name = 'admin_panel/cms/pricing/form.html'
    success_url = reverse_lazy('landing:cms-pricing-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Dodaj pakiet'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Pakiet został dodany.')
        return super().form_valid(form)


class PricingPackageUpdateView(
    LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, UpdateView
):
    """Edit pricing package."""

    model = PricingPackage
    form_class = PricingPackageForm
    template_name = 'admin_panel/cms/pricing/form.html'
    success_url = reverse_lazy('landing:cms-pricing-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edytuj: {self.object.name}'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Pakiet został zaktualizowany.')
        return super().form_valid(form)


class PricingPackageDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    """Delete pricing package."""

    model = PricingPackage
    success_url = reverse_lazy('landing:cms-pricing-list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        if request.headers.get('HX-Request'):
            return HttpResponse('')
        messages.success(request, 'Pakiet został usunięty.')
        return redirect(self.success_url)


class PricingPackageReorderView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Reorder pricing packages via AJAX."""

    def post(self, request):
        try:
            data = json.loads(request.body)
            order = data.get('order', [])
            for index, package_id in enumerate(order):
                PricingPackage.objects.filter(pk=package_id).update(order_index=index)
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


# =============================================================================
# CMS Admin Views - Education Levels
# =============================================================================


class EducationLevelListView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, ListView):
    """List all education levels."""

    model = EducationLevel
    template_name = 'admin_panel/cms/levels/list.html'
    partial_template_name = 'admin_panel/cms/levels/partials/_list.html'
    context_object_name = 'levels'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Poziomy edukacyjne'
        return context


class EducationLevelCreateView(
    LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, CreateView
):
    """Create new education level."""

    model = EducationLevel
    form_class = EducationLevelForm
    template_name = 'admin_panel/cms/levels/form.html'
    success_url = reverse_lazy('landing:cms-level-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Dodaj poziom'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Poziom został dodany.')
        return super().form_valid(form)


class EducationLevelUpdateView(
    LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, UpdateView
):
    """Edit education level."""

    model = EducationLevel
    form_class = EducationLevelForm
    template_name = 'admin_panel/cms/levels/form.html'
    success_url = reverse_lazy('landing:cms-level-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edytuj: {self.object.name}'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Poziom został zaktualizowany.')
        return super().form_valid(form)


class EducationLevelDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    """Delete education level."""

    model = EducationLevel
    success_url = reverse_lazy('landing:cms-level-list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        if request.headers.get('HX-Request'):
            return HttpResponse('')
        messages.success(request, 'Poziom został usunięty.')
        return redirect(self.success_url)


# =============================================================================
# CMS Admin Views - Lesson Types
# =============================================================================


class LessonTypeListView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, ListView):
    """List all lesson types."""

    model = LessonType
    template_name = 'admin_panel/cms/lessontypes/list.html'
    partial_template_name = 'admin_panel/cms/lessontypes/partials/_list.html'
    context_object_name = 'lesson_types'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Formy zajęć'
        return context


class LessonTypeCreateView(
    LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, CreateView
):
    """Create new lesson type."""

    model = LessonType
    form_class = LessonTypeForm
    template_name = 'admin_panel/cms/lessontypes/form.html'
    success_url = reverse_lazy('landing:cms-lessontype-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Dodaj formę zajęć'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Forma zajęć została dodana.')
        return super().form_valid(form)


class LessonTypeUpdateView(
    LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, UpdateView
):
    """Edit lesson type."""

    model = LessonType
    form_class = LessonTypeForm
    template_name = 'admin_panel/cms/lessontypes/form.html'
    success_url = reverse_lazy('landing:cms-lessontype-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edytuj: {self.object.name}'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Forma zajęć została zaktualizowana.')
        return super().form_valid(form)


class LessonTypeDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    """Delete lesson type."""

    model = LessonType
    success_url = reverse_lazy('landing:cms-lessontype-list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        if request.headers.get('HX-Request'):
            return HttpResponse('')
        messages.success(request, 'Forma zajęć została usunięta.')
        return redirect(self.success_url)
