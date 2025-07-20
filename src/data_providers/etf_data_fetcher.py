"""
ETF Data Fetcher Module

Handles downloading and storing ETF price data from Yahoo Finance.
Independent module that can be tested separately.
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from pathlib import Path
import os


class ETFDataFetcher:
    """Fetches and manages ETF price data."""
    
    def __init__(self, data_dir="data"):
        """
        Initialize the data fetcher.
        
        Args:
            data_dir (str): Directory to store data files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
    
    def fetch_etf_data(self, symbol, start_date, end_date):
        """
        Fetch ETF data from Yahoo Finance.
        
        Args:
            symbol (str): ETF symbol (e.g., 'SPY')
            start_date (str): Start date in 'YYYY-MM-DD' format
            end_date (str): End date in 'YYYY-MM-DD' format
            
        Returns:
            pd.DataFrame: ETF price data with Date, Open, High, Low, Close, Volume
        """
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)
            
            if data.empty:
                raise ValueError(f"No data found for {symbol}")
            
            # Reset index to make Date a column
            data.reset_index(inplace=True)
            
            # Ensure we have the required columns
            required_columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            for col in required_columns:
                if col not in data.columns:
                    raise ValueError(f"Missing required column: {col}")
            
            return data[required_columns]
            
        except Exception as e:
            print(f"Error fetching data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def save_data_to_csv(self, data, symbol):
        """
        Save ETF data to CSV file.
        
        Args:
            data (pd.DataFrame): ETF price data
            symbol (str): ETF symbol for filename
            
        Returns:
            str: Path to saved file
        """
        if data.empty:
            print(f"No data to save for {symbol}")
            return None
            
        filepath = self.data_dir / f"{symbol}.csv"
        data.to_csv(filepath, index=False)
        print(f"Saved {len(data)} rows of data to {filepath}")
        return str(filepath)
    
    def load_data_from_csv(self, symbol):
        """
        Load ETF data from CSV file.
        
        Args:
            symbol (str): ETF symbol
            
        Returns:
            pd.DataFrame: ETF price data or empty DataFrame if file not found
        """
        filepath = self.data_dir / f"{symbol}.csv"
        
        if not filepath.exists():
            print(f"Data file not found: {filepath}")
            return pd.DataFrame()
        
        try:
            data = pd.read_csv(filepath)
            data['Date'] = pd.to_datetime(data['Date'], utc=True)
            return data
        except Exception as e:
            print(f"Error loading data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def fetch_and_save_etf_data(self, symbol, start_date, end_date):
        """
        Fetch ETF data and save to CSV in one operation.
        
        Args:
            symbol (str): ETF symbol
            start_date (str): Start date in 'YYYY-MM-DD' format
            end_date (str): End date in 'YYYY-MM-DD' format
            
        Returns:
            pd.DataFrame: ETF price data
        """
        print(f"Fetching data for {symbol} from {start_date} to {end_date}")
        data = self.fetch_etf_data(symbol, start_date, end_date)
        
        if not data.empty:
            self.save_data_to_csv(data, symbol)
        
        return data
    
    def get_date_range_for_backtest(self, years_back=1):
        """
        Get appropriate date range for backtesting.
        
        Args:
            years_back (int): Number of years of data to fetch
            
        Returns:
            tuple: (start_date, end_date) as strings
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years_back * 365 + 30)  # Extra days for momentum calculation
        
        return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')


def test_etf_data_fetcher():
    """Test function to verify ETF data fetcher works correctly."""
    
    print("Testing ETF Data Fetcher...")
    
    # Initialize fetcher
    fetcher = ETFDataFetcher()
    
    # Get date range for 1 year backtest
    start_date, end_date = fetcher.get_date_range_for_backtest(1)
    print(f"Date range: {start_date} to {end_date}")
    
    # Test with SPY
    print("\n--- Testing SPY data fetch ---")
    spy_data = fetcher.fetch_and_save_etf_data('SPY', start_date, end_date)
    
    if not spy_data.empty:
        print(f"SPY data shape: {spy_data.shape}")
        print(f"Date range: {spy_data['Date'].min()} to {spy_data['Date'].max()}")
        print(f"Sample data:\n{spy_data.head()}")
        
        # Test loading from CSV
        print("\n--- Testing data loading from CSV ---")
        loaded_data = fetcher.load_data_from_csv('SPY')
        print(f"Loaded data shape: {loaded_data.shape}")
        
        return True
    else:
        print("Failed to fetch SPY data")
        return False


if __name__ == "__main__":
    # Run test when script is executed directly
    test_etf_data_fetcher()