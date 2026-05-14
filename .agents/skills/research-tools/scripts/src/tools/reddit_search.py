"""Reddit Search via public JSON API."""

import argparse
import requests
from .common import output_json, error_exit, success_result


# Browser-like User-Agent required for Reddit API
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def get_subreddit_posts(
    subreddit: str,
    sort: str = "hot",  # hot, new, top, rising
    time: str = "day",  # hour, day, week, month, year, all (for top/controversial)
    limit: int = 25,
) -> dict:
    """Get posts from a subreddit.
    
    Args:
        subreddit: Subreddit name (without r/)
        sort: Sort method (hot, new, top, rising)
        time: Time filter for top/controversial
        limit: Number of posts (max 100)
    
    Returns:
        Dict with posts
    """
    url = f"https://www.reddit.com/r/{subreddit}/{sort}.json"
    params = {"limit": min(limit, 100)}
    
    if sort in ["top", "controversial"]:
        params["t"] = time
    
    response = requests.get(url, headers=HEADERS, params=params, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    
    posts = []
    for child in data.get("data", {}).get("children", []):
        post = child.get("data", {})
        posts.append({
            "id": post.get("id"),
            "title": post.get("title"),
            "selftext": post.get("selftext", "")[:500],  # Truncate long text
            "author": post.get("author"),
            "score": post.get("score"),
            "upvote_ratio": post.get("upvote_ratio"),
            "num_comments": post.get("num_comments"),
            "url": post.get("url"),
            "permalink": f"https://reddit.com{post.get('permalink')}",
            "created_utc": post.get("created_utc"),
            "subreddit": post.get("subreddit"),
        })
    
    return {
        "subreddit": subreddit,
        "sort": sort,
        "posts": posts,
    }


def search_reddit(
    query: str,
    subreddit: str | None = None,
    sort: str = "relevance",  # relevance, hot, top, new, comments
    time: str = "all",
    limit: int = 25,
) -> dict:
    """Search Reddit.
    
    Args:
        query: Search query
        subreddit: Optional subreddit to search within
        sort: Sort method
        time: Time filter
        limit: Number of results
    
    Returns:
        Dict with search results
    """
    if subreddit:
        url = f"https://www.reddit.com/r/{subreddit}/search.json"
    else:
        url = "https://www.reddit.com/search.json"
    
    params = {
        "q": query,
        "sort": sort,
        "t": time,
        "limit": min(limit, 100),
    }
    
    if subreddit:
        params["restrict_sr"] = "on"
    
    response = requests.get(url, headers=HEADERS, params=params, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    
    posts = []
    for child in data.get("data", {}).get("children", []):
        post = child.get("data", {})
        posts.append({
            "id": post.get("id"),
            "title": post.get("title"),
            "selftext": post.get("selftext", "")[:500],
            "author": post.get("author"),
            "score": post.get("score"),
            "num_comments": post.get("num_comments"),
            "permalink": f"https://reddit.com{post.get('permalink')}",
            "subreddit": post.get("subreddit"),
            "created_utc": post.get("created_utc"),
        })
    
    return {
        "query": query,
        "subreddit": subreddit,
        "sort": sort,
        "results": posts,
    }


def main():
    parser = argparse.ArgumentParser(description="Reddit Search")
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # Posts command
    posts_parser = subparsers.add_parser("posts", help="Get subreddit posts")
    posts_parser.add_argument("subreddit", help="Subreddit name")
    posts_parser.add_argument("-s", "--sort", default="hot",
                              choices=["hot", "new", "top", "rising"],
                              help="Sort method")
    posts_parser.add_argument("-t", "--time", default="day",
                              choices=["hour", "day", "week", "month", "year", "all"],
                              help="Time filter (for top)")
    posts_parser.add_argument("-n", "--limit", type=int, default=25, help="Number of posts")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search Reddit")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("-r", "--subreddit", help="Limit to subreddit")
    search_parser.add_argument("-s", "--sort", default="relevance",
                               choices=["relevance", "hot", "top", "new", "comments"],
                               help="Sort method")
    search_parser.add_argument("-t", "--time", default="all",
                               choices=["hour", "day", "week", "month", "year", "all"],
                               help="Time filter")
    search_parser.add_argument("-n", "--limit", type=int, default=25, help="Number of results")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == "posts":
            results = get_subreddit_posts(
                subreddit=args.subreddit,
                sort=args.sort,
                time=args.time,
                limit=args.limit,
            )
        else:  # search
            results = search_reddit(
                query=args.query,
                subreddit=args.subreddit,
                sort=args.sort,
                time=args.time,
                limit=args.limit,
            )
        
        output_json(success_result(results, f"reddit-{args.command}"))
    except requests.RequestException as e:
        error_exit(f"Request failed: {e}")
    except Exception as e:
        error_exit(f"Error: {e}")


if __name__ == "__main__":
    main()
