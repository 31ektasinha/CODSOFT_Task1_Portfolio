from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import datetime, timedelta
import json

from accounts.models import UserProfile, SocialMediaAccount, ActivityLog
from social_media.models import Post, Comment, Like, ScheduledPost, SocialMediaMetrics, Hashtag


@login_required
def dashboard_home(request):
    """Main dashboard view with overview statistics."""
    user = request.user
    
    # Get user's social media accounts
    social_accounts = SocialMediaAccount.objects.filter(user=user, is_active=True)
    
    # Get recent posts
    recent_posts = Post.objects.filter(user=user).order_by('-posted_at')[:10]
    
    # Get statistics
    total_posts = Post.objects.filter(user=user).count()
    total_likes = Like.objects.filter(post__user=user).count()
    total_comments = Comment.objects.filter(post__user=user).count()
    
    # Get engagement metrics for the last 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_posts_count = Post.objects.filter(
        user=user, 
        posted_at__gte=thirty_days_ago
    ).count()
    
    # Get scheduled posts
    pending_scheduled = ScheduledPost.objects.filter(
        user=user,
        status='pending',
        scheduled_time__gte=timezone.now()
    ).order_by('scheduled_time')[:5]
    
    # Get platform breakdown
    platform_stats = Post.objects.filter(user=user).values('platform').annotate(
        count=Count('id'),
        likes=Sum('likes_count'),
        comments=Sum('comments_count')
    ).order_by('-count')
    
    # Get recent activity
    recent_activities = ActivityLog.objects.filter(user=user)[:10]
    
    # Calculate engagement rate
    engagement_rate = 0
    if total_posts > 0:
        total_engagement = total_likes + total_comments
        engagement_rate = round((total_engagement / total_posts) * 100, 2)
    
    context = {
        'user': user,
        'social_accounts': social_accounts,
        'recent_posts': recent_posts,
        'total_posts': total_posts,
        'total_likes': total_likes,
        'total_comments': total_comments,
        'recent_posts_count': recent_posts_count,
        'pending_scheduled': pending_scheduled,
        'platform_stats': platform_stats,
        'recent_activities': recent_activities,
        'engagement_rate': engagement_rate,
    }
    
    return render(request, 'dashboard/home.html', context)


@login_required
def analytics_view(request):
    """Analytics dashboard with detailed metrics."""
    user = request.user
    
    # Date range filtering
    period = request.GET.get('period', '30')  # Default to 30 days
    try:
        days = int(period)
    except ValueError:
        days = 30
    
    start_date = timezone.now() - timedelta(days=days)
    
    # Get posts in date range
    posts_in_period = Post.objects.filter(
        user=user,
        posted_at__gte=start_date
    )
    
    # Engagement metrics
    total_posts = posts_in_period.count()
    total_likes = posts_in_period.aggregate(Sum('likes_count'))['likes_count__sum'] or 0
    total_comments = posts_in_period.aggregate(Sum('comments_count'))['comments_count__sum'] or 0
    total_shares = posts_in_period.aggregate(Sum('shares_count'))['shares_count__sum'] or 0
    
    # Platform performance
    platform_performance = posts_in_period.values('platform').annotate(
        posts_count=Count('id'),
        avg_likes=Count('likes_count'),
        avg_comments=Count('comments_count'),
        avg_shares=Count('shares_count')
    ).order_by('-posts_count')
    
    # Daily activity data for charts
    daily_activity = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        posts_count = posts_in_period.filter(
            posted_at__date=date.date()
        ).count()
        daily_activity.append({
            'date': date.strftime('%Y-%m-%d'),
            'posts': posts_count
        })
    
    # Top performing posts
    top_posts = posts_in_period.order_by('-likes_count')[:10]
    
    # Hashtag performance
    hashtag_performance = []
    for hashtag in Hashtag.objects.filter(posts__user=user).distinct()[:10]:
        user_posts_with_hashtag = hashtag.posts.filter(user=user)
        avg_engagement = user_posts_with_hashtag.aggregate(
            avg_likes=Count('likes_count'),
            avg_comments=Count('comments_count')
        )
        hashtag_performance.append({
            'hashtag': hashtag,
            'posts_count': user_posts_with_hashtag.count(),
            'avg_likes': avg_engagement['avg_likes'] or 0,
            'avg_comments': avg_engagement['avg_comments'] or 0,
        })
    
    context = {
        'period': days,
        'total_posts': total_posts,
        'total_likes': total_likes,
        'total_comments': total_comments,
        'total_shares': total_shares,
        'platform_performance': platform_performance,
        'daily_activity': json.dumps(daily_activity),
        'top_posts': top_posts,
        'hashtag_performance': hashtag_performance,
    }
    
    return render(request, 'dashboard/analytics.html', context)


