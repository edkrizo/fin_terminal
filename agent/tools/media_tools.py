import urllib.request
import urllib.parse
import re
import json
import logging

logger = logging.getLogger(__name__)

def get_youtube_videos(query: str) -> str:
    """Use this tool to find relevant YouTube video IDs for the dashboard media player."""
    try:
        # 🚀 THE FIX: Remove 'bloomberg cnbc' hardcoding!
        # Let the Persona-aware LLM drive the query, and explicitly append "-live" 
        # to force YouTube to return standard VODs (Video On Demand) instead of 24/7 broadcasts.
        safe_query = urllib.parse.quote(query + " -live")
        url = f"https://www.youtube.com/results?search_query={safe_query}"
        
        # Hardened User-Agent to prevent YouTube from dropping the connection
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        )
        import ssl
        context = ssl._create_unverified_context()
        
        # 3.0s timeout: Fail fast if YouTube throttles the IP
        with urllib.request.urlopen(req, timeout=3.0, context=context) as response:
            html = response.read().decode('utf-8')
            
            video_ids = re.findall(r"watch\?v=([a-zA-Z0-9_-]{11})", html)
            
            # Remove duplicates while preserving order
            unique_ids = list(dict.fromkeys(video_ids))
            
            # Return JSON string of top 2 IDs to save context window tokens
            return json.dumps(unique_ids[:2])
            
    except Exception as e:
        logger.warning(f"YouTube Scraper failed or timed out: {e}")
        return "[]"