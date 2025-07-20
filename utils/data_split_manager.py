"""
Data Split Manager Module

Handles clean separation of in-sample vs out-of-sample data for backtesting.
Prevents data leakage and ensures proper chronological splits.
Independent module that can be tested separately.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Tuple, List


class DataSplitManager:
    """Manages data splits for out-of-sample backtesting."""
    
    def __init__(self):
        self.split_history = []
        self.validation_results = {}
    
    def split_data_chronologically(self, data: pd.DataFrame, split_date: str, symbol: str = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Split data chronologically into in-sample and out-of-sample periods.
        
        Args:
            data (pd.DataFrame): ETF data with Date column
            split_date (str): Date to split data ('YYYY-MM-DD')
            symbol (str): ETF symbol for logging
            
        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]: (in_sample_data, out_of_sample_data)
        """
        if data.empty:
            return pd.DataFrame(), pd.DataFrame()
        
        # Ensure Date column is datetime
        data = data.copy()
        data['Date'] = pd.to_datetime(data['Date'], utc=True)
        split_dt = pd.to_datetime(split_date, utc=True)
        
        # Split data chronologically
        in_sample = data[data['Date'] < split_dt].copy()
        out_of_sample = data[data['Date'] >= split_dt].copy()
        
        # Log split information
        split_info = {
            'symbol': symbol,
            'split_date': split_date,
            'total_rows': len(data),
            'in_sample_rows': len(in_sample),
            'out_of_sample_rows': len(out_of_sample),
            'in_sample_start': in_sample['Date'].min().strftime('%Y-%m-%d') if not in_sample.empty else None,
            'in_sample_end': in_sample['Date'].max().strftime('%Y-%m-%d') if not in_sample.empty else None,
            'out_of_sample_start': out_of_sample['Date'].min().strftime('%Y-%m-%d') if not out_of_sample.empty else None,
            'out_of_sample_end': out_of_sample['Date'].max().strftime('%Y-%m-%d') if not out_of_sample.empty else None,
        }
        
        self.split_history.append(split_info)
        
        return in_sample, out_of_sample
    
    def validate_no_data_leakage(self, in_sample: pd.DataFrame, out_of_sample: pd.DataFrame, symbol: str = None) -> Dict:
        """
        Validate that there's no temporal overlap between in-sample and out-of-sample data.
        
        Args:
            in_sample (pd.DataFrame): In-sample data
            out_of_sample (pd.DataFrame): Out-of-sample data
            symbol (str): ETF symbol for logging
            
        Returns:
            Dict: Validation results
        """
        validation = {
            'symbol': symbol,
            'passed': True,
            'issues': [],
            'in_sample_dates': None,
            'out_of_sample_dates': None,
            'overlap_detected': False
        }
        
        if in_sample.empty or out_of_sample.empty:
            validation['issues'].append('One or both datasets are empty')
            validation['passed'] = False
            return validation
        
        # Get date ranges
        in_sample_start = in_sample['Date'].min()
        in_sample_end = in_sample['Date'].max()
        out_of_sample_start = out_of_sample['Date'].min()
        out_of_sample_end = out_of_sample['Date'].max()
        
        validation['in_sample_dates'] = (in_sample_start.strftime('%Y-%m-%d'), in_sample_end.strftime('%Y-%m-%d'))
        validation['out_of_sample_dates'] = (out_of_sample_start.strftime('%Y-%m-%d'), out_of_sample_end.strftime('%Y-%m-%d'))
        
        # Check for temporal overlap
        if in_sample_end >= out_of_sample_start:
            validation['overlap_detected'] = True
            validation['issues'].append(f'Temporal overlap detected: in-sample ends {in_sample_end.strftime("%Y-%m-%d")}, out-of-sample starts {out_of_sample_start.strftime("%Y-%m-%d")}')
            validation['passed'] = False
        
        # Check for proper chronological order
        if out_of_sample_start <= in_sample_end:
            validation['issues'].append('Out-of-sample data should start after in-sample data ends')
            validation['passed'] = False
        
        # Check for sufficient data in each split
        min_days_required = 90  # At least 3 months for momentum calculation
        
        if len(in_sample) < min_days_required:
            validation['issues'].append(f'Insufficient in-sample data: {len(in_sample)} days (minimum {min_days_required})')
            validation['passed'] = False
        
        if len(out_of_sample) < 30:  # At least 1 month for OOS testing
            validation['issues'].append(f'Insufficient out-of-sample data: {len(out_of_sample)} days (minimum 30)')
            validation['passed'] = False
        
        return validation
    
    def get_training_testing_periods(self, data: pd.DataFrame, split_date: str) -> Dict:
        """
        Get detailed information about training and testing periods.
        
        Args:
            data (pd.DataFrame): Full dataset
            split_date (str): Split date
            
        Returns:
            Dict: Period information
        """
        data_copy = data.copy()
        data_copy['Date'] = pd.to_datetime(data_copy['Date'], utc=True)
        split_dt = pd.to_datetime(split_date, utc=True)
        
        total_start = data_copy['Date'].min()
        total_end = data_copy['Date'].max()
        
        in_sample_data = data_copy[data_copy['Date'] < split_dt]
        out_of_sample_data = data_copy[data_copy['Date'] >= split_dt]
        
        periods_info = {
            'total_period': {
                'start': total_start.strftime('%Y-%m-%d'),
                'end': total_end.strftime('%Y-%m-%d'),
                'duration_days': (total_end - total_start).days,
                'total_observations': len(data_copy)
            },
            'in_sample_period': {
                'start': in_sample_data['Date'].min().strftime('%Y-%m-%d') if not in_sample_data.empty else None,
                'end': in_sample_data['Date'].max().strftime('%Y-%m-%d') if not in_sample_data.empty else None,
                'duration_days': (in_sample_data['Date'].max() - in_sample_data['Date'].min()).days if not in_sample_data.empty else 0,
                'observations': len(in_sample_data),
                'percentage_of_total': len(in_sample_data) / len(data_copy) * 100 if len(data_copy) > 0 else 0
            },
            'out_of_sample_period': {
                'start': out_of_sample_data['Date'].min().strftime('%Y-%m-%d') if not out_of_sample_data.empty else None,
                'end': out_of_sample_data['Date'].max().strftime('%Y-%m-%d') if not out_of_sample_data.empty else None,
                'duration_days': (out_of_sample_data['Date'].max() - out_of_sample_data['Date'].min()).days if not out_of_sample_data.empty else 0,
                'observations': len(out_of_sample_data),
                'percentage_of_total': len(out_of_sample_data) / len(data_copy) * 100 if len(data_copy) > 0 else 0
            },
            'split_date': split_date
        }
        
        return periods_info
    
    def split_multiple_etfs(self, etf_data_dict: Dict[str, pd.DataFrame], split_date: str) -> Tuple[Dict, Dict]:
        """
        Split data for multiple ETFs simultaneously.
        
        Args:
            etf_data_dict (Dict): Dictionary with ETF symbols as keys and DataFrames as values
            split_date (str): Split date
            
        Returns:
            Tuple[Dict, Dict]: (in_sample_dict, out_of_sample_dict)
        """
        in_sample_dict = {}
        out_of_sample_dict = {}
        
        for symbol, data in etf_data_dict.items():
            in_sample, out_of_sample = self.split_data_chronologically(data, split_date, symbol)
            
            # Validate split
            validation = self.validate_no_data_leakage(in_sample, out_of_sample, symbol)
            self.validation_results[symbol] = validation
            
            if validation['passed']:
                in_sample_dict[symbol] = in_sample
                out_of_sample_dict[symbol] = out_of_sample
            else:
                print(f"WARNING: Data split validation failed for {symbol}")
                for issue in validation['issues']:
                    print(f"  - {issue}")
        
        return in_sample_dict, out_of_sample_dict
    
    def get_recommended_split_date(self, data: pd.DataFrame, oos_percentage: float = 0.3) -> str:
        """
        Recommend a split date based on desired out-of-sample percentage.
        
        Args:
            data (pd.DataFrame): Full dataset
            oos_percentage (float): Desired percentage for out-of-sample (0.0 to 1.0)
            
        Returns:
            str: Recommended split date
        """
        if data.empty:
            return None
        
        data_copy = data.copy()
        data_copy['Date'] = pd.to_datetime(data_copy['Date'], utc=True)
        data_copy = data_copy.sort_values('Date')
        
        total_observations = len(data_copy)
        oos_observations = int(total_observations * oos_percentage)
        split_index = total_observations - oos_observations
        
        if split_index >= len(data_copy):
            split_index = len(data_copy) - 1
        
        split_date = data_copy.iloc[split_index]['Date']
        return split_date.strftime('%Y-%m-%d')
    
    def print_split_summary(self):
        """Print summary of all data splits performed."""
        if not self.split_history:
            print("No data splits performed yet.")
            return
        
        print("\n=== DATA SPLIT SUMMARY ===")
        for i, split in enumerate(self.split_history, 1):
            print(f"\nSplit {i}: {split['symbol'] or 'Unknown'}")
            print(f"  Split Date: {split['split_date']}")
            print(f"  Total Rows: {split['total_rows']}")
            print(f"  In-Sample: {split['in_sample_rows']} rows ({split['in_sample_start']} to {split['in_sample_end']})")
            print(f"  Out-of-Sample: {split['out_of_sample_rows']} rows ({split['out_of_sample_start']} to {split['out_of_sample_end']})")
            
            # Show validation results if available
            symbol = split['symbol']
            if symbol in self.validation_results:
                validation = self.validation_results[symbol]
                status = "PASSED" if validation['passed'] else "FAILED"
                print(f"  Validation: {status}")
                if not validation['passed']:
                    for issue in validation['issues']:
                        print(f"    - {issue}")


