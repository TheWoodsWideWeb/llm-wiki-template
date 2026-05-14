"""X/Twitter Search via Grok 4.1 DeepSearch."""

import argparse
import requests
from .common import get_env, output_json, error_exit, success_result


def search_x(
    query: str,
    model: str = "grok-4-1-fast-non-reasoning",
) -> dict:
    """Search X/Twitter via Grok 4.1 with DeepSearch.
    
    Can search for topics, read specific posts, or get account takes.
    
    Args:
        query: Search query or instruction (e.g., "What are people saying about rapamycin?")
        model: Grok model to use
    
    Returns:
        Dict with search results
    """
    api_key = get_env("XAI_API_KEY")
    
    response = requests.post(
        "https://api.x.ai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": query}],
        },
        timeout=60,
    )
    response.raise_for_status()
    
    data = response.json()
    
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    usage = data.get("usage", {})
    
    return {
        "query": query,
        "model": model,
        "content": content,
        "tokens": {
            "prompt": usage.get("prompt_tokens"),
            "completion": usage.get("completion_tokens"),
            "total": usage.get("total_tokens"),
        },
    }


def read_x_post(url: str) -> dict:
    """Read a specific X post.
    
    Args:
        url: X post URL
    
    Returns:
        Dict with post content
    """
    query = f"What does this tweet say? Summarize the content and any notable replies: {url}"
    return search_x(query)


def main():
    parser = argparse.ArgumentParser(description="X/Twitter Search via Grok 4.1")
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search X")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("-m", "--model", default="grok-4-1-fast-non-reasoning",
                               help="Grok model")
    
    # Read command
    read_parser = subparsers.add_parser("read", help="Read a specific post")
    read_parser.add_argument("url", help="X post URL")
    
    args = parser.parse_args()
    
    if not args.command:
        # Default to search if just a query is provided
        if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
            results = search_x(sys.argv[1])
            output_json(success_result(results, "x-search"))
            return
        parser.print_help()
        return
    
    try:
        if args.command == "search":
            results = search_x(args.query, model=args.model)
        else:  # read
            results = read_x_post(args.url)
        
        output_json(success_result(results, f"x-{args.command}"))
    except requests.RequestException as e:
        error_exit(f"Request failed: {e}")
    except Exception as e:
        error_exit(f"Error: {e}")


# Need to import sys for the default behavior
import sys

if __name__ == "__main__":
    main()
