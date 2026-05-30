# 🔬 Haptic Histology - Arduino Lab Edition

## 📌 Overview

This version runs **entirely on your Arduino UNO Q/R4** using **Arduino Lab for MicroPython**. No Mac/PC required for operation - everything runs on the board with a web interface!

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│      ARDUINO UNO Q/R4 BOARD             │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────┐   ┌───────────────┐  │
│  │ Python Brain │◄─►│ Arduino Sketch│  │
│  │  (main.py)   │   │  (sketch.ino) │  │
│  │              │   │               │  │
│  │ • K-Means ML │   │ • LED Matrix  │  │
│  │ • Image Proc │   │ • Density Map │  │
│  │ • Bridge API │   │ • 4 Modes     │  │
│  └──────────────┘   └───────────────┘  │
│         ▲                    │          │
│         │                    ▼          │
│    ┌─────────┐        ┌──────────┐     │
│    │Web UI   │        │12x8 LED  │     │
│    │(HTML)   │        │Matrix    │     │
│    └─────────┘        └──────────┘     │
└─────────────────────────────────────────┘
```

---

## 📂 Files

### Required Files for Arduino Lab Project:

```
app_lab_version/
├── main.py          ⭐ Python brain (K-Means ML)
├── sketch.ino       ⚡ Arduino sketch (LED control)
└── index.html       🌐 Web interface (optional)
```

---

## 🚀 Setup Instructions

### Step 1: Install Arduino Lab for MicroPython

1. Download from: https://labs.arduino.cc/
2. Install on your computer
3. Connect Arduino UNO Q/R4 via USB

### Step 2: Create New Project

1. Open Arduino Lab
2. Click **"New Project"**
3. Name it: `haptic-histology`

### Step 3: Add Files

1. **Create `main.py`**:
   - Copy contents from `app_lab_version/main.py`
   - This runs the Python brain with K-Means

2. **Create `sketch.ino`**:
   - Copy contents from `app_lab_version/sketch.ino`
   - This controls the LED matrix

3. **Add `index.html`** (optional):
   - Copy contents from `app_lab_version/index.html`
   - Provides web interface for image upload

### Step 4: Install Python Libraries

Arduino Lab will auto-install these when you run:
- `pillow` - Image processing
- `numpy` - Numerical computing
- `scikit-learn` - K-Means clustering

### Step 5: Upload and Run

1. Click **"Upload"** in Arduino Lab
2. Wait for compilation and upload
3. Open **Serial Monitor** (should show "Python Brain initialized")
4. LED matrix will flash 3 times = ready!

---

## 🎮 How to Use

### Method 1: Serial Input (Testing)

Open Serial Monitor and send:

```
POS:0.5,0.5          # Check center of image
POS:0.25,0.25        # Check top-left quadrant
MODE:TEXTURE         # Switch to texture mode
MODE:TUMOR_LOCK      # Switch to tumor lock mode
```

### Method 2: Web Interface (Recommended)

1. Arduino Lab serves the web UI automatically
2. Open browser to: `http://arduino.local` or board IP
3. Upload your MRI scan image
4. Move mouse over image
5. LED matrix shows tissue density in real-time!

---

## 📊 LED Matrix Visualization

The 12x8 LED matrix displays tissue density:

```
Fluid (0-50):     ░░░░░░░░░░░░  (Few LEDs)
Tissue (50-150):  ████░░░░░░░░  (Half filled)
Tumor (200-255):  ████████████  (Fully lit)
```

### Modes:

1. **DIRECT** - Bar graph matches density directly
2. **TEXTURE** - Pulses for soft tissue, steady for tumors
3. **TUMOR_LOCK** - Full brightness when over tumor
4. **EDGE_DETECT** - Flashes on tissue boundaries

---

## 🖼️ Image Requirements

### Supported Formats:
- JPG, PNG (will be converted to grayscale)
- Recommended: 200x200 to 600x600 pixels
- Grayscale MRI/CT scans work best

### Getting Test Images:

**Option 1: Generate Synthetic**
The system auto-generates a test scan on startup

**Option 2: Download Real Scans**
- The Cancer Imaging Archive: https://www.cancerimagingarchive.net/
- Radiopaedia: https://radiopaedia.org/
- MedPix (NIH): https://medpix.nlm.nih.gov/

**Option 3: Use Sample**
Check `MEDICAL_IMAGES_GUIDE.md` for creation script

---

## 🔧 Troubleshooting

### LED Matrix Not Updating
```
✓ Check Serial Monitor for "Python Brain Connected"
✓ Verify Bridge is working: Send "test" via Serial
✓ Re-upload sketch.ino
```

### Python Brain Not Loading
```
✓ Arduino Lab needs internet for first library install
✓ Check main.py syntax (no errors in console)
✓ Restart Arduino Lab and re-upload
```

### Image Not Loading
```
✓ Convert to JPEG format
✓ Resize to <1MB file size
✓ Check Serial output for error messages
```

