import os
from functools import lru_cache
from google.cloud import discoveryengine_v1 as discoveryengine
from google.cloud import secretmanager
import logging

logger = logging.getLogger(__name__)

# Global Singleton to prevent rebuilding gRPC connections on every query
_search_client = None

@lru_cache(maxsize=1)
def get_mercury_config():
    """Fetches IDs securely from Secret Manager. Cached after first run."""
    client = secretmanager.SecretManagerServiceClient()
    project_id = "100609325159"
    
    def fetch_secret(secret_id):
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8").strip()

    return {
        "project": project_id,
        "app_id": fetch_secret("MERCURY_APP_ID"), 
    }

# 🚀 THE FIX: Explicitly defined the list contents as strings
def fetch_institutional_news(query: str, num_results: int = 3) -> list[str]:
    """Enterprise news fetcher with 404-safe pathing and hot-pooled connections."""
    global _search_client
    
    try:
        config = get_mercury_config()
        
        if _search_client is None:
            _search_client = discoveryengine.SearchServiceClient()

        serving_config = (
            f"projects/{config['project']}/locations/global/"
            f"collections/default_collection/engines/{config['app_id']}/"
            f"servingConfigs/default_config"
        )

        request = discoveryengine.SearchRequest(
            serving_config=serving_config,
            query=query,
            page_size=num_results,
        )

        response = _search_client.search(request)
        
        news_items = []
        for result in response.results:
            data = result.document.derived_struct_data
            title = data.get("title", "Institutional News")
            link = data.get("link", "#")
            news_items.append(f"<b>{title}</b> <a href='{link}' target='_blank'>[Source]</a>")

        return news_items if news_items else ["Whitelisted sources are currently indexing..."]

    except Exception as e:
        logger.error(f"❌ Professional Search Error: {e}")
        return ["Institutional news feed is synchronizing. Please refresh in 2 minutes."]