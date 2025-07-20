"""
Performance Comparator Module

Statistical comparison between in-sample and out-of-sample performance.
Calculates performance metrics and tests for statistical significance.
Independent module that can be tested separately.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import warnings


class PerformanceComparator:
    """Compares and analyzes performance between different periods or strategies."""
    
    def __init__(self):
        self.comparison_history = []
    
    def calculate_performance_metrics(self, returns: List[float], period_name: str = None) -> Dict:
        """
        Calculate comprehensive performance metrics for a return series.
        
        Args:
            returns (List[float]): List of periodic returns
            period_name (str): Name of the period for reporting
            
        Returns:
            Dict: Performance metrics
        """
        if not returns or len(returns) == 0:
            return {'error': 'No returns provided'}
        
        returns_array = np.array(returns)
        
        # Remove any infinite or NaN values
        returns_clean = returns_array[np.isfinite(returns_array)]
        
        if len(returns_clean) == 0:
            return {'error': 'No valid returns after cleaning'}
        
        metrics = {
            'period_name': period_name,
            'total_observations': len(returns_clean),
            'missing_observations': len(returns) - len(returns_clean)
        }
        
        try:
            # Basic return metrics
            total_return = np.prod(1 + returns_clean) - 1
            mean_return = np.mean(returns_clean)
            median_return = np.median(returns_clean)
            
            # Risk metrics
            volatility = np.std(returns_clean, ddof=1) if len(returns_clean) > 1 else 0
            downside_returns = returns_clean[returns_clean < 0]
            downside_volatility = np.std(downside_returns, ddof=1) if len(downside_returns) > 1 else 0
            
            # Risk-adjusted metrics
            sharpe_ratio = mean_return / volatility if volatility > 0 else 0
            sortino_ratio = mean_return / downside_volatility if downside_volatility > 0 else 0
            
            # Drawdown analysis
            cumulative_returns = np.cumprod(1 + returns_clean)
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdowns = (cumulative_returns - running_max) / running_max
            max_drawdown = np.min(drawdowns)
            
            # Win/Loss analysis
            positive_returns = returns_clean[returns_clean > 0]
            negative_returns = returns_clean[returns_clean < 0]
            win_rate = len(positive_returns) / len(returns_clean) * 100
            
            # Average win/loss
            avg_win = np.mean(positive_returns) if len(positive_returns) > 0 else 0
            avg_loss = np.mean(negative_returns) if len(negative_returns) > 0 else 0
            win_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
            
            # Update metrics dictionary
            metrics.update({
                'total_return': total_return,
                'total_return_pct': total_return * 100,
                'annualized_return': (1 + total_return) ** (252 / len(returns_clean)) - 1 if len(returns_clean) > 0 else 0,
                'mean_return': mean_return,
                'median_return': median_return,
                'volatility': volatility,
                'annualized_volatility': volatility * np.sqrt(252),
                'downside_volatility': downside_volatility,
                'sharpe_ratio': sharpe_ratio,
                'annualized_sharpe': sharpe_ratio * np.sqrt(252),
                'sortino_ratio': sortino_ratio,
                'max_drawdown': max_drawdown,
                'max_drawdown_pct': max_drawdown * 100,
                'win_rate': win_rate,
                'average_win': avg_win,
                'average_loss': avg_loss,
                'win_loss_ratio': win_loss_ratio,
                'positive_periods': len(positive_returns),
                'negative_periods': len(negative_returns),
                'best_return': np.max(returns_clean),
                'worst_return': np.min(returns_clean),
                'skewness': self._calculate_skewness(returns_clean),
                'kurtosis': self._calculate_kurtosis(returns_clean)
            })
            
        except Exception as e:
            metrics['error'] = f'Error calculating metrics: {str(e)}'
        
        return metrics
    
    def _calculate_skewness(self, returns: np.ndarray) -> float:
        """Calculate skewness of returns."""
        if len(returns) < 3:
            return 0
        
        mean_return = np.mean(returns)
        std_return = np.std(returns, ddof=1)
        
        if std_return == 0:
            return 0
        
        skewness = np.mean(((returns - mean_return) / std_return) ** 3)
        return skewness
    
    def _calculate_kurtosis(self, returns: np.ndarray) -> float:
        """Calculate excess kurtosis of returns."""
        if len(returns) < 4:
            return 0
        
        mean_return = np.mean(returns)
        std_return = np.std(returns, ddof=1)
        
        if std_return == 0:
            return 0
        
        kurtosis = np.mean(((returns - mean_return) / std_return) ** 4) - 3
        return kurtosis
    
    def compare_in_sample_vs_oos(self, is_results: Dict, oos_results: Dict) -> Dict:
        """
        Compare in-sample vs out-of-sample performance.
        
        Args:
            is_results (Dict): In-sample backtest results
            oos_results (Dict): Out-of-sample backtest results
            
        Returns:
            Dict: Detailed comparison analysis
        """
        comparison = {
            'comparison_date': datetime.now().isoformat(),
            'in_sample_period': None,
            'out_of_sample_period': None,
            'performance_comparison': {},
            'statistical_tests': {},
            'degradation_analysis': {},
            'risk_analysis': {},
            'consistency_analysis': {}
        }
        
        # Extract returns for both periods
        if 'daily_returns' in is_results:
            is_returns = is_results['daily_returns']
        elif 'portfolio_values' in is_results:
            is_returns = self._calculate_returns_from_values(is_results['portfolio_values'])
        else:
            comparison['error'] = 'Cannot extract in-sample returns'
            return comparison
        
        if 'daily_returns' in oos_results:
            oos_returns = oos_results['daily_returns']
        elif 'portfolio_values' in oos_results:
            oos_returns = self._calculate_returns_from_values(oos_results['portfolio_values'])
        else:
            comparison['error'] = 'Cannot extract out-of-sample returns'
            return comparison
        
        # Calculate metrics for both periods
        is_metrics = self.calculate_performance_metrics(is_returns, 'In-Sample')
        oos_metrics = self.calculate_performance_metrics(oos_returns, 'Out-of-Sample')
        
        if 'error' in is_metrics or 'error' in oos_metrics:
            comparison['error'] = f"Metrics calculation failed: IS={is_metrics.get('error', 'OK')}, OOS={oos_metrics.get('error', 'OK')}"
            return comparison
        
        # Store period information
        comparison['in_sample_period'] = {
            'start_date': is_results.get('start_date'),
            'end_date': is_results.get('end_date'),
            'observations': is_metrics['total_observations']
        }
        
        comparison['out_of_sample_period'] = {
            'start_date': oos_results.get('start_date'),
            'end_date': oos_results.get('end_date'),
            'observations': oos_metrics['total_observations']
        }
        
        # Performance comparison
        comparison['performance_comparison'] = self._compare_metrics(is_metrics, oos_metrics)
        
        # Statistical significance tests
        comparison['statistical_tests'] = self.statistical_significance_test(is_returns, oos_returns)
        
        # Performance degradation analysis
        comparison['degradation_analysis'] = self._analyze_degradation(is_metrics, oos_metrics)
        
        # Risk analysis
        comparison['risk_analysis'] = self._analyze_risk_changes(is_metrics, oos_metrics)
        
        # Consistency analysis
        comparison['consistency_analysis'] = self._analyze_consistency(is_metrics, oos_metrics)
        
        # Store comparison
        self.comparison_history.append(comparison)
        
        return comparison
    
    def _calculate_returns_from_values(self, portfolio_values: List[float]) -> List[float]:
        """Calculate returns from portfolio values."""
        if len(portfolio_values) < 2:
            return []
        
        returns = []
        for i in range(1, len(portfolio_values)):
            if portfolio_values[i-1] > 0:
                ret = (portfolio_values[i] / portfolio_values[i-1]) - 1
                returns.append(ret)
        
        return returns
    
    def _compare_metrics(self, is_metrics: Dict, oos_metrics: Dict) -> Dict:
        """Compare key metrics between periods."""
        key_metrics = [
            'total_return_pct', 'annualized_return', 'annualized_volatility',
            'annualized_sharpe', 'max_drawdown_pct', 'win_rate'
        ]
        
        comparison = {}
        
        for metric in key_metrics:
            if metric in is_metrics and metric in oos_metrics:
                is_value = is_metrics[metric]
                oos_value = oos_metrics[metric]
                
                comparison[metric] = {
                    'in_sample': is_value,
                    'out_of_sample': oos_value,
                    'difference': oos_value - is_value,
                    'percentage_change': ((oos_value / is_value) - 1) * 100 if is_value != 0 else 0
                }
        
        return comparison
    
    def _analyze_degradation(self, is_metrics: Dict, oos_metrics: Dict) -> Dict:
        """Analyze performance degradation from IS to OOS."""
        degradation = {
            'return_degradation': 0,
            'sharpe_degradation': 0,
            'drawdown_increase': 0,
            'volatility_increase': 0,
            'overall_degradation_score': 0
        }
        
        # Return degradation
        if 'total_return_pct' in is_metrics and 'total_return_pct' in oos_metrics:
            degradation['return_degradation'] = is_metrics['total_return_pct'] - oos_metrics['total_return_pct']
        
        # Sharpe ratio degradation
        if 'annualized_sharpe' in is_metrics and 'annualized_sharpe' in oos_metrics:
            degradation['sharpe_degradation'] = is_metrics['annualized_sharpe'] - oos_metrics['annualized_sharpe']
        
        # Drawdown increase (negative is worse)
        if 'max_drawdown_pct' in is_metrics and 'max_drawdown_pct' in oos_metrics:
            degradation['drawdown_increase'] = oos_metrics['max_drawdown_pct'] - is_metrics['max_drawdown_pct']
        
        # Volatility increase
        if 'annualized_volatility' in is_metrics and 'annualized_volatility' in oos_metrics:
            degradation['volatility_increase'] = oos_metrics['annualized_volatility'] - is_metrics['annualized_volatility']
        
        # Overall degradation score (higher is worse)
        degradation['overall_degradation_score'] = (
            degradation['return_degradation'] * 0.4 +
            degradation['sharpe_degradation'] * 0.3 +
            abs(degradation['drawdown_increase']) * 0.2 +
            degradation['volatility_increase'] * 0.1
        )
        
        return degradation
    
    def _analyze_risk_changes(self, is_metrics: Dict, oos_metrics: Dict) -> Dict:
        """Analyze changes in risk characteristics."""
        risk_analysis = {
            'volatility_change': 0,
            'downside_risk_change': 0,
            'tail_risk_change': 0,
            'risk_adjusted_performance_change': 0
        }
        
        # Volatility change
        if 'annualized_volatility' in is_metrics and 'annualized_volatility' in oos_metrics:
            is_vol = is_metrics['annualized_volatility']
            oos_vol = oos_metrics['annualized_volatility']
            risk_analysis['volatility_change'] = ((oos_vol / is_vol) - 1) * 100 if is_vol > 0 else 0
        
        # Downside risk change
        if 'downside_volatility' in is_metrics and 'downside_volatility' in oos_metrics:
            is_down = is_metrics['downside_volatility']
            oos_down = oos_metrics['downside_volatility']
            risk_analysis['downside_risk_change'] = ((oos_down / is_down) - 1) * 100 if is_down > 0 else 0
        
        # Tail risk (worst return)
        if 'worst_return' in is_metrics and 'worst_return' in oos_metrics:
            risk_analysis['tail_risk_change'] = oos_metrics['worst_return'] - is_metrics['worst_return']
        
        # Risk-adjusted performance change
        if 'annualized_sharpe' in is_metrics and 'annualized_sharpe' in oos_metrics:
            is_sharpe = is_metrics['annualized_sharpe']
            oos_sharpe = oos_metrics['annualized_sharpe']
            risk_analysis['risk_adjusted_performance_change'] = ((oos_sharpe / is_sharpe) - 1) * 100 if is_sharpe > 0 else 0
        
        return risk_analysis
    
    def _analyze_consistency(self, is_metrics: Dict, oos_metrics: Dict) -> Dict:
        """Analyze consistency between periods."""
        consistency = {
            'win_rate_consistency': 0,
            'return_distribution_similarity': 0,
            'risk_profile_consistency': 0,
            'overall_consistency_score': 0
        }
        
        # Win rate consistency
        if 'win_rate' in is_metrics and 'win_rate' in oos_metrics:
            consistency['win_rate_consistency'] = abs(is_metrics['win_rate'] - oos_metrics['win_rate'])
        
        # Risk profile consistency (based on Sharpe ratio similarity)
        if 'annualized_sharpe' in is_metrics and 'annualized_sharpe' in oos_metrics:
            sharpe_diff = abs(is_metrics['annualized_sharpe'] - oos_metrics['annualized_sharpe'])
            consistency['risk_profile_consistency'] = max(0, 100 - sharpe_diff * 50)  # Scale to 0-100
        
        # Overall consistency score (higher is more consistent)
        consistency['overall_consistency_score'] = (
            (100 - consistency['win_rate_consistency']) * 0.5 +
            consistency['risk_profile_consistency'] * 0.5
        )
        
        return consistency
    
    def statistical_significance_test(self, returns1: List[float], returns2: List[float]) -> Dict:
        """
        Test for statistical significance between two return series.
        
        Args:
            returns1 (List[float]): First return series (in-sample)
            returns2 (List[float]): Second return series (out-of-sample)
            
        Returns:
            Dict: Statistical test results
        """
        test_results = {
            'mean_difference_test': {},
            'variance_difference_test': {},
            'distribution_test': {}
        }
        
        if len(returns1) < 2 or len(returns2) < 2:
            test_results['error'] = 'Insufficient data for statistical tests'
            return test_results
        
        returns1_clean = np.array([r for r in returns1 if np.isfinite(r)])
        returns2_clean = np.array([r for r in returns2 if np.isfinite(r)])
        
        # Simple mean difference test (approximating t-test)
        mean1 = np.mean(returns1_clean)
        mean2 = np.mean(returns2_clean)
        var1 = np.var(returns1_clean, ddof=1) if len(returns1_clean) > 1 else 0
        var2 = np.var(returns2_clean, ddof=1) if len(returns2_clean) > 1 else 0
        
        # Pooled standard error
        n1, n2 = len(returns1_clean), len(returns2_clean)
        pooled_se = np.sqrt(var1/n1 + var2/n2) if n1 > 0 and n2 > 0 else 0
        
        if pooled_se > 0:
            t_statistic = (mean1 - mean2) / pooled_se
            # Approximate p-value using normal distribution (for large samples)
            from math import erfc
            p_value = erfc(abs(t_statistic) / np.sqrt(2))
        else:
            t_statistic = 0
            p_value = 1
        
        test_results['mean_difference_test'] = {
            'mean_1': mean1,
            'mean_2': mean2,
            'difference': mean1 - mean2,
            't_statistic': t_statistic,
            'p_value': p_value,
            'significant_at_5pct': p_value < 0.05
        }
        
        # Variance comparison (F-test approximation)
        if var1 > 0 and var2 > 0:
            f_statistic = var1 / var2 if var1 > var2 else var2 / var1
            test_results['variance_difference_test'] = {
                'variance_1': var1,
                'variance_2': var2,
                'f_statistic': f_statistic,
                'variance_ratio': var2 / var1
            }
        
        return test_results
    
    def print_comparison_report(self, comparison: Dict):
        """Print detailed comparison report."""
        print("\n=== PERFORMANCE COMPARISON REPORT ===")
        
        if 'error' in comparison:
            print(f"Error: {comparison['error']}")
            return
        
        # Period information
        print(f"\nPERIODS:")
        is_period = comparison['in_sample_period']
        oos_period = comparison['out_of_sample_period']
        print(f"  In-Sample: {is_period['start_date']} to {is_period['end_date']} ({is_period['observations']} obs)")
        print(f"  Out-of-Sample: {oos_period['start_date']} to {oos_period['end_date']} ({oos_period['observations']} obs)")
        
        # Performance comparison
        print(f"\nPERFORMANCE METRICS:")
        perf_comp = comparison['performance_comparison']
        for metric, values in perf_comp.items():
            print(f"  {metric}:")
            print(f"    In-Sample: {values['in_sample']:.4f}")
            print(f"    Out-of-Sample: {values['out_of_sample']:.4f}")
            print(f"    Difference: {values['difference']:.4f} ({values['percentage_change']:.1f}%)")
        
        # Degradation analysis
        print(f"\nDEGRADATION ANALYSIS:")
        degradation = comparison['degradation_analysis']
        print(f"  Return Degradation: {degradation['return_degradation']:.2f}%")
        print(f"  Sharpe Degradation: {degradation['sharpe_degradation']:.4f}")
        print(f"  Overall Degradation Score: {degradation['overall_degradation_score']:.4f}")
        
        # Statistical tests
        print(f"\nSTATISTICAL TESTS:")
        if 'mean_difference_test' in comparison['statistical_tests']:
            mean_test = comparison['statistical_tests']['mean_difference_test']
            print(f"  Mean Difference: {mean_test['difference']:.6f}")
            print(f"  T-Statistic: {mean_test['t_statistic']:.4f}")
            print(f"  P-Value: {mean_test['p_value']:.4f}")
            print(f"  Significant at 5%: {mean_test['significant_at_5pct']}")


def test_performance_comparator():
    """Test function to verify performance comparator works correctly."""
    
    print("Testing Performance Comparator...")
    
    # Initialize comparator
    comparator = PerformanceComparator()
    
    # Test 1: Calculate performance metrics
    print(f"\n--- Test 1: Performance metrics calculation ---")
    
    # Generate sample returns
    np.random.seed(42)
    sample_returns = np.random.normal(0.001, 0.02, 100)  # Daily returns
    
    metrics = comparator.calculate_performance_metrics(sample_returns.tolist(), 'Test Period')
    
    print(f"Sample metrics for {metrics['total_observations']} observations:")
    print(f"  Total Return: {metrics['total_return_pct']:.2f}%")
    print(f"  Annualized Sharpe: {metrics['annualized_sharpe']:.4f}")
    print(f"  Max Drawdown: {metrics['max_drawdown_pct']:.2f}%")
    print(f"  Win Rate: {metrics['win_rate']:.1f}%")
    
    # Test 2: Compare in-sample vs out-of-sample
    print(f"\n--- Test 2: In-sample vs out-of-sample comparison ---")
    
    # Simulate in-sample (better performance)
    is_returns = np.random.normal(0.002, 0.015, 150)  # Higher mean, lower vol
    oos_returns = np.random.normal(0.001, 0.02, 75)   # Lower mean, higher vol
    
    is_results = {
        'start_date': '2024-01-01',
        'end_date': '2024-06-30',
        'daily_returns': is_returns.tolist()
    }
    
    oos_results = {
        'start_date': '2024-07-01',
        'end_date': '2024-12-31',
        'daily_returns': oos_returns.tolist()
    }
    
    comparison = comparator.compare_in_sample_vs_oos(is_results, oos_results)
    
    # Test 3: Statistical significance
    print(f"\n--- Test 3: Statistical significance test ---")
    
    stat_tests = comparator.statistical_significance_test(is_returns.tolist(), oos_returns.tolist())
    print(f"Mean difference: {stat_tests['mean_difference_test']['difference']:.6f}")
    print(f"P-value: {stat_tests['mean_difference_test']['p_value']:.4f}")
    print(f"Significant at 5%: {stat_tests['mean_difference_test']['significant_at_5pct']}")
    
    # Test 4: Print full comparison report
    print(f"\n--- Test 4: Full comparison report ---")
    comparator.print_comparison_report(comparison)
    
    return True


if __name__ == "__main__":
    # Run test when script is executed directly
    test_performance_comparator()