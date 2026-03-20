from typing import Any, Dict, List, Optional

try:
    from tavily import TavilyClient
except ImportError:
    TavilyClient = None

import os
from dotenv import load_dotenv

load_dotenv()


def run(query: str, max_results: int = 5) -> Dict[str, Any]:
    if TavilyClient is None:
        return {"error": "tavily package not installed. Run: pip install tavily-python"}

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return {"error": "TAVILY_API_KEY not found in environment variables"}

    try:
        client = TavilyClient(api_key=api_key)
        search_results = client.search(
            query=query,
            max_results=max_results,
        )

        results = []
        for result in search_results.get("results", []):
            results.append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "content": result.get("content", "")[:500],
                "score": result.get("score", 0),
            })

        return {
            "query": query,
            "answer": search_results.get("answer"),
            "results": results,
        }
    except Exception as e:
        return {"error": str(e)}


SKILL = {
    "name": "tavily_search",
    "description": "Search the web using Tavily Search API. Use this when you need to find documentation, examples, or troubleshooting information.",
    "inputs": {
        "query": "str (required) - Search query in English for best results",
        "max_results": "int (optional, default 5) - Maximum number of results to return",
    },
    "run": run,
}
