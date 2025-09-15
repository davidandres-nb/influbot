from __future__ import annotations
from typing import TypedDict, List, Literal, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
import os
import json
import re

from pydantic import BaseModel, Field
from dateutil import parser as dateparser

from langgraph.graph import StateGraph, END
from ddgs import DDGS # New import for web search

# ------------------------------
# Config
# ------------------------------
# Ensure environment variables are loaded
from dotenv import load_dotenv
load_dotenv()

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o")

# Verify OpenAI API key is available
if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("OPENAI_API_KEY environment variable is not set. Please check your .env file.")

# ------------------------------
# Minimal OpenAI client wrapper (supports new and legacy SDKs)
# ------------------------------
class _LLM:
    def __init__(self, model: str, temperature: float = 0.2):
        self.model = model
        self.temperature = temperature
        self._client = None
        
        # Try to use the new OpenAI API
        try:
            from openai import OpenAI
            self._client = OpenAI()
        except ImportError:
            # Fallback to legacy API if needed
            import openai
            self._client = openai

    def chat(self, prompt: str, as_json: bool = False) -> str:
        try:
            # Try new OpenAI API first
            kwargs: Dict[str, Any] = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.temperature,
            }
            if as_json:
                kwargs["response_format"] = {"type": "json_object"}
            
            resp = self._client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content or ""
        except Exception as e:
            # Fallback to legacy API if needed
            try:
                resp = self._client.ChatCompletion.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature,
                )
                return resp["choices"][0]["message"]["content"]
            except Exception:
                # If both fail, raise the original error
                raise RuntimeError(f"OpenAI API call failed: {str(e)}")

llm = _LLM(MODEL_NAME, temperature=0.2)

# ------------------------------
# State
# ------------------------------
class NewsItem(BaseModel):
    title: str
    url: str
    description: Optional[str] = None
    published_at: str
    source: Optional[str] = None

class GraphState(TypedDict):
    # inputs
    terms: List[str]
    topic: str
    audience_profile: str
    language: str
    register: str
    company_focus: Optional[Dict[str, str]]
    content_instructions: Optional[str]
    country: Optional[str]
    start_date: Optional[str]
    data_types: Optional[List[str]]
    source_language: Optional[str]
    enable_company_search: bool  # ADD THIS LINE
    max_fetch: int
    top_k: int
    output_kind: str                   # e.g., "linkedin_post", "article"
    output_format: Literal["text", "markdown", "html"]
    max_chars: int
    article_usage: Literal["direct_reference", "informational_synthesis", "examples"]
    include_links: bool
    links_in_char_limit: bool         # Whether source links count toward max_chars
    verbose: bool

    # internals
    now_utc: str
    articles: List[Dict[str, Any]]
    company_articles: Dict[str, List[Dict[str, Any]]]  # Articles about each company
    selected: List[Dict[str, Any]]
    used_sources: List[Dict[str, Any]]  # Sources actually used in the post
    post: str
    critique: Optional[str]
    iteration: int
    max_iterations: int

# ------------------------------
# Utilities
# ------------------------------
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")

def _log(state: GraphState, msg: str) -> None:
    if state.get("verbose"):
        ts = datetime.now().isoformat(timespec="seconds")
        print(f"[{ts}] {msg}")

def sanitize_plain(text: str) -> str:
    # Convert Markdown links to plain URLs and strip common markdown
    text = MD_LINK_RE.sub(r"\2", text)
    text = re.sub(r"[*_]{1,3}([^*_`]+)[*_]{1,3}", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text

def within_range(dt_iso: str, start_dt: datetime, end_dt: datetime) -> bool:
    try:
        dt = dateparser.parse(dt_iso)
    except Exception:
        return False
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=timezone.utc)
    return start_dt <= dt <= end_dt

