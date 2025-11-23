# MCU Firmware Setup Guide

## Hardware Configuration

### Pin Assignments (Arduino UNO Q)

```
Pin 9  (PWM) → Haptic Motor (+) via transistor
Pin 10 (PWM) → Vibration Motor (optional)
Pin 13 (LED) → Built-in LED (status indicator)
GND         → Motor ground & transistor emitter
5V          → Motor power supply (or external if needed)
```

### Recommended Motor Driver Circuit

```
                     +5V (or external motor supply)
                      |
                      |
                     [Motor]
                      |
                      |---→ Diode (flyback protection)
                      |
    Pin 9 ────R1───┤|  NPN Transistor (2N2222 or similar)
    (PWM)           └|
                      |
                     GND
                     
R1 = 1kΩ resistor
Diode = 1N4001 or similar (cathode to +5V)
```

### Safety Notes

⚠️ **Important:**
- Always use a flyback diode with inductive loads (motors)
- Don't drive motors directly from Arduino pins (max 40mA)
- Use external power supply for motors >100mA
- Add decoupling capacitors (100nF) across motor terminals

## Serial Configuration

### For USB Connection (Laptop)
```cpp
#define LINK_SERIAL Serial
```
Use this when running Python on your laptop connected via USB.

### For Internal Bridge (Arduino UNO Q Linux MPU)
```cpp
#define LINK_SERIAL Serial1
```
Use this when Python runs on the onboard Linux processor.

### Finding Your Port

**Linux:**
```bash
ls /dev/tty*
# Look for: /dev/ttyACM0, /dev/ttyUSB0, or /dev/ttyS0
```

**macOS:**
```bash
ls /dev/cu.*
# Look for: /dev/cu.usbmodem* or /dev/cu.usbserial*
```

**Windows:**
Open Device Manager → Ports (COM & LPT)
Look for: COM3, COM4, etc.

## Upload Instructions

### Arduino IDE

1. **Install Arduino IDE**
   - Download from: https://www.arduino.cc/en/software
   - Install for your OS

2. **Select Board**
   - Tools → Board → Arduino → Arduino UNO R4 WiFi (or your board)
   - For Arduino UNO Q: Select appropriate STM32 board

3. **Select Port**
   - Tools → Port → [Your detected port]

4. **Upload**
   - Click Upload button (→) or press Ctrl+U
   - Wait for "Done uploading" message

### Arduino CLI (Advanced)

```bash
# Install Arduino CLI
brew install arduino-cli  # macOS
# or download from: https://arduino.github.io/arduino-cli/

# Configure
arduino-cli config init

# Install board support
arduino-cli core install arduino:renesas_uno  # For UNO R4

# Compile
arduino-cli compile --fqbn arduino:renesas_uno:unor4wifi mcu_reflex.ino

# Upload
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:renesas_uno:unor4wifi mcu_reflex.ino
```

## Troubleshooting

### Upload Fails

**Error: Port not found**
- Check USB cable connection
- Try different USB port
- Install USB drivers (CH340/CP2102 if needed)

**Error: Permission denied (Linux)**
```bash
sudo usermod -a -G dialout $USER
# Log out and back in
```

### Serial Communication Issues

**No response from MCU**
- Check baud rate matches (115200)
- Verify correct serial port in Python
- Check RX/TX connections if using external serial
- Open Arduino Serial Monitor (115200 baud) to test

**Garbled data**
- Ensure baud rate matches on both sides
- Check for loose connections
- Verify ground connection

### Motor Not Working

**LED blinks but motor doesn't run**
- Check transistor connections
- Verify motor power supply
- Test motor separately with battery
- Check flyback diode orientation

**Motor runs erratically**
- Add capacitors (100nF) across motor terminals
- Use separate power supply for motor
- Reduce PWM frequency if needed

**Motor too weak**
- Increase PWM value in software
- Use higher voltage motor supply
- Check transistor can handle current

