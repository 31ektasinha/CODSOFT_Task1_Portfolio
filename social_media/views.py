from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
import json

from .models import Post, Comment, Like, Hashtag, SocialMediaMetrics
from .services import SocialMediaManager
from accounts.models import SocialMediaAccount, ActivityLog


@login_required
def sync_posts(request):
    """Sync posts from connected social media platforms."""
    if request.method == 'POST':
        try:
            manager = SocialMediaManager(request.user)
            synced_count = manager.sync_posts_from_platforms()
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully synced {synced_count} posts',
                'synced_count': synced_count
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Failed to sync posts: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
def platform_status(request):
    """Get status of connected social media platforms."""
    accounts = SocialMediaAccount.objects.filter(user=request.user)
    
    platform_data = []
    for account in accounts:
        # Get recent posts count
        recent_posts = Post.objects.filter(
            user=request.user,
            platform=account.platform,
            posted_at__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        platform_data.append({
            'platform': account.platform,
            'platform_username': account.platform_username,
            'is_active': account.is_active,
            'is_token_expired': account.is_token_expired,
            'recent_posts': recent_posts,
            'last_updated': account.updated_at.isoformat(),
        })
    
    return JsonResponse({
        'platforms': platform_data,
        'total_connected': accounts.filter(is_active=True).count()
    })


@login_required
@csrf_exempt
def like_post(request, post_id):
    """Like or unlike a post."""
    if request.method == 'POST':
        try:
            post = get_object_or_404(Post, id=post_id)
            like, created = Like.objects.get_or_create(
                user=request.user,
                post=post
            )
            
            if not created:
                # Unlike the post
                like.delete()
                liked = False
                action = 'unliked'
            else:
                liked = True
                action = 'liked'
                
                # Log the activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='post_liked',
                    description=f'Liked post: {post.content[:50]}...'
                )
            
            # Update post likes count
            post.likes_count = post.likes.count()
            post.save()
            
            return JsonResponse({
                'success': True,
                'liked': liked,
                'action': action,
                'likes_count': post.likes_count
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
@csrf_exempt
def add_comment(request, post_id):
    """Add a comment to a post."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            content = data.get('content', '').strip()
            parent_id = data.get('parent_id')
            
            if not content:
                return JsonResponse({
                    'success': False,
                    'message': 'Comment content is required'
                })
            
            post = get_object_or_404(Post, id=post_id)
            
            # Get parent comment if specified
            parent_comment = None
            if parent_id:
                parent_comment = get_object_or_404(Comment, id=parent_id)
            
            # Create comment
            comment = Comment.objects.create(
                post=post,
                user=request.user,
                content=content,
                parent_comment=parent_comment
            )
            
            # Update post comments count
            post.comments_count = post.comments.count()
            post.save()
            
            # Log the activity
            ActivityLog.objects.create(
                user=request.user,
                action='comment_created',
                description=f'Commented on post: {post.content[:50]}...'
            )
            
            return JsonResponse({
                'success': True,
                'comment': {
                    'id': str(comment.id),
                    'content': comment.content,
                    'user': comment.user.username,
                    'created_at': comment.created_at.isoformat()
                },
                'comments_count': post.comments_count
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
@csrf_exempt
def share_post(request, post_id):
    """Share a post (create a repost)."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            platforms = data.get('platforms', [])
            comment = data.get('comment', '')
            
            if not platforms:
                return JsonResponse({
                    'success': False,
                    'message': 'At least one platform must be selected'
                })
            
            original_post = get_object_or_404(Post, id=post_id)
            
            # Create share content
            share_content = comment
            if comment:
                share_content += f"\n\nSharing: {original_post.content}"
            else:
                share_content = f"Sharing: {original_post.content}"
            
            # Use social media manager to post to platforms
            manager = SocialMediaManager(request.user)
            results = manager.post_to_platforms(share_content, platforms)
            
            # Update original post shares count
            original_post.shares_count += 1
            original_post.save()
            
            # Log the activity
            ActivityLog.objects.create(
                user=request.user,
                action='post_shared',
                description=f'Shared post to {len(platforms)} platform(s)'
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Post shared to {len(platforms)} platform(s)',
                'results': results,
                'shares_count': original_post.shares_count
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
def insights_view(request):
    """Get social media insights and analytics."""
    user = request.user
    period = request.GET.get('period', '30')
    
    try:
        days = int(period)
    except ValueError:
        days = 30
    
    start_date = timezone.now() - timedelta(days=days)
    
    # Get posts in period
    posts = Post.objects.filter(user=user, posted_at__gte=start_date)
    
    # Calculate insights
    insights = {
        'period_days': days,
        'total_posts': posts.count(),
        'total_likes': sum(post.likes_count for post in posts),
        'total_comments': sum(post.comments_count for post in posts),
        'total_shares': sum(post.shares_count for post in posts),
        
        # Platform breakdown
        'platform_breakdown': {},
        
        # Best performing posts
        'top_posts': [],
        
        # Engagement trends
        'daily_engagement': [],
        
        # Popular hashtags
        'popular_hashtags': [],
    }
    
    # Platform breakdown
    for platform in posts.values_list('platform', flat=True).distinct():
        platform_posts = posts.filter(platform=platform)
        insights['platform_breakdown'][platform] = {
            'posts': platform_posts.count(),
            'likes': sum(post.likes_count for post in platform_posts),
            'comments': sum(post.comments_count for post in platform_posts),
            'shares': sum(post.shares_count for post in platform_posts),
        }
    
    # Top performing posts
    top_posts = posts.order_by('-likes_count')[:5]
    for post in top_posts:
        insights['top_posts'].append({
            'id': str(post.id),
            'content': post.content[:100],
            'platform': post.platform,
            'likes': post.likes_count,
            'comments': post.comments_count,
            'shares': post.shares_count,
            'posted_at': post.posted_at.isoformat(),
        })
    
    # Daily engagement for the last 14 days
    for i in range(14):
        date = timezone.now() - timedelta(days=i)
        day_posts = posts.filter(posted_at__date=date.date())
        daily_likes = sum(post.likes_count for post in day_posts)
        daily_comments = sum(post.comments_count for post in day_posts)
        
        insights['daily_engagement'].append({
            'date': date.strftime('%Y-%m-%d'),
            'posts': day_posts.count(),
            'likes': daily_likes,
            'comments': daily_comments,
            'total_engagement': daily_likes + daily_comments,
        })
    
    # Popular hashtags
    hashtags = Hashtag.objects.filter(
        posts__user=user,
        posts__posted_at__gte=start_date
    ).distinct().order_by('-usage_count')[:10]
    
    for hashtag in hashtags:
        user_hashtag_posts = hashtag.posts.filter(user=user, posted_at__gte=start_date)
        insights['popular_hashtags'].append({
            'name': hashtag.name,
            'usage_count': user_hashtag_posts.count(),
            'total_engagement': sum(
                post.likes_count + post.comments_count + post.shares_count
                for post in user_hashtag_posts
            ),
        })
    
    return JsonResponse(insights)


@login_required
def trending_hashtags(request):
    """Get trending hashtags."""
    period = request.GET.get('period', '7')  # Default to 7 days
    
    try:
        days = int(period)
    except ValueError:
        days = 7
    
    start_date = timezone.now() - timedelta(days=days)
    
    # Get hashtags used in the period
    hashtags = Hashtag.objects.filter(
        posts__posted_at__gte=start_date
    ).annotate(
        recent_usage=Count('posts', filter=Q(posts__posted_at__gte=start_date))
    ).order_by('-recent_usage')[:20]
    
    trending_data = []
    for hashtag in hashtags:
        recent_posts = hashtag.posts.filter(posted_at__gte=start_date)
        total_engagement = sum(
            post.likes_count + post.comments_count + post.shares_count
            for post in recent_posts
        )
        
        # Calculate trending score (simplified)
        trending_score = (hashtag.recent_usage * 2) + (total_engagement * 0.1)
        
        trending_data.append({
            'name': hashtag.name,
            'recent_usage': hashtag.recent_usage,
            'total_engagement': total_engagement,
            'trending_score': round(trending_score, 2),
        })
    
    # Sort by trending score
    trending_data.sort(key=lambda x: x['trending_score'], reverse=True)
    
    return JsonResponse({
        'period_days': days,
        'trending_hashtags': trending_data[:10],
        'total_hashtags': len(trending_data),
    })