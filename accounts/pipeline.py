from django.contrib.auth.models import User
from social_core.exceptions import AuthAlreadyAssociated
from .models import UserProfile, SocialMediaAccount, ActivityLog


def save_profile(strategy, details, user=None, *args, **kwargs):
    """
    Create or update user profile when social authentication is used.
    """
    if user:
        # Create user profile if it doesn't exist
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        # Get backend name
        backend_name = kwargs.get('backend', {}).name if kwargs.get('backend') else 'unknown'
        
        # Map backend names to our platform choices
        platform_mapping = {
            'twitter': 'twitter',
            'facebook': 'facebook',
            'instagram': 'instagram',
            'github': 'github',
        }
        
        platform = platform_mapping.get(backend_name, backend_name)
        
        # Get social account details
        uid = kwargs.get('uid', '')
        response = kwargs.get('response', {})
        
        # Extract username based on platform
        platform_username = ''
        if platform == 'twitter':
            platform_username = response.get('screen_name', '')
        elif platform == 'facebook':
            platform_username = response.get('name', '')
        elif platform == 'instagram':
            platform_username = response.get('username', '')
        elif platform == 'github':
            platform_username = response.get('login', '')
        
        # Create or update social media account
        social_account, account_created = SocialMediaAccount.objects.get_or_create(
            user=user,
            platform=platform,
            defaults={
                'platform_user_id': uid,
                'platform_username': platform_username,
                'access_token': kwargs.get('access_token', ''),
            }
        )
        
        if not account_created:
            # Update existing account
            social_account.platform_user_id = uid
            social_account.platform_username = platform_username
            social_account.access_token = kwargs.get('access_token', '')
            social_account.is_active = True
            social_account.save()
        
        # Log the account connection
        ActivityLog.objects.create(
            user=user,
            action='account_connected',
            description=f'Connected {platform} account: {platform_username}'
        )
        
        # Update profile with additional information if available
        if created and response:
            if platform == 'github' and not profile.bio:
                profile.bio = response.get('bio', '')
            elif platform == 'facebook' and not profile.location:
                location = response.get('location', {})
                if isinstance(location, dict):
                    profile.location = location.get('name', '')
            
            profile.save()


def check_for_existing_account(strategy, details, user=None, *args, **kwargs):
    """
    Check if an account with the same email already exists.
    """
    email = details.get('email')
    if email:
        existing_users = User.objects.filter(email=email)
        if existing_users.exists() and user not in existing_users:
            # Email is already associated with another account
            raise AuthAlreadyAssociated(
                strategy.backend,
                'This email address is already associated with another account.'
            )


def create_user_with_social_data(strategy, details, backend, user=None, *args, **kwargs):
    """
    Create user with social data if user doesn't exist.
    """
    if user:
        return {'is_new': False}
    
    fields = {
        'email': details.get('email', ''),
        'first_name': details.get('first_name', ''),
        'last_name': details.get('last_name', ''),
    }
    
    # Clean up fields
    fields = {k: v for k, v in fields.items() if v}
    
    if not fields.get('email'):
        # Generate a placeholder email if none provided
        username = details.get('username', 'user')
        fields['email'] = f"{username}@{backend.name}.local"
    
    user = strategy.create_user(**fields)
    return {
        'is_new': True,
        'user': user
    }