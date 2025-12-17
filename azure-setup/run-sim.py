#!/usr/bin/env python3
import subprocess
import time
import random
from datetime import datetime

def update_twin():
    """Update twins with random sensor data"""
    # Generate values
    temp = round(random.uniform(24, 32), 1)
    hum = round(random.uniform(60, 85), 1)
    soil = round(random.uniform(55, 75), 1)
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Update zone_A
    cmd1 = [
        './az-docker.sh', 'dt', 'twin', 'update',
        '-n', 'farm-digital-twin',
        '--twin-id', 'zone_A',
        '--json-patch',
        f'[{{"op":"replace","path":"/temperature","value":{temp}}},{{"op":"replace","path":"/humidity","value":{hum}}},{{"op":"replace","path":"/soilMoisture","value":{soil}}}]'
    ]
    
    try:
        subprocess.run(cmd1, check=True, capture_output=True, cwd='/home/hs32/Documents/Projects/adt/azure-setup')
        print(f"[{datetime.now().strftime('%H:%M:%S')}] T:{temp}°C H:{hum}% S:{soil}% ✅")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

print("🌾 ADT Simulation Starting...")
print("Updates every 5 seconds\n")

count = 0
while True:
    try:
        if update_twin():
            count += 1
        time.sleep(5)
    except KeyboardInterrupt:
        print(f"\nStopped after {count} updates")
        break
