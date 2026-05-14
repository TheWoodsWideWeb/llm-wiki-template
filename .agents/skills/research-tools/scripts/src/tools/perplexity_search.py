"""Perplexity Sonar Pro for synthesized research with citations."""

import argparse
import requests
from .common import get_env, output_json, error_exit, success_result


def query_perplexity(
    query: str,
    model: str = "sonar-pro",
    system_prompt: str | None = None,
) -> dict:
    """Query Perplexity Sonar Pro for synthesized research.
    
    Returns content with citations - great for research overviews.
    
    Args:
        query: Research question or topic
        model: Perplexity model (sonar-pro recommended)
        system_prompt: Optional system prompt for context
    
    Returns:
        Dict with content and citations
    """
    api_key = get_env("PERPLEXITY_API_KEY")
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": query})
    
    response = requests.post(
        "https://api.perplexity.ai/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": messages,
        },
        timeout=60,
    )
    response.raise_for_status()
    
    data = response.json()
    
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    citations = data.get("citations", [])
    usage = data.get("usage", {})
    
    return {
        "query": query,
        "model": model,
        "content": content,
        "citations": citations,
        "tokens": {
            "prompt": usage.get("prompt_tokens"),
            "completion": usage.get("completion_tokens"),
            "total": usage.get("total_tokens"),
        },
    }


def research_topic(topic: str) -> dict:
    """Research a topic with a structured approach.
    
    Uses a system prompt optimized for research synthesis.
    """
    system_prompt = """You are a research assistant. Provide:
1. A clear, accurate summary of the topic
2. Key facts and findings from reliable sources
3. Current state of research or practice
4. Any controversies or debates

Be concise but thorough. Cite sources where appropriate."""
    
    return query_perplexity(topic, system_prompt=system_prompt)


def main():
    parser = argparse.ArgumentParser(description="Perplexity Sonar Pro Search")
    parser.add_argument("query", help="Research query")
    parser.add_argument("-m", "--model", default="sonar-pro", help="Perplexity model")
    parser.add_argument("-s", "--system", dest="system_prompt",
                        help="System prompt for context")
    parser.add_argument("-r", "--research", action="store_true",
                        help="Use structured research prompt")
    
    args = parser.parse_args()
    
    try:
        if args.research:
            results = research_topic(args.query)
        else:
            results = query_perplexity(
                query=args.query,
                model=args.model,
                system_prompt=args.system_prompt,
            )
        
        output_json(success_result(results, "perplexity-search"))
    except requests.RequestException as e:
        error_exit(f"Request failed: {e}")
    except Exception as e:
        error_exit(f"Error: {e}")


if __name__ == "__main__":
    main()
