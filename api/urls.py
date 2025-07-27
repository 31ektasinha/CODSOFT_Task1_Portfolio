from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'api'

# Create a router for any ViewSets (if we add them later)
router = DefaultRouter()

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Posts
    path('posts/', views.PostListCreateView.as_view(), name='post-list'),
    path('posts/<uuid:pk>/', views.PostDetailView.as_view(), name='post-detail'),
    path('posts/<uuid:post_id>/like/', views.like_post, name='like-post'),
    path('posts/<uuid:post_id>/comments/', views.CommentListCreateView.as_view(), name='post-comments'),
    
    # Scheduled Posts
    path('scheduled-posts/', views.ScheduledPostListCreateView.as_view(), name='scheduled-post-list'),
    path('scheduled-posts/<uuid:pk>/', views.ScheduledPostDetailView.as_view(), name='scheduled-post-detail'),
    
    # User Profile
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    
    # Social Media Accounts
    path('social-accounts/', views.SocialMediaAccountListView.as_view(), name='social-accounts'),
    
    # Activity Logs
    path('activity-logs/', views.ActivityLogListView.as_view(), name='activity-logs'),
    
    # Dashboard & Analytics
    path('dashboard/stats/', views.dashboard_stats, name='dashboard-stats'),
    path('analytics/', views.analytics_data, name='analytics-data'),
    
    # Utilities
    path('sync/', views.sync_social_media, name='sync-social-media'),
    path('platforms/', views.platform_options, name='platform-options'),
    path('users/search/', views.user_search, name='user-search'),
]