"""
Configuration loader for IDS system
"""
import yaml
import os
from pathlib import Path
from typing import Dict, Any


class Config:
    """Configuration manager for IDS"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize configuration
        
        Args:
            config_path: Path to configuration YAML file
        """
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        return config
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        
        Args:
            key: Configuration key (e.g., 'camera.url')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    @property
    def camera_url(self) -> str:
        """Get camera URL"""
        return self.get('camera.url', 0)
    
    @property
    def camera_width(self) -> int:
        """Get camera width"""
        return self.get('camera.width', 1280)
    
    @property
    def camera_height(self) -> int:
        """Get camera height"""
        return self.get('camera.height', 720)
    
    @property
    def model_weights(self) -> str:
        """Get model weights path"""
        return self.get('model.weights', 'models/yolov8n.pt')
    
    @property
    def confidence_threshold(self) -> float:
        """Get confidence threshold"""
        return self.get('model.confidence_threshold', 0.5)
    
    @property
    def target_classes(self) -> list:
        """Get target detection classes"""
        return self.get('detection.target_classes', ['person'])
    
    @property
    def alert_cooldown(self) -> int:
        """Get alert cooldown period"""
        return self.get('detection.alert_cooldown', 30)
    
    @property
    def show_window(self) -> bool:
        """Whether to show display window"""
        return self.get('display.show_window', True)
