#!/usr/bin/env python3
"""
Test Suite for Haptic Histology System
=======================================
Run this to verify all components are working correctly.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all required packages are installed"""
    print("Testing imports...")
    
    try:
        import pygame
        print("  ✓ pygame")
    except ImportError:
        print(" pygame - Install with: pip install pygame")
        return False
    
    try:
        import cv2
        print("  ✓ opencv-python")
    except ImportError:
        print("   opencv-python - Install with: pip install opencv-python")
        return False
    
    try:
        import numpy
        print("  ✓ numpy")
    except ImportError:
        print("   numpy - Install with: pip install numpy")
        return False
    
    try:
        import serial
        print("  ✓ pyserial")
    except ImportError:
        print("   pyserial - Install with: pip install pyserial")
        return False
    
    try:
        from sklearn.cluster import KMeans
        print("  ✓ scikit-learn")
    except ImportError:
        print("   scikit-learn - Install with: pip install scikit-learn")
        return False
    
    return True


def test_kmeans():
    """Test K-Means clustering on synthetic data"""
    print("\nTesting K-Means clustering...")
    
    try:
        import numpy as np
        from sklearn.cluster import KMeans
        
        # Create synthetic image data
        data = np.array([[10], [15], [80], [85], [250], [255]])
        
        # Fit K-Means
        kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
        labels = kmeans.fit_predict(data)
        
        # Verify we got 3 clusters
        unique_labels = len(set(labels))
        if unique_labels == 3:
            print("  ✓ K-Means clustering works correctly")
            return True
        else:
            print(f"   Expected 3 clusters, got {unique_labels}")
            return False
            
    except Exception as e:
        print(f"   K-Means test failed: {e}")
        return False


def test_image_generation():
    """Test synthetic MRI scan generation"""
    print("\nTesting synthetic MRI generation...")
    
    try:
        import cv2
        import numpy as np
        
        # Create synthetic scan
        img = np.zeros((600, 600), dtype=np.uint8)
        img[:] = 80
        cv2.circle(img, (300, 300), 150, 100, -1)
        cv2.circle(img, (350, 280), 60, 255, -1)
        
        # Verify image properties
        if img.shape == (600, 600):
            print("  ✓ Synthetic MRI generation works")
            return True
        else:
            print(f"   Unexpected image shape: {img.shape}")
            return False
            
    except Exception as e:
        print(f"   Image generation failed: {e}")
        return False


def test_serial_detection():
    """Test serial port detection"""
    print("\nTesting serial port detection...")
    
    try:
        import serial.tools.list_ports
        
        ports = list(serial.tools.list_ports.comports())
        
        if len(ports) > 0:
            print(f"  ✓ Found {len(ports)} serial port(s):")
            for port in ports:
                print(f"    - {port.device}: {port.description}")
            return True
        else:
            print("  ⚠  No serial ports found (this is OK for demo mode)")
            return True
            
    except Exception as e:
        print(f"   Serial detection failed: {e}")
        return False


def test_file_structure():
    """Verify project file structure"""
    print("\nTesting file structure...")
    
    base_path = Path(__file__).parent.parent
    
    required_files = [
        "linux_brain/haptic_scanner.py",
        "linux_brain/scanner.py",
        "linux_brain/scanner_ml.py",
        "linux_brain/calibration_tool.py",
        "linux_brain/requirements.txt",
        "mcu_reflex/mcu_reflex.ino",
        "start.sh",
        "start.bat"
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists():
            print(f"  ✓ {file_path}")
        else:
            print(f"   Missing: {file_path}")
            all_exist = False
    
    return all_exist


def test_data_directory():
    """Verify data directory exists"""
    print("\nTesting data directory...")
    
    data_dir = Path(__file__).parent / "data"
    
    if data_dir.exists() and data_dir.is_dir():
        print(f"  ✓ Data directory exists: {data_dir}")
        
        # Check for MRI scan
        mri_path = data_dir / "mri_scan.jpg"
        if mri_path.exists():
            print(f"  ✓ MRI scan found: {mri_path}")
        else:
            print(f"  No MRI scan (will be auto-generated)")
        
        return True
    else:
        print(f"   Data directory missing: {data_dir}")
        return False


def run_all_tests():
    """Run complete test suite"""
    print("=" * 60)
    print("HAPTIC HISTOLOGY - SYSTEM TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Package Imports", test_imports),
        ("K-Means Algorithm", test_kmeans),
        ("Image Generation", test_image_generation),
        ("Serial Port Detection", test_serial_detection),
        ("File Structure", test_file_structure),
        ("Data Directory", test_data_directory)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else " FAIL"
        print(f"{status:8} {test_name}")
    
    print("=" * 60)
    print(f"Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n All tests passed! System is ready to use.")
        print("   Run: ./start.sh (Linux/Mac) or start.bat (Windows)")
        return 0
    else:
        print("\n Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