def test_data_split_manager():
    """Test function to verify data split manager works correctly."""
    
    print("Testing Data Split Manager...")
    
    # Import ETF data fetcher to get test data
    import sys
    sys.path.append('src/data_providers')
    from etf_data_fetcher import ETFDataFetcher
    
    # Load test data
    fetcher = ETFDataFetcher()
    spy_data = fetcher.load_data_from_csv('SPY')
    
    if spy_data.empty:
        print("No SPY data found. Run data fetcher first.")
        return False
    
    # Initialize data split manager
    splitter = DataSplitManager()
    
    print(f"Testing with {len(spy_data)} days of SPY data")
    
    # Test 1: Get recommended split date (70/30 split)
    print(f"\n--- Test 1: Recommended split date ---")
    recommended_split = splitter.get_recommended_split_date(spy_data, oos_percentage=0.3)
    print(f"Recommended split date (30% OOS): {recommended_split}")
    
    # Test 2: Split data chronologically
    print(f"\n--- Test 2: Chronological data split ---")
    split_date = '2025-04-01'  # Use fixed date for testing
    in_sample, out_of_sample = splitter.split_data_chronologically(spy_data, split_date, 'SPY')
    
    print(f"Split at {split_date}:")
    print(f"  In-sample: {len(in_sample)} rows")
    print(f"  Out-of-sample: {len(out_of_sample)} rows")
    
    # Test 3: Validate no data leakage
    print(f"\n--- Test 3: Data leakage validation ---")
    validation = splitter.validate_no_data_leakage(in_sample, out_of_sample, 'SPY')
    print(f"Validation passed: {validation['passed']}")
    if not validation['passed']:
        for issue in validation['issues']:
            print(f"  Issue: {issue}")
    
    # Test 4: Get period information
    print(f"\n--- Test 4: Period information ---")
    periods = splitter.get_training_testing_periods(spy_data, split_date)
    print(f"Total period: {periods['total_period']['start']} to {periods['total_period']['end']}")
    print(f"In-sample: {periods['in_sample_period']['observations']} observations ({periods['in_sample_period']['percentage_of_total']:.1f}%)")
    print(f"Out-of-sample: {periods['out_of_sample_period']['observations']} observations ({periods['out_of_sample_period']['percentage_of_total']:.1f}%)")
    
    # Test 5: Multiple ETF split
    print(f"\n--- Test 5: Multiple ETF split ---")
    qqq_data = fetcher.load_data_from_csv('QQQ')
    iwm_data = fetcher.load_data_from_csv('IWM')
    
    etf_data = {'SPY': spy_data, 'QQQ': qqq_data, 'IWM': iwm_data}
    in_sample_dict, out_of_sample_dict = splitter.split_multiple_etfs(etf_data, split_date)
    
    print(f"Multi-ETF split results:")
    for symbol in ['SPY', 'QQQ', 'IWM']:
        if symbol in in_sample_dict:
            print(f"  {symbol}: {len(in_sample_dict[symbol])} in-sample, {len(out_of_sample_dict[symbol])} out-of-sample")
    
    # Print summary
    splitter.print_split_summary()
    
    return True


if __name__ == "__main__":
    # Run test when script is executed directly
    test_data_split_manager()