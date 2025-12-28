"""
This file is deprecated - streaming functionality moved to live.py
"""
# Redirect imports if needed
from .live import router, video_stream, websocket_endpoint

__all__ = ['router', 'video_stream', 'websocket_endpoint']
