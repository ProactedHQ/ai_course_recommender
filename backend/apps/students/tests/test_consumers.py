"""
Tests for WebSocket consumers.
Tests RecommendationConsumer and NotificationConsumer.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from apps.students.consumers import RecommendationConsumer, NotificationConsumer
import json
import pytest


@pytest.mark.asyncio
class RecommendationConsumerTestCase(TestCase):
    """Test RecommendationConsumer WebSocket"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test user"""
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    async def test_websocket_connection_without_auth(self):
        """Test WebSocket requires authentication"""
        communicator = WebsocketCommunicator(
            RecommendationConsumer.as_asgi(),
            "/ws/recommendations/"
        )
        
        # Should reject connection
        connected, _ = await communicator.connect()
        self.assertFalse(connected)
    
    async def test_websocket_connection_with_auth(self):
        """Test authenticated WebSocket connection"""
        # Create communicator with authenticated user
        communicator = WebsocketCommunicator(
            RecommendationConsumer.as_asgi(),
            "/ws/recommendations/"
        )
        communicator.scope['user'] = self.user
        
        # Should accept connection
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Should receive connection confirmation
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'connection_established')
        self.assertIn('user_id', response)
        
        # Close connection
        await communicator.disconnect()
    
    async def test_websocket_receive_message(self):
        """Test receiving messages via WebSocket"""
        communicator = WebsocketCommunicator(
            RecommendationConsumer.as_asgi(),
            "/ws/recommendations/"
        )
        communicator.scope['user'] = self.user
        
        await communicator.connect()
        
        # Skip connection message
        await communicator.receive_json_from()
        
        # Send a test message
        await communicator.send_json_to({
            'type': 'ping',
            'message': 'test'
        })
        
        # Should receive echo response
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'echo')
        
        await communicator.disconnect()


@pytest.mark.asyncio
class NotificationConsumerTestCase(TestCase):
    """Test NotificationConsumer WebSocket"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test user"""
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    async def test_notification_connection(self):
        """Test notification WebSocket connection"""
        communicator = WebsocketCommunicator(
            NotificationConsumer.as_asgi(),
            "/ws/notifications/"
        )
        communicator.scope['user'] = self.user
        
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Should receive connection confirmation
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'connection_established')
        self.assertIn('Notification WebSocket', response['message'])
        
        await communicator.disconnect()


# Non-async tests for channel layer functionality
class ChannelLayerTestCase(TestCase):
    """Test channel layer functionality"""
    
    def test_channel_layer_available(self):
        """Test that channel layer is configured"""
        from django.conf import settings
        
        if getattr(settings, 'REDIS_AVAILABLE', False):
            channel_layer = get_channel_layer()
            self.assertIsNotNone(channel_layer)
