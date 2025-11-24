# SPDX-FileCopyrightText: Copyright (C) 2025 Haptic Histology Team
# SPDX-License-Identifier: MPL-2.0

"""
Haptic Histology - Python Brain (Arduino Lab Version)
Runs K-Means segmentation on Arduino UNO Q/R4
Provides tissue density via bridge to Arduino sketch
"""

from arduino.app_utils import *
from arduino.app_bricks.web_ui import WebUI
import io
import base64

try:
    from PIL import Image
except ImportError:
    print("Installing PIL...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'pillow'])
    from PIL import Image


class SimpleKMeans:
    """Lightweight K-Means for embedded systems (no sklearn needed)"""
    
    def __init__(self, n_clusters=3, max_iters=10):
        self.n_clusters = n_clusters
        self.max_iters = max_iters
        self.centroids = None
    
    def fit(self, data):
        """Fit K-Means on grayscale data (1D array)"""
        # Initialize centroids evenly across range
        min_val, max_val = min(data), max(data)
        step = (max_val - min_val) / (self.n_clusters - 1)
        self.centroids = [min_val + i * step for i in range(self.n_clusters)]
        
        for _ in range(self.max_iters):
            # Assign points to nearest centroid
            clusters = [[] for _ in range(self.n_clusters)]
            for val in data:
                distances = [abs(val - c) for c in self.centroids]
                cluster_idx = distances.index(min(distances))
                clusters[cluster_idx].append(val)
            
            # Update centroids
            new_centroids = []
            for i, cluster in enumerate(clusters):
                if len(cluster) > 0:
                    new_centroids.append(sum(cluster) / len(cluster))
                else:
                    new_centroids.append(self.centroids[i])
            
            self.centroids = new_centroids
        
        # Sort centroids (Fluid < Tissue < Tumor)
        self.centroids.sort()
        return self
    
    def predict(self, value):
        """Predict cluster for a single value"""
        distances = [abs(value - c) for c in self.centroids]
        return distances.index(min(distances))


class TissueAnalyzer:
    """K-Means based tissue density analyzer"""
    
    def __init__(self):
        self.haptic_map = None
        self.image_width = 0
        self.image_height = 0
        self.trained = False
        
    def load_and_train(self, image_data: str):
        """
        Load image from base64 string and train K-Means
        
        Args:
            image_data: Base64 encoded image string
        """
        try:
            # Decode base64 image
            img_bytes = base64.b64decode(image_data)
            img = Image.open(io.BytesIO(img_bytes))
            
            # Convert to grayscale
            img_gray = img.convert('L')
            
            # Resize for processing (smaller = faster)
            img_resized = img_gray.resize((200, 200), Image.Resampling.LANCZOS)
            self.image_width, self.image_height = img_resized.size
            
            # Convert to list of pixel values
            pixels = list(img_resized.getdata())
            
            # Train K-Means (3 clusters: Fluid, Tissue, Tumor)
            self.kmeans = SimpleKMeans(n_clusters=3, max_iters=10)
            self.kmeans.fit(pixels)
            
            # Create haptic map - map cluster indices to density values
            # Centroids are sorted: [dark, medium, bright]
            cluster_to_density = {
                0: 0,     # Dark cluster -> Fluid
                1: 128,   # Medium cluster -> Tissue  
                2: 255    # Bright cluster -> Tumor
            }
            
            # Build 2D haptic map
            self.haptic_map = []
            for y in range(self.image_height):
                row = []
                for x in range(self.image_width):
                    idx = y * self.image_width + x
                    pixel_val = pixels[idx]
                    cluster = self.kmeans.predict(pixel_val)
                    density = cluster_to_density[cluster]
                    row.append(density)
                self.haptic_map.append(row)
            
            self.trained = True
            print(f"✓ Trained on {self.image_width}x{self.image_height} image")
            print(f"  Centroids: {[int(c) for c in self.kmeans.centroids]}")
            
            return "success"
            
        except Exception as e:
            print(f"Error loading image: {e}")
            return f"error: {str(e)}"
    
    def get_density_at(self, x: int, y: int) -> int:
        """
        Get tissue density at pixel coordinates
        
        Args:
            x: X coordinate (0 to image_width)
            y: Y coordinate (0 to image_height)
            
        Returns:
            Density value (0-255)
        """
        if not self.trained or self.haptic_map is None:
            return 0
        
        # Bounds check
        x = max(0, min(x, self.image_width - 1))
        y = max(0, min(y, self.image_height - 1))
        
        return int(self.haptic_map[y][x])
    
    def get_density_normalized(self, x_norm: float, y_norm: float) -> int:
        """
        Get density using normalized coordinates (0.0 to 1.0)
        Useful for web UI where canvas size may differ from image
        
        Args:
            x_norm: X position as fraction (0.0 = left, 1.0 = right)
            y_norm: Y position as fraction (0.0 = top, 1.0 = bottom)
            
        Returns:
            Density value (0-255)
        """
        if not self.trained:
            return 0
        
        x = int(x_norm * self.image_width)
        y = int(y_norm * self.image_height)
        
        return self.get_density_at(x, y)
    
    def get_image_info(self) -> dict:
        """Get information about loaded image"""
        return {
            'width': self.image_width,
            'height': self.image_height,
            'trained': self.trained
        }


# Initialize analyzer
analyzer = TissueAnalyzer()

# Global state for sharing with Arduino
current_density = 0
current_mode = "DIRECT"


# Bridge functions for Arduino sketch

def load_image(image_base64: str) -> str:
    """Load and train on medical image"""
    return analyzer.load_and_train(image_base64)


def get_density(x: int, y: int) -> int:
    """Get tissue density at pixel position"""
    return analyzer.get_density_at(x, y)


def get_density_norm(x_norm: float, y_norm: float) -> int:
    """Get tissue density using normalized coordinates (0.0-1.0)"""
    return analyzer.get_density_normalized(x_norm, y_norm)


def get_info() -> str:
    """Get image information as JSON string"""
    import json
    return json.dumps(analyzer.get_image_info())


def test_system() -> str:
    """Test function to verify bridge is working"""
    return "Haptic Histology Brain Online - K-Means Ready"


# Socket message handlers for WebUI

def on_load_image(client, data):
    """Handle image upload from web interface"""
    if 'image' in data:
        result = analyzer.load_and_train(data['image'])
        ui.send_message('image_loaded', {'status': result})
        return result
    return "error: no image data"

def on_get_density(client, data):
    """Handle density request from web UI"""
    global current_density
    if 'x' in data and 'y' in data:
        density = analyzer.get_density_normalized(data['x'], data['y'])
        prev = current_density
        current_density = density  # Store for Arduino to poll
        
        # Only log when density changes significantly (reduce spam)
        if abs(density - prev) > 10:
            print(f"[WebUI → Python] Position ({data['x']:.2f}, {data['y']:.2f}) → Density: {density} (was {prev})")
        
        ui.send_message('density_update', {'density': density, 'x': data['x'], 'y': data['y']})
        return density
    return 0

def on_set_mode(client, data):
    """Handle mode change from web UI"""
    global current_mode
    if 'mode' in data:
        current_mode = data['mode']  # Store for Arduino to read
        ui.send_message('mode_changed', {'mode': data['mode']})
        return f"Mode set to {data['mode']}"
    return "error: no mode specified"

# Functions Arduino can call to get current state

def get_current_density() -> int:
    """Arduino polls this to get latest density"""
    # Log when Arduino actually calls this function
    print(f"[BRIDGE CALL] Arduino requested density: {current_density}")
    return current_density

def get_current_mode() -> str:
    """Arduino polls this to get current mode"""
    return current_mode


# Provide functions to Arduino sketch
print("[BRIDGE] Registering functions for Arduino...")
Bridge.provide("load_image", load_image)
Bridge.provide("get_density", get_density)
Bridge.provide("get_density_norm", get_density_norm)
Bridge.provide("get_info", get_info)
Bridge.provide("test_system", test_system)
Bridge.provide("get_current_density", get_current_density)
Bridge.provide("get_current_mode", get_current_mode)
print("[BRIDGE] ✓ All 7 functions registered")

# Initialize WebUI
ui = WebUI()

# Register socket message handlers
ui.on_message('load_image', on_load_image)
ui.on_message('get_density', on_get_density)
ui.on_message('set_mode', on_set_mode)

print("=" * 60)
print("🧠 HAPTIC HISTOLOGY - ARDUINO LAB EDITION")
print("=" * 60)
print("Python Brain initialized and ready")
print("WebUI server starting...")
print("Available functions:")
print("  - load_image(base64_data)")
print("  - get_density(x, y)")
print("  - get_density_norm(x_norm, y_norm)")
print("  - get_info()")
print("  - test_system()")
print("=" * 60)

# Run the app (this starts the web server)
App.run()
