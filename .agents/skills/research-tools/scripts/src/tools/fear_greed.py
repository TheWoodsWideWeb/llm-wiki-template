"""Crypto Fear & Greed Index via Alternative.me API."""

import argparse
import requests
from .common import output_json, error_exit, success_result


def get_fear_greed(limit: int = 1) -> dict:
    """Get Fear & Greed Index.
    
    Args:
        limit: Number of historical days (1 = today only)
    
    Returns:
        Dict with current value and classification
    """
    response = requests.get(
        "https://api.alternative.me/fng/",
        params={"limit": limit},
        timeout=10,
    )
    response.raise_for_status()
    
    data = response.json()
    
    if data.get("metadata", {}).get("error"):
        error_exit(f"API error: {data['metadata']['error']}")
    
    entries = data.get("data", [])
    
    # Parse entries
    results = []
    for entry in entries:
        results.append({
            "value": int(entry.get("value", 0)),
            "classification": entry.get("value_classification"),
            "timestamp": entry.get("timestamp"),
        })
    
    current = results[0] if results else None
    
    return {
        "current": current,
        "history": results if limit > 1 else None,
    }


def main():
    parser = argparse.ArgumentParser(description="Crypto Fear & Greed Index")
    parser.add_argument("-n", "--days", type=int, default=1,
                        help="Number of historical days")
    
    args = parser.parse_args()
    
    try:
        results = get_fear_greed(limit=args.days)
        output_json(success_result(results, "fear-greed"))
    except requests.RequestException as e:
        error_exit(f"Request failed: {e}")
    except Exception as e:
        error_exit(f"Error: {e}")


if __name__ == "__main__":
    main()
