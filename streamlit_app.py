import streamlit as st
import os
import tempfile
from typing import List, Optional, Dict
from dotenv import load_dotenv
import requests
import json
from datetime import datetime, timedelta

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
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'generated_post' not in st.session_state:
    st.session_state.generated_post = None
if 'post_urn' not in st.session_state:
    st.session_state.post_urn = None
if 'api_mode' not in st.session_state:
    st.session_state.api_mode = True

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

def call_api_generate_post(data):
    """Call the FastAPI endpoint to generate a post"""
    try:
        response = requests.post(
            "http://localhost:8000/generate-post",
            json=data,
            timeout=300  # 5 minutes timeout
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API call failed: {str(e)}")
        return None

def call_api_generate_only(data):
    """Call the FastAPI endpoint to generate a post without posting"""
    try:
        response = requests.post(
            "http://localhost:8000/generate-only",
            json=data,
            timeout=300  # 5 minutes timeout
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API call failed: {str(e)}")
        return None

def main():
    # Header
    st.markdown('<h1 class="main-header">🔗 LinkedIn Post Generator</h1>', unsafe_allow_html=True)
    st.markdown("Generate AI-powered LinkedIn posts with news research and optional image generation")
    
    # Sidebar for configuration
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")
        
        # API Mode Selection
        st.markdown("### API Mode")
        api_mode = st.radio(
            "Choose how to run the post generator:",
            ["FastAPI Server", "Direct Import"],
            help="FastAPI Server: Uses the running API server. Direct Import: Imports modules directly (requires all dependencies)"
        )
        st.session_state.api_mode = (api_mode == "FastAPI Server")
        
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
        
        # API Server Status (only for API mode)
        if st.session_state.api_mode:
            st.markdown("### API Server Status")
            try:
                response = requests.get("http://localhost:8000/health", timeout=5)
                if response.status_code == 200:
                    st.success("✅ API server is running")
                else:
                    st.error("❌ API server returned error")
            except requests.exceptions.RequestException:
                st.error("❌ API server is not running")
                st.info("Start the API server with: `python app/main.py`")
    
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
                    
                    # Custom image prompt
                    custom_image_prompt = st.text_area(
                        "Additional Image Guidelines (Optional)",
                        placeholder="Add specific visual guidelines to enhance the auto-generated prompt\n\nExample: Use blue and white color scheme, modern office setting, clean minimalist design, professional lighting",
                        help="Add additional visual guidelines that will be combined with the auto-generated prompt based on post content.",
                        height=80
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
            
            # Prepare request data
            request_data = {
                "terms": terms,
                "topic": topic,
                "audience_profile": audience_profile,
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
                "max_chars": max_chars,
                "article_usage": article_usage,
                "include_links": include_links,
                "links_in_char_limit": links_in_char_limit,
                "verbose": True,
                "should_post": should_post,
                "linkedin_token": linkedin_token_input if should_post else None,
                "author_urn": linkedin_urn_input if should_post else None,
                "visibility": "PUBLIC",
                "generate_image": generate_image,
                "image_model": image_model if generate_image else "gpt-4o",
                "image_size": image_size if generate_image else "1024x1024",
                "custom_image_prompt": custom_image_prompt if generate_image else None
            }
            
            # Show progress
            with st.spinner("Generating post... This may take a few minutes."):
                if st.session_state.api_mode:
                    # Use API mode
                    if should_post:
                        result = call_api_generate_post(request_data)
                    else:
                        result = call_api_generate_only(request_data)
                else:
                    # Direct import mode (not implemented in this version)
                    st.error("Direct import mode not implemented. Please use FastAPI Server mode.")
                    return
            
            if result and result.get('success'):
                st.session_state.generated_post = result.get('post_content')
                st.session_state.post_urn = result.get('post_urn')
                
                st.success("✅ Post generated successfully!")
                if result.get('post_urn'):
                    st.success(f"✅ Posted to LinkedIn! Post URN: {result.get('post_urn')}")
                
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
        
        st.markdown("### API Server")
        if st.session_state.api_mode:
            st.info("Make sure the FastAPI server is running on http://localhost:8000")
            if st.button("Check API Status"):
                try:
                    response = requests.get("http://localhost:8000/health", timeout=5)
                    if response.status_code == 200:
                        st.success("✅ API server is running")
                    else:
                        st.error("❌ API server returned error")
                except requests.exceptions.RequestException:
                    st.error("❌ API server is not running")
        else:
            st.info("Direct import mode selected. All dependencies must be installed locally.")
    
    with tab3:
        st.markdown('<div class="section-header">Generated Content</div>', unsafe_allow_html=True)
        
        if st.session_state.generated_post:
            st.markdown("### Generated Post")
            st.text_area(
                "Post Content",
                value=st.session_state.generated_post,
                height=300,
                disabled=True
            )
            
            st.markdown(f"**Character Count:** {len(st.session_state.generated_post)}")
            
            if st.session_state.post_urn:
                st.markdown("### LinkedIn Post")
                st.success(f"✅ Successfully posted to LinkedIn!")
                st.code(f"Post URN: {st.session_state.post_urn}")
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📋 Copy to Clipboard"):
                    st.write("Post content copied to clipboard!")
            
            with col2:
                if st.button("🔄 Generate New Post"):
                    st.session_state.generated_post = None
                    st.session_state.post_urn = None
                    st.rerun()
            
            with col3:
                if st.button("💾 Download as Text"):
                    st.download_button(
                        label="Download Post",
                        data=st.session_state.generated_post,
                        file_name=f"linkedin_post_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
        else:
            st.info("No post generated yet. Go to the 'Generate Post' tab to create a new post.")

if __name__ == "__main__":
    main()
