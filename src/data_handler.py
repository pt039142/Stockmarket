import pandas as pd
import time
from src.logger import log_event

class DataHandler:
    """Handles real-time and historical market data from Zerodha API."""
    
    def __init__(self, zerodha_api):
        """
        Initialize DataHandler with Zerodha API instance.
        
        Args:
            zerodha_api: ZerodhaAPI or MockZerodhaAPI instance
        """
        self.api = zerodha_api
        self.data_cache = {}
        log_event('DataHandler initialized')
    
    def get_ltp(self, symbol):
        """
        Get Last Traded Price for a symbol.
        
        Args:
            symbol (str): Trading symbol (e.g., 'BANKNIFTY')
        
        Returns:
            float: Last traded price or None
        """
        try:
            # Ensure NSE prefix
            formatted_symbol = f'NSE:{symbol}' if ':' not in symbol else symbol
            ltp_data = self.api.get_ltp(formatted_symbol)
            
            if formatted_symbol in ltp_data:
                return ltp_data[formatted_symbol]['last_price']
            return None
        except Exception as e:
            log_event(f'Error fetching LTP for {symbol}: {str(e)}')
            return None
    
    def get_ltps(self, symbols):
        """
        Get LTP for multiple symbols.
        
        Args:
            symbols (list): List of symbols
        
        Returns:
            dict: Symbol -> LTP mapping
        """
        try:
            formatted_symbols = [f'NSE:{sym}' if ':' not in sym else sym for sym in symbols]
            ltp_data = self.api.get_ltp(formatted_symbols)
            
            result = {}
            for fmt_symbol, data in ltp_data.items():
                clean_symbol = fmt_symbol.replace('NSE:', '')
                result[clean_symbol] = data['last_price']
            
            return result
        except Exception as e:
            log_event(f'Error fetching LTPs: {str(e)}')
            return {}
    
    def get_quote(self, symbol):
        """
        Get quote data (OHLC) for a symbol.
        
        Args:
            symbol (str): Trading symbol
        
        Returns:
            dict: Quote data with OHLC, volume, etc.
        """
        try:
            formatted_symbol = f'NSE:{symbol}' if ':' not in symbol else symbol
            quote_data = self.api.get_quote(formatted_symbol)
            
            if formatted_symbol in quote_data:
                return quote_data[formatted_symbol]
            return None
        except Exception as e:
            log_event(f'Error fetching quote for {symbol}: {str(e)}')
            return None
    
    def get_quotes(self, symbols):
        """
        Get quote data for multiple symbols.
        
        Args:
            symbols (list): List of symbols
        
        Returns:
            dict: Symbol -> Quote mapping
        """
        try:
            formatted_symbols = [f'NSE:{sym}' if ':' not in sym else sym for sym in symbols]
            quote_data = self.api.get_quote(formatted_symbols)
            
            result = {}
            for fmt_symbol, data in quote_data.items():
                clean_symbol = fmt_symbol.replace('NSE:', '')
                result[clean_symbol] = data
            
            return result
        except Exception as e:
            log_event(f'Error fetching quotes: {str(e)}')
            return {}
    
    def get_historical_data(self, symbol, from_date=None, to_date=None, interval='15minute', days_back=30):
        """
        Fetch historical OHLC data for backtesting.
        
        Args:
            symbol (str): Trading symbol
            from_date (str): Start date 'YYYY-MM-DD' (optional)
            to_date (str): End date 'YYYY-MM-DD' (optional)
            interval (str): Candle interval (default: 15minute)
            days_back (int): Days of historical data if from_date/to_date not provided
        
        Returns:
            pd.DataFrame: Historical data with validations
        """
        try:
            # Calculate date range if not provided
            if not from_date or not to_date:
                to_date = pd.Timestamp.now().strftime('%Y-%m-%d')
                from_date = (pd.Timestamp.now() - pd.Timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            # Get instrument token
            token = self.api.get_instrument_token(symbol)
            if not token:
                log_event(f'Could not find token for {symbol}')
                return None
            
            # Fetch historical data with retry
            data = self.api.get_historical_data(token, from_date, to_date, interval)
            
            if not data:
                log_event(f'No historical data returned for {symbol}')
                return None
            
            # Convert to DataFrame with validation
            df = pd.DataFrame(data)
            
            # Validate required columns
            required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required_cols):
                log_event(f'Missing required columns in data for {symbol}')
                return None
            
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            df = df.sort_index()
            
            # Remove duplicate entries
            df = df[~df.index.duplicated(keep='last')]
            
            # Validate OHLC relationships
            df = df[(df['high'] >= df['low']) & 
                   (df['high'] >= df['open']) & 
                   (df['high'] >= df['close']) &
                   (df['low'] <= df['open']) & 
                   (df['low'] <= df['close'])].copy()
            
            if len(df) < 2:
                log_event(f'Insufficient valid data for {symbol} after validation')
                return None
            
            log_event(f'Fetched {len(df)} valid candles for {symbol}')
            return df
        
        except Exception as e:
            log_event(f'Error fetching historical data for {symbol}: {str(e)}')
            return None
    
    def cache_quote(self, symbol, quote_data):
        """
        Cache quote data for quick access.
        
        Args:
            symbol (str): Trading symbol
            quote_data (dict): Quote data to cache
        """
        self.data_cache[symbol] = {
            'data': quote_data,
            'timestamp': time.time()
        }
    
    def get_cached_quote(self, symbol, max_age=60):
        """
        Get cached quote if available and fresh.
        
        Args:
            symbol (str): Trading symbol
            max_age (int): Max age in seconds
        
        Returns:
            dict: Quote data or None
        """
        if symbol in self.data_cache:
            cached = self.data_cache[symbol]
            age = time.time() - cached['timestamp']
            
            if age < max_age:
                return cached['data']
        
        return None
    
    def validate_market_hours(self):
        """
        Check if market is currently open.
        
        Returns:
            bool: True if market is open
        """
        return self.api.is_market_open()
    
    def stream_data(self, symbols, callback, interval=1):
        """
        Stream real-time data with callback.
        
        Args:
            symbols (list): Symbols to stream
            callback (function): Callback function for data updates
            interval (int): Update interval in seconds
        """
        try:
            log_event(f'Data streaming started for {symbols}')
            
            while True:
                try:
                    prices = self.get_ltps(symbols)
                    callback(prices)
                    time.sleep(interval)
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    log_event(f'Error in data stream: {str(e)}')
                    time.sleep(interval)
        
        except Exception as e:
            log_event(f'Error starting data stream: {str(e)}')

