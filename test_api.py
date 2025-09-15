#!/usr/bin/env python3
"""
Simple test script for the LinkedIn Post Generator API
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API base URL
BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint"""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_generate_only():
    """Test generating a post without posting to LinkedIn"""
    print("Testing generate-only endpoint...")
    
    payload = {
        "terms": ["AI", "automation", "productivity"],
        "topic": "AI Tools for Business Productivity",
        "audience_profile": "business owners",
        "language": "English",
        "register": "professional",
        "max_chars": 1000,
        "content_instructions": "Make it engaging and include a call-to-action"
    }
    
    response = requests.post(
        f"{BASE_URL}/generate-only",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data['success']}")
        print(f"Message: {data['message']}")
        print(f"Post Content: {data['post_content'][:200]}...")
    else:
        print(f"Error: {response.text}")
    print()

def test_generate_post():
    """Test generating a post with LinkedIn posting"""
    print("Testing generate-post endpoint...")
    
    # Get LinkedIn credentials from environment variables
    linkedin_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    author_urn = os.getenv("LINKEDIN_AUTHOR_URN")
    
    if not linkedin_token or not author_urn:
        print("⚠️  LinkedIn credentials not found in environment variables.")
        print("   Set LINKEDIN_ACCESS_TOKEN and LINKEDIN_AUTHOR_URN in your .env file")
        print("   Skipping LinkedIn posting test...")
        return
    
    print("✅ LinkedIn credentials found, testing full generate + post flow...")
    
    payload = {
        "terms": ["AI", "automation", "productivity"],
        "topic": "AI Tools for Business Productivity",
        "audience_profile": "business owners",
        "language": "English",
        "register": "professional",
        "max_chars": 1000,
        "should_post": True,
        "linkedin_token": linkedin_token,
        "author_urn": author_urn
    }
    
    response = requests.post(
        f"{BASE_URL}/generate-post",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data['success']}")
        print(f"Message: {data['message']}")
    else:
        print(f"Error: {response.text}")
    print()

if __name__ == "__main__":
    print("LinkedIn Post Generator API Test")
    print("=" * 40)
    
    try:
        test_health()
        # test_generate_only()
        test_generate_post()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API. Make sure it's running on http://localhost:8000")
    except Exception as e:
        print(f"Error: {e}")
