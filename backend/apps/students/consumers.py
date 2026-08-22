"""
WebSocket consumers for real-time recommendation updates.
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class RecommendationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time recommendation status updates.
    
    Frontend connects to: ws://localhost:8000/ws/recommendations/
    """
    
    async def connect(self):
        self.user = self.scope['user']
        
        # Only allow authenticated users
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Create a user-specific channel group
        self.group_name = f'recommendations_{self.user.id}'
        
        # Join the group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'WebSocket connected',
            'user_id': str(self.user.id)
        }))
    
    async def disconnect(self, close_code):
        # Leave the group
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle messages from WebSocket client"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            # Echo back for testing
            await self.send(text_data=json.dumps({
                'type': 'echo',
                'data': data,
                'message': 'Message received'
            }))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
    
    # Handler methods for different event types
    async def recommendation_status(self, event):
        """Send recommendation status update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'recommendation_status',
            'submission_id': event.get('submission_id'),
            'status': event.get('status'),
            'progress': event.get('progress', 0),
            'message': event.get('message', ''),
        }))
    
    async def recommendation_complete(self, event):
        """Send completed recommendation to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'recommendation_complete',
            'submission_id': event.get('submission_id'),
            'recommendations': event.get('recommendations'),
        }))


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time general notifications.
    
    Frontend connects to: ws://localhost:8000/ws/notifications/
    """
    
    async def connect(self):
        self.user = self.scope['user']
        
        # Only allow authenticated users
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Create a user-specific channel group for notifications
        self.group_name = f'notifications_{self.user.id}'
        
        # Join the group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Notification WebSocket connected',
            'user_id': str(self.user.id)
        }))
    
    async def disconnect(self, close_code):
        # Leave the group
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle messages from WebSocket client"""
        try:
            data = json.loads(text_data)
            # Process notification acknowledgments or other client messages
            await self.send(text_data=json.dumps({
                'type': 'ack',
                'message': 'Notification acknowledged'
            }))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
    
    # Handler methods for different notification types
    async def system_notification(self, event):
        """Send system notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'system_notification',
            'title': event.get('title'),
            'message': event.get('message'),
            'level': event.get('level', 'info'),  # info, warning, error, success
            'timestamp': event.get('timestamp'),
        }))
    
    async def user_notification(self, event):
        """Send user-specific notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'user_notification',
            'title': event.get('title'),
            'message': event.get('message'),
            'action_url': event.get('action_url'),
            'read': event.get('read', False),
            'timestamp': event.get('timestamp'),
        }))

