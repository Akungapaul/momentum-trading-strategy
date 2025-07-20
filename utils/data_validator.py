"""
Data Validator Module

Handles cleaning and validation of ETF price data.
Independent module that can be tested separately.
"""

import pandas as pd
import numpy as np
from datetime import datetime


class DataValidator:
    """Validates and cleans ETF price data."""
    
    def __init__(self):
        self.validation_results = {}
    
    def check_missing_data(self, data, symbol):
        """
        Check for missing data in the dataset.
        
        Args:
            data (pd.DataFrame): ETF price data
            symbol (str): ETF symbol for reporting
            
        Returns:
            dict: Summary of missing data issues
        """
        if data.empty:
            return {"status": "error", "message": f"No data provided for {symbol}"}
        
        missing_summary = {
            "symbol": symbol,
            "total_rows": len(data),
            "missing_dates": data['Date'].isnull().sum(),
            "missing_prices": data['Close'].isnull().sum(),
            "missing_volumes": data['Volume'].isnull().sum(),
            "status": "pass"
        }
        
        # Check for any missing critical data
        if missing_summary["missing_dates"] > 0 or missing_summary["missing_prices"] > 0:
            missing_summary["status"] = "warning"
            missing_summary["message"] = f"Missing critical data for {symbol}"
        
        return missing_summary
    
    def validate_price_ranges(self, data, symbol):
        """
        Validate that prices are within reasonable ranges.
        
        Args:
            data (pd.DataFrame): ETF price data
            symbol (str): ETF symbol for reporting
            
        Returns:
            dict: Summary of price validation
        """
        if data.empty or 'Close' not in data.columns:
            return {"status": "error", "message": f"No price data for {symbol}"}
        
        prices = data['Close'].dropna()
        
        if len(prices) == 0:
            return {"status": "error", "message": f"No valid prices for {symbol}"}
        
        # Basic price validation
        validation_summary = {
            "symbol": symbol,
            "min_price": float(prices.min()),
            "max_price": float(prices.max()),
            "mean_price": float(prices.mean()),
            "negative_prices": (prices <= 0).sum(),
            "extreme_changes": 0,
            "status": "pass"
        }
        
        # Check for negative or zero prices
        if validation_summary["negative_prices"] > 0:
            validation_summary["status"] = "error"
            validation_summary["message"] = f"Found {validation_summary['negative_prices']} negative/zero prices"
            return validation_summary
        
        # Check for extreme daily changes (>50% in one day)
        if len(prices) > 1:
            daily_returns = prices.pct_change().dropna()
            extreme_changes = (abs(daily_returns) > 0.5).sum()
            validation_summary["extreme_changes"] = extreme_changes
            
            if extreme_changes > 0:
                validation_summary["status"] = "warning"
                validation_summary["message"] = f"Found {extreme_changes} extreme price changes (>50%)"
        
        return validation_summary
    
    def check_data_continuity(self, data, symbol):
        """
        Check for gaps in trading dates.
        
        Args:
            data (pd.DataFrame): ETF price data
            symbol (str): ETF symbol for reporting
            
        Returns:
            dict: Summary of data continuity
        """
        if data.empty or 'Date' not in data.columns:
            return {"status": "error", "message": f"No date data for {symbol}"}
        
        dates = pd.to_datetime(data['Date'], utc=True).sort_values()
        
        if len(dates) < 2:
            return {"status": "warning", "message": f"Insufficient data for continuity check: {len(dates)} days"}
        
        # Calculate gaps between trading days
        date_diffs = dates.diff().dropna()
        
        # Find gaps larger than 5 days (accounting for weekends)
        large_gaps = date_diffs[date_diffs > pd.Timedelta(days=5)]
        
        continuity_summary = {
            "symbol": symbol,
            "total_days": len(dates),
            "start_date": str(dates.min().date()),
            "end_date": str(dates.max().date()),
            "large_gaps": len(large_gaps),
            "status": "pass"
        }
        
        if len(large_gaps) > 0:
            continuity_summary["status"] = "warning"
            continuity_summary["message"] = f"Found {len(large_gaps)} large gaps in data"
            continuity_summary["gap_details"] = [str(gap) for gap in large_gaps.head()]
        
        return continuity_summary
    
    def fill_missing_data(self, data, method='forward_fill'):
        """
        Fill missing price data using specified method.
        
        Args:
            data (pd.DataFrame): ETF price data
            method (str): Method to fill missing data ('forward_fill', 'interpolate')
            
        Returns:
            pd.DataFrame: Data with missing values filled
        """
        if data.empty:
            return data
        
        data_filled = data.copy()
        
        # Fill missing prices
        price_columns = ['Open', 'High', 'Low', 'Close']
        
        for col in price_columns:
            if col in data_filled.columns:
                if method == 'forward_fill':
                    data_filled[col] = data_filled[col].ffill()
                elif method == 'interpolate':
                    data_filled[col] = data_filled[col].interpolate()
        
        # Fill missing volume with 0 or forward fill
        if 'Volume' in data_filled.columns:
            data_filled['Volume'] = data_filled['Volume'].fillna(0)
        
        return data_filled
    
    def validate_etf_data(self, data, symbol):
        """
        Comprehensive validation of ETF data.
        
        Args:
            data (pd.DataFrame): ETF price data
            symbol (str): ETF symbol
            
        Returns:
            dict: Complete validation report
        """
        print(f"\n--- Validating {symbol} data ---")
        
        validation_report = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "overall_status": "pass"
        }
        
        # Run all validation checks
        missing_check = self.check_missing_data(data, symbol)
        price_check = self.validate_price_ranges(data, symbol)
        continuity_check = self.check_data_continuity(data, symbol)
        
        validation_report["missing_data"] = missing_check
        validation_report["price_validation"] = price_check
        validation_report["continuity_check"] = continuity_check
        
        # Determine overall status
        statuses = [missing_check["status"], price_check["status"], continuity_check["status"]]
        
        if "error" in statuses:
            validation_report["overall_status"] = "error"
        elif "warning" in statuses:
            validation_report["overall_status"] = "warning"
        
        # Print summary
        print(f"Missing data: {missing_check['status']}")
        print(f"Price validation: {price_check['status']}")
        print(f"Data continuity: {continuity_check['status']}")
        print(f"Overall status: {validation_report['overall_status']}")
        
        return validation_report


