import requests
import json
import logging
from typing import Dict, List, Optional
from django.conf import settings
from django.utils import timezone
from datetime import datetime
from .models import Post, SocialMediaMetrics
from accounts.models import SocialMediaAccount

logger = logging.getLogger('social_media')


class BaseSocialMediaService:
    """Base class for social media API integrations."""
    
    def __init__(self, user, platform):
        self.user = user
        self.platform = platform
        self.account = self._get_account()
    
    def _get_account(self):
        """Get the social media account for the user and platform."""
        try:
            return SocialMediaAccount.objects.get(
                user=self.user,
                platform=self.platform,
                is_active=True
            )
        except SocialMediaAccount.DoesNotExist:
            raise Exception(f"No active {self.platform} account found for user {self.user.username}")
    
    def _make_request(self, method, url, headers=None, data=None, params=None):
        """Make HTTP request with error handling."""
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=data,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for {self.platform}: {e}")
            raise
    
    def fetch_posts(self) -> List[Dict]:
        """Fetch posts from the platform."""
        raise NotImplementedError
    
    def post_content(self, content: str, **kwargs) -> Dict:
        """Post content to the platform."""
        raise NotImplementedError
    
    def get_metrics(self) -> Dict:
        """Get platform metrics."""
        raise NotImplementedError


class TwitterService(BaseSocialMediaService):
    """Twitter API integration service."""
    
    def __init__(self, user):
        super().__init__(user, 'twitter')
        self.api_base = 'https://api.twitter.com/2'
    
    def _get_headers(self):
        """Get Twitter API headers."""
        return {
            'Authorization': f'Bearer {self.account.access_token}',
            'Content-Type': 'application/json'
        }
    
    def fetch_posts(self, count=50) -> List[Dict]:
        """Fetch recent tweets for the user."""
        try:
            # Note: This is a simplified example. Real implementation would need proper OAuth
            url = f"{self.api_base}/users/{self.account.platform_user_id}/tweets"
            params = {
                'max_results': min(count, 100),
                'tweet.fields': 'created_at,public_metrics,text',
            }
            
            response = self._make_request(
                'GET', url, 
                headers=self._get_headers(),
                params=params
            )
            
            posts = []
            for tweet in response.get('data', []):
                posts.append({
                    'platform_post_id': tweet['id'],
                    'content': tweet['text'],
                    'posted_at': datetime.fromisoformat(tweet['created_at'].replace('Z', '+00:00')),
                    'likes_count': tweet.get('public_metrics', {}).get('like_count', 0),
                    'comments_count': tweet.get('public_metrics', {}).get('reply_count', 0),
                    'shares_count': tweet.get('public_metrics', {}).get('retweet_count', 0),
                })
            
            return posts
            
        except Exception as e:
            logger.error(f"Failed to fetch Twitter posts: {e}")
            return []
    
    def post_content(self, content: str, **kwargs) -> Dict:
        """Post a tweet."""
        try:
            url = f"{self.api_base}/tweets"
            data = {'text': content}
            
            response = self._make_request(
                'POST', url,
                headers=self._get_headers(),
                data=json.dumps(data)
            )
            
            return {
                'success': True,
                'platform_post_id': response['data']['id'],
                'message': 'Tweet posted successfully'
            }
            
        except Exception as e:
            logger.error(f"Failed to post to Twitter: {e}")
            return {
                'success': False,
                'error': str(e)
            }


class FacebookService(BaseSocialMediaService):
    """Facebook API integration service."""
    
    def __init__(self, user):
        super().__init__(user, 'facebook')
        self.api_base = 'https://graph.facebook.com/v18.0'
    
    def fetch_posts(self, count=50) -> List[Dict]:
        """Fetch recent Facebook posts."""
        try:
            url = f"{self.api_base}/me/posts"
            params = {
                'access_token': self.account.access_token,
                'fields': 'id,message,created_time,likes.summary(true),comments.summary(true)',
                'limit': min(count, 100)
            }
            
            response = self._make_request('GET', url, params=params)
            
            posts = []
            for post in response.get('data', []):
                posts.append({
                    'platform_post_id': post['id'],
                    'content': post.get('message', ''),
                    'posted_at': datetime.fromisoformat(post['created_time'].replace('Z', '+00:00')),
                    'likes_count': post.get('likes', {}).get('summary', {}).get('total_count', 0),
                    'comments_count': post.get('comments', {}).get('summary', {}).get('total_count', 0),
                    'shares_count': 0,  # Facebook API doesn't provide shares count easily
                })
            
            return posts
            
        except Exception as e:
            logger.error(f"Failed to fetch Facebook posts: {e}")
            return []
    
    def post_content(self, content: str, **kwargs) -> Dict:
        """Post to Facebook."""
        try:
            url = f"{self.api_base}/me/feed"
            data = {
                'message': content,
                'access_token': self.account.access_token
            }
            
            response = self._make_request('POST', url, data=data)
            
            return {
                'success': True,
                'platform_post_id': response['id'],
                'message': 'Facebook post published successfully'
            }
            
        except Exception as e:
            logger.error(f"Failed to post to Facebook: {e}")
            return {
                'success': False,
                'error': str(e)
            }


