from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import UserProfile, SocialMediaAccount, ActivityLog


class UserProfileInline(admin.StackedInline):
    """Inline admin for user profile."""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ['bio', 'location', 'birth_date', 'avatar', 'website', 'phone_number', 'is_verified']


class SocialMediaAccountInline(admin.TabularInline):
    """Inline admin for social media accounts."""
    model = SocialMediaAccount
    extra = 0
    readonly_fields = ['platform_user_id', 'created_at', 'updated_at']
    fields = ['platform', 'platform_username', 'is_active', 'created_at']


class CustomUserAdmin(UserAdmin):
    """Extended User admin with profile and social accounts."""
    inlines = [UserProfileInline, SocialMediaAccountInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_verified', 'date_joined']
    list_filter = ['is_staff', 'is_active', 'userprofile__is_verified', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    def is_verified(self, obj):
        """Show verification status."""
        try:
            return obj.userprofile.is_verified
        except UserProfile.DoesNotExist:
            return False
    is_verified.boolean = True
    is_verified.short_description = 'Verified'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin for user profiles."""
    list_display = ['user', 'location', 'is_verified', 'created_at']
    list_filter = ['is_verified', 'created_at', 'location']
    search_fields = ['user__username', 'user__email', 'bio', 'location']
    readonly_fields = ['created_at', 'updated_at']
    fields = [
        'user', 'bio', 'location', 'birth_date', 'avatar', 
        'website', 'phone_number', 'is_verified', 'created_at', 'updated_at'
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(SocialMediaAccount)
class SocialMediaAccountAdmin(admin.ModelAdmin):
    """Admin for social media accounts."""
    list_display = ['user', 'platform', 'platform_username', 'is_active', 'created_at']
    list_filter = ['platform', 'is_active', 'created_at']
    search_fields = ['user__username', 'platform_username', 'platform']
    readonly_fields = ['platform_user_id', 'created_at', 'updated_at', 'token_expires_at']
    fields = [
        'user', 'platform', 'platform_user_id', 'platform_username',
        'is_active', 'token_expires_at', 'created_at', 'updated_at'
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    """Admin for activity logs."""
    list_display = ['user', 'action', 'description_short', 'ip_address', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['user__username', 'action', 'description']
    readonly_fields = ['user', 'action', 'description', 'ip_address', 'user_agent', 'created_at']
    fields = ['user', 'action', 'description', 'ip_address', 'user_agent', 'created_at']
    
    def description_short(self, obj):
        """Show truncated description."""
        if len(obj.description) > 50:
            return obj.description[:50] + '...'
        return obj.description
    description_short.short_description = 'Description'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    def has_add_permission(self, request):
        """Disable manual addition of activity logs."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing of activity logs."""
        return False


# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Customize admin site headers
admin.site.site_header = 'Social Media Dashboard Admin'
admin.site.site_title = 'Social Media Dashboard'
admin.site.index_title = 'Dashboard Administration'