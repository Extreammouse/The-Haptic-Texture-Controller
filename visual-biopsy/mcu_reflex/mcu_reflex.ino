/* 
 * PROJECT: Haptic Histology - The Muscle (Arduino UNO R4)
 * ROLE: High-frequency control loop for haptic feedback
 * FEATURES:
 *  - LED Matrix visualization of tissue density
 *  - 4D Texture Simulation (pulsing for soft tissue, locked for tumors)
 *  - Real-time edge detection feedback
 *  - Adaptive tissue rendering based on AI segmentation
 */

#include <Arduino_LED_Matrix.h>

// SERIAL CONFIGURATION
// For Arduino UNO R4:
//   - Use 'Serial' for USB communication
#define LINK_SERIAL Serial 

// LED MATRIX SETUP
Arduino_LED_Matrix matrix;

// HARDWARE PINS - Using built-in LED on pin 13 as backup
#define BACKUP_LED_PIN 13

// HAPTIC MODES
enum HapticMode {
  MODE_DIRECT,      // Simple 0-255 pass-through
  MODE_TEXTURE,     // Simulated tissue texture (pulsing)
  MODE_TUMOR_LOCK,  // High resistance on tumor detection
  MODE_EDGE_DETECT  // Vibration pulse on tissue boundaries
};

// GLOBAL STATE
HapticMode currentMode = MODE_TEXTURE;
int densityValue = 0;           // Current tissue density (0-255)
int prevDensityValue = 0;       // Previous value for edge detection
unsigned long lastUpdateTime = 0;
unsigned long pulsePhase = 0;   // For texture simulation

// CONFIGURATION
const int LOOP_FREQUENCY = 1000; // Target: 1kHz control loop
const int LOOP_PERIOD_MS = 1000 / LOOP_FREQUENCY;
const int TUMOR_THRESHOLD = 200; // Density above this = tumor
const int EDGE_THRESHOLD = 50;   // Gradient for edge detection

void setup() {
  // Initialize serial communication
  LINK_SERIAL.begin(115200);
  
  // Initialize LED Matrix
  matrix.begin();
  
  // Configure backup LED pin
  pinMode(BACKUP_LED_PIN, OUTPUT);
  pinMode(LED_BUILTIN, OUTPUT);
  
  // Startup sequence - "I'm alive" triple blink
  for (int i = 0; i < 3; i++) {
    digitalWrite(BACKUP_LED_PIN, HIGH);
    digitalWrite(LED_BUILTIN, HIGH);
    delay(200);
    digitalWrite(BACKUP_LED_PIN, LOW);
    digitalWrite(LED_BUILTIN, LOW);
    delay(200);
  }
  
  // Clear matrix
  matrix.clear();
  
  // Send ready signal to MPU
  LINK_SERIAL.println("MCU_READY");
}

