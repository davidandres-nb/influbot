import streamlit as st
import os
import tempfile
from typing import List, Optional, Dict
from dotenv import load_dotenv
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add app directory to path for imports
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="LinkedIn Post Generator",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #0077b5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #333;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #0077b5;
        padding-bottom: 0.5rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.375rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 0.375rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 0.375rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .stTextArea > div > div > textarea {
        min-height: 100px;
    }
    .metric-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 0.375rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'generated_post' not in st.session_state:
    st.session_state.generated_post = None
if 'post_urn' not in st.session_state:
    st.session_state.post_urn = None
if 'used_sources' not in st.session_state:
    st.session_state.used_sources = []

def check_environment():
    """Check if required environment variables are set"""
    required_vars = {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'EVENTREGISTRY_API_KEY': os.getenv('EVENTREGISTRY_API_KEY'),
        'NEWSAPI_KEY': os.getenv('NEWSAPI_KEY'),
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    return missing_vars

def check_linkedin_config():
    """Check LinkedIn configuration"""
    linkedin_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
    linkedin_urn = os.getenv('LINKEDIN_AUTHOR_URN')
    return linkedin_token, linkedin_urn

def generate_post_direct(terms, topic, audience_profile, **kwargs):
    """Directly call the post generator without API"""
    try:
        from post_generator import run_workflow
        return run_workflow(
            terms=terms,
            topic=topic,
            audience_profile=audience_profile,
            **kwargs
        )
    except Exception as e:
        st.error(f"Error generating post: {str(e)}")
        return None

def post_to_linkedin_direct(token, author_urn, commentary, image_paths=None, alt_texts=None, visibility="PUBLIC"):
    """Directly post to LinkedIn without API"""
    try:
        from linkedin_post import post_linkedin_images_text
        return post_linkedin_images_text(
            token=token,
            author_urn=author_urn,
            commentary=commentary,
            image_paths=image_paths or [],
            alt_texts=alt_texts,
            visibility=visibility
        )
    except Exception as e:
        st.error(f"Error posting to LinkedIn: {str(e)}")
        return None

def generate_image_direct(post_content, openai_api_key, model="gpt-image-1", size="1024x1024"):
    """Generate AI image directly"""
    try:
        from image_generator import generate_linkedin_image
        return generate_linkedin_image(
            post_content=post_content,
            openai_api_key=openai_api_key,
            model=model,
            size=size
        )
    except Exception as e:
        st.error(f"Error generating image: {str(e)}")
        return None

def main():
    # Header
    st.markdown('<h1 class="main-header">🔗 LinkedIn Post Generator</h1>', unsafe_allow_html=True)
    st.markdown("Generate AI-powered LinkedIn posts with news research and optional image generation")
    
    # Sidebar for configuration
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")
        
        # Environment Check
        st.markdown("### Environment Status")
        missing_vars = check_environment()
        if missing_vars:
            st.error(f"Missing environment variables: {', '.join(missing_vars)}")
        else:
            st.success("✅ Required environment variables are set")
        
        # LinkedIn Configuration
        st.markdown("### LinkedIn Configuration")
        linkedin_token, linkedin_urn = check_linkedin_config()
        if linkedin_token and linkedin_urn:
            st.success("✅ LinkedIn credentials configured")
        else:
            st.warning("⚠️ LinkedIn credentials not configured")
            st.info("Set LINKEDIN_ACCESS_TOKEN and LINKEDIN_AUTHOR_URN in your .env file")
        
        # Quick stats
        st.markdown("### Quick Stats")
        if st.session_state.generated_post:
            st.metric("Post Length", f"{len(st.session_state.generated_post)} chars")
            st.metric("Sources Used", len(st.session_state.used_sources))
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["📝 Generate Post", "🔧 Settings", "📊 Results"])
    
    with tab1:
        st.markdown('<div class="section-header">Post Generation</div>', unsafe_allow_html=True)
        
        # Create form
        with st.form("post_generation_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Basic Information")
                
                # Topic and terms
                topic = st.text_input(
                    "Main Topic *",
                    placeholder="e.g., AI Revolution in iGaming",
                    help="The main topic your post will focus on"
                )
                
                terms_input = st.text_area(
                    "Search Terms *",
                    placeholder="Enter search terms separated by commas\ne.g., AI casinos, AI sports betting, AI poker",
                    help="Keywords to search for relevant news articles"
                )
                
                audience_profile = st.selectbox(
                    "Target Audience",
                    ["professionals", "general readers", "technical audience", "business executives", "marketing professionals"],
                    help="This affects the tone and complexity of the content"
                )
                
                language = st.selectbox(
                    "Language",
                    ["English (UK)", "English (US)", "Spanish", "French", "German", "Italian", "Portuguese", "Dutch", "Japanese", "Chinese"],
                    help="Language for the generated content"
                )
                
                register = st.selectbox(
                    "Writing Style",
                    ["professional", "informal", "technical", "conversational", "formal"],
                    help="Tone and style of the writing"
                )
            
            with col2:
                st.markdown("### Content Settings")
                
                max_chars = st.slider(
                    "Maximum Characters",
                    min_value=500,
                    max_value=3000,
                    value=1900,
                    step=100,
                    help="Maximum length of the generated post"
                )
                
                article_usage = st.selectbox(
                    "How to use articles",
                    ["informational_synthesis", "direct_reference", "examples"],
                    help="How to incorporate information from articles"
                )
                
                include_links = st.checkbox(
                    "Include source links",
                    value=True,
                    help="Whether to include links to source articles"
                )
                
                links_in_char_limit = st.checkbox(
                    "Count links in character limit",
                    value=True,
                    help="Whether source links count toward the character limit"
                )
                
                enable_company_search = st.checkbox(
                    "Enable company verification",
                    value=True,
                    help="Search for additional information about companies online"
                )
            
            # Advanced settings (collapsible)
            with st.expander("🔧 Advanced Settings"):
                col3, col4 = st.columns(2)
                
                with col3:
                    st.markdown("#### Search Parameters")
                    
                    country = st.text_input(
                        "Country Filter",
                        placeholder="e.g., US, UK, DE",
                        help="Filter news by country (optional)"
                    )
                    
                    start_date = st.date_input(
                        "Start Date",
                        value=datetime.now() - timedelta(days=7),
                        help="Search for articles from this date onwards"
                    )
                    
                    data_types = st.multiselect(
                        "Content Types",
                        ["news", "blog", "pr"],
                        default=["news", "blog"],
                        help="Types of content to search for"
                    )
                    
                    max_fetch = st.slider(
                        "Max Articles to Fetch",
                        min_value=10,
                        max_value=100,
                        value=30,
                        step=5,
                        help="Maximum number of articles to fetch from news sources"
                    )
                    
                    top_k = st.slider(
                        "Top Articles to Use",
                        min_value=1,
                        max_value=10,
                        value=5,
                        step=1,
                        help="Number of best articles to use for content generation"
                    )
                
                with col4:
                    st.markdown("#### Company Focus")
                    
                    company_focus_text = st.text_area(
                        "Companies to Highlight",
                        placeholder="Company Name: Description\nAnother Company: Another description",
                        help="Companies to mention in the post with their descriptions"
                    )
                    
                    content_instructions = st.text_area(
                        "Custom Instructions",
                        placeholder="e.g., Include a call-to-action, start with a question, add emojis",
                        help="Specific instructions for content generation"
                    )
            
            # LinkedIn posting settings
            st.markdown("### LinkedIn Posting")
            
            col5, col6 = st.columns(2)
            
            with col5:
                should_post = st.checkbox(
                    "Post to LinkedIn",
                    value=False,
                    help="Whether to automatically post to LinkedIn after generation"
                )
                
                if should_post:
                    linkedin_token_input = st.text_input(
                        "LinkedIn Access Token",
                        value=linkedin_token or "",
                        type="password",
                        help="Your LinkedIn API access token"
                    )
                    
                    linkedin_urn_input = st.text_input(
                        "LinkedIn Author URN",
                        value=linkedin_urn or "",
                        placeholder="urn:li:person:your_id_here",
                        help="Your LinkedIn author URN"
                    )
                else:
                    linkedin_token_input = ""
                    linkedin_urn_input = ""
            
            with col6:
                generate_image = st.checkbox(
                    "Generate AI Image",
                    value=False,
                    help="Generate an AI image to accompany the post"
                )
                
                if generate_image:
                    image_model = st.selectbox(
                        "Image Model",
                        ["gpt-image-1", "dall-e-3", "dall-e-2"],
                        help="AI model to use for image generation"
                    )
                    
                    image_size = st.selectbox(
                        "Image Size",
                        ["1024x1024", "1792x1024", "1024x1792"],
                        help="Size of the generated image"
                    )
            
            # Submit button
            submitted = st.form_submit_button(
                "🚀 Generate Post",
                type="primary",
                use_container_width=True
            )
        
        # Process form submission
        if submitted:
            if not topic or not terms_input:
                st.error("Please fill in the required fields: Topic and Search Terms")
                return
            
            # Parse search terms
            terms = [term.strip() for term in terms_input.split(',') if term.strip()]
            
            # Parse company focus
            company_focus = {}
            if company_focus_text:
                for line in company_focus_text.split('\n'):
                    if ':' in line:
                        company, description = line.split(':', 1)
                        company_focus[company.strip()] = description.strip()
            
            # Show progress
            with st.spinner("Generating post... This may take a few minutes."):
                # Prepare parameters
                params = {
                    "language": language,
                    "register": register,
                    "company_focus": company_focus if company_focus else None,
                    "content_instructions": content_instructions if content_instructions else None,
                    "country": country if country else None,
                    "start_date": start_date.isoformat() if start_date else None,
                    "data_types": data_types,
                    "enable_company_search": enable_company_search,
                    "max_fetch": max_fetch,
                    "top_k": top_k,
                    "output_kind": "linkedin_post",
                    "output_format": "text",
                    "max_chars": max_chars,
                    "article_usage": article_usage,
                    "include_links": include_links,
                    "links_in_char_limit": links_in_char_limit,
                    "verbose": True
                }
                
                # Generate the post
                post_content = generate_post_direct(terms, topic, audience_profile, **params)
                
                if post_content:
                    st.session_state.generated_post = post_content
                    st.success("✅ Post generated successfully!")
                    
                    # Generate image if requested
                    generated_image_path = None
                    if generate_image:
                        with st.spinner("Generating AI image..."):
                            openai_key = os.getenv('OPENAI_API_KEY')
                            if openai_key:
                                generated_image_path = generate_image_direct(
                                    post_content, 
                                    openai_key, 
                                    image_model, 
                                    image_size
                                )
                                if generated_image_path:
                                    st.success("✅ AI image generated successfully!")
                                else:
                                    st.warning("⚠️ Image generation failed, continuing without image")
                            else:
                                st.error("❌ OpenAI API key not found for image generation")
                    
                    # Post to LinkedIn if requested
                    if should_post and linkedin_token_input and linkedin_urn_input:
                        with st.spinner("Posting to LinkedIn..."):
                            image_paths = [generated_image_path] if generated_image_path else None
                            alt_texts = ["AI-generated professional image"] if generated_image_path else None
                            
                            post_urn = post_to_linkedin_direct(
                                token=linkedin_token_input,
                                author_urn=linkedin_urn_input,
                                commentary=post_content,
                                image_paths=image_paths,
                                alt_texts=alt_texts,
                                visibility="PUBLIC"
                            )
                            
                            if post_urn:
                                st.session_state.post_urn = post_urn
                                st.success(f"✅ Posted to LinkedIn successfully! Post URN: {post_urn}")
                            else:
                                st.error("❌ Failed to post to LinkedIn")
                    
                    # Clean up generated image
                    if generated_image_path and os.path.exists(generated_image_path):
                        try:
                            from image_generator import cleanup_image
                            cleanup_image(generated_image_path)
                        except:
                            pass
                    
                    # Switch to results tab
                    st.rerun()
                else:
                    st.error("❌ Failed to generate post. Please check the error messages above.")
    
    with tab2:
        st.markdown('<div class="section-header">Settings & Configuration</div>', unsafe_allow_html=True)
        
        st.markdown("### Environment Variables")
        st.info("Make sure your .env file contains the required API keys and tokens.")
        
        env_vars = {
            "OPENAI_API_KEY": "Required for AI content generation",
            "EVENTREGISTRY_API_KEY": "Required for news article search",
            "NEWSAPI_KEY": "Alternative to EventRegistry for news search",
            "LINKEDIN_ACCESS_TOKEN": "Required for posting to LinkedIn",
            "LINKEDIN_AUTHOR_URN": "Required for posting to LinkedIn"
        }
        
        for var, description in env_vars.items():
            status = "✅ Set" if os.getenv(var) else "❌ Not set"
            st.write(f"**{var}**: {status} - {description}")
        
        st.markdown("### Module Status")
        try:
            from post_generator import run_workflow
            st.success("✅ Post generator module loaded")
        except Exception as e:
            st.error(f"❌ Post generator module error: {e}")
        
        try:
            from linkedin_post import post_linkedin_images_text
            st.success("✅ LinkedIn post module loaded")
        except Exception as e:
            st.error(f"❌ LinkedIn post module error: {e}")
        
        try:
            from image_generator import generate_linkedin_image
            st.success("✅ Image generator module loaded")
        except Exception as e:
            st.error(f"❌ Image generator module error: {e}")
    
    with tab3:
        st.markdown('<div class="section-header">Generated Content</div>', unsafe_allow_html=True)
        
        if st.session_state.generated_post:
            # Display metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Character Count", len(st.session_state.generated_post))
            with col2:
                st.metric("Word Count", len(st.session_state.generated_post.split()))
            with col3:
                st.metric("LinkedIn Status", "Posted" if st.session_state.post_urn else "Not Posted")
            
            st.markdown("### Generated Post")
            st.text_area(
                "Post Content",
                value=st.session_state.generated_post,
                height=300,
                disabled=True
            )
            
            if st.session_state.post_urn:
                st.markdown("### LinkedIn Post")
                st.success(f"✅ Successfully posted to LinkedIn!")
                st.code(f"Post URN: {st.session_state.post_urn}")
            
            # Action buttons
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("📋 Copy to Clipboard", use_container_width=True):
                    st.write("Post content copied to clipboard!")
            
            with col2:
                if st.button("🔄 Generate New Post", use_container_width=True):
                    st.session_state.generated_post = None
                    st.session_state.post_urn = None
                    st.session_state.used_sources = []
                    st.rerun()
            
            with col3:
                if st.button("💾 Download as Text", use_container_width=True):
                    st.download_button(
                        label="Download Post",
                        data=st.session_state.generated_post,
                        file_name=f"linkedin_post_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
            
            with col4:
                if st.button("📊 View Sources", use_container_width=True):
                    if st.session_state.used_sources:
                        st.markdown("### Sources Used")
                        for i, source in enumerate(st.session_state.used_sources, 1):
                            st.write(f"**{i}.** {source.get('title', 'No title')}")
                            st.write(f"   Source: {source.get('source', 'Unknown')}")
                            st.write(f"   URL: {source.get('url', 'No URL')}")
                            st.write("---")
                    else:
                        st.info("No source information available")
        else:
            st.info("No post generated yet. Go to the 'Generate Post' tab to create a new post.")
            
            # Show example
            st.markdown("### Example Usage")
            st.code("""
Topic: AI Revolution in iGaming
Search Terms: AI casinos, AI sports betting, AI poker, AI bingo
Audience: iGaming professionals
Language: English (UK)
Style: Professional
Max Characters: 1900
            """, language="text")

if __name__ == "__main__":
    main()
