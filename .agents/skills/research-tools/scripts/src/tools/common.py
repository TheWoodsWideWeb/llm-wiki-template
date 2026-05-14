"""Common utilities for all tools."""

import json
import os
import sys
from datetime import datetime
from typing import Any

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))


def get_env(key: str, required: bool = True) -> str | None:
    """Get environment variable, optionally required."""
    value = os.environ.get(key)
    if required and not value:
        error_exit(f"Missing required environment variable: {key}")
    return value


def output_json(data: dict[str, Any]) -> None:
    """Output JSON to stdout."""
    print(json.dumps(data, indent=2, ensure_ascii=False))


def error_exit(message: str, code: int = 1) -> None:
    """Print error and exit."""
    result = {
        "success": False,
        "error": message,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    print(json.dumps(result, indent=2), file=sys.stderr)
    sys.exit(code)


def success_result(data: Any, source: str, **extra: Any) -> dict[str, Any]:
    """Create a success result dict."""
    return {
        "success": True,
        "data": data,
        "source": source,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        **extra
    }


def get_oxylabs_proxy_url() -> str | None:
    """Build Oxylabs residential proxy URL from env vars."""
    username = os.environ.get("OXY_USERNAME")
    password = os.environ.get("OXY_PASSWORD")
    if username and password:
        return f"http://{username}:{password}@pr.oxylabs.io:7777"
    return None
