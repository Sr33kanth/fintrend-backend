from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import uvicorn

# Import our custom modules (we'll create these next)
from services.watchlist import WatchlistService
from services.stock_news import StockNewsService

# Create FastAPI app instance
app = FastAPI(
    title="Finance Trend App",
    description="A modern stock watchlist and news tracking application",
    version="0.1.0"
)

# Add CORS middleware to allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://localhost:3000"],  # Explicitly allow frontend origin
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicitly list allowed methods
    allow_headers=["*"],  # Allows all headers
)

# Pydantic model for adding a stock to watchlist
class StockSymbol(BaseModel):
    symbol: str

# Dependency injection for services
watchlist_service = WatchlistService()
stock_news_service = StockNewsService()

# Routes for watchlist management
@app.post("/watchlist/add", response_model=List[str])
async def add_to_watchlist(stock: StockSymbol):
    """
    Add a stock symbol to the watchlist
    
    Args:
        stock (StockSymbol): Stock symbol to add
    
    Returns:
        List of current watchlist stocks
    """
    try:
        return watchlist_service.add_stock(stock.symbol)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/watchlist", response_model=List[str])
async def get_watchlist():
    """
    Retrieve current watchlist
    
    Returns:
        List of stocks in watchlist
    """
    return watchlist_service.get_stocks()

@app.delete("/watchlist/remove", response_model=List[str])
async def remove_from_watchlist(stock: StockSymbol):
    """
    Remove a stock symbol from the watchlist
    
    Args:
        stock (StockSymbol): Stock symbol to remove
    
    Returns:
        Updated list of stocks in watchlist
    """
    try:
        return watchlist_service.remove_stock(stock.symbol)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Routes for stock news
@app.get("/news")
def get_watchlist_news(include_reddit: bool = True, source: str = None):
    """
    Fetch news for all stocks in the watchlist
    
    Args:
        include_reddit (bool, optional): Whether to include Reddit posts. Defaults to True.
        source (str, optional): Filter news by source. Defaults to None.
    
    Returns:
        List of news articles for watchlist stocks
    """
    watchlist = watchlist_service.get_stocks()
    return stock_news_service.get_stocks_news(watchlist, include_reddit=include_reddit, source=source)

@app.get("/reddit/trending")
def get_trending_reddit_posts(subreddits: str = None, limit: int = 10):
    """
    Fetch trending posts from Reddit
    
    Args:
        subreddits (str, optional): Comma-separated list of subreddits. Defaults to None.
        limit (int, optional): Maximum number of posts to return. Defaults to 10.
    
    Returns:
        List of trending Reddit posts
    """
    subreddit_list = subreddits.split(",") if subreddits else None
    return stock_news_service.get_trending_reddit_posts(subreddits=subreddit_list, limit=limit)

@app.get("/reddit/breakouts")
def get_breakout_reddit_posts(
    subreddits: str = None, 
    limit: int = 20, 
    flairs: str = None, 
    sentiment: str = None
):
    """
    Fetch Reddit posts filtered by specific flairs and sentiment indicators
    
    Args:
        subreddits (str, optional): Comma-separated list of subreddits. Defaults to None.
        limit (int, optional): Maximum number of posts to return. Defaults to 20.
        flairs (str, optional): Comma-separated list of flairs to filter for. Defaults to None.
        sentiment (str, optional): Comma-separated list of sentiment phrases. Defaults to None.
    
    Returns:
        List of filtered Reddit posts
    """
    subreddit_list = subreddits.split(",") if subreddits else None
    flair_list = flairs.split(",") if flairs else None
    sentiment_list = sentiment.split(",") if sentiment else None
    
    return stock_news_service.get_breakout_posts(
        subreddits=subreddit_list, 
        limit=limit,
        target_flairs=flair_list,
        sentiment_phrases=sentiment_list
    )

# For local development and testing
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)