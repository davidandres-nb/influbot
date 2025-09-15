#!/usr/bin/env python3
"""
Test script for the full LinkedIn Post Generator API workflow
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API base URL
BASE_URL = "http://localhost:8000"

def test_full_workflow():
    """Test the complete generate + post workflow"""
    print("🚀 Testing Full LinkedIn Post Generator Workflow")
    print("=" * 60)
    
    # Check if LinkedIn credentials are available
    linkedin_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    author_urn = os.getenv("LINKEDIN_AUTHOR_URN")
    
    if not linkedin_token or not author_urn:
        print("❌ LinkedIn credentials not found in environment variables")
        print("   Set LINKEDIN_ACCESS_TOKEN and LINKEDIN_AUTHOR_URN in your .env file")
        print("   Skipping LinkedIn posting test...")
        return False
    
    print("✅ LinkedIn credentials found")
    print(f"   Token: {linkedin_token[:20]}...")
    print(f"   Author URN: {author_urn}")
    
    # Test payload matching the run_workflow example
    payload = {
        "terms": ["AI casinos", "AI sports betting", "AI poker", "AI bingo", "AI live casino"],
        "topic": "AI Revolution in iGaming",
        "audience_profile": "iGaming professionals",
        "language": "English (UK)",
        "register": "professional",
        
        # Companies to verify via web search
        "company_focus": {
            "Netbet": "NetBet is a regulated online gambling and betting company offering sports betting, casino, live dealer, poker and more across multiple markets. Founded in the early 2000s, it operates under licences in several European jurisdictions and is known for football sponsorships and a focus on security and fair play."
        },
        
        "content_instructions": """Include a call-to-action to embrace AI in iGaming. 
        Start with a thought-provoking question. 
        End with a vision of the future. 
        Do NOT say or mention that companies are not mentioned in sources.
        Add emojis for a more engaging, yet professional, post.""",
        
        "country": None,
        "start_date": "2025-08-01",
        "data_types": ["news", "blog"],
        "source_language": None,
        "max_fetch": 30,
        "top_k": 5,
        "max_chars": 1100,
        "article_usage": "informational_synthesis",
        "include_links": True,
        "links_in_char_limit": False,
        "verbose": True,
        "enable_company_search": True,
        
        # LinkedIn posting parameters
        "should_post": True,
        "linkedin_token": linkedin_token,
        "author_urn": author_urn,
        "visibility": "PUBLIC",
        
        # Image generation parameters
        "generate_image": True,
        "image_model": "gpt-image-1",
        "image_size": "1024x1024"
    }
    

    # payload = {
    #     "terms": ["AI nutrition", "AI in healthcare", "AI diet planning", "AI wellness", "AI fitness"],
    #     "topic": "AI-Powered Transformation in Nutrition and Health",
    #     "audience_profile": "Healthcare and wellness professionals, nutritionists, and health tech innovators",
    #     "language": "English (UK)",
    #     "register": "professional",
        
    #     # Companies to verify via web search
    #     "company_focus": {
    #         "Larry AI": "Larry AI (https://heylarry.app/) is an AI-powered nutrition and wellness platform that helps users make healthier choices with personalised, science-backed recommendations. It combines the latest in artificial intelligence with evidence-based nutrition to simplify healthy living."
    #     },
        
    #     "content_instructions": """Start with a thought-provoking question about the future of nutrition and health. 
    #     Highlight how AI is transforming personalised diets, preventive healthcare, and fitness tracking. 
    #     Include a call-to-action encouraging professionals to embrace AI solutions for better patient and consumer outcomes. 
    #     End with a visionary note on how AI could revolutionise global health and wellness. 
    #     Add emojis to make the post more engaging, while keeping it professional.""",
        
    #     "country": None,
    #     "start_date": "2025-08-01",
    #     "data_types": ["news", "blog"],
    #     "source_language": None,
    #     "max_fetch": 30,
    #     "top_k": 5,
    #     "max_chars": 1100,
    #     "article_usage": "informational_synthesis",
    #     "include_links": True,
    #     "links_in_char_limit": False,
    #     "verbose": True,
    #     "enable_company_search": True,
        
    #     # LinkedIn posting parameters
    #     "should_post": True,
    #     "linkedin_token": linkedin_token,
    #     "author_urn": author_urn,
    #     "visibility": "PUBLIC",
        
    #     # Image generation parameters
    #     "generate_image": True,
    #     "image_model": "gpt-image-1",
    #     "image_size": "1024x1024"
    # }

    print(f"📝 Payload prepared:")
    print(f"   Topic: {payload['topic']}")
    print(f"   Terms: {', '.join(payload['terms'])}")
    print(f"   Audience: {payload['audience_profile']}")
    print(f"   Company: {list(payload['company_focus'].keys())[0]}")
    print(f"   Max chars: {payload['max_chars']}")
    print(f"   Should post: {payload['should_post']}")
    print(f"   Generate image: {payload['generate_image']}")
    print(f"   Image model: {payload['image_model']}")
    
    try:
        print(f"\n📤 Calling generate-post endpoint...")
        
        response = requests.post(
            f"{BASE_URL}/generate-post",
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
            print(f"   LinkedIn URL: https://www.linkedin.com/feed/update/{data['post_urn']}/")
            
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

def test_generate_only():
    """Test generate-only mode (no LinkedIn posting)"""
    print(f"\n📝 Testing Generate-Only Mode")
    print("-" * 40)
    
    # Simplified payload for generate-only test
    payload = {
        "terms": ["AI", "automation", "productivity"],
        "topic": "AI Tools for Business Productivity",
        "audience_profile": "business owners",
        "language": "English",
        "register": "professional",
        "max_chars": 800,
        "content_instructions": "Make it engaging and include a call-to-action",
        "should_post": False  # This will be overridden by the endpoint
    }
    
    try:
        print(f"📤 Calling generate-only endpoint...")
        
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
    print("LinkedIn Post Generator API - Full Workflow Test")
    print("=" * 60)
    
    try:
        # Test health endpoint first
        print("🏥 Testing API health...")
        health_response = requests.get(f"{BASE_URL}/health")
        if health_response.status_code == 200:
            print("✅ API is healthy and running")
        else:
            print("❌ API health check failed")
            exit(1)
        
        # Test generate-only first (safer)
        # generate_success = test_generate_only()
        
        # Test full workflow with LinkedIn posting
        full_success = test_full_workflow()
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY:")
        # print(f"   Generate-only: {'✅ PASSED' if generate_success else '❌ FAILED'}")
        print(f"   Full workflow: {'✅ PASSED' if full_success else '❌ FAILED'}")
        
        # if generate_success and full_success:
        #     print("\n🎉 All tests passed! Your LinkedIn Post Generator API is working perfectly!")
        # elif generate_success:
        #     print("\n⚠️  Content generation works, but LinkedIn posting failed. Check your credentials.")
        if full_success:
            print("\n🎉 All tests passed! Your LinkedIn Post Generator API is working perfectly!")
        else:
            print("\n❌ Content generation failed. Check the API logs for details.")
            print("\n⚠️  LinkedIn posting works, but content generation failed. Check the API logs for details.")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API. Make sure it's running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
