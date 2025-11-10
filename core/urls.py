from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('create-disk/', views.create_disk_view, name='create_disk'),
    path('disk/<str:disk_name>/', views.disk_stats_view, name='disk_stats'),
    path('refresh-disks/', views.refresh_disks_view, name='refresh_disks'),
]