void loop() {
  unsigned long currentTime = millis();
  
  // STEP 1: RECEIVE DATA FROM LINUX BRAIN
  if (LINK_SERIAL.available() > 0) {
    String command = LINK_SERIAL.readStringUntil('\n');
    command.trim();
    
    // Parse command format: "D:255" or "M:TEXTURE" or plain "255"
    if (command.startsWith("D:")) {
      // Density data
      prevDensityValue = densityValue;
      densityValue = command.substring(2).toInt();
      densityValue = constrain(densityValue, 0, 255);
    } 
    else if (command.startsWith("M:")) {
      // Mode change
      String modeStr = command.substring(2);
      if (modeStr == "DIRECT") currentMode = MODE_DIRECT;
      else if (modeStr == "TEXTURE") currentMode = MODE_TEXTURE;
      else if (modeStr == "TUMOR_LOCK") currentMode = MODE_TUMOR_LOCK;
      else if (modeStr == "EDGE_DETECT") currentMode = MODE_EDGE_DETECT;
      
      LINK_SERIAL.print("MODE_SET:");
      LINK_SERIAL.println(modeStr);
    }
    else if (command.length() > 0 && isDigit(command[0])) {
      // Legacy format: plain number
      prevDensityValue = densityValue;
      densityValue = command.toInt();
      densityValue = constrain(densityValue, 0, 255);
    }
  }
  
  // STEP 2: PROCESS HAPTIC FEEDBACK (1kHz loop)
  if (currentTime - lastUpdateTime >= LOOP_PERIOD_MS) {
    lastUpdateTime = currentTime;
    
    int hapticOutput = 0;
    bool edgeDetected = false;
    
    // Edge detection (works across all modes)
    int gradient = abs(densityValue - prevDensityValue);
    if (gradient > EDGE_THRESHOLD) {
      edgeDetected = true;
    }
    
    // Mode-specific processing
    switch (currentMode) {
      case MODE_DIRECT:
        // Simple pass-through
        hapticOutput = densityValue;
        break;
        
      case MODE_TEXTURE:
        // Simulate tissue "squishiness" with pulsing
        pulsePhase += 50; // Increment phase
        if (densityValue < 100) {
          // Soft tissue: gentle pulsing (5-10 Hz)
          int pulse = 20 * sin(pulsePhase * 0.01);
          hapticOutput = densityValue + pulse;
        } else if (densityValue < TUMOR_THRESHOLD) {
          // Medium tissue: subtle vibration (2-5 Hz)
          int pulse = 10 * sin(pulsePhase * 0.005);
          hapticOutput = densityValue + pulse;
        } else {
          // Tumor: solid, no pulsing
          hapticOutput = densityValue;
        }
        hapticOutput = constrain(hapticOutput, 0, 255);
        break;
        
      case MODE_TUMOR_LOCK:
        // LED at max brightness when tumor detected
        if (densityValue > TUMOR_THRESHOLD) {
          hapticOutput = 255; // Full brightness - tumor warning
        } else {
          hapticOutput = densityValue / 2; // Dimmer for normal tissue
        }
        break;
        
      case MODE_EDGE_DETECT:
        // Boost LED brightness on tissue boundaries
        if (edgeDetected) {
          hapticOutput = 255; // Sharp pulse on edge
        } else {
          hapticOutput = densityValue;
        }
        break;
    }
    
    // STEP 3: OUTPUT TO LEDs
    // Update backup LED with PWM
    analogWrite(BACKUP_LED_PIN, hapticOutput);
    analogWrite(LED_BUILTIN, hapticOutput);
    
    // Update LED Matrix - fill matrix based on density
    updateLEDMatrix(hapticOutput);
    
    // For TUMOR_LOCK mode, ensure full brightness
    if (currentMode == MODE_TUMOR_LOCK) {
      if (densityValue > TUMOR_THRESHOLD) {
        digitalWrite(BACKUP_LED_PIN, HIGH);
        digitalWrite(LED_BUILTIN, HIGH);
      }
    }
    
    // Debug output (can be disabled in production)
    // LINK_SERIAL.print("D:");
    // LINK_SERIAL.print(densityValue);
    // LINK_SERIAL.print(" O:");
    // LINK_SERIAL.println(hapticOutput);
  }
  
  // Prevent watchdog timeout on some boards
  yield();
}

// Function to update LED Matrix based on density
void updateLEDMatrix(int brightness) {
  // Map brightness (0-255) to number of LEDs to light (0-96)
  // Arduino UNO R4 has 12x8 LED matrix = 96 LEDs
  int numLEDs = map(brightness, 0, 255, 0, 96);
  
  uint8_t frame[96];  // 12x8 = 96 LEDs
  
  // Fill matrix proportionally
  for (int i = 0; i < 96; i++) {
    if (i < numLEDs) {
      frame[i] = 1;  // LED ON
    } else {
      frame[i] = 0;  // LED OFF
    }
  }
  
  // Update the matrix
  matrix.renderBitmap(frame, 8, 12);
}