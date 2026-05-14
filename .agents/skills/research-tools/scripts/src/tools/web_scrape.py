"""Web Scraping via Firecrawl API."""

import argparse
import requests
from .common import get_env, output_json, error_exit, success_result


def scrape_url(
    url: str,
    formats: list[str] | None = None,  # markdown, html, links, screenshot
    only_main_content: bool = True,
    wait_for: int | None = None,  # ms to wait for dynamic content
) -> dict:
    """Scrape a URL via Firecrawl API.
    
    Args:
        url: URL to scrape
        formats: Output formats (default: ["markdown"])
        only_main_content: Extract only main content
        wait_for: Milliseconds to wait for dynamic content
    
    Returns:
        Dict with scraped content
    """
    api_key = get_env("FIRECRAWL_API_KEY")
    
    if formats is None:
        formats = ["markdown"]
    
    payload = {
        "url": url,
        "formats": formats,
        "onlyMainContent": only_main_content,
    }
    
    if wait_for:
        payload["waitFor"] = wait_for
    
    response = requests.post(
        "https://api.firecrawl.dev/v1/scrape",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    
    data = response.json()
    
    if not data.get("success"):
        error_exit(f"Scrape failed: {data.get('error', 'Unknown error')}")
    
    result_data = data.get("data", {})
    
    return {
        "url": url,
        "markdown": result_data.get("markdown"),
        "html": result_data.get("html"),
        "links": result_data.get("links", []),
        "metadata": result_data.get("metadata", {}),
    }


def search_and_scrape(
    query: str,
    limit: int = 5,
    scrape: bool = False,
    tbs: str | None = None,  # Time filter
) -> dict:
    """Search and optionally scrape results via Firecrawl.
    
    Args:
        query: Search query
        limit: Number of results
        scrape: Whether to scrape results
        tbs: Time filter (qdr:h, qdr:d, qdr:w, qdr:m, qdr:y)
    
    Returns:
        Dict with search results and optionally content
    """
    api_key = get_env("FIRECRAWL_API_KEY")
    
    payload = {
        "query": query,
        "limit": limit,
    }
    
    if tbs:
        payload["tbs"] = tbs
    
    if scrape:
        payload["scrapeOptions"] = {
            "formats": ["markdown"],
            "onlyMainContent": True,
        }
    
    response = requests.post(
        "https://api.firecrawl.dev/v1/search",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=120,
    )
    response.raise_for_status()
    
    data = response.json()
    
    if not data.get("success"):
        error_exit(f"Search failed: {data.get('error', 'Unknown error')}")
    
    return {
        "query": query,
        "results": data.get("data", []),
    }


def main():
    parser = argparse.ArgumentParser(description="Web Scraping via Firecrawl")
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # Scrape command
    scrape_parser = subparsers.add_parser("scrape", help="Scrape a URL")
    scrape_parser.add_argument("url", help="URL to scrape")
    scrape_parser.add_argument("-f", "--formats", nargs="+", default=["markdown"],
                               help="Output formats: markdown, html, links, screenshot")
    scrape_parser.add_argument("--include-all", action="store_true",
                               help="Include non-main content")
    scrape_parser.add_argument("--wait", type=int, help="Wait ms for dynamic content")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search and optionally scrape")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("-n", "--limit", type=int, default=5, help="Number of results")
    search_parser.add_argument("-s", "--scrape", action="store_true", help="Scrape results")
    search_parser.add_argument("-t", "--time", dest="tbs",
                               help="Time filter: h=hour, d=day, w=week, m=month, y=year")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == "scrape":
            results = scrape_url(
                url=args.url,
                formats=args.formats,
                only_main_content=not args.include_all,
                wait_for=args.wait,
            )
        else:  # search
            tbs = None
            if args.tbs:
                if args.tbs in ["h", "d", "w", "m", "y"]:
                    tbs = f"qdr:{args.tbs}"
                else:
                    tbs = args.tbs
            
            results = search_and_scrape(
                query=args.query,
                limit=args.limit,
                scrape=args.scrape,
                tbs=tbs,
            )
        
        output_json(success_result(results, f"web-scrape-{args.command}"))
    except requests.RequestException as e:
        error_exit(f"Request failed: {e}")
    except Exception as e:
        error_exit(f"Error: {e}")


if __name__ == "__main__":
    main()
