"""Google Search via SERP API."""

import argparse
import requests
from .common import get_env, output_json, error_exit, success_result


def search_google(
    query: str,
    num: int = 10,
    location: str | None = None,
    gl: str = "us",
    hl: str = "en",
    tbs: str | None = None,  # Time filter: qdr:h (hour), qdr:d (day), qdr:w (week), qdr:m (month), qdr:y (year)
) -> dict:
    """Search Google via SERP API.
    
    Args:
        query: Search query
        num: Number of results (1-100)
        location: Location for search (e.g., "Denver, Colorado")
        gl: Country code (e.g., "us", "uk")
        hl: Language code (e.g., "en", "es")
        tbs: Time filter (e.g., "qdr:d" for past day)
    
    Returns:
        Dict with organic_results, knowledge_graph, etc.
    """
    api_key = get_env("SERPAPI_API_KEY")
    
    params = {
        "engine": "google",
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
    
    # Extract the useful parts
    return {
        "query": query,
        "organic_results": data.get("organic_results", []),
        "knowledge_graph": data.get("knowledge_graph"),
        "answer_box": data.get("answer_box"),
        "related_searches": data.get("related_searches", []),
        "total_results": data.get("search_information", {}).get("total_results"),
    }


def main():
    parser = argparse.ArgumentParser(description="Google Search via SERP API")
    parser.add_argument("query", help="Search query")
    parser.add_argument("-n", "--num", type=int, default=10, help="Number of results")
    parser.add_argument("-l", "--location", help="Location (e.g., 'Denver, Colorado')")
    parser.add_argument("--gl", default="us", help="Country code")
    parser.add_argument("--hl", default="en", help="Language code")
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
        results = search_google(
            query=args.query,
            num=args.num,
            location=args.location,
            gl=args.gl,
            hl=args.hl,
            tbs=tbs,
        )
        output_json(success_result(results, "google-search"))
    except requests.RequestException as e:
        error_exit(f"Request failed: {e}")
    except Exception as e:
        error_exit(f"Error: {e}")


if __name__ == "__main__":
    main()
