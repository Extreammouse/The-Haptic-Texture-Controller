#!/usr/bin/env python3
"""
Haptic Histology: The Linux Brain
==================================
Real-time K-Means segmentation + haptic feedback control

ARCHITECTURE:
- Unsupervised ML (K-Means) for tissue segmentation
- Hardware-in-the-Loop (HIL) communication with STM32 MCU
- Adaptive haptic modes based on tissue type
- Sub-10ms latency for clinical-grade responsiveness

Author: Haptic Histology Team
Date: November 2025
"""

import pygame
import cv2
import serial
import numpy as np
from sklearn.cluster import KMeans
import time
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Tuple
import json

# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class SystemConfig:
    """System-wide configuration parameters"""
    # Serial Communication
    serial_port: str = '/dev/cu.usbmodem20305080322'  # Change to COM3 on Windows, /dev/ttyACM0 on Linux
    baud_rate: int = 115200
    serial_timeout: float = 0.1
    
    # Image Processing
    image_path: str = 'data/mri_scan.jpg'
    display_size: Tuple[int, int] = (600, 600)
    ai_processing_size: Tuple[int, int] = (400, 400)  # Smaller for K-Means speed
    
    # Machine Learning
    n_clusters: int = 3  # Fluid, Tissue, Tumor
    kmeans_random_state: int = 42
    
    # Haptic Feedback
    haptic_mode: str = 'TEXTURE'  # DIRECT, TEXTURE, TUMOR_LOCK, EDGE_DETECT
    edge_detection_threshold: int = 50
    tumor_threshold: int = 200
    
    # Performance
    target_fps: int = 60
    ai_update_interval: int = 30  # Recompute K-Means every N frames (for dynamic images)
    
    # Visualization
    show_ai_overlay: bool = True
    show_debug_info: bool = True
    cursor_size: int = 10


# =============================================================================
# SERIAL COMMUNICATION LAYER
# =============================================================================

