# src/main.py

from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import Optional

from src.utils.database_handler import (
    get_company_status,
    mark_company_as_processing,
    initialize_database,
)
from src.ingestion.orchestrator import process_company_data_background
from src.ingestion.news_fetcher import fetch_company_news
from src.ingestion.stock_data_fetcher import get_company_overview
from src.core.qa_agent import create_persistent_rag_chain, create_live_rag_chain
from src.utils.ticker_checker import find_best_ticker_match


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application starting up...")
    initialize_database()
    yield
    print("Application shutting down...")


class QueryRequest(BaseModel):
    company_input: str
    question: str
    # [NEW] Add an optional field for the user to provide an exact ticker
    exact_ticker: Optional[str] = None


app = FastAPI(title="Financial Analyst AI Agent", lifespan=lifespan)


@app.post("/query")
async def handle_query(request: QueryRequest, background_tasks: BackgroundTasks):
    question = request.question

    # --- [MODIFIED] Handle direct ticker input or perform search ---
    if request.exact_ticker:
        # If the user provides an exact ticker, use it directly
        ticker = request.exact_ticker.upper()
        # We might not have the full company name, so we use the ticker as a fallback
        company_name = ticker
    else:
        # Otherwise, use the intelligent search
        company_input = request.company_input
        # NOTE: This assumes `find_best_ticker_match` is modified to return
        # (None, "API_LIMIT_REACHED") when the Alpha Vantage limit is hit.
        ticker, company_name = find_best_ticker_match(company_input)

        # [NEW] Check for the specific API limit error signal
        if company_name == "API_LIMIT_REACHED":
            return {
                "status": "api_limit_exceeded",
                "message": "The automatic ticker search has reached its daily limit. Please provide an exact ticker.",
            }

        if not ticker or not company_name:
            return {
                "status": "error",
                "message": f"Could not find a valid stock ticker for '{company_input}'. Please be more specific.",
            }
    # --- End of modification ---

    status = get_company_status(ticker)

    if status == "indexed":
        rag_chain = create_persistent_rag_chain(ticker)
        answer = rag_chain.invoke(question)
        return {"status": "complete", "answer": answer, "ticker": ticker}

    elif status == "processing":
        return {
            "status": "processing",
            "message": f"Analysis for {company_name} ({ticker}) is already underway.",
            "ticker": ticker,
        }

    elif status == "failed":
        return {
            "status": "failed",
            "message": f"Data processing failed for {company_name} ({ticker}). This may be due to a lack of available online documents.",
            "ticker": ticker,
        }

    else:  # Status is None (not found)
        mark_company_as_processing(ticker)
        background_tasks.add_task(process_company_data_background, ticker, company_name)

        live_news_docs = fetch_company_news(company_name)
        live_stock_overview = get_company_overview(ticker)

        if not live_news_docs:
            return {
                "status": "processing",
                "message": "Could not fetch live news data. Background indexing has started.",
                "ticker": ticker,
            }

        live_rag_chain = create_live_rag_chain(live_news_docs, live_stock_overview)
        initial_answer = live_rag_chain.invoke(question)

        final_answer = (
            f"{initial_answer}\n\n"
            f"*Disclaimer: This is a preliminary answer based on live news. "
            f"The full financial report is now being processed in the background. "
            f"This page will automatically update with the complete analysis when ready.*"
        )
        return {
            "status": "complete_preliminary",
            "answer": final_answer,
            "ticker": ticker,
        }


@app.get("/status/{ticker}")
def get_status(ticker: str):
    status = get_company_status(ticker)
    return {"ticker": ticker, "status": status}


@app.get("/")
def read_root():
    return {"message": "Financial Analyst AI Agent is running."}
