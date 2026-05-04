# showroom/views.py
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import HttpResponse
from .models import Branch, Seller, Car
from .forms  import CarForm, SellerForm

# Authentication
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic.edit import CreateView
from .forms import RegisterForm

from django.contrib.auth.mixins import LoginRequiredMixin

class RegisterView(CreateView):
    form_class    = RegisterForm
    template_name = 'showroom/auth/register.html'
    success_url   = reverse_lazy('branch-list')

    def form_valid(self, form):
        # Save the user, then log them in immediately
        response = super().form_valid(form)
        login(self.request, self.object)
        return response

# ── Branches ───────────────────────────────────────────────────────────────

class BranchListView(LoginRequiredMixin, ListView):
    model               = Branch
    template_name       = 'showroom/branch_list.html'
    context_object_name = 'branches'


class BranchDetailView(LoginRequiredMixin, DetailView):
    model               = Branch
    template_name       = 'showroom/branch_detail.html'
    context_object_name = 'branch'

    # 🔑 KEY CONCEPT: add extra context from related models
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # branch.cars uses the related_name we set on Car.branch
        ctx['cars']    = self.object.cars.select_related('seller')
        # branch.sellers uses the ManyToManyField related_name
        ctx['sellers'] = self.object.sellers.filter(is_active=True)
        return ctx
    
# ── Cars ───────────────────────────────────────────────────────────────────

class CarListView(LoginRequiredMixin, ListView):
    model               = Car
    template_name       = 'showroom/car_list.html'
    context_object_name = 'cars'
    # Eager-load branch and seller to avoid N+1 queries
    queryset            = Car.objects.select_related('branch', 'seller')


class CarCreateView(LoginRequiredMixin, CreateView):
    model         = Car
    form_class    = CarForm
    template_name = 'showroom/car_form.html'
    success_url   = reverse_lazy('car-list')


class CarUpdateView(LoginRequiredMixin, UpdateView):
    model         = Car
    form_class    = CarForm
    template_name = 'showroom/car_form.html'
    success_url   = reverse_lazy('car-list')


class CarDeleteView(LoginRequiredMixin, DeleteView):
    model         = Car
    template_name = 'showroom/car_confirm_delete.html'
    success_url   = reverse_lazy('car-list')


# ── HTMX: live search (returns a partial HTML fragment) ────────────────────

class CarSearchView(LoginRequiredMixin, ListView):
    model               = Car
    # Returns a partial template, not a full page
    template_name       = 'showroom/partials/car_table.html'
    context_object_name = 'cars'

    def get_queryset(self):
        q = self.request.GET.get('q', '')
        qs = Car.objects.select_related('branch', 'seller')
        if q:
            qs = qs.filter(
                Q(make__icontains=q)  |
                Q(model__icontains=q) |
                Q(branch__name__icontains=q)
            )
        return qs

class CarInlineDeleteView(LoginRequiredMixin, DeleteView):
    model = Car

    def form_valid(self, form):
        self.object.delete()
        return HttpResponse('')
      
# ── Sellers ────────────────────────────────────────────────────────────────

class SellerListView(LoginRequiredMixin, ListView):
    model               = Seller
    template_name       = 'showroom/seller_list.html'
    context_object_name = 'sellers'
    queryset            = Seller.objects.prefetch_related('branches')


class SellerDetailView(LoginRequiredMixin, DetailView):
    model               = Seller
    template_name       = 'showroom/seller_detail.html'
    context_object_name = 'seller'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['cars'] = self.object.cars.select_related('branch')
        return ctx


class SellerCreateView(LoginRequiredMixin, CreateView):
    model         = Seller
    form_class    = SellerForm
    template_name = 'showroom/seller_form.html'
    success_url   = reverse_lazy('seller-list')


class SellerUpdateView(LoginRequiredMixin, UpdateView):
    model         = Seller
    form_class    = SellerForm
    template_name = 'showroom/seller_form.html'
    success_url   = reverse_lazy('seller-list')


class SellerDeleteView(LoginRequiredMixin, DeleteView):
    model         = Seller
    template_name = 'showroom/seller_confirm_delete.html'
    success_url   = reverse_lazy('seller-list')


# ── HTMX: live seller search (returns a partial HTML fragment) ─────────────

class SellerSearchView(LoginRequiredMixin, ListView):
    model               = Seller
    # Returns a partial template, not a full page
    template_name       = 'showroom/partials/seller_cards.html'
    context_object_name = 'sellers'

    def get_queryset(self):
        q  = self.request.GET.get('q', '')
        qs = Seller.objects.prefetch_related('branches')
        if q:
            qs = qs.filter(
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q)  |
                Q(branches__name__icontains=q)
            ).distinct()  # distinct() needed because M2M joins can duplicate rows
        return qs


# ── HTMX: inline delete returns empty 200 so HTMX removes the row ──────────

class CarInlineDeleteView(DeleteView):
    model = Car

    def form_valid(self, form):
        self.object.delete()
        # Return empty response — HTMX replaces the deleted row with nothing
        return HttpResponse('')