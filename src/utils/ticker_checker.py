# src/utils/ticker_checker.py

import os
import requests
from dotenv import load_dotenv

load_dotenv()


def find_best_ticker_match(keywords: str) -> tuple[str | None, str | None]:
    """
    Searches Alpha Vantage for a ticker and returns the best match.
    Now includes better error handling for API rate limits.
    """
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        print("Error: ALPHA_VANTAGE_API_KEY not found.")
        return None, None

    url = f"https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={keywords}&apikey={api_key}"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()

        # NEW: Check for the rate limit note from the API
        if "Note" in data:
            print(
                f"Alpha Vantage API rate limit likely exceeded. Response: {data['Note']}"
            )
            return None, None

        if "bestMatches" in data and data["bestMatches"]:
            best_match = data["bestMatches"][0]
            symbol = best_match.get("1. symbol")
            name = best_match.get("2. name")

            if not symbol or not name:
                return None, None

            cleaned_symbol = "".join(e for e in symbol if e.isalnum() or e in ".-_")

            if 3 <= len(cleaned_symbol) <= 63:
                return cleaned_symbol, name
            else:
                return None, None
        else:
            print(f"No matches found for '{keywords}'. API response: {data}")
            return None, None

    except Exception as e:
        print(f"An error occurred during ticker search: {e}")
        return None, None
