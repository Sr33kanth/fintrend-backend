class WatchlistService:
    """
    Service to manage the stock watchlist
    Stores watchlist in memory for now - we'll upgrade to persistent storage later
    """
    def __init__(self):
        self._stocks = set()
    
    def add_stock(self, symbol: str) -> list:
        """
        Add a stock symbol to the watchlist
        
        Args:
            symbol (str): Stock symbol to add
        
        Returns:
            list: Updated list of stocks in watchlist
        
        Raises:
            ValueError: If stock symbol is invalid or already exists
        """
        # Basic symbol validation (uppercase, no special characters)
        symbol = symbol.upper().strip()
        
        if not symbol:
            raise ValueError("Stock symbol cannot be empty")
        
        if not symbol.isalpha():
            raise ValueError("Invalid stock symbol")
        
        if symbol in self._stocks:
            raise ValueError(f"Stock {symbol} is already in watchlist")
        
        self._stocks.add(symbol)
        return list(self._stocks)
    
    def remove_stock(self, symbol: str) -> list:
        """
        Remove a stock symbol from the watchlist
        
        Args:
            symbol (str): Stock symbol to remove
        
        Returns:
            list: Updated list of stocks in watchlist
        
        Raises:
            ValueError: If stock symbol is not in watchlist
        """
        symbol = symbol.upper().strip()
        
        if symbol not in self._stocks:
            raise ValueError(f"Stock {symbol} not found in watchlist")
        
        self._stocks.remove(symbol)
        return list(self._stocks)
    
    def get_stocks(self) -> list:
        """
        Get current list of stocks in watchlist
        
        Returns:
            list: Current stocks in watchlist
        """
        return list(self._stocks)