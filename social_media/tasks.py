from celery import shared_task
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import datetime, timedelta
import logging

from .models import ScheduledPost, Post, SocialMediaMetrics
from .services import SocialMediaManager
from accounts.models import ActivityLog

logger = logging.getLogger('social_media')


@shared_task
def process_scheduled_posts():
    """Process and publish scheduled posts that are due."""
    now = timezone.now()
    
    # Get posts that are ready to be published
    pending_posts = ScheduledPost.objects.filter(
        status='pending',
        scheduled_time__lte=now
    )
    
    for scheduled_post in pending_posts:
        try:
            # Update status to processing
            scheduled_post.status = 'processing'
            scheduled_post.save()
            
            # Post to platforms
            manager = SocialMediaManager(scheduled_post.user)
            results = manager.post_to_platforms(
                content=scheduled_post.content,
                platforms=scheduled_post.platforms
            )
            
            # Update scheduled post with results
            published_posts = {}
            error_messages = {}
            
            for platform, result in results.items():
                if result.get('success'):
                    published_posts[platform] = result.get('platform_post_id', '')
                else:
                    error_messages[platform] = result.get('error', 'Unknown error')
            
            # Update status based on results
            if published_posts and not error_messages:
                scheduled_post.status = 'published'
            elif published_posts and error_messages:
                scheduled_post.status = 'published'  # Partially published
            else:
                scheduled_post.status = 'failed'
            
            scheduled_post.published_posts = published_posts
            scheduled_post.error_messages = error_messages
            scheduled_post.save()
            
            # Log the activity
            ActivityLog.objects.create(
                user=scheduled_post.user,
                action='post_created',
                description=f'Scheduled post published to {len(published_posts)} platform(s)'
            )
            
            logger.info(f"Processed scheduled post {scheduled_post.id} for user {scheduled_post.user.username}")
            
        except Exception as e:
            # Mark as failed
            scheduled_post.status = 'failed'
            scheduled_post.error_messages = {'system': str(e)}
            scheduled_post.save()
            
            logger.error(f"Failed to process scheduled post {scheduled_post.id}: {e}")


@shared_task
def sync_user_social_media_data(user_id):
    """Sync social media data for a specific user."""
    try:
        user = User.objects.get(id=user_id)
        manager = SocialMediaManager(user)
        synced_count = manager.sync_posts_from_platforms()
        
        logger.info(f"Synced {synced_count} posts for user {user.username}")
        return synced_count
        
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} not found")
        return 0
    except Exception as e:
        logger.error(f"Failed to sync data for user {user_id}: {e}")
        return 0


@shared_task
def sync_all_users_data():
    """Sync social media data for all active users."""
    users_with_accounts = User.objects.filter(
        social_accounts__is_active=True
    ).distinct()
    
    total_synced = 0
    
    for user in users_with_accounts:
        try:
            synced_count = sync_user_social_media_data.delay(user.id).get()
            total_synced += synced_count
        except Exception as e:
            logger.error(f"Failed to queue sync for user {user.username}: {e}")
    
    logger.info(f"Synced data for {users_with_accounts.count()} users, total posts: {total_synced}")
    return total_synced


@shared_task
def cleanup_old_activity_logs():
    """Clean up activity logs older than 90 days."""
    cutoff_date = timezone.now() - timedelta(days=90)
    
    deleted_count = ActivityLog.objects.filter(
        created_at__lt=cutoff_date
    ).delete()[0]
    
    logger.info(f"Cleaned up {deleted_count} old activity log entries")
    return deleted_count


