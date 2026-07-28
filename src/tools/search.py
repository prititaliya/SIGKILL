# search tool
import re
import urllib.parse
from typing import List, Optional
from html import unescape


def web_search(query: str, num_results: int = 5) -> List[str]:
    """
    Perform a web search using DuckDuckGo and return the top results.

    Args:
        query (str): The search query.
        num_results (int): The number of top results to return.

    Returns:
        List[str]: A list of URLs of the top search results.
    """
    # Encode the query for URL
    encoded_query = urllib.parse.quote_plus(query)
    search_url = f"https://duckduckgo.com/html/?q={encoded_query}"

    # Fetch the search results page
    import requests
    response = requests.get(search_url)
    response.raise_for_status()

    # Extract URLs from the search results
    urls = re.findall(r'<a rel="nofollow" class="result__a" href="(.*?)">', response.text)
    
    # Unescape HTML entities and return the top results
    return [unescape(url) for url in urls[:num_results]]