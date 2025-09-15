#!/usr/bin/env python3
"""
Simple startup script for the LinkedIn Post Generator Streamlit app.
This script starts only the Streamlit app without FastAPI.
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    print("🔗 LinkedIn Post Generator - Simple Mode")
    print("=" * 50)
    
    # Check if .env file exists
    if not os.path.exists(".env"):
        print("⚠️  Warning: .env file not found!")
        print("   Please create a .env file based on env.example")
        print("   The app may not work without proper configuration.")
        print()
    
    print("🚀 Starting Streamlit app...")
    print("   No FastAPI server needed - direct Python imports")
    print()
    print("🌐 App will be available at: http://localhost:8501")
    print()
    print("Press Ctrl+C to stop the app")
    print("=" * 50)
    
    try:
        # Start Streamlit directly
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_simple.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    except Exception as e:
        print(f"❌ Error starting Streamlit: {e}")

if __name__ == "__main__":
    main()
