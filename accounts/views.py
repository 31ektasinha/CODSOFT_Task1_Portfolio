from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.db import transaction
import json

from .models import UserProfile, SocialMediaAccount, ActivityLog
from .forms import UserRegistrationForm, UserProfileForm, UserUpdateForm


class CustomLoginView(LoginView):
    """Custom login view with activity logging."""
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Log the login activity
        ActivityLog.objects.create(
            user=self.request.user,
            action='login',
            description=f'User logged in from {self.request.META.get("REMOTE_ADDR")}',
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
        
        messages.success(self.request, 'Welcome back!')
        return response


class CustomLogoutView(LogoutView):
    """Custom logout view with activity logging."""
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            # Log the logout activity
            ActivityLog.objects.create(
                user=request.user,
                action='logout',
                description=f'User logged out from {request.META.get("REMOTE_ADDR")}',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        
        return super().dispatch(request, *args, **kwargs)


class SignUpView(CreateView):
    """User registration view."""
    form_class = UserRegistrationForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('accounts:login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Create user profile
        UserProfile.objects.create(user=self.object)
        
        messages.success(
            self.request, 
            'Account created successfully! Please log in to continue.'
        )
        return response


@login_required
def profile_view(request, username=None):
    """View user profile."""
    if username:
        user = get_object_or_404(User, username=username)
    else:
        user = request.user
    
    profile, created = UserProfile.objects.get_or_create(user=user)
    social_accounts = SocialMediaAccount.objects.filter(user=user, is_active=True)
    recent_activities = ActivityLog.objects.filter(user=user)[:10]
    
    context = {
        'profile_user': user,
        'profile': profile,
        'social_accounts': social_accounts,
        'recent_activities': recent_activities,
        'is_own_profile': user == request.user,
    }
    
    return render(request, 'accounts/profile.html', context)


@login_required
def edit_profile(request):
    """Edit user profile."""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            with transaction.atomic():
                user_form.save()
                profile_form.save()
            
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('accounts:profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    
    return render(request, 'accounts/edit_profile.html', context)


@login_required
def connected_accounts(request):
    """Manage connected social media accounts."""
    social_accounts = SocialMediaAccount.objects.filter(user=request.user)
    
    # Available platforms that user can connect to
    available_platforms = [
        {'key': 'twitter', 'name': 'Twitter', 'icon': 'fab fa-twitter'},
        {'key': 'facebook', 'name': 'Facebook', 'icon': 'fab fa-facebook'},
        {'key': 'instagram', 'name': 'Instagram', 'icon': 'fab fa-instagram'},
        {'key': 'github', 'name': 'GitHub', 'icon': 'fab fa-github'},
    ]
    
    # Mark which platforms are already connected
    connected_platform_keys = [acc.platform for acc in social_accounts]
    for platform in available_platforms:
        platform['is_connected'] = platform['key'] in connected_platform_keys
    
    context = {
        'social_accounts': social_accounts,
        'available_platforms': available_platforms,
    }
    
    return render(request, 'accounts/connected_accounts.html', context)


@login_required
@csrf_exempt
def disconnect_account(request, platform):
    """Disconnect a social media account."""
    if request.method == 'POST':
        try:
            account = SocialMediaAccount.objects.get(
                user=request.user,
                platform=platform
            )
            account.delete()
            
            # Log the disconnection
            ActivityLog.objects.create(
                user=request.user,
                action='account_disconnected',
                description=f'Disconnected {platform} account'
            )
            
            return JsonResponse({
                'success': True,
                'message': f'{platform.capitalize()} account disconnected successfully!'
            })
        except SocialMediaAccount.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Account not found.'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


@login_required
def activity_log(request):
    """View user's activity log."""
    activities = ActivityLog.objects.filter(user=request.user)
    
    # Filter by action if specified
    action_filter = request.GET.get('action')
    if action_filter:
        activities = activities.filter(action=action_filter)
    
    activities = activities[:50]  # Limit to last 50 activities
    
    # Get available action choices for filter
    action_choices = ActivityLog.ACTION_CHOICES
    
    context = {
        'activities': activities,
        'action_choices': action_choices,
        'current_filter': action_filter,
    }
    
    return render(request, 'accounts/activity_log.html', context)


@login_required
def delete_account(request):
    """Delete user account."""
    if request.method == 'POST':
        password = request.POST.get('password')
        
        if request.user.check_password(password):
            # Log the account deletion
            ActivityLog.objects.create(
                user=request.user,
                action='account_deleted',
                description='User account deleted'
            )
            
            user = request.user
            logout(request)
            user.delete()
            
            messages.success(request, 'Your account has been deleted successfully.')
            return redirect('accounts:signup')
        else:
            messages.error(request, 'Incorrect password. Account not deleted.')
    
    return render(request, 'accounts/delete_account.html')


def user_search(request):
    """Search for users."""
    query = request.GET.get('q', '')
    users = []
    
    if query:
        users = User.objects.filter(
            username__icontains=query
        ).select_related('userprofile')[:20]
    
    context = {
        'users': users,
        'query': query,
    }
    
    return render(request, 'accounts/user_search.html', context)


@login_required
def export_data(request):
    """Export user's data."""
    # This would implement data export functionality
    # For now, return a simple response
    return JsonResponse({
        'message': 'Data export functionality will be implemented here.'
    })