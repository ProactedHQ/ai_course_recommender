"""
Logging configuration for AI Course Recommender backend.
Provides structured logging for monitoring and debugging.
"""
import logging
import os
from pathlib import Path

# Get BASE_DIR
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Create logs directory if it doesn't exist
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)


def setup_logging():
    """
    Setup logging configuration for the application.
    Call this from settings.py
    """
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '[{levelname}] {asctime} {name} {module} {process:d} {thread:d} - {message}',
                'style': '{',
            },
            'simple': {
                'format': '[{levelname}] {asctime} - {message}',
                'style': '{',
            },
        },
        'filters': {
            'require_debug_true': {
                '()': 'django.utils.log.RequireDebugTrue',
            },
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'simple'
            },
            'file_general': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': LOGS_DIR / 'general.log',
                'maxBytes': 1024 * 1024 * 10,  # 10 MB
                'backupCount': 5,
                'formatter': 'verbose',
            },
            'file_error': {
                'level': 'ERROR',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': LOGS_DIR / 'error.log',
                'maxBytes': 1024 * 1024 * 10,  # 10 MB
                'backupCount': 5,
                'formatter': 'verbose',
            },
            'file_cache': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': LOGS_DIR / 'cache.log',
                'maxBytes': 1024 * 1024 * 5,  # 5 MB
                'backupCount': 3,
                'formatter': 'verbose',
            },
            'file_websocket': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': LOGS_DIR / 'websocket.log',
                'maxBytes': 1024 * 1024 * 5,  # 5 MB
                'backupCount': 3,
                'formatter': 'verbose',
            },
        },
        'loggers': {
            'django': {
                'handlers': ['console', 'file_general'],
                'level': 'INFO',
                'propagate': False,
            },
            'django.request': {
                'handlers': ['console', 'file_error'],
                'level': 'ERROR',
                'propagate': False,
            },
            'apps': {
                'handlers': ['console', 'file_general'],
                'level': 'INFO',
                'propagate': False,
            },
            'utils.cache_utils': {
                'handlers': ['console', 'file_cache'],
                'level': 'INFO',
                'propagate': False,
            },
            'students.consumers': {
                'handlers': ['console', 'file_websocket'],
                'level': 'INFO',
                'propagate': False,
            },
            'channels': {
                'handlers': ['console', 'file_websocket'],
                'level': 'INFO',
                'propagate': False,
            },
        },
        'root': {
            'handlers': ['console', 'file_general'],
            'level': 'INFO',
        },
    }
