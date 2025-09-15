#!/usr/bin/env python3
"""
Test script for LinkedIn posting only (without post generation)
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_linkedin_posting():
    """Test LinkedIn posting with test text"""
    print("🔗 Testing LinkedIn posting functionality...")
    
    # Check if LinkedIn credentials are available
    linkedin_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    author_urn = os.getenv("LINKEDIN_AUTHOR_URN")
    
    if not linkedin_token:
        print("❌ LINKEDIN_ACCESS_TOKEN not found in environment variables")
        return False
    
    if not author_urn:
        print("❌ LINKEDIN_AUTHOR_URN not found in environment variables")
        return False
    
    print(f"✅ LinkedIn credentials found")
    print(f"   Token: {linkedin_token[:20]}...")
    print(f"   Author URN: {author_urn}")
    
    # Test text-only post
    test_text = """🚀 Test Post from LinkedIn Post Generator API

This is a test post to verify that the LinkedIn integration is working correctly.

Features tested:
✅ Text-only posting
✅ API authentication
✅ Post creation
✅ URN retrieval

#TestPost #LinkedInAPI #Integration"""
    
    print(f"📝 Test text prepared ({len(test_text)} characters)")
    print(f"   Preview: {test_text[:100]}...")
    
    try:
        # Import the LinkedIn posting function
        from linkedin_post import post_linkedin_images_text
        print("✅ linkedin_post module imported successfully")
        
        # Test the posting function
        print("📤 Attempting to post to LinkedIn...")
        
        post_urn = post_linkedin_images_text(
            token=linkedin_token,
            author_urn=author_urn,
            commentary=test_text,
            image_paths=[],  # No images for this test
            alt_texts=None,
            visibility="PUBLIC"
        )
        
        print(f"🎉 LinkedIn post successful!")
        print(f"   Post URN: {post_urn}")
        print(f"   Post URL: https://www.linkedin.com/feed/update/{post_urn}/")
        
        return True
        
    except Exception as e:
        print(f"❌ LinkedIn posting failed: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        
        # Print more details for debugging
        import traceback
        print(f"   Full traceback:")
        traceback.print_exc()
        
        return False

def test_linkedin_with_image():
    """Test LinkedIn posting with a test image (if available)"""
    print("\n🖼️  Testing LinkedIn posting with image...")
    
    # Check if LinkedIn credentials are available
    linkedin_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    author_urn = os.getenv("LINKEDIN_AUTHOR_URN")
    
    if not linkedin_token or not author_urn:
        print("❌ LinkedIn credentials not available")
        return False
    
    # Look for a test image in the current directory
    test_image_paths = []
    for ext in ['.jpg', '.jpeg', '.png', '.gif']:
        for filename in os.listdir('.'):
            if filename.lower().endswith(ext):
                test_image_paths.append(filename)
                break
    
    if not test_image_paths:
        print("⚠️  No test images found in current directory")
        print("   Skipping image upload test")
        return False
    
    test_image = test_image_paths[0]
    print(f"📸 Found test image: {test_image}")
    
    test_text = """🖼️  Test Post with Image

This post includes an image to test the full LinkedIn posting functionality.

Testing:
✅ Image upload
✅ Text + image posting
✅ Multi-media content

#TestImage #LinkedInAPI #ImageUpload"""
    
    try:
        from linkedin_post import post_linkedin_images_text
        
        print(f"📤 Attempting to post with image...")
        
        post_urn = post_linkedin_images_text(
            token=linkedin_token,
            author_urn=author_urn,
            commentary=test_text,
            image_paths=[test_image],
            alt_texts=["Test image for LinkedIn API"],
            visibility="PUBLIC"
        )
        
        print(f"🎉 LinkedIn post with image successful!")
        print(f"   Post URN: {post_urn}")
        print(f"   Post URL: https://www.linkedin.com/feed/update/{post_urn}/")
        
        return True
        
    except Exception as e:
        print(f"❌ LinkedIn posting with image failed: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("LinkedIn Posting Test")
    print("=" * 50)
    
    # Test text-only posting
    text_success = test_linkedin_posting()
    
    # Test image posting
    image_success = test_linkedin_with_image()
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY:")
    print(f"   Text-only posting: {'✅ PASSED' if text_success else '❌ FAILED'}")
    print(f"   Image posting: {'✅ PASSED' if image_success else '❌ FAILED'}")
    
    if text_success or image_success:
        print("\n🎉 At least one test passed! LinkedIn integration is working.")
    else:
        print("\n❌ All tests failed. Check your LinkedIn credentials and API setup.")
