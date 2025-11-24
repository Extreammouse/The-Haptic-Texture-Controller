// SPDX-FileCopyrightText: Copyright (C) 2025 Haptic Histology Team
// SPDX-License-Identifier: MPL-2.0

/*
 * Haptic Histology - Arduino Lab Edition
 * LED Matrix shows tissue density from MRI scan
 * Runs entirely on Arduino UNO Q/R4 with Web UI
 */

#include <Arduino_RouterBridge.h>

// LED Matrix functions (provided by Arduino Lab)
extern "C" void matrixWrite(const uint32_t* buf);
extern "C" void matrixBegin();

// Global state
int currentDensity = 0;
int prevDensity = 0;
String currentMode = "DIRECT";

// Thresholds
const int TUMOR_THRESHOLD = 200;
const int EDGE_THRESHOLD = 50;

// LED Matrix buffer (12x8 = 96 bits, stored as 32-bit words)
uint32_t ledFrame[8];  // 8 rows of 32-bit words

void setup() {
  Serial.begin(115200);
  delay(1000);  // Wait for serial
  
  Serial.println("======================================");
  Serial.println("SKETCH STARTING...");
  Serial.println("======================================");
  
  matrixBegin();
  Serial.println("[INIT] LED Matrix initialized");
  
  Bridge.begin();
  Serial.println("[INIT] Bridge started");
  
  // Test Python brain
  String test_result;
  bool ok = Bridge.call("test_system").result(test_result);
  if (ok) {
    Serial.println("✓ Python Brain Connected: " + test_result);
  } else {
    Serial.println("⚠ Python Brain not responding");
    Serial.println("[ERROR] Bridge test failed!");
  }
  
  // Show startup animation
  Serial.println("[INIT] Starting LED animation...");
  flashMatrix(3);
  Serial.println("[INIT] Setup complete - entering loop");
}

void loop() {
  static unsigned long lastPoll = 0;
  static unsigned long lastHeartbeat = 0;
  static int loopCount = 0;
  unsigned long now = millis();
  
  // Heartbeat every 2 seconds to show Arduino is alive
  if (now - lastHeartbeat >= 2000) {
    Serial.print("[HEARTBEAT] Loop running, current density: ");
    Serial.println(currentDensity);
    lastHeartbeat = now;
  }
  
  // Poll Python for current density and mode (20 Hz for responsiveness)
  int density;
  String mode;
  
  bool densityOk = Bridge.call("get_current_density").result(density);
  bool modeOk = Bridge.call("get_current_mode").result(mode);
  
  // Debug: Always show what we got from Python
  if (loopCount % 20 == 0) {
    Serial.print("[POLL] Got from Python - Density: ");
    Serial.print(density);
    Serial.print(", Mode: ");
    Serial.print(mode);
    Serial.print(", Success: ");
    Serial.println(densityOk ? "YES" : "NO");
  }
  
  if (densityOk) {
    // Only update if density actually changed
    if (density != currentDensity) {
      prevDensity = currentDensity;
      currentDensity = density;
      
      Serial.print("[UPDATE] Density: ");
      Serial.print(currentDensity);
      Serial.print(" → LEDs: ");
      int numLEDs = map(currentDensity, 0, 255, 0, 12);
      Serial.print(numLEDs);
      Serial.println("/12");
      
      // Update LEDs immediately when density changes
      updateLEDMatrix(currentDensity);
    }
  } else {
    Serial.println("[ERROR] Failed to get density from Python!");
  }
  
  if (modeOk && mode != currentMode) {
    currentMode = mode;
    Serial.print("[Mode] Changed to: ");
    Serial.println(currentMode);
  }
  
  // Periodic refresh for mode effects (texture pulse, etc.)
  if (loopCount % 10 == 0) {
    updateLEDMatrix(currentDensity);
  }
  
  loopCount++;
  delay(50);  // 20 Hz polling rate
}

void updateDensityFromPosition(float x_norm, float y_norm) {
  // Call Python to get density at position
  int density;
  bool ok = Bridge.call("get_density_norm", x_norm, y_norm).result(density);
  
  if (ok) {
    prevDensity = currentDensity;
    currentDensity = density;
    
    Serial.print("Position (");
    Serial.print(x_norm, 2);
    Serial.print(", ");
    Serial.print(y_norm, 2);
    Serial.print(") -> Density: ");
    Serial.println(currentDensity);
  }
}

void updateLEDMatrix(int density) {
  // Apply haptic mode processing
  int displayValue = processDensity(density);
  
  // Map density (0-255) to number of LED columns (0-12)
  // 0 = no LEDs, 255 = all 12 columns lit
  
  // Clear frame
  for (int i = 0; i < 8; i++) {
    ledFrame[i] = 0;
  }
  
  // Calculate how many columns to light (0-12)
  int numCols = map(displayValue, 0, 255, 0, 12);
  
  // Clamp to valid range
  numCols = constrain(numCols, 0, 12);
  
  // Create vertical bar graph (fill columns from left to right)
  for (int col = 0; col < numCols; col++) {
    for (int row = 0; row < 8; row++) {
      setLED(col, row, true);
    }
  }
  
  // Write to matrix
  matrixWrite(ledFrame);
}

void setLED(int col, int row, bool on) {
  // Arduino UNO R4 LED matrix is 12x8
  // Data is stored as 8 rows of 32-bit words
  // Each row has 12 bits (one per column)
  
  if (row < 0 || row >= 8 || col < 0 || col >= 12) return;
  
  if (on) {
    ledFrame[row] |= (1 << (11 - col));  // Set bit
  } else {
    ledFrame[row] &= ~(1 << (11 - col)); // Clear bit
  }
}

int processDensity(int density) {
  // Apply haptic mode processing
  
  if (currentMode == "DIRECT") {
    return density;
  }
  else if (currentMode == "TEXTURE") {
    // Pulse for soft tissue
    if (density < 100) {
      int pulse = 20 * sin(millis() * 0.01);
      return constrain(density + pulse, 0, 255);
    }
    return density;
  }
  else if (currentMode == "TUMOR_LOCK") {
    // Full brightness if tumor detected
    if (density > TUMOR_THRESHOLD) {
      return 255;
    }
    return density / 2;
  }
  else if (currentMode == "EDGE_DETECT") {
    // Flash on edge
    int gradient = abs(density - prevDensity);
    if (gradient > EDGE_THRESHOLD) {
      return 255;
    }
    return density;
  }
  
  return density;
}

void flashMatrix(int times) {
  // Startup animation
  for (int t = 0; t < times; t++) {
    // Fill matrix
    for (int i = 0; i < 8; i++) {
      ledFrame[i] = 0xFFF;  // All 12 LEDs on
    }
    matrixWrite(ledFrame);
    delay(200);
    
    // Clear matrix
    for (int i = 0; i < 8; i++) {
      ledFrame[i] = 0;
    }
    matrixWrite(ledFrame);
    delay(200);
  }
}
