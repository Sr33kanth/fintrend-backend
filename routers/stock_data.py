from fastapi import APIRouter, HTTPException
from typing import List, Dict
from services.alpha_vantage_service import AlphaVantageService
from services.watchlist import WatchlistService

router = APIRouter()
alpha_vantage_service = AlphaVantageService()
watchlist_service = WatchlistService()

@router.get("/stock/{symbol}/price")
async def get_stock_price(symbol: str) -> Dict:
    """
    Get current stock price and daily data
    
    Args:
        symbol (str): Stock symbol
        
    Returns:
        Dict: Current price and daily data
    """
    try:
        return alpha_vantage_service.get_stock_price(symbol)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stocks/prices")
async def get_stocks_prices(symbols: List[str]) -> Dict[str, Dict]:
    """
    Get current prices for multiple stocks
    
    Args:
        symbols (List[str]): List of stock symbols
        
    Returns:
        Dict[str, Dict]: Current prices for each stock
    """
    try:
        return {
            symbol: alpha_vantage_service.get_stock_price(symbol)
            for symbol in symbols
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stock/{symbol}/historical")
async def get_stock_historical_data(symbol: str, period: str = "1m") -> Dict:
    """
    Get historical stock data for graphing
    
    Args:
        symbol (str): Stock symbol
        period (str): Time period (1d, 5d, 1m, 3m, 6m, 1y, etc.)
        
    Returns:
        Dict: Historical price data formatted for graphing
    """
    try:
        return alpha_vantage_service.get_historical_data(symbol, period)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/watchlist/historical")
async def get_watchlist_historical_data(period: str = "1m") -> Dict[str, Dict]:
    """
    Get historical data for all stocks in watchlist
    
    Args:
        period (str): Time period (1d, 5d, 1m, 3m, 6m, 1y, etc.)
        
    Returns:
        Dict[str, Dict]: Historical data for each stock in watchlist
    """
    try:
        stocks = watchlist_service.get_stocks()
        return {
            symbol: alpha_vantage_service.get_historical_data(symbol, period)
            for symbol in stocks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 