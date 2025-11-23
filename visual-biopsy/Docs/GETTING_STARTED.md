# 🚀 Getting Started - Haptic Histology

## Welcome! 👋

This guide will get your **Haptic Histology** system running in **under 10 minutes**.

---

## ⚡ Super Quick Start

### Option 1: Automatic (Recommended)

```bash
cd visual-biopsy

# Linux/Mac:
./start.sh

# Windows:
start.bat
```

That's it! The script will:
-  Check Python installation
-  Install dependencies
-  Detect Arduino automatically
-  Launch the application

### Option 2: Manual Setup

```bash
# 1. Install Python packages
pip install -r visual-biopsy/linux_brain/requirements.txt

# 2. Upload Arduino firmware
# Open mcu_reflex/mcu_reflex.ino in Arduino IDE and upload

# 3. Run the application
cd visual-biopsy/linux_brain
python3 haptic_scanner.py
```

---

## 📋 Prerequisites

### Required Hardware
- ✅ Computer (Linux/Mac/Windows)
- ✅ Arduino UNO Q (or compatible board)
- ✅ USB cable

### Optional Hardware
- Haptic motor (vibration motor)
- Rotary encoder
- Force sensor

**Don't have hardware?** No problem! Run in **demo mode** with LED visualization.

### Required Software
- Python 3.8 or higher
- Arduino IDE (for firmware upload)

---

## 🔧 First-Time Setup

### Step 1: Check Python
```bash
python3 --version
# Should show: Python 3.8.x or higher
```

**Don't have Python?** Download from [python.org](https://www.python.org/downloads/)

### Step 2: Install Dependencies
```bash
cd visual-biopsy/linux_brain
pip install -r requirements.txt
```

This installs:
- `pygame` - Graphics and input
- `opencv-python` - Image processing
- `numpy` - Numerical computing
- `scikit-learn` - K-Means ML
- `pyserial` - Arduino communication

### Step 3: Upload Firmware

1. **Download Arduino IDE**
   - Get it from: https://www.arduino.cc/en/software

2. **Open the firmware**
   - File → Open → `visual-biopsy/mcu_reflex/mcu_reflex.ino`

3. **Select your board**
   - Tools → Board → Arduino UNO R4 WiFi (or your board)

4. **Select the port**
   - Tools → Port → (Select your Arduino)
   - Mac: `/dev/cu.usbmodem*`
   - Linux: `/dev/ttyACM0`
   - Windows: `COM3` or `COM4`

5. **Upload**
   - Click the Upload button (→) or press Ctrl+U
   - Wait for "Done uploading"

6. **Verify**
   - Watch for **3 quick LED blinks** (startup signal)

### Step 4: Configure Serial Port

**Find your port:**

```bash
# Linux/Mac:
ls /dev/tty* | grep -E "USB|ACM"

# Windows: Check Device Manager → Ports
```

**Update configuration:**

Edit `linux_brain/haptic_scanner.py` (line 31):
```python
serial_port: str = '/dev/ttyACM0'  # ← Change this to your port
```

### Step 5: Test Everything

```bash
cd visual-biopsy/linux_brain
python3 test_system.py
```

This checks:
- ✅ Python packages installed
- ✅ K-Means working
- ✅ Serial port detected
- ✅ File structure correct

**All green?** You're ready! 🎉

---

## 🎮 First Run

### Launch the application:
```bash
cd visual-biopsy/linux_brain
python3 haptic_scanner.py
```

### What you'll see:

```
============================================================
HAPTIC HISTOLOGY: 4D DIAGNOSTIC SCANNER
============================================================
✓ Loaded MRI scan: data/mri_scan.jpg
🧠 Training K-Means tissue segmentation model...
✓ Segmentation complete. Cluster mapping:
  Air/Fluid: Cluster 0 -> Haptic 0
  Soft Tissue: Cluster 1 -> Haptic 80
  Dense/Tumor: Cluster 2 -> Haptic 255
✓ Connected to MCU on /dev/ttyACM0
✓ MCU handshake successful
✓ MCU mode set to: TEXTURE
============================================================
✓ System ready. Move cursor over scan to feel tissue density.
  [SPACE] Toggle AI overlay
  [1-4]   Change haptic mode
  [ESC]   Exit
============================================================
```

### What to do:

