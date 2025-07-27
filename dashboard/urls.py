from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Main dashboard
    path('', views.dashboard_home, name='home'),
    
    # Analytics
    path('analytics/', views.analytics_view, name='analytics'),
    
    # Posts management
    path('posts/', views.posts_view, name='posts'),
    path('posts/delete/<uuid:post_id>/', views.delete_post, name='delete_post'),
    
    # Scheduled posts
    path('scheduled/', views.scheduled_posts_view, name='scheduled_posts'),
    path('scheduled/cancel/<uuid:post_id>/', views.cancel_scheduled_post, name='cancel_scheduled_post'),
    
    # Compose posts
    path('compose/', views.compose_post, name='compose_post'),
    
    # Settings
    path('settings/', views.settings_view, name='settings'),
]