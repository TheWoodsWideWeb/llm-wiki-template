"""Google Trends via SERP API."""

import argparse
import requests
from .common import get_env, output_json, error_exit, success_result


def get_google_trends(
    query: str,
    data_type: str = "TIMESERIES",  # TIMESERIES, GEO_MAP, RELATED_TOPICS, RELATED_QUERIES
    geo: str = "US",
    tz: int = 420,  # Timezone offset (420 = PST)
    date: str = "today 12-m",  # Time range: "now 1-H", "now 4-H", "now 1-d", "now 7-d", "today 1-m", "today 3-m", "today 12-m", "today 5-y", "all"
    cat: int = 0,  # Category (0 = all)
) -> dict:
    """Get Google Trends data via SERP API.
    
    Args:
        query: Search term (or comma-separated for comparison)
        data_type: Type of data to fetch
        geo: Country/region code
        tz: Timezone offset in minutes
        date: Time range
        cat: Category ID
    
    Returns:
        Dict with trends data
    """
    api_key = get_env("SERPAPI_API_KEY")
    
    params = {
        "engine": "google_trends",
        "q": query,
        "api_key": api_key,
        "data_type": data_type,
        "geo": geo,
        "tz": tz,
        "date": date,
        "cat": cat,
    }
    
    response = requests.get("https://serpapi.com/search", params=params, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    
    result = {
        "query": query,
        "data_type": data_type,
        "geo": geo,
        "date_range": date,
    }
    
    # Add type-specific data
    if data_type == "TIMESERIES":
        result["interest_over_time"] = data.get("interest_over_time", {})
    elif data_type == "GEO_MAP":
        result["interest_by_region"] = data.get("interest_by_region", {})
    elif data_type == "RELATED_TOPICS":
        result["related_topics"] = data.get("related_topics", {})
    elif data_type == "RELATED_QUERIES":
        result["related_queries"] = data.get("related_queries", {})
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Google Trends via SERP API")
    parser.add_argument("query", help="Search term(s), comma-separated for comparison")
    parser.add_argument("-t", "--type", dest="data_type", default="TIMESERIES",
                        choices=["TIMESERIES", "GEO_MAP", "RELATED_TOPICS", "RELATED_QUERIES"],
                        help="Data type to fetch")
    parser.add_argument("--geo", default="US", help="Country/region code")
    parser.add_argument("-d", "--date", default="today 12-m",
                        help="Time range: 'now 1-H', 'now 1-d', 'now 7-d', 'today 1-m', 'today 3-m', 'today 12-m', 'today 5-y', 'all'")
    parser.add_argument("--cat", type=int, default=0, help="Category ID (0=all)")
    
    args = parser.parse_args()
    
    try:
        results = get_google_trends(
            query=args.query,
            data_type=args.data_type,
            geo=args.geo,
            date=args.date,
            cat=args.cat,
        )
        output_json(success_result(results, "google-trends"))
    except requests.RequestException as e:
        error_exit(f"Request failed: {e}")
    except Exception as e:
        error_exit(f"Error: {e}")


if __name__ == "__main__":
    main()
