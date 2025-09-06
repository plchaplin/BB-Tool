from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('job/<int:job_id>/update_status/', views.update_job_status, name='update_job_status'),
]