def test_data_validator():
    """Test function to verify data validator works correctly."""
    
    print("Testing Data Validator...")
    
    # Import the data fetcher to get test data
    import sys
    sys.path.append('src/data_providers')
    from etf_data_fetcher import ETFDataFetcher
    
    # Load SPY data that was saved in Step 1
    fetcher = ETFDataFetcher()
    spy_data = fetcher.load_data_from_csv('SPY')
    
    if spy_data.empty:
        print("No SPY data found. Run data fetcher first.")
        return False
    
    # Initialize validator
    validator = DataValidator()
    
    # Test validation
    validation_report = validator.validate_etf_data(spy_data, 'SPY')
    
    print(f"\nValidation Report Summary:")
    print(f"Overall Status: {validation_report['overall_status']}")
    print(f"Total rows: {validation_report['missing_data']['total_rows']}")
    print(f"Price range: ${validation_report['price_validation']['min_price']:.2f} - ${validation_report['price_validation']['max_price']:.2f}")
    print(f"Date range: {validation_report['continuity_check']['start_date']} to {validation_report['continuity_check']['end_date']}")
    
    # Test data filling
    print(f"\n--- Testing data filling ---")
    filled_data = validator.fill_missing_data(spy_data)
    print(f"Original shape: {spy_data.shape}")
    print(f"Filled shape: {filled_data.shape}")
    
    return validation_report['overall_status'] in ['pass', 'warning']


if __name__ == "__main__":
    # Run test when script is executed directly
    test_data_validator()