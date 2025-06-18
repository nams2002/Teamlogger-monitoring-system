#!/usr/bin/env python3
"""
Debug config import issues
"""

import os
import sys
from pathlib import Path

print("🔍 DEBUGGING CONFIG IMPORT")
print("=" * 70)

# Check Python path
print("📁 Current directory:", os.getcwd())
print("🐍 Python path:")
for p in sys.path[:5]:
    print(f"   - {p}")

# Check for multiple .env files
print("\n📋 Searching for all .env files:")
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.startswith('.env'):
            full_path = os.path.join(root, file)
            print(f"   Found: {full_path}")

# Try to load dotenv manually
print("\n🔧 Loading .env manually:")
try:
    from dotenv import load_dotenv, find_dotenv
    
    # Find .env file
    dotenv_path = find_dotenv()
    print(f"   dotenv found at: {dotenv_path}")
    
    # Load it
    load_dotenv(dotenv_path, override=True)
    
    # Check the values
    min_hours = os.getenv('MINIMUM_HOURS_PER_WEEK')
    print(f"   MINIMUM_HOURS_PER_WEEK from env: '{min_hours}'")
    print(f"   Type: {type(min_hours)}")
    print(f"   Repr: {repr(min_hours)}")
    
    # Try to convert
    try:
        float_val = float(min_hours)
        print(f"   ✅ Converts to float: {float_val}")
    except Exception as e:
        print(f"   ❌ Error converting: {e}")
        # Check each character
        print("   Character breakdown:")
        for i, char in enumerate(min_hours):
            print(f"     [{i}] = '{char}' (ord: {ord(char)})")
    
except Exception as e:
    print(f"   ❌ Error loading dotenv: {e}")

# Now try to import Config
print("\n📦 Trying to import Config:")
try:
    # First, let's look at the actual settings.py file
    settings_path = Path('config/settings.py')
    if settings_path.exists():
        print(f"   Found settings.py at: {settings_path.absolute()}")
        
        # Read the specific line
        with open(settings_path, 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                if 'MINIMUM_HOURS_PER_WEEK' in line and 'float' in line:
                    print(f"   Line {i+1}: {line.strip()}")
                    print(f"   Raw repr: {repr(line)}")
    
    # Try importing
    from config.settings import Config
    
    print("   ✅ Import successful!")
    print(f"   Config.MINIMUM_HOURS_PER_WEEK = {Config.MINIMUM_HOURS_PER_WEEK}")
    
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    import traceback
    print("\n   Full traceback:")
    traceback.print_exc()

# Check if there's a config/__init__.py
print("\n📁 Checking config directory:")
config_dir = Path('config')
if config_dir.exists():
    print(f"   Config directory exists")
    init_file = config_dir / '__init__.py'
    if init_file.exists():
        print(f"   __init__.py exists (size: {init_file.stat().st_size} bytes)")
        if init_file.stat().st_size > 0:
            print("   ⚠️  __init__.py is not empty - might be importing something")
            with open(init_file, 'r') as f:
                content = f.read()
                if content.strip():
                    print(f"   Content: {repr(content[:100])}")
    else:
        print("   ❌ __init__.py missing - creating it")
        init_file.write_text("")

# Final check - look for any other settings files
print("\n🔍 Looking for other settings files:")
for root, dirs, files in os.walk('.'):
    for file in files:
        if 'settings' in file.lower() and file.endswith('.py'):
            print(f"   Found: {os.path.join(root, file)}")

print("\n" + "=" * 70)
print("💡 RECOMMENDATIONS:")
print("1. Make sure config/__init__.py exists and is empty")
print("2. Check if there are multiple .env files")
print("3. Verify no other settings.py files exist")
print("4. Try using the clean .env file created earlier")