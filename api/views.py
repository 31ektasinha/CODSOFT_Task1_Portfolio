from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth.models import User
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import timedelta
import json

from social_media.models import Post, Comment, Like, ScheduledPost, SocialMediaMetrics
from accounts.models import UserProfile, SocialMediaAccount, ActivityLog
from .serializers import (
    PostSerializer, CommentSerializer, ScheduledPostSerializer,
    UserProfileSerializer, SocialMediaAccountSerializer,
    SocialMediaMetricsSerializer, ActivityLogSerializer
)


class CustomPagination(PageNumberPagination):
    """Custom pagination class."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class PostListCreateView(generics.ListCreateAPIView):
    """List and create posts."""
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination
    
    def get_queryset(self):
        queryset = Post.objects.filter(user=self.request.user)
        
        # Filter by platform
        platform = self.request.query_params.get('platform')
        if platform:
            queryset = queryset.filter(platform=platform)
        
        # Search in content
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(content__icontains=search) |
                Q(hashtags__icontains=search)
            )
        
        return queryset.order_by('-posted_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a post."""
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Post.objects.filter(user=self.request.user)


class CommentListCreateView(generics.ListCreateAPIView):
    """List and create comments for a post."""
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        post_id = self.kwargs['post_id']
        return Comment.objects.filter(
            post_id=post_id,
            post__user=self.request.user
        ).order_by('created_at')
    
    def perform_create(self, serializer):
        post_id = self.kwargs['post_id']
        post = Post.objects.get(id=post_id, user=self.request.user)
        serializer.save(user=self.request.user, post=post)


class ScheduledPostListCreateView(generics.ListCreateAPIView):
    """List and create scheduled posts."""
    serializer_class = ScheduledPostSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination
    
    def get_queryset(self):
        return ScheduledPost.objects.filter(user=self.request.user).order_by('scheduled_time')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ScheduledPostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a scheduled post."""
    serializer_class = ScheduledPostSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ScheduledPost.objects.filter(user=self.request.user)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Retrieve and update user profile."""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


class SocialMediaAccountListView(generics.ListAPIView):
    """List connected social media accounts."""
    serializer_class = SocialMediaAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return SocialMediaAccount.objects.filter(user=self.request.user)


