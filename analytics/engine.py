# app/analytics/engine.py
import os
import pandas as pd
import yfinance as yf
import praw
import requests
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Tuple, Optional
import json
import time

from app.db.models import (
    StockAnalysis, 
    StockNews, 
    StockRedditPost, 
    BreakoutRecommendation,
    Watchlist
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("stock_analyzer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LLMAgent:
    """Class to interact with LLM services like ChatGPT/OpenAI"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")  # Default to GPT-4o if not specified
        
    def analyze_news_sentiment(self, articles: List[Dict]) -> Dict:
        """Analyze news sentiment using LLM"""
        if not articles:
            return {"overall_sentiment": 0, "analysis": "No news articles found"}
            
        # Prepare articles for LLM input (limit to 10 most recent to avoid token limits)
        recent_articles = articles[:10]
        article_texts = [f"Title: {a.get('title', '')}\nSource: {a.get('source', '')}\nSummary: {a.get('description', '')}" 
                         for a in recent_articles]
        
        prompt = f"""
        Analyze the sentiment of these news articles about a stock. Rate the overall sentiment on a scale from -1 (very negative) to 1 (very positive).
        For each article, provide a brief sentiment analysis.
        
        Articles:
        {article_texts}
        
        Return your analysis in this JSON format:
        {{
            "overall_sentiment": [number between -1 and 1],
            "key_themes": [list of key themes or topics mentioned],
            "article_sentiments": [list of individual article sentiments with brief explanations],
            "analysis_summary": [brief overall analysis]
        }}
        """
        
        return self._call_llm_api(prompt, json_output=True)
        
    def analyze_reddit_sentiment(self, posts: List[Dict]) -> Dict:
        """Analyze Reddit sentiment using LLM"""
        if not posts:
            return {"overall_sentiment": 0, "analysis": "No Reddit posts found"}
            
        # Prepare posts for LLM input (limit to avoid token limits)
        recent_posts = posts[:10]
        post_texts = [f"Title: {p.get('title', '')}\nSubreddit: {p.get('subreddit', '')}\nScore: {p.get('score', '')}\nUpvote Ratio: {p.get('upvote_ratio', '')}" 
                    for p in recent_posts]
        
        prompt = f"""
        Analyze the sentiment in these Reddit posts about a stock. Rate the overall sentiment on a scale from -1 (very negative) to 1 (very positive).
        Consider the popularity of posts (score and upvote ratio) in your analysis.
        
        Reddit Posts:
        {post_texts}
        
        Return your analysis in this JSON format:
        {{
            "overall_sentiment": [number between -1 and 1],
            "key_themes": [list of key themes or topics mentioned],
            "post_sentiments": [list of individual post sentiments with brief explanations],
            "retail_investor_outlook": [assessment of how retail investors view this stock],
            "analysis_summary": [brief overall analysis]
        }}
        """
        
        return self._call_llm_api(prompt, json_output=True)
    
    def generate_stock_summary(self, ticker: str, news_analysis: Dict, reddit_analysis: Dict, stock_data: Dict) -> Dict:
        """Generate comprehensive stock summary using LLM"""
        # Extract relevant financial data
        financials = {
            "current_price": stock_data.get("regularMarketPrice", "N/A"),
            "previous_close": stock_data.get("previousClose", "N/A"),
            "fifty_day_avg": stock_data.get("fiftyDayAverage", "N/A"),
            "market_cap": stock_data.get("marketCap", "N/A"),
            "pe_ratio": stock_data.get("trailingPE", "N/A"),
            "sector": stock_data.get("sector", "N/A"),
            "industry": stock_data.get("industry", "N/A"),
            "short_ratio": stock_data.get("shortRatio", "N/A")
        }
        
        prompt = f"""
        Create a comprehensive analysis for {ticker} stock based on recent news, Reddit sentiment, and financial data.
        
        News Analysis:
        {json.dumps(news_analysis, indent=2)}
        
        Reddit Analysis:
        {json.dumps(reddit_analysis, indent=2)}
        
        Financial Data:
        {json.dumps(financials, indent=2)}
        
        Return your analysis in this JSON format:
        {{
            "overall_sentiment_score": [number between -1 and 1],
            "summary": [concise 2-3 sentence summary],
            "detailed_analysis": [paragraph with more detailed analysis],
            "key_drivers": [list of key factors driving stock sentiment],
            "risks": [list of potential risks],
            "opportunities": [list of potential opportunities],
            "is_breakout_candidate": [boolean - true if this looks like a potential breakout stock],
            "breakout_reasoning": [explanation for breakout assessment],
            "recommendation": [one of: "Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"],
            "confidence_score": [number between 0 and 1 indicating confidence in this analysis]
        }}
        """
        
        return self._call_llm_api(prompt, json_output=True)
    
    def identify_breakout_stocks(self, trending_tickers: List[str], market_data: Dict, recent_analyses: Dict) -> Dict:
        """Identify potential breakout stocks from trending tickers"""
        prompt = f"""
        Analyze these trending stock tickers and identify which ones are most likely to be breakout candidates.
        
        Trending Tickers: {trending_tickers}
        
        Market Data:
        {json.dumps(market_data, indent=2)}
        
        Recent Stock Analyses:
        {json.dumps(recent_analyses, indent=2)}
        
        For each potential breakout stock, explain why it might break out and assign a confidence score (0-1).
        
        Return your analysis in this JSON format:
        {{
            "breakout_candidates": [
                {{
                    "ticker": "XYZ",
                    "value_proposition": [1-2 sentences on why this stock might break out],
                    "confidence_score": [number between 0 and 1],
                    "key_catalysts": [list of key catalysts that could drive price movement]
                }}
            ],
            "market_assessment": [brief assessment of current market conditions and how they affect these stocks],
            "sectors_to_watch": [list of sectors showing momentum]
        }}
        """
        
        return self._call_llm_api(prompt, json_output=True)
    
    def _call_llm_api(self, prompt: str, json_output: bool = False, max_retries: int = 3) -> Dict:
        """Call the LLM API with retry logic"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,  # Low temperature for more deterministic outputs
        }
        
        if json_output:
            payload["response_format"] = {"type": "json_object"}
        
        retry_count = 0
        while retry_count < max_retries:
            try:
                response = requests.post(self.api_url, headers=headers, json=payload)
                response.raise_for_status()
                
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                if json_output:
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse JSON response: {content}")
                        return {"error": "Failed to parse response", "raw_content": content}
                else:
                    return {"content": content}
                
            except requests.exceptions.RequestException as e:
                retry_count += 1
                logger.warning(f"API call failed (attempt {retry_count}/{max_retries}): {str(e)}")
                if retry_count < max_retries:
                    time.sleep(2)  # Wait before retrying
                else:
                    logger.error(f"API call failed after {max_retries} attempts")
                    return {"error": str(e)}


class StockAnalyzer:
    def __init__(self, db: Session):
        self.db = db
        
        # Reddit API setup
        self.reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT', 'Mozilla/5.0')
        )
        
        # News API setup
        self.news_api_key = os.getenv('NEWS_API_KEY')
        
        # Initialize LLM Agent
        self.llm_agent = LLMAgent()
        
        # Subreddits to monitor
        self.finance_subreddits = [
            'wallstreetbets', 'investing', 'stocks', 'stockmarket',
            'options', 'pennystocks', 'SecurityAnalysis'
        ]
        
    def analyze_watchlist_stocks(self) -> None:
        """Analyze all stocks in users' watchlists"""
        # Get unique tickers from all watchlists
        tickers = self.db.query(Watchlist.ticker).distinct().all()
        tickers = [ticker[0] for ticker in tickers]
        
        for ticker in tickers:
            try:
                self.analyze_stock(ticker)
            except Exception as e:
                logger.error(f"Error analyzing {ticker}: {str(e)}")
    
    def find_breakout_stocks(self) -> None:
        """Find potential breakout stocks and create recommendations"""
        try:
            # Get trending stocks from Reddit and other sources
            trending_tickers = self._get_trending_tickers()
            
            if not trending_tickers:
                logger.warning("No trending tickers found")
                return
            
            # Get market data for context
            market_indices = ['SPY', 'QQQ', 'IWM']  # S&P 500, Nasdaq, Russell 2000
            market_data = {}
            
            for index in market_indices:
                try:
                    index_data = yf.Ticker(index).history(period="5d")
                    market_data[index] = {
                        "5d_change": ((index_data['Close'].iloc[-1] / index_data['Close'].iloc[0]) - 1) * 100,
                        "current_price": index_data['Close'].iloc[-1]
                    }
                except Exception as e:
                    logger.error(f"Error fetching data for {index}: {str(e)}")
            
            # Get recent analyses for trending tickers
            recent_analyses = {}
            for ticker in trending_tickers[:20]:  # Limit to 20 tickers
                analysis = self.db.query(StockAnalysis).filter(
                    StockAnalysis.ticker == ticker
                ).order_by(StockAnalysis.analysis_date.desc()).first()
                
                if analysis:
                    recent_analyses[ticker] = {
                        "sentiment_score": analysis.sentiment_score,
                        "mention_count": analysis.mention_count,
                        "summary": analysis.summary
                    }
            
            # Use LLM to identify breakout candidates
            breakout_results = self.llm_agent.identify_breakout_stocks(
                trending_tickers, market_data, recent_analyses
            )
            
            # Save breakout recommendations
            today = datetime.now().date()
            for candidate in breakout_results.get("breakout_candidates", []):
                ticker = candidate.get("ticker")
                
                # Skip if no ticker or invalid confidence score
                if not ticker or not isinstance(candidate.get("confidence_score"), (int, float)):
                    continue
                
                # Check if we already have a recommendation for this ticker today
                existing = self.db.query(BreakoutRecommendation).filter(
                    BreakoutRecommendation.ticker == ticker,
                    BreakoutRecommendation.recommendation_date == today
                ).first()
                
                if existing:
                    continue
                
                try:
                    # Get current price
                    stock = yf.Ticker(ticker)
                    price = stock.info.get("regularMarketPrice", 0)
                    
                    # Create recommendation
                    recommendation = BreakoutRecommendation(
                        ticker=ticker,
                        recommendation_date=today,
                        value_proposition=candidate.get("value_proposition", ""),
                        confidence_score=candidate.get("confidence_score", 0.5),
                        price_at_recommendation=price
                    )
                    
                    self.db.add(recommendation)
                    self.db.commit()
                    logger.info(f"Created breakout recommendation for {ticker}")
                except Exception as e:
                    self.db.rollback()
                    logger.error(f"Error creating recommendation for {ticker}: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error finding breakout stocks: {str(e)}")
    
    def analyze_stock(self, ticker: str) -> Optional[StockAnalysis]:
        """
        Analyze a stock by gathering data from various sources and using LLM for analysis
        
        Args:
            ticker: The stock ticker symbol
            
        Returns:
            The StockAnalysis object if successful, None otherwise
        """
        logger.info(f"Analyzing stock: {ticker}")
        
        try:
            today = datetime.now().date()
            
            # Check if we already analyzed this stock today
            existing = self.db.query(StockAnalysis).filter(
                StockAnalysis.ticker == ticker,
                StockAnalysis.analysis_date == today
            ).first()
            
            if existing:
                logger.info(f"Already analyzed {ticker} today. Skipping.")
                return existing
            
            # Fetch news articles
            news_articles = self._fetch_stock_news(ticker)
            
            # Fetch Reddit posts
            reddit_posts = self._fetch_reddit_posts(ticker)
            
            # Fetch stock data
            stock_data = self._fetch_stock_data(ticker)
            
            if not stock_data:
                logger.error(f"Could not fetch stock data for {ticker}")
                return None
            
            # Use LLM to analyze sentiment in news and Reddit data
            news_analysis = self.llm_agent.analyze_news_sentiment(news_articles)
            reddit_analysis = self.llm_agent.analyze_reddit_sentiment(reddit_posts)
            
            # Generate comprehensive stock analysis using LLM
            stock_summary = self.llm_agent.generate_stock_summary(ticker, news_analysis, reddit_analysis, stock_data)
            
            # Extract key metrics
            overall_sentiment = stock_summary.get("overall_sentiment_score", 0)
            mention_count = len(news_articles) + len(reddit_posts)
            is_breakout = stock_summary.get("is_breakout_candidate", False)
            summary = stock_summary.get("summary", "")
            detailed_analysis = stock_summary.get("detailed_analysis", "")
            
            # Create stock analysis record
            analysis = StockAnalysis(
                ticker=ticker,
                analysis_date=today,
                sentiment_score=overall_sentiment,
                reddit_sentiment=reddit_analysis.get("overall_sentiment", 0),
                news_sentiment=news_analysis.get("overall_sentiment", 0),
                mention_count=mention_count,
                is_breakout=is_breakout,
                summary=f"{summary}\n\n{detailed_analysis}"
            )
            
            self.db.add(analysis)
            self.db.commit()
            self.db.refresh(analysis)
            
            # Save news articles
            for article in news_articles:
                # Find sentiment in article_sentiments if available
                article_sentiment = 0
                for sent_item in news_analysis.get("article_sentiments", []):
                    if article.get('title') in str(sent_item):
                        # Extract sentiment value if found in the text
                        try:
                            sentiment_txt = str(sent_item).split(":")[-1].strip()
                            article_sentiment = float(sentiment_txt) if sentiment_txt and sentiment_txt[0].isdigit() else 0
                        except (ValueError, IndexError):
                            pass
                
                news = StockNews(
                    ticker=ticker,
                    title=article.get('title', ''),
                    url=article.get('url', ''),
                    source=article.get('source', {}).get('name', ''),
                    published_at=article.get('publishedAt'),
                    sentiment_score=article_sentiment,
                    analysis_id=analysis.id
                )
                self.db.add(news)
            
            # Save Reddit posts
            for post in reddit_posts:
                # Find sentiment in post_sentiments if available
                post_sentiment = 0
                for sent_item in reddit_analysis.get("post_sentiments", []):
                    if post.get('title') in str(sent_item):
                        try:
                            sentiment_txt = str(sent_item).split(":")[-1].strip()
                            post_sentiment = float(sentiment_txt) if sentiment_txt and sentiment_txt[0].isdigit() else 0
                        except (ValueError, IndexError):
                            pass
                
                reddit_post = StockRedditPost(
                    ticker=ticker,
                    title=post.get('title', ''),
                    url=post.get('url', ''),
                    subreddit=post.get('subreddit', ''),
                    posted_at=datetime.fromtimestamp(post.get('created_utc', 0)),
                    sentiment_score=post_sentiment,
                    upvote_ratio=post.get('upvote_ratio', 0),
                    analysis_id=analysis.id
                )
                self.db.add(reddit_post)
            
            self.db.commit()
            logger.info(f"Analysis completed for {ticker}")
            
            return analysis
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error analyzing {ticker}: {str(e)}")
            return None
    
    def _fetch_stock_news(self, ticker: str) -> List[Dict[str, Any]]:
        """Fetch news articles for a stock"""
        articles = []
        
        try:
            # Use News API to get articles
            url = f"https://newsapi.org/v2/everything"
            params = {
                "q": f"({ticker} OR ${ticker}) AND (stock OR stocks OR investing OR shares)",
                "apiKey": self.news_api_key,
                "language": "en",
                "sortBy": "publishedAt",
                "from": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get("articles", [])
                logger.info(f"Found {len(articles)} news articles for {ticker}")
            else:
                logger.error(f"Error fetching news for {ticker}: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error fetching news for {ticker}: {str(e)}")
            
        return articles
    
    def _fetch_reddit_posts(self, ticker: str) -> List[Dict[str, Any]]:
        """Fetch Reddit posts mentioning a stock"""
        posts = []
        
        try:
            # Search across multiple subreddits
            for subreddit_name in self.finance_subreddits:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Search for both ticker and $ticker
                search_queries = [ticker, f"${ticker}"]
                
                for query in search_queries:
                    try:
                        search_results = subreddit.search(query, time_filter="week", limit=20)
                        
                        for post in search_results:
                            # Only include posts that explicitly mention the ticker
                            if ticker.lower() in post.title.lower() or f"${ticker.lower()}" in post.title.lower():
                                posts.append({
                                    "title": post.title,
                                    "url": f"https://www.reddit.com{post.permalink}",
                                    "score": post.score,
                                    "upvote_ratio": post.upvote_ratio,
                                    "num_comments": post.num_comments,
                                    "created_utc": post.created_utc,
                                    "subreddit": subreddit_name
                                })
                    except Exception as e:
                        logger.error(f"Error searching {subreddit_name} for {query}: {str(e)}")
            
            logger.info(f"Found {len(posts)} Reddit posts for {ticker}")
            
        except Exception as e:
            logger.error(f"Error fetching Reddit posts for {ticker}: {str(e)}")
            
        return posts
    
    def _fetch_stock_data(self, ticker: str) -> Dict[str, Any]:
        """Fetch stock data from Yahoo Finance"""
        try:
            stock = yf.Ticker(ticker)
            return stock.info
        except Exception as e:
            logger.error(f"Error fetching stock data for {ticker}: {str(e)}")
            return {}
    
    def _get_trending_tickers(self) -> List[str]:
        """Get trending stock tickers from various sources"""
        trending_tickers = set()
        
        # Get tickers from Reddit
        try:
            for subreddit_name in self.finance_subreddits:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                for post in subreddit.hot(limit=50):
                    # Simple ticker extraction - look for patterns like $AAPL or TSLA
                    # This is a simple approach - a more robust system would use a better extraction method
                    title = post.title
                    
                    # Find $TICKER patterns
                    dollar_tickers = [match[1:].upper() for match in re.findall(r'\$[A-Za-z]{1,5}', title)]
                    
                    # Find standalone uppercase words that look like tickers (3-5 chars)
                    word_tickers = [word.upper() for word in re.findall(r'\b[A-Z]{3,5}\b', title)]
                    
                    # Add found tickers to our set
                    trending_tickers.update(dollar_tickers)
                    trending_tickers.update(word_tickers)
        except Exception as e:
            logger.error(f"Error getting trending tickers from Reddit: {str(e)}")
        
        # Filter out common non-ticker uppercase words and known ETFs
        common_words = {"THE", "AND", "FOR", "THIS", "THAT", "WITH", "FROM", "WHAT", "HAVE"}
        known_etfs = {"SPY", "QQQ", "IWM", "DIA", "VTI"}
        
        filtered_tickers = [ticker for ticker in trending_tickers 
                            if ticker not in common_words and ticker not in known_etfs]
        
        # Verify tickers are valid by checking with Yahoo Finance (first 50 to avoid rate limits)
        validated_tickers = []
        for ticker in list(filtered_tickers)[:50]:
            try:
                stock = yf.Ticker(ticker)
                if 'regularMarketPrice' in stock.info:
                    validated_tickers.append(ticker)
            except:
                pass
        
        logger.info(f"Found {len(validated_tickers)} trending tickers")
        return validated_tickers