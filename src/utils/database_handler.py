# src/utils/database_handler.py

import sqlite3
import json
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / "company_data.db"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    # ... (no changes here)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS indexed_companies (
            ticker TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            indexed_at TIMESTAMP NOT NULL,
            stock_overview_json TEXT
        )
    """
    )
    conn.commit()
    conn.close()


def get_company_status(ticker: str) -> str | None:
    # ... (no changes here)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM indexed_companies WHERE ticker = ?", (ticker,))
    result = cursor.fetchone()
    conn.close()
    return result["status"] if result else None


def mark_company_as_processing(ticker: str):
    # ... (no changes here)
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.now()
    cursor.execute(
        """
        INSERT OR REPLACE INTO indexed_companies (ticker, status, indexed_at, stock_overview_json)
        VALUES (?, ?, ?, ?)
    """,
        (ticker, "processing", timestamp, None),
    )
    conn.commit()
    conn.close()
    print(f"Marked ticker '{ticker}' as processing in the database.")


def mark_company_as_indexed(ticker: str, stock_overview: dict | None):
    # ... (no changes here)
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.now()
    overview_json = json.dumps(stock_overview) if stock_overview else None
    cursor.execute(
        """
        UPDATE indexed_companies SET status = ?, indexed_at = ?, stock_overview_json = ? WHERE ticker = ?
    """,
        ("indexed", timestamp, overview_json, ticker),
    )
    conn.commit()
    conn.close()
    print(f"Marked ticker '{ticker}' as indexed in the database.")


def mark_company_as_failed(ticker: str):
    # NEW: Marks a company's ingestion as failed
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.now()
    cursor.execute(
        """
        UPDATE indexed_companies SET status = ?, indexed_at = ? WHERE ticker = ?
    """,
        ("failed", timestamp, ticker),
    )
    conn.commit()
    conn.close()
    print(f"Marked ticker '{ticker}' as failed in the database.")


def get_cached_stock_overview(ticker: str) -> dict | None:
    # ... (no changes here)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT stock_overview_json FROM indexed_companies WHERE ticker = ?", (ticker,)
    )
    result = cursor.fetchone()
    conn.close()
    if result and result["stock_overview_json"]:
        return json.loads(result["stock_overview_json"])
    return None


if __name__ == "__main__":
    initialize_database()
