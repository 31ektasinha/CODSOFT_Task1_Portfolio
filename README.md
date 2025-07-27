# Social Media Dashboard

A comprehensive Django-based social media dashboard that allows users to manage their social media presence across multiple platforms from a unified interface.

## 🌟 Features

### User Authentication & Profile Management
- **User Registration & Login**: Secure authentication with email verification
- **Profile Management**: Extended user profiles with avatars, bio, and social links
- **Social Authentication**: Login with Twitter, Facebook, Instagram, and GitHub
- **Activity Logging**: Track user activities and interactions

### Social Media Integration
- **Multi-Platform Support**: Connect and manage Twitter, Facebook, Instagram, and GitHub accounts
- **Post Synchronization**: Automatically fetch and sync posts from connected platforms
- **Real-time Updates**: Keep engagement metrics updated across platforms
- **Secure Token Management**: Safely store and manage OAuth tokens

### Content Management
- **Unified Post Feed**: View all posts from different platforms in one place
- **Post Interactions**: Like, comment, and share posts directly from the dashboard
- **Content Filtering**: Filter posts by platform, date, or engagement metrics
- **Post Search**: Full-text search across all your social media content

### Scheduling & Automation
- **Cross-Platform Posting**: Compose and publish posts to multiple platforms simultaneously
- **Post Scheduling**: Schedule posts for optimal engagement times
- **Background Processing**: Automated posting using Celery task queue
- **Retry Logic**: Automatic retry for failed posts with intelligent error handling

### Analytics & Insights
- **Engagement Analytics**: Track likes, comments, shares, and reach across platforms
- **Performance Metrics**: Analyze post performance and engagement rates
- **Platform Comparison**: Compare performance across different social media platforms
- **Trend Analysis**: Identify trending hashtags and content patterns
- **Visual Charts**: Interactive charts and graphs for data visualization

### API & Extensibility
- **REST API**: Comprehensive RESTful API for all functionality
- **API Documentation**: Auto-generated API documentation
- **Webhook Support**: Real-time updates via webhooks
- **Plugin Architecture**: Extensible design for adding new platforms

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Redis (for Celery background tasks)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd social-media-dashboard
   ```

2. **Run the setup script**
   ```bash
   python setup.py
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start the development server**
   ```bash
   source social_media_env/bin/activate
   cd social_media_dashboard
   python manage.py runserver
   ```

5. **Start background workers (in separate terminals)**
   ```bash
   # Celery worker
   celery -A social_media_dashboard worker --loglevel=info
   
   # Celery beat (for scheduled tasks)
   celery -A social_media_dashboard beat --loglevel=info
   ```

## 📖 Detailed Setup

### Environment Configuration

Create a `.env` file in the project root with the following variables:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DATABASE_URL=sqlite:///db.sqlite3

# Social Media API Keys
TWITTER_CONSUMER_KEY=your-twitter-consumer-key
TWITTER_CONSUMER_SECRET=your-twitter-consumer-secret
FACEBOOK_APP_ID=your-facebook-app-id
FACEBOOK_APP_SECRET=your-facebook-app-secret
INSTAGRAM_CLIENT_ID=your-instagram-client-id
INSTAGRAM_CLIENT_SECRET=your-instagram-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True
```

### Social Media API Setup

#### Twitter API
1. Create a Twitter Developer account at https://developer.twitter.com/
2. Create a new app and get your API keys
3. Add the keys to your `.env` file

#### Facebook API
1. Go to https://developers.facebook.com/
2. Create a new app and configure Facebook Login
3. Add your app credentials to `.env`

#### Instagram API
1. Instagram uses Facebook's API (Instagram Basic Display)
2. Set up through Facebook Developers console
3. Configure Instagram Basic Display product

#### GitHub API
1. Go to GitHub Settings > Developer settings > OAuth Apps
2. Create a new OAuth App
3. Add client ID and secret to `.env`

## 🏗️ Project Structure

```
social_media_dashboard/
├── accounts/                 # User authentication and profiles
│   ├── models.py            # User profile, social accounts
│   ├── views.py             # Authentication views
│   ├── forms.py             # User forms
│   └── pipeline.py          # Social auth pipeline
├── dashboard/               # Main dashboard interface
│   ├── views.py             # Dashboard views
│   └── urls.py              # Dashboard URLs
├── social_media/            # Social media integration
│   ├── models.py            # Posts, comments, metrics
│   ├── services.py          # API integration services
│   ├── tasks.py             # Celery background tasks
│   └── admin.py             # Admin interface
├── api/                     # REST API
│   ├── views.py             # API views
│   ├── serializers.py       # DRF serializers
│   └── urls.py              # API URLs
├── templates/               # HTML templates
├── static/                  # Static files (CSS, JS)
├── media/                   # User uploads
└── requirements.txt         # Python dependencies
```

## 🎯 Usage

### Connecting Social Media Accounts

1. **Navigate to Account Settings**
   - Go to Profile > Connected Accounts
   - Click "Connect" next to your desired platform

2. **OAuth Authorization**
   - You'll be redirected to the platform's authorization page
   - Grant necessary permissions
   - You'll be redirected back to the dashboard

3. **Account Management**
   - View connected accounts
   - Disconnect accounts when needed
   - Monitor token expiration status

### Creating and Scheduling Posts

1. **Compose New Post**
   - Click "Compose" in the dashboard
   - Write your content (supports hashtags and mentions)
   - Select target platforms
   - Add images or links if desired

2. **Schedule for Later**
   - Choose "Schedule" option
   - Select date and time
   - Posts will be automatically published

3. **Immediate Posting**
   - Click "Post Now" to publish immediately
   - Monitor posting results in real-time

### Analytics and Insights

1. **Dashboard Overview**
   - View key metrics at a glance
   - See recent activity and engagement
   - Monitor scheduled posts

2. **Detailed Analytics**
   - Go to Analytics section
   - Filter by date range and platform
   - Export reports as needed

3. **Performance Tracking**
   - Track engagement rates
   - Identify top-performing content
   - Monitor follower growth

## 🔧 API Documentation

### Authentication
All API endpoints require authentication. Use session authentication or token authentication.

### Endpoints

#### Posts
- `GET /api/posts/` - List user's posts
- `POST /api/posts/` - Create new post
- `GET /api/posts/{id}/` - Get specific post
- `PUT /api/posts/{id}/` - Update post
- `DELETE /api/posts/{id}/` - Delete post

#### Scheduled Posts
- `GET /api/scheduled-posts/` - List scheduled posts
- `POST /api/scheduled-posts/` - Create scheduled post
- `GET /api/scheduled-posts/{id}/` - Get scheduled post
- `PUT /api/scheduled-posts/{id}/` - Update scheduled post
- `DELETE /api/scheduled-posts/{id}/` - Cancel scheduled post

#### Analytics
- `GET /api/dashboard/stats/` - Get dashboard statistics
- `GET /api/analytics/` - Get detailed analytics data

#### Utilities
- `POST /api/sync/` - Trigger social media sync
- `GET /api/platforms/` - Get available platforms
- `GET /api/users/search/` - Search users

### Example API Usage

```python
import requests