class MCUCommunicator:
    """Handles serial communication with STM32 MCU"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.serial: Optional[serial.Serial] = None
        self.demo_mode = False
        self.last_send_time = 0
        self.send_interval = 0.01  # 100Hz max send rate
        
    def connect(self) -> bool:
        """Establish serial connection with MCU"""
        try:
            self.serial = serial.Serial(
                self.config.serial_port, 
                self.config.baud_rate, 
                timeout=self.config.serial_timeout
            )
            print(f"✓ Connected to MCU on {self.config.serial_port}")
            
            # Wait for MCU ready signal
            start_time = time.time()
            while time.time() - start_time < 3:
                if self.serial.in_waiting:
                    response = self.serial.readline().decode('utf-8', errors='ignore').strip()
                    if response == "MCU_READY":
                        print("✓ MCU handshake successful")
                        return True
            
            print("⚠ MCU connected but no handshake received")
            return True
            
        except Exception as e:
            print(f"⚠ Serial connection failed: {e}")
            print("⚡ Running in DEMO MODE (no hardware)")
            self.demo_mode = True
            return False
    
    def send_density(self, density: int) -> None:
        """Send tissue density value to MCU"""
        current_time = time.time()
        if current_time - self.last_send_time < self.send_interval:
            return  # Rate limiting
            
        if self.serial and not self.demo_mode:
            try:
                message = f"D:{density}\n"
                self.serial.write(message.encode('utf-8'))
                self.last_send_time = current_time
            except Exception as e:
                print(f"Serial send error: {e}")
    
    def set_mode(self, mode: str) -> None:
        """Change haptic feedback mode"""
        if self.serial and not self.demo_mode:
            try:
                message = f"M:{mode}\n"
                self.serial.write(message.encode('utf-8'))
                print(f"✓ MCU mode set to: {mode}")
            except Exception as e:
                print(f"Mode change error: {e}")
    
    def disconnect(self):
        """Close serial connection"""
        if self.serial:
            self.serial.close()
            print("✓ Serial connection closed")


# =============================================================================
# TISSUE SEGMENTATION ENGINE
# =============================================================================

class TissueSegmenter:
    """K-Means based tissue classifier"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.kmeans: Optional[KMeans] = None
        self.haptic_map: Optional[np.ndarray] = None
        self.cluster_labels = ["Air/Fluid", "Soft Tissue", "Dense/Tumor"]
        self.haptic_values = {}
        
    def train(self, image: np.ndarray) -> None:
        """Train K-Means model on image"""
        print("🧠 Training K-Means tissue segmentation model...")
        
        # Resize for performance
        img_small = cv2.resize(image, self.config.ai_processing_size)
        h, w = img_small.shape
        
        # Flatten image to 1D array of pixels
        pixel_data = img_small.reshape(-1, 1).astype(np.float32)
        
        # Train K-Means
        self.kmeans = KMeans(
            n_clusters=self.config.n_clusters,
            random_state=self.config.kmeans_random_state,
            n_init=10
        )
        labels = self.kmeans.fit_predict(pixel_data)
        
        # Sort clusters by intensity (dark -> bright)
        centers = self.kmeans.cluster_centers_.flatten()
        sorted_indices = np.argsort(centers)
        
        # Map clusters to haptic intensities
        self.haptic_values = {
            sorted_indices[0]: 0,     # Darkest -> No resistance
            sorted_indices[1]: 80,    # Medium -> Moderate resistance
            sorted_indices[2]: 255    # Brightest -> Maximum resistance (tumor)
        }
        
        # Create haptic map
        haptic_map_flat = [self.haptic_values[label] for label in labels]
        self.haptic_map = np.array(haptic_map_flat).reshape(h, w).astype(np.uint8)
        
        # Resize haptic map to display size
        self.haptic_map = cv2.resize(
            self.haptic_map, 
            self.config.display_size,
            interpolation=cv2.INTER_NEAREST
        )
        
        print(f"✓ Segmentation complete. Cluster mapping:")
        for idx, (cluster_id, haptic_val) in enumerate(self.haptic_values.items()):
            print(f"  {self.cluster_labels[idx]}: Cluster {cluster_id} -> Haptic {haptic_val}")
    
    def get_haptic_value(self, x: int, y: int) -> int:
        """Get pre-computed haptic value at coordinate"""
        if self.haptic_map is None:
            return 0
        
        h, w = self.haptic_map.shape
        if 0 <= y < h and 0 <= x < w:
            return int(self.haptic_map[y, x])
        return 0
    
    def get_overlay_image(self) -> np.ndarray:
        """Generate color-coded segmentation overlay"""
        if self.haptic_map is None:
            return np.zeros((self.config.display_size[1], self.config.display_size[0], 3), dtype=np.uint8)
        
        overlay = np.zeros((self.haptic_map.shape[0], self.haptic_map.shape[1], 3), dtype=np.uint8)
        
        # Color mapping
        colors = {
            0: [0, 0, 50],        # Dark blue for fluid
            80: [0, 255, 0],      # Green for soft tissue
            255: [255, 0, 0]      # Red for tumor
        }
        
        for haptic_val, color in colors.items():
            mask = self.haptic_map == haptic_val
            overlay[mask] = color
        
        return overlay


# =============================================================================
# MAIN APPLICATION
# =============================================================================

