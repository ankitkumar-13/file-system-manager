from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('create-disk/', views.create_disk_view, name='create_disk'),
    path('disk/<str:disk_name>/', views.disk_stats_view, name='disk_stats'),
    path('disk/<str:disk_name>/create-file/', views.create_file_view, name='create_file'),
    path('disk/<str:disk_name>/delete-file/<str:file_name>/', views.delete_file_view, name='delete_file'),
    path('disk/<str:disk_name>/download-file/<str:file_name>/', views.download_file_view, name='download_file'),
    path('refresh-disks/', views.refresh_disks_view, name='refresh_disks'),
]


