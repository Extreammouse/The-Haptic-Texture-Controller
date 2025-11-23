import pygame
import cv2
import serial
import numpy as np

# --- CONFIG ---
# SERIAL_PORT = '/dev/ttyS0' # Internal Bridge
SERIAL_PORT = 'COM3'  # Windows
BAUD_RATE = 115200

# --- SETUP SERIAL ---
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
except:
    print("Warning: No Serial Device Found (Running in Demo Mode)")
    ser = None

# --- SETUP IMAGE processing ---
# Load image in grayscale (0-255)
image_path = 'data/mri_scan.jpg' 
img_cv = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
if img_cv is None:
    print(f"Error: Could not load {image_path}. Please download a dummy MRI image.")
    exit()

# Resize for the demo window (e.g., 600x600)
img_cv = cv2.resize(img_cv, (600, 600))
h, w = img_cv.shape

# --- PYGAME WINDOW ---
pygame.init()
screen = pygame.display.set_mode((w, h))
pygame.display.set_caption("Haptic Histology - Virtual Scanner")

# Convert CV2 image to Pygame Surface
# We stack grayscale to RGB because Pygame needs 3 channels
img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_GRAY2RGB)
# Rotate because Pygame and CV2 handle axes differently
img_rgb = np.rot90(img_rgb)
img_surf = pygame.surfarray.make_surface(img_rgb)
img_surf = pygame.transform.flip(img_surf, True, False) # Fix final orientation

running = True
print("--- SCROLL OVER THE WHITE SPOTS (TUMORS) ---")

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 1. Get Mouse Position
    mouse_x, mouse_y = pygame.mouse.get_pos()
    
    # 2. Safety Check (Stay inside window)
    if 0 <= mouse_x < w and 0 <= mouse_y < h:
        
        # 3. LEVEL 1: READ PIXEL DENSITY
        # Get the brightness value (0-255) at this coordinate
        tissue_density = int(img_cv[mouse_y, mouse_x])
        
        # 4. LEVEL 2: EDGE DETECTION (Optional "Buzz")
        # Check surrounding pixels to see if we are on an edge
        # Simple gradient calculation
        if mouse_x < w-1:
            next_pixel = int(img_cv[mouse_y, mouse_x+1])
            gradient = abs(tissue_density - next_pixel)
            
            # If gradient is high, we hit an edge! 
            # Boost the feedback for a "Click" feeling
            if gradient > 50: 
                tissue_density = 255 

        # 5. Send to Arduino Q (The Muscle)
        if ser:
            msg = f"{tissue_density}\n"
            ser.write(msg.encode('utf-8'))
            
        # VISUAL DEBUG: Print to console
        # print(f"Pos: {mouse_x},{mouse_y} | Density: {tissue_density}")

    # --- RENDER ---
    screen.blit(img_surf, (0, 0))
    
    # Draw the "Scanner Cursor"
    pygame.draw.circle(screen, (255, 0, 0), (mouse_x, mouse_y), 10, 2)
    
    # Show "Haptic Force" visual bar
    pygame.draw.rect(screen, (0, 255, 0), (10, 10, tissue_density, 20))
    
    pygame.display.flip()

pygame.quit()