#!/usr/bin/env python3
"""
Startup script for the LinkedIn Post Generator Streamlit app.
This script starts both the FastAPI server and the Streamlit app.
"""

import subprocess
import sys
import time
import os
import signal
import threading
from pathlib import Path

def start_api_server():
    """Start the FastAPI server in a separate process"""
    print("🚀 Starting FastAPI server...")
    try:
        # Change to the app directory
        app_dir = Path(__file__).parent / "app"
        process = subprocess.Popen(
            [sys.executable, "main.py"],
            cwd=app_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return process
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")
        return None

def start_streamlit():
    """Start the Streamlit app"""
    print("🚀 Starting Streamlit app...")
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ])
    except Exception as e:
        print(f"❌ Failed to start Streamlit: {e}")

def main():
    print("🔗 LinkedIn Post Generator - Starting Services")
    print("=" * 50)
    
    # Check if .env file exists
    if not os.path.exists(".env"):
        print("⚠️  Warning: .env file not found!")
        print("   Please create a .env file based on env.example")
        print("   The app may not work without proper configuration.")
        print()
    
    # Start API server
    api_process = start_api_server()
    if not api_process:
        print("❌ Cannot start without API server. Exiting.")
        sys.exit(1)
    
    # Wait a moment for the API server to start
    print("⏳ Waiting for API server to start...")
    time.sleep(3)
    
    # Check if API server is running
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API server is running")
        else:
            print("⚠️  API server may not be ready yet")
    except Exception as e:
        print(f"⚠️  Could not verify API server status: {e}")
    
    print()
    print("🌐 Services will be available at:")
    print("   📊 Streamlit App: http://localhost:8501")
    print("   🔌 API Server: http://localhost:8000")
    print()
    print("Press Ctrl+C to stop all services")
    print("=" * 50)
    
    try:
        # Start Streamlit (this will block)
        start_streamlit()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down services...")
    finally:
        # Clean up API server
        if api_process:
            print("🛑 Stopping API server...")
            api_process.terminate()
            try:
                api_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                api_process.kill()
            print("✅ API server stopped")

if __name__ == "__main__":
    main()
