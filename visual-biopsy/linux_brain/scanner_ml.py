import pygame
import cv2
import serial
import numpy as np
from sklearn.cluster import KMeans

# --- CONFIG ---
SERIAL_PORT = '/dev/ttyS0'  # Check your port!
BAUD_RATE = 115200
IMAGE_PATH = 'data/mri_scan.jpg' # Make sure this file exists

# --- 1. SERIAL CONNECTION ---
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
    print(f"Connected to MCU on {SERIAL_PORT}")
except:
    print("DEMO MODE: No Serial Port Found")
    ser = None

# --- 2. IMAGE PREP ---
print("Loading MRI Scan...")
img_original = cv2.imread(IMAGE_PATH, cv2.IMREAD_GRAYSCALE)
if img_original is None:
    print("Error: Image not found.")
    exit()

# Resize for performance (K-Means is slow on 4K images)
img_small = cv2.resize(img_original, (400, 400)) 
h, w = img_small.shape

# --- 3. THE AI (K-MEANS) ---
print("Training K-Means Model (finding tumors)...")

# Flatten image to 1D array of pixels for the AI
# Shape changes from (400, 400) -> (160000, 1)
pixel_data = img_small.reshape(-1, 1)

# Fit the model with 3 clusters (Air, Tissue, Tumor)
kmeans = KMeans(n_clusters=3, random_state=42)
kmeans.fit(pixel_data)

# --- 4. THE "HAPTIC SORTING" TRICK ---
# Get the center brightness of each cluster (e.g., [10, 150, 240])
centers = kmeans.cluster_centers_.flatten()

# We need to know which cluster ID corresponds to "Dark", "Med", "Bright"
# argsort() gives us the indices that would sort the array
sorted_indices = np.argsort(centers)

# Create a lookup map: 
# If a pixel belongs to the Darkest Cluster -> Output 0
# If a pixel belongs to the Medium Cluster  -> Output 80
# If a pixel belongs to the Brightest Cluster -> Output 255
haptic_values = {}
haptic_values[sorted_indices[0]] = 0    # Lowest intensity
haptic_values[sorted_indices[1]] = 80   # Medium intensity
haptic_values[sorted_indices[2]] = 255  # Max intensity (Tumor)

print("Tissue Segmentation Complete.")
print(f"Cluster Map: {haptic_values}")

# Predict labels for the whole image at once to create a "Haptic Map"
labels = kmeans.labels_
# Map every label to its haptic value
haptic_map_flat = [haptic_values[label] for label in labels]
# Reshape back to 2D image
haptic_map = np.array(haptic_map_flat).reshape(h, w).astype(np.uint8)


# --- 5. PYGAME VISUALIZATION ---
pygame.init()
screen = pygame.display.set_mode((w, h))
pygame.display.set_caption("AI Haptic Segmentation")

# Create a visual overlay of the clusters (Colorizing the output)
# We make a color version just for the screen
overlay_img = np.zeros((h, w, 3), dtype=np.uint8)
# Color Code: Dark=Black, Med=Green, Bright=Red
colors = {
    sorted_indices[0]: [0, 0, 0],      # Air
    sorted_indices[1]: [0, 255, 0],    # Tissue
    sorted_indices[2]: [255, 0, 0]     # Tumor
}
# Apply colors
label_matrix = labels.reshape(h, w)
for r in range(h):
    for c in range(w):
        cluster_id = label_matrix[r, c]
        overlay_img[r, c] = colors[cluster_id]

# Convert for Pygame
surf_original = pygame.surfarray.make_surface(np.rot90(np.stack((img_small,)*3, axis=-1)))
surf_ai = pygame.surfarray.make_surface(np.rot90(overlay_img))

mode = "AI" # Toggle between Original and AI view

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                mode = "ORIGINAL" if mode == "AI" else "AI"

    # Mouse Tracking
    mx, my = pygame.mouse.get_pos()
    
    # Send Data to Arduino Q
    if 0 <= mx < w and 0 <= my < h:
        # Look up the pre-calculated haptic value
        # Note: haptic_map is (row, col) so (my, mx)
        intensity = haptic_map[my, mx]
        
        if ser:
            ser.write(f"{intensity}\n".encode())
            
    # Rendering
    if mode == "AI":
        screen.blit(surf_ai, (0,0))
    else:
        screen.blit(surf_original, (0,0))

    # Draw Cursor
    pygame.draw.circle(screen, (255, 255, 0), (mx, my), 8, 1)
    
    # UI Text
    pygame.display.set_caption(f"Mode: {mode} | Haptic Force: {intensity}")
    
    pygame.display.flip()

pygame.quit()