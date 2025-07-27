from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication URLs
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    
    # Profile URLs
    path('profile/', views.profile_view, name='profile'),
    path('profile/<str:username>/', views.profile_view, name='profile_detail'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    
    # Social Media Account Management
    path('connected-accounts/', views.connected_accounts, name='connected_accounts'),
    path('disconnect-account/<str:platform>/', views.disconnect_account, name='disconnect_account'),
    
    # Activity and Settings
    path('activity-log/', views.activity_log, name='activity_log'),
    path('delete-account/', views.delete_account, name='delete_account'),
    path('export-data/', views.export_data, name='export_data'),
    
    # Search
    path('search/', views.user_search, name='user_search'),
]