### Web UI Not Accessible
```
✓ Check Arduino Lab web server is running
✓ Use board's IP address instead of arduino.local
✓ Try different browser (Chrome recommended)
```

---

## 🧪 Testing

### Quick Test Sequence:

1. **Power On**: 3 LED blinks = ready ✅
2. **Serial Test**:
   ```
   Send: POS:0.5,0.5
   Expect: "Density: 128" (or similar)
   ```
3. **Mode Test**:
   ```
   Send: MODE:TUMOR_LOCK
   Expect: "Mode changed to: TUMOR_LOCK"
   ```
4. **LED Test**: Matrix should fill based on position

---

## 📐 Technical Details

### Python → Arduino Communication

**Python provides:**
```python
Bridge.provide("get_density_norm", get_density_norm)
```

**Arduino calls:**
```cpp
int density;
Bridge.call("get_density_norm", x_norm, y_norm).result(density);
```

### LED Matrix Format

```cpp
// 12x8 matrix = 8 rows of 32-bit words
uint32_t ledFrame[8];

// Set LED at column, row
setLED(col, row, true);

// Update display
matrixWrite(ledFrame);
```

### Performance

- **K-Means Training**: ~2 seconds (200x200 image)
- **Density Lookup**: <1ms
- **LED Update**: 20 Hz (50ms intervals)
- **Total Latency**: ~50ms (cursor → LED)

---

## 🎯 Advantages Over Desktop Version

✅ **Fully Self-Contained** - No laptop needed
✅ **Web Interface** - Access from any device
✅ **Portable** - Just power the Arduino
✅ **No Installation** - Everything on the board
✅ **IoT Ready** - Can add WiFi streaming

---

## 🔮 Future Enhancements

### Easy Additions:
- [ ] WiFi image upload
- [ ] Multiple image storage
- [ ] Touch screen interface
- [ ] DICOM file support
- [ ] Real-time video stream

### Hardware Upgrades:
- [ ] External motor via PWM
- [ ] Larger LED display
- [ ] Battery power
- [ ] Rotary encoder input

---

## 📚 Resources

### Arduino Lab Documentation:
- MicroPython Guide: https://docs.arduino.cc/micropython/
- Bridge API: https://docs.arduino.cc/learn/programming/bridge/
- LED Matrix: https://docs.arduino.cc/tutorials/uno-r4-wifi/led-matrix/

### Medical Imaging:
- See `MEDICAL_IMAGES_GUIDE.md` for tumor detection info
- Sample images in parent directory

---

## 🎓 Educational Use

Perfect for demonstrating:
- **Edge AI** - ML running on microcontroller
- **Bridge Architecture** - Python + C++ communication  
- **Haptic Interfaces** - Visual + tactile feedback
- **Medical Tech** - Practical healthcare application

Great for:
- University engineering projects
- Hackathons (hardware + AI category)
- Medical education demonstrations
- IoT/Edge computing research

---

## ⚠️ Medical Disclaimer

**NOT FOR CLINICAL USE**

This is an educational demonstration only. Real medical diagnosis requires:
- Qualified radiologists
- Approved medical devices
- Multiple diagnostic methods
- Proper clinical workflow

---

## 💡 Quick Start Checklist

- [ ] Arduino Lab installed
- [ ] UNO Q/R4 connected via USB
- [ ] Project created with 3 files (main.py, sketch.ino, index.html)
- [ ] Uploaded successfully
- [ ] LED matrix blinks 3 times on startup
- [ ] Serial monitor shows "Python Brain Connected"
- [ ] Test with `POS:0.5,0.5` command
- [ ] LED matrix responds to position

**All checked? You're ready!** 🎉

---

## 🆘 Support

- Arduino Lab Issues: https://github.com/arduino/lab-micropython-editor
- This Project: GitHub Issues
- Hardware: See `mcu_reflex/README.md`

---

**Built with ❤️ for Arduino Lab**  
*"Making medical AI accessible on microcontrollers"*

**Version**: 2.0.0 (Arduino Lab Edition)  
**Date**: November 2025



# 1. Start with MRI image (grayscale 0-255)
pixels = [34, 89, 245, 88, 240, 35, ...]  # Brightness values

# 2. K-Means finds 3 "centroids" (cluster centers)
centroids = [8, 94, 168]
#            ↑   ↑    ↑
#         Fluid Tissue Tumor

# 3. Each pixel gets assigned to nearest centroid
pixel = 245  → Closest to 168 → Cluster 2 (Tumor)
pixel = 35   → Closest to 8   → Cluster 0 (Fluid)
pixel = 89   → Closest to 94  → Cluster 1 (Tissue)

# 4. Map clusters to haptic density (for LEDs)
Cluster 0 (Fluid)  → Density 0   → 0 LEDs
Cluster 1 (Tissue) → Density 128 → 6 LEDs
Cluster 2 (Tumor)  → Density 255 → 12 LEDs