def unique_by_url(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    deduped = []
    for it in items:
        u = it.get("url")
        if not u or u in seen:
            continue
        seen.add(u)
        deduped.append(it)
    return deduped

def truncate_under(text: str, max_chars: int) -> str:
    if max_chars <= 0:
        return text
    if len(text) <= max_chars:
        return text
    trimmed = text[: max_chars - 1]
    m = re.finditer(r"[\.!?]", trimmed)
    last_end = 0
    for match in m:
        last_end = match.end()
    if last_end > 0 and last_end > max_chars * 0.6:
        return trimmed[:last_end].strip()
    return trimmed.strip()

def extract_json(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        fragment = text[start : end + 1]
        try:
            return json.loads(fragment)
        except Exception:
            return {}
    return {}

def parse_start_date(start_date: Optional[str]) -> datetime:
    if start_date:
        try:
            dt = dateparser.parse(start_date)
            if dt and not dt.tzinfo:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            pass
    return datetime.now(timezone.utc) - timedelta(hours=24)

def normalise_types(types: Optional[List[str]]) -> List[str]:
    if not types:
        return ["news"]
    valid = {"news", "blog", "pr"}
    out = []
    for t in types:
        t = (t or "").strip().lower()
        if t == "blogs":
            t = "blog"
        if t in valid:
            out.append(t)
    return out or ["news"]

_LANG_MAP = {
    "english": "eng", "en": "eng", "en-gb": "eng", "en-us": "eng", "eng": "eng",
    "spanish": "spa", "es": "spa", "es-es": "spa", "spa": "spa",
    "french": "fra", "fr": "fra", "fra": "fra",
    "german": "deu", "de": "deu", "deu": "deu",
    "italian": "ita", "it": "ita", "ita": "ita",
    "portuguese": "por", "pt": "por", "por": "por",
    "dutch": "nld", "nl": "nld", "nld": "nld",
    "japanese": "jpn", "ja": "jpn", "jpn": "jpn",
    "chinese": "zho", "zh": "zho", "zho": "zho",
}

def map_language_to_er(language: Optional[str]) -> Optional[str]:
    if not language:
        return None
    key = language.strip().lower()
    return _LANG_MAP.get(key)

# ------------------------------
# Search providers
# ------------------------------
def search_articles(
    terms: List[str],
    *,
    country: Optional[str] = None,
    start_date: Optional[str] = None,
    data_types: Optional[List[str]] = None,
    max_results: int = 25,
    source_language: Optional[str] = None,  # Optional: filter by source language
) -> List[Dict[str, Any]]:
    """Searches for news articles using Event Registry API."""
    try:
        from eventregistry import EventRegistry, QueryArticlesIter, QueryItems
    except ImportError as e:
        raise RuntimeError("eventregistry is not installed. Run `pip install eventregistry`.") from e

    ER_API_KEY = (
        os.getenv("EVENTREGISTRY_API_KEY")
        or os.getenv("NEWSAPI_KEY")
        or os.getenv("NEWS_API_KEY")
    )
    if not ER_API_KEY:
        raise RuntimeError("EVENTREGISTRY_API_KEY (or NEWSAPI_KEY/NEWS_API_KEY) is not set.")

    terms = [t.strip() for t in (terms or []) if t and t.strip()]
    if not terms:
        return []

    er = EventRegistry(apiKey=ER_API_KEY)

    end_dt = datetime.now(timezone.utc)
    since_dt = parse_start_date(start_date)

    source_location_uri = None
    if country:
        try:
            source_location_uri = er.getLocationUri(country)
        except Exception:
            source_location_uri = None

    types = normalise_types(data_types)
    
    er_lang = None
    if source_language:
        er_lang = map_language_to_er(source_language)

    q = QueryArticlesIter(
        keywords=QueryItems.OR(terms),
        sourceLocationUri=source_location_uri,
        dataType=types,
        dateStart=since_dt.date(),
        lang=er_lang,
    )

    raw_items: List[Dict[str, Any]] = []
    max_items = min(max_results, 500)

    for art in q.execQuery(er, sortBy="relevance", maxItems=max_items):
        published_iso = art.get("dateTimePub") or art.get("dateTime")
        if not published_iso:
            continue
        item = {
            "title": art.get("title"),
            "url": art.get("url"),
            "description": (art.get("body") or "").strip()[:280] or None,
            "published_at": published_iso,
            "source": ((art.get("source") or {}).get("title")
                       or (art.get("source") or {}).get("uri")),
        }
        if not item["url"]:
            continue
        raw_items.append(item)

    items = [x for x in raw_items if within_range(x["published_at"], since_dt, end_dt)]
    items = unique_by_url(items)
    items.sort(key=lambda x: x["published_at"], reverse=True)
    return items[:max_results]

from typing import List, Dict, Any
from datetime import datetime, timezone
from urllib.parse import urlparse
from ddgs import DDGS
import time
import random

def search_companies_web(
    terms: List[str],
    max_results: int = 10,
    region: str = "wt-wt",               # global
    global_mix: bool = False,            # sample multiple regions for breadth
    retries: int = 2,                    # retry attempts per region/backend
    backends: List[str] = None,          # try several DDG backends for resilience
    verbose: bool = False,
) -> List[Dict[str, Any]]:
    """
    DuckDuckGo search for company info with safesearch OFF and robust fallbacks.
    Fixes: localisation, empty pages, and flakiness from a single backend.
    """
    if backends is None:
        backends = ["api", "html", "lite"]  # rotate if one is flaky

    query = " ".join(terms) if isinstance(terms, list) else str(terms)
    now_iso = datetime.now(timezone.utc).isoformat()

    # Regions to sample when global_mix is enabled
    mix_regions = ["wt-wt"] #, "us-en", "uk-en", "in-en", "de-de", "fr-fr", "es-es", "jp-ja", "br-pt"]
    regions = mix_regions if global_mix else [region]

    results: List[Dict[str, Any]] = []
    seen = set()

    def norm(u: str) -> str:
        p = urlparse(u)
        host = p.netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        path = p.path.rstrip("/")
        return f"{host}{path}"

    def fetch_block(ddgs: DDGS, reg: str, backend: str, want: int) -> List[Dict[str, Any]]:
        block = []
        # Over-fetch to allow for dedupe
        target = max(want * 3, 15)
        for r in ddgs.text(
            query,
            region=reg,
            safesearch="off",          # no filters as requested
            max_results=target,
            backend=backend,
        ):
            url = r.get("href")
            if not url:
                continue
            key = norm(url)
            if key in seen:
                continue
            seen.add(key)
            block.append({
                "title": r.get("title"),
                "url": url,
                "description": r.get("body"),
                "published_at": now_iso,
                "source": urlparse(url).netloc,
            })
            if len(block) >= target:
                break
        return block

    try:
        with DDGS() as ddgs:
            buckets = []
            for reg in regions:
                got_for_region = []
                for backend in backends:
                    # retry loop per backend
                    attempt = 0
                    while attempt <= retries and len(got_for_region) < max_results * 2:
                        try:
                            chunk = fetch_block(ddgs, reg, backend, want=max_results)
                            if verbose:
                                print(f"[ddg] region={reg} backend={backend} items={len(chunk)}")
                            if chunk:
                                got_for_region.extend(chunk)
                                break
                        except Exception as e:
                            if verbose:
                                print(f"[ddg] error region={reg} backend={backend}: {e}")
                        # backoff with jitter
                        sleep_s = (0.6 * (2 ** attempt)) + random.uniform(0, 0.3)
                        time.sleep(sleep_s)
                        attempt += 1
                # keep a per-region bucket
                buckets.append(got_for_region)

            # Round-robin merge for diversity
            i = 0
            while len(results) < max_results and any(buckets):
                advanced = False
                for b in buckets:
                    if i < len(b):
                        results.append(b[i])
                        advanced = True
                        if len(results) >= max_results:
                            break
                if not advanced:
                    break
                i += 1

    except Exception as e:
        if verbose:
            print(f"[ddg] fatal error: {e}")

    # Final trim
    return results[:max_results]


# ------------------------------
# Nodes
# ------------------------------
class RankAndScoreSchema(BaseModel):
    top_indices: List[int]
    per_item: List[Dict[str, Any]]

def node_search_companies(state: GraphState) -> Dict[str, Any]:
    """Search for information about specified companies using a general web search to verify and enrich content."""
    company_focus = state.get("company_focus", {})
    enable_company_search = state.get("enable_company_search", True)  # Default to True for backward compatibility
    
    if not company_focus:
        _log(state, "No companies to search for, skipping company search.")
        return {"company_articles": {}}
    
    # Check if company search is disabled
    if not enable_company_search:
        _log(state, "Company search disabled - using provided descriptions only.")
        return {"company_articles": {}}
    
    # Rest of the function remains the same...
    topic = state.get("topic", "")
    terms = state.get("terms", [])
    
    _log(state, f"Step 1b/6: Verifying companies via web search ({len(company_focus)} companies)...")
    _log(state, f"  Topic context: {topic}")
    
    company_articles = {}
    for company_name, description in company_focus.items():
        _log(state, f"  Searching for: {company_name}")
        
        # Create a focused query that strongly links the company to the topic
        # The query structure ensures we find company information relevant to the topic
        company_query_parts = []
        
        # 1. Always include the company name
        company_query_parts.append(company_name)
        
        # 2. Add the main topic to ensure relevance
        if topic:
            # Create a query that links company and topic
            # This ensures we find articles about the company in the context of the topic
            company_query_parts.append(topic)
        
        # 3. Add key terms from the search (but limit to most relevant)
        # Filter out generic terms and focus on topic-specific ones
        relevant_terms = []
        for term in terms[:3]:  # Take up to 3 most relevant terms
            # Skip the company name if it's already in the terms
            if term.lower() != company_name.lower():
                relevant_terms.append(term)
        
        if relevant_terms:
            company_query_parts.extend(relevant_terms[:2])  # Add max 2 additional terms
        
        # 4. If there's a specific aspect in the description that relates to the topic, include it
        # Extract key phrases from description that might relate to the topic
        if description and topic:
            # Look for topic-related keywords in the description
            topic_words = topic.lower().split()
            description_words = description.lower().split()
            
            # Find overlapping concepts
            relevant_description_parts = []
            for word in topic_words:
                if word in description_words and len(word) > 3:  # Skip short words
                    # Find the phrase around this word in the description
                    idx = description_words.index(word)
                    start = max(0, idx - 1)
                    end = min(len(description_words), idx + 2)
                    phrase = " ".join(description.split()[start:end])
                    if phrase not in relevant_description_parts:
                        relevant_description_parts.append(phrase)
            
            # Add the most relevant phrase from description if found
            if relevant_description_parts:
                company_query_parts.append(relevant_description_parts[0])
        
        # Build the final search query
        # Structure: "CompanyName topic relevant_terms"
        search_query = " ".join(company_query_parts)
        
        # Ensure the query isn't too long (search engines have limits)
        if len(search_query) > 100:
            # Prioritize: company name + topic + 1 key term
            search_query = f"{company_name} {topic}"
            if relevant_terms:
                search_query += f" {relevant_terms[0]}"
        
        _log(state, f"    Query: {search_query}")
        
        try:
            # Use web search with the topic-linked query
            articles = search_companies_web(
                [search_query],  # Pass as single query string in list
                max_results=5,
            )
            
            # Post-filter results to ensure relevance
            # Keep only results that seem relevant to both company and topic
            filtered_articles = []
            for article in articles:
                title = (article.get("title") or "").lower()
                description = (article.get("description") or "").lower()
                combined_text = f"{title} {description}"
                
                # Check if the article mentions the company
                company_mentioned = company_name.lower() in combined_text
                
                # Check if the article is related to the topic
                topic_related = False
                if topic:
                    topic_keywords = topic.lower().split()
                    topic_related = any(keyword in combined_text for keyword in topic_keywords if len(keyword) > 3)
                
                # Include article if it mentions the company and is topic-related
                # OR if it strongly mentions the company (even without explicit topic mention)
                if company_mentioned and (topic_related or combined_text.count(company_name.lower()) >= 2):
                    filtered_articles.append(article)
                    _log(state, f"      ✓ Relevant: {article.get('title', '')[:60]}...")
                elif company_mentioned:
                    # Still include if company is mentioned but mark as potentially less relevant
                    article["relevance_score"] = "medium"
                    filtered_articles.append(article)
                    _log(state, f"      ~ Partial: {article.get('title', '')[:60]}...")
            
            company_articles[company_name] = filtered_articles
            _log(state, f"    Found {len(filtered_articles)} relevant results for {company_name}")
            
        except Exception as e:
            _log(state, f"    Error searching for {company_name}: {str(e)}")
            company_articles[company_name] = []
    
    return {"company_articles": company_articles}

def node_search(state: GraphState) -> Dict[str, Any]:
    _log(state, "Step 1a/6: Searching news articles...")
    articles = search_articles(
        state["terms"],
        country=state.get("country"),
        start_date=state.get("start_date"),
        data_types=state.get("data_types"),
        max_results=int(state.get("max_fetch", 30)),
        source_language=state.get("source_language"),
    )
    _log(state, f"Found {len(articles)} articles after filters.")
    return {"articles": articles, "now_utc": datetime.now(timezone.utc).isoformat()}

def node_rank(state: GraphState) -> Dict[str, Any]:
    _log(state, "Step 2/6: Scoring and selecting top items...")
    articles = state["articles"]
    if not articles:
        raise RuntimeError("No articles found for the given filters.")

    audience = state.get("audience_profile", "general readers")
    topic = state.get("topic", "")
    company_focus = state.get("company_focus", {})
    company_articles = state.get("company_articles", {})
    top_k = int(state.get("top_k", 3))

    # Combine main articles with company articles for context
    all_articles = articles.copy()
    company_article_ids = set()
    
    if company_articles:
        for company_name, comp_arts in company_articles.items():
            for art in comp_arts[:2]:
                if art.get("url") and art["url"] not in [a.get("url") for a in all_articles]:
                    art["company_related"] = company_name
                    all_articles.append(art)
                    company_article_ids.add(art.get("url"))

    bullet = []
    for i, a in enumerate(all_articles):
        company_tag = f" [Related to {a.get('company_related')}]" if a.get('company_related') else ""
        bullet.append(
            f"[{i}] Title: {a.get('title')}{company_tag}\n"
            f"Source: {a.get('source')}\n"
            f"Published: {a.get('published_at')}\n"
            f"URL: {a.get('url')}\n"
            f"Summary: {a.get('description', 'N/A')}"
        )

    company_criteria = ""
    if company_focus:
        company_names = ", ".join(company_focus.keys())
        company_criteria = f"""6. Company relevance: Prioritize articles mentioning or relevant to {company_names}
7. Verification value: Articles that help verify company claims or provide current company information"""

    prompt = f"""Score and rank these articles for relevance and quality.

EVALUATION CRITERIA:
1. Term relevance: How well does it match the search terms?
2. Topic alignment: How relevant is it to the main topic?
3. Freshness & novelty: Prefer recent, unique angles
4. Source quality: Prioritize reputable sources
5. Information value: Practical, actionable insights
{company_criteria}

Consider the content complexity appropriate for: {audience}

Search terms: {', '.join(state['terms'])}
Main topic: {topic}
Number to select: {top_k}

Note: Articles marked with [Related to CompanyName] are from web searches to verify those companies.

ARTICLES:
{chr(10).join(bullet)}

Return JSON with:
- top_indices: list of {top_k} article indices (most relevant first)
- per_item: list with index, rationale for each selected item"""

    raw = llm.chat(prompt, as_json=True)
    data = extract_json(raw)

    idxs = data.get("top_indices") if isinstance(data.get("top_indices"), list) else []
    idxs = [int(i) for i in idxs if isinstance(i, int) or (isinstance(i, str) and str(i).isdigit())]
    idxs = [i for i in idxs if 0 <= i < len(all_articles)]

    if len(idxs) < top_k:
        pad = [i for i in range(len(all_articles)) if i not in idxs][: top_k - len(idxs)]
        idxs = idxs + pad
    else:
        idxs = idxs[:top_k]

    selected = [all_articles[i] for i in idxs]
    _log(state, "Selected: " + " | ".join([s.get("title", "")[:60] for s in selected]))
    return {"selected": selected}

def build_fact_sheet(selected: List[Dict[str, Any]]) -> str:
    rows = []
    for a in selected:
        rows.append(
            f"Title: {a.get('title')}\n"
            f"URL: {a.get('url')}\n"
            f"Source: {a.get('source')}\n"
            f"Published: {a.get('published_at')}\n"
            f"Content: {a.get('description', 'No description available')}\n"
        )
    return "\n".join(rows)

def render_output(body: str, used_sources: List[Dict[str, Any]], fmt: str, max_chars: int, 
                  include_sources: bool = True, links_in_char_limit: bool = True) -> str:
    urls = [a.get("url") for a in used_sources if a.get("url")]
    
    if fmt == "text":
        body = sanitize_plain(body)
        for u in urls:
            body = body.replace(u, "")
        
        if include_sources and urls:
            sources_section = "\n\nSources:\n" + "\n".join(urls)
            if links_in_char_limit:
                available_for_body = max_chars - len(sources_section)
                if len(body) > available_for_body:
                    body = truncate_under(body, available_for_body)
                return body + sources_section
            else:
                body = truncate_under(body, max_chars)
                return body + sources_section
        return truncate_under(body, max_chars)

    if fmt == "markdown":
        if include_sources and urls:
            sources_section = "\n\n**Sources:**\n" + "\n".join(f"- {u}" for u in urls)
            if links_in_char_limit:
                available_for_body = max_chars - len(sources_section)
                if len(body) > available_for_body:
                    body = truncate_under(body, available_for_body)
                return body.rstrip() + sources_section
            else:
                body = truncate_under(body, max_chars)
                return body.rstrip() + sources_section
        return truncate_under(body, max_chars)

    if fmt == "html":
        parts = [p.strip() for p in re.split(r"\n\n+", body.strip()) if p.strip()]
        html = "".join(f"<p>{p.replace(chr(10), '<br/>')}</p>" for p in parts)
        if include_sources and urls:
            items = "".join(f'<li><a href="{u}">{u}</a></li>' for u in urls)
            sources_section = f"<h3>Sources</h3><ul>{items}</ul>"
            if links_in_char_limit:
                available_for_body = max_chars - len(sources_section)
                if len(html) > available_for_body:
                    html = truncate_under(html, available_for_body)
                return html + sources_section
            else:
                html = truncate_under(html, max_chars)
                return html + sources_section
        return truncate_under(html, max_chars)

    return truncate_under(body.strip(), max_chars)

def node_draft(state: GraphState) -> Dict[str, Any]:
    _log(state, "Step 3/6: Drafting output...")
    selected = state["selected"]
    facts = build_fact_sheet(selected)
    audience = state.get("audience_profile", "general readers")
    topic = state.get("topic", "")
    language = state.get("language", "English (UK)")
    register = state.get("register", "professional")
    company_focus = state.get("company_focus", {})
    company_articles = state.get("company_articles", {})
    content_instructions = state.get("content_instructions", "")
    output_kind = state.get("output_kind", "linkedin_post")
    output_format = state.get("output_format", "text")
    max_chars = int(state.get("max_chars", 1900))
    article_usage = state.get("article_usage", "informational_synthesis")
    include_links = bool(state.get("include_links", True))
    links_in_char_limit = bool(state.get("links_in_char_limit", True))

    if article_usage == "direct_reference":
        usage_instruction = "Explicitly cite sources by name (e.g., 'According to TechCrunch...', 'Reuters reports...')."
    elif article_usage == "examples":
        usage_instruction = "Use articles as illustrative examples and case studies to support broader insights."
    else:  # informational_synthesis
        usage_instruction = "Synthesize information across sources into a cohesive narrative without naming specific outlets."

    format_constraints = {
        "text": "Plain text only. No markdown, no formatting symbols, no URLs in body.",
        "markdown": "Use markdown formatting sparingly. Bold for emphasis, lists where appropriate.",
        "html": "Simple HTML with <p>, <ul>, <li> tags only. No inline styles."
    }

    complexity_guide = f"Write at a complexity level suitable for {audience}. Adjust technical depth and vocabulary accordingly."

    custom_instructions = ""
    if content_instructions:
        custom_instructions = f"""
SPECIFIC CONTENT INSTRUCTIONS:
{content_instructions}
"""

    company_instruction = ""
    if company_focus:
        enable_company_search = state.get("enable_company_search", True)
        company_entries = []
        for company, description in company_focus.items():
            comp_arts = company_articles.get(company, [])
            
            if enable_company_search:
                verification_note = f" [VERIFIED - Web results available]" if comp_arts else " [Use provided description only]"
            else:
                verification_note = " [Using provided description]"
            
            company_entries.append(f"- {company}: {description}{verification_note}")
        
        company_instruction = f"""
MANDATORY COMPANY INTEGRATION:
You MUST incorporate and highlight these companies in the content:
{chr(10).join(company_entries)}

Requirements:
- Naturally weave these companies into the narrative
- Use the provided descriptions {"and any verified information from articles" if enable_company_search else ""}
- Connect their relevance to the topic and source material
- Position them as key players or solutions in the discussion
- Ensure each company is meaningfully mentioned at least once
{"- Articles marked [Related to CompanyName] contain verified current information about those companies" if enable_company_search else ""}
"""

    char_limit_note = f"Maximum {max_chars} characters for the body text"
    if include_links and links_in_char_limit:
        char_limit_note += " (source links will be included in this limit)"
    elif include_links:
        char_limit_note += " (source links will be added separately, not counting toward this limit)"

    indexed_facts = []
    for i, a in enumerate(selected):
        company_tag = f" [Related to {a.get('company_related')}]" if a.get('company_related') else ""
        indexed_facts.append(
            f"[Article {i+1}]{company_tag}\n"
            f"Title: {a.get('title')}\n"
            f"URL: {a.get('url')}\n"
            f"Source: {a.get('source')}\n"
            f"Published: {a.get('published_at')}\n"
            f"Content: {a.get('description', 'No description available')}\n"
        )

    prompt = f"""Create a {output_kind.replace('_', ' ')} based on the provided articles.

IMPORTANT: You have {len(selected)} articles available, but only use those most relevant to the topic and narrative.
List the article numbers you actually used at the end in this format: "USED_SOURCES: [1, 3, 5]"

CONTENT REQUIREMENTS:
- {char_limit_note}
- Language: {language} (translate/adapt content from sources as needed)
- Tone: {register}
- {complexity_guide}
- Focus on topic: {topic}
{custom_instructions}
{company_instruction}

SOURCE USAGE:
{usage_instruction}
Note: Not all provided articles need to be used - select only the most relevant ones.
Articles marked [Related to CompanyName] provide verified information about those companies.

FORMAT ({output_format}):
{format_constraints[output_format]}
{'Note: Source links will be automatically appended at the end.' if include_links else 'Do not include any source links.'}

STRUCTURE:
1. Compelling opening that establishes relevance
2. Key insights and developments from the most relevant sources
3. Analysis of implications and trends (integrate company mentions here if applicable)
4. Actionable takeaway or forward-looking conclusion

AVAILABLE ARTICLES:
{chr(10).join(indexed_facts)}

Write the content directly, then add "USED_SOURCES: [list of article numbers]" at the very end."""

    response = llm.chat(prompt).strip()
    
    used_indices = []
    if "USED_SOURCES:" in response:
        parts = response.split("USED_SOURCES:")
        body = parts[0].strip()
        try:
            sources_str = parts[1].strip()
            import re
            numbers = re.findall(r'\d+', sources_str)
            used_indices = [int(n) - 1 for n in numbers if 0 <= int(n) - 1 < len(selected)]
        except:
            used_indices = list(range(len(selected)))
    else:
        body = response
        used_indices = list(range(len(selected)))
    
    used_sources = [selected[i] for i in used_indices] if used_indices else selected
    
    formatted = render_output(body, used_sources, output_format, max_chars, 
                            include_sources=include_links, links_in_char_limit=links_in_char_limit)
    
    _log(state, f"Draft length: {len(formatted)} chars (limit {max_chars}). Used {len(used_sources)}/{len(selected)} sources.")
    
    return {
        "post": formatted, 
        "used_sources": used_sources,
        "iteration": state.get("iteration", 0)
    }

class VerificationSchema(BaseModel):
    verdict: Literal["approve", "revise"]
    critique: Optional[str] = None

def node_verify(state: GraphState) -> Dict[str, Any]:
    _log(state, "Step 4/6: Verifying accuracy and quality...")
    used_sources = state.get("used_sources", state["selected"])
    post = state["post"]
    facts = build_fact_sheet(used_sources)
    topic = state.get("topic", "")
    language = state.get("language", "English (UK)")
    register = state.get("register", "professional")
    company_focus = state.get("company_focus", {})
    company_articles = state.get("company_articles", {})
    content_instructions = state.get("content_instructions", "")
    output_format = state.get("output_format", "text")
    max_chars = int(state.get("max_chars", 1900))
    article_usage = state.get("article_usage", "informational_synthesis")
    include_links = bool(state.get("include_links", True))
    links_in_char_limit = bool(state.get("links_in_char_limit", True))

    company_check = ""
    company_verification = ""
    if company_focus:
        company_list = list(company_focus.keys())
        company_check = f"""10. Company integration: ALL of these companies MUST be mentioned:
   {', '.join(company_list)}
   - Each company must be mentioned at least once
   - Companies must be integrated naturally with context"""
        
        verification_items = []
        for company in company_list:
            comp_arts = company_articles.get(company, [])
            if comp_arts:
                verification_items.append(f"- {company}: Found {len(comp_arts)} web results - verify accuracy")
            else:
                verification_items.append(f"- {company}: No web results found - use provided description only")
        
        if verification_items:
            company_verification = f"""
COMPANY VERIFICATION INFO:
{chr(10).join(verification_items)}
"""

    custom_check = ""
    if content_instructions:
        custom_check = f"""11. Custom instructions compliance: Content follows these specific instructions:
   {content_instructions[:200]}..."""

    length_note = f"{max_chars} characters"
    if not links_in_char_limit and include_links:
        length_note += " (excluding source links)"

    prompt = f"""Review this content for accuracy and quality.
{company_verification}
VERIFICATION CHECKLIST:
1. Factual accuracy: All claims traceable to source material
2. No speculation or unsupported statements  
3. Language matches requirement: {language}
4. Tone matches requirement: {register}
5. Topic focus maintained: {topic}
6. Length within limit: {length_note}
7. Format compliance: {output_format}
8. Source usage follows {article_usage} approach
9. {'Links section present at end' if include_links else 'No links included'}
{company_check}
{custom_check}

CONTENT TO VERIFY:
{post}

SOURCE MATERIAL (only used sources):
{facts}

Return JSON with:
- verdict: "approve" or "revise"
- critique: specific improvements needed (if revising)"""

    raw = llm.chat(prompt, as_json=True)
    data = extract_json(raw)
    verdict = str(data.get("verdict", "")).strip().lower()
    critique = data.get("critique") if isinstance(data.get("critique"), str) else None
    
    _log(state, f"Verification: {verdict}{' - ' + critique if critique else ''}")
    
    if verdict == "approve":
        return {"critique": None}
    return {"critique": critique or "Content needs revision for accuracy and compliance."}

def node_revise(state: GraphState) -> Dict[str, Any]:
    iteration = state.get("iteration", 0)
    _log(state, f"Step 5-6/6: Revising based on feedback (iteration {iteration + 1})...")
    post = state["post"]
    critique = state.get("critique", "")
    used_sources = state.get("used_sources", state["selected"])
    selected = state["selected"]
    facts = build_fact_sheet(used_sources)
    topic = state.get("topic", "")
    language = state.get("language", "English (UK)")
    register = state.get("register", "professional")
    company_focus = state.get("company_focus", {})
    company_articles = state.get("company_articles", {})
    content_instructions = state.get("content_instructions", "")
    output_format = state.get("output_format", "text")
    max_chars = int(state.get("max_chars", 1900))
    article_usage = state.get("article_usage", "informational_synthesis")
    include_links = bool(state.get("include_links", True))
    links_in_char_limit = bool(state.get("links_in_char_limit", True))

    company_instruction = ""
    if company_focus:
        company_entries = []
        for company, description in company_focus.items():
            comp_arts = company_articles.get(company, [])
            verification_note = " [VERIFIED]" if comp_arts else " [UNVERIFIED - use description]"
            company_entries.append(f"  - {company}: {description}{verification_note}")
        company_instruction = f"""- MANDATORY: Include ALL these companies with their context:
{chr(10).join(company_entries)}"""

    custom_instruction = ""
    if content_instructions:
        custom_instruction = f"- IMPORTANT: Follow these specific instructions: {content_instructions}"

    char_limit_note = f"{max_chars} characters for body text"
    if include_links and links_in_char_limit:
        char_limit_note += " (including source links)"
    elif include_links:
        char_limit_note += " (excluding source links)"

    indexed_facts = []
    for i, a in enumerate(selected):
        company_tag = f" [Related to {a.get('company_related')}]" if a.get('company_related') else ""
        indexed_facts.append(
            f"[Article {i+1}]{company_tag}\n"
            f"Title: {a.get('title')}\n"
            f"Content: {a.get('description', 'No description available')}\n"
        )

    prompt = f"""Revise this content to address the identified issues.

ISSUES TO FIX:
{critique}

CURRENT CONTENT:
{post}

REQUIREMENTS:
- Stay within {char_limit_note}
- Language: {language}, Tone: {register}
- Topic focus: {topic}
- Format: {output_format}
- Source usage: {article_usage}
- {'Include links section at end' if include_links else 'No links'}
{company_instruction}
{custom_instruction}

You may use different sources if needed. Available articles:
{chr(10).join(indexed_facts)}

Provide the revised content directly, then add "USED_SOURCES: [list of article numbers]" at the end."""

    response = llm.chat(prompt).strip()
    
    used_indices = []
    if "USED_SOURCES:" in response:
        parts = response.split("USED_SOURCES:")
        improved = parts[0].strip()
        try:
            sources_str = parts[1].strip()
            import re
            numbers = re.findall(r'\d+', sources_str)
            used_indices = [int(n) - 1 for n in numbers if 0 <= int(n) - 1 < len(selected)]
        except:
            used_indices = [selected.index(s) for s in used_sources if s in selected]
    else:
        improved = response
        used_indices = [selected.index(s) for s in used_sources if s in selected]
    
    new_used_sources = [selected[i] for i in used_indices] if used_indices else used_sources
    
    formatted = render_output(improved, new_used_sources, output_format, max_chars,
                            include_sources=include_links, links_in_char_limit=links_in_char_limit)
    
    _log(state, f"Revised length: {len(formatted)} chars (limit {max_chars}). Used {len(new_used_sources)} sources.")
    
    return {
        "post": formatted,
        "used_sources": new_used_sources,
        "iteration": iteration + 1
    }

def should_continue(state: GraphState) -> Literal["revise", "finish"]:
    iters = int(state.get("iteration", 0))
    if state.get("critique") and iters < int(state.get("max_iterations", 2)):
        return "revise"
    if state.get("critique"):
        _log(state, f"Max iterations reached ({state.get('max_iterations', 2)}) - finishing with current version")
    else:
        _log(state, "Content approved - workflow complete!")
    return "finish"

# ------------------------------
# Build graph
# ------------------------------
def build_graph() -> "CompiledGraph":
    g = StateGraph(GraphState)
    g.add_node("search", node_search)
    g.add_node("search_companies", node_search_companies)
    g.add_node("rank", node_rank)
    g.add_node("draft", node_draft)
    g.add_node("verify", node_verify)
    g.add_node("revise", node_revise)

    g.set_entry_point("search")
    g.add_edge("search", "search_companies")
    g.add_edge("search_companies", "rank")
    g.add_edge("rank", "draft")
    g.add_edge("draft", "verify")

    g.add_conditional_edges("verify", should_continue, {"revise": "revise", "finish": END})
    g.add_edge("revise", "verify")

    return g.compile()

# ------------------------------
# Public runner
# ------------------------------
def run_workflow(
    terms: List[str],
    topic: str,
    audience_profile: str,
    *,
    language: str = "English (UK)",
    register: str = "professional",
    company_focus: Optional[Dict[str, str]] = None,
    content_instructions: Optional[str] = None,
    enable_company_search: bool = True,  # ADD THIS PARAMETER
    country: Optional[str] = None,
    start_date: Optional[str] = None,
    data_types: Optional[List[str]] = None,
    source_language: Optional[str] = None,
    max_fetch: int = 30,
    top_k: int = 3,
    output_kind: str = "linkedin_post",
    output_format: Literal["text", "markdown", "html"] = "text",
    max_chars: int = 1900,
    article_usage: Literal["direct_reference", "informational_synthesis", "examples"] = "informational_synthesis",
    include_links: bool = True,
    links_in_char_limit: bool = True,
    max_iterations: int = 2,
    verbose: bool = True,
) -> str:
    """
    Generate content from news articles.
    
    Args:
        terms: Search keywords
        topic: Main topic to focus on
        audience_profile: Target audience (for tone/complexity calibration)
        language: Output language for generated content
        register: Writing style (formal/informal/technical)
        company_focus: Dict of companies to promote with descriptions
                      e.g., {'CompanyA': 'Leading AI provider...', 'CompanyB': 'Innovative startup...'}
        content_instructions: Custom instructions for content creation
        enable_company_search: Whether to search for company information online (True) or use descriptions only (False)
        # ... rest of the docstring
    """
    graph = build_graph()

    initial: GraphState = {
        "terms": terms,
        "topic": topic,
        "audience_profile": audience_profile,
        "language": language,
        "register": register,
        "company_focus": company_focus or {},
        "content_instructions": content_instructions or "",
        "enable_company_search": bool(enable_company_search),  # ADD THIS LINE
        "country": country,
        "start_date": start_date,
        "data_types": data_types,
        "source_language": source_language,
        "max_fetch": int(max_fetch),
        "top_k": int(top_k),
        "output_kind": output_kind,
        "output_format": output_format,
        "max_chars": int(max_chars),
        "article_usage": article_usage,
        "include_links": bool(include_links),
        "links_in_char_limit": bool(links_in_char_limit),
        "verbose": bool(verbose),
        "now_utc": datetime.now(timezone.utc).isoformat(),
        "articles": [],
        "company_articles": {},
        "selected": [],
        "used_sources": [],
        "post": "",
        "critique": None,
        "iteration": 0,
        "max_iterations": int(max_iterations),
    }
    final_state = graph.invoke(initial)
    post = final_state.get("post", "").strip()
    return post

# --------------------------------------------------------------------------------
# NOTE: To run this code, you need to update your dependencies.
#
# Dependencies:
# pip install langgraph pydantic requests python-dateutil openai eventregistry ddgs
# --------------------------------------------------------------------------------

# Example usage:
# post = run_workflow(
#     terms=["AI casinos", "AI sports betting", "AI poker", "AI bingo", "AI live casino"],
#     topic="AI Revolution in iGaming",
#     audience_profile="iGaming professionals",
#     language="English (UK)",
#     register="professional",
    
#     # Companies to verify via web search
#     company_focus={
#         "Netbet": "NetBet is a regulated online gambling and betting company offering sports betting, casino, live dealer, poker and more across multiple markets. Founded in the early 2000s, it operates under licences in several European jurisdictions and is known for football sponsorships and a focus on security and fair play."
#     },
    
#     content_instructions="""Include a call-to-action to embrace AI in iGaming. 
#     Start with a thought-provoking question. 
#     End with a vision of the future. 
#     Do NOT say or mention that companies are not mentioned in sources.
#     Add emojis for a more engaging, yet professional, post.""",
    
#     country=None,
#     start_date="2025-08-01",
#     data_types=["news", "blog"],
#     source_language=None,
#     max_fetch=30,
#     top_k=5,
#     output_kind="linkedin_post",
#     output_format="text",
#     max_chars=1100,
#     article_usage="informational_synthesis",
#     include_links=True,
#     links_in_char_limit=False,
#     verbose=True,
#     enable_company_search=True
# )