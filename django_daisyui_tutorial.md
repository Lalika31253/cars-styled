# Django + HTMX + DaisyUI
## Car Dealership App with Tailwind CSS, Auth Modals & Toast Notifications

---

## Table of Contents

1. [What Changes From the Plain HTML Version](#1-what-changes-from-the-plain-html-version)
2. [Setup — Adding Tailwind CSS & DaisyUI](#2-setup--adding-tailwind-css--daisyui)
3. [Django Messages + Toast System](#3-django-messages--toast-system)
4. [Views — Adding Messages to Every CRUD Action](#4-views--adding-messages-to-every-crud-action)
5. [base.html — Navbar, Footer, Toast & Modal Shell](#5-basehtml--navbar-footer-toast--modal-shell)
6. [Authentication Modal](#6-authentication-modal)
7. [branch_list.html](#7-branch_listhtml)
8. [branch_detail.html](#8-branch_detailhtml)
9. [car_list.html](#9-car_listhtml)
10. [partials/car_table.html](#10-partialscar_tablehtml)
11. [car_form.html](#11-car_formhtml)
12. [car_confirm_delete.html](#12-car_confirm_deletehtml)
13. [seller_list.html](#13-seller_listhtml)
14. [partials/seller_cards.html](#14-partialsseller_cardshtml)
15. [seller_detail.html](#15-seller_detailhtml)
16. [seller_form.html](#16-seller_formhtml)
17. [seller_confirm_delete.html](#17-seller_confirm_deletehtml)
18. [Template File Structure](#18-template-file-structure)

---

## 1. What Changes From the Plain HTML Version

The models, views, URLs, and forms stay **exactly the same** as the previous tutorial. The only things we replace are:

| Was | Now |
|---|---|
| No CSS | Tailwind CSS via CDN |
| Plain `<table border="1">` | DaisyUI `table`, `card`, `badge` components |
| Plain `<nav>` | DaisyUI `navbar` with dropdown menus |
| No footer | DaisyUI `footer` |
| Plain login/register pages | DaisyUI `modal` triggered from the navbar |
| No feedback after actions | Django `messages` rendered as DaisyUI `toast` + `alert` |
| Plain `<input>` for search | DaisyUI `input` with `join` group |
| Plain `<button>` for delete | DaisyUI `btn btn-error` with `modal` confirmation |

Everything else — HTMX attributes, CBVs, `LoginRequiredMixin`, seed command — carries over unchanged.

---

## 2. Setup — Adding Tailwind CSS & DaisyUI

We load both libraries from a CDN. No build step, no `npm`, no config file needed for a tutorial.

Add these two lines inside `<head>` in your `base.html` (shown in full in section 5):

```html
<!-- Tailwind CSS -->
<script src="https://cdn.tailwindcss.com"></script>

<!-- DaisyUI component styles (must come after Tailwind) -->
<link href="https://cdn.jsdelivr.net/npm/daisyui@4.12.10/dist/full.min.css" rel="stylesheet">
```

> 💡 The CDN version of Tailwind scans your HTML at runtime and injects only the classes you use. It is perfect for development and small projects. For production use the PostCSS build pipeline instead.

### DaisyUI theme

DaisyUI ships with 35 colour themes. We use `"night"` (a dark theme). Set it on the `<html>` tag:

```html
<html lang="en" data-theme="night">
```

To try other themes, swap `"night"` for any of: `light`, `dark`, `cupcake`, `business`, `corporate`, `dracula`, `forest`, `aqua`, `luxury`.

---

## 3. Django Messages + Toast System

### How Django messages work

Django's messages framework lets a view attach a one-time notification to the request. The message survives a redirect and is available exactly once in the next template render.

```python
# In any view:
from django.contrib import messages

messages.success(request, "Car added successfully.")   # green
messages.info(request,    "Viewing North End branch.") # blue
messages.warning(request, "Car updated.")              # yellow
messages.error(request,   "Car deleted.")              # red
```

### Mapping message levels to DaisyUI alert colours

| Django level | `messages.XXX()` | DaisyUI class | Colour |
|---|---|---|---|
| `SUCCESS` | `messages.success` | `alert-success` | Green |
| `INFO` | `messages.info` | `alert-info` | Blue |
| `WARNING` | `messages.warning` | `alert-warning` | Yellow |
| `ERROR` | `messages.error` | `alert-error` | Red |

### The toast snippet (goes in base.html)

```html
<!-- Toast container — fixed bottom-right corner -->
{% if messages %}
<div class="toast toast-end toast-bottom z-50">
  {% for message in messages %}
    <div class="alert
      {% if message.tags == 'success' %}alert-success
      {% elif message.tags == 'error' %}alert-error
      {% elif message.tags == 'warning' %}alert-warning
      {% else %}alert-info{% endif %}
      shadow-lg">
      <span>{{ message }}</span>
    </div>
  {% endfor %}
</div>
{% endif %}
```

> 💡 DaisyUI's `toast` class positions the container. `toast-end toast-bottom` puts it in the bottom-right corner. Each child `alert` is a separate notification card.

### Auto-dismiss with a tiny script

DaisyUI toasts do not disappear on their own. Add this script once in `base.html` to fade them out after 3 seconds:

```html
<script>
  document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
      document.querySelectorAll('.toast .alert').forEach(el => {
        el.style.transition = 'opacity 0.5s';
        el.style.opacity = '0';
        setTimeout(() => el.remove(), 500);
      });
    }, 3000);
  });
</script>
```

---

## 4. Views — Adding Messages to Every CRUD Action

We override `form_valid` and `delete` methods to attach a message before every redirect. The colour convention is:

- 🟢 **Create** → `messages.success`
- 🔵 **Read** (detail view) → `messages.info`
- 🟡 **Update** → `messages.warning`
- 🔴 **Delete** → `messages.error`

Replace the views section of `showroom/views.py` with the full version below:

```python
# showroom/views.py
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Branch, Seller, Car
from .forms  import CarForm, SellerForm, RegisterForm


# ── Branches ───────────────────────────────────────────────────────────────

class BranchListView(LoginRequiredMixin, ListView):
    model               = Branch
    template_name       = 'showroom/branch_list.html'
    context_object_name = 'branches'


class BranchDetailView(LoginRequiredMixin, DetailView):
    model               = Branch
    template_name       = 'showroom/branch_detail.html'
    context_object_name = 'branch'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['cars']    = self.object.cars.select_related('seller')
        ctx['sellers'] = self.object.sellers.filter(is_active=True)
        # 🔵 info toast on every detail view load
        messages.info(self.request, f'Viewing {self.object.name} branch.')
        return ctx


# ── Cars ───────────────────────────────────────────────────────────────────

class CarListView(LoginRequiredMixin, ListView):
    model               = Car
    template_name       = 'showroom/car_list.html'
    context_object_name = 'cars'
    queryset            = Car.objects.select_related('branch', 'seller')


class CarCreateView(LoginRequiredMixin, CreateView):
    model         = Car
    form_class    = CarForm
    template_name = 'showroom/car_form.html'
    success_url   = reverse_lazy('car-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        # 🟢 success toast
        messages.success(self.request,
            f'{self.object} has been added to the inventory.')
        return response


class CarUpdateView(LoginRequiredMixin, UpdateView):
    model         = Car
    form_class    = CarForm
    template_name = 'showroom/car_form.html'
    success_url   = reverse_lazy('car-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        # 🟡 warning toast
        messages.warning(self.request,
            f'{self.object} has been updated.')
        return response


class CarDeleteView(LoginRequiredMixin, DeleteView):
    model         = Car
    template_name = 'showroom/car_confirm_delete.html'
    success_url   = reverse_lazy('car-list')

    def form_valid(self, form):
        name = str(self.object)
        response = super().form_valid(form)
        # 🔴 error toast
        messages.error(self.request, f'{name} has been deleted.')
        return response


class CarSearchView(LoginRequiredMixin, ListView):
    model               = Car
    template_name       = 'showroom/partials/car_table.html'
    context_object_name = 'cars'

    def get_queryset(self):
        q  = self.request.GET.get('q', '')
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
        name = str(self.object)
        self.object.delete()
        messages.error(self.request, f'{name} has been deleted.')
        # Return the toast HTML directly so HTMX can inject it
        toast_html = f'''
        <tr id="car-{self.object.pk}"></tr>
        <div hx-swap-oob="beforeend:#toast-container">
          <div class="alert alert-error shadow-lg">
            <span>{name} has been deleted.</span>
          </div>
        </div>
        '''
        return HttpResponse(toast_html)


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
        messages.info(self.request, f'Viewing seller {self.object}.')
        return ctx


class SellerCreateView(LoginRequiredMixin, CreateView):
    model         = Seller
    form_class    = SellerForm
    template_name = 'showroom/seller_form.html'
    success_url   = reverse_lazy('seller-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'{self.object} has been added.')
        return response


class SellerUpdateView(LoginRequiredMixin, UpdateView):
    model         = Seller
    form_class    = SellerForm
    template_name = 'showroom/seller_form.html'
    success_url   = reverse_lazy('seller-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.warning(self.request, f'{self.object} has been updated.')
        return response


class SellerDeleteView(LoginRequiredMixin, DeleteView):
    model         = Seller
    template_name = 'showroom/seller_confirm_delete.html'
    success_url   = reverse_lazy('seller-list')

    def form_valid(self, form):
        name = str(self.object)
        response = super().form_valid(form)
        messages.error(self.request, f'{name} has been deleted.')
        return response


class SellerSearchView(LoginRequiredMixin, ListView):
    model               = Seller
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
            ).distinct()
        return qs


# ── Auth ───────────────────────────────────────────────────────────────────

class RegisterView(CreateView):
    form_class    = RegisterForm
    template_name = 'showroom/auth/register.html'
    success_url   = reverse_lazy('branch-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request,
            f'Welcome, {self.object.username}! Your account has been created.')
        return response
```

> ⚠️ `form_valid` on `DeleteView` receives a form argument in Django 4+. Always capture `str(self.object)` **before** calling `super().form_valid(form)` — after deletion `self.object` no longer exists in the database.

---

## 5. base.html — Navbar, Footer, Toast & Modal Shell

This is the most important template. Every other template extends it.

```html
<!DOCTYPE html>
<html lang="en" data-theme="night">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}AutoHub{% endblock %} — AutoHub Dealerships</title>

  <!-- Tailwind CSS (CDN) -->
  <script src="https://cdn.tailwindcss.com"></script>

  <!-- DaisyUI component styles -->
  <link href="https://cdn.jsdelivr.net/npm/daisyui@4.12.10/dist/full.min.css"
        rel="stylesheet">

  <!-- HTMX -->
  <script src="https://unpkg.com/htmx.org@1.9.10"></script>
</head>

<!-- hx-headers sends the Django CSRF token with every HTMX request -->
<body class="min-h-screen flex flex-col bg-base-100"
      hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>


  <!-- ═══════════════════════════════════════════════
       NAVBAR
  ═══════════════════════════════════════════════ -->
  <div class="navbar bg-base-300 shadow-lg px-4">

    <!-- Brand / Logo -->
    <div class="navbar-start">
      <a href="{% url 'branch-list' %}"
         class="btn btn-ghost text-xl font-bold tracking-wide">
        🚗 AutoHub
      </a>
    </div>

    <!-- Desktop links (hidden on mobile) -->
    <div class="navbar-center hidden lg:flex gap-1">
      {% if user.is_authenticated %}
        <a href="{% url 'branch-list' %}" class="btn btn-ghost btn-sm">Branches</a>
        <a href="{% url 'car-list' %}"    class="btn btn-ghost btn-sm">Cars</a>
        <a href="{% url 'seller-list' %}" class="btn btn-ghost btn-sm">Sellers</a>
      {% endif %}
    </div>

    <!-- Right side -->
    <div class="navbar-end gap-2">
      {% if user.is_authenticated %}
        <!-- Mobile hamburger -->
        <div class="dropdown dropdown-end lg:hidden">
          <label tabindex="0" class="btn btn-ghost btn-circle">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M4 6h16M4 12h16M4 18h16"/>
            </svg>
          </label>
          <ul tabindex="0"
              class="menu menu-sm dropdown-content bg-base-200 rounded-box z-50
                     mt-3 w-52 p-2 shadow">
            <li><a href="{% url 'branch-list' %}">Branches</a></li>
            <li><a href="{% url 'car-list' %}">Cars</a></li>
            <li><a href="{% url 'seller-list' %}">Sellers</a></li>
          </ul>
        </div>

        <!-- User dropdown -->
        <div class="dropdown dropdown-end">
          <label tabindex="0" class="btn btn-ghost btn-circle avatar placeholder">
            <div class="bg-primary text-primary-content rounded-full w-9">
              <span class="text-sm font-bold">
                {{ user.username|first|upper }}
              </span>
            </div>
          </label>
          <ul tabindex="0"
              class="menu menu-sm dropdown-content bg-base-200 rounded-box z-50
                     mt-3 w-48 p-2 shadow">
            <li class="menu-title px-4 py-2 text-xs opacity-60">
              {{ user.username }}
            </li>
            <li>
              <form method="post" action="{% url 'logout' %}">
                {% csrf_token %}
                <button type="submit" class="w-full text-left text-error">
                  Logout
                </button>
              </form>
            </li>
          </ul>
        </div>

      {% else %}
        <!-- Login / Register buttons → open modal -->
        <button onclick="auth_modal.showModal()"
                class="btn btn-primary btn-sm">
          Login / Register
        </button>
      {% endif %}
    </div>
  </div><!-- /navbar -->


  <!-- ═══════════════════════════════════════════════
       MAIN CONTENT
  ═══════════════════════════════════════════════ -->
  <main class="flex-1 container mx-auto px-4 py-8 max-w-6xl">
    {% block content %}{% endblock %}
  </main>


  <!-- ═══════════════════════════════════════════════
       FOOTER
  ═══════════════════════════════════════════════ -->
  <footer class="footer footer-center bg-base-300 text-base-content p-6 mt-auto">
    <aside>
      <p class="font-bold text-lg">🚗 AutoHub Dealerships</p>
      <p class="text-sm opacity-60">
        4 branches across the city &mdash; Toronto, Mississauga, Scarborough
      </p>
      <p class="text-xs opacity-40 mt-1">
        &copy; {% now "Y" %} AutoHub. Built with Django + HTMX + DaisyUI.
      </p>
    </aside>
  </footer>


  <!-- ═══════════════════════════════════════════════
       TOAST NOTIFICATIONS
       id="toast-container" lets HTMX OOB swaps inject
       toasts from inline-delete responses
  ═══════════════════════════════════════════════ -->
  {% if messages %}
  <div id="toast-container" class="toast toast-end toast-bottom z-50">
    {% for message in messages %}
      <div class="alert shadow-lg
        {% if message.tags == 'success' %}alert-success
        {% elif message.tags == 'error' %}alert-error
        {% elif message.tags == 'warning' %}alert-warning
        {% else %}alert-info{% endif %}">
        <span>{{ message }}</span>
      </div>
    {% endfor %}
  </div>
  {% else %}
  <!-- Empty container so HTMX OOB swaps always have a target -->
  <div id="toast-container" class="toast toast-end toast-bottom z-50"></div>
  {% endif %}


  <!-- ═══════════════════════════════════════════════
       AUTH MODAL (Login + Register tabs)
       See section 6 for the full template explanation
  ═══════════════════════════════════════════════ -->
  {% include 'showroom/auth/modal.html' %}


  <!-- Auto-dismiss toasts after 3 seconds -->
  <script>
    document.addEventListener('DOMContentLoaded', () => {
      setTimeout(() => {
        document.querySelectorAll('#toast-container .alert').forEach(el => {
          el.style.transition = 'opacity 0.5s ease';
          el.style.opacity = '0';
          setTimeout(() => el.remove(), 500);
        });
      }, 3000);
    });
  </script>

</body>
</html>
```

---

## 6. Authentication Modal

The login and register forms live inside a DaisyUI `<dialog>` modal with two tabs — so the user never leaves the current page to authenticate.

Create `showroom/templates/showroom/auth/modal.html`:

```html
<!-- DaisyUI dialog modal — id must match the onclick in the navbar -->
<dialog id="auth_modal" class="modal modal-bottom sm:modal-middle">
  <div class="modal-box w-full max-w-md">

    <!-- Close button -->
    <form method="dialog">
      <button class="btn btn-sm btn-circle btn-ghost absolute right-3 top-3">
        ✕
      </button>
    </form>

    <h2 class="text-2xl font-bold mb-6 text-center">Welcome to AutoHub</h2>

    <!-- Tab selector -->
    <div role="tablist" class="tabs tabs-bordered mb-6">
      <input type="radio" name="auth_tabs" role="tab"
             class="tab" aria-label="Login" checked>
      <div role="tabpanel" class="tab-content pt-4">

        <!-- ── LOGIN FORM ── -->
        <form method="post" action="{% url 'login' %}">
          {% csrf_token %}
          <!-- 'next' ensures redirect back to the current page after login -->
          <input type="hidden" name="next"
                 value="{{ request.path }}">

          <div class="form-control mb-4">
            <label class="label">
              <span class="label-text">Username</span>
            </label>
            <input type="text" name="username" required
                   placeholder="your username"
                   class="input input-bordered w-full">
          </div>

          <div class="form-control mb-6">
            <label class="label">
              <span class="label-text">Password</span>
            </label>
            <input type="password" name="password" required
                   placeholder="••••••••"
                   class="input input-bordered w-full">
          </div>

          <button type="submit" class="btn btn-primary w-full">
            Log in
          </button>
        </form>

      </div><!-- /login tab panel -->

      <input type="radio" name="auth_tabs" role="tab"
             class="tab" aria-label="Register">
      <div role="tabpanel" class="tab-content pt-4">

        <!-- ── REGISTER FORM ── -->
        <form method="post" action="{% url 'register' %}">
          {% csrf_token %}

          <div class="form-control mb-4">
            <label class="label">
              <span class="label-text">Username</span>
            </label>
            <input type="text" name="username" required
                   placeholder="choose a username"
                   class="input input-bordered w-full">
          </div>

          <div class="form-control mb-4">
            <label class="label">
              <span class="label-text">Email <span class="opacity-50">(optional)</span></span>
            </label>
            <input type="email" name="email"
                   placeholder="you@example.com"
                   class="input input-bordered w-full">
          </div>

          <div class="form-control mb-4">
            <label class="label">
              <span class="label-text">Password</span>
            </label>
            <input type="password" name="password1" required
                   placeholder="••••••••"
                   class="input input-bordered w-full">
          </div>

          <div class="form-control mb-6">
            <label class="label">
              <span class="label-text">Confirm Password</span>
            </label>
            <input type="password" name="password2" required
                   placeholder="••••••••"
                   class="input input-bordered w-full">
          </div>

          <button type="submit" class="btn btn-success w-full">
            Create Account
          </button>
        </form>

      </div><!-- /register tab panel -->
    </div><!-- /tabs -->

  </div>

  <!-- Click outside to close -->
  <form method="dialog" class="modal-backdrop">
    <button>close</button>
  </form>
</dialog>
```

> 💡 The modal uses native HTML `<dialog>` under the hood, which DaisyUI styles. `auth_modal.showModal()` (called from the navbar button's `onclick`) is a browser built-in — no JavaScript framework needed.

### Showing form validation errors in the modal

When login or registration fails, Django redirects back with form errors. To re-open the modal automatically and show the errors, add this snippet to `base.html` just before the closing `</body>`:

```html
{% if form and form.errors %}
<script>
  // Re-open the modal if a form was submitted with errors
  document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('auth_modal');
    if (modal) modal.showModal();
  });
</script>
{% endif %}
```

For the full error-display version, the auth views (`LoginView`, `RegisterView`) should pass the form back to `base.html` context when there are errors. The simplest way is to override the login and register views to render `base.html` with the form in context — but for a beginner tutorial, a standalone error page (the current approach) is easier to follow.

---

## 7. branch_list.html

```html
{% extends 'showroom/base.html' %}
{% block title %}Branches{% endblock %}

{% block content %}
<div class="flex items-center justify-between mb-8">
  <div>
    <h1 class="text-3xl font-bold">Our Branches</h1>
    <p class="text-base-content/60 mt-1">
      {{ branches|length }} location{{ branches|length|pluralize }} across the city
    </p>
  </div>
</div>

<!-- Branch cards grid -->
<div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-6">
  {% for branch in branches %}
  <div class="card bg-base-200 shadow-md hover:shadow-xl
              transition-shadow duration-200">
    <div class="card-body">

      <!-- Branch name + city badge -->
      <h2 class="card-title text-lg">
        {{ branch.name }}
        <div class="badge badge-primary badge-outline text-xs">
          {{ branch.city }}
        </div>
      </h2>

      <!-- Opened date -->
      <p class="text-sm text-base-content/60">
        Open since {{ branch.opened_date|date:"M Y" }}
      </p>

      <!-- Notes (if any) -->
      {% if branch.notes %}
      <p class="text-sm mt-2 line-clamp-2">{{ branch.notes }}</p>
      {% endif %}

      <!-- Stats row -->
      <div class="flex gap-4 mt-3 text-sm">
        <span class="badge badge-ghost">
          🚗 {{ branch.cars.count }} cars
        </span>
        <span class="badge badge-ghost">
          👤 {{ branch.sellers.count }} sellers
        </span>
      </div>

      <!-- Action -->
      <div class="card-actions justify-end mt-4">
        <a href="{% url 'branch-detail' branch.pk %}"
           class="btn btn-primary btn-sm">
          View Branch →
        </a>
      </div>

    </div>
  </div>
  {% empty %}
  <div class="col-span-4">
    <div class="alert alert-info">
      <span>No branches found. Run <code>python manage.py seed</code> to add data.</span>
    </div>
  </div>
  {% endfor %}
</div>
{% endblock %}
```

---

## 8. branch_detail.html

```html
{% extends 'showroom/base.html' %}
{% block title %}{{ branch.name }}{% endblock %}

{% block content %}

<!-- Breadcrumb -->
<div class="breadcrumbs text-sm mb-6">
  <ul>
    <li><a href="{% url 'branch-list' %}">Branches</a></li>
    <li>{{ branch.name }}</li>
  </ul>
</div>

<!-- Header card -->
<div class="card bg-base-200 shadow mb-8">
  <div class="card-body">
    <div class="flex flex-wrap items-start justify-between gap-4">
      <div>
        <h1 class="text-3xl font-bold">{{ branch.name }}</h1>
        <div class="flex flex-wrap gap-2 mt-2">
          <div class="badge badge-primary">{{ branch.city }}</div>
          <div class="badge badge-ghost">
            Open since {{ branch.opened_date|date:"F j, Y" }}
          </div>
        </div>
        {% if branch.notes %}
        <p class="mt-3 text-base-content/70 max-w-lg">{{ branch.notes }}</p>
        {% endif %}
      </div>
      <div class="stats stats-vertical lg:stats-horizontal shadow">
        <div class="stat">
          <div class="stat-title">Cars</div>
          <div class="stat-value text-primary">{{ cars|length }}</div>
        </div>
        <div class="stat">
          <div class="stat-title">Sellers</div>
          <div class="stat-value text-secondary">{{ sellers|length }}</div>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- Two-column layout: sellers left, cars right -->
<div class="grid grid-cols-1 lg:grid-cols-3 gap-8">

  <!-- Sellers column -->
  <div>
    <h2 class="text-xl font-bold mb-4">Active Sellers</h2>
    <div class="flex flex-col gap-3">
      {% for seller in sellers %}
      <div class="card bg-base-200 shadow-sm">
        <div class="card-body p-4 flex-row items-center gap-3">
          <div class="avatar placeholder">
            <div class="bg-secondary text-secondary-content
                        rounded-full w-10">
              <span>{{ seller.first_name|first }}{{ seller.last_name|first }}</span>
            </div>
          </div>
          <div class="flex-1">
            <p class="font-semibold text-sm">{{ seller }}</p>
            <div class="badge badge-success badge-sm">Active</div>
          </div>
          <a href="{% url 'seller-detail' seller.pk %}"
             class="btn btn-ghost btn-xs">→</a>
        </div>
      </div>
      {% empty %}
      <p class="text-base-content/50 text-sm">No active sellers.</p>
      {% endfor %}
    </div>
  </div>

  <!-- Cars column (spans 2 cols) -->
  <div class="lg:col-span-2">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-xl font-bold">Cars at this Branch</h2>
      <a href="{% url 'car-create' %}" class="btn btn-primary btn-sm">
        + Add Car
      </a>
    </div>

    <div class="overflow-x-auto rounded-lg shadow">
      <table class="table table-zebra w-full">
        <thead class="bg-base-300">
          <tr>
            <th>Car</th>
            <th>Year</th>
            <th>Price</th>
            <th>Trans.</th>
            <th>Seller</th>
            <th class="text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {% for car in cars %}
          <tr id="car-{{ car.pk }}" class="hover">
            <td class="font-medium">{{ car.make }} {{ car.model }}</td>
            <td>{{ car.year }}</td>
            <td class="font-semibold text-success">
              ${{ car.price|floatformat:0 }}
            </td>
            <td>
              <div class="badge badge-ghost badge-sm">
                {{ car.get_transmission_display }}
              </div>
            </td>
            <td class="text-sm">{{ car.seller }}</td>
            <td class="text-right">
              <div class="join">
                <a href="{% url 'car-update' car.pk %}"
                   class="btn btn-warning btn-xs join-item">Edit</a>

                <!-- HTMX inline delete with DaisyUI confirm modal trigger -->
                <button
                  hx-delete="{% url 'car-inline-delete' car.pk %}"
                  hx-target="#car-{{ car.pk }}"
                  hx-swap="outerHTML"
                  hx-confirm="Permanently delete {{ car }}?"
                  class="btn btn-error btn-xs join-item">
                  Delete
                </button>
              </div>
            </td>
          </tr>
          {% empty %}
          <tr>
            <td colspan="6" class="text-center text-base-content/50 py-8">
              No cars at this branch yet.
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

## 9. car_list.html

```html
{% extends 'showroom/base.html' %}
{% block title %}Cars{% endblock %}

{% block content %}
<div class="flex flex-wrap items-center justify-between gap-4 mb-8">
  <div>
    <h1 class="text-3xl font-bold">Car Inventory</h1>
    <p class="text-base-content/60 mt-1">All vehicles across all branches</p>
  </div>
  <a href="{% url 'car-create' %}" class="btn btn-primary">
    + Add Car
  </a>
</div>

<!-- Search bar -->
<!--
  hx-get      → calls CarSearchView which returns the partial
  hx-trigger  → fires on keyup with 300ms debounce
  hx-target   → replaces the content of #car-results
  hx-swap     → replaces innerHTML of the target div
-->
<div class="form-control mb-6">
  <div class="join w-full max-w-md">
    <input
      type="search"
      name="q"
      placeholder="Search by make, model or branch…"
      hx-get="{% url 'car-search' %}"
      hx-trigger="keyup changed delay:300ms"
      hx-target="#car-results"
      hx-swap="innerHTML"
      class="input input-bordered join-item w-full"
    >
    <button class="btn join-item btn-neutral">
      🔍
    </button>
  </div>
</div>

<!-- Results container (initial render + HTMX swap target) -->
<div id="car-results">
  {% include 'showroom/partials/car_table.html' %}
</div>
{% endblock %}
```

---

## 10. partials/car_table.html

This partial has **no `{% extends %}`**. It is a fragment returned by `CarSearchView` and also used by `{% include %}` in `car_list.html` for the initial render.

```html
{# Fragment only — no {% extends %} #}
{% if cars %}
<div class="overflow-x-auto rounded-lg shadow">
  <table class="table table-zebra w-full">
    <thead class="bg-base-300">
      <tr>
        <th>Car</th>
        <th>Year</th>
        <th>Price</th>
        <th>Transmission</th>
        <th>Branch</th>
        <th>Seller</th>
        <th class="text-right">Actions</th>
      </tr>
    </thead>
    <tbody>
      {% for car in cars %}
      <tr id="car-{{ car.pk }}" class="hover">
        <td class="font-semibold">{{ car.make }} {{ car.model }}</td>
        <td>{{ car.year }}</td>
        <td class="font-semibold text-success">
          ${{ car.price|floatformat:0 }}
        </td>
        <td>
          <div class="badge badge-outline badge-sm">
            {{ car.get_transmission_display }}
          </div>
        </td>
        <td>
          <a href="{% url 'branch-detail' car.branch.pk %}"
             class="link link-hover link-primary text-sm">
            {{ car.branch.name }}
          </a>
        </td>
        <td class="text-sm">{{ car.seller }}</td>
        <td class="text-right">
          <div class="join">
            <a href="{% url 'car-update' car.pk %}"
               class="btn btn-warning btn-xs join-item">Edit</a>
            <button
              hx-delete="{% url 'car-inline-delete' car.pk %}"
              hx-target="#car-{{ car.pk }}"
              hx-swap="outerHTML"
              hx-confirm="Permanently delete {{ car }}?"
              class="btn btn-error btn-xs join-item">
              Delete
            </button>
          </div>
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>
{% else %}
<div class="alert alert-info mt-4">
  <span>No cars found matching your search.</span>
</div>
{% endif %}
```

---

## 11. car_form.html

This template handles both **create** and **update**. Django sets `object` only for update, so we use it to adjust the title and button label.

```html
{% extends 'showroom/base.html' %}
{% block title %}{% if object %}Edit Car{% else %}Add Car{% endif %}{% endblock %}

{% block content %}

<!-- Breadcrumb -->
<div class="breadcrumbs text-sm mb-6">
  <ul>
    <li><a href="{% url 'car-list' %}">Cars</a></li>
    <li>{% if object %}Edit {{ object }}{% else %}Add Car{% endif %}</li>
  </ul>
</div>

<div class="max-w-2xl mx-auto">
  <div class="card bg-base-200 shadow-lg">
    <div class="card-body">

      <h1 class="card-title text-2xl mb-4">
        {% if object %}
          ✏️ Edit {{ object }}
        {% else %}
          🚗 Add a New Car
        {% endif %}
      </h1>

      <form method="post" novalidate>
        {% csrf_token %}

        <!-- Make -->
        <div class="form-control mb-4">
          <label class="label" for="id_make">
            <span class="label-text font-medium">Make</span>
          </label>
          <input type="text" name="make" id="id_make"
                 value="{{ form.make.value|default:'' }}"
                 placeholder="e.g. Toyota"
                 class="input input-bordered w-full
                   {% if form.make.errors %}input-error{% endif %}">
          {% for error in form.make.errors %}
            <label class="label">
              <span class="label-text-alt text-error">{{ error }}</span>
            </label>
          {% endfor %}
        </div>

        <!-- Model -->
        <div class="form-control mb-4">
          <label class="label" for="id_model">
            <span class="label-text font-medium">Model</span>
          </label>
          <input type="text" name="model" id="id_model"
                 value="{{ form.model.value|default:'' }}"
                 placeholder="e.g. Camry"
                 class="input input-bordered w-full
                   {% if form.model.errors %}input-error{% endif %}">
          {% for error in form.model.errors %}
            <label class="label">
              <span class="label-text-alt text-error">{{ error }}</span>
            </label>
          {% endfor %}
        </div>

        <!-- Year + Price row -->
        <div class="grid grid-cols-2 gap-4 mb-4">
          <div class="form-control">
            <label class="label" for="id_year">
              <span class="label-text font-medium">Year</span>
            </label>
            <input type="number" name="year" id="id_year"
                   value="{{ form.year.value|default:'' }}"
                   placeholder="2023"
                   class="input input-bordered w-full
                     {% if form.year.errors %}input-error{% endif %}">
            {% for error in form.year.errors %}
              <label class="label">
                <span class="label-text-alt text-error">{{ error }}</span>
              </label>
            {% endfor %}
          </div>

          <div class="form-control">
            <label class="label" for="id_price">
              <span class="label-text font-medium">Price ($)</span>
            </label>
            <input type="number" name="price" id="id_price"
                   step="0.01"
                   value="{{ form.price.value|default:'' }}"
                   placeholder="29999.99"
                   class="input input-bordered w-full
                     {% if form.price.errors %}input-error{% endif %}">
            {% for error in form.price.errors %}
              <label class="label">
                <span class="label-text-alt text-error">{{ error }}</span>
              </label>
            {% endfor %}
          </div>
        </div>

        <!-- Transmission -->
        <div class="form-control mb-4">
          <label class="label" for="id_transmission">
            <span class="label-text font-medium">Transmission</span>
          </label>
          <select name="transmission" id="id_transmission"
                  class="select select-bordered w-full">
            {% for value, label in form.fields.transmission.choices %}
              <option value="{{ value }}"
                {% if form.transmission.value == value %}selected{% endif %}>
                {{ label }}
              </option>
            {% endfor %}
          </select>
        </div>

        <!-- Branch -->
        <div class="form-control mb-4">
          <label class="label" for="id_branch">
            <span class="label-text font-medium">Branch</span>
          </label>
          <select name="branch" id="id_branch"
                  class="select select-bordered w-full
                    {% if form.branch.errors %}select-error{% endif %}">
            <option value="">— select a branch —</option>
            {% for value, label in form.fields.branch.choices %}
              {% if value %}
              <option value="{{ value }}"
                {% if form.branch.value|stringformat:"s" == value|stringformat:"s" %}
                  selected{% endif %}>
                {{ label }}
              </option>
              {% endif %}
            {% endfor %}
          </select>
          {% for error in form.branch.errors %}
            <label class="label">
              <span class="label-text-alt text-error">{{ error }}</span>
            </label>
          {% endfor %}
        </div>

        <!-- Seller -->
        <div class="form-control mb-6">
          <label class="label" for="id_seller">
            <span class="label-text font-medium">Seller</span>
          </label>
          <select name="seller" id="id_seller"
                  class="select select-bordered w-full">
            <option value="">— no seller assigned —</option>
            {% for value, label in form.fields.seller.choices %}
              {% if value %}
              <option value="{{ value }}"
                {% if form.seller.value|stringformat:"s" == value|stringformat:"s" %}
                  selected{% endif %}>
                {{ label }}
              </option>
              {% endif %}
            {% endfor %}
          </select>
        </div>

        <!-- Buttons -->
        <div class="card-actions justify-end gap-2">
          <a href="{% url 'car-list' %}" class="btn btn-ghost">Cancel</a>
          <button type="submit"
                  class="btn {% if object %}btn-warning{% else %}btn-success{% endif %}">
            {% if object %}💾 Save Changes{% else %}➕ Add Car{% endif %}
          </button>
        </div>

      </form>
    </div>
  </div>
</div>
{% endblock %}
```

---

## 12. car_confirm_delete.html

```html
{% extends 'showroom/base.html' %}
{% block title %}Delete Car{% endblock %}

{% block content %}
<div class="max-w-md mx-auto mt-16">
  <div class="card bg-base-200 shadow-lg border border-error/30">
    <div class="card-body text-center">

      <div class="text-6xl mb-2">🗑️</div>
      <h1 class="text-2xl font-bold text-error">Delete Car?</h1>
      <p class="text-base-content/70 mt-2">
        You are about to permanently delete
        <span class="font-bold text-base-content">{{ object }}</span>.
        This action cannot be undone.
      </p>

      <div class="card-actions justify-center gap-4 mt-6">
        <a href="{% url 'car-list' %}" class="btn btn-ghost btn-wide">
          Cancel
        </a>
        <form method="post">
          {% csrf_token %}
          <button type="submit" class="btn btn-error btn-wide">
            Yes, Delete
          </button>
        </form>
      </div>

    </div>
  </div>
</div>
{% endblock %}
```

---

## 13. seller_list.html

```html
{% extends 'showroom/base.html' %}
{% block title %}Sellers{% endblock %}

{% block content %}
<div class="flex flex-wrap items-center justify-between gap-4 mb-8">
  <div>
    <h1 class="text-3xl font-bold">Sellers</h1>
    <p class="text-base-content/60 mt-1">All sales staff across all branches</p>
  </div>
  <a href="{% url 'seller-create' %}" class="btn btn-primary">
    + Add Seller
  </a>
</div>

<!-- Search bar -->
<div class="form-control mb-6">
  <div class="join w-full max-w-md">
    <input
      type="search"
      name="q"
      placeholder="Search by name or branch…"
      hx-get="{% url 'seller-search' %}"
      hx-trigger="keyup changed delay:300ms"
      hx-target="#seller-results"
      hx-swap="innerHTML"
      class="input input-bordered join-item w-full"
    >
    <button class="btn join-item btn-neutral">🔍</button>
  </div>
</div>

<!-- Results container -->
<div id="seller-results">
  {% include 'showroom/partials/seller_cards.html' %}
</div>
{% endblock %}
```

---

## 14. partials/seller_cards.html

```html
{# Fragment only — no {% extends %} #}
{% if sellers %}
<div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
  {% for seller in sellers %}
  <div id="seller-{{ seller.pk }}"
       class="card bg-base-200 shadow hover:shadow-lg
              transition-shadow duration-200">
    <div class="card-body p-5">

      <!-- Avatar + name -->
      <div class="flex items-center gap-3 mb-3">
        <div class="avatar placeholder">
          <div class="bg-secondary text-secondary-content
                      rounded-full w-12">
            <span class="text-lg font-bold">
              {{ seller.first_name|first }}{{ seller.last_name|first }}
            </span>
          </div>
        </div>
        <div>
          <h3 class="font-bold text-base">
            <a href="{% url 'seller-detail' seller.pk %}"
               class="link link-hover">{{ seller }}</a>
          </h3>
          {% if seller.is_active %}
            <div class="badge badge-success badge-sm">Active</div>
          {% else %}
            <div class="badge badge-ghost badge-sm">Inactive</div>
          {% endif %}
        </div>
      </div>

      <!-- Branches -->
      <div class="flex flex-wrap gap-1 mb-4">
        {% for branch in seller.branches.all %}
          <a href="{% url 'branch-detail' branch.pk %}"
             class="badge badge-outline badge-primary badge-sm hover:badge-primary
                    transition-colors">
            {{ branch.name }}
          </a>
        {% empty %}
          <span class="text-xs text-base-content/40">No branches assigned</span>
        {% endfor %}
      </div>

      <!-- Action buttons -->
      <div class="card-actions justify-end">
        <a href="{% url 'seller-update' seller.pk %}"
           class="btn btn-warning btn-xs">Edit</a>
        <a href="{% url 'seller-delete' seller.pk %}"
           class="btn btn-error btn-xs">Delete</a>
      </div>

    </div>
  </div>
  {% endfor %}
</div>
{% else %}
<div class="alert alert-info mt-4">
  <span>No sellers found matching your search.</span>
</div>
{% endif %}
```

---

## 15. seller_detail.html

```html
{% extends 'showroom/base.html' %}
{% block title %}{{ seller }}{% endblock %}

{% block content %}

<!-- Breadcrumb -->
<div class="breadcrumbs text-sm mb-6">
  <ul>
    <li><a href="{% url 'seller-list' %}">Sellers</a></li>
    <li>{{ seller }}</li>
  </ul>
</div>

<!-- Profile hero card -->
<div class="card bg-base-200 shadow mb-8">
  <div class="card-body">
    <div class="flex flex-wrap items-start gap-6">

      <!-- Avatar -->
      <div class="avatar placeholder">
        <div class="bg-secondary text-secondary-content rounded-full w-20">
          <span class="text-3xl font-bold">
            {{ seller.first_name|first }}{{ seller.last_name|first }}
          </span>
        </div>
      </div>

      <!-- Info -->
      <div class="flex-1">
        <h1 class="text-3xl font-bold">{{ seller }}</h1>
        <div class="flex flex-wrap gap-2 mt-2">
          {% if seller.is_active %}
            <div class="badge badge-success">Active</div>
          {% else %}
            <div class="badge badge-ghost">Inactive</div>
          {% endif %}
          <div class="badge badge-neutral">
            {{ seller.cars.count }} car{{ seller.cars.count|pluralize }} managed
          </div>
        </div>

        <!-- Branches -->
        <div class="mt-3">
          <p class="text-sm text-base-content/60 mb-1">Works at:</p>
          <div class="flex flex-wrap gap-2">
            {% for branch in seller.branches.all %}
              <a href="{% url 'branch-detail' branch.pk %}"
                 class="badge badge-primary badge-outline hover:badge-primary
                        transition-colors">
                {{ branch.name }} — {{ branch.city }}
              </a>
            {% empty %}
              <span class="text-sm text-base-content/40">No branches assigned</span>
            {% endfor %}
          </div>
        </div>
      </div>

      <!-- Edit button -->
      <a href="{% url 'seller-update' seller.pk %}"
         class="btn btn-warning btn-sm">
        ✏️ Edit Seller
      </a>
    </div>
  </div>
</div>

<!-- Cars managed by this seller -->
<h2 class="text-xl font-bold mb-4">
  Cars Managed by {{ seller.first_name }}
</h2>

{% if cars %}
<div class="overflow-x-auto rounded-lg shadow">
  <table class="table table-zebra w-full">
    <thead class="bg-base-300">
      <tr>
        <th>Car</th>
        <th>Year</th>
        <th>Price</th>
        <th>Branch</th>
        <th>Transmission</th>
        <th class="text-right">Actions</th>
      </tr>
    </thead>
    <tbody>
      {% for car in cars %}
      <tr class="hover">
        <td class="font-semibold">{{ car.make }} {{ car.model }}</td>
        <td>{{ car.year }}</td>
        <td class="text-success font-semibold">
          ${{ car.price|floatformat:0 }}
        </td>
        <td>
          <a href="{% url 'branch-detail' car.branch.pk %}"
             class="link link-primary link-hover text-sm">
            {{ car.branch.name }}
          </a>
        </td>
        <td>
          <div class="badge badge-ghost badge-sm">
            {{ car.get_transmission_display }}
          </div>
        </td>
        <td class="text-right">
          <a href="{% url 'car-update' car.pk %}"
             class="btn btn-warning btn-xs">Edit</a>
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>
{% else %}
<div class="alert alert-ghost">
  <span>{{ seller.first_name }} has no cars assigned yet.</span>
</div>
{% endif %}

{% endblock %}
```

---

## 16. seller_form.html

```html
{% extends 'showroom/base.html' %}
{% block title %}{% if object %}Edit Seller{% else %}Add Seller{% endif %}{% endblock %}

{% block content %}

<!-- Breadcrumb -->
<div class="breadcrumbs text-sm mb-6">
  <ul>
    <li><a href="{% url 'seller-list' %}">Sellers</a></li>
    <li>{% if object %}Edit {{ object }}{% else %}Add Seller{% endif %}</li>
  </ul>
</div>

<div class="max-w-xl mx-auto">
  <div class="card bg-base-200 shadow-lg">
    <div class="card-body">

      <h1 class="card-title text-2xl mb-4">
        {% if object %}✏️ Edit {{ object }}{% else %}👤 Add a Seller{% endif %}
      </h1>

      <form method="post" novalidate>
        {% csrf_token %}

        <!-- First name -->
        <div class="form-control mb-4">
          <label class="label" for="id_first_name">
            <span class="label-text font-medium">First Name</span>
          </label>
          <input type="text" name="first_name" id="id_first_name"
                 value="{{ form.first_name.value|default:'' }}"
                 class="input input-bordered w-full
                   {% if form.first_name.errors %}input-error{% endif %}">
          {% for error in form.first_name.errors %}
            <label class="label">
              <span class="label-text-alt text-error">{{ error }}</span>
            </label>
          {% endfor %}
        </div>

        <!-- Last name -->
        <div class="form-control mb-4">
          <label class="label" for="id_last_name">
            <span class="label-text font-medium">Last Name</span>
          </label>
          <input type="text" name="last_name" id="id_last_name"
                 value="{{ form.last_name.value|default:'' }}"
                 class="input input-bordered w-full
                   {% if form.last_name.errors %}input-error{% endif %}">
          {% for error in form.last_name.errors %}
            <label class="label">
              <span class="label-text-alt text-error">{{ error }}</span>
            </label>
          {% endfor %}
        </div>

        <!-- Branches (multi-select) -->
        <div class="form-control mb-4">
          <label class="label">
            <span class="label-text font-medium">Branches</span>
            <span class="label-text-alt opacity-60">Hold Ctrl/Cmd to select multiple</span>
          </label>
          <select name="branches" id="id_branches" multiple
                  class="select select-bordered w-full h-32">
            {% for value, label in form.fields.branches.choices %}
            <option value="{{ value }}"
              {% if value in form.branches.value %}selected{% endif %}>
              {{ label }}
            </option>
            {% endfor %}
          </select>
        </div>

        <!-- Is active -->
        <div class="form-control mb-6">
          <label class="label cursor-pointer justify-start gap-4">
            <input type="checkbox" name="is_active" id="id_is_active"
                   class="toggle toggle-success"
                   {% if form.is_active.value %}checked{% endif %}>
            <span class="label-text font-medium">Active seller</span>
          </label>
        </div>

        <!-- Buttons -->
        <div class="card-actions justify-end gap-2">
          <a href="{% url 'seller-list' %}" class="btn btn-ghost">Cancel</a>
          <button type="submit"
                  class="btn {% if object %}btn-warning{% else %}btn-success{% endif %}">
            {% if object %}💾 Save Changes{% else %}➕ Add Seller{% endif %}
          </button>
        </div>

      </form>
    </div>
  </div>
</div>
{% endblock %}
```

---

## 17. seller_confirm_delete.html

```html
{% extends 'showroom/base.html' %}
{% block title %}Delete Seller{% endblock %}

{% block content %}
<div class="max-w-md mx-auto mt-16">
  <div class="card bg-base-200 shadow-lg border border-error/30">
    <div class="card-body text-center">

      <div class="text-6xl mb-2">👤</div>
      <h1 class="text-2xl font-bold text-error">Delete Seller?</h1>
      <p class="text-base-content/70 mt-2">
        You are about to permanently remove
        <span class="font-bold text-base-content">{{ object }}</span>
        from the system. Their cars will have the seller field set to empty.
        This action cannot be undone.
      </p>

      <!-- Stats warning -->
      <div class="stats shadow mt-4 w-full">
        <div class="stat">
          <div class="stat-title">Cars assigned</div>
          <div class="stat-value text-error text-2xl">
            {{ object.cars.count }}
          </div>
          <div class="stat-desc">will lose their seller</div>
        </div>
        <div class="stat">
          <div class="stat-title">Branches</div>
          <div class="stat-value text-warning text-2xl">
            {{ object.branches.count }}
          </div>
          <div class="stat-desc">will lose this seller</div>
        </div>
      </div>

      <div class="card-actions justify-center gap-4 mt-6">
        <a href="{% url 'seller-list' %}" class="btn btn-ghost btn-wide">
          Cancel
        </a>
        <form method="post">
          {% csrf_token %}
          <button type="submit" class="btn btn-error btn-wide">
            Yes, Delete
          </button>
        </form>
      </div>

    </div>
  </div>
</div>
{% endblock %}
```

---

## 18. Template File Structure

Every template file in the project, in the location Django expects it:

```
showroom/
└── templates/
    └── showroom/
        ├── base.html                     ← Section 5
        ├── auth/
        │   └── modal.html                ← Section 6
        ├── branch_list.html              ← Section 7
        ├── branch_detail.html            ← Section 8
        ├── car_list.html                 ← Section 9
        ├── car_form.html                 ← Section 11
        ├── car_confirm_delete.html       ← Section 12
        ├── seller_list.html              ← Section 13
        ├── seller_detail.html            ← Section 15
        ├── seller_form.html              ← Section 16
        ├── seller_confirm_delete.html    ← Section 17
        └── partials/
            ├── car_table.html            ← Section 10
            └── seller_cards.html         ← Section 14
```

### DaisyUI component quick reference

| Component | Classes used | Used in |
|---|---|---|
| Navbar | `navbar navbar-start navbar-center navbar-end` | base.html |
| Dropdown | `dropdown dropdown-end menu` | Navbar mobile menu, user menu |
| Modal / Dialog | `modal modal-box modal-backdrop` | Auth modal |
| Tabs | `tabs tabs-bordered tab tab-content` | Auth modal |
| Card | `card card-body card-title card-actions` | Branches, forms, delete pages |
| Table | `table table-zebra` | Cars, seller detail |
| Badge | `badge badge-primary badge-success` | Status labels, branch tags |
| Button | `btn btn-primary btn-warning btn-error` | All action buttons |
| Input | `input input-bordered input-error` | Forms, search |
| Select | `select select-bordered` | Form dropdowns |
| Toggle | `toggle toggle-success` | is_active checkbox |
| Join | `join join-item` | Search bar button group, action button groups |
| Alert | `alert alert-success alert-info alert-warning alert-error` | Toast notifications, empty states |
| Toast | `toast toast-end toast-bottom` | Toast container |
| Stats | `stats stat stat-title stat-value` | Branch detail header, delete warning |
| Avatar | `avatar avatar-placeholder` | Seller initials |
| Breadcrumbs | `breadcrumbs` | Form pages, detail pages |
| Footer | `footer footer-center` | base.html |

### Checklist

- [ ] Tailwind CDN `<script>` tag is in `<head>` of `base.html`
- [ ] DaisyUI CDN `<link>` tag is in `<head>` **after** the Tailwind script
- [ ] `data-theme="night"` is on the `<html>` tag
- [ ] `{% include 'showroom/auth/modal.html' %}` is in `base.html`
- [ ] `id="toast-container"` exists in `base.html` even when there are no messages
- [ ] `hx-headers` with `csrf_token` is on `<body>` in `base.html`
- [ ] `{% now "Y" %}` works — confirm `django.contrib.humanize` is not required (it is a built-in template tag, no extra app needed)
- [ ] `messages.success/warning/error/info` calls are in every `form_valid` override in `views.py`
- [ ] `partials/car_table.html` and `partials/seller_cards.html` do **not** have `{% extends %}`