@login_required
def posts_view(request):
    """View and manage all posts."""
    user = request.user
    
    # Filter parameters
    platform_filter = request.GET.get('platform', '')
    search_query = request.GET.get('search', '')
    
    # Get posts with filters
    posts = Post.objects.filter(user=user).order_by('-posted_at')
    
    if platform_filter:
        posts = posts.filter(platform=platform_filter)
    
    if search_query:
        posts = posts.filter(
            Q(content__icontains=search_query) |
            Q(hashtags__icontains=search_query)
        )
    
    # Pagination would be added here in a real application
    posts = posts[:50]  # Limit to 50 posts for now
    
    # Get available platforms for filter
    available_platforms = Post.objects.filter(user=user).values_list(
        'platform', flat=True
    ).distinct()
    
    context = {
        'posts': posts,
        'available_platforms': available_platforms,
        'current_platform': platform_filter,
        'search_query': search_query,
    }
    
    return render(request, 'dashboard/posts.html', context)


@login_required
def scheduled_posts_view(request):
    """View and manage scheduled posts."""
    user = request.user
    
    # Get scheduled posts
    scheduled_posts = ScheduledPost.objects.filter(user=user).order_by('scheduled_time')
    
    # Separate by status
    pending_posts = scheduled_posts.filter(status='pending')
    published_posts = scheduled_posts.filter(status='published')
    failed_posts = scheduled_posts.filter(status='failed')
    
    context = {
        'pending_posts': pending_posts,
        'published_posts': published_posts,
        'failed_posts': failed_posts,
    }
    
    return render(request, 'dashboard/scheduled_posts.html', context)


@login_required
def compose_post(request):
    """Compose and schedule new posts."""
    user = request.user
    
    # Get user's connected social media accounts
    connected_accounts = SocialMediaAccount.objects.filter(user=user, is_active=True)
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        platforms = request.POST.getlist('platforms')
        schedule_time = request.POST.get('schedule_time')
        
        if not content:
            messages.error(request, 'Post content is required.')
            return redirect('dashboard:compose_post')
        
        if not platforms:
            messages.error(request, 'Please select at least one platform.')
            return redirect('dashboard:compose_post')
        
        # Handle immediate posting vs scheduling
        if schedule_time:
            try:
                scheduled_datetime = datetime.strptime(schedule_time, '%Y-%m-%dT%H:%M')
                scheduled_datetime = timezone.make_aware(scheduled_datetime)
                
                if scheduled_datetime <= timezone.now():
                    messages.error(request, 'Scheduled time must be in the future.')
                    return redirect('dashboard:compose_post')
                
                # Create scheduled post
                ScheduledPost.objects.create(
                    user=user,
                    content=content,
                    platforms=platforms,
                    scheduled_time=scheduled_datetime
                )
                
                messages.success(request, f'Post scheduled for {scheduled_datetime.strftime("%B %d, %Y at %I:%M %p")}')
                
            except ValueError:
                messages.error(request, 'Invalid date/time format.')
                return redirect('dashboard:compose_post')
        else:
            # Post immediately (this would integrate with actual social media APIs)
            for platform in platforms:
                Post.objects.create(
                    user=user,
                    platform=platform,
                    content=content,
                    post_type='text'
                )
            
            messages.success(request, f'Post published to {len(platforms)} platform(s)!')
        
        return redirect('dashboard:posts')
    
    context = {
        'connected_accounts': connected_accounts,
    }
    
    return render(request, 'dashboard/compose_post.html', context)


@login_required
def settings_view(request):
    """Dashboard settings and preferences."""
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    context = {
        'profile': profile,
    }
    
    return render(request, 'dashboard/settings.html', context)


@login_required
def delete_post(request, post_id):
    """Delete a post."""
    if request.method == 'POST':
        try:
            post = Post.objects.get(id=post_id, user=request.user)
            post.delete()
            
            ActivityLog.objects.create(
                user=request.user,
                action='post_deleted',
                description=f'Deleted post: {post.content[:50]}...'
            )
            
            return JsonResponse({'success': True, 'message': 'Post deleted successfully!'})
        except Post.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Post not found.'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


@login_required
def cancel_scheduled_post(request, post_id):
    """Cancel a scheduled post."""
    if request.method == 'POST':
        try:
            scheduled_post = ScheduledPost.objects.get(id=post_id, user=request.user)
            scheduled_post.status = 'cancelled'
            scheduled_post.save()
            
            ActivityLog.objects.create(
                user=request.user,
                action='scheduled_post_cancelled',
                description=f'Cancelled scheduled post: {scheduled_post.content[:50]}...'
            )
            
            return JsonResponse({'success': True, 'message': 'Scheduled post cancelled!'})
        except ScheduledPost.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Scheduled post not found.'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})