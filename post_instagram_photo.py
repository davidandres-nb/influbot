#!/usr/bin/env python3
"""
Post a single image with a caption to Instagram using instagrapi.

Usage:
  python post_instagram_photo.py --image /path/to/photo.jpg --caption "Hello Instagram"

Optional flags:
  --username USERNAME         Instagram username, otherwise read from IG_USERNAME env var or prompt
  --password PASSWORD         Instagram password, otherwise read from IG_PASSWORD env var or prompt (hidden)
  --settings SETTINGS.json    Path to save or load session settings, default: ig_settings.json

Requirements:
  pip install instagrapi Pillow
"""

import argparse
import os
import sys
from getpass import getpass
from pathlib import Path
from typing import Optional

try:
    from instagrapi import Client
    from instagrapi.exceptions import TwoFactorRequired, ChallengeRequired
except Exception as e:
    print("instagrapi is not installed. Please run: pip install instagrapi", file=sys.stderr)
    raise

# Pillow is optional but helps convert non-JPEG formats cleanly
try:
    from PIL import Image, ImageOps
except Exception:
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
            # Some formats like PNG/WEBP/HEIC can cause issues, convert to JPEG
            suffix = path.suffix.lower()
            if suffix not in (".jpg", ".jpeg"):
                out_path = path.with_suffix(".upload.jpg")
                # Use exif transpose to fix orientation
                im = ImageOps.exif_transpose(im)
                # Basic size normalisation that plays nicely with Instagram
                # Keep aspect ratio, max width 1080
                if im.width > 1080:
                    new_h = int(im.height * (1080 / im.width))
                    im = im.resize((1080, new_h))
                im.save(out_path, format="JPEG", quality=95, optimize=True)
                return out_path
            else:
                # For JPEG, still fix orientation
                im = ImageOps.exif_transpose(im)
                # If we modified orientation, write to a temp to preserve fix
                out_path = path.with_suffix(".upload.jpg")
                im.save(out_path, format="JPEG", quality=95, optimize=True)
                return out_path
    except Exception:
        # If anything goes wrong, fall back to original path
        return path


def login_client(username: str, password: str, settings_path: Path) -> Client:
    cl = Client()

    # Load previous session settings if available to reduce chances of challenge
    if settings_path.exists():
        try:
            cl.load_settings(str(settings_path))
        except Exception:
            pass

    # Simple handler for challenge codes delivered by email/SMS
    def code_handler(username, choice):
        print(f"A verification code was requested via {choice}.")
        return input("Enter the code you received: ").strip()

    cl.challenge_code_handler = code_handler

    try:
        cl.login(username, password)
    except TwoFactorRequired:
        code = input("Two-factor code required. Enter your 2FA code: ").strip()
        cl.two_factor_login(username, password, code)
    except ChallengeRequired:
        print("Instagram triggered a challenge. Approve the login from the Instagram app or email, then try again.", file=sys.stderr)
        sys.exit(2)

    # Save session for next time
    try:
        cl.dump_settings(str(settings_path))
    except Exception:
        pass

    return cl


def main(argv=None):
    parser = argparse.ArgumentParser(description="Post a photo with a caption to Instagram using instagrapi.")
    parser.add_argument("--image", required=True, help="Path to the image to upload")
    parser.add_argument("--caption", required=True, help="Caption text for the post")
    parser.add_argument("--username", help="Instagram username, or set IG_USERNAME env var")
    parser.add_argument("--password", help="Instagram password, or set IG_PASSWORD env var")
    parser.add_argument("--settings", default="ig_settings.json", help="Path to session settings JSON")
    args = parser.parse_args(argv)

    img_path = Path(args.image).expanduser().resolve()
    if not img_path.exists():
        print(f"Image not found: {img_path}", file=sys.stderr)
        sys.exit(1)

    username = args.username or os.getenv("IG_USERNAME") or input("Instagram username: ").strip()
    password = args.password or os.getenv("IG_PASSWORD") or getpass("Instagram password: ").strip()

    settings_path = Path(args.settings).expanduser().resolve()

    # Prepare image for upload
    upload_path = prepare_image(img_path)

    # Log in and upload
    cl = login_client(username, password, settings_path)

    print("Uploading...")
    media = cl.photo_upload(str(upload_path), args.caption)

    # Clean up temp file if we created one
    if upload_path != img_path and upload_path.exists():
        try:
            upload_path.unlink()
        except Exception:
            pass

    try:
        media_url = f"https://www.instagram.com/p/{media.code}/"
    except Exception:
        media_url = "(URL unavailable)"

    print("Success. Post code:", getattr(media, "code", None))
    print("Post URL:", media_url)


if __name__ == "__main__":
    main()
