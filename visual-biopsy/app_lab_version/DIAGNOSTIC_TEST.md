# 🔍 LED Update Diagnostic Test

## Enhanced Debugging Installed ✅

I've added comprehensive logging to track data flow:
- **Python Brain**: Shows WebUI→Python and Python→Arduino data flow
- **Arduino Sketch**: Loop counter, timing, density changes, LED count
- **Web UI**: Console logs for mouse position and socket responses

---

## 🧪 Test Procedure

### Step 1: Open Monitoring Windows
1. **Arduino Lab Console** (Python output)
2. **Serial Monitor** (Arduino output)
3. **Browser Console** (F12 → Console tab)

### Step 2: Start the Application
1. Upload `sketch.ino` to Arduino UNO R4
2. Run `main.py` in Arduino Lab
3. Open the Web UI in your browser

### Step 3: Move Mouse Over Synthetic Scan
Move your mouse slowly over these areas:

| Area | Expected Density | Expected LEDs |
|------|-----------------|---------------|
| **Dark area (fluid)** | ~30 | 1-2 LEDs |
| **Gray background (tissue)** | ~80 | 3-4 LEDs |
| **White circles (tumors)** | ~255 | 12 LEDs |

---

## 📊 What to Look For

### ✅ **GOOD SIGNS** (System Working):
```
[WebUI Console]
[WebUI] Mouse at (0.25, 0.25) | Local pixel: 80
[Socket] Received density update: 128

[Python Console]
[WebUI → Python] Position (0.25, 0.25) → Density: 128 (was 0)
[Python → Arduino] Polling density: 128

[Arduino Serial Monitor]
[Loop #42] Density: 128 (prev: 0) | LEDs: 6/12 | Time: 50ms
```

### ❌ **BAD SIGNS** (Problems):

#### Problem 1: Density Stuck at 0
```
[Arduino Serial Monitor]
[Loop #100] Density: 0 (prev: 0) | LEDs: 0/12 | Time: 50ms
```
**Cause**: Arduino polling before Python updates
**Fix**: Switch to push-based updates

#### Problem 2: Python Not Receiving Mouse Events
```
[WebUI Console]
[WebUI] Mouse at (0.50, 0.50) | Local pixel: 255
(No socket response)
```
**Cause**: Socket.IO connection issue
**Fix**: Check `socket.connected` status

#### Problem 3: Python Not Training on Image
```
[Python Console]
[WebUI → Python] Position (0.25, 0.25) → Density: 0 (was 0)
```
**Cause**: K-Means not trained, haptic map empty
**Fix**: Load synthetic scan or upload image

---

## 🐛 Common Issues & Solutions

### Issue: LEDs Stay at One Brightness
**Symptoms**: LEDs turn on but don't change when moving mouse

**Diagnosis Steps**:
1. Check Arduino Serial Monitor for density changes
2. Check Python console for polling messages
3. Check Browser console for socket messages

**Possible Causes**:
- **Timing Issue**: Arduino polls before Python updates
  - **Fix**: Implement push-based updates (see below)
- **K-Means Not Trained**: All densities return 0
  - **Fix**: Load the synthetic scan by refreshing page
- **Socket Disconnected**: Browser can't talk to Python
  - **Fix**: Check connection status in UI

### Issue: Bridge Call Failures
```
[ERROR] Failed to get density from Python!
```
**Fix**: Verify `Bridge.provide()` calls in `main.py` match Arduino calls

---

## 🔧 Quick Fix: Push-Based Updates

If you see Arduino polling before Python updates, try this fix:

### In `main.py`, add:
```python
def on_get_density(client, data):
    global current_density
    if 'x' in data and 'y' in data:
        density = analyzer.get_density_normalized(data['x'], data['y'])
        current_density = density
        
        # PUSH density to Arduino instead of waiting for poll
        from arduino.app_utils import Bridge
        Bridge.send_to_sketch('update_density', density)
        
        ui.send_message('density_update', {'density': density})
        return density
    return 0
```

### In `sketch.ino`, add:
```cpp
// Add this function before setup()
void on_update_density(int density) {
    prevDensity = currentDensity;
    currentDensity = density;
    Serial.print("[PUSH] Received density: ");
    Serial.println(density);
    updateLEDMatrix(currentDensity);
}

// In setup(), register the handler:
void setup() {
    matrixBegin();
    Bridge.begin();
    
    // Register push handler
    Bridge.listen("update_density", on_update_density);
    
    // ... rest of setup
}

// In loop(), remove polling (or reduce frequency to 1Hz for monitoring):
void loop() {
    // No need to poll every 50ms anymore!
    // LEDs update when Python pushes data
    delay(1000);
}
```

---

## 📝 Report Your Findings

Please report what you see in **all three consoles** when you:
1. Move mouse over **dark area** (fluid)
2. Move mouse over **gray background** (tissue)  
3. Move mouse over **white circle** (tumor)

**Example Report**:
```
Dark area (fluid):
- Browser: Local pixel: 34
- Python: Density: 0 (was 0)  ← PROBLEM! Should be 0
- Arduino: Density: 0 | LEDs: 0/12 ✅

White tumor:
- Browser: Local pixel: 255
- Python: Density: 255 (was 0) ✅
- Arduino: Density: 0 | LEDs: 0/12 ← STUCK!
```

This will tell us exactly where the data flow breaks!
