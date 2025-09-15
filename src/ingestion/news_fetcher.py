# src/ingestion/news_fetcher.py

import os
from tavily import TavilyClient
from dotenv import load_dotenv
from langchain_core.documents import Document

load_dotenv()


def fetch_company_news(company_name: str, max_results: int = 5) -> list[Document]:
    try:
        tavily_api_key = os.getenv("TAVILY_API_KEY")
        if not tavily_api_key:
            raise ValueError("Tavily API key not found in environment variables.")

        client = TavilyClient(api_key=tavily_api_key)
        search_query = f"latest financial news and analysis for {company_name}"

        response = client.search(
            query=search_query,
            search_depth="advanced",
            max_results=max_results,
        )

        news_documents = [
            Document(
                page_content=result["content"],
                metadata={"url": result["url"], "title": result["title"]},
            )
            for result in response["results"]
        ]
        return news_documents
    except Exception as e:
        print(f"An error occurred while fetching news: {e}")
        return []
