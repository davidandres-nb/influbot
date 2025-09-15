#!/usr/bin/env python3
"""
Test script for image generation functionality
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_image_generation():
    """Test image generation with sample post content"""
    print("🎨 Testing Image Generation")
    print("=" * 50)
    
    # Check if OpenAI API key is available
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("   Set OPENAI_API_KEY in your .env file")
        return False
    
    print("✅ OpenAI API key found")
    print(f"   Key: {openai_key[:20]}...")
    
    # Sample post content for testing
    test_post = """🚀 The Future of AI in iGaming

Artificial Intelligence is revolutionizing the online gambling industry, from personalized experiences to enhanced security and fair play.

Key areas of transformation:
• AI-powered game recommendations
• Fraud detection and prevention
• Personalized user experiences
• Real-time analytics and insights

What's your take on AI in iGaming?

#AI #iGaming #Innovation #Technology #Gaming"""
    
    print(f"📝 Test post prepared ({len(test_post)} characters)")
    print(f"   Preview: {test_post[:100]}...")
    
    try:
        # Import the image generation function
        from image_generator import generate_linkedin_image, cleanup_image
        print("✅ image_generator module imported successfully")
        
        # Test image generation
        print(f"\n🎨 Generating image...")
        image_path = generate_linkedin_image(
            post_content=test_post,
            openai_api_key=openai_key,
            model="gpt-image-1",
            size="1024x1024"
        )
        
        print(f"🎉 Image generation successful!")
        print(f"   Image path: {image_path}")
        print(f"   File exists: {os.path.exists(image_path)}")
        print(f"   File size: {os.path.getsize(image_path)} bytes")
        
        # Test cleanup
        print(f"\n🗑️  Testing cleanup...")
        cleanup_success = cleanup_image(image_path)
        
        if cleanup_success:
            print(f"✅ Cleanup successful!")
            print(f"   File still exists: {os.path.exists(image_path)}")
        else:
            print(f"❌ Cleanup failed!")
        
        return True
        
    except Exception as e:
        print(f"❌ Image generation test failed: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        
        # Print more details for debugging
        import traceback
        print(f"   Full traceback:")
        traceback.print_exc()
        
        return False

if __name__ == "__main__":
    print("Image Generation Test")
    print("=" * 50)
    
    success = test_image_generation()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Image generation test PASSED!")
        print("   Your image generation setup is working correctly.")
    else:
        print("❌ Image generation test FAILED!")
        print("   Check the error messages above for details.")
