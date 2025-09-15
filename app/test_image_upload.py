#!/usr/bin/env python3
"""
Test script to debug image generation and LinkedIn upload
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_image_generation_and_upload():
    """Test image generation and LinkedIn upload directly"""
    print("🔍 Debugging Image Generation and LinkedIn Upload")
    print("=" * 60)
    
    # Check credentials
    openai_key = os.getenv("OPENAI_API_KEY")
    linkedin_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    author_urn = os.getenv("LINKEDIN_AUTHOR_URN")
    
    if not all([openai_key, linkedin_token, author_urn]):
        print("❌ Missing credentials:")
        print(f"   OpenAI API Key: {'✅' if openai_key else '❌'}")
        print(f"   LinkedIn Token: {'✅' if linkedin_token else '❌'}")
        print(f"   Author URN: {'✅' if author_urn else '❌'}")
        return False
    
    print("✅ All credentials found")
    
    # Test payload
    payload = {
        "terms": ["AI", "testing"],
        "topic": "AI Testing and Debugging",
        "audience_profile": "developers",
        "language": "English",
        "register": "professional",
        "max_chars": 500,
        "content_instructions": "Make it short and technical",
        "should_post": True,
        "linkedin_token": linkedin_token,
        "author_urn": author_urn,
        "generate_image": True,
        "image_model": "gpt-image-1",
        "image_size": "1024x1024"
    }
    
    print(f"📝 Test payload prepared")
    print(f"   Generate image: {payload['generate_image']}")
    print(f"   Should post: {payload['should_post']}")
    
    try:
        print(f"\n📤 Calling API endpoint...")
        
        response = requests.post(
            "http://localhost:8000/generate-post",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=300  # 5 minutes timeout for image generation
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS!")
            print(f"   Success: {data['success']}")
            print(f"   Message: {data['message']}")
            print(f"   Post URN: {data['post_urn']}")
            
            if data['post_urn']:
                print(f"   LinkedIn URL: https://www.linkedin.com/feed/update/{data['post_urn']}/")
                print(f"   🔍 Check this URL to see if the image was actually posted!")
            
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
    success = test_image_generation_and_upload()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Test completed successfully!")
        print("   Check the LinkedIn URL above to verify if the image was posted")
    else:
        print("❌ Test failed!")
        print("   Check the error messages above for details")