@shared_task
def update_social_media_metrics():
    """Update daily metrics for all users."""
    today = timezone.now().date()
    users_with_accounts = User.objects.filter(
        social_accounts__is_active=True
    ).distinct()
    
    for user in users_with_accounts:
        for account in user.social_accounts.filter(is_active=True):
            try:
                # Get posts for today
                today_posts = Post.objects.filter(
                    user=user,
                    platform=account.platform,
                    posted_at__date=today
                )
                
                # Calculate metrics
                posts_count = today_posts.count()
                likes_received = sum(post.likes_count for post in today_posts)
                comments_received = sum(post.comments_count for post in today_posts)
                shares_received = sum(post.shares_count for post in today_posts)
                
                # Create or update metrics
                metrics, created = SocialMediaMetrics.objects.get_or_create(
                    user=user,
                    platform=account.platform,
                    date=today,
                    defaults={
                        'posts_count': posts_count,
                        'likes_received': likes_received,
                        'comments_received': comments_received,
                        'shares_received': shares_received,
                    }
                )
                
                if not created:
                    metrics.posts_count = posts_count
                    metrics.likes_received = likes_received
                    metrics.comments_received = comments_received
                    metrics.shares_received = shares_received
                    metrics.save()
                
            except Exception as e:
                logger.error(f"Failed to update metrics for {user.username} on {account.platform}: {e}")
    
    logger.info(f"Updated metrics for {users_with_accounts.count()} users")


@shared_task
def generate_analytics_report(user_id, period_days=30):
    """Generate analytics report for a user."""
    try:
        user = User.objects.get(id=user_id)
        start_date = timezone.now() - timedelta(days=period_days)
        
        # Get posts in period
        posts = Post.objects.filter(
            user=user,
            posted_at__gte=start_date
        )
        
        # Calculate analytics
        total_posts = posts.count()
        total_likes = sum(post.likes_count for post in posts)
        total_comments = sum(post.comments_count for post in posts)
        total_shares = sum(post.shares_count for post in posts)
        
        # Platform breakdown
        platform_stats = {}
        for platform in posts.values_list('platform', flat=True).distinct():
            platform_posts = posts.filter(platform=platform)
            platform_stats[platform] = {
                'posts': platform_posts.count(),
                'likes': sum(post.likes_count for post in platform_posts),
                'comments': sum(post.comments_count for post in platform_posts),
                'shares': sum(post.shares_count for post in platform_posts),
            }
        
        # Top performing posts
        top_posts = posts.order_by('-likes_count')[:5]
        
        report = {
            'user_id': user_id,
            'period_days': period_days,
            'total_posts': total_posts,
            'total_likes': total_likes,
            'total_comments': total_comments,
            'total_shares': total_shares,
            'platform_stats': platform_stats,
            'top_posts': [
                {
                    'id': str(post.id),
                    'content': post.content[:100],
                    'platform': post.platform,
                    'likes': post.likes_count,
                    'comments': post.comments_count,
                    'shares': post.shares_count,
                }
                for post in top_posts
            ],
            'generated_at': timezone.now().isoformat(),
        }
        
        logger.info(f"Generated analytics report for user {user.username}")
        return report
        
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} not found")
        return None
    except Exception as e:
        logger.error(f"Failed to generate analytics report for user {user_id}: {e}")
        return None


@shared_task
def retry_failed_scheduled_posts():
    """Retry scheduled posts that failed due to temporary errors."""
    failed_posts = ScheduledPost.objects.filter(
        status='failed',
        scheduled_time__gte=timezone.now() - timedelta(hours=24)  # Only retry recent failures
    )
    
    retry_count = 0
    
    for scheduled_post in failed_posts:
        # Check if the failure was due to temporary error
        error_messages = scheduled_post.error_messages
        temporary_errors = ['timeout', 'rate limit', 'temporary', 'unavailable']
        
        is_temporary_error = any(
            any(temp_error in str(error).lower() for temp_error in temporary_errors)
            for error in error_messages.values()
        )
        
        if is_temporary_error:
            # Reset status to pending for retry
            scheduled_post.status = 'pending'
            scheduled_post.error_messages = {}
            scheduled_post.save()
            retry_count += 1
    
    logger.info(f"Queued {retry_count} failed posts for retry")
    return retry_count