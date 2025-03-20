import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict
from alpha_vantage.timeseries import TimeSeries
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AlphaVantageService:
    """
    Service to fetch stock data and news from Alpha Vantage API
    """
    def __init__(self):
        # Get API key from environment variable
        self.api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        
        if not self.api_key:
            raise ValueError("Alpha Vantage API key not found. Please set ALPHA_VANTAGE_API_KEY in .env file")
        
        # Initialize Alpha Vantage client
        self.time_series = TimeSeries(key=self.api_key)
        self.base_url = "https://www.alphavantage.co/query"
    
    def get_stock_price(self, symbol: str) -> Dict:
        """
        Get current stock price and daily data
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            Dict: Current price and daily data
        """
        try:
            # Get daily data
            data, meta_data = self.time_series.get_daily(symbol=symbol, outputsize='compact')
            
            # Get the most recent data point
            latest_date = max(data.keys())
            latest_data = data[latest_date]
            
            return {
                "symbol": symbol,
                "price": float(latest_data['4. close']),
                "open": float(latest_data['1. open']),
                "high": float(latest_data['2. high']),
                "low": float(latest_data['3. low']),
                "volume": int(latest_data['5. volume']),
                "date": latest_date,
                "daily_data": data
            }
        except Exception as e:
            raise Exception(f"Error fetching stock price for {symbol}: {str(e)}")
    
    def get_stock_news(self, symbol: str, limit: int = 5) -> List[Dict]:
        """
        Get news articles for a stock using Alpha Vantage News API
        
        Args:
            symbol (str): Stock symbol
            limit (int): Maximum number of news articles to return
            
        Returns:
            List[Dict]: List of news articles
        """
        try:
            # Make request to Alpha Vantage News Sentiment API
            params = {
                "function": "NEWS_SENTIMENT",
                "tickers": symbol,
                "apikey": self.api_key,
                "limit": limit
            }
            
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()  # Raise an error for bad status codes
            data = response.json()
            
            # Format news articles
            formatted_news = []
            for article in data.get('feed', [])[:limit]:
                formatted_news.append({
                    "headline": article.get('title', 'No Headline'),
                    "summary": article.get('summary', 'No Summary'),
                    "url": article.get('url', ''),
                    "source": article.get('source', 'Unknown'),
                    "datetime": article.get('time_published', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                    "platform": "alpha_vantage"
                })
            
            return formatted_news
        except Exception as e:
            raise Exception(f"Error fetching news for {symbol}: {str(e)}") 