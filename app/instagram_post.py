#!/usr/bin/env python3
"""
Instagram posting module using instagrapi for LinkedIn Post Generator.
"""

import os
import sys
from pathlib import Path
from typing import Optional, List
from getpass import getpass

try:
    from instagrapi import Client
    from instagrapi.exceptions import TwoFactorRequired, ChallengeRequired
except ImportError as e:
    raise ImportError("instagrapi is not installed. Please run: pip install instagrapi") from e

try:
    from PIL import Image, ImageOps
except ImportError:
    Image = None


def prepare_image(path: Path) -> Path:
    """
    Ensure the image is a JPEG and RGB. If Pillow is available and the file
    is not a JPEG, convert it to JPEG to avoid upload issues.
    Returns the path to the file to upload, which may be a temporary JPG.
    """
    if Image is None:
        return path

    try:
        with Image.open(path) as im:
            # Convert to RGB if needed
            if im.mode not in ("RGB", "L"):
                im = im.convert("RGB")
            
            # Use a temporary path for the converted/optimized image
            out_path = path.with_suffix(".upload.jpg")
            
            # Some formats like PNG/WEBP/HEIC can cause issues, convert to JPEG
            # Also, fix orientation from EXIF data for all images
            im = ImageOps.exif_transpose(im)
            
            # Basic size normalization that plays nicely with Instagram
            # Keep aspect ratio, max width 1080
            if im.width > 1080:
                new_h = int(im.height * (1080 / im.width))
                im = im.resize((1080, new_h))
                print(f"Resized image to 1080x{new_h}")

            im.save(out_path, format="JPEG", quality=95, optimize=True)
            print(f"Saved temporary upload file to: {out_path}")
            return out_path
    except Exception as e:
        print(f"Could not process image with Pillow: {e}. Falling back to original path.")
        # If anything goes wrong, fall back to original path
        return path


def login_client(username: str, password: str, settings_path: Path) -> Optional[Client]:
    """
    Logs into Instagram, handling 2FA and challenges.
    Saves session settings to a file to reuse.
    """
    cl = Client()
    
    # Load previous session settings if available to reduce chances of challenge
    if settings_path.exists():
        try:
            cl.load_settings(str(settings_path))
            print(f"Loaded session settings from {settings_path}")
        except Exception as e:
            print(f"Could not load settings: {e}")

    # Simple handler for challenge codes delivered by email/SMS
    def code_handler(username, choice):
        print(f"A verification code was requested via {choice}.")
        return input("Enter the code you received: ").strip()

    cl.challenge_code_handler = code_handler

    try:
        print(f"Logging in to Instagram as {username}...")
        cl.login(username, password)
    except TwoFactorRequired:
        print("Two-factor authentication required.")
        code = input("Enter your 2FA code: ").strip()
        cl.two_factor_login(code)
    except ChallengeRequired:
        print("Instagram triggered a security challenge.")
        print("Please go to the Instagram app or website on your phone/computer to approve this login.")
        print("After approving, try again.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during login: {e}")
        return None

    # Save session for next time
    try:
        cl.dump_settings(str(settings_path))
        print(f"Session settings saved to {settings_path}")
    except Exception as e:
        print(f"Could not save session settings: {e}")

    return cl


