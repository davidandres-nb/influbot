from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Literal
import os
from dotenv import load_dotenv

# Load environment variables BEFORE importing modules that need them
load_dotenv()

# Verify environment variables are loaded
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    print("WARNING: OPENAI_API_KEY not found in environment variables")
    print("Available env vars:", [k for k in os.environ.keys() if 'OPENAI' in k or 'API' in k])

try:
    from post_generator import run_workflow
    print("✅ post_generator imported successfully")
except Exception as e:
    print(f"❌ Failed to import post_generator: {e}")
    raise

try:
    from linkedin_post import post_linkedin_images_text
    print("✅ linkedin_post imported successfully")
except Exception as e:
    print(f"❌ Failed to import linkedin_post: {e}")
    raise

try:
    from image_generator import generate_linkedin_image, cleanup_image
    print("✅ image_generator imported successfully")
except Exception as e:
    print(f"❌ Failed to import image_generator: {e}")
    raise

app = FastAPI(
    title="LinkedIn Post Generator API",
    description="API to generate and optionally post LinkedIn posts using AI",
    version="1.0.0"
)

class PostRequest(BaseModel):
    terms: List[str]
    topic: str
    audience_profile: str = "professionals"
    language: str = "English"
    register: str = "professional"
    company_focus: Optional[Dict[str, str]] = None
    content_instructions: Optional[str] = None
    country: Optional[str] = None
    start_date: Optional[str] = None
    data_types: Optional[List[str]] = None
    source_language: Optional[str] = None
    enable_company_search: bool = True
    max_fetch: int = 30
    top_k: int = 5
    max_chars: int = 1900
    article_usage: Literal["direct_reference", "informational_synthesis", "examples"] = "informational_synthesis"
    include_links: bool = True
    links_in_char_limit: bool = True
    verbose: bool = False
    
    # LinkedIn posting parameters
    should_post: bool = False
    linkedin_token: Optional[str] = None
    author_urn: Optional[str] = None
    image_paths: Optional[List[str]] = None
    alt_texts: Optional[List[str]] = None
    visibility: str = "PUBLIC"
    
    # Image generation parameters
    generate_image: bool = False
    image_model: str = "gpt-4o"
    image_size: str = "1024x1024"
    custom_image_prompt: Optional[str] = None

class PostResponse(BaseModel):
    success: bool
    post_content: str
    post_urn: Optional[str] = None
    message: str

@app.get("/")
async def root():
    return {"message": "LinkedIn Post Generator API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/env-check")
async def env_check():
    """Check if environment variables are properly loaded"""
    return {
        "openai_key_set": bool(os.getenv("OPENAI_API_KEY")),
        "openai_model": os.getenv("OPENAI_MODEL", "not_set"),
        "eventregistry_key_set": bool(os.getenv("EVENTREGISTRY_API_KEY")),
        "newsapi_key_set": bool(os.getenv("NEWSAPI_KEY")),
        "linkedin_token_set": bool(os.getenv("LINKEDIN_ACCESS_TOKEN")),
        "linkedin_urn_set": bool(os.getenv("LINKEDIN_AUTHOR_URN"))
    }

