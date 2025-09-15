# src/ingestion/stock_data_fetcher.py

import os
from alpha_vantage.fundamentaldata import FundamentalData
from alpha_vantage.timeseries import TimeSeries
from dotenv import load_dotenv

load_dotenv()


def get_company_overview(symbol: str) -> dict:
    try:
        alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        if not alpha_vantage_key:
            raise ValueError("Alpha Vantage API key not found.")

        fd = FundamentalData(key=alpha_vantage_key, output_format="json")
        overview, _ = fd.get_company_overview(symbol=symbol)
        return overview
    except Exception as e:
        print(f"An error occurred fetching company overview for {symbol}: {e}")
        return {}


def get_daily_stock_prices(symbol: str) -> dict:
    try:
        alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        if not alpha_vantage_key:
            raise ValueError("Alpha Vantage API key not found.")

        ts = TimeSeries(key=alpha_vantage_key, output_format="json")
        data, _ = ts.get_daily_adjusted(symbol=symbol, outputsize="compact")
        return data
    except Exception as e:
        print(f"An error occurred fetching stock prices for {symbol}: {e}")
        return {}
