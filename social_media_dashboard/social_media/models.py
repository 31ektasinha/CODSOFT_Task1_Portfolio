from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
import uuid


class Post(models.Model):
    """Model for social media posts aggregated from different platforms."""
    PLATFORM_CHOICES = [
        ('twitter', 'Twitter'),
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('github', 'GitHub'),
        ('manual', 'Manual Post'),
    ]
    
    POST_TYPE_CHOICES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('link', 'Link'),
        ('retweet', 'Retweet/Share'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    platform_post_id = models.CharField(max_length=100, blank=True)
    post_type = models.CharField(max_length=20, choices=POST_TYPE_CHOICES, default='text')
    content = models.TextField()
    image = models.ImageField(upload_to='posts/images/', blank=True, null=True)
    video_url = models.URLField(blank=True)
    link_url = models.URLField(blank=True)
    link_title = models.CharField(max_length=200, blank=True)
    link_description = models.TextField(blank=True)
    
    # Engagement metrics
    likes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    shares_count = models.PositiveIntegerField(default=0)
    
    # Metadata
    is_public = models.BooleanField(default=True)
    location = models.CharField(max_length=100, blank=True)
    hashtags = models.JSONField(default=list, blank=True)
    mentions = models.JSONField(default=list, blank=True)
    
    # Timestamps
    posted_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-posted_at']
        indexes = [
            models.Index(fields=['user', '-posted_at']),
            models.Index(fields=['platform', '-posted_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.platform} - {self.content[:50]}..."


class Comment(models.Model):
    """Model for comments on posts."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    platform_comment_id = models.CharField(max_length=100, blank=True)
    
    # For nested comments
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.user.username} on {self.post.content[:30]}..."


class Like(models.Model):
    """Model for likes on posts."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'post']
    
    def __str__(self):
        return f"{self.user.username} likes {self.post.content[:30]}..."


class ScheduledPost(models.Model):
    """Model for scheduling posts across multiple platforms."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('published', 'Published'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scheduled_posts')
    platforms = models.JSONField(default=list)  # List of platforms to post to
    content = models.TextField()
    image = models.ImageField(upload_to='scheduled/images/', blank=True, null=True)
    video_url = models.URLField(blank=True)
    link_url = models.URLField(blank=True)
    
    # Scheduling
    scheduled_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Results
    published_posts = models.JSONField(default=dict, blank=True)  # Platform -> Post ID mapping
    error_messages = models.JSONField(default=dict, blank=True)  # Platform -> Error message
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['scheduled_time']
    
    def __str__(self):
        return f"Scheduled: {self.content[:50]}... at {self.scheduled_time}"


class SocialMediaMetrics(models.Model):
    """Model for storing aggregated social media metrics."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='metrics')
    platform = models.CharField(max_length=20)
    date = models.DateField()
    
    # Follower metrics
    followers_count = models.PositiveIntegerField(default=0)
    following_count = models.PositiveIntegerField(default=0)
    
    # Engagement metrics
    posts_count = models.PositiveIntegerField(default=0)
    likes_received = models.PositiveIntegerField(default=0)
    comments_received = models.PositiveIntegerField(default=0)
    shares_received = models.PositiveIntegerField(default=0)
    
    # Reach and impressions
    reach = models.PositiveIntegerField(default=0)
    impressions = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'platform', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.user.username} - {self.platform} - {self.date}"


class Hashtag(models.Model):
    """Model for tracking hashtags and their performance."""
    name = models.CharField(max_length=100, unique=True)
    posts = models.ManyToManyField(Post, related_name='hashtag_objects')
    usage_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-usage_count']
    
    def __str__(self):
        return f"#{self.name} ({self.usage_count} uses)"


class SavedPost(models.Model):
    """Model for users to save posts for later reference."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_posts')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='saved_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'post']
    
    def __str__(self):
        return f"{self.user.username} saved {self.post.content[:30]}..."
