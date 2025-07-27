#!/usr/bin/env python3
"""
Setup script for Social Media Dashboard Django project.
This script helps set up the project environment and dependencies.
"""

import os
import sys
import subprocess
import platform

def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully!")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during {description}: {e}")
        print(f"Command output: {e.stdout}")
        print(f"Error output: {e.stderr}")
        return None

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required.")
        sys.exit(1)
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")

def setup_virtual_environment():
    """Set up Python virtual environment."""
    if os.path.exists('social_media_env'):
        print("📁 Virtual environment already exists")
        return True
    
    return run_command(
        'python3 -m venv social_media_env',
        'Creating virtual environment'
    ) is not None

def install_dependencies():
    """Install Python dependencies."""
    # Determine the correct pip command based on OS
    if platform.system() == 'Windows':
        pip_cmd = 'social_media_env\\Scripts\\pip'
    else:
        pip_cmd = 'social_media_env/bin/pip'
    
    return run_command(
        f'{pip_cmd} install -r requirements.txt',
        'Installing Python dependencies'
    ) is not None

def setup_database():
    """Set up the database with initial migrations."""
    # Determine the correct python command based on OS
    if platform.system() == 'Windows':
        python_cmd = 'social_media_env\\Scripts\\python'
    else:
        python_cmd = 'social_media_env/bin/python'
    
    # Run migrations
    success = run_command(
        f'{python_cmd} manage.py makemigrations',
        'Creating database migrations'
    ) is not None
    
    if not success:
        return False
    
    return run_command(
        f'{python_cmd} manage.py migrate',
        'Applying database migrations'
    ) is not None

def create_superuser():
    """Create Django superuser."""
    if platform.system() == 'Windows':
        python_cmd = 'social_media_env\\Scripts\\python'
    else:
        python_cmd = 'social_media_env/bin/python'
    
    print("\n👤 Create a superuser account for admin access")
    print("You can skip this step by pressing Ctrl+C")
    
    try:
        subprocess.run(
            f'{python_cmd} manage.py createsuperuser',
            shell=True,
            check=True
        )
        print("✅ Superuser created successfully!")
        return True
    except subprocess.CalledProcessError:
        print("⚠️ Superuser creation skipped or failed")
        return False
    except KeyboardInterrupt:
        print("\n⚠️ Superuser creation skipped")
        return False

def collect_static_files():
    """Collect static files."""
    if platform.system() == 'Windows':
        python_cmd = 'social_media_env\\Scripts\\python'
    else:
        python_cmd = 'social_media_env/bin/python'
    
    return run_command(
        f'{python_cmd} manage.py collectstatic --noinput',
        'Collecting static files'
    ) is not None

def create_directories():
    """Create necessary directories."""
    directories = [
        'media/avatars',
        'media/posts/images',
        'media/scheduled/images',
        'static',
        'staticfiles',
        'logs'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"📁 Created directory: {directory}")
    
    return True

def copy_env_file():
    """Copy .env.example to .env if it doesn't exist."""
    if not os.path.exists('.env') and os.path.exists('.env.example'):
        import shutil
        shutil.copy('.env.example', '.env')
        print("✅ Created .env file from .env.example")
        print("⚠️ Please update .env file with your actual configuration")
        return True
    elif os.path.exists('.env'):
        print("📄 .env file already exists")
        return True
    else:
        print("⚠️ .env.example not found")
        return False

def main():
    """Main setup function."""
    print("🚀 Setting up Social Media Dashboard Django Project")
    print("=" * 50)
    
    # Check Python version
    check_python_version()
    
    # Navigate to project directory
    if os.path.exists('social_media_dashboard'):
        os.chdir('social_media_dashboard')
        print("📁 Changed to project directory")
    
    # Setup steps
    steps = [
        ("Copy environment file", copy_env_file),
        ("Create directories", create_directories),
        ("Setup virtual environment", setup_virtual_environment),
        ("Install dependencies", install_dependencies),
        ("Setup database", setup_database),
        ("Collect static files", collect_static_files),
    ]
    
    for step_name, step_function in steps:
        if not step_function():
            print(f"❌ Failed at step: {step_name}")
            print("🛑 Setup aborted")
            sys.exit(1)
    
    # Optional superuser creation
    create_superuser()
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed successfully!")
    print("\n📝 Next steps:")
    print("1. Update the .env file with your configuration")
    print("2. Add your social media API keys to .env")
    print("3. Start the development server:")
    
    if platform.system() == 'Windows':
        print("   social_media_env\\Scripts\\python manage.py runserver")
    else:
        print("   source social_media_env/bin/activate")
        print("   python manage.py runserver")
    
    print("\n4. For background tasks, start Celery worker:")
    print("   celery -A social_media_dashboard worker --loglevel=info")
    print("\n5. For scheduled tasks, start Celery beat:")
    print("   celery -A social_media_dashboard beat --loglevel=info")
    
    print("\n🌐 Access the application at: http://localhost:8000")
    print("🔧 Admin interface at: http://localhost:8000/admin")

if __name__ == "__main__":
    main()