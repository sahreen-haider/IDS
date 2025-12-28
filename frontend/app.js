// IDS Frontend Application

function idsApp() {
    return {
        // Configuration
        apiUrl: 'http://localhost:8000',
        videoUrl: 'http://localhost:8000/api/live/stream',
        
        // State
        activeTab: 'alerts',
        systemStatus: {
            running: false,
            camera_connected: false
        },
        stats: {
            fps: 0,
            detection_fps: 0,
            in_perimeter: 0,
            outside_perimeter: 0,
            detection_count: 0
        },
        alertStats: {
            total_alerts: 0,
            alerts_by_type: {},
            last_alert: 'None'
        },
        alerts: [],
        config: {
            camera: {},
            model: {},
            detection: {
                frame_skip: 2,
                inference_size: 416,
                enable_perimeter: true,
                perimeter_zone: []
            },
            alerts: {}
        },
        
        // Initialization
        async init() {
            console.log('Initializing IDS Frontend...');
            await this.checkHealth();
            await this.loadConfig();
            await this.loadAlerts();
            await this.loadStats();
            
            // Start polling for updates
            this.startPolling();
            
            // Add timestamp to video URL to prevent caching
            this.videoUrl = this.videoUrl + '?t=' + Date.now();
        },
        
        // API Methods
        async checkHealth() {
            try {
                const response = await fetch(`${this.apiUrl}/api/health`);
                const data = await response.json();
                this.systemStatus.running = data.detection_running;
                this.systemStatus.camera_connected = data.camera_connected;
            } catch (error) {
                console.error('Health check failed:', error);
                this.systemStatus.running = false;
                this.systemStatus.camera_connected = false;
            }
        },
        
        async loadConfig() {
            try {
                const response = await fetch(`${this.apiUrl}/api/config/`);
                this.config = await response.json();
            } catch (error) {
                console.error('Failed to load config:', error);
            }
        },
        
        async loadAlerts() {
            try {
                const response = await fetch(`${this.apiUrl}/api/alerts/?limit=10`);
                this.alerts = await response.json();
            } catch (error) {
                console.error('Failed to load alerts:', error);
                this.alerts = [];
            }
        },
        
        async loadStats() {
            try {
                // System stats
                const statsResponse = await fetch(`${this.apiUrl}/api/stats/system`);
                this.stats = await statsResponse.json();
                
                // Alert stats
                const alertStatsResponse = await fetch(`${this.apiUrl}/api/stats/alerts`);
                this.alertStats = await alertStatsResponse.json();
            } catch (error) {
                console.error('Failed to load stats:', error);
            }
        },
        
        async toggleDetection() {
            try {
                const endpoint = this.systemStatus.running ? 'stop' : 'start';
                const response = await fetch(`${this.apiUrl}/api/detection/${endpoint}`, {
                    method: 'POST'
                });
                
                if (response.ok) {
                    await this.checkHealth();
                    this.showNotification(`Detection ${endpoint}ed successfully`, 'success');
                } else {
                    this.showNotification(`Failed to ${endpoint} detection`, 'error');
                }
            } catch (error) {
                console.error('Failed to toggle detection:', error);
                this.showNotification('Failed to toggle detection', 'error');
            }
        },
        
        async saveConfig() {
            try {
                const response = await fetch(`${this.apiUrl}/api/config/detection`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(this.config.detection)
                });
                
                if (response.ok) {
                    this.showNotification('Configuration saved successfully', 'success');
                } else {
                    this.showNotification('Failed to save configuration', 'error');
                }
            } catch (error) {
                console.error('Failed to save config:', error);
                this.showNotification('Failed to save configuration', 'error');
            }
        },
        
        async savePerimeter() {
            try {
                const response = await fetch(`${this.apiUrl}/api/config/perimeter`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        perimeter_zone: this.config.detection.perimeter_zone,
                        enable: this.config.detection.enable_perimeter
                    })
                });
                
                if (response.ok) {
                    const result = await response.json();
                    // Update local config with server response to ensure sync
                    this.config.detection.perimeter_zone = result.perimeter_zone;
                    this.config.detection.enable_perimeter = result.enabled;
                    this.showNotification('Perimeter updated successfully', 'success');
                } else {
                    this.showNotification('Failed to update perimeter', 'error');
                }
            } catch (error) {
                console.error('Failed to save perimeter:', error);
                this.showNotification('Failed to update perimeter', 'error');
            }
        },
        
        async deleteAlert(alertId) {
            try {
                const response = await fetch(`${this.apiUrl}/api/alerts/${alertId}`, {
                    method: 'DELETE'
                });
                
                if (response.ok) {
                    await this.loadAlerts();
                    this.showNotification('Alert deleted', 'success');
                }
            } catch (error) {
                console.error('Failed to delete alert:', error);
            }
        },
        
        async clearAllAlerts() {
            if (!confirm('Are you sure you want to clear all alerts?')) return;
            
            try {
                const response = await fetch(`${this.apiUrl}/api/alerts/`, {
                    method: 'DELETE'
                });
                
                if (response.ok) {
                    await this.loadAlerts();
                    await this.loadStats();
                    this.showNotification('All alerts cleared', 'success');
                }
            } catch (error) {
                console.error('Failed to clear alerts:', error);
            }
        },
        
        // Helper Methods
        setPerimeter(preset) {
            const presets = {
                'full': [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]],
                'center': [[0.25, 0.25], [0.75, 0.25], [0.75, 0.75], [0.25, 0.75]],
                'bottom': [[0.0, 0.5], [1.0, 0.5], [1.0, 1.0], [0.0, 1.0]],
                'door': [[0.3, 0.0], [0.7, 0.0], [0.7, 1.0], [0.3, 1.0]]
            };
            
            this.config.detection.perimeter_zone = presets[preset];
            // Automatically enable perimeter when selecting a preset
            this.config.detection.enable_perimeter = true;
            this.showNotification(`${preset.charAt(0).toUpperCase() + preset.slice(1)} zone preset applied`, 'info');
        },
        
        async refreshData() {
            await this.checkHealth();
            await this.loadConfig();
            await this.loadAlerts();
            await this.loadStats();
            this.showNotification('Data refreshed', 'success');
        },
        
        startPolling() {
            // Poll stats every 2 seconds
            setInterval(async () => {
                if (this.systemStatus.running) {
                    await this.loadStats();
                }
            }, 2000);
            
            // Poll health every 5 seconds
            setInterval(async () => {
                await this.checkHealth();
            }, 5000);
            
            // Poll alerts every 10 seconds
            setInterval(async () => {
                await this.loadAlerts();
            }, 10000);
        },
        
        showNotification(message, type = 'info') {
            // Simple notification using alert for now
            // In production, use a proper toast notification library
            const colors = {
                'success': '✅',
                'error': '❌',
                'info': 'ℹ️'
            };
            
            console.log(`${colors[type]} ${message}`);
            
            // You can implement a toast notification here
            // For now, we'll use console logging
        }
    }
}
