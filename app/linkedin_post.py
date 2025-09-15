import os
import mimetypes
from typing import List, Optional, Tuple
import requests


def post_linkedin_images_text(
    token: str,
    author_urn: str,                       # e.g. "urn:li:person:silLGwf55c"
    commentary: str,                       # your post text, keep under ~3000 chars
    image_paths: List[str],                # 1..N local file paths
    alt_texts: Optional[List[str]] = None, # optional per-image alt text
    visibility: str = "PUBLIC",            # or "CONNECTIONS"
    linkedin_version: str = "202508"       # YYYYMM as per LinkedIn docs
) -> str:
    print(f"🔗 LinkedIn: Starting post creation...")
    print(f"   Text length: {len(commentary)} characters")
    print(f"   Images: {len(image_paths)} image(s)")
    print(f"   Image paths: {image_paths}")
    print(f"   Alt texts: {alt_texts}")
    print(f"   Visibility: {visibility}")
    """
    Returns the created post URN on success. Raises an exception on error.
    Requires the 'requests' package and a member access token with scope w_member_social.
    """

    if len(commentary) > 3000:
        raise ValueError("Commentary is over 3000 characters")
    
    # Handle text-only posts (no images)
    if not image_paths:
        # Text-only post - LinkedIn requires some content structure
        content = None  # Will be omitted from the request body
    else:
        # Post with images - content will be set later after image upload
        content = None  # Placeholder, will be set after image upload

    H_BASE = {
        "Authorization": f"Bearer {token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "LinkedIn-Version": linkedin_version,
    }

    def _init_image_upload(owner_urn: str) -> Tuple[str, str]:
        url = "https://api.linkedin.com/rest/images?action=initializeUpload"
        body = {"initializeUploadRequest": {"owner": owner_urn}}
        r = requests.post(url, headers={**H_BASE, "Content-Type": "application/json"}, json=body, timeout=60)
        if r.status_code != 200:
            raise RuntimeError(f"initializeUpload failed {r.status_code}: {r.text}")
        value = r.json().get("value") or {}
        upload_url = value.get("uploadUrl")
        image_urn = value.get("image")
        if not upload_url or not image_urn:
            raise RuntimeError(f"Missing uploadUrl or image URN in response: {r.text}")
        return upload_url, image_urn

    def _put_image(upload_url: str, path: str) -> None:
        mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
        with open(path, "rb") as f:
            data = f.read()
        r = requests.put(upload_url, headers={"Authorization": f"Bearer {token}", "Content-Type": mime}, data=data, timeout=120)
        if r.status_code not in (200, 201):
            raise RuntimeError(f"Binary upload failed {r.status_code}: {r.text}")

    # 1) Upload all images and collect URNs (only if images provided)
    image_urns: List[str] = []
    if image_paths:
        print(f"🖼️  LinkedIn: Uploading {len(image_paths)} image(s)...")
        for i, p in enumerate(image_paths):
            print(f"   Image {i+1}/{len(image_paths)}: {os.path.basename(p)}")
            if not os.path.isfile(p):
                raise FileNotFoundError(f"Image not found: {p}")
            print(f"     Initializing upload...")
            upload_url, image_urn = _init_image_upload(author_urn)
            print(f"     Uploading binary data...")
            _put_image(upload_url, p)
            image_urns.append(image_urn)
            print(f"     ✅ Image {i+1} uploaded successfully")
    else:
        print(f"📝 LinkedIn: Text-only post (no images)")

    # 2) Build content for single or multi image post (only if images provided)
    if image_paths:
        if len(image_urns) == 1:
            content = {"media": {"id": image_urns[0]}}
            print(f"   📸 Single image content: {content}")
        else:
            items = []
            for i, urn in enumerate(image_urns):
                item = {"id": urn}
                if alt_texts and i < len(alt_texts) and alt_texts[i]:
                    item["altText"] = alt_texts[i]
                items.append(item)
            content = {"multiImage": {"images": items}}
            print(f"   📸 Multi-image content: {content}")
    else:
        print(f"   📝 No images, content remains None")
    # content is already set to {} for text-only posts

    # 3) Create the post
    print(f"📤 LinkedIn: Creating post...")
    posts_url = "https://api.linkedin.com/rest/posts"
    body = {
        "author": author_urn,
        "commentary": commentary,
        "visibility": visibility,
        "lifecycleState": "PUBLISHED",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": []
        },
        "isReshareDisabledByAuthor": False
    }
    
    # Only add content field if we have images
    if content is not None:
        body["content"] = content
        print(f"   📤 Final request body includes content: {body['content']}")
    else:
        print(f"   📤 Final request body has no content field")
    print(f"   Sending POST request to LinkedIn API...")
    r = requests.post(posts_url, headers={**H_BASE, "Content-Type": "application/json"}, json=body, timeout=60)
    if r.status_code not in (201, 202):
        print(f"   ❌ LinkedIn API error: {r.status_code}")
        raise RuntimeError(f"Create post failed {r.status_code}: {r.text}")
    print(f"   ✅ LinkedIn API response: {r.status_code}")

    # Post URN is usually in the x-restli-id header
    post_urn = r.headers.get("x-restli-id") or ""
    if not post_urn:
        try:
            post_urn = r.json().get("id", "")
        except Exception:
            post_urn = ""
    if not post_urn:
        raise RuntimeError("Could not determine the post URN from the response")

    print(f"🎉 LinkedIn: Post created successfully!")
    print(f"   Post URN: {post_urn}")
    return post_urn


# Example usage:
# urn = post_linkedin_images_text(
#     token=ACCESS_TOKEN,
#     author_urn=AUTHOR_URN,
#     commentary="These are the 4 pillars of context engineering",
#     image_paths=[r"C:\Users\andre\Documents\mlpills\issue103.png"],
#     alt_texts=["context engineering"],
#     visibility="PUBLIC",
# )
# print("Created post:", urn)