class GitHubService(BaseSocialMediaService):
    """GitHub API integration service (for activity tracking)."""
    
    def __init__(self, user):
        super().__init__(user, 'github')
        self.api_base = 'https://api.github.com'
    
    def _get_headers(self):
        """Get GitHub API headers."""
        return {
            'Authorization': f'token {self.account.access_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
    
    def fetch_posts(self, count=50) -> List[Dict]:
        """Fetch recent GitHub activity (commits, issues, etc.)."""
        try:
            url = f"{self.api_base}/users/{self.account.platform_username}/events"
            params = {'per_page': min(count, 100)}
            
            response = self._make_request(
                'GET', url,
                headers=self._get_headers(),
                params=params
            )
            
            posts = []
            for event in response:
                if event['type'] in ['PushEvent', 'IssuesEvent', 'PullRequestEvent']:
                    content = self._format_github_event(event)
                    if content:
                        posts.append({
                            'platform_post_id': event['id'],
                            'content': content,
                            'posted_at': datetime.fromisoformat(event['created_at'].replace('Z', '+00:00')),
                            'likes_count': 0,
                            'comments_count': 0,
                            'shares_count': 0,
                        })
            
            return posts
            
        except Exception as e:
            logger.error(f"Failed to fetch GitHub activity: {e}")
            return []
    
    def _format_github_event(self, event) -> str:
        """Format GitHub event into readable content."""
        event_type = event['type']
        repo_name = event['repo']['name']
        
        if event_type == 'PushEvent':
            commits = len(event['payload'].get('commits', []))
            return f"Pushed {commits} commit(s) to {repo_name}"
        elif event_type == 'IssuesEvent':
            action = event['payload']['action']
            issue_title = event['payload']['issue']['title']
            return f"{action.capitalize()} issue: {issue_title} in {repo_name}"
        elif event_type == 'PullRequestEvent':
            action = event['payload']['action']
            pr_title = event['payload']['pull_request']['title']
            return f"{action.capitalize()} pull request: {pr_title} in {repo_name}"
        
        return ''
    
    def post_content(self, content: str, **kwargs) -> Dict:
        """GitHub doesn't support posting arbitrary content."""
        return {
            'success': False,
            'error': 'GitHub does not support posting arbitrary content'
        }


class SocialMediaServiceFactory:
    """Factory class to get appropriate service for platform."""
    
    services = {
        'twitter': TwitterService,
        'facebook': FacebookService,
        'github': GitHubService,
    }
    
    @classmethod
    def get_service(cls, user, platform):
        """Get service instance for platform."""
        service_class = cls.services.get(platform)
        if service_class:
            return service_class(user)
        else:
            raise ValueError(f"Unsupported platform: {platform}")


class SocialMediaManager:
    """Main manager for social media operations."""
    
    def __init__(self, user):
        self.user = user
    
    def sync_posts_from_platforms(self):
        """Sync posts from all connected platforms."""
        connected_accounts = SocialMediaAccount.objects.filter(
            user=self.user,
            is_active=True
        )
        
        synced_count = 0
        
        for account in connected_accounts:
            try:
                service = SocialMediaServiceFactory.get_service(self.user, account.platform)
                posts_data = service.fetch_posts()
                
                for post_data in posts_data:
                    post, created = Post.objects.get_or_create(
                        user=self.user,
                        platform=account.platform,
                        platform_post_id=post_data['platform_post_id'],
                        defaults={
                            'content': post_data['content'],
                            'posted_at': post_data['posted_at'],
                            'likes_count': post_data['likes_count'],
                            'comments_count': post_data['comments_count'],
                            'shares_count': post_data['shares_count'],
                        }
                    )
                    
                    if created:
                        synced_count += 1
                    else:
                        # Update engagement metrics for existing posts
                        post.likes_count = post_data['likes_count']
                        post.comments_count = post_data['comments_count']
                        post.shares_count = post_data['shares_count']
                        post.save()
                
            except Exception as e:
                logger.error(f"Failed to sync posts from {account.platform}: {e}")
        
        return synced_count
    
    def post_to_platforms(self, content: str, platforms: List[str], **kwargs) -> Dict:
        """Post content to multiple platforms."""
        results = {}
        
        for platform in platforms:
            try:
                service = SocialMediaServiceFactory.get_service(self.user, platform)
                result = service.post_content(content, **kwargs)
                results[platform] = result
                
                # Create Post object if successful
                if result.get('success'):
                    Post.objects.create(
                        user=self.user,
                        platform=platform,
                        platform_post_id=result.get('platform_post_id', ''),
                        content=content,
                        post_type='text'
                    )
                
            except Exception as e:
                logger.error(f"Failed to post to {platform}: {e}")
                results[platform] = {
                    'success': False,
                    'error': str(e)
                }
        
        return results