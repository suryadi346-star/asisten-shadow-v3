#!/usr/bin/env python3
"""
Quick Test - Password Input
Test apakah password input works dengan dots
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.password_input import get_password_with_dots

print("═══════════════════════════════════════")
print("  PASSWORD INPUT TEST")
print("═══════════════════════════════════════")
print()
print("Test 1: Password dengan dots")
print("-" * 40)

pwd1 = get_password_with_dots("Password: ")
print(f"✓ Password entered: {len(pwd1)} characters")
print(f"  Preview: {'•' * len(pwd1)}")

print()
print("Test 2: Konfirmasi password")
print("-" * 40)

pwd2 = get_password_with_dots("Confirm: ")
print(f"✓ Password entered: {len(pwd2)} characters")

print()
if pwd1 == pwd2:
    print("✅ SUCCESS! Passwords match!")
else:
    print("❌ Passwords don't match")

print()
print("═══════════════════════════════════════")
print("  TEST COMPLETE")
print("═══════════════════════════════════════")