1. **Move your mouse** over the window
2. **Feel the LED/motor respond** to tissue density
3. **Press SPACE** to see AI segmentation overlay
4. **Try different modes**:
   - Press `1` for DIRECT (simple)
   - Press `2` for TEXTURE (realistic)
   - Press `3` for TUMOR_LOCK (warning mode)
   - Press `4` for EDGE_DETECT (boundaries)

---

## 🎯 Understanding the Interface

### Visual Elements

```
┌─────────────────────────────────────────┐
│ [████████████░░░░░░░░░░░░] ← Haptic Bar │
│                                          │
│  FPS: 60                                 │
│  Position: (245, 312)                    │
│  Density: 255         ← Your values      │
│  Mode: TEXTURE                           │
│  MCU: CONNECTED                          │
│                                          │
│         🔴 ← Red = Tumor                │
│            ← Yellow = Normal             │
│                                          │
│  [MRI Scan Image]                        │
│                                          │
└─────────────────────────────────────────┘
```

### Color Overlay (Press SPACE)
- 🔵 **Dark Blue**: Air/Fluid (soft, haptic = 0)
- 🟢 **Green**: Soft Tissue (medium, haptic = 80)
- 🔴 **Red**: Dense/Tumor (hard, haptic = 255)

---

## 🧪 Test the Haptics

### LED Test (No Motor Required)

1. Run the application
2. Move cursor over white spots (tumors)
3. **LED should get brighter** over dense areas
4. **LED should dim** over dark areas

### Motor Test (If Connected)

1. Run calibration tool:
   ```bash
   python3 calibration_tool.py /dev/ttyACM0
   ```

2. Follow the prompts:
   - PWM sweep (0-255)
   - Mode testing
   - Interactive control

3. **Feel the difference**:
   - Low PWM = gentle vibration
   - High PWM = strong resistance

---

## 🐛 Common Issues

### "No module named 'pygame'"
```bash
pip install pygame
```

### "Serial port not found"
- Check USB cable
- Try different USB port
- Update serial_port in haptic_scanner.py
- Run `ls /dev/tty*` to find port

### "Permission denied" (Linux)
```bash
sudo usermod -a -G dialout $USER
# Then log out and back in
```

### "MCU handshake failed"
- Check firmware is uploaded
- Verify baud rate (115200)
- Press Arduino reset button
- Open Arduino Serial Monitor to test

### Image not loading
- Check `data/mri_scan.jpg` exists
- Or let it auto-generate (will create synthetic scan)

### Python version too old
```bash
# Install Python 3.8+
# macOS:
brew install python@3.11

# Linux:
sudo apt install python3.11

# Windows: Download from python.org
```

---

## 📚 Next Steps

### 1. Try Custom Images
```bash
# Place your MRI scan in data/
cp my_scan.jpg visual-biopsy/linux_brain/data/mri_scan.jpg

# Or specify path:
python3 haptic_scanner.py /path/to/scan.jpg
```

### 2. Add a Real Motor
- See `mcu_reflex/README.md` for wiring
- Use vibration motor or solenoid
- Connect via transistor (see circuit diagram)

### 3. Calibrate Your Hardware
```bash
python3 calibration_tool.py /dev/ttyACM0
```

### 4. Explore the Code
- `haptic_scanner.py` - Main application
- `mcu_reflex.ino` - Firmware
- `PROJECT_GUIDE.md` - Technical details

### 5. Contribute!
- Add new haptic modes
- Support DICOM images
- Improve ML algorithms
- Share your results!

---

## 🎓 Learn More

- **README.md** - Full project documentation
- **PROJECT_GUIDE.md** - Technical deep dive
- **mcu_reflex/README.md** - Hardware setup
- **GitHub Issues** - Ask questions

---

## ✅ Quick Checklist

Before running:
- [ ] Python 3.8+ installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Arduino firmware uploaded
- [ ] Serial port configured
- [ ] Test suite passed (`python3 test_system.py`)

All checked? **You're ready to go!** 🚀

---

## 🎉 Success!

If you see the MRI scan and can move the cursor around with the LED responding, **congratulations!** You've successfully built a **4D diagnostic haptic interface**.

Now experiment with:
- Different images
- Custom haptic modes
- Real motors
- Clinical applications

---

## 📞 Need Help?

- **Quick questions**: GitHub Discussions
- **Bug reports**: GitHub Issues
- **Hardware help**: See mcu_reflex/README.md
- **Email**: [Add contact]

---

**Happy Hacking!** 🔬✨

*Built with ❤️ for the medical community*
