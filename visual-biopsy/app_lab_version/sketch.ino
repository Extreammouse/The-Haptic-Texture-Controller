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
  matrixBegin();
  Bridge.begin();
  
  // Test Python brain
  String test_result;
  bool ok = Bridge.call("test_system").result(test_result);
  if (ok) {
    Serial.println("✓ Python Brain Connected: " + test_result);
  } else {
    Serial.println("⚠ Python Brain not responding");
  }
  
  // Show startup animation
  flashMatrix(3);
}

void loop() {
  // This will be replaced by web UI input
  // For now, simulate mouse movement or use Serial input
  
  // Example: Read from Serial (for testing)
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    
    if (input.startsWith("POS:")) {
      // Format: "POS:0.5,0.5" (normalized coordinates)
      int commaPos = input.indexOf(',');
      if (commaPos > 0) {
        String xStr = input.substring(4, commaPos);
        String yStr = input.substring(commaPos + 1);
        
        float x_norm = xStr.toFloat();
        float y_norm = yStr.toFloat();
        
        updateDensityFromPosition(x_norm, y_norm);
      }
    }
    else if (input.startsWith("MODE:")) {
      // Format: "MODE:TEXTURE"
      currentMode = input.substring(5);
      Serial.println("Mode changed to: " + currentMode);
    }
  }
  
  // Update LED matrix
  updateLEDMatrix(currentDensity);
  
  delay(50);  // 20 Hz update rate
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
  
  // Map density (0-255) to brightness pattern on matrix
  // We'll use a "bar graph" style visualization
  
  // Clear frame
  for (int i = 0; i < 8; i++) {
    ledFrame[i] = 0;
  }
  
  // Calculate how many columns to light (0-12)
  int numCols = map(displayValue, 0, 255, 0, 12);
  
  // Create vertical bar graph
  for (int col = 0; col < 12; col++) {
    for (int row = 0; row < 8; row++) {
      if (col < numCols) {
        // Light this LED
        setLED(col, row, true);
      }
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
