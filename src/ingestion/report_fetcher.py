# src/ingestion/report_fetcher.py

import os
import requests
import shutil
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

TEMP_STORAGE_PATH = "data/TEMP"


def find_and_download_report(company_name: str, ticker: str) -> str | None:
    """
    Searches for a company's latest report using Tavily and downloads the first PDF result.

    Args:
        company_name (str): The full name of the company for the search query.
        ticker (str): The company ticker for creating the storage path.

    Returns:
        str | None: The path to the directory containing the downloaded report, or None.
    """
    print(f"Searching for the latest report for {company_name}...")
    try:
        tavily_api_key = os.getenv("TAVILY_API_KEY")
        if not tavily_api_key:
            raise ValueError("Tavily API key not found in environment variables.")

        client = TavilyClient(api_key=tavily_api_key)

        # A targeted query to find official investor reports
        query = (
            f'"{company_name}" investor relations latest quarterly report filetype:pdf'
        )

        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=5,  # Check the top 5 results
        )

        pdf_url = None
        for result in response.get("results", []):
            if result.get("url", "").lower().endswith(".pdf"):
                pdf_url = result["url"]
                break

        if not pdf_url:
            print(
                f"No direct PDF link found for {company_name}'s report in search results."
            )
            return None

        print(f"Found report URL: {pdf_url}")
        print("Downloading report...")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        pdf_response = requests.get(pdf_url, headers=headers, stream=True, timeout=30)
        pdf_response.raise_for_status()

        report_dir = os.path.join(TEMP_STORAGE_PATH, ticker)
        if os.path.exists(report_dir):
            shutil.rmtree(report_dir)
        os.makedirs(report_dir, exist_ok=True)

        file_path = os.path.join(report_dir, "downloaded_report.pdf")

        with open(file_path, "wb") as f:
            for chunk in pdf_response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"Report successfully downloaded to: {file_path}")
        return report_dir

    except Exception as e:
        print(f"An error occurred while fetching the report for {company_name}: {e}")
        return None
    