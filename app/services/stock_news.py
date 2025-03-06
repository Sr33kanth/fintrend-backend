import os
from datetime import datetime, timedelta
from typing import List, Dict
import finnhub
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class StockNewsService:
    """
    Service to fetch stock news from Finnhub API using Finnhub Python client
    """
    def __init__(self):
        # Get API key from environment variable
        api_key = os.getenv('FINNHUB_API_KEY')
        
        if not api_key:
            raise ValueError("Finnhub API key not found. Please set FINNHUB_API_KEY in .env file")
        
        # Initialize Finnhub client
        self.finnhub_client = finnhub.Client(api_key=api_key)
    
    def get_stocks_news(self, stocks: List[str], limit: int = 5) -> Dict:
        """
        Fetch news for multiple stock symbols
        
        Args:
            stocks (List[str]): List of stock symbols
            limit (int, optional): Number of news articles per stock. Defaults to 5.
        
        Returns:
            Dict: News articles for each stock
        """
        # Get date range for news (last 30 days)
        now = datetime.now()
        from_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")
        to_date = now.strftime("%Y-%m-%d")
        
        news_results = {}
        
        for symbol in stocks:
            try:
                # Fetch company news
                stock_news = self.finnhub_client.company_news(symbol, _from=from_date, to=to_date)
                
                # Limit and format news
                formatted_news = [
                    {
                        "headline": article.get("headline", "No Headline"),
                        "summary": article.get("summary", "No Summary"),
                        "url": article.get("url", ""),
                        "source": article.get("source", "Unknown"),
                        "datetime": datetime.fromtimestamp(article.get("datetime", 0)).strftime("%Y-%m-%d %H:%M:%S")
                    } 
                    for article in stock_news[:limit]
                ]
                
                news_results[symbol] = formatted_news
            
            except Exception as e:
                # Handle any errors in fetching news
                news_results[symbol] = [
                    {
                        "headline": f"Error fetching news for {symbol}",
                        "summary": str(e),
                        "url": "",
                        "source": "Error",
                        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                ]
        
        return news_results