def post_instagram_photo(
    image_path: str,
    caption: str,
    username: Optional[str] = None,
    password: Optional[str] = None,
    settings_path: str = "ig_settings.json"
) -> Optional[str]:
    """
    Post a single photo to Instagram with a caption.
    
    Args:
        image_path: Path to the image file
        caption: Caption text for the post
        username: Instagram username (if None, uses IG_USERNAME env var)
        password: Instagram password (if None, uses IG_PASSWORD env var)
        settings_path: Path to save session settings
    
    Returns:
        str: Post URL if successful, None if failed
    """
    print(f"📸 Instagram: Starting photo upload...")
    print(f"   Image: {image_path}")
    print(f"   Caption length: {len(caption)} characters")
    
    # Get credentials
    if not username:
        username = os.getenv("IG_USERNAME")
    if not password:
        password = os.getenv("IG_PASSWORD")
    
    if not username or not password:
        print("❌ Instagram credentials not found. Set IG_USERNAME and IG_PASSWORD environment variables.")
        return None
    
    img_path = Path(image_path).expanduser().resolve()
    if not img_path.exists():
        print(f"❌ Image not found: {img_path}")
        return None

    settings_file = Path(settings_path).expanduser().resolve()

    # Log in to Instagram
    client = login_client(username, password, settings_file)
    if not client:
        print("❌ Instagram login failed. Aborting upload.")
        return None

    # Prepare image for upload (convert, resize, fix orientation)
    upload_path = prepare_image(img_path)

    # Upload the photo
    try:
        print(f"📤 Uploading {upload_path} to Instagram...")
        media = client.photo_upload(str(upload_path), caption)
        media_url = f"https://www.instagram.com/p/{media.code}/"
        print("✅ Success! Your photo has been uploaded to Instagram.")
        print(f"   Post Code: {media.code}")
        print(f"   Post URL: {media_url}")
        return media_url
    except Exception as e:
        print(f"❌ Error occurred during Instagram upload: {e}")
        return None
    finally:
        # Clean up the temporary .upload.jpg file if one was created
        if upload_path != img_path and upload_path.exists():
            try:
                upload_path.unlink()
                print(f"🗑️ Removed temporary file: {upload_path}")
            except Exception as e:
                print(f"⚠️ Could not remove temporary file {upload_path}: {e}")


def post_instagram_carousel(
    image_paths: List[str],
    caption: str,
    username: Optional[str] = None,
    password: Optional[str] = None,
    settings_path: str = "ig_settings.json"
) -> Optional[str]:
    """
    Post multiple photos as a carousel to Instagram.
    
    Args:
        image_paths: List of paths to image files
        caption: Caption text for the post
        username: Instagram username (if None, uses IG_USERNAME env var)
        password: Instagram password (if None, uses IG_PASSWORD env var)
        settings_path: Path to save session settings
    
    Returns:
        str: Post URL if successful, None if failed
    """
    print(f"📸 Instagram: Starting carousel upload...")
    print(f"   Images: {len(image_paths)} photos")
    print(f"   Caption length: {len(caption)} characters")
    
    # Get credentials
    if not username:
        username = os.getenv("IG_USERNAME")
    if not password:
        password = os.getenv("IG_PASSWORD")
    
    if not username or not password:
        print("❌ Instagram credentials not found. Set IG_USERNAME and IG_PASSWORD environment variables.")
        return None
    
    # Check all images exist
    for img_path in image_paths:
        if not Path(img_path).exists():
            print(f"❌ Image not found: {img_path}")
            return None

    settings_file = Path(settings_path).expanduser().resolve()

    # Log in to Instagram
    client = login_client(username, password, settings_file)
    if not client:
        print("❌ Instagram login failed. Aborting upload.")
        return None

    # Prepare images for upload
    upload_paths = []
    for img_path in image_paths:
        upload_path = prepare_image(Path(img_path))
        upload_paths.append(str(upload_path))

    # Upload the carousel
    try:
        print(f"📤 Uploading carousel to Instagram...")
        media = client.album_upload(upload_paths, caption)
        media_url = f"https://www.instagram.com/p/{media.code}/"
        print("✅ Success! Your carousel has been uploaded to Instagram.")
        print(f"   Post Code: {media.code}")
        print(f"   Post URL: {media_url}")
        return media_url
    except Exception as e:
        print(f"❌ Error occurred during Instagram carousel upload: {e}")
        return None
    finally:
        # Clean up temporary files
        for upload_path in upload_paths:
            if upload_path != img_path and Path(upload_path).exists():
                try:
                    Path(upload_path).unlink()
                    print(f"🗑️ Removed temporary file: {upload_path}")
                except Exception as e:
                    print(f"⚠️ Could not remove temporary file {upload_path}: {e}")


# Example usage:
if __name__ == "__main__":
    # Test single photo upload
    result = post_instagram_photo(
        image_path="casino.jpg",
        caption="Test post from LinkedIn Post Generator! #AI #Automation 🚀"
    )
    if result:
        print(f"Posted successfully: {result}")
    else:
        print("Post failed")
