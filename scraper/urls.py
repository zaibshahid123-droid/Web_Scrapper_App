from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Job CRUD
    path('jobs/create/', views.job_create, name='job_create'),
    path('jobs/<int:pk>/', views.job_detail, name='job_detail'),
    path('jobs/<int:pk>/edit/', views.job_edit, name='job_edit'),
    path('jobs/<int:pk>/delete/', views.job_delete, name='job_delete'),

    # Job actions
    path('jobs/<int:pk>/run/', views.job_run, name='job_run'),
    path('jobs/<int:pk>/clear/', views.job_clear_results, name='job_clear_results'),

    # Export
    path('jobs/<int:pk>/export/csv/', views.export_csv, name='export_csv'),
    path('jobs/<int:pk>/export/json/', views.export_json, name='export_json'),

    # AJAX
    path('jobs/<int:pk>/status/', views.job_status_api, name='job_status_api'),
]
