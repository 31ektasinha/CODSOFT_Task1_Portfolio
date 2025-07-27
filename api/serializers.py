from rest_framework import serializers
from django.contrib.auth.models import User
from social_media.models import Post, Comment, Like, ScheduledPost, SocialMediaMetrics, Hashtag
from accounts.models import UserProfile, SocialMediaAccount, ActivityLog


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model."""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'user', 'bio', 'location', 'birth_date', 'avatar',
            'website', 'phone_number', 'is_verified', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'is_verified', 'created_at', 'updated_at']


class SocialMediaAccountSerializer(serializers.ModelSerializer):
    """Serializer for SocialMediaAccount model."""
    platform_display = serializers.CharField(source='get_platform_display', read_only=True)
    is_token_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = SocialMediaAccount
        fields = [
            'id', 'platform', 'platform_display', 'platform_username',
            'is_active', 'is_token_expired', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for Comment model."""
    user = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'user', 'content', 'parent_comment',
            'replies', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_replies(self, obj):
        """Get replies to this comment."""
        if obj.parent_comment is None:
            replies = Comment.objects.filter(parent_comment=obj)
            return CommentSerializer(replies, many=True, context=self.context).data
        return []


class PostSerializer(serializers.ModelSerializer):
    """Serializer for Post model."""
    user = UserSerializer(read_only=True)
    platform_display = serializers.CharField(source='get_platform_display', read_only=True)
    post_type_display = serializers.CharField(source='get_post_type_display', read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    is_liked = serializers.SerializerMethodField()
    time_since_posted = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = [
            'id', 'user', 'platform', 'platform_display', 'platform_post_id',
            'post_type', 'post_type_display', 'content', 'image', 'video_url',
            'link_url', 'link_title', 'link_description', 'likes_count',
            'comments_count', 'shares_count', 'is_public', 'location',
            'hashtags', 'mentions', 'posted_at', 'created_at', 'updated_at',
            'comments', 'is_liked', 'time_since_posted'
        ]
        read_only_fields = [
            'id', 'user', 'platform_post_id', 'likes_count', 'comments_count',
            'shares_count', 'created_at', 'updated_at', 'comments', 'is_liked',
            'time_since_posted'
        ]
    
    def get_is_liked(self, obj):
        """Check if current user has liked this post."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Like.objects.filter(user=request.user, post=obj).exists()
        return False
    
    def get_time_since_posted(self, obj):
        """Get human-readable time since post was created."""
        from django.utils.timesince import timesince
        return timesince(obj.posted_at)


class ScheduledPostSerializer(serializers.ModelSerializer):
    """Serializer for ScheduledPost model."""
    user = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    time_until_scheduled = serializers.SerializerMethodField()
    
    class Meta:
        model = ScheduledPost
        fields = [
            'id', 'user', 'platforms', 'content', 'image', 'video_url',
            'link_url', 'scheduled_time', 'status', 'status_display',
            'published_posts', 'error_messages', 'created_at', 'updated_at',
            'time_until_scheduled'
        ]
        read_only_fields = [
            'id', 'user', 'published_posts', 'error_messages',
            'created_at', 'updated_at', 'time_until_scheduled'
        ]
    
    def get_time_until_scheduled(self, obj):
        """Get time until scheduled post should be published."""
        from django.utils import timezone
        from django.utils.timesince import timeuntil
        
        if obj.status == 'pending' and obj.scheduled_time > timezone.now():
            return timeuntil(obj.scheduled_time)
        return None
    
    def validate_scheduled_time(self, value):
        """Validate that scheduled time is in the future."""
        from django.utils import timezone
        
        if value <= timezone.now():
            raise serializers.ValidationError("Scheduled time must be in the future.")
        return value
    
    def validate_platforms(self, value):
        """Validate that at least one platform is selected."""
        if not value or len(value) == 0:
            raise serializers.ValidationError("At least one platform must be selected.")
        
        valid_platforms = ['twitter', 'facebook', 'instagram', 'github']
        for platform in value:
            if platform not in valid_platforms:
                raise serializers.ValidationError(f"Invalid platform: {platform}")
        
        return value


class SocialMediaMetricsSerializer(serializers.ModelSerializer):
    """Serializer for SocialMediaMetrics model."""
    platform_display = serializers.CharField(source='get_platform_display', read_only=True)
    engagement_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = SocialMediaMetrics
        fields = [
            'id', 'platform', 'platform_display', 'date', 'followers_count',
            'following_count', 'posts_count', 'likes_received', 'comments_received',
            'shares_received', 'reach', 'impressions', 'engagement_rate', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_engagement_rate(self, obj):
        """Calculate engagement rate."""
        if obj.posts_count > 0:
            total_engagement = obj.likes_received + obj.comments_received + obj.shares_received
            return round((total_engagement / obj.posts_count) * 100, 2)
        return 0


class HashtagSerializer(serializers.ModelSerializer):
    """Serializer for Hashtag model."""
    trending_score = serializers.SerializerMethodField()
    
    class Meta:
        model = Hashtag
        fields = ['id', 'name', 'usage_count', 'trending_score', 'created_at']
        read_only_fields = ['id', 'usage_count', 'created_at']
    
    def get_trending_score(self, obj):
        """Calculate trending score based on recent usage."""
        from django.utils import timezone
        from datetime import timedelta
        
        recent_posts = obj.posts.filter(
            posted_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        # Simple trending score: recent posts / total posts * 100
        if obj.usage_count > 0:
            return round((recent_posts / obj.usage_count) * 100, 2)
        return 0


class ActivityLogSerializer(serializers.ModelSerializer):
    """Serializer for ActivityLog model."""
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    time_since = serializers.SerializerMethodField()
    
    class Meta:
        model = ActivityLog
        fields = [
            'id', 'action', 'action_display', 'description',
            'ip_address', 'created_at', 'time_since'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_time_since(self, obj):
        """Get human-readable time since activity."""
        from django.utils.timesince import timesince
        return timesince(obj.created_at)


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics."""
    total_posts = serializers.IntegerField()
    total_likes = serializers.IntegerField()
    total_comments = serializers.IntegerField()
    recent_posts = serializers.IntegerField()
    pending_scheduled = serializers.IntegerField()
    connected_accounts = serializers.IntegerField()
    engagement_rate = serializers.FloatField()
    platform_stats = serializers.ListField()


class AnalyticsDataSerializer(serializers.Serializer):
    """Serializer for analytics data."""
    period = serializers.IntegerField()
    daily_activity = serializers.ListField()
    platform_performance = serializers.ListField()
    top_posts = PostSerializer(many=True)
    total_likes = serializers.IntegerField()
    total_comments = serializers.IntegerField()
    total_shares = serializers.IntegerField()
    total_posts = serializers.IntegerField()


class BulkPostCreateSerializer(serializers.Serializer):
    """Serializer for creating multiple posts at once."""
    content = serializers.CharField(max_length=5000)
    platforms = serializers.ListField(
        child=serializers.CharField(max_length=20),
        min_length=1
    )
    post_type = serializers.ChoiceField(
        choices=Post.POST_TYPE_CHOICES,
        default='text'
    )
    image = serializers.ImageField(required=False)
    video_url = serializers.URLField(required=False)
    link_url = serializers.URLField(required=False)
    scheduled_time = serializers.DateTimeField(required=False)
    
    def validate_platforms(self, value):
        """Validate platforms."""
        valid_platforms = ['twitter', 'facebook', 'instagram', 'github']
        for platform in value:
            if platform not in valid_platforms:
                raise serializers.ValidationError(f"Invalid platform: {platform}")
        return value
    
    def validate_scheduled_time(self, value):
        """Validate scheduled time."""
        if value:
            from django.utils import timezone
            if value <= timezone.now():
                raise serializers.ValidationError("Scheduled time must be in the future.")
        return value