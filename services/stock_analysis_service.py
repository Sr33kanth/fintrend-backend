import os
from typing import List, Dict, Optional
from datetime import datetime
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class StockAnalysisService:
    """Service for analyzing stocks using LLM"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in .env file")
        
        openai.api_key = self.api_key
        self.model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    
    def analyze_breakout_candidates(self, reddit_posts: List[Dict]) -> Dict:
        """
        Analyze Reddit posts to identify potential breakout stock candidates
        
        Args:
            reddit_posts: List of Reddit posts to analyze
            
        Returns:
            Dict containing analysis results with potential breakout stocks
        """
        if not reddit_posts:
            return {
                "breakout_candidates": [],
                "analysis_timestamp": datetime.now().isoformat()
            }
        
        # Prepare posts for LLM analysis
        formatted_posts = []
        for post in reddit_posts:
            formatted_post = (
                f"Title: {post.get('headline', '')}\n"
                f"Content: {post.get('summary', '')}\n"
                f"Subreddit: {post.get('subreddit', '')}\n"
                f"Upvotes: {post.get('upvotes', 0)}\n"
                f"Comments: {post.get('comments', 0)}\n"
                f"Flair: {post.get('flair', 'None')}\n"
                f"URL: {post.get('url', '')}\n"
            )
            formatted_posts.append(formatted_post)
        
        # Create prompt for LLM
        prompt = f"""Analyze these Reddit posts about stocks and identify potential breakout candidates.
A breakout stock should have:
1. Strong catalysts or upcoming events
2. Significant community interest and discussion
3. Clear fundamental or technical reasons for potential price movement
4. Reasonable risk/reward ratio

Only identify stocks that have genuine potential - it's better to return no candidates than to suggest risky or unfounded plays.

Reddit Posts:
{formatted_posts}

For each potential breakout stock found in the posts, provide:
1. The stock symbol
2. A brief but specific reason why it could break out
3. Key catalysts or drivers
4. Risk factors to consider
5. A confidence score (0-1)

Return the analysis in this JSON format:
{{
    "breakout_candidates": [
        {{
            "symbol": "TICKER",
            "breakout_reason": "Clear, specific reason for potential breakout",
            "catalysts": ["list", "of", "specific", "catalysts"],
            "risks": ["list", "of", "key", "risks"],
            "confidence_score": 0.XX,
            "source_urls": ["relevant", "reddit", "post", "urls"]
        }}
    ],
    "analysis_summary": "Brief overall summary of findings"
}}

If no strong breakout candidates are found, return an empty list for breakout_candidates.
"""
        
        try:
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional stock analyst skilled at identifying breakout opportunities from social media discussions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for more focused analysis
                response_format={"type": "json_object"}
            )
            
            # Extract and return the analysis
            analysis = response.choices[0].message.content
            return {
                "analysis": analysis,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "error": f"Error analyzing posts: {str(e)}",
                "breakout_candidates": [],
                "analysis_timestamp": datetime.now().isoformat()
            }
    
    def get_stock_symbol_from_text(self, text: str) -> Optional[str]:
        """
        Extract stock symbol from text using LLM
        
        Args:
            text: Text to analyze
            
        Returns:
            Stock symbol if found, None otherwise
        """
        prompt = f"""Extract the main stock symbol discussed in this text. 
Return ONLY the symbol in standard format (e.g., AAPL, MSFT).
If multiple symbols are mentioned, return the main one being discussed.
If no clear stock symbol is found, return null.

Text:
{text}
"""
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a financial text analyzer that extracts stock symbols."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=10
            )
            
            symbol = response.choices[0].message.content.strip().upper()
            return symbol if symbol and symbol != "NULL" else None
            
        except Exception:
            return None 