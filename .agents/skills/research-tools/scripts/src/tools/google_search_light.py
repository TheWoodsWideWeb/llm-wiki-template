"""Google Search Light via SERP API - organic results only, faster and cheaper."""

import argparse
import requests
from .common import get_env, output_json, error_exit, success_result


def search_google_light(
    query: str,
    num: int = 10,
    location: str | None = None,
    gl: str = "us",
    hl: str = "en",
    tbs: str | None = None,
) -> dict:
    """Search Google Light via SERP API.
    
    Light API returns only organic results - no ads, knowledge graph, etc.
    Faster and uses fewer credits.
    
    Args:
        query: Search query
        num: Number of results (1-100)
        location: Location for search
        gl: Country code
        hl: Language code
        tbs: Time filter
    
    Returns:
        Dict with organic_results only
    """
    api_key = get_env("SERPAPI_API_KEY")
    
    params = {
        "engine": "google_light",
        "q": query,
        "api_key": api_key,
        "num": num,
        "gl": gl,
        "hl": hl,
    }
    
    if location:
        params["location"] = location
    if tbs:
        params["tbs"] = tbs
    
    response = requests.get("https://serpapi.com/search", params=params, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    
    return {
        "query": query,
        "organic_results": data.get("organic_results", []),
        "total_results": data.get("search_information", {}).get("total_results"),
    }


def main():
    parser = argparse.ArgumentParser(description="Google Search Light via SERP API (organic results only)")
    parser.add_argument("query", help="Search query")
    parser.add_argument("-n", "--num", type=int, default=10, help="Number of results")
    parser.add_argument("-l", "--location", help="Location")
    parser.add_argument("--gl", default="us", help="Country code")
    parser.add_argument("--hl", default="en", help="Language code")
    parser.add_argument("-t", "--time", dest="tbs", help="Time filter: h/d/w/m/y")
    
    args = parser.parse_args()
    
    tbs = None
    if args.tbs:
        if args.tbs in ["h", "d", "w", "m", "y"]:
            tbs = f"qdr:{args.tbs}"
        else:
            tbs = args.tbs
    
    try:
        results = search_google_light(
            query=args.query,
            num=args.num,
            location=args.location,
            gl=args.gl,
            hl=args.hl,
            tbs=tbs,
        )
        output_json(success_result(results, "google-search-light"))
    except requests.RequestException as e:
        error_exit(f"Request failed: {e}")
    except Exception as e:
        error_exit(f"Error: {e}")


if __name__ == "__main__":
    main()
