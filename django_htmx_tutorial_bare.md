# Django + HTMX
## CRUD Operations & Search with Class-Based Views
### Car Dealership Tutorial for Python Beginners

---

## Table of Contents

1. [Overview & What You'll Build](#1-overview--what-youll-build)
2. [Project Setup](#2-project-setup)
3. [Models](#3-models)
4. [Forms](#4-forms)
5. [Views](#5-views)
6. [URL Configuration](#6-url-configuration)
7. [Templates](#7-templates)
8. [HTMX — How It Works](#8-htmx--how-it-works)
9. [Key Concepts Explained](#9-key-concepts-explained)
10. [Authentication — Login & Registration](#10-authentication--login--registration)
11. [Running the Project](#11-running-the-project)
12. [Extensions to Try](#12-extensions-to-try)

---

## 1. Overview & What You'll Build

In this tutorial you will build a web application for a car dealership company that has 4 branches. Each branch lists cars and the sellers who work there. You will practise the core skills every Django developer needs: connecting models with foreign keys, writing class-based views, and making pages feel dynamic with HTMX — all without writing a single line of custom CSS.

### What you will learn

- How to design models connected by `ForeignKey` and `ManyToManyField`
- How Django's ORM lets views pull data from multiple related models
- How to use Django's built-in generic class-based views (`ListView`, `DetailView`, `CreateView`, `UpdateView`, `DeleteView`)
- How to add HTMX so pages update without a full reload
- How to build live search and inline CRUD entirely in Django templates

### Project structure at a glance

```
dealership/          ← Django project folder
├── dealership/      ← project settings package
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── showroom/        ← our single app
    ├── models.py
    ├── views.py
    ├── urls.py
    ├── forms.py
    └── templates/
        └── showroom/
            ├── auth/
            │   ├── login.html
            │   └── register.html
            ├── base.html
            ├── branch_list.html
            ├── branch_detail.html
            ├── car_list.html
            ├── car_form.html
            ├── car_confirm_delete.html
            ├── seller_list.html
            ├── seller_detail.html
            ├── seller_form.html
            ├── seller_confirm_delete.html
            └── partials/
                ├── car_table.html
                └── seller_cards.html
```

---

## 2. Project Setup

### Prerequisites

- Python 3.10 or newer installed
- Basic familiarity with Python functions and classes
- A terminal / command prompt

### Step-by-step setup

**1. Create and activate a virtual environment**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

**2. Install Django**

```bash
pip install django
```

**3. Create the project and app**

```bash
django-admin startproject dealership .
python manage.py startapp showroom
```

**4. Register the app in settings.py**

Open `dealership/settings.py` and add the app to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ... Django built-ins ...
    'showroom',
]
```

> 💡 No external libraries needed for HTMX — we load it from a CDN in the base template.

---

## 3. Models

We keep every model minimal on purpose. The goal is to show different Django field types and how models connect to each other — not to build an exhaustive database schema.

### Data-type cheat sheet

| Django field      | Python type   | Used in                              |
|-------------------|---------------|--------------------------------------|
| `CharField`       | `str`         | Branch name, city, car make/model    |
| `TextField`       | `str` (long)  | Branch notes                         |
| `IntegerField`    | `int`         | Car year                             |
| `DecimalField`    | `Decimal`     | Car price                            |
| `BooleanField`    | `bool`        | Seller active status                 |
| `DateField`       | `datetime.date` | Branch opened date                 |
| `ForeignKey`      | model instance | Car → Branch, Car → Seller          |
| `ManyToManyField` | QuerySet      | Seller ↔ Branch                      |

### models.py

```python
from django.db import models


class Branch(models.Model):
    name        = models.CharField(max_length=100)   # CharField → str
    city        = models.CharField(max_length=80)
    opened_date = models.DateField()                 # DateField
    notes       = models.TextField(blank=True)       # TextField (optional)

    def __str__(self):
        return f'{self.name} ({self.city})'


class Seller(models.Model):
    first_name = models.CharField(max_length=50)
    last_name  = models.CharField(max_length=50)
    # ManyToManyField: a seller can work at multiple branches
    branches   = models.ManyToManyField(
        Branch,
        related_name='sellers',  # branch.sellers.all()
    )
    is_active  = models.BooleanField(default=True)   # BooleanField

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Car(models.Model):
    TRANSMISSION_CHOICES = [
        ('auto',   'Automatic'),
        ('manual', 'Manual'),
    ]

    make         = models.CharField(max_length=60)
    model        = models.CharField(max_length=60)
    year         = models.IntegerField()             # IntegerField
    price        = models.DecimalField(              # DecimalField
                       max_digits=10, decimal_places=2
                   )
    transmission = models.CharField(
                       max_length=10,
                       choices=TRANSMISSION_CHOICES,
                       default='auto',
                   )
    # ForeignKey: each car belongs to one branch
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='cars',   # branch.cars.all()
    )
    # ForeignKey: each car is managed by one seller
    seller = models.ForeignKey(
        Seller,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cars',   # seller.cars.all()
    )

    def __str__(self):
        return f'{self.year} {self.make} {self.model}'
```

### Model relationship diagram

```
Branch ──< Car >── Seller
  │                  │
  └──── M2M ─────────┘
   (branch.sellers)  (seller.branches)

One Branch  has many Cars           (ForeignKey on Car)
One Seller  has many Cars           (ForeignKey on Car)
One Seller  works at many Branches  (ManyToManyField)
One Branch  has many Sellers        (reverse of ManyToManyField)
```

### Create and apply migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Seed data (management command — optional but recommended)

Create this file so you can quickly fill the database for testing.

Create file: `showroom/management/commands/seed.py`

```python
from django.core.management.base import BaseCommand
from showroom.models import Branch, Seller, Car
import datetime


class Command(BaseCommand):
    def handle(self, *args, **options):
        # 4 branches
        b1 = Branch.objects.create(
            name='North End',
            city='Toronto',
            opened_date=datetime.date(2010, 3, 15),
        )
        b2 = Branch.objects.create(
            name='Lakeshore',
            city='Toronto',
            opened_date=datetime.date(2015, 7, 1),
        )
        b3 = Branch.objects.create(
            name='Westgate',
            city='Mississauga',
            opened_date=datetime.date(2018, 1, 20),
        )
        b4 = Branch.objects.create(
            name='Eastview',
            city='Scarborough',
            opened_date=datetime.date(2021, 9, 5),
        )

        # 3 sellers — some work at multiple branches
        s1 = Seller.objects.create(first_name='Alice', last_name='Martin')
        s2 = Seller.objects.create(first_name='Bob',   last_name='Chen')
        s3 = Seller.objects.create(first_name='Carol', last_name='Patel')

        s1.branches.set([b1, b2])   # Alice works at two branches
        s2.branches.set([b1, b3])
        s3.branches.set([b2, b3, b4])

        # a few cars
        Car.objects.create(make='Toyota', model='Camry',    year=2022,
                           price=28500, branch=b1, seller=s1)
        Car.objects.create(make='Honda',  model='Civic',    year=2023,
                           price=26000, branch=b1, seller=s2)
        Car.objects.create(make='Ford',   model='F-150',    year=2021,
                           price=45000, branch=b2, seller=s3,
                           transmission='manual')
        Car.objects.create(make='BMW',    model='3 Series', year=2023,
                           price=55000, branch=b3, seller=s2)

        self.stdout.write(self.style.SUCCESS('Database seeded!'))
```

```bash
python manage.py seed
```

---

## 4. Forms

Django forms handle validation automatically. We use `ModelForm` so the form is generated directly from our model fields.

```python
# showroom/forms.py
from django import forms
from .models import Car, Seller


class CarForm(forms.ModelForm):
    class Meta:
        model  = Car
        fields = ['make', 'model', 'year', 'price',
                  'transmission', 'branch', 'seller']


class SellerForm(forms.ModelForm):
    class Meta:
        model  = Seller
        fields = ['first_name', 'last_name', 'branches', 'is_active']
```

> 💡 `ModelForm` automatically creates the right HTML input for each field type — a checkbox for `BooleanField`, a number input for `IntegerField`, a dropdown for `ForeignKey`, etc.

---

## 5. Views

Class-based views (CBVs) give you full CRUD with very little code. We also add a search view that returns only a partial HTML fragment — that partial is what HTMX will swap into the page.

### 5.1 Branch views (read-only)

Branches are managed by admins only, so we expose just list and detail views.

```python
# showroom/views.py
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import HttpResponse
from .models import Branch, Seller, Car
from .forms  import CarForm, SellerForm


# ── Branches ───────────────────────────────────────────────────────────────

class BranchListView(ListView):
    model               = Branch
    template_name       = 'showroom/branch_list.html'
    context_object_name = 'branches'


class BranchDetailView(DetailView):
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
```

### 5.2 Car views (full CRUD)

```python
# ── Cars ───────────────────────────────────────────────────────────────────

class CarListView(ListView):
    model               = Car
    template_name       = 'showroom/car_list.html'
    context_object_name = 'cars'
    # Eager-load branch and seller to avoid N+1 queries
    queryset            = Car.objects.select_related('branch', 'seller')


class CarCreateView(CreateView):
    model         = Car
    form_class    = CarForm
    template_name = 'showroom/car_form.html'
    success_url   = reverse_lazy('car-list')


class CarUpdateView(UpdateView):
    model         = Car
    form_class    = CarForm
    template_name = 'showroom/car_form.html'
    success_url   = reverse_lazy('car-list')


class CarDeleteView(DeleteView):
    model         = Car
    template_name = 'showroom/car_confirm_delete.html'
    success_url   = reverse_lazy('car-list')


# ── HTMX: live search (returns a partial HTML fragment) ────────────────────

class CarSearchView(ListView):
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
```

### 5.3 Seller views (full CRUD)

```python
# ── Sellers ────────────────────────────────────────────────────────────────

class SellerListView(ListView):
    model               = Seller
    template_name       = 'showroom/seller_list.html'
    context_object_name = 'sellers'
    queryset            = Seller.objects.prefetch_related('branches')


class SellerDetailView(DetailView):
    model               = Seller
    template_name       = 'showroom/seller_detail.html'
    context_object_name = 'seller'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['cars'] = self.object.cars.select_related('branch')
        return ctx


class SellerCreateView(CreateView):
    model         = Seller
    form_class    = SellerForm
    template_name = 'showroom/seller_form.html'
    success_url   = reverse_lazy('seller-list')


class SellerUpdateView(UpdateView):
    model         = Seller
    form_class    = SellerForm
    template_name = 'showroom/seller_form.html'
    success_url   = reverse_lazy('seller-list')


class SellerDeleteView(DeleteView):
    model         = Seller
    template_name = 'showroom/seller_confirm_delete.html'
    success_url   = reverse_lazy('seller-list')


# ── HTMX: live seller search (returns a partial HTML fragment) ─────────────

class SellerSearchView(ListView):
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
```

> 💡 `select_related('branch', 'seller')` makes Django fetch related rows in a single SQL JOIN instead of one extra query per row. Always use it in list views.

---

## 6. URL Configuration

### showroom/urls.py

```python
from django.urls import path
from . import views

urlpatterns = [
    # Branches
    path('',                 views.BranchListView.as_view(),  name='branch-list'),
    path('branch/<int:pk>/', views.BranchDetailView.as_view(), name='branch-detail'),

    # Cars
    path('cars/',                    views.CarListView.as_view(),       name='car-list'),
    path('cars/add/',                views.CarCreateView.as_view(),     name='car-create'),
    path('cars/<int:pk>/edit/',      views.CarUpdateView.as_view(),     name='car-update'),
    path('cars/<int:pk>/delete/',    views.CarDeleteView.as_view(),     name='car-delete'),
    path('cars/<int:pk>/inline-delete/',
                                     views.CarInlineDeleteView.as_view(),
                                     name='car-inline-delete'),
    # HTMX search endpoint
    path('cars/search/',             views.CarSearchView.as_view(),     name='car-search'),

    # Sellers
    path('sellers/',                 views.SellerListView.as_view(),    name='seller-list'),
    path('sellers/<int:pk>/',        views.SellerDetailView.as_view(),  name='seller-detail'),
    path('sellers/add/',             views.SellerCreateView.as_view(),  name='seller-create'),
    path('sellers/<int:pk>/edit/',   views.SellerUpdateView.as_view(),  name='seller-update'),
    path('sellers/<int:pk>/delete/', views.SellerDeleteView.as_view(),  name='seller-delete'),
    # HTMX search endpoint
    path('sellers/search/',          views.SellerSearchView.as_view(),  name='seller-search'),
]
```

### dealership/urls.py

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('showroom.urls')),
]
```

---

## 7. Templates

All templates use plain HTML with no custom CSS. HTMX is loaded from a CDN in the base template.

### 7.1 base.html

Every other template extends this one. Note the script tag at the bottom and the `hx-headers` attribute on `<body>` — this ensures every HTMX request carries the Django CSRF token.

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}Dealership{% endblock %}</title>
</head>
<!-- hx-headers sends the CSRF token with every HTMX request -->
<body hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>
  <nav>
    <a href="{% url 'branch-list' %}">Branches</a> |
    <a href="{% url 'car-list' %}">Cars</a> |
    <a href="{% url 'seller-list' %}">Sellers</a>
  </nav>
  <hr>
  <main>
    {% block content %}{% endblock %}
  </main>

  <!-- HTMX from CDN — no installation needed -->
  <script src="https://unpkg.com/htmx.org@1.9.10"></script>
</body>
</html>
```

### 7.2 branch_list.html

```html
{% extends 'showroom/base.html' %}
{% block title %}Branches{% endblock %}
{% block content %}
<h1>Our 4 Branches</h1>
<ul>
  {% for branch in branches %}
    <li>
      <a href="{% url 'branch-detail' branch.pk %}">{{ branch }}</a>
      &mdash; Opened: {{ branch.opened_date|date:"M d, Y" }}
    </li>
  {% endfor %}
</ul>
{% endblock %}
```

### 7.3 branch_detail.html — showing related data

This template demonstrates how one view can present data from all three related models at once.

```html
{% extends 'showroom/base.html' %}
{% block title %}{{ branch.name }}{% endblock %}
{% block content %}
<h1>{{ branch.name }} — {{ branch.city }}</h1>
<p>Opened: {{ branch.opened_date }}</p>
<p>{{ branch.notes }}</p>

<h2>Active Sellers at this branch</h2>
<ul>
  {% for seller in sellers %}
    {# seller comes from ctx['sellers'] = branch.sellers.filter(is_active=True) #}
    <li>
      <a href="{% url 'seller-detail' seller.pk %}">{{ seller }}</a>
    </li>
  {% empty %}
    <li>No active sellers.</li>
  {% endfor %}
</ul>

<h2>Cars at this branch</h2>
<a href="{% url 'car-create' %}">+ Add a car</a>
<table border="1">
  <tr>
    <th>Car</th><th>Year</th><th>Price</th>
    <th>Transmission</th><th>Seller</th><th>Actions</th>
  </tr>
  {% for car in cars %}
    {# car comes from ctx['cars'] = branch.cars.select_related('seller') #}
    <tr id="car-{{ car.pk }}">
      <td>{{ car.make }} {{ car.model }}</td>
      <td>{{ car.year }}</td>
      <td>${{ car.price }}</td>
      <td>{{ car.get_transmission_display }}</td>
      <td>{{ car.seller }}</td>
      <td>
        <a href="{% url 'car-update' car.pk %}">Edit</a>
        <!-- HTMX inline delete: replaces #car-{{ car.pk }} with empty string -->
        <button
          hx-delete="{% url 'car-inline-delete' car.pk %}"
          hx-target="#car-{{ car.pk }}"
          hx-swap="outerHTML"
          hx-confirm="Delete this car?">
          Delete
        </button>
      </td>
    </tr>
  {% empty %}
    <tr><td colspan="6">No cars at this branch.</td></tr>
  {% endfor %}
</table>
{% endblock %}
```

### 7.4 car_list.html — HTMX live search

The search input fires a GET request as you type. HTMX swaps only the table, not the whole page.

```html
{% extends 'showroom/base.html' %}
{% block title %}All Cars{% endblock %}
{% block content %}
<h1>All Cars</h1>
<a href="{% url 'car-create' %}">+ Add Car</a>

<!--
  hx-get      → the URL HTMX calls
  hx-trigger  → fires on keyup with 300 ms debounce
  hx-target   → the element whose HTML gets replaced
  hx-swap     → replace the inner HTML of the target
-->
<input
  type="search"
  name="q"
  placeholder="Search by make, model or branch..."
  hx-get="{% url 'car-search' %}"
  hx-trigger="keyup changed delay:300ms"
  hx-target="#car-results"
  hx-swap="innerHTML"
>

<!-- Initial full list rendered by the server -->
<div id="car-results">
  {% include 'showroom/partials/car_table.html' %}
</div>
{% endblock %}
```

### 7.5 partials/car_table.html — reusable fragment

This partial is used both for the initial render and for every HTMX search response. It does **not** extend `base.html`.

```html
{# This template renders with NO extends — it is a fragment, not a full page #}
<table border="1">
  <tr>
    <th>Car</th><th>Year</th><th>Price</th>
    <th>Branch</th><th>Seller</th><th>Actions</th>
  </tr>
  {% for car in cars %}
    <tr id="car-{{ car.pk }}">
      <td>{{ car.make }} {{ car.model }}</td>
      <td>{{ car.year }}</td>
      <td>${{ car.price }}</td>
      <td>
        <a href="{% url 'branch-detail' car.branch.pk %}">
          {{ car.branch.name }}
        </a>
      </td>
      <td>{{ car.seller }}</td>
      <td>
        <a href="{% url 'car-update' car.pk %}">Edit</a> |
        <a href="{% url 'car-delete' car.pk %}">Delete</a>
      </td>
    </tr>
  {% empty %}
    <tr><td colspan="6">No cars found.</td></tr>
  {% endfor %}
</table>
```

### 7.6 car_form.html — create & update

The same template works for both `CarCreateView` and `CarUpdateView`. Django sets `object` only on updates, so we use it to show a different title.

```html
{% extends 'showroom/base.html' %}
{% block title %}
  {% if object %}Edit Car{% else %}Add Car{% endif %}
{% endblock %}
{% block content %}
<h1>{% if object %}Edit {{ object }}{% else %}Add a Car{% endif %}</h1>
<form method="post">
  {% csrf_token %}
  {{ form.as_p }}
  <button type="submit">Save</button>
  <a href="{% url 'car-list' %}">Cancel</a>
</form>
{% endblock %}
```

### 7.7 car_confirm_delete.html

```html
{% extends 'showroom/base.html' %}
{% block title %}Delete Car{% endblock %}
{% block content %}
<h1>Delete {{ object }}?</h1>
<p>This action cannot be undone.</p>
<form method="post">
  {% csrf_token %}
  <button type="submit">Yes, delete</button>
  <a href="{% url 'car-list' %}">Cancel</a>
</form>
{% endblock %}
```

### 7.8 seller_list.html — HTMX live search with ManyToManyField display

The search input works exactly like the car search — HTMX calls `seller-search` and swaps the result into `#seller-results`. Notice the `distinct()` note: because sellers join to branches via a M2M table, filtering on `branches__name` can produce duplicate rows without it.

```html
{% extends 'showroom/base.html' %}
{% block title %}Sellers{% endblock %}
{% block content %}
<h1>Sellers</h1>
<a href="{% url 'seller-create' %}">+ Add Seller</a>

<!--
  Same HTMX pattern as car_list.html but targeting seller_cards.html
  distinct() in the view prevents duplicate cards when M2M matches multiple rows
-->
<input
  type="search"
  name="q"
  placeholder="Search by name or branch..."
  hx-get="{% url 'seller-search' %}"
  hx-trigger="keyup changed delay:300ms"
  hx-target="#seller-results"
  hx-swap="innerHTML"
>

<!-- Initial full list rendered by the server -->
<div id="seller-results">
  {% include 'showroom/partials/seller_cards.html' %}
</div>
{% endblock %}
```

### 7.9 partials/seller_cards.html — reusable fragment

This partial is used both for the initial render and for every HTMX search response. It does **not** extend `base.html`. We deliberately use cards (one `<div>` per seller) instead of a table to show that partials can return any HTML structure, not just table rows.

```html
{# Fragment only — no {% extends %} here #}
{% for seller in sellers %}
  <div id="seller-{{ seller.pk }}">
    <strong>
      <a href="{% url 'seller-detail' seller.pk %}">{{ seller }}</a>
    </strong>
    &mdash;
    {# Branches come from prefetch_related('branches') in the view #}
    Branches:
    {% for branch in seller.branches.all %}
      <a href="{% url 'branch-detail' branch.pk %}">{{ branch.name }}</a>
      {% if not forloop.last %}, {% endif %}
    {% endfor %}
    &mdash;
    Active: {{ seller.is_active|yesno:"Yes,No" }}
    &mdash;
    <a href="{% url 'seller-update' seller.pk %}">Edit</a> |
    <a href="{% url 'seller-delete' seller.pk %}">Delete</a>
  </div>
{% empty %}
  <p>No sellers found.</p>
{% endfor %}
```

> 💡 `seller.branches.all` works here without an extra query because `SellerSearchView` used `prefetch_related('branches')` — Django already fetched all branch data in one batch query and cached it on each seller object.

---

## 8. HTMX — How It Works

HTMX lets any HTML element make HTTP requests and swap the response into the page. You control everything with HTML attributes — no JavaScript required.

### The HTMX attributes you need

| Attribute    | What it does                         | Example value                    |
|--------------|--------------------------------------|----------------------------------|
| `hx-get`     | Make a GET request                   | `/cars/search/`                  |
| `hx-delete`  | Make a DELETE request                | `/cars/5/inline-delete/`         |
| `hx-trigger` | When to fire the request             | `keyup changed delay:300ms`      |
| `hx-target`  | CSS selector of element to update    | `#car-results`                   |
| `hx-swap`    | How to replace the target            | `innerHTML` / `outerHTML`        |
| `hx-confirm` | Browser confirmation dialog          | `Delete this car?`               |
| `hx-headers` | Extra HTTP headers on every request  | `{"X-CSRFToken": "..."}` on body |

### Live search flow

```
User types in search box
        ↓
HTMX fires GET /cars/search/?q=cam  (after 300 ms idle)
        ↓
Django CarSearchView filters queryset, renders partials/car_table.html
        ↓
HTMX swaps the HTML into <div id="car-results">
        ↓
Page updates without reload ✓
```

### Inline delete flow

```
User clicks Delete button
        ↓
Browser shows confirm dialog (hx-confirm)
        ↓
HTMX fires DELETE /cars/5/inline-delete/
        ↓
Django deletes the car, returns empty 200 response
        ↓
HTMX replaces <tr id="car-5"> with empty string (outerHTML swap)
        ↓
Row disappears without reload ✓
```

### CSRF token fix

Django's CSRF middleware blocks DELETE requests unless the token is present. Add `hx-headers` to `<body>` in `base.html` so every HTMX request carries it automatically:

```html
<body hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>
```

---

## 9. Key Concepts Explained

### ForeignKey vs ManyToManyField

| Concept        | ForeignKey                         | ManyToManyField                    |
|----------------|------------------------------------|------------------------------------|
| Relationship   | Many-to-one                        | Many-to-many                       |
| Example        | Many cars belong to one branch     | Sellers work at many branches      |
| DB storage     | Column in child table              | Separate join table                |
| Access forward | `car.branch`                       | `seller.branches.all()`            |
| Access reverse | `branch.cars.all()`                | `branch.sellers.all()`             |

### How `related_name` works

```python
# In models.py:
branch = models.ForeignKey(Branch, related_name='cars', ...)

# In a view or template you can then write:
branch.cars.all()              # all cars belonging to this branch
branch.cars.filter(year=2023)  # filter the related set
branch.cars.count()            # how many cars at this branch
```

### `get_context_data` — adding extra data to a view

By default, a `DetailView` only passes the single object to the template. Override `get_context_data` to pass anything else:

```python
def get_context_data(self, **kwargs):
    # 1. Call the parent method first to get the default context
    ctx = super().get_context_data(**kwargs)
    # 2. self.object is the Branch instance Django fetched for us
    ctx['cars']    = self.object.cars.select_related('seller')
    ctx['sellers'] = self.object.sellers.filter(is_active=True)
    # 3. Return the enriched context
    return ctx

# Now the template can use {{ cars }} and {{ sellers }} alongside {{ branch }}
```

### `select_related` vs `prefetch_related`

- Use `select_related` for `ForeignKey` or `OneToOneField` (single JOIN, fewer queries).
- Use `prefetch_related` for `ManyToManyField` or reverse `ForeignKey` (separate queries, combined in Python).

```python
# ForeignKey → select_related
Car.objects.select_related('branch', 'seller')  # 1 query

# ManyToManyField → prefetch_related
Seller.objects.prefetch_related('branches')     # 2 queries total
```

---

## 10. Authentication — Login & Registration

Django ships with a complete authentication system. We use it directly — no extra packages needed. We add:

- **Login** — Django's built-in `LoginView`
- **Logout** — Django's built-in `LogoutView`
- **Registration** — a custom `RegisterView` using `UserCreationForm`
- **Protection** — `LoginRequiredMixin` on every CRUD view so anonymous users are redirected to login

### How Django's auth system works

```
django.contrib.auth   (already in INSTALLED_APPS by default)
        │
        ├── User model          — stores username, password (hashed), email
        ├── LoginView           — handles the login form and session creation
        ├── LogoutView          — clears the session
        ├── UserCreationForm    — validates and saves a new user
        └── LoginRequiredMixin  — blocks unauthenticated access to a view
```

> 💡 You do not need to run extra migrations for auth — `django.contrib.auth` is migrated when you first run `python manage.py migrate`.

---

### 10.1 Settings — tell Django where to redirect

Add these two lines anywhere in `dealership/settings.py`:

```python
# Where to send unauthenticated users who hit a protected page
LOGIN_URL = '/login/'

# Where to send users after a successful login
LOGIN_REDIRECT_URL = '/'

# Where to send users after logout
LOGOUT_REDIRECT_URL = '/login/'
```

---

### 10.2 Registration form — forms.py

Django's `UserCreationForm` already handles username, password, and password confirmation. We extend it to add an optional email field.

Add this to `showroom/forms.py`:

```python
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RegisterForm(UserCreationForm):
    # email is optional — remove if you don't need it
    email = forms.EmailField(required=False)

    class Meta:
        model  = User
        fields = ['username', 'email', 'password1', 'password2']
```

> 💡 `password1` and `password2` are the two password fields built into `UserCreationForm`. Django checks they match and validates password strength automatically.

---

### 10.3 Registration view — views.py

Django provides `LoginView` and `LogoutView` out of the box. We only need to write the registration view ourselves.

Add these imports and view to `showroom/views.py`:

```python
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic.edit import CreateView
from .forms import RegisterForm


class RegisterView(CreateView):
    form_class    = RegisterForm
    template_name = 'showroom/auth/register.html'
    success_url   = reverse_lazy('branch-list')

    def form_valid(self, form):
        # Save the user, then log them in immediately
        response = super().form_valid(form)
        login(self.request, self.object)
        return response
```

---

### 10.4 Protect views with LoginRequiredMixin

`LoginRequiredMixin` must be the **first** class in the inheritance list. Any user who is not logged in will be redirected to `LOGIN_URL`.

Update `showroom/views.py` — add the mixin to every view that should be protected:

```python
from django.contrib.auth.mixins import LoginRequiredMixin


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


class CarUpdateView(LoginRequiredMixin, UpdateView):
    model         = Car
    form_class    = CarForm
    template_name = 'showroom/car_form.html'
    success_url   = reverse_lazy('car-list')


class CarDeleteView(LoginRequiredMixin, DeleteView):
    model         = Car
    template_name = 'showroom/car_confirm_delete.html'
    success_url   = reverse_lazy('car-list')


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
```

---

### 10.5 URLs — wire up auth views

Update `showroom/urls.py` to add the three auth paths:

```python
from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────────────────────
    path('login/',    LoginView.as_view(template_name='showroom/auth/login.html'),
                      name='login'),
    path('logout/',   LogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(),  name='register'),

    # ── Branches ──────────────────────────────────────────────────────────
    path('',                 views.BranchListView.as_view(),   name='branch-list'),
    path('branch/<int:pk>/', views.BranchDetailView.as_view(), name='branch-detail'),

    # ── Cars ──────────────────────────────────────────────────────────────
    path('cars/',                        views.CarListView.as_view(),       name='car-list'),
    path('cars/add/',                    views.CarCreateView.as_view(),     name='car-create'),
    path('cars/search/',                 views.CarSearchView.as_view(),     name='car-search'),
    path('cars/<int:pk>/edit/',          views.CarUpdateView.as_view(),     name='car-update'),
    path('cars/<int:pk>/delete/',        views.CarDeleteView.as_view(),     name='car-delete'),
    path('cars/<int:pk>/inline-delete/', views.CarInlineDeleteView.as_view(), name='car-inline-delete'),

    # ── Sellers ───────────────────────────────────────────────────────────
    path('sellers/',                     views.SellerListView.as_view(),    name='seller-list'),
    path('sellers/<int:pk>/',            views.SellerDetailView.as_view(),  name='seller-detail'),
    path('sellers/add/',                 views.SellerCreateView.as_view(),  name='seller-create'),
    path('sellers/<int:pk>/edit/',       views.SellerUpdateView.as_view(),  name='seller-update'),
    path('sellers/<int:pk>/delete/',     views.SellerDeleteView.as_view(),  name='seller-delete'),
    path('sellers/search/',              views.SellerSearchView.as_view(),  name='seller-search'),
]
```

> 💡 `LoginView` and `LogoutView` are imported directly from `django.contrib.auth.views` — they need no custom code, just a template path.

---

### 10.6 Templates — auth folder

Create the folder `showroom/templates/showroom/auth/` and add two files.

**auth/login.html**

```html
{% extends 'showroom/base.html' %}
{% block title %}Login{% endblock %}
{% block content %}
<h1>Login</h1>

{% if form.errors %}
  <p>Username or password is incorrect. Please try again.</p>
{% endif %}

<form method="post">
  {% csrf_token %}
  {{ form.as_p }}
  <button type="submit">Log in</button>
</form>

<p>Don't have an account? <a href="{% url 'register' %}">Register here</a></p>
{% endblock %}
```

**auth/register.html**

```html
{% extends 'showroom/base.html' %}
{% block title %}Register{% endblock %}
{% block content %}
<h1>Create an account</h1>

<form method="post">
  {% csrf_token %}
  {{ form.as_p }}
  <button type="submit">Register</button>
</form>

<p>Already have an account? <a href="{% url 'login' %}">Log in here</a></p>
{% endblock %}
```

---

### 10.7 Update base.html — show login state in the nav

Replace the `<nav>` block in `base.html` so it shows the logged-in username and a logout link, or a login link for anonymous users:

```html
<nav>
  {% if user.is_authenticated %}
    <a href="{% url 'branch-list' %}">Branches</a> |
    <a href="{% url 'car-list' %}">Cars</a> |
    <a href="{% url 'seller-list' %}">Sellers</a>
    &nbsp;&nbsp;|&nbsp;&nbsp;
    Hello, {{ user.username }} &mdash;
    <a href="{% url 'logout' %}">Logout</a>
  {% else %}
    <a href="{% url 'login' %}">Login</a> |
    <a href="{% url 'register' %}">Register</a>
  {% endif %}
</nav>
```

---

### 10.8 New file structure for templates

```
showroom/templates/showroom/
├── auth/
│   ├── login.html
│   └── register.html
├── base.html
├── branch_list.html
├── branch_detail.html
├── car_list.html
├── car_form.html
├── car_confirm_delete.html
├── seller_list.html
└── partials/
    └── car_table.html
```

---

### 10.9 Authentication flow summary

```
Anonymous user visits /cars/
        ↓
LoginRequiredMixin checks request.user.is_authenticated → False
        ↓
Redirects to /login/?next=/cars/
        ↓
User submits login form → LoginView validates credentials
        ↓
Django creates a session, sets a cookie
        ↓
Redirects to /cars/  (the original ?next= destination)
        ↓
LoginRequiredMixin check → True → view runs normally ✓


New user visits /register/
        ↓
RegisterView renders RegisterForm
        ↓
User submits form → UserCreationForm validates passwords
        ↓
User object saved to DB, login() called immediately
        ↓
Redirects to branch-list ✓
```

---

## 11. Running the Project

### Start the development server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser. You should see the branch list.

### Register models in admin (optional but useful)

```python
# showroom/admin.py
from django.contrib import admin
from .models import Branch, Seller, Car

admin.site.register(Branch)
admin.site.register(Seller)
admin.site.register(Car)
```

```bash
python manage.py createsuperuser
# Visit http://127.0.0.1:8000/admin/
```

### Checklist before testing

- [ ] `makemigrations` and `migrate` have run
- [ ] You have seeded data (`python manage.py seed`) or added records via admin
- [ ] `LOGIN_URL`, `LOGIN_REDIRECT_URL`, and `LOGOUT_REDIRECT_URL` are set in `settings.py`
- [ ] `auth/login.html` and `auth/register.html` exist inside `showroom/templates/showroom/auth/`
- [ ] All CRUD views have `LoginRequiredMixin` as their first base class
- [ ] `base.html` includes the HTMX CDN script tag
- [ ] `base.html` `<body>` has `hx-headers` with `csrf_token`
- [ ] `car-inline-delete` URL is registered in `urls.py`
- [ ] `partials/car_table.html` exists and does **not** extend `base.html`

---

## 12. Extensions to Try

Once the core app works, practise these additions on your own:

1. Add pagination to `CarListView` using Django's built-in `paginate_by = 10`
2. Add an `hx-indicator` spinner that shows while HTMX waits for a response
3. Create a `SellerSearchView` similar to `CarSearchView`
4. Add a `BranchFilterView` that filters cars by branch using a dropdown
5. Write a `CarDetailView` (`DetailView`) showing all fields plus the seller's other cars
6. Use the Django messages framework to show a success toast after create/update

> 💡 All of the above can be done without adding any CSS. Focus on the Django and HTMX mechanics first; style later.