@app.post("/generate-post", response_model=PostResponse)
async def generate_post(request: PostRequest):
    """
    Generate a LinkedIn post using AI. Optionally post it to LinkedIn if should_post is True.
    """
    try:
        print(f"🚀 Starting post generation...")
        print(f"   Topic: {request.topic}")
        print(f"   Terms: {', '.join(request.terms)}")
        print(f"   Audience: {request.audience_profile}")
        print(f"   Max chars: {request.max_chars}")
        
        # Generate the post content
        print(f"📝 Generating AI content...")
        try:
            # Convert async context to sync for run_workflow
            import asyncio
            loop = asyncio.get_event_loop()
            post_content = await loop.run_in_executor(None, lambda: run_workflow(
                terms=request.terms,
                topic=request.topic,
                audience_profile=request.audience_profile,
                language=request.language,
                register=request.register,
                company_focus=request.company_focus,
                content_instructions=request.content_instructions,
                country=request.country,
                start_date=request.start_date,
                data_types=request.data_types or ["news", "blog"],
                source_language=request.source_language,
                enable_company_search=request.enable_company_search,
                max_fetch=request.max_fetch,
                top_k=request.top_k,
                output_kind="linkedin_post",
                output_format="text",
                max_chars=request.max_chars,
                article_usage=request.article_usage,
                include_links=request.include_links,
                links_in_char_limit=request.links_in_char_limit,
                verbose=request.verbose
            ))
        except Exception as workflow_error:
            print(f"❌ Error in run_workflow: {str(workflow_error)}")
            print(f"   Error type: {type(workflow_error).__name__}")
            raise workflow_error
        
        print(f"✅ Content generated successfully!")
        print(f"   Content length: {len(post_content)} characters")
        print(f"   Preview: {post_content[:100]}...")
        
        # Generate image if requested
        generated_image_path = None
        if request.generate_image:
            print(f"🎨 Image generation requested...")
            try:
                if request.custom_image_prompt:
                    print(f"🎨 Using custom prompt guidelines: {request.custom_image_prompt[:100]}...")
                else:
                    print("🤖 Using standard prompt based on post content")
                
                generated_image_path = generate_linkedin_image(
                    post_content=post_content,
                    openai_api_key=openai_key,
                    model=request.image_model,
                    size=request.image_size,
                    custom_prompt=request.custom_image_prompt
                )
                print(f"✅ Image generated successfully!")
                print(f"   Image path: {generated_image_path}")
                
                # Add generated image to image_paths if not already provided
                if not request.image_paths:
                    request.image_paths = []
                request.image_paths.append(generated_image_path)
                
                # Add alt text for the generated image
                if not request.alt_texts:
                    request.alt_texts = []
                request.alt_texts.append("AI-generated professional image for LinkedIn post")
                
            except Exception as e:
                print(f"❌ Image generation failed: {str(e)}")
                print(f"   Error type: {type(e).__name__}")
                # Continue without image if generation fails
                generated_image_path = None
        
        post_urn = None
        message = "Post generated successfully"
        if generated_image_path:
            message += " with AI-generated image"
        
        # Post to LinkedIn if requested
        if request.should_post:
            print(f"🔗 LinkedIn posting requested...")
            if not request.linkedin_token:
                print(f"❌ LinkedIn token missing!")
                raise HTTPException(
                    status_code=400, 
                    detail="LinkedIn token is required when should_post is True"
                )
            if not request.author_urn:
                print(f"❌ LinkedIn author URN missing!")
                raise HTTPException(
                    status_code=400, 
                    detail="LinkedIn author URN is required when should_post is True"
                )
            
            print(f"📤 Posting to LinkedIn...")
            print(f"   Author URN: {request.author_urn}")
            print(f"   Visibility: {request.visibility}")
            print(f"   Images: {len(request.image_paths or [])} image(s)")
            print(f"   Image paths: {request.image_paths}")
            print(f"   Alt texts: {request.alt_texts}")
            
            try:
                # Post to LinkedIn
                post_urn = post_linkedin_images_text(
                    token=request.linkedin_token,
                    author_urn=request.author_urn,
                    commentary=post_content,
                    image_paths=request.image_paths or [],
                    alt_texts=request.alt_texts,
                    visibility=request.visibility
                )
                print(f"✅ LinkedIn post successful!")
                print(f"   Post URN: {post_urn}")
                message = "Post generated and posted to LinkedIn successfully"
                if generated_image_path:
                    message += " with AI-generated image"
            except Exception as e:
                import traceback
                error_details = f"Failed to post to LinkedIn: {str(e)}"
                if hasattr(e, '__traceback__'):
                    error_details += f"\n\nLinkedIn Error Traceback:\n{''.join(traceback.format_tb(e.__traceback__))}"
                raise HTTPException(
                    status_code=500,
                    detail=error_details
                )
        
        print(f"🎉 All done! Returning response...")
        
        # Clean up generated image after successful posting
        if generated_image_path and os.path.exists(generated_image_path):
            try:
                cleanup_image(generated_image_path)
                print(f"🗑️  Generated image cleaned up successfully")
            except Exception as cleanup_error:
                print(f"⚠️  Failed to cleanup generated image: {str(cleanup_error)}")
        
        return PostResponse(
            success=True,
            post_content=post_content,
            post_urn=post_urn,
            message=message
        )
        
    except Exception as e:
        import traceback
        error_details = f"Failed to generate post: {str(e)}"
        try:
            if hasattr(e, '__traceback__'):
                tb_lines = traceback.format_tb(e.__traceback__)
                error_details += f"\n\nTraceback:\n{''.join(tb_lines)}"
        except Exception as tb_error:
            error_details += f"\n\nTraceback formatting failed: {str(tb_error)}"
        
        print(f"❌ Error in generate_post: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        
        raise HTTPException(
            status_code=500,
            detail=error_details
        )

@app.post("/generate-only", response_model=PostResponse)
async def generate_only(request: PostRequest):
    """
    Generate a LinkedIn post without posting it to LinkedIn.
    """
    print(f"📝 Generate-only mode - no LinkedIn posting")
    # Override should_post to False
    request.should_post = False
    return await generate_post(request)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
