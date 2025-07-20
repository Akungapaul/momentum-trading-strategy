"""
Momentum Calculator Module

Calculates price momentum scores for ETFs without using technical analysis.
Pure price-based momentum using different time periods.
Independent module that can be tested separately.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class MomentumCalculator:
    """Calculates momentum scores based on price returns."""
    
    def __init__(self, periods=[30, 90, 180], weights=[0.5, 0.3, 0.2]):
        """
        Initialize momentum calculator.
        
        Args:
            periods (list): List of lookback periods in days [1-month, 3-month, 6-month]
            weights (list): Weights for each period in momentum score calculation
        """
        self.periods = periods
        self.weights = weights
        
        if len(periods) != len(weights):
            raise ValueError("Periods and weights must have same length")
        
        if abs(sum(weights) - 1.0) > 1e-6:
            raise ValueError("Weights must sum to 1.0")
    
    def calculate_period_return(self, prices, period_days):
        """
        Calculate return over a specific period.
        
        Args:
            prices (pd.Series): Price series with datetime index
            period_days (int): Number of days to look back
            
        Returns:
            float: Period return or None if insufficient data
        """
        if len(prices) < period_days + 1:
            return None
        
        # Get current price (most recent)
        current_price = prices.iloc[-1]
        
        # Get price from period_days ago
        past_price = prices.iloc[-(period_days + 1)]
        
        if past_price <= 0:
            return None
        
        # Calculate return
        period_return = (current_price / past_price) - 1.0
        return period_return
    
    def calculate_monthly_returns(self, data, symbol):
        """
        Calculate returns for all specified periods.
        
        Args:
            data (pd.DataFrame): ETF price data with Date and Close columns
            symbol (str): ETF symbol for reporting
            
        Returns:
            dict: Returns for each period
        """
        if data.empty or 'Close' not in data.columns:
            return {"error": f"No price data for {symbol}"}
        
        # Sort by date to ensure chronological order
        data_sorted = data.sort_values('Date').copy()
        prices = data_sorted['Close']
        
        returns = {
            "symbol": symbol,
            "calculation_date": data_sorted['Date'].iloc[-1].strftime('%Y-%m-%d'),
            "current_price": float(prices.iloc[-1]),
            "returns": {}
        }
        
        # Calculate returns for each period
        for period in self.periods:
            period_return = self.calculate_period_return(prices, period)
            returns["returns"][f"{period}d"] = period_return
        
        return returns
    
    def calculate_momentum_score(self, returns_dict):
        """
        Calculate weighted momentum score from period returns.
        
        Args:
            returns_dict (dict): Dictionary with period returns
            
        Returns:
            float: Weighted momentum score or None if insufficient data
        """
        if "error" in returns_dict:
            return None
        
        period_returns = returns_dict["returns"]
        
        # Check if we have returns for all periods
        valid_returns = []
        for i, period in enumerate(self.periods):
            ret = period_returns.get(f"{period}d")
            if ret is not None:
                valid_returns.append(ret * self.weights[i])
            else:
                # If any period is missing, return None
                return None
        
        momentum_score = sum(valid_returns)
        return momentum_score
    
    def rank_etfs_by_momentum(self, etf_scores):
        """
        Rank ETFs by their momentum scores.
        
        Args:
            etf_scores (dict): Dictionary with ETF symbols as keys and momentum scores as values
            
        Returns:
            list: List of tuples (symbol, score) sorted by score descending
        """
        # Filter out ETFs with None scores
        valid_scores = {symbol: score for symbol, score in etf_scores.items() 
                       if score is not None}
        
        if not valid_scores:
            return []
        
        # Sort by score descending (highest momentum first)
        ranked_etfs = sorted(valid_scores.items(), key=lambda x: x[1], reverse=True)
        
        return ranked_etfs
    
    def calculate_etf_momentum(self, data, symbol):
        """
        Calculate momentum score for a single ETF.
        
        Args:
            data (pd.DataFrame): ETF price data
            symbol (str): ETF symbol
            
        Returns:
            dict: Complete momentum analysis
        """
        # Calculate period returns
        returns = self.calculate_monthly_returns(data, symbol)
        
        if "error" in returns:
            return {"symbol": symbol, "error": returns["error"], "momentum_score": None}
        
        # Calculate momentum score
        momentum_score = self.calculate_momentum_score(returns)
        
        # Compile full analysis
        analysis = {
            "symbol": symbol,
            "calculation_date": returns["calculation_date"],
            "current_price": returns["current_price"],
            "period_returns": returns["returns"],
            "momentum_score": momentum_score,
            "periods_used": self.periods,
            "weights_used": self.weights
        }
        
        return analysis
    
    def calculate_multi_etf_momentum(self, etf_data_dict):
        """
        Calculate momentum scores for multiple ETFs and rank them.
        
        Args:
            etf_data_dict (dict): Dictionary with ETF symbols as keys and DataFrames as values
            
        Returns:
            dict: Complete momentum analysis with rankings
        """
        etf_analyses = {}
        momentum_scores = {}
        
        # Calculate momentum for each ETF
        for symbol, data in etf_data_dict.items():
            analysis = self.calculate_etf_momentum(data, symbol)
            etf_analyses[symbol] = analysis
            momentum_scores[symbol] = analysis["momentum_score"]
        
        # Rank ETFs by momentum
        rankings = self.rank_etfs_by_momentum(momentum_scores)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "etf_analyses": etf_analyses,
            "momentum_scores": momentum_scores,
            "rankings": rankings,
            "top_etf": rankings[0][0] if rankings else None
        }


def test_momentum_calculator():
    """Test function to verify momentum calculator works correctly."""
    
    print("Testing Momentum Calculator...")
    
    # Import required modules
    import sys
    sys.path.append('src/data_providers')
    sys.path.append('utils')
    from etf_data_fetcher import ETFDataFetcher
    
    # Initialize components
    fetcher = ETFDataFetcher()
    calculator = MomentumCalculator()
    
    # Load SPY data from Step 1
    spy_data = fetcher.load_data_from_csv('SPY')
    
    if spy_data.empty:
        print("No SPY data found. Run data fetcher first.")
        return False
    
    print(f"Testing with {len(spy_data)} days of SPY data")
    
    # Test single ETF momentum calculation
    print(f"\n--- Testing single ETF momentum calculation ---")
    spy_analysis = calculator.calculate_etf_momentum(spy_data, 'SPY')
    
    print(f"SPY Analysis:")
    print(f"  Current Price: ${spy_analysis['current_price']:.2f}")
    print(f"  Period Returns:")
    for period, ret in spy_analysis['period_returns'].items():
        if ret is not None:
            print(f"    {period}: {ret:.4f} ({ret*100:.2f}%)")
        else:
            print(f"    {period}: Insufficient data")
    print(f"  Momentum Score: {spy_analysis['momentum_score']:.4f}")
    
    # Test with multiple ETFs (simulate QQQ and IWM data for testing)
    print(f"\n--- Testing multiple ETF ranking ---")
    
    # For testing, let's create some sample data for QQQ and IWM
    # In real implementation, we'd fetch actual data
    qqq_data = spy_data.copy()
    qqq_data['Close'] = qqq_data['Close'] * 1.05  # Simulate 5% higher performance
    
    iwm_data = spy_data.copy()
    iwm_data['Close'] = iwm_data['Close'] * 0.98  # Simulate 2% lower performance
    
    etf_data = {
        'SPY': spy_data,
        'QQQ': qqq_data,
        'IWM': iwm_data
    }
    
    multi_analysis = calculator.calculate_multi_etf_momentum(etf_data)
    
    print(f"ETF Momentum Rankings:")
    for i, (symbol, score) in enumerate(multi_analysis['rankings'], 1):
        print(f"  {i}. {symbol}: {score:.4f}")
    
    print(f"Top ETF: {multi_analysis['top_etf']}")
    
    return True


if __name__ == "__main__":
    # Run test when script is executed directly
    test_momentum_calculator()