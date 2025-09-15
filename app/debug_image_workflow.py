#!/usr/bin/env python3
"""
Debug script to test image generation and LinkedIn posting workflow
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def debug_image_workflow():
    """Debug the image generation and LinkedIn posting workflow"""
    print("🔍 Debugging Image Generation and LinkedIn Posting Workflow")
    print("=" * 70)
    
    # Check environment variables
    openai_key = os.getenv("OPENAI_API_KEY")
    linkedin_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    author_urn = os.getenv("LINKEDIN_AUTHOR_URN")
    
    print(f"🔑 Environment Check:")
    print(f"   OpenAI API Key: {'✅ Set' if openai_key else '❌ Missing'}")
    print(f"   LinkedIn Token: {'✅ Set' if linkedin_token else '❌ Missing'}")
    print(f"   Author URN: {'✅ Set' if author_urn else '❌ Missing'}")
    
    if not all([openai_key, linkedin_token, author_urn]):
        print("❌ Missing required environment variables")
        return False
    
    # Test post content
    test_post = """🚀 AI Revolution in iGaming

Artificial Intelligence is transforming the online gambling industry, from personalized experiences to enhanced security and fair play.

What's your take on AI in iGaming?

#AI #iGaming #Innovation #Technology #Gaming"""
    
    print(f"\n📝 Test Post Content:")
    print(f"   Length: {len(test_post)} characters")
    print(f"   Content: {test_post}")
    
    try:
        # Test 1: Image Generation
        print(f"\n🎨 Test 1: Image Generation")
        print("-" * 40)
        
        from image_generator import generate_linkedin_image
        
        print("   Generating image...")
        image_path = generate_linkedin_image(
            post_content=test_post,
            openai_api_key=openai_key,
            model="gpt-image-1",
            size="1024x1024"
        )
        
        print(f"   ✅ Image generated successfully!")
        print(f"   Image path: {image_path}")
        print(f"   File exists: {os.path.exists(image_path)}")
        print(f"   File size: {os.path.getsize(image_path)} bytes")
        
        # Test 2: LinkedIn Posting with Image
        print(f"\n🔗 Test 2: LinkedIn Posting with Image")
        print("-" * 40)
        
        from linkedin_post import post_linkedin_images_text
        
        print("   Posting to LinkedIn with image...")
        post_urn = post_linkedin_images_text(
            token=linkedin_token,
            author_urn=author_urn,
            commentary=test_post,
            image_paths=[image_path],
            alt_texts=["AI-generated professional image for LinkedIn post"],
            visibility="PUBLIC"
        )
        
        print(f"   ✅ LinkedIn post successful!")
        print(f"   Post URN: {post_urn}")
        print(f"   LinkedIn URL: https://www.linkedin.com/feed/update/{post_urn}/")
        
        # Cleanup
        print(f"\n🗑️  Cleanup")
        print("-" * 40)
        
        from image_generator import cleanup_image
        
        cleanup_success = cleanup_image(image_path)
        print(f"   Image cleanup: {'✅ Success' if cleanup_success else '❌ Failed'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in debug workflow: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        
        import traceback
        print(f"   Full traceback:")
        traceback.print_exc()
        
        return False

if __name__ == "__main__":
    print("Image Workflow Debug Script")
    print("=" * 70)
    
    success = debug_image_workflow()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 Debug workflow completed successfully!")
        print("   Image generation and LinkedIn posting are working correctly.")
    else:
        print("❌ Debug workflow failed!")
        print("   Check the error messages above for details.")