class ActivityLogListView(generics.ListAPIView):
    """List user activity logs."""
    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination
    
    def get_queryset(self):
        queryset = ActivityLog.objects.filter(user=self.request.user)
        
        # Filter by action
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)
        
        return queryset.order_by('-created_at')


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics."""
    user = request.user
    
    # Basic stats
    total_posts = Post.objects.filter(user=user).count()
    total_likes = Like.objects.filter(post__user=user).count()
    total_comments = Comment.objects.filter(post__user=user).count()
    
    # Recent activity (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_posts = Post.objects.filter(
        user=user,
        posted_at__gte=thirty_days_ago
    ).count()
    
    # Platform breakdown
    platform_stats = Post.objects.filter(user=user).values('platform').annotate(
        count=Count('id'),
        total_likes=Sum('likes_count'),
        total_comments=Sum('comments_count')
    ).order_by('-count')
    
    # Scheduled posts
    pending_scheduled = ScheduledPost.objects.filter(
        user=user,
        status='pending',
        scheduled_time__gte=timezone.now()
    ).count()
    
    # Connected accounts
    connected_accounts = SocialMediaAccount.objects.filter(
        user=user,
        is_active=True
    ).count()
    
    # Engagement rate
    engagement_rate = 0
    if total_posts > 0:
        total_engagement = total_likes + total_comments
        engagement_rate = round((total_engagement / total_posts) * 100, 2)
    
    return Response({
        'total_posts': total_posts,
        'total_likes': total_likes,
        'total_comments': total_comments,
        'recent_posts': recent_posts,
        'platform_stats': platform_stats,
        'pending_scheduled': pending_scheduled,
        'connected_accounts': connected_accounts,
        'engagement_rate': engagement_rate,
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def analytics_data(request):
    """Get analytics data for charts and insights."""
    user = request.user
    period = int(request.GET.get('period', 30))  # Default to 30 days
    
    start_date = timezone.now() - timedelta(days=period)
    
    # Posts in period
    posts_in_period = Post.objects.filter(
        user=user,
        posted_at__gte=start_date
    )
    
    # Daily activity for chart
    daily_activity = []
    for i in range(period):
        date = start_date + timedelta(days=i)
        posts_count = posts_in_period.filter(
            posted_at__date=date.date()
        ).count()
        daily_activity.append({
            'date': date.strftime('%Y-%m-%d'),
            'posts': posts_count
        })
    
    # Platform performance
    platform_performance = posts_in_period.values('platform').annotate(
        posts_count=Count('id'),
        avg_likes=Sum('likes_count') / Count('id') if posts_in_period.count() > 0 else 0,
        avg_comments=Sum('comments_count') / Count('id') if posts_in_period.count() > 0 else 0,
        total_engagement=Sum('likes_count') + Sum('comments_count')
    ).order_by('-posts_count')
    
    # Top performing posts
    top_posts = posts_in_period.order_by('-likes_count')[:10]
    top_posts_data = PostSerializer(top_posts, many=True).data
    
    # Engagement metrics
    total_likes = posts_in_period.aggregate(Sum('likes_count'))['likes_count__sum'] or 0
    total_comments = posts_in_period.aggregate(Sum('comments_count'))['comments_count__sum'] or 0
    total_shares = posts_in_period.aggregate(Sum('shares_count'))['shares_count__sum'] or 0
    
    return Response({
        'period': period,
        'daily_activity': daily_activity,
        'platform_performance': list(platform_performance),
        'top_posts': top_posts_data,
        'total_likes': total_likes,
        'total_comments': total_comments,
        'total_shares': total_shares,
        'total_posts': posts_in_period.count(),
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def like_post(request, post_id):
    """Like or unlike a post."""
    try:
        post = Post.objects.get(id=post_id)
        like, created = Like.objects.get_or_create(
            user=request.user,
            post=post
        )
        
        if not created:
            # Unlike the post
            like.delete()
            liked = False
        else:
            liked = True
            
            # Log the activity
            ActivityLog.objects.create(
                user=request.user,
                action='post_liked',
                description=f'Liked post: {post.content[:50]}...'
            )
        
        # Update post likes count
        post.likes_count = post.likes.count()
        post.save()
        
        return Response({
            'success': True,
            'liked': liked,
            'likes_count': post.likes_count
        })
        
    except Post.DoesNotExist:
        return Response(
            {'error': 'Post not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def sync_social_media(request):
    """Trigger social media data synchronization."""
    from social_media.tasks import sync_user_social_media_data
    
    # Queue the sync task
    task = sync_user_social_media_data.delay(request.user.id)
    
    return Response({
        'success': True,
        'message': 'Social media sync started',
        'task_id': task.id
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def platform_options(request):
    """Get available platform options."""
    connected_accounts = SocialMediaAccount.objects.filter(
        user=request.user,
        is_active=True
    ).values_list('platform', flat=True)
    
    all_platforms = [
        {'key': 'twitter', 'name': 'Twitter', 'icon': 'fab fa-twitter', 'color': '#1da1f2'},
        {'key': 'facebook', 'name': 'Facebook', 'icon': 'fab fa-facebook', 'color': '#4267b2'},
        {'key': 'instagram', 'name': 'Instagram', 'icon': 'fab fa-instagram', 'color': '#e4405f'},
        {'key': 'github', 'name': 'GitHub', 'icon': 'fab fa-github', 'color': '#333'},
    ]
    
    # Mark connected platforms
    for platform in all_platforms:
        platform['is_connected'] = platform['key'] in connected_accounts
    
    return Response({
        'platforms': all_platforms,
        'connected_count': len(connected_accounts)
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_search(request):
    """Search for users."""
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return Response({'users': []})
    
    users = User.objects.filter(
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query)
    ).select_related('userprofile')[:20]
    
    users_data = []
    for user in users:
        try:
            profile = user.userprofile
            avatar_url = profile.avatar.url if profile.avatar else None
        except UserProfile.DoesNotExist:
            avatar_url = None
        
        users_data.append({
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'avatar_url': avatar_url
        })
    
    return Response({'users': users_data})