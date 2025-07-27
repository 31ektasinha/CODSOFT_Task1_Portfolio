from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import Post, Comment, Like, ScheduledPost, SocialMediaMetrics, Hashtag, SavedPost


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Admin configuration for Post model."""
    list_display = [
        'content_short', 'user', 'platform', 'post_type', 
        'likes_count', 'comments_count', 'shares_count', 'posted_at'
    ]
    list_filter = ['platform', 'post_type', 'is_public', 'posted_at', 'created_at']
    search_fields = ['content', 'user__username', 'hashtags', 'mentions']
    readonly_fields = ['id', 'platform_post_id', 'created_at', 'updated_at']
    date_hierarchy = 'posted_at'
    ordering = ['-posted_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'platform', 'platform_post_id', 'post_type')
        }),
        ('Content', {
            'fields': ('content', 'image', 'video_url', 'link_url', 'link_title', 'link_description')
        }),
        ('Engagement', {
            'fields': ('likes_count', 'comments_count', 'shares_count')
        }),
        ('Metadata', {
            'fields': ('is_public', 'location', 'hashtags', 'mentions')
        }),
        ('Timestamps', {
            'fields': ('posted_at', 'created_at', 'updated_at')
        }),
    )
    
    def content_short(self, obj):
        """Show truncated content."""
        if len(obj.content) > 100:
            return obj.content[:100] + '...'
        return obj.content
    content_short.short_description = 'Content'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin configuration for Comment model."""
    list_display = ['content_short', 'user', 'post_platform', 'parent_comment', 'created_at']
    list_filter = ['created_at', 'post__platform']
    search_fields = ['content', 'user__username', 'post__content']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def content_short(self, obj):
        """Show truncated content."""
        if len(obj.content) > 80:
            return obj.content[:80] + '...'
        return obj.content
    content_short.short_description = 'Content'
    
    def post_platform(self, obj):
        """Show post platform."""
        return obj.post.platform
    post_platform.short_description = 'Platform'
    
    def get_queryset(self, request):
        """Optimize queryset."""
        return super().get_queryset(request).select_related('user', 'post', 'parent_comment')


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    """Admin configuration for Like model."""
    list_display = ['user', 'post_content', 'post_platform', 'created_at']
    list_filter = ['created_at', 'post__platform']
    search_fields = ['user__username', 'post__content']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def post_content(self, obj):
        """Show post content."""
        if len(obj.post.content) > 50:
            return obj.post.content[:50] + '...'
        return obj.post.content
    post_content.short_description = 'Post Content'
    
    def post_platform(self, obj):
        """Show post platform."""
        return obj.post.platform
    post_platform.short_description = 'Platform'
    
    def get_queryset(self, request):
        """Optimize queryset."""
        return super().get_queryset(request).select_related('user', 'post')


