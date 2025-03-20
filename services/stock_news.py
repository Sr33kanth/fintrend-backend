import os
from datetime import datetime, timedelta
from typing import List, Dict
import finnhub
from dotenv import load_dotenv
from services.reddit_service import RedditService
from services.alpha_vantage_service import AlphaVantageService

# Load environment variables
load_dotenv()

class StockNewsService:
    """
    Service to fetch stock news from Finnhub API, Alpha Vantage, and Reddit
    """
    def __init__(self):
        # Get API key from environment variable
        api_key = os.getenv('FINNHUB_API_KEY')
        
        if not api_key:
            raise ValueError("Finnhub API key not found. Please set FINNHUB_API_KEY in .env file")
        
        # Initialize clients
        self.finnhub_client = finnhub.Client(api_key=api_key)
        self.reddit_service = RedditService()
        self.alpha_vantage_service = AlphaVantageService()
    
    def get_stocks_news(self, stocks: List[str], limit: int = 5, include_reddit: bool = True, source: str = None) -> Dict:
        """
        Fetch news for multiple stock symbols
        
        Args:
            stocks (List[str]): List of stock symbols
            limit (int, optional): Number of news articles per stock. Defaults to 5.
            include_reddit (bool, optional): Whether to include Reddit posts. Defaults to True.
            source (str, optional): Filter news by source. Defaults to None.
        
        Returns:
            Dict: News articles for each stock
        """
        # Get date range for news (last 30 days)
        now = datetime.now()
        from_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")
        to_date = now.strftime("%Y-%m-%d")
        
        news_results = {}
        
        # Normalize source parameter
        source_lower = source.lower() if source else None
        is_reddit_source = source_lower == "reddit" if source_lower else False
        is_alpha_vantage_source = source_lower == "alpha_vantage" if source_lower else False
        
        for symbol in stocks:
            try:
                formatted_news = []
                
                # Fetch news from different sources based on filter
                if not is_reddit_source and not is_alpha_vantage_source:
                    # Fetch company news from Finnhub
                    stock_news = self.finnhub_client.company_news(symbol, _from=from_date, to=to_date)
                    
                    # Format Finnhub news
                    formatted_news.extend([
                        {
                            "headline": article.get("headline", "No Headline"),
                            "summary": article.get("summary", "No Summary"),
                            "url": article.get("url", ""),
                            "source": article.get("source", "Unknown"),
                            "datetime": datetime.fromtimestamp(article.get("datetime", 0)).strftime("%Y-%m-%d %H:%M:%S"),
                            "platform": "finnhub"
                        } 
                        for article in stock_news[:limit]
                    ])
                
                if not is_reddit_source and (not source or is_alpha_vantage_source):
                    try:
                        # Fetch news from Alpha Vantage
                        alpha_vantage_news = self.alpha_vantage_service.get_stock_news(symbol, limit=limit)
                        formatted_news.extend(alpha_vantage_news)
                    except Exception as e:
                        print(f"Error fetching Alpha Vantage news: {e}")
                
                # Add Reddit posts if enabled or specifically requested
                if include_reddit or is_reddit_source:
                    try:
                        reddit_posts = self.reddit_service.get_posts_for_symbol(symbol, limit=limit)
                        formatted_news.extend(reddit_posts)
                    except Exception as e:
                        print(f"Error fetching Reddit posts: {e}")
                
                # Filter by source if specified
                if source and not is_reddit_source:
                    formatted_news = [
                        article for article in formatted_news 
                        if article["platform"].lower() == source_lower
                    ]
                
                # Sort by datetime (newest first)
                formatted_news.sort(key=lambda x: x.get("datetime", ""), reverse=True)
                
                news_results[symbol] = formatted_news[:limit]
            
            except Exception as e:
                # Handle any errors in fetching news
                news_results[symbol] = [
                    {
                        "headline": f"Error fetching news for {symbol}",
                        "summary": str(e),
                        "url": "",
                        "source": "Error",
                        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "platform": "error"
                    }
                ]
        
        return news_results
    
    def get_trending_reddit_posts(self, subreddits: List[str] = None, limit: int = 10) -> List[Dict]:
        """
        Fetch trending posts from Reddit
        
        Args:
            subreddits (List[str], optional): List of subreddits to fetch from. Defaults to None.
            limit (int, optional): Maximum number of posts to return. Defaults to 10.
        
        Returns:
            List[Dict]: List of trending Reddit posts
        """
        return self.reddit_service.get_trending_posts(subreddits=subreddits, limit=limit)
        
    def get_breakout_posts(self, subreddits: List[str] = None, limit: int = 20, 
                          target_flairs: List[str] = None, 
                          sentiment_phrases: List[str] = None) -> List[Dict]:
        """
        Get Reddit posts filtered by specific flairs and sentiment indicators
        
        Args:
            subreddits (List[str], optional): List of subreddits to fetch from. Defaults to None.
            limit (int, optional): Maximum number of posts to return. Defaults to 20.
            target_flairs (List[str], optional): List of flairs to filter for. Defaults to None.
            sentiment_phrases (List[str], optional): List of phrases indicating positive sentiment. Defaults to None.
            
        Returns:
            List[Dict]: List of filtered Reddit posts
        """
        return self.reddit_service.get_breakout_posts(
            subreddits=subreddits, 
            limit=limit,
            target_flairs=target_flairs,
            sentiment_phrases=sentiment_phrases
        )