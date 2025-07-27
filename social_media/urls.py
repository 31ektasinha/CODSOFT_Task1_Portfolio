from django.urls import path
from . import views

app_name = 'social_media'

urlpatterns = [
    # Sync and management
    path('sync/', views.sync_posts, name='sync_posts'),
    path('platforms/', views.platform_status, name='platform_status'),
    
    # Post interactions
    path('post/<uuid:post_id>/like/', views.like_post, name='like_post'),
    path('post/<uuid:post_id>/comment/', views.add_comment, name='add_comment'),
    path('post/<uuid:post_id>/share/', views.share_post, name='share_post'),
    
    # Analytics and insights
    path('insights/', views.insights_view, name='insights'),
    path('trending/', views.trending_hashtags, name='trending_hashtags'),
]