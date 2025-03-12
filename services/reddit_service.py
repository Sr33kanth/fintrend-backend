import os
import praw
from datetime import datetime, timedelta
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class RedditService:
    """
    Service to fetch posts from Reddit subreddits
    """
    def __init__(self):
        # Get API credentials from environment variables
        client_id = os.getenv('REDDIT_CLIENT_ID')
        client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        user_agent = os.getenv('REDDIT_USER_AGENT', 'FinTrend/1.0')
        
        if not client_id or not client_secret:
            raise ValueError("Reddit API credentials not found. Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env file")
        
        # Initialize Reddit client
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        
        # Default subreddits to monitor
        self.default_subreddits = ['wallstreetbets']
    
    def _format_post(self, post, subreddit_name: str) -> dict:
        """
        Format a Reddit post into a consistent structure
        
        Args:
            post: Reddit post object
            subreddit_name: Name of the subreddit
            
        Returns:
            dict: Formatted post data
        """
        return {
            "headline": post.title,
            "summary": post.selftext[:200] + "..." if len(post.selftext) > 200 else post.selftext,
            "url": f"https://www.reddit.com{post.permalink}",
            "source": "reddit",
            "subreddit": subreddit_name,
            "datetime": datetime.fromtimestamp(post.created_utc).strftime("%Y-%m-%d %H:%M:%S"),
            "upvotes": post.score,
            "comments": post.num_comments,
            "platform": "reddit"
        }
    
    def _format_error(self, error_message: str, subreddit_name: str = "unknown") -> dict:
        """
        Format an error message into a consistent structure
        
        Args:
            error_message: Error message
            subreddit_name: Name of the subreddit
            
        Returns:
            dict: Formatted error data
        """
        return {
            "headline": f"Error fetching Reddit posts from r/{subreddit_name}",
            "summary": str(error_message),
            "url": "",
            "source": "reddit",
            "subreddit": subreddit_name,
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "platform": "error"
        }
    
    def get_posts_for_symbol(self, symbol: str, subreddits: List[str] = None, limit: int = 5) -> List[Dict]:
        """
        Get Reddit posts related to a stock symbol
        
        Args:
            symbol: Stock symbol to search for
            subreddits: List of subreddits to search in
            limit: Maximum number of posts to return
            
        Returns:
            List of posts related to the symbol
        """
        # Use default subreddits if none provided
        subreddit_list = subreddits if subreddits else self.default_subreddits
        
        results = []
        
        for subreddit_name in subreddit_list:
            try:
                # Get subreddit instance
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Search for posts containing the symbol
                for post in subreddit.search(symbol, limit=limit*2):
                    # Only include posts that explicitly mention the symbol
                    if symbol.lower() in post.title.lower() or f"${symbol.lower()}" in post.title.lower():
                        results.append(self._format_post(post, subreddit_name))
            except Exception as e:
                # Handle any errors in fetching from Reddit
                results.append(self._format_error(str(e), subreddit_name))
        
        # Sort by datetime (newest first) and limit results
        results.sort(key=lambda x: x.get("datetime", ""), reverse=True)
        return results[:limit]
    
    def get_trending_posts(self, subreddits: List[str] = None, limit: int = 10) -> List[Dict]:
        """
        Get trending posts from Reddit
        
        Args:
            subreddits: List of subreddits to fetch from
            limit: Maximum number of posts to return
            
        Returns:
            List of trending posts
        """
        # Use default subreddits if none provided
        subreddit_list = subreddits if subreddits else self.default_subreddits
        
        results = []
        
        for subreddit_name in subreddit_list:
            try:
                # Get subreddit instance
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Get hot posts
                for post in subreddit.hot(limit=limit):
                    results.append(self._format_post(post, subreddit_name))
            except Exception as e:
                results.append(self._format_error(str(e), subreddit_name))
        
        # Sort by datetime (newest first) and limit results
        results.sort(key=lambda x: x.get("datetime", ""), reverse=True)
        return results[:limit]
    
    def get_breakout_posts(self, subreddits: List[str] = None, limit: int = 20, 
                          target_flairs: List[str] = None, 
                          sentiment_phrases: List[str] = None) -> List[Dict]:
        """
        Get Reddit posts filtered by specific flairs and sentiment indicators
        
        Args:
            subreddits: List of subreddits to fetch from
            limit: Maximum number of posts to return
            target_flairs: List of flairs to filter for (e.g., "DD", "Discussion", "YOLO")
            sentiment_phrases: List of phrases indicating positive sentiment
            
        Returns:
            List of filtered Reddit posts
        """
        # Use default subreddits if none provided
        subreddit_list = subreddits if subreddits else self.default_subreddits
        
        # Default target flairs if none provided
        if target_flairs is None:
            target_flairs = ["DD", "Discussion", "YOLO", "Technical Analysis"]
            
        # Default sentiment phrases if none provided
        if sentiment_phrases is None:
            sentiment_phrases = [
                "to the moon", "going up", "bullish", "buy", "calls", 
                "rocket", "🚀", "gain", "breakout", "squeeze", "short squeeze"
            ]
            
        results = []
        
        for subreddit_name in subreddit_list:
            try:
                # Get subreddit instance
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Get hot and new posts with a higher limit to ensure we have enough after filtering
                posts = list(subreddit.hot(limit=limit*2))
                posts.extend(list(subreddit.new(limit=limit*2)))
                
                for post in posts:
                    # Check if post has one of the target flairs
                    has_target_flair = post.link_flair_text and any(
                        flair.lower() in post.link_flair_text.lower() for flair in target_flairs
                    )
                    
                    # Check if post contains sentiment phrases in title or body
                    has_sentiment =  any(
                        phrase.lower() in post.title.lower() or 
                        (post.selftext and phrase.lower() in post.selftext.lower())
                        for phrase in sentiment_phrases
                    )
                    
                    # Add post if it matches our criteria
                    if has_target_flair or has_sentiment:
                        formatted_post = self._format_post(post, subreddit_name)
                        # Add flair information
                        formatted_post["flair"] = post.link_flair_text
                        results.append(formatted_post)
                        
            except Exception as e:
                results.append(self._format_error(str(e), subreddit_name))
        
        # Remove duplicates (posts might appear in both hot and new)
        unique_results = []
        seen_urls = set()
        
        for post in results:
            if post["url"] not in seen_urls:
                seen_urls.add(post["url"])
                unique_results.append(post)
        
        # Sort by upvotes (highest first) and limit results
        unique_results.sort(key=lambda x: x.get("upvotes", 0), reverse=True)
        return unique_results[:limit] 