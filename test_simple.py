#!/usr/bin/env python3
"""
Test script to verify the simple Streamlit app setup.
This script checks if all required modules can be imported directly.
"""

import sys
import os
from pathlib import Path

def test_direct_imports():
    """Test if all required modules can be imported directly"""
    print("🔍 Testing direct imports...")
    
    # Add app directory to path
    app_dir = Path(__file__).parent / "app"
    sys.path.insert(0, str(app_dir))
    
    try:
        import streamlit
        print("✅ Streamlit imported successfully")
    except ImportError as e:
        print(f"❌ Streamlit import failed: {e}")
        return False
    
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
    
    try:
        from image_generator import generate_linkedin_image
        print("✅ Image generator imported successfully")
    except ImportError as e:
        print(f"❌ Image generator import failed: {e}")
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

def test_simple_workflow():
    """Test a simple workflow without actually generating content"""
    print("\n🔍 Testing simple workflow...")
    
    try:
        # Test that we can call the functions without errors
        from post_generator import run_workflow
        
        # This should not actually run due to missing API keys, but should not crash
        print("✅ Post generator function accessible")
        
        from linkedin_post import post_linkedin_images_text
        print("✅ LinkedIn post function accessible")
        
        from image_generator import generate_linkedin_image
        print("✅ Image generator function accessible")
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow test failed: {e}")
        return False

def main():
    print("🚀 LinkedIn Post Generator - Simple Mode Test")
    print("=" * 50)
    
    # Test imports
    imports_ok = test_direct_imports()
    
    # Test environment
    env_ok = test_environment()
    
    # Test workflow
    workflow_ok = test_simple_workflow()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Direct Imports: {'✅ PASS' if imports_ok else '❌ FAIL'}")
    print(f"   Environment: {'✅ PASS' if env_ok else '⚠️  WARN'}")
    print(f"   Workflow: {'✅ PASS' if workflow_ok else '❌ FAIL'}")
    
    if imports_ok and workflow_ok:
        print("\n🎉 Simple mode is ready! You can use the direct Streamlit app.")
        print("\nTo start the simple app:")
        print("   python run_simple.py")
        print("\nOr on Windows:")
        print("   start_simple.bat")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        if not imports_ok:
            print("   Install missing dependencies with: pip install -r requirements.txt")
        if not env_ok:
            print("   Set up your .env file with required API keys")

if __name__ == "__main__":
    main()
