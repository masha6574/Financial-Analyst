# src/ingestion/orchestrator.py
import os
import shutil
from src.ingestion.report_fetcher import find_and_download_report
from src.ingestion.document_loader import load_and_chunk_pdfs
from src.ingestion.news_fetcher import fetch_company_news
from src.ingestion.stock_data_fetcher import get_company_overview

# CHANGED: Import the new 'mark_company_as_failed' function
from src.utils.database_handler import mark_company_as_indexed, mark_company_as_failed
from src.core.processing import create_and_store_embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


def process_company_data_background(ticker: str, company_name: str):
    print(f"BACKGROUND TASK: Starting ingestion for {ticker}.")
    report_dir = None
    try:
        all_chunks = []
        stock_overview = {}

        # --- Step 1: Fetch Fast, Live Data ---
        news_docs = fetch_company_news(company_name)
        if news_docs:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1024, chunk_overlap=100
            )
            news_chunks = text_splitter.split_documents(news_docs)
            all_chunks.extend(news_chunks)

        stock_overview = get_company_overview(ticker) or get_company_overview(
            f"{ticker}.BSE"
        )

        # --- Step 2: Fetch Slow, Document Data ---
        report_dir = find_and_download_report(company_name, ticker)
        if report_dir:
            pdf_chunks = load_and_chunk_pdfs(report_dir)
            all_chunks.extend(pdf_chunks)

        if not all_chunks:
            raise ValueError("Failed to gather any processable text data.")

        create_and_store_embeddings(ticker, all_chunks)
        mark_company_as_indexed(ticker, stock_overview)
        print(f"BACKGROUND TASK: Successfully finished ingestion for {ticker}.")

    except Exception as e:
        # NEW: Catch any exception and mark the task as failed
        print(f"BACKGROUND TASK FAILED for {ticker}. Error: {e}")
        mark_company_as_failed(ticker)
    finally:
        if report_dir and os.path.exists(report_dir):
            shutil.rmtree(report_dir)
