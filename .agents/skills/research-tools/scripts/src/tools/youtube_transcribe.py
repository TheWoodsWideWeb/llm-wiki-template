"""YouTube Transcription via ytscrape with Oxylabs proxy support."""

import argparse
import os
import sys
from .common import output_json, error_exit, success_result, get_oxylabs_proxy_url


def transcribe_youtube(
    video: str,  # URL or video ID
    format: str = "text",  # text, json, srt, vtt
    lang: str = "en",
    no_cache: bool = False,
    verbose: bool = False,
) -> dict:
    """Transcribe a YouTube video via ytscrape.
    
    Uses Oxylabs proxy if configured to avoid IP blocks.
    
    Args:
        video: YouTube URL or video ID
        format: Output format (text, json, srt, vtt)
        lang: Preferred language
        no_cache: Force re-fetch
        verbose: Show extraction attempts
    
    Returns:
        Dict with transcript data
    """
    try:
        from ytscrape import TranscriptFetcher
    except ImportError:
        error_exit("ytscrape not installed. Run: uv add ytscrape")
    
    # Configure proxy from Oxylabs
    proxy_url = get_oxylabs_proxy_url()
    
    # Get OpenAI key for Whisper fallback
    openai_key = os.environ.get("OPENAI_API_KEY")
    
    # Initialize fetcher
    fetcher = TranscriptFetcher(
        proxy_url=proxy_url,
        openai_api_key=openai_key,
        use_cache=not no_cache,
    )
    
    try:
        result = fetcher.fetch(video, preferred_language=lang)
    except Exception as e:
        error_exit(f"Transcription failed: {e}")
    
    # Format output
    if format == "text":
        content = result.to_text()
    elif format == "json":
        content = result.model_dump()
    elif format == "srt":
        content = result.to_srt()
    elif format == "vtt":
        content = result.to_vtt()
    else:
        content = result.to_text()
    
    return {
        "video_id": result.video_id,
        "language": result.language,
        "is_generated": result.is_generated,
        "source": result.source,  # transcript_api, ytdlp, or whisper
        "format": format,
        "content": content,
        "segment_count": len(result.segments),
        "proxy_used": proxy_url is not None,
    }


def main():
    parser = argparse.ArgumentParser(description="YouTube Transcription via ytscrape")
    parser.add_argument("video", help="YouTube URL or video ID")
    parser.add_argument("-f", "--format", default="text",
                        choices=["text", "json", "srt", "vtt"],
                        help="Output format")
    parser.add_argument("-l", "--lang", default="en", help="Preferred language")
    parser.add_argument("--no-cache", action="store_true", help="Force re-fetch")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show extraction attempts")
    
    args = parser.parse_args()
    
    try:
        results = transcribe_youtube(
            video=args.video,
            format=args.format,
            lang=args.lang,
            no_cache=args.no_cache,
            verbose=args.verbose,
        )
        output_json(success_result(results, "youtube-transcribe"))
    except Exception as e:
        error_exit(f"Error: {e}")


if __name__ == "__main__":
    main()
