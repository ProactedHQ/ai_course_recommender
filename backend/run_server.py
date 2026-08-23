#!/usr/bin/env python
"""
Smart server launcher for AI Course Recommender backend.
Automatically detects Redis availability and runs appropriate server:
- ASGI (Daphne) if Redis is available -> Full WebSocket support
- WSGI (Django runserver) if Redis is NOT available -> HTTP only

Usage: python run_server.py [host:port]
Default: 0.0.0.0:8000
"""
import os
import sys
import subprocess
import django
from dotenv import load_dotenv

load_dotenv()

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'course_recomeder_backend.settings')
django.setup()

from django.conf import settings


if __name__ == '__main__':
    # Get host and port from arguments or use defaults
    address = sys.argv[1] if len(sys.argv) > 1 else '0.0.0.0:8000'
    redis_available = getattr(settings, 'REDIS_AVAILABLE', False)
    
    print("=" * 70)
    print("AI Course Recommender Backend - Smart Server Launcher")
    print("=" * 70)
    
    if redis_available:
        redis_url = os.environ.get('REDIS_URL', '')
        redis_source = "Remote (Upstash)" if 'upstash' in redis_url or 'rediss://' in redis_url else "Local"
        
        print(f"🚀 Starting ASGI server (Daphne) with WebSocket support...")
        print(f"   Redis Connection: {redis_source}")
        print(f"   Server address: http://{address}")
        print(f"   WebSocket available at: ws://{address}/ws/")
        print("=" * 70)
        
        # Run Daphne (ASGI server)
        subprocess.run([
            sys.executable, '-m', 'daphne',
            '-b', address.split(':')[0],
            '-p', address.split(':')[1] if ':' in address else '8000',
            'course_recomeder_backend.asgi:application'
        ])
    else:
        print("🚀 Starting WSGI server (Django runserver)...")
        print(f"   Server address: http://{address}")
        print("   ⚠️  WebSocket support DISABLED (Redis not available)")
        print("   ℹ️   REST API fully functional")
        print("=" * 70)
        
        # Run Django development server
        subprocess.run([
            sys.executable, 'manage.py', 'runserver', address
        ])