## Testing

### Basic LED Test
1. Upload firmware
2. Watch for triple blink on startup
3. Open Serial Monitor (115200 baud)
4. Type: `D:128` and press Enter
5. LED should light at ~50% brightness

### Motor Test
1. Connect motor circuit
2. Upload firmware
3. Run calibration tool:
   ```bash
   cd linux_brain
   python3 calibration_tool.py /dev/ttyACM0
   ```
4. Test all PWM values from 0-255

### Communication Test
1. Upload firmware
2. Open Serial Monitor
3. Check for "MCU_READY" message
4. Send commands:
   - `D:0` → Motor off
   - `D:128` → 50% power
   - `D:255` → 100% power
   - `M:TEXTURE` → Switch mode

## Haptic Mode Behavior

### DIRECT Mode
- Linear PWM output
- Value = Density (0-255)

### TEXTURE Mode
- Soft tissue (<100): Pulsing 5-10 Hz
- Medium (100-200): Subtle vibration 2-5 Hz
- Tumor (>200): Solid, no modulation

### TUMOR_LOCK Mode
- Density >200: Full power (255)
- Density ≤200: Half power
- LED turns ON when locked

### EDGE_DETECT Mode
- Sharp pulse (255) when gradient detected
- Optional vibration motor activates

## Performance Tuning

### Adjust Loop Frequency
```cpp
const int LOOP_FREQUENCY = 1000;  // Default: 1kHz
// Higher = smoother response, more CPU
// Lower = less responsive, less power
```

### Adjust Thresholds
```cpp
const int TUMOR_THRESHOLD = 200;  // Default
// Lower = more sensitive
// Higher = less sensitive

const int EDGE_THRESHOLD = 50;    // Default
// Lower = detect smaller edges
// Higher = only major boundaries
```

### PWM Frequency (Advanced)
```cpp
// In setup():
analogWriteFrequency(9, 1000);  // 1kHz PWM
// Higher = smoother motor, more EMI
// Lower = less smooth, less EMI
```

## Hardware Upgrades

### Add Rotary Encoder
```cpp
#define ENCODER_PIN_A 2
#define ENCODER_PIN_B 3

void setup() {
    pinMode(ENCODER_PIN_A, INPUT_PULLUP);
    pinMode(ENCODER_PIN_B, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(ENCODER_PIN_A), encoderISR, CHANGE);
}
```

### Add Force Sensor
```cpp
#define FORCE_SENSOR_PIN A0

int force = analogRead(FORCE_SENSOR_PIN);
// Use force to modulate haptic intensity
```

### Multi-Motor Array
```cpp
const int MOTOR_PINS[] = {9, 10, 11};  // 3 motors
for (int i = 0; i < 3; i++) {
    analogWrite(MOTOR_PINS[i], hapticOutput);
}
```

## Debugging

### Enable Debug Output
```cpp
// Uncomment in main loop:
LINK_SERIAL.print("D:");
LINK_SERIAL.print(densityValue);
LINK_SERIAL.print(" O:");
LINK_SERIAL.println(hapticOutput);
```

### Monitor Performance
```cpp
unsigned long loopTime = micros();
// ... control loop code ...
loopTime = micros() - loopTime;
LINK_SERIAL.print("Loop time: ");
LINK_SERIAL.print(loopTime);
LINK_SERIAL.println(" us");
```

## Resources

- **Arduino UNO Q Documentation**: [Link needed]
- **Haptic Motor Selection Guide**: [Link needed]
- **PWM Tutorial**: https://www.arduino.cc/en/Tutorial/PWM
- **Serial Communication**: https://www.arduino.cc/reference/en/language/functions/communication/serial/

## Support

For hardware issues:
- GitHub Issues: [Link]
- Arduino Forum: https://forum.arduino.cc/
- Haptic Motor Suppliers: Adafruit, Pololu, SparkFun