class HapticHistologyScanner:
    """Main application controller"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.mcu = MCUCommunicator(config)
        self.segmenter = TissueSegmenter(config)
        
        # State variables
        self.running = True
        self.show_overlay = config.show_ai_overlay
        self.current_density = 0
        self.prev_density = 0
        self.frame_count = 0
        
        # Performance metrics
        self.fps = 0
        self.last_fps_update = time.time()
        
    def load_image(self) -> np.ndarray:
        """Load and prepare MRI scan image"""
        image_path = Path(self.config.image_path)
        
        if not image_path.exists():
            print(f"❌ Error: Image not found at {image_path}")
            print("💡 Generating synthetic MRI scan...")
            return self._generate_synthetic_scan()
        
        img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            print(f"❌ Error: Could not load {image_path}")
            return self._generate_synthetic_scan()
        
        print(f"✓ Loaded MRI scan: {image_path}")
        return img
    
    def _generate_synthetic_scan(self) -> np.ndarray:
        """Create a synthetic MRI scan for testing"""
        img = np.zeros((600, 600), dtype=np.uint8)
        
        # Background tissue
        img[:] = 80
        
        # Simulate tumor regions
        cv2.circle(img, (300, 300), 150, 100, -1)  # Soft tissue mass
        cv2.circle(img, (350, 280), 60, 255, -1)   # Dense tumor
        cv2.circle(img, (250, 320), 40, 255, -1)   # Second tumor
        cv2.circle(img, (150, 150), 50, 30, -1)    # Fluid-filled cyst
        
        # Add noise for realism
        noise = np.random.normal(0, 10, img.shape).astype(np.int16)
        img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        # Save for future use
        output_path = Path(self.config.image_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), img)
        print(f"✓ Synthetic scan saved to {output_path}")
        
        return img
    
    def initialize(self) -> bool:
        """Initialize all system components"""
        print("=" * 60)
        print("HAPTIC HISTOLOGY: 4D DIAGNOSTIC SCANNER")
        print("=" * 60)
        
        # Load image
        self.mri_image = self.load_image()
        self.mri_image = cv2.resize(self.mri_image, self.config.display_size)
        
        # Train AI model
        self.segmenter.train(self.mri_image)
        
        # Connect to MCU
        self.mcu.connect()
        self.mcu.set_mode(self.config.haptic_mode)
        
        # Initialize Pygame
        pygame.init()
        self.screen = pygame.display.set_mode(self.config.display_size)
        pygame.display.set_caption("Haptic Histology Scanner")
        self.clock = pygame.time.Clock()
        
        # Prepare display surfaces
        self._prepare_surfaces()
        
        print("=" * 60)
        print("✓ System ready. Move cursor over scan to feel tissue density.")
        print("  [SPACE] Toggle AI overlay")
        print("  [1-4]   Change haptic mode")
        print("  [ESC]   Exit")
        print("=" * 60)
        
        return True
    
    def _prepare_surfaces(self):
        """Prepare Pygame surfaces for rendering"""
        # Convert grayscale to RGB for pygame
        img_rgb = cv2.cvtColor(self.mri_image, cv2.COLOR_GRAY2RGB)
        self.mri_surface = pygame.surfarray.make_surface(np.rot90(img_rgb))
        
        # AI overlay
        overlay_rgb = self.segmenter.get_overlay_image()
        self.overlay_surface = pygame.surfarray.make_surface(np.rot90(overlay_rgb))
        self.overlay_surface.set_alpha(180)  # Semi-transparent
    
    def handle_input(self):
        """Process user input"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                
                elif event.key == pygame.K_SPACE:
                    self.show_overlay = not self.show_overlay
                    print(f"AI Overlay: {'ON' if self.show_overlay else 'OFF'}")
                
                # Mode switching
                elif event.key == pygame.K_1:
                    self._set_haptic_mode('DIRECT')
                elif event.key == pygame.K_2:
                    self._set_haptic_mode('TEXTURE')
                elif event.key == pygame.K_3:
                    self._set_haptic_mode('TUMOR_LOCK')
                elif event.key == pygame.K_4:
                    self._set_haptic_mode('EDGE_DETECT')
    
    def _set_haptic_mode(self, mode: str):
        """Change haptic feedback mode"""
        self.config.haptic_mode = mode
        self.mcu.set_mode(mode)
        print(f"🎯 Haptic Mode: {mode}")
    
    def process_haptic_feedback(self, mouse_x: int, mouse_y: int):
        """Calculate and send haptic feedback"""
        h, w = self.mri_image.shape
        
        if not (0 <= mouse_x < w and 0 <= mouse_y < h):
            return
        
        # Get base density from AI segmentation
        self.prev_density = self.current_density
        self.current_density = self.segmenter.get_haptic_value(mouse_x, mouse_y)
        
        # Edge detection boost (handled by MCU, but we can pre-process)
        if self.config.haptic_mode == 'EDGE_DETECT':
            gradient = abs(self.current_density - self.prev_density)
            if gradient > self.config.edge_detection_threshold:
                # Edge detected - MCU will handle the pulse
                pass
        
        # Send to MCU
        self.mcu.send_density(self.current_density)
    
    def render(self, mouse_x: int, mouse_y: int):
        """Render the display"""
        # Draw base image
        self.screen.blit(self.mri_surface, (0, 0))
        
        # Draw AI overlay if enabled
        if self.show_overlay:
            self.screen.blit(self.overlay_surface, (0, 0))
        
        # Draw cursor
        cursor_color = (255, 255, 0)  # Yellow
        if self.current_density > self.config.tumor_threshold:
            cursor_color = (255, 0, 0)  # Red for tumor
        
        pygame.draw.circle(self.screen, cursor_color, (mouse_x, mouse_y), 
                          self.config.cursor_size, 2)
        
        # Draw haptic force bar
        bar_width = int(self.current_density * 2)  # Scale to 0-510 pixels
        pygame.draw.rect(self.screen, (0, 255, 0), (10, 10, bar_width, 20))
        pygame.draw.rect(self.screen, (255, 255, 255), (10, 10, 510, 20), 1)
        
        # Debug info
        if self.config.show_debug_info:
            self._draw_debug_info(mouse_x, mouse_y)
        
        pygame.display.flip()
    
    def _draw_debug_info(self, mouse_x: int, mouse_y: int):
        """Draw debug information overlay"""
        font = pygame.font.Font(None, 24)
        
        info_lines = [
            f"FPS: {int(self.fps)}",
            f"Position: ({mouse_x}, {mouse_y})",
            f"Density: {self.current_density}",
            f"Mode: {self.config.haptic_mode}",
            f"MCU: {'CONNECTED' if not self.mcu.demo_mode else 'DEMO MODE'}"
        ]
        
        y_offset = 40
        for line in info_lines:
            text_surface = font.render(line, True, (255, 255, 255))
            # Black background for readability
            bg_rect = text_surface.get_rect()
            bg_rect.topleft = (10, y_offset)
            bg_rect.inflate_ip(10, 4)
            pygame.draw.rect(self.screen, (0, 0, 0), bg_rect)
            self.screen.blit(text_surface, (10, y_offset))
            y_offset += 25
    
    def update_fps(self):
        """Calculate and update FPS counter"""
        self.frame_count += 1
        current_time = time.time()
        
        if current_time - self.last_fps_update >= 1.0:
            self.fps = self.frame_count / (current_time - self.last_fps_update)
            self.frame_count = 0
            self.last_fps_update = current_time
    
    def run(self):
        """Main application loop"""
        if not self.initialize():
            return
        
        while self.running:
            # Handle input
            self.handle_input()
            
            # Get mouse position
            mouse_x, mouse_y = pygame.mouse.get_pos()
            
            # Process haptic feedback
            self.process_haptic_feedback(mouse_x, mouse_y)
            
            # Render
            self.render(mouse_x, mouse_y)
            
            # Update metrics
            self.update_fps()
            
            # Maintain target framerate
            self.clock.tick(self.config.target_fps)
        
        # Cleanup
        self.shutdown()
    
    def shutdown(self):
        """Clean shutdown"""
        print("\n Shutting down...")
        self.mcu.disconnect()
        pygame.quit()
        print("✓ Goodbye!")


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    """Application entry point"""
    # Load config (could be from JSON file in production)
    config = SystemConfig()
    
    # Override config from command line if needed
    if len(sys.argv) > 1:
        config.image_path = sys.argv[1]
    
    # Run application
    app = HapticHistologyScanner(config)
    try:
        app.run()
    except KeyboardInterrupt:
        print("\n⚠ Interrupted by user")
        app.shutdown()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        app.shutdown()


if __name__ == "__main__":
    main()
