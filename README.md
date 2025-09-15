# LinkedIn Post Generator

A comprehensive tool that generates LinkedIn posts using AI and optionally posts them to LinkedIn. Available as both a web interface (Streamlit) and API.

## Features

- **🌐 Web Interface**: Easy-to-use Streamlit app for generating and posting LinkedIn content
- **🤖 AI-Powered Post Generation**: Uses OpenAI to generate engaging LinkedIn posts based on search terms and topics
- **📰 News Research**: Automatically researches recent news and articles related to your topic
- **🔗 LinkedIn Integration**: Generate posts without posting them, or generate and post directly to LinkedIn
- **🎨 AI Image Generation**: Optional AI-generated images to accompany your posts
- **⚙️ Flexible Content Control**: Customize audience profile, language, tone, and content instructions
- **🏢 Company Integration**: Include company information and focus in your posts
- **🔧 Advanced Settings**: Fine-tune search parameters, article selection, and content generation

## Quick Start

### Option 1: Simple Web Interface (Recommended)

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Configuration**:
   - Copy `env.example` to `.env`
   - Fill in your API keys (see Environment Variables section below)

3. **Start the application**:
   ```bash
   python run_simple.py
   ```
   
   Or on Windows:
   ```cmd
   start_simple.bat
   ```

4. **Open your browser**: http://localhost:8501

### Option 2: API + Web Interface

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Configuration**:
   - Copy `env.example` to `.env`
   - Fill in your API keys

3. **Start the application**:
   ```bash
   python run_streamlit.py
   ```
   
   Or on Windows:
   ```cmd
   start_app.bat
   ```

4. **Open your browser**:
   - Streamlit App: http://localhost:8501
   - API Server: http://localhost:8000

### Option 3: API Only

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Configuration**:
   - Copy `env.example` to `.env`
   - Fill in your API keys

3. **Run the API server**:
   ```bash
   cd app
   python main.py
   ```

   Or using uvicorn directly:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Environment Variables

Create a `.env` file with the following variables:

```env
# Required for AI content generation
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o

# Required for news article search (choose one)
EVENTREGISTRY_API_KEY=your_eventregistry_api_key_here
# OR
NEWSAPI_KEY=your_newsapi_key_here

# Required for LinkedIn posting (optional)
LINKEDIN_ACCESS_TOKEN=your_linkedin_access_token_here
LINKEDIN_AUTHOR_URN=urn:li:person:your_linkedin_id_here
```

### Getting API Keys

