"""YouTube Search via SERP API."""

import argparse
import requests
from .common import get_env, output_json, error_exit, success_result


def search_youtube(
    query: str,
    num: int | None = None,
    sp: str | None = None,  # Search parameters (filters)
    gl: str = "us",
    hl: str = "en",
) -> dict:
    """Search YouTube via SERP API.
    
    Args:
        query: Search query
        sp: Search parameters for filtering (e.g., "EgIQAQ==" for videos only)
        gl: Country code
        hl: Language code
    
    Returns:
        Dict with video_results
    """
    api_key = get_env("SERPAPI_API_KEY")
    
    params = {
        "engine": "youtube",
        "search_query": query,
        "api_key": api_key,
        "gl": gl,
        "hl": hl,
    }
    
    if sp:
        params["sp"] = sp
    
    response = requests.get("https://serpapi.com/search", params=params, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    
    # Extract and simplify video results
    video_results = data.get("video_results", [])
    
    simplified = []
    for video in video_results:
        simplified.append({
            "title": video.get("title"),
            "link": video.get("link"),
            "video_id": video.get("link", "").split("v=")[-1].split("&")[0] if video.get("link") else None,
            "channel": video.get("channel", {}).get("name") if isinstance(video.get("channel"), dict) else video.get("channel"),
            "channel_link": video.get("channel", {}).get("link") if isinstance(video.get("channel"), dict) else None,
            "published_date": video.get("published_date"),
            "views": video.get("views"),
            "length": video.get("length"),
            "description": video.get("description"),
            "thumbnail": video.get("thumbnail", {}).get("static") if isinstance(video.get("thumbnail"), dict) else video.get("thumbnail"),
        })
    
    if num is not None:
        simplified = simplified[:num]

    return {
        "query": query,
        "video_results": simplified,
        "ads": data.get("ads", []),
        "filters": data.get("filters", []),
    }


def main():
    parser = argparse.ArgumentParser(description="YouTube Search via SERP API")
    parser.add_argument("query", help="Search query")
    parser.add_argument("-n", "--num", type=int, default=None, help="Max number of results")
    parser.add_argument("--gl", default="us", help="Country code")
    parser.add_argument("--hl", default="en", help="Language code")
    parser.add_argument("--sp", help="Search parameters for filtering (raw)")
    parser.add_argument("-t", "--time", dest="time_filter", help="Time filter: h=hour, d=day, w=week, m=month, y=year")
    
    args = parser.parse_args()
    
    # YouTube upload date sp params (from SERP API docs)
    TIME_FILTER_MAP = {
        "h": "EgIIAQ%3D%3D",   # Last hour
        "d": "EgIIAg%3D%3D",   # Today
        "w": "EgIIAw%3D%3D",   # This week
        "m": "EgIIBA%3D%3D",   # This month
        "y": "EgIIBQ%3D%3D",   # This year
    }
    
    sp = args.sp
    if args.time_filter:
        sp = TIME_FILTER_MAP.get(args.time_filter, args.time_filter)
    
    try:
        results = search_youtube(
            query=args.query,
            num=args.num,
            sp=sp,
            gl=args.gl,
            hl=args.hl,
        )
        output_json(success_result(results, "youtube-search"))
    except requests.RequestException as e:
        error_exit(f"Request failed: {e}")
    except Exception as e:
        error_exit(f"Error: {e}")


if __name__ == "__main__":
    main()
