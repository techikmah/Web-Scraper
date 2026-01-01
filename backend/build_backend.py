"""
Build script for creating Python backend executable
This creates a standalone executable that can be bundled with Electron
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

print("="*60)
print("Building Python Backend Executable")
print("="*60)

# Get current directory
backend_dir = Path(__file__).parent
project_root = backend_dir.parent

print(f"\nBackend directory: {backend_dir}")
print(f"Project root: {project_root}")

# Check if PyInstaller is installed
try:
    import PyInstaller
    print("✅ PyInstaller found")
except ImportError:
    print("❌ PyInstaller not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    print("✅ PyInstaller installed")

# Clean previous builds
dist_dir = backend_dir / "dist"
build_dir = backend_dir / "build"

print("\nCleaning previous builds...")
if dist_dir.exists():
    shutil.rmtree(dist_dir)
    print("  - Removed dist/")
if build_dir.exists():
    shutil.rmtree(build_dir)
    print("  - Removed build/")

# Determine executable name based on platform
if sys.platform == "win32":
    exe_name = "web-scraper-backend.exe"
elif sys.platform == "darwin":
    exe_name = "web-scraper-backend"
else:  # Linux
    exe_name = "web-scraper-backend"

print(f"\nBuilding executable: {exe_name}")

# PyInstaller command
cmd = [
    "pyinstaller",
    "--onefile",
    "--name", "web-scraper-backend",
    "--hidden-import", "flask",
    "--hidden-import", "flask_cors",
    "--hidden-import", "bs4",
    "--hidden-import", "lxml",
    "--hidden-import", "lxml.etree",
    "--hidden-import", "lxml._elementpath",
    "--hidden-import", "pandas",
    "--hidden-import", "openpyxl",
    "--hidden-import", "requests",
    "--hidden-import", "urllib3",
    "--add-data", f"scraper.py{os.pathsep}.",
    "--console",
    "--clean",
    "app.py"
]

print("\nRunning PyInstaller...")
print(" ".join(cmd))
print()

try:
    # Run PyInstaller
    result = subprocess.run(
        cmd,
        cwd=backend_dir,
        check=True,
        capture_output=False
    )
    
    # Check if executable was created
    exe_path = dist_dir / exe_name
    
    if exe_path.exists():
        exe_size = exe_path.stat().st_size / (1024 * 1024)  # Size in MB
        print(f"\n✅ Build successful!")
        print(f"   Executable: {exe_path}")
        print(f"   Size: {exe_size:.2f} MB")
        
        # Test the executable
        print("\n🧪 Testing executable...")
        test_process = subprocess.Popen(
            [str(exe_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=dist_dir
        )
        
        # Wait 3 seconds and check if it's still running
        import time
        time.sleep(3)
        
        if test_process.poll() is None:
            print("✅ Executable is running!")
            test_process.terminate()
            test_process.wait()
        else:
            print("⚠️  Executable exited immediately. Check for errors.")
            stdout, stderr = test_process.communicate()
            if stderr:
                print(f"Error output: {stderr.decode()}")
        
        print("\n" + "="*60)
        print("Backend build complete!")
        print("="*60)
        print(f"\nExecutable location: {exe_path}")
        print("\nNext steps:")
        print("  1. Build frontend: cd frontend && npm run build")
        print("  2. Build Electron app: npm run build:win (or :mac, :linux)")
        print()
        
    else:
        print("\n❌ Build failed: Executable not found")
        sys.exit(1)
        
except subprocess.CalledProcessError as e:
    print(f"\n❌ Build failed with error code {e.returncode}")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Build failed: {e}")
    sys.exit(1)