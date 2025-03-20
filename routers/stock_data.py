from fastapi import APIRouter, HTTPException
from typing import List, Dict
from services.alpha_vantage_service import AlphaVantageService

router = APIRouter()
alpha_vantage_service = AlphaVantageService()

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