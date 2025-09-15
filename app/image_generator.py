#!/usr/bin/env python3
"""
Image generation module using OpenAI's GPT-4o for LinkedIn posts
"""

import os
import base64
import tempfile
from typing import Optional
import requests
from datetime import datetime

def generate_linkedin_image(
    post_content: str,
    openai_api_key: str,
    model: str = "gpt-image-1",
    size: str = "1024x1024",
    custom_prompt: Optional[str] = None,
    # quality: str = "standard",
    # style: str = "natural"
) -> str:
    """
    Generate a professional LinkedIn image using GPT-4o based on post content.
    
    Args:
        post_content: The LinkedIn post content to base the image on
        openai_api_key: OpenAI API key
        model: OpenAI model to use (default: gpt-image-1)
        size: Image size (default: 1024x1024 for square)
        custom_prompt: Additional custom guidelines for image generation (optional)
        quality: Image quality (standard, hd)
        style: Image style (natural, vivid)
    
    Returns:
        str: Path to the generated image file
    
    Raises:
        Exception: If image generation fails
    """
    
    print(f"🎨 Generating LinkedIn image...")
    print(f"   Model: {model}")
    print(f"   Size: {size}")
    # print(f"   Quality: {quality}")
    # print(f"   Style: {style}")
    
    # Create the base prompt for image generation
    base_prompt = f"""Create a squared image to include together with the following post in LinkedIn. No text based. Nice, very visual and professional.

Post: {post_content}

Requirements:
- Square format (1:1 aspect ratio)
- No text or words
- Professional and business-appropriate
- Visually appealing and modern
- Related to the post content theme
- High quality and polished appearance"""

    # Add custom prompt as additional guidelines if provided
    if custom_prompt and custom_prompt.strip():
        prompt = f"""{base_prompt}

Additional Guidelines:
{custom_prompt.strip()}"""
        print(f"🎨 Using custom prompt guidelines: {custom_prompt[:100]}...")
    else:
        prompt = base_prompt
        print("🤖 Using standard prompt based on post content")
    
    print(f"📝 Image prompt prepared ({len(prompt)} characters)")
    print(f"   Preview: {prompt[:200]}...")
    
    try:
        # OpenAI API endpoint for image generation
        url = "https://api.openai.com/v1/images/generations"
        
        headers = {
            "Authorization": f"Bearer {openai_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "prompt": prompt,
            "size": size,
            # "quality": quality,
            # "style": style,
            "n": 1
        }
        
        print(f"📤 Sending request to OpenAI API...")
        
        response = requests.post(url, headers=headers, json=data, timeout=120)
        
        if response.status_code != 200:
            error_msg = f"OpenAI API error: {response.status_code}"
            try:
                error_data = response.json()
                if 'error' in error_data:
                    error_msg += f" - {error_data['error'].get('message', 'Unknown error')}"
            except:
                error_msg += f" - {response.text}"
            raise Exception(error_msg)
        
        # Extract image data from response
        result = response.json()
        
        # Handle both URL and base64 formats
        image_data = result['data'][0]
        image_content = None
        
        if 'url' in image_data:
            # Handle URL format (older API)
            print(f"✅ Image generated successfully (URL format)!")
            print(f"   Image URL: {image_data['url']}")
            
            # Download and save the image locally
            print(f"💾 Downloading image from URL...")
            image_response = requests.get(image_data['url'], timeout=60)
            
            if image_response.status_code != 200:
                raise Exception(f"Failed to download image: {image_response.status_code}")
            
            image_content = image_response.content
            
        elif 'b64_json' in image_data:
            # Handle base64 format (newer API)
            print(f"✅ Image generated successfully (base64 format)!")
            print(f"   Image data: base64 encoded")
            
            # Decode base64 data
            import base64
            image_content = base64.b64decode(image_data['b64_json'])
            
        else:
            raise Exception(f"Unexpected image data format. Available keys: {list(image_data.keys())}")
        
        # Create a temporary file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_dir = tempfile.gettempdir()
        image_filename = f"linkedin_post_{timestamp}.png"
        image_path = os.path.join(temp_dir, image_filename)
        
        # Save the image
        with open(image_path, 'wb') as f:
            f.write(image_content)
        
        # Verify file was created and has content
        if not os.path.exists(image_path) or os.path.getsize(image_path) == 0:
            raise Exception("Failed to save image file")
        
        file_size = os.path.getsize(image_path)
        print(f"✅ Image saved successfully!")
        print(f"   Path: {image_path}")
        print(f"   Size: {file_size} bytes")
        
        return image_path
        
    except Exception as e:
        print(f"❌ Image generation failed: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        raise

def cleanup_image(image_path: str) -> bool:
    """
    Clean up the generated image file.
    
    Args:
        image_path: Path to the image file to delete
    
    Returns:
        bool: True if cleanup successful, False otherwise
    """
    try:
        if os.path.exists(image_path):
            os.remove(image_path)
            print(f"🗑️  Image cleaned up: {image_path}")
            return True
        else:
            print(f"⚠️  Image file not found for cleanup: {image_path}")
            return False
    except Exception as e:
        print(f"❌ Failed to cleanup image {image_path}: {str(e)}")
        return False

def generate_and_cleanup_image(
    post_content: str,
    openai_api_key: str,
    **kwargs
) -> str:
    """
    Generate an image and return the path. The caller is responsible for cleanup.
    
    Args:
        post_content: The LinkedIn post content
        openai_api_key: OpenAI API key
        **kwargs: Additional arguments for generate_linkedin_image
    
    Returns:
        str: Path to the generated image file
    """
    return generate_linkedin_image(post_content, openai_api_key, **kwargs)

# Example usage:
if __name__ == "__main__":
    # Test the image generation (requires OPENAI_API_KEY in environment)
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        exit(1)
    
    # Test with sample post content
    test_post = """🚀 The Future of AI in Business

Artificial Intelligence is transforming how we work, think, and innovate. From automation to decision-making, AI is becoming an essential tool for modern businesses.

What's your experience with AI in your industry?

#AI #Business #Innovation #FutureOfWork"""
    
    try:
        print("🧪 Testing image generation...")
        image_path = generate_linkedin_image(test_post, api_key)
        
        print(f"🎉 Test successful! Image saved at: {image_path}")
        print(f"   File exists: {os.path.exists(image_path)}")
        print(f"   File size: {os.path.getsize(image_path)} bytes")
        
        # Clean up
        cleanup_image(image_path)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
