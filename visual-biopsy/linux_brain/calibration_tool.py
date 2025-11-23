#!/usr/bin/env python3
"""
Haptic Motor Calibration Tool
==============================
Calibrates haptic motor response curves and tests different PWM values.

Usage:
    python calibration_tool.py [serial_port]

Example:
    python calibration_tool.py /dev/ttyACM0
"""

import serial
import time
import sys
from dataclasses import dataclass
from typing import Optional

@dataclass
class CalibrationConfig:
    serial_port: str = '/dev/ttyACM0'
    baud_rate: int = 115200
    pwm_step: int = 25
    dwell_time: float = 1.0  # seconds


class HapticCalibrator:
    """Haptic motor calibration utility"""
    
    def __init__(self, config: CalibrationConfig):
        self.config = config
        self.serial: Optional[serial.Serial] = None
        
    def connect(self) -> bool:
        """Connect to MCU"""
        try:
            self.serial = serial.Serial(
                self.config.serial_port,
                self.config.baud_rate,
                timeout=1.0
            )
            print(f"✓ Connected to {self.config.serial_port}")
            time.sleep(2)  # Wait for MCU reset
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def send_pwm(self, value: int) -> None:
        """Send PWM value to MCU"""
        if self.serial:
            message = f"D:{value}\n"
            self.serial.write(message.encode('utf-8'))
    
    def run_sweep(self):
        """Run full PWM sweep from 0 to 255"""
        print("\n" + "=" * 60)
        print("PWM SWEEP TEST")
        print("=" * 60)
        print("Testing motor response across full range...")
        print("Observe motor behavior and note any irregularities.\n")
        
        for pwm in range(0, 256, self.config.pwm_step):
            print(f"PWM: {pwm:3d}/255", end=' ')
            self.send_pwm(pwm)
            
            # Visual bar
            bar_length = pwm // 10
            print(f"[{'█' * bar_length}{' ' * (25 - bar_length)}]")
            
            time.sleep(self.config.dwell_time)
        
        # Turn off
        self.send_pwm(0)
        print("\n✓ Sweep complete")
    
    def test_modes(self):
        """Test all haptic modes"""
        print("\n" + "=" * 60)
        print("HAPTIC MODE TEST")
        print("=" * 60)
        
        modes = ['DIRECT', 'TEXTURE', 'TUMOR_LOCK', 'EDGE_DETECT']
        test_value = 150  # Medium density
        
        for mode in modes:
            print(f"\nTesting {mode} mode...")
            if self.serial:
                self.serial.write(f"M:{mode}\n".encode('utf-8'))
                time.sleep(0.5)
            
            print(f"Sending density value: {test_value}")
            self.send_pwm(test_value)
            
            input(f"  Press ENTER to continue to next mode...")
        
        print("\n✓ Mode test complete")
    
    def interactive_test(self):
        """Interactive PWM testing"""
        print("\n" + "=" * 60)
        print("INTERACTIVE TEST MODE")
        print("=" * 60)
        print("Enter PWM values (0-255) or commands:")
        print("  0-255  : Set PWM value")
        print("  'q'    : Quit")
        print("  'sweep': Run full sweep")
        print("=" * 60)
        
        while True:
            try:
                user_input = input("\nPWM> ").strip().lower()
                
                if user_input == 'q':
                    break
                elif user_input == 'sweep':
                    self.run_sweep()
                    continue
                
                pwm = int(user_input)
                if 0 <= pwm <= 255:
                    self.send_pwm(pwm)
                    print(f"✓ Set PWM to {pwm}")
                else:
                    print("⚠ Value must be 0-255")
                    
            except ValueError:
                print("⚠ Invalid input. Enter a number (0-255) or command.")
            except KeyboardInterrupt:
                break
        
        # Turn off on exit
        self.send_pwm(0)
        print("\n✓ Interactive test complete")
    
    def run_all_tests(self):
        """Run complete calibration sequence"""
        if not self.connect():
            return
        
        try:
            print("\n🔧 HAPTIC MOTOR CALIBRATION UTILITY")
            print("=" * 60)
            print("This tool will test your haptic motor response.\n")
            
            # Test 1: PWM Sweep
            input("Press ENTER to start PWM sweep test...")
            self.run_sweep()
            
            # Test 2: Mode Testing
            input("\nPress ENTER to start mode test...")
            self.test_modes()
            
            # Test 3: Interactive
            input("\nPress ENTER to start interactive test (or Ctrl+C to skip)...")
            self.interactive_test()
            
            print("\n" + "=" * 60)
            print("✓ CALIBRATION COMPLETE")
            print("=" * 60)
            print("\nRecommendations:")
            print("- Note any PWM values where motor behaves erratically")
            print("- Verify all modes produce distinct haptic sensations")
            print("- Check that motor turns off completely at PWM=0")
            
        except KeyboardInterrupt:
            print("\n\n⚠ Calibration interrupted by user")
        finally:
            if self.serial:
                self.send_pwm(0)  # Safety: turn off motor
                self.serial.close()
                print("✓ Serial connection closed")


def main():
    """Entry point"""
    config = CalibrationConfig()
    
    # Override serial port from command line
    if len(sys.argv) > 1:
        config.serial_port = sys.argv[1]
    
    calibrator = HapticCalibrator(config)
    calibrator.run_all_tests()


if __name__ == "__main__":
    main()