# Get dashboard stats
response = requests.get(
    'http://localhost:8000/api/dashboard/stats/',
    headers={'Authorization': 'Token your-token-here'}
)
stats = response.json()

# Create a scheduled post
post_data = {
    'content': 'Hello from the API!',
    'platforms': ['twitter', 'facebook'],
    'scheduled_time': '2024-01-15T15:30:00Z'
}
response = requests.post(
    'http://localhost:8000/api/scheduled-posts/',
    json=post_data,
    headers={'Authorization': 'Token your-token-here'}
)
```

## 🔒 Security Considerations

### API Security
- All API endpoints are authenticated
- Rate limiting implemented
- CORS properly configured
- Input validation and sanitization

### Social Media Tokens
- Tokens encrypted at rest
- Secure token refresh mechanism
- Token expiration monitoring
- Secure OAuth implementation

### User Data Protection
- GDPR compliance features
- Data export functionality
- Account deletion with data cleanup
- Activity logging for audit trails

## 🚀 Deployment

### Production Setup

1. **Environment Variables**
   ```bash
   DEBUG=False
   ALLOWED_HOSTS=yourdomain.com
   SECRET_KEY=production-secret-key
   ```

2. **Database**
   - Use PostgreSQL for production
   - Configure backup strategies
   - Set up connection pooling

3. **Static Files**
   - Configure WhiteNoise for static files
   - Use CDN for media files
   - Implement proper caching

4. **Background Tasks**
   - Deploy Redis for Celery
   - Use supervisor for process management
   - Configure monitoring and logging

5. **Web Server**
   - Use Gunicorn with Nginx
   - Configure SSL certificates
   - Set up load balancing if needed

### Docker Deployment

```dockerfile
# Example Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "social_media_dashboard.wsgi:application"]
```

## 🧪 Testing

### Running Tests
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test accounts
python manage.py test social_media

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

### Test Structure
- Unit tests for models and services
- Integration tests for API endpoints
- End-to-end tests for user workflows
- Performance tests for background tasks

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/new-platform-integration
   ```
3. **Make your changes**
4. **Add tests for new functionality**
5. **Submit a pull request**

### Code Style
- Follow PEP 8 guidelines
- Use type hints where appropriate
- Write comprehensive docstrings
- Maintain test coverage above 80%

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Common Issues

**Issue: Celery tasks not running**
- Ensure Redis is running
- Check Celery worker logs
- Verify CELERY_BROKER_URL in settings

**Issue: Social media authentication failing**
- Verify API credentials in .env
- Check callback URLs in platform settings
- Ensure proper scopes/permissions

**Issue: Database migration errors**
- Delete migration files and recreate
- Check for circular dependencies
- Ensure proper field types

### Getting Help

- **Documentation**: Check the docs for detailed guides
- **Issues**: Create GitHub issues for bugs
- **Discussions**: Use GitHub discussions for questions
- **Email**: Contact support for urgent issues

## 🗺️ Roadmap

### Upcoming Features
- [ ] LinkedIn integration
- [ ] TikTok API support
- [ ] Advanced scheduling with AI optimization
- [ ] Team collaboration features
- [ ] Enhanced analytics with ML insights
- [ ] Mobile app for iOS and Android
- [ ] Integration with Google Analytics
- [ ] Advanced content calendar
- [ ] Automated content generation
- [ ] Social listening features

### Version History
- **v1.0.0** - Initial release with core features
- **v1.1.0** - Added scheduling and analytics
- **v1.2.0** - API improvements and new platforms
- **v2.0.0** - Major UI overhaul and performance improvements

---

**Built with ❤️ using Django, Celery, and modern web technologies.**
