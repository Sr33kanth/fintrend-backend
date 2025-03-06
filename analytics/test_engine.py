import logging
from typing import Dict, List, Any
from collections import Counter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def analyze_data(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze collected financial data to identify trends and potential breakout stocks
    
    Args:
        data: List of collected data items
        
    Returns:
        Analysis results including trending tickers and potential breakouts
    """
    logger.info(f"Analyzing {len(data)} data items")
    
    # Extract all mentioned tickers
    all_tickers = []
    for item in data:
        if "tickers" in item and item["tickers"]:
            all_tickers.extend(item["tickers"])
    
    # Count ticker mentions
    ticker_counts = Counter(all_tickers)
    
    # Get sentiment data for each ticker
    ticker_sentiment = {}
    for ticker in set(all_tickers):
        positive = sum(1 for item in data if ticker in item.get("tickers", []) and item.get("sentiment") == "positive")
        neutral = sum(1 for item in data if ticker in item.get("tickers", []) and item.get("sentiment") == "neutral")
        negative = sum(1 for item in data if ticker in item.get("tickers", []) and item.get("sentiment") == "negative")
        
        ticker_sentiment[ticker] = {
            "positive": positive,
            "neutral": neutral,
            "negative": negative,
            "total": positive + neutral + negative,
            "score": (positive - negative) / (positive + neutral + negative) if (positive + neutral + negative) > 0 else 0
        }
    
    # Identify trending tickers (most mentioned)
    trending_tickers = [ticker for ticker, count in ticker_counts.most_common(5)]
    
    # Identify potential breakout stocks based on positive sentiment and mention count
    potential_breakouts = []
    for ticker, sentiment in ticker_sentiment.items():
        # Simple criteria: high mention count and positive sentiment score
        if ticker_counts[ticker] >= 2 and sentiment["score"] > 0.5:
            # Find sources that mentioned this ticker
            sources = set()
            for item in data:
                if ticker in item.get("tickers", []):
                    sources.add(item["source"])
            
            # Find a good reason for the breakout
            reason = "Strong positive sentiment"
            for item in data:
                if ticker in item.get("tickers", []) and item.get("sentiment") == "positive":
                    # Use the title as the reason
                    reason = f"Strong positive sentiment and {item['title']}"
                    break
            
            potential_breakouts.append({
                "ticker": ticker,
                "mentions": ticker_counts[ticker],
                "sentiment_score": sentiment["score"],
                "sources": len(sources),
                "reason": reason
            })
    
    # Sort by sentiment score and mention count
    potential_breakouts.sort(key=lambda x: (x["sentiment_score"], x["mentions"]), reverse=True)
    
    analysis_results = {
        "trending_tickers": trending_tickers,
        "ticker_counts": {ticker: count for ticker, count in ticker_counts.most_common()},
        "sentiment_summary": {
            ticker: sentiment for ticker, sentiment in ticker_sentiment.items()
        },
        "potential_breakouts": potential_breakouts
    }
    
    logger.info(f"Analysis complete. Found {len(potential_breakouts)} potential breakout stocks")
    return analysis_results