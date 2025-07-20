"""
Momentum Backtest Engine

Runs historical simulation of momentum strategy with monthly rebalancing.
Combines all previous components into a complete backtesting framework.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import sys
import os

# Add paths to import our modules
sys.path.append('src/data_providers')
sys.path.append('src/portfolio')
sys.path.append('strategies/scenario_based')
sys.path.append('utils')

from etf_data_fetcher import ETFDataFetcher
from portfolio_manager import PortfolioManager
from momentum_calculator import MomentumCalculator
from data_validator import DataValidator


class MomentumBacktest:
    """Backtests momentum strategy with monthly rebalancing."""
    
    def __init__(self, etf_symbols=['SPY', 'QQQ', 'IWM'], 
                 initial_capital=100000, 
                 transaction_cost_pct=0.001,
                 rebalance_frequency='monthly'):
        """
        Initialize backtest engine.
        
        Args:
            etf_symbols (list): List of ETF symbols to trade
            initial_capital (float): Starting capital
            transaction_cost_pct (float): Transaction cost percentage
            rebalance_frequency (str): How often to rebalance ('monthly')
        """
        self.etf_symbols = etf_symbols
        self.initial_capital = initial_capital
        self.transaction_cost_pct = transaction_cost_pct
        self.rebalance_frequency = rebalance_frequency
        
        # Initialize components
        self.data_fetcher = ETFDataFetcher()
        self.validator = DataValidator()
        self.momentum_calculator = MomentumCalculator()
        self.portfolio = PortfolioManager(initial_capital, transaction_cost_pct)
        
        # Results storage
        self.backtest_results = {}
        self.daily_portfolio_values = []
        self.rebalance_history = []
        self.etf_data = {}
    
    def load_etf_data(self, start_date, end_date):
        """
        Load data for all ETFs in the backtest.
        
        Args:
            start_date (str): Start date for backtest
            end_date (str): End date for backtest
            
        Returns:
            bool: True if all data loaded successfully
        """
        print(f"Loading ETF data from {start_date} to {end_date}...")
        
        for symbol in self.etf_symbols:
            print(f"  Loading {symbol}...")
            
            # Try to load from file first
            data = self.data_fetcher.load_data_from_csv(symbol)
            
            # If no data or insufficient data, fetch from API
            if data.empty:
                print(f"    Fetching {symbol} from API...")
                data = self.data_fetcher.fetch_and_save_etf_data(symbol, start_date, end_date)
            
            # Validate data
            validation = self.validator.validate_etf_data(data, symbol)
            if validation['overall_status'] == 'error':
                print(f"    ERROR: Invalid data for {symbol}")
                return False
            
            # Filter data to backtest period
            data['Date'] = pd.to_datetime(data['Date'], utc=True)
            start_dt = pd.to_datetime(start_date, utc=True)
            end_dt = pd.to_datetime(end_date, utc=True)
            
            filtered_data = data[(data['Date'] >= start_dt) & (data['Date'] <= end_dt)].copy()
            
            if len(filtered_data) < 180:  # Need at least 6 months for momentum calculation
                print(f"    WARNING: Insufficient data for {symbol}: {len(filtered_data)} days")
                return False
            
            self.etf_data[symbol] = filtered_data.sort_values('Date')
            print(f"    Loaded {len(filtered_data)} days of {symbol} data")
        
        return True
    
    def get_rebalance_dates(self, start_date, end_date):
        """
        Generate list of rebalancing dates.
        
        Args:
            start_date (str): Start date
            end_date (str): End date
            
        Returns:
            list: List of rebalancing dates
        """
        rebalance_dates = []
        current_date = pd.to_datetime(start_date, utc=True)
        end_dt = pd.to_datetime(end_date, utc=True)
        
        # Start rebalancing 6 months after start to have momentum data
        current_date = current_date + relativedelta(months=6)
        
        while current_date <= end_dt:
            rebalance_dates.append(current_date)
            current_date = current_date + relativedelta(months=1)
        
        return rebalance_dates
    
    def get_prices_on_date(self, target_date):
        """
        Get ETF prices on or closest to target date.
        
        Args:
            target_date (pd.Timestamp): Target date
            
        Returns:
            dict: Dictionary with symbol: price pairs
        """
        prices = {}
        
        for symbol, data in self.etf_data.items():
            # Find closest date (on or before target date)
            available_dates = data[data['Date'] <= target_date]
            
            if len(available_dates) == 0:
                continue  # No data available for this date
            
            closest_data = available_dates.iloc[-1]
            prices[symbol] = closest_data['Close']
        
        return prices
    
    def get_data_up_to_date(self, target_date):
        """
        Get ETF data up to a specific date for momentum calculation.
        
        Args:
            target_date (pd.Timestamp): Target date
            
        Returns:
            dict: Dictionary with symbol: DataFrame pairs
        """
        data_subset = {}
        
        for symbol, data in self.etf_data.items():
            # Get all data up to and including target date
            subset = data[data['Date'] <= target_date].copy()
            if len(subset) > 0:
                data_subset[symbol] = subset
        
        return data_subset
    
    def run_backtest(self, start_date, end_date):
        """
        Run the complete momentum backtest.
        
        Args:
            start_date (str): Start date for backtest
            end_date (str): End date for backtest
            
        Returns:
            dict: Backtest results
        """
        print(f"\\n=== RUNNING MOMENTUM BACKTEST ===")
        print(f"Period: {start_date} to {end_date}")
        print(f"ETFs: {', '.join(self.etf_symbols)}")
        print(f"Initial Capital: ${self.initial_capital:,.2f}")
        print(f"Transaction Cost: {self.transaction_cost_pct*100:.2f}%")
        
        # Load data
        if not self.load_etf_data(start_date, end_date):
            return {"error": "Failed to load ETF data"}
        
        # Get rebalancing dates
        rebalance_dates = self.get_rebalance_dates(start_date, end_date)
        print(f"\\nRebalancing on {len(rebalance_dates)} dates")
        
        # Run backtest
        for i, rebalance_date in enumerate(rebalance_dates):
            print(f"\\n--- Rebalance {i+1}: {rebalance_date.strftime('%Y-%m-%d')} ---")
            
            # Get data up to rebalance date
            current_data = self.get_data_up_to_date(rebalance_date)
            
            # Calculate momentum scores
            momentum_analysis = self.momentum_calculator.calculate_multi_etf_momentum(current_data)
            
            if not momentum_analysis['rankings']:
                print("  No valid momentum rankings, skipping...")
                continue
            
            # Get top ETF
            top_etf = momentum_analysis['top_etf']
            top_score = momentum_analysis['rankings'][0][1]
            
            print(f"  Top ETF: {top_etf} (score: {top_score:.4f})")
            
            # Print all rankings
            for rank, (symbol, score) in enumerate(momentum_analysis['rankings'], 1):
                print(f"    {rank}. {symbol}: {score:.4f}")
            
            # Get current prices
            current_prices = self.get_prices_on_date(rebalance_date)
            
            # Update portfolio value before rebalancing
            portfolio_value_before = self.portfolio.update_portfolio_value(current_prices)
            
            # Rebalance to top ETF
            rebalance_result = self.portfolio.rebalance_to_etf(
                top_etf, current_prices, rebalance_date.strftime('%Y-%m-%d'))
            
            # Record rebalancing
            rebalance_record = {
                "date": rebalance_date.strftime('%Y-%m-%d'),
                "selected_etf": top_etf,
                "momentum_score": top_score,
                "portfolio_value_before": portfolio_value_before,
                "rebalance_success": rebalance_result['success'],
                "rankings": momentum_analysis['rankings']
            }
            
            if rebalance_result['success']:
                portfolio_value_after = self.portfolio.update_portfolio_value(current_prices)
                rebalance_record["portfolio_value_after"] = portfolio_value_after
                print(f"  Rebalanced successfully to {top_etf}")
                print(f"  Portfolio value: ${portfolio_value_after:,.2f}")
            else:
                print(f"  Rebalancing failed: {rebalance_result.get('error', 'Unknown error')}")
            
            self.rebalance_history.append(rebalance_record)
        
        # Calculate final results
        final_prices = self.get_prices_on_date(pd.to_datetime(end_date, utc=True))
        final_portfolio_value = self.portfolio.update_portfolio_value(final_prices)
        
        self.backtest_results = {
            "start_date": start_date,
            "end_date": end_date,
            "initial_capital": self.initial_capital,
            "final_portfolio_value": final_portfolio_value,
            "total_return": (final_portfolio_value / self.initial_capital - 1) * 100,
            "rebalance_count": len(self.rebalance_history),
            "transaction_summary": self.portfolio.get_transaction_summary(),
            "final_position": self.portfolio.get_current_position()
        }
        
        return self.backtest_results
    
    def print_backtest_summary(self):
        """Print summary of backtest results."""
        
        if not self.backtest_results:
            print("No backtest results available")
            return
        
        results = self.backtest_results
        
        print(f"\\n=== BACKTEST RESULTS SUMMARY ===")
        print(f"Period: {results['start_date']} to {results['end_date']}")
        print(f"Initial Capital: ${results['initial_capital']:,.2f}")
        print(f"Final Portfolio Value: ${results['final_portfolio_value']:,.2f}")
        print(f"Total Return: {results['total_return']:.2f}%")
        print(f"Number of Rebalances: {results['rebalance_count']}")
        
        # Transaction costs
        tx_summary = results['transaction_summary']
        print(f"\\nTransaction Summary:")
        print(f"  Total Transactions: {tx_summary['total_transactions']}")
        print(f"  Total Transaction Costs: ${tx_summary['total_transaction_costs']:.2f}")
        print(f"  Average Cost per Transaction: ${tx_summary['average_cost_per_transaction']:.2f}")
        
        # Final position
        final_pos = results['final_position']
        print(f"\\nFinal Position:")
        print(f"  ETF: {final_pos['symbol']}")
        print(f"  Shares: {final_pos['shares']}")
        print(f"  Cash: ${final_pos['cash']:.2f}")
        
        # Show rebalancing history
        print(f"\\nRebalancing History:")
        for i, rebal in enumerate(self.rebalance_history, 1):
            print(f"  {i}. {rebal['date']}: {rebal['selected_etf']} (score: {rebal['momentum_score']:.4f})")


def test_momentum_backtest():
    """Test the momentum backtest engine."""
    
    print("Testing Momentum Backtest Engine...")
    
    # Create backtest with smaller capital for testing
    backtest = MomentumBacktest(
        etf_symbols=['SPY', 'QQQ', 'IWM'],
        initial_capital=100000,
        transaction_cost_pct=0.001
    )
    
    # Run backtest with available data (we have data from 2024-06-20 to 2025-07-18)
    start_date = '2024-06-20'
    end_date = '2025-07-18'
    
    results = backtest.run_backtest(start_date, end_date)
    
    if "error" in results:
        print(f"Backtest failed: {results['error']}")
        return False
    
    # Print results
    backtest.print_backtest_summary()
    
    return True


if __name__ == "__main__":
    # Install required package for date arithmetic
    try:
        from dateutil.relativedelta import relativedelta
    except ImportError:
        print("Installing python-dateutil...")
        os.system("pip install python-dateutil")
        from dateutil.relativedelta import relativedelta
    
    # Run test
    test_momentum_backtest()