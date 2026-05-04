from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView  
from . import views

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────────────────────
    path('login/',    LoginView.as_view(template_name='showroom/auth/login.html'),
                      name='login'),
    path('logout/',   LogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(),  name='register'),
    
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