@admin.register(ScheduledPost)
class ScheduledPostAdmin(admin.ModelAdmin):
    """Admin configuration for ScheduledPost model."""
    list_display = [
        'content_short', 'user', 'platforms_list', 'scheduled_time', 
        'status', 'created_at'
    ]
    list_filter = ['status', 'scheduled_time', 'created_at']
    search_fields = ['content', 'user__username']
    readonly_fields = ['id', 'published_posts', 'error_messages', 'created_at', 'updated_at']
    date_hierarchy = 'scheduled_time'
    ordering = ['scheduled_time']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'platforms', 'status')
        }),
        ('Content', {
            'fields': ('content', 'image', 'video_url', 'link_url')
        }),
        ('Scheduling', {
            'fields': ('scheduled_time',)
        }),
        ('Results', {
            'fields': ('published_posts', 'error_messages')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def content_short(self, obj):
        """Show truncated content."""
        if len(obj.content) > 80:
            return obj.content[:80] + '...'
        return obj.content
    content_short.short_description = 'Content'
    
    def platforms_list(self, obj):
        """Show platforms as comma-separated list."""
        return ', '.join(obj.platforms) if obj.platforms else 'None'
    platforms_list.short_description = 'Platforms'
    
    def get_queryset(self, request):
        """Optimize queryset."""
        return super().get_queryset(request).select_related('user')


@admin.register(SocialMediaMetrics)
class SocialMediaMetricsAdmin(admin.ModelAdmin):
    """Admin configuration for SocialMediaMetrics model."""
    list_display = [
        'user', 'platform', 'date', 'posts_count', 'likes_received', 
        'comments_received', 'followers_count', 'engagement_rate'
    ]
    list_filter = ['platform', 'date', 'created_at']
    search_fields = ['user__username']
    readonly_fields = ['engagement_rate', 'created_at']
    date_hierarchy = 'date'
    ordering = ['-date']
    
    def engagement_rate(self, obj):
        """Calculate and display engagement rate."""
        if obj.posts_count > 0:
            total_engagement = obj.likes_received + obj.comments_received + obj.shares_received
            rate = (total_engagement / obj.posts_count) * 100
            return f"{rate:.2f}%"
        return "0%"
    engagement_rate.short_description = 'Engagement Rate'
    
    def get_queryset(self, request):
        """Optimize queryset."""
        return super().get_queryset(request).select_related('user')


@admin.register(Hashtag)
class HashtagAdmin(admin.ModelAdmin):
    """Admin configuration for Hashtag model."""
    list_display = ['name', 'usage_count', 'posts_count', 'trending_indicator', 'created_at']
    search_fields = ['name']
    readonly_fields = ['usage_count', 'posts_count', 'created_at']
    ordering = ['-usage_count']
    
    def posts_count(self, obj):
        """Show number of posts using this hashtag."""
        return obj.posts.count()
    posts_count.short_description = 'Posts Count'
    
    def trending_indicator(self, obj):
        """Show trending indicator."""
        from django.utils import timezone
        from datetime import timedelta
        
        recent_posts = obj.posts.filter(
            posted_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        if recent_posts >= 5:
            return format_html('<span style="color: green;">🔥 Trending</span>')
        elif recent_posts >= 2:
            return format_html('<span style="color: orange;">📈 Rising</span>')
        else:
            return format_html('<span style="color: gray;">📊 Normal</span>')
    trending_indicator.short_description = 'Trend Status'
    
    def get_queryset(self, request):
        """Optimize queryset with prefetch_related."""
        return super().get_queryset(request).prefetch_related('posts')


@admin.register(SavedPost)
class SavedPostAdmin(admin.ModelAdmin):
    """Admin configuration for SavedPost model."""
    list_display = ['user', 'post_content', 'post_platform', 'created_at']
    list_filter = ['created_at', 'post__platform']
    search_fields = ['user__username', 'post__content']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def post_content(self, obj):
        """Show post content."""
        if len(obj.post.content) > 80:
            return obj.post.content[:80] + '...'
        return obj.post.content
    post_content.short_description = 'Post Content'
    
    def post_platform(self, obj):
        """Show post platform."""
        return obj.post.platform
    post_platform.short_description = 'Platform'
    
    def get_queryset(self, request):
        """Optimize queryset."""
        return super().get_queryset(request).select_related('user', 'post')


# Custom admin actions
def mark_posts_as_public(modeladmin, request, queryset):
    """Mark selected posts as public."""
    updated = queryset.update(is_public=True)
    modeladmin.message_user(request, f'{updated} posts marked as public.')
mark_posts_as_public.short_description = "Mark selected posts as public"

def mark_posts_as_private(modeladmin, request, queryset):
    """Mark selected posts as private."""
    updated = queryset.update(is_public=False)
    modeladmin.message_user(request, f'{updated} posts marked as private.')
mark_posts_as_private.short_description = "Mark selected posts as private"

# Add actions to PostAdmin
PostAdmin.actions = [mark_posts_as_public, mark_posts_as_private]


def cancel_scheduled_posts(modeladmin, request, queryset):
    """Cancel selected scheduled posts."""
    updated = queryset.filter(status='pending').update(status='cancelled')
    modeladmin.message_user(request, f'{updated} scheduled posts cancelled.')
cancel_scheduled_posts.short_description = "Cancel selected pending posts"

# Add actions to ScheduledPostAdmin
ScheduledPostAdmin.actions = [cancel_scheduled_posts]