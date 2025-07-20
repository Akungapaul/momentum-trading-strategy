"""
Out-of-Sample Backtest Engine

Runs backtest on unseen data with frozen strategy parameters.
Ensures no parameter optimization on out-of-sample data.
Independent module that can be tested separately.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import sys
import os
from typing import Dict, List, Tuple, Optional

# Add paths to import our modules
sys.path.append('src/data_providers')
sys.path.append('src/portfolio')
sys.path.append('strategies/scenario_based')
sys.path.append('utils')
sys.path.append('backtesting')

from etf_data_fetcher import ETFDataFetcher
from portfolio_manager import PortfolioManager
from momentum_calculator import MomentumCalculator
from data_validator import DataValidator
from data_split_manager import DataSplitManager
from oos_validator import OutOfSampleValidator


class OOSBacktestEngine:
    """Runs out-of-sample backtest with frozen parameters."""
    
    def __init__(self, frozen_parameters: Dict, initial_capital: float = 100000):
        """
        Initialize OOS backtest engine with frozen parameters.
        
        Args:
            frozen_parameters (Dict): Strategy parameters that cannot be changed
            initial_capital (float): Starting capital for backtest
        """
        self.frozen_parameters = frozen_parameters.copy()
        self.initial_capital = initial_capital
        
        # Create parameter lock
        self.oos_validator = OutOfSampleValidator()
        self.parameter_lock = self.oos_validator.create_parameter_lock('momentum_strategy', frozen_parameters)
        
        # Initialize components with frozen parameters
        self.momentum_calculator = MomentumCalculator(
            periods=frozen_parameters.get('periods', [30, 90, 180]),
            weights=frozen_parameters.get('weights', [0.5, 0.3, 0.2])
        )
        
        self.portfolio = PortfolioManager(
            initial_capital=initial_capital,
            transaction_cost_pct=frozen_parameters.get('transaction_cost_pct', 0.001)
        )
        
        # Results storage
        self.oos_results = {}
        self.daily_portfolio_values = []
        self.rebalance_history = []
        self.parameter_validation_log = []
    
    def validate_parameters_unchanged(self, current_parameters: Dict) -> bool:
        """
        Validate that current parameters match frozen parameters.
        
        Args:
            current_parameters (Dict): Current parameters to validate
            
        Returns:
            bool: True if parameters are unchanged
        """
        validation = self.oos_validator.validate_against_lock(self.parameter_lock, current_parameters)
        self.parameter_validation_log.append(validation)
        
        if not validation['lock_valid']:
            print("WARNING: Parameter validation failed!")
            for violation in validation['violations']:
                print(f"  - {violation}")
        
        return validation['lock_valid']
    
    def run_oos_backtest(self, oos_data: Dict[str, pd.DataFrame], 
                        start_date: str, end_date: str) -> Dict:
        """
        Run out-of-sample backtest with frozen parameters.
        
        Args:
            oos_data (Dict): Out-of-sample data for each ETF
            start_date (str): Start date of OOS period
            end_date (str): End date of OOS period
            
        Returns:
            Dict: OOS backtest results
        """
        print(f"\n=== RUNNING OUT-OF-SAMPLE BACKTEST ===")
        print(f"Period: {start_date} to {end_date}")
        print(f"ETFs: {', '.join(oos_data.keys())}")
        print(f"Initial Capital: ${self.initial_capital:,.2f}")
        
        # Validate frozen parameters haven't changed
        current_params = {
            'periods': self.momentum_calculator.periods,
            'weights': self.momentum_calculator.weights,
            'transaction_cost_pct': self.portfolio.transaction_cost_pct,
            'rebalance_frequency': self.frozen_parameters.get('rebalance_frequency', 'monthly'),
            'etf_symbols': list(oos_data.keys())
        }
        
        if not self.validate_parameters_unchanged(current_params):
            return {"error": "Parameter validation failed - parameters have been modified"}
        
        print(f"Parameter validation passed - using frozen parameters from in-sample period")
        
        # Get rebalancing dates for OOS period
        rebalance_dates = self.get_oos_rebalance_dates(start_date, end_date)
        print(f"OOS rebalancing on {len(rebalance_dates)} dates")
        
        # Track daily portfolio values
        self.daily_portfolio_values = []
        self.rebalance_history = []
        
        # Run OOS backtest
        for i, rebalance_date in enumerate(rebalance_dates):
            print(f"\n--- OOS Rebalance {i+1}: {rebalance_date.strftime('%Y-%m-%d')} ---")
            
            # Get data up to rebalance date (no future data)
            current_data = self.get_data_up_to_date(oos_data, rebalance_date)
            
            if not current_data:
                print("  No data available for this date, skipping...")
                continue
            
            # Calculate momentum scores using FROZEN parameters
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
            current_prices = self.get_prices_on_date(oos_data, rebalance_date)
            
            # Update portfolio value before rebalancing
            portfolio_value_before = self.portfolio.update_portfolio_value(current_prices)
            
            # Rebalance to top ETF using FROZEN parameters
            rebalance_result = self.portfolio.rebalance_to_etf(
                top_etf, current_prices, rebalance_date.strftime('%Y-%m-%d'))
            
            # Record rebalancing
            rebalance_record = {
                "date": rebalance_date.strftime('%Y-%m-%d'),
                "selected_etf": top_etf,
                "momentum_score": top_score,
                "portfolio_value_before": portfolio_value_before,
                "rebalance_success": rebalance_result['success'],
                "rankings": momentum_analysis['rankings'],
                "oos_period": True  # Flag to identify OOS decisions
            }
            
            if rebalance_result['success']:
                portfolio_value_after = self.portfolio.update_portfolio_value(current_prices)
                rebalance_record["portfolio_value_after"] = portfolio_value_after
                print(f"  Rebalanced successfully to {top_etf}")
                print(f"  Portfolio value: ${portfolio_value_after:,.2f}")
            else:
                print(f"  Rebalancing failed: {rebalance_result.get('error', 'Unknown error')}")
            
            self.rebalance_history.append(rebalance_record)
        
        # Calculate final OOS results
        final_prices = self.get_prices_on_date(oos_data, pd.to_datetime(end_date, utc=True))
        final_portfolio_value = self.portfolio.update_portfolio_value(final_prices)
        
        # Calculate daily returns for the OOS period
        daily_returns = self.calculate_oos_daily_returns(oos_data, start_date, end_date)
        
        self.oos_results = {
            "backtest_type": "out_of_sample",
            "start_date": start_date,
            "end_date": end_date,
            "initial_capital": self.initial_capital,
            "final_portfolio_value": final_portfolio_value,
            "total_return": (final_portfolio_value / self.initial_capital - 1) * 100,
            "rebalance_count": len(self.rebalance_history),
            "transaction_summary": self.portfolio.get_transaction_summary(),
            "final_position": self.portfolio.get_current_position(),
            "frozen_parameters": self.frozen_parameters,
            "parameter_validation_passed": all(v['lock_valid'] for v in self.parameter_validation_log),
            "daily_returns": daily_returns,
            "rebalance_history": self.rebalance_history
        }
        
        return self.oos_results
    
    def get_oos_rebalance_dates(self, start_date: str, end_date: str) -> List[pd.Timestamp]:
        """
        Generate rebalancing dates for OOS period.
        
        Args:
            start_date (str): Start date
            end_date (str): End date
            
        Returns:
            List[pd.Timestamp]: List of rebalancing dates
        """
        rebalance_dates = []
        current_date = pd.to_datetime(start_date, utc=True)
        end_dt = pd.to_datetime(end_date, utc=True)
        
        # Start rebalancing from the beginning of OOS period
        while current_date <= end_dt:
            rebalance_dates.append(current_date)
            current_date = current_date + relativedelta(months=1)
        
        return rebalance_dates
    
    def get_data_up_to_date(self, oos_data: Dict[str, pd.DataFrame], 
                           target_date: pd.Timestamp) -> Dict[str, pd.DataFrame]:
        """
        Get ETF data up to a specific date (no future data leakage).
        
        Args:
            oos_data (Dict): OOS data for each ETF
            target_date (pd.Timestamp): Target date
            
        Returns:
            Dict: Data subset up to target date
        """
        data_subset = {}
        
        for symbol, data in oos_data.items():
            # Get all data up to and including target date
            subset = data[data['Date'] <= target_date].copy()
            
            # Need sufficient data for momentum calculation
            # For OOS testing, we need all available historical data plus OOS data up to target date
            if len(subset) >= 30:  # Minimum for monthly momentum
                data_subset[symbol] = subset
        
        return data_subset
    
    def get_prices_on_date(self, oos_data: Dict[str, pd.DataFrame], 
                          target_date: pd.Timestamp) -> Dict[str, float]:
        """
        Get ETF prices on or closest to target date.
        
        Args:
            oos_data (Dict): OOS data for each ETF
            target_date (pd.Timestamp): Target date
            
        Returns:
            Dict: Prices for each ETF
        """
        prices = {}
        
        for symbol, data in oos_data.items():
            # Find closest date (on or before target date)
            available_dates = data[data['Date'] <= target_date]
            
            if len(available_dates) == 0:
                continue
            
            closest_data = available_dates.iloc[-1]
            prices[symbol] = closest_data['Close']
        
        return prices
    
    def calculate_oos_daily_returns(self, oos_data: Dict[str, pd.DataFrame], 
                                   start_date: str, end_date: str) -> List[float]:
        """
        Calculate daily portfolio returns for OOS period.
        
        Args:
            oos_data (Dict): OOS data for each ETF
            start_date (str): Start date
            end_date (str): End date
            
        Returns:
            List[float]: Daily returns
        """
        # Get all trading dates in OOS period
        all_dates = set()
        for data in oos_data.values():
            dates = data[(data['Date'] >= start_date) & (data['Date'] <= end_date)]['Date']
            all_dates.update(dates)
        
        trading_dates = sorted(list(all_dates))
        
        if len(trading_dates) < 2:
            return []
        
        # Calculate daily portfolio values
        daily_values = []
        
        for date in trading_dates:
            prices = self.get_prices_on_date(oos_data, date)
            portfolio_value = self.portfolio.update_portfolio_value(prices)
            daily_values.append(portfolio_value)
        
        # Calculate daily returns
        daily_returns = []
        for i in range(1, len(daily_values)):
            if daily_values[i-1] > 0:
                ret = (daily_values[i] / daily_values[i-1]) - 1
                daily_returns.append(ret)
        
        return daily_returns
    
    def ensure_no_parameter_fitting(self) -> Dict:
        """
        Ensure no parameter optimization occurred during OOS testing.
        
        Returns:
            Dict: Validation results
        """
        validation_summary = {
            'no_parameter_fitting': True,
            'total_validations': len(self.parameter_validation_log),
            'failed_validations': 0,
            'violations': []
        }
        
        for validation in self.parameter_validation_log:
            if not validation['lock_valid']:
                validation_summary['no_parameter_fitting'] = False
                validation_summary['failed_validations'] += 1
                validation_summary['violations'].extend(validation['violations'])
        
        return validation_summary
    
    def generate_oos_performance_report(self) -> Dict:
        """
        Generate comprehensive OOS performance report.
        
        Returns:
            Dict: Performance report
        """
        if not self.oos_results:
            return {"error": "No OOS results available"}
        
        report = {
            "oos_period": {
                "start_date": self.oos_results["start_date"],
                "end_date": self.oos_results["end_date"],
                "duration_days": None
            },
            "performance_summary": {
                "initial_capital": self.oos_results["initial_capital"],
                "final_value": self.oos_results["final_portfolio_value"],
                "total_return_pct": self.oos_results["total_return"],
                "number_of_rebalances": self.oos_results["rebalance_count"]
            },
            "strategy_validation": {
                "parameters_frozen": True,
                "validation_passed": self.oos_results["parameter_validation_passed"],
                "frozen_parameters": self.oos_results["frozen_parameters"]
            },
            "transaction_analysis": self.oos_results["transaction_summary"],
            "rebalancing_decisions": []
        }
        
        # Add rebalancing decisions
        for rebalance in self.oos_results["rebalance_history"]:
            decision = {
                "date": rebalance["date"],
                "selected_etf": rebalance["selected_etf"],
                "momentum_score": rebalance["momentum_score"],
                "portfolio_value": rebalance.get("portfolio_value_after", rebalance["portfolio_value_before"])
            }
            report["rebalancing_decisions"].append(decision)
        
        return report
    
    def print_oos_summary(self):
        """Print OOS backtest summary."""
        
        if not self.oos_results:
            print("No OOS results available")
            return
        
        print(f"\n=== OUT-OF-SAMPLE BACKTEST SUMMARY ===")
        print(f"Period: {self.oos_results['start_date']} to {self.oos_results['end_date']}")
        print(f"Initial Capital: ${self.oos_results['initial_capital']:,.2f}")
        print(f"Final Portfolio Value: ${self.oos_results['final_portfolio_value']:,.2f}")
        print(f"Total Return: {self.oos_results['total_return']:.2f}%")
        print(f"Number of Rebalances: {self.oos_results['rebalance_count']}")
        
        # Parameter validation
        print(f"\nParameter Validation:")
        print(f"  Parameters Frozen: YES")
        print(f"  Validation Passed: {'YES' if self.oos_results['parameter_validation_passed'] else 'NO'}")
        
        # Transaction summary
        tx_summary = self.oos_results['transaction_summary']
        print(f"\nTransaction Summary:")
        print(f"  Total Transactions: {tx_summary['total_transactions']}")
        print(f"  Total Transaction Costs: ${tx_summary.get('total_transaction_costs', 0):.2f}")
        
        # Final position
        final_pos = self.oos_results['final_position']
        print(f"\nFinal Position:")
        print(f"  ETF: {final_pos['symbol']}")
        print(f"  Shares: {final_pos['shares']}")
        print(f"  Cash: ${final_pos['cash']:.2f}")
        
        # Rebalancing history
        print(f"\nOOS Rebalancing History:")
        for i, rebal in enumerate(self.oos_results['rebalance_history'], 1):
            print(f"  {i}. {rebal['date']}: {rebal['selected_etf']} (score: {rebal['momentum_score']:.4f})")


def test_oos_backtest_engine():
    """Test the OOS backtest engine."""
    
    print("Testing OOS Backtest Engine...")
    
    # Import data components
    from data_split_manager import DataSplitManager
    
    # Load ETF data
    fetcher = ETFDataFetcher()
    spy_data = fetcher.load_data_from_csv('SPY')
    qqq_data = fetcher.load_data_from_csv('QQQ')
    iwm_data = fetcher.load_data_from_csv('IWM')
    
    if spy_data.empty:
        print("No ETF data found. Run data fetcher first.")
        return False
    
    # Split data into in-sample and out-of-sample
    splitter = DataSplitManager()
    split_date = '2025-04-01'
    
    etf_data = {'SPY': spy_data, 'QQQ': qqq_data, 'IWM': iwm_data}
    in_sample_dict, oos_dict = splitter.split_multiple_etfs(etf_data, split_date)
    
    print(f"Data split at {split_date}:")
    for symbol in etf_data.keys():
        if symbol in oos_dict:
            print(f"  {symbol}: {len(oos_dict[symbol])} OOS observations")
    
    # Define frozen parameters (from original momentum strategy)
    frozen_params = {
        'periods': [30, 90, 180],
        'weights': [0.5, 0.3, 0.2],
        'transaction_cost_pct': 0.001,
        'rebalance_frequency': 'monthly',
        'etf_symbols': ['SPY', 'QQQ', 'IWM']
    }
    
    # Initialize OOS backtest engine
    oos_engine = OOSBacktestEngine(frozen_params, initial_capital=100000)
    
    print(f"\nInitialized OOS engine with frozen parameters")
    
    # For OOS backtest, we need full historical data to calculate momentum
    # but only make decisions based on data up to each rebalance date
    print(f"\n--- Running OOS Backtest ---")
    oos_results = oos_engine.run_oos_backtest(
        etf_data,  # Use full data, engine will filter properly
        split_date, 
        '2025-07-18'
    )
    
    if "error" in oos_results:
        print(f"OOS backtest failed: {oos_results['error']}")
        return False
    
    # Print summary
    oos_engine.print_oos_summary()
    
    # Test parameter validation
    print(f"\n--- Parameter Validation Test ---")
    fitting_check = oos_engine.ensure_no_parameter_fitting()
    print(f"No parameter fitting: {fitting_check['no_parameter_fitting']}")
    print(f"Total validations: {fitting_check['total_validations']}")
    print(f"Failed validations: {fitting_check['failed_validations']}")
    
    return True


if __name__ == "__main__":
    # Run test when script is executed directly
    test_oos_backtest_engine()