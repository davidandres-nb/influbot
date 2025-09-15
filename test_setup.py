#!/usr/bin/env python3
"""
Test script to verify the LinkedIn Post Generator setup.
This script checks if all required modules can be imported and basic functionality works.
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        import streamlit
        print("✅ Streamlit imported successfully")
    except ImportError as e:
        print(f"❌ Streamlit import failed: {e}")
        return False
    
    try:
        import requests
        print("✅ Requests imported successfully")
    except ImportError as e:
        print(f"❌ Requests import failed: {e}")
        return False
    
    try:
        from dotenv import load_dotenv
        print("✅ Python-dotenv imported successfully")
    except ImportError as e:
        print(f"❌ Python-dotenv import failed: {e}")
        return False
    
    # Test app modules
    app_dir = Path(__file__).parent / "app"
    sys.path.insert(0, str(app_dir))
    
    try:
        from post_generator import run_workflow
        print("✅ Post generator imported successfully")
    except ImportError as e:
        print(f"❌ Post generator import failed: {e}")
        return False
    
    try:
        from linkedin_post import post_linkedin_images_text
        print("✅ LinkedIn post module imported successfully")
    except ImportError as e:
        print(f"❌ LinkedIn post module import failed: {e}")
        return False
    
    return True

def test_environment():
    """Test environment variable loading"""
    print("\n🔍 Testing environment variables...")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'EVENTREGISTRY_API_KEY': os.getenv('EVENTREGISTRY_API_KEY'),
        'NEWSAPI_KEY': os.getenv('NEWSAPI_KEY'),
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    
    if missing_vars:
        print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("   Please check your .env file")
        return False
    else:
        print("✅ All required environment variables are set")
        return True

def test_api_server():
    """Test if API server can be started"""
    print("\n🔍 Testing API server startup...")
    
    try:
        import subprocess
        import time
        
        # Start API server in background
        app_dir = Path(__file__).parent / "app"
        process = subprocess.Popen(
            [sys.executable, "main.py"],
            cwd=app_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait a moment for startup
        time.sleep(3)
        
        # Test health endpoint
        import requests
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ API server started successfully")
                success = True
            else:
                print(f"❌ API server returned error: {response.status_code}")
                success = False
        except requests.exceptions.RequestException as e:
            print(f"❌ Could not connect to API server: {e}")
            success = False
        
        # Clean up
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        
        return success
        
    except Exception as e:
        print(f"❌ API server test failed: {e}")
        return False

def main():
    print("🚀 LinkedIn Post Generator - Setup Test")
    print("=" * 50)
    
    # Test imports
    imports_ok = test_imports()
    
    # Test environment
    env_ok = test_environment()
    
    # Test API server
    api_ok = test_api_server()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Imports: {'✅ PASS' if imports_ok else '❌ FAIL'}")
    print(f"   Environment: {'✅ PASS' if env_ok else '⚠️  WARN'}")
    print(f"   API Server: {'✅ PASS' if api_ok else '❌ FAIL'}")
    
    if imports_ok and env_ok and api_ok:
        print("\n🎉 All tests passed! You're ready to use the LinkedIn Post Generator.")
        print("\nTo start the application:")
        print("   python run_streamlit.py")
        print("\nOr on Windows:")
        print("   start_app.bat")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        if not imports_ok:
            print("   Install missing dependencies with: pip install -r requirements.txt")
        if not env_ok:
            print("   Set up your .env file with required API keys")
        if not api_ok:
            print("   Check that all dependencies are installed and API keys are valid")

if __name__ == "__main__":
    main()
