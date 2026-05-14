"""Google News Search via SERP API."""

import argparse
import requests
from .common import get_env, output_json, error_exit, success_result


def search_google_news(
    query: str,
    num: int | None = None,
    gl: str = "us",
    hl: str = "en",
    topic_token: str | None = None,  # For browsing specific topics
    tbs: str | None = None,  # Time filter: qdr:h, qdr:d, qdr:w, qdr:m, qdr:y
) -> dict:
    """Search Google News via SERP API.
    
    Args:
        query: Search query (or topic name)
        gl: Country code
        hl: Language code
        topic_token: Specific topic token for browsing
        tbs: Time filter (e.g., "qdr:d" for past day)
    
    Returns:
        Dict with news_results
    """
    api_key = get_env("SERPAPI_API_KEY")
    
    params = {
        "engine": "google_news",
        "q": query,
        "api_key": api_key,
        "gl": gl,
        "hl": hl,
    }
    
    if topic_token:
        params["topic_token"] = topic_token
    if tbs:
        params["tbs"] = tbs
    
    response = requests.get("https://serpapi.com/search", params=params, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    
    # Extract news results
    news_results = data.get("news_results", [])
    
    # Simplify each result
    simplified = []
    for item in news_results:
        simplified.append({
            "title": item.get("title"),
            "link": item.get("link"),
            "source": item.get("source", {}).get("name") if isinstance(item.get("source"), dict) else item.get("source"),
            "date": item.get("date"),
            "snippet": item.get("snippet"),
            "thumbnail": item.get("thumbnail"),
        })
    
    if num is not None:
        simplified = simplified[:num]

    return {
        "query": query,
        "news_results": simplified,
        "menu_links": data.get("menu_links", []),  # Topic categories
    }


def main():
    parser = argparse.ArgumentParser(description="Google News Search via SERP API")
    parser.add_argument("query", help="Search query")
    parser.add_argument("-n", "--num", type=int, default=None, help="Max number of results")
    parser.add_argument("--gl", default="us", help="Country code")
    parser.add_argument("--hl", default="en", help="Language code")
    parser.add_argument("--topic", dest="topic_token", help="Topic token for specific topics")
    parser.add_argument("-t", "--time", dest="tbs", help="Time filter: h=hour, d=day, w=week, m=month, y=year")
    
    args = parser.parse_args()
    
    # Convert shorthand time filter
    tbs = None
    if args.tbs:
        if args.tbs in ["h", "d", "w", "m", "y"]:
            tbs = f"qdr:{args.tbs}"
        else:
            tbs = args.tbs
    
    try:
        results = search_google_news(
            query=args.query,
            num=args.num,
            gl=args.gl,
            hl=args.hl,
            topic_token=args.topic_token,
            tbs=tbs,
        )
        output_json(success_result(results, "google-news"))
    except requests.RequestException as e:
        error_exit(f"Request failed: {e}")
    except Exception as e:
        error_exit(f"Error: {e}")


if __name__ == "__main__":
    main()