- **OpenAI**: Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)
- **EventRegistry**: Sign up at [EventRegistry](https://eventregistry.org/) for news search
- **NewsAPI**: Alternative news source at [NewsAPI](https://newsapi.org/)
- **LinkedIn**: Create an app at [LinkedIn Developers](https://developer.linkedin.com/) and get your access token

## Web Interface Usage

### Simple Mode (Recommended)

The simplified Streamlit app (`streamlit_simple.py`) provides a clean, direct interface that imports Python modules without requiring a FastAPI server:

**Key Features:**
- ✅ **No FastAPI dependency** - Direct Python imports
- ✅ **Faster startup** - No server management needed
- ✅ **Simpler deployment** - Single Streamlit process
- ✅ **Same functionality** - All features available
- ✅ **Better UX** - Cleaner, more responsive interface

**Usage:**
```bash
python run_simple.py
# or on Windows: start_simple.bat
```

### Full Mode (API + Web Interface)

The full Streamlit app (`streamlit_app.py`) provides the same interface but uses the FastAPI server for processing:

### Main Features

1. **📝 Generate Post Tab**:
   - Enter your topic and search terms
   - Select target audience and writing style
   - Configure content settings (character limit, article usage, etc.)
   - Add company focus and custom instructions
   - Choose whether to post to LinkedIn and generate AI images

2. **🔧 Settings Tab**:
   - Check environment variable status
   - Verify API server connectivity
   - View configuration details

3. **📊 Results Tab**:
   - View generated post content
   - See LinkedIn posting status
   - Copy content or download as text file
   - Generate new posts

### Advanced Settings

The web interface includes collapsible advanced settings for:
- **Search Parameters**: Country filter, date range, content types
- **Article Selection**: Number of articles to fetch and use
- **Company Focus**: Add multiple companies with descriptions
- **Custom Instructions**: Specific content generation guidelines

### LinkedIn Integration

- **Automatic Posting**: Generate and post directly to LinkedIn
- **Image Support**: Upload images or generate AI images
- **Visibility Control**: Choose between public and connections-only posts
- **Real-time Status**: See posting status and get post URNs

## API Endpoints

### 1. Generate and Optionally Post (`POST /generate-post`)

This endpoint generates a LinkedIn post and optionally posts it to LinkedIn.

**Request Body**:
```json
{
  "terms": ["AI", "machine learning", "automation"],
  "topic": "The Future of AI in Business",
  "audience_profile": "business professionals",
  "language": "English",
  "register": "professional",
  "should_post": false,
  "linkedin_token": "your_token_here",
  "author_urn": "urn:li:person:your_id_here"
}
```

**Response**:
```json
{
  "success": true,
  "post_content": "Generated LinkedIn post content...",
  "post_urn": "urn:li:share:123456789",
  "message": "Post generated and posted to LinkedIn successfully"
}
```

### 2. Generate Only (`POST /generate-only`)

This endpoint generates a LinkedIn post without posting it to LinkedIn.

**Request Body**: Same as above, but `should_post` is automatically set to `false`.

### 3. Health Check (`GET /health`)

Returns the API health status.

## Key Parameters

### Content Generation
- `terms`: List of search keywords for content research
- `topic`: Main topic to focus on
- `audience_profile`: Target audience (affects tone and complexity)
- `language`: Output language
- `register`: Writing style (formal/informal/technical)
- `max_chars`: Maximum character limit for the post
- `content_instructions`: Custom instructions for content creation

### LinkedIn Posting (when `should_post: true`)
- `linkedin_token`: Your LinkedIn API access token
- `author_urn`: Your LinkedIn profile URN
- `image_paths`: Optional list of image file paths
- `alt_texts`: Optional alt text for images
- `visibility`: Post visibility ("PUBLIC" or "CONNECTIONS")

## Example Usage

### Generate a post without posting:
```bash
curl -X POST "http://localhost:8000/generate-only" \
  -H "Content-Type: application/json" \
  -d '{
    "terms": ["AI", "automation", "productivity"],
    "topic": "AI Tools for Business Productivity",
    "audience_profile": "business owners",
    "max_chars": 1000
  }'
```

### Generate and post to LinkedIn:
```bash
curl -X POST "http://localhost:8000/generate-post" \
  -H "Content-Type: application/json" \
  -d '{
    "terms": ["AI", "automation", "productivity"],
    "topic": "AI Tools for Business Productivity",
    "audience_profile": "business owners",
    "max_chars": 1000,
    "should_post": true,
    "linkedin_token": "your_token_here",
    "author_urn": "urn:li:person:your_id_here"
  }'
```

## LinkedIn API Setup

To post to LinkedIn, you'll need:

1. **LinkedIn Developer Account**: Create an app at [LinkedIn Developers](https://developer.linkedin.com/)
2. **Access Token**: Generate a token with `w_member_social` scope
3. **Author URN**: Your LinkedIn profile URN (found in your profile URL or via API)

## Notes

- The API uses the existing `post_generator.py` and `linkedin_post.py` modules
- Posts are generated using AI based on recent news and web content
- Image posting is supported but optional
- All generated content respects LinkedIn's character limits and guidelines

## Error Handling

The API provides detailed error messages for:
- Missing required LinkedIn credentials when posting
- Content generation failures
- LinkedIn API posting errors
- Invalid request parameters
