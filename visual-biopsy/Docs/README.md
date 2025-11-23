# 🔬 Haptic Histology: The Virtual Texture Interface

**Restoring the sense of touch to digital medical imaging**

![Project Status](https://img.shields.io/badge/status-prototype-orange)
![Hardware](https://img.shields.io/badge/hardware-Arduino%20UNO%20Q-blue)
![AI](https://img.shields.io/badge/AI-K--Means%20Clustering-green)

---

##  The Problem

For centuries, doctors diagnosed tumors through **palpation** — physically feeling for hard lumps, texture changes, and density variations. Modern medical imaging (MRI/CT) has made diagnosis more accurate, but **doctors have lost their sense of touch**. They can only look at pixels on a screen.

##  Our Solution

**Haptic Histology** is a Hardware-in-the-Loop (HIL) system that allows clinicians to **physically feel tissue density** while examining digital scans. When the cursor moves over a tumor, the haptic motor increases resistance. Over a fluid-filled cyst, it feels soft. This creates **"4D Diagnostics"** — adding the dimension of touch to visual medical data.

---

##  System Architecture

### Dual-Brain Design (Arduino UNO Q)

```
┌─────────────────────────────────────────────────────────────┐
│                    HAPTIC HISTOLOGY SYSTEM                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────┐         ┌─────────────────────┐   │
│  │   LINUX BRAIN       │         │   MCU MUSCLE        │   │
│  │  (Qualcomm MPU)     │◄───────►│   (STM32 MCU)       │   │
│  │                     │  Serial │                     │   │
│  │  • Python Runtime   │         │  • 1kHz Control Loop│   │
│  │  • K-Means ML       │         │  • PWM Generation   │   │
│  │  • Image Processing │         │  • Haptic Modes     │   │
│  │  • Pygame GUI       │         │  • Edge Detection   │   │
│  └─────────────────────┘         └─────────────────────┘   │
│           │                                │                 │
│           ▼                                ▼                 │
│  ┌─────────────────────┐         ┌─────────────────────┐   │
│  │   MRI/CT Scans      │         │  Haptic Motor       │   │
│  │   (DICOM/JPEG)      │         │  LED Indicator      │   │
│  └─────────────────────┘         └─────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow Pipeline

```
MRI Scan → K-Means Segmentation → Tissue Classification → Serial Protocol → MCU Processing → Haptic Output
   (jpg)      (3 clusters)         (0-255 density)        (115200 baud)     (1kHz PWM)      (motor/LED)
```

---

## 🧠 The AI: Unsupervised Learning

We use **K-Means Clustering** to segment medical images into tissue types **without any training data**:

1. **Input**: Grayscale MRI scan (0-255 pixel values)
2. **Processing**: K-Means groups pixels into 3 clusters based on brightness
3. **Classification**:
   - **Cluster 0** (Dark): Air/Fluid → Haptic value: `0` (soft)
   - **Cluster 1** (Medium): Soft Tissue → Haptic value: `80` (moderate)
   - **Cluster 2** (Bright): Dense/Tumor → Haptic value: `255` (hard)
4. **Output**: Real-time haptic map for instant feedback

### Why K-Means?

- ✅ **No training data required** — works on any scan
- ✅ **Runs on edge devices** — no cloud needed
- ✅ **Fast inference** — <100ms on Arduino UNO Q
- ✅ **Clinically relevant** — separates tissue types effectively

---

## 🎮 Haptic Feedback Modes

The MCU implements 4 distinct haptic modes:

### 1. **DIRECT Mode** (Key: `1`)
Simple pass-through of tissue density. Linear mapping from brightness to resistance.

### 2. **TEXTURE Mode** (Key: `2`) — *Default*
Simulates realistic tissue feel:
- **Soft tissue**: Gentle pulsing (5-10 Hz) to simulate squishiness
- **Medium tissue**: Subtle vibration (2-5 Hz)
- **Tumor**: Solid, no pulsing — feels "locked"

### 3. **TUMOR_LOCK Mode** (Key: `3`)
Provides maximum resistance when cursor is over a tumor (density > 200). Visual LED warning activates simultaneously.

### 4. **EDGE_DETECT Mode** (Key: `4`)
Sharp haptic pulse when crossing tissue boundaries. Helps identify tumor margins.

---

## 🚀 Getting Started

### Hardware Requirements

- **Arduino UNO Q** (or compatible dual-core board: Portenta H7, Giga R1)
- **Haptic motor** or vibration motor (optional — LED works for demo)
- **USB cable** for serial communication
- **Computer** running Linux/macOS/Windows

### Software Dependencies

#### Linux Brain (Python)
```bash
# Install Python dependencies
pip install pygame opencv-python numpy scikit-learn pyserial

# Or use the requirements file
pip install -r visual-biopsy/linux_brain/requirements.txt
```

#### MCU Muscle (Arduino)
1. Install [Arduino IDE](https://www.arduino.cc/en/software)
2. Open `visual-biopsy/mcu_reflex/mcu_reflex.ino`
3. Select your board (Tools → Board → Arduino UNO Q)
4. Upload the firmware

---

## 📦 Installation & Setup

### Step 1: Clone the Repository
```bash
git clone https://github.com/Extreammouse/The-Haptic-Texture-Controller.git
cd The-Haptic-Texture-Controller/visual-biopsy
```

### Step 2: Configure Serial Port

Edit `linux_brain/haptic_scanner.py`:
```python
@dataclass
class SystemConfig:
    serial_port: str = '/dev/ttyS0'  # Linux internal bridge
    # serial_port: str = '/dev/ttyACM0'  # Linux USB
    # serial_port: str = 'COM3'  # Windows
    # serial_port: str = '/dev/cu.usbmodem'  # macOS
```

Find your port:
- **Linux**: `ls /dev/tty*`
- **macOS**: `ls /dev/cu.*`
- **Windows**: Check Device Manager → Ports

### Step 3: Upload MCU Firmware

1. Open `mcu_reflex/mcu_reflex.ino` in Arduino IDE
2. Configure the serial interface:
   ```cpp
   #define LINK_SERIAL Serial   // For USB (laptop communication)
   // #define LINK_SERIAL Serial1  // For internal bridge (MPU communication)
   ```
3. Upload to your Arduino board

### Step 4: Run the System

```bash
cd linux_brain
python3 haptic_scanner.py

# Or with custom MRI scan:
python3 haptic_scanner.py /path/to/scan.jpg
```

---

## 🎯 Usage Guide

### Controls

| Key | Action |
|-----|--------|
| `SPACE` | Toggle AI segmentation overlay |
| `1` | Switch to DIRECT mode |
| `2` | Switch to TEXTURE mode |
| `3` | Switch to TUMOR_LOCK mode |
| `4` | Switch to EDGE_DETECT mode |
| `ESC` | Exit application |

### Workflow

1. **Start the application** — System auto-generates synthetic scan if none exists
2. **Wait for AI training** — K-Means processes the image (~2 seconds)
3. **Move cursor over scan** — Feel different tissue densities
4. **Toggle overlay** (SPACE) — See AI segmentation in real-time
5. **Switch modes** (1-4) — Experience different haptic profiles

### Visual Feedback

- **Green bar** (top-left): Current haptic force (0-255)
- **Yellow cursor**: Normal scanning
- **Red cursor**: Tumor detected (density > 200)
- **Color overlay**:
  - 🔵 **Blue**: Air/Fluid
  - 🟢 **Green**: Soft Tissue
  - 🔴 **Red**: Dense/Tumor

---

## 🔬 Clinical Applications

### Radiology
- **Tumor detection**: Feel suspicious masses while reviewing scans
- **Margin assessment**: Use edge detection to identify tumor boundaries
- **Density differentiation**: Distinguish calcifications from soft tissue

### Pathology
- **Virtual microscopy**: Apply haptic feedback to digital histology slides
- **Tissue classification**: Feel the difference between normal and abnormal cells

### Surgical Planning
- **Pre-operative assessment**: Understand tissue density before surgery
- **Navigation**: Combine with surgical robots for intraoperative guidance

### Medical Education
- **Training tool**: Teach students palpation skills on digital images
- **Remote learning**: Share haptic experiences over network

---

## 🧪 Technical Details

### Performance Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| **AI Inference** | <100ms | K-Means clustering time |
| **Serial Latency** | <10ms | 115200 baud, optimized protocol |
| **MCU Loop Rate** | 1000 Hz | Ensures smooth haptic response |
| **Display FPS** | 60 FPS | Pygame rendering |
| **Total Latency** | <50ms | Cursor to haptic feedback |

### Communication Protocol

**Python → MCU Commands:**
```
D:255\n          # Send density value (0-255)
M:TEXTURE\n      # Set haptic mode
```

**MCU → Python Responses:**
```
MCU_READY\n         # Startup handshake
MODE_SET:TEXTURE\n  # Mode confirmation
```

---

## 📂 Project Structure

```
The-Haptic-Texture-Controller/
├── README.md                          # This file
├── visual-biopsy/
│   ├── linux_brain/                   # MPU software (Python)
│   │   ├── haptic_scanner.py         # Main application (PRODUCTION)
│   │   ├── scanner.py                # Simple demo (legacy)
│   │   ├── scanner_ml.py             # ML-only demo (legacy)
│   │   ├── calibration_tool.py       # Hardware calibration utility
│   │   ├── requirements.txt          # Python dependencies
│   │   └── data/                     # MRI scan storage
│   │       └── mri_scan.jpg         # Auto-generated test image
│   └── mcu_reflex/                   # MCU firmware (Arduino C++)
│       └── mcu_reflex.ino            # Main firmware
└── LICENSE
```

---

## 🛠️ Development & Extensions

### Easy Additions
- [ ] Add 3D volume rendering (scroll through MRI slices)
- [ ] Support DICOM medical image format
- [ ] Network streaming (remote haptic feedback)
- [ ] Multi-actuator array (spatial haptic display)

### Hardware Upgrades
- Replace LED with haptic motor (vibration motor, solenoid)
- Add rotary encoder knob for realistic "scroll feel"
- Integrate with force-feedback joystick

---

## 📜 License

MIT License — See [LICENSE](LICENSE) for details

---

## 🙏 Acknowledgments

- **Arduino Team**: For the excellent UNO Q platform
- **scikit-learn**: K-Means implementation
- **OpenCV & Pygame**: Image processing and visualization
- **Medical community**: For inspiration from traditional palpation techniques

---

## 📧 Contact

- **Issues**: [GitHub Issues](https://github.com/Extreammouse/The-Haptic-Texture-Controller/issues)
- **Author**: @Extreammouse

---

**Built with ❤️ for the medical community**

*"Bringing back the human touch to digital medicine"*
