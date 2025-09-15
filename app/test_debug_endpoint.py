#!/usr/bin/env python3
"""
Test script to check if the debug endpoint is working
"""

import requests
import json

# API base URL
BASE_URL = "http://localhost:8000"

def test_debug_endpoint():
    """Test the debug endpoint to see if updated code is running"""
    print("🔍 Testing Debug Endpoint")
    print("=" * 50)
    
    try:
        # Test health endpoint first
        print("🏥 Testing API health...")
        health_response = requests.get(f"{BASE_URL}/health")
        if health_response.status_code == 200:
            print("✅ API is healthy and running")
        else:
            print("❌ API health check failed")
            return False
        
        # Test env-check endpoint
        print("\n🔑 Testing env-check endpoint...")
        env_response = requests.get(f"{BASE_URL}/env-check")
        if env_response.status_code == 200:
            env_data = env_response.json()
            print("✅ Environment check successful:")
            for key, value in env_data.items():
                print(f"   {key}: {value}")
        else:
            print(f"❌ Environment check failed: {env_response.status_code}")
            return False
        
        # Test a simple generate-only request to see debug output
        print("\n📝 Testing simple generate-only request...")
        payload = {
            "terms": ["AI", "test"],
            "topic": "AI Testing",
            "audience_profile": "developers",
            "language": "English",
            "register": "professional",
            "max_chars": 100,
            "content_instructions": "Make it short and simple",
            "should_post": False,
            "generate_image": True,  # This should trigger image generation
            "image_model": "gpt-image-1",
            "image_size": "1024x1024"
        }
        
        response = requests.post(
            f"{BASE_URL}/generate-only",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS!")
            print(f"   Success: {data['success']}")
            print(f"   Message: {data['message']}")
            print(f"   Post URN: {data['post_urn']}")
            
            print(f"\n📝 Generated Content:")
            print(f"   Length: {len(data['post_content'])} characters")
            print(f"   Preview: {data['post_content'][:200]}...")
            
            return True
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    print("Debug Endpoint Test")
    print("=" * 50)
    
    success = test_debug_endpoint()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Debug endpoint test completed!")
        print("   Check the server logs for debug output.")
    else:
        print("❌ Debug endpoint test failed!")
        print("   Check the error messages above for details.")
