"""
Out-of-Sample Validator Module

Ensures strategy parameters aren't modified during out-of-sample testing.
Prevents parameter optimization on future data and maintains scientific rigor.
Independent module that can be tested separately.
"""

import json
import hashlib
from typing import Dict, List, Any, Tuple
from datetime import datetime


class OutOfSampleValidator:
    """Validates that strategy parameters remain unchanged during OOS testing."""
    
    def __init__(self):
        self.parameter_snapshots = {}
        self.validation_log = []
    
    def capture_strategy_parameters(self, strategy_name: str, parameters: Dict) -> str:
        """
        Capture and hash strategy parameters to detect any changes.
        
        Args:
            strategy_name (str): Name of the strategy
            parameters (Dict): Strategy parameters to capture
            
        Returns:
            str: Hash of the parameters for future validation
        """
        # Create a consistent string representation of parameters
        param_str = json.dumps(parameters, sort_keys=True, separators=(',', ':'))
        param_hash = hashlib.md5(param_str.encode()).hexdigest()
        
        snapshot = {
            'strategy_name': strategy_name,
            'parameters': parameters.copy(),
            'parameter_hash': param_hash,
            'captured_at': datetime.now().isoformat(),
            'param_string': param_str
        }
        
        self.parameter_snapshots[strategy_name] = snapshot
        
        return param_hash
    
    def validate_parameters_unchanged(self, strategy_name: str, current_parameters: Dict) -> Dict:
        """
        Validate that current parameters match the captured snapshot.
        
        Args:
            strategy_name (str): Name of the strategy
            current_parameters (Dict): Current parameters to validate
            
        Returns:
            Dict: Validation results
        """
        validation_result = {
            'strategy_name': strategy_name,
            'validation_passed': False,
            'parameter_changes': [],
            'current_hash': None,
            'original_hash': None,
            'validated_at': datetime.now().isoformat()
        }
        
        if strategy_name not in self.parameter_snapshots:
            validation_result['parameter_changes'].append('No parameter snapshot found for this strategy')
            self.validation_log.append(validation_result)
            return validation_result
        
        original_snapshot = self.parameter_snapshots[strategy_name]
        original_params = original_snapshot['parameters']
        original_hash = original_snapshot['parameter_hash']
        
        # Calculate current hash
        current_param_str = json.dumps(current_parameters, sort_keys=True, separators=(',', ':'))
        current_hash = hashlib.md5(current_param_str.encode()).hexdigest()
        
        validation_result['current_hash'] = current_hash
        validation_result['original_hash'] = original_hash
        
        # Check if hashes match (quick check)
        if current_hash == original_hash:
            validation_result['validation_passed'] = True
        else:
            # Detailed comparison to identify specific changes
            changes = self._compare_parameters(original_params, current_parameters)
            validation_result['parameter_changes'] = changes
        
        self.validation_log.append(validation_result)
        return validation_result
    
    def _compare_parameters(self, original: Dict, current: Dict) -> List[str]:
        """
        Compare two parameter dictionaries and identify differences.
        
        Args:
            original (Dict): Original parameters
            current (Dict): Current parameters
            
        Returns:
            List[str]: List of changes detected
        """
        changes = []
        
        # Check for removed parameters
        for key in original:
            if key not in current:
                changes.append(f"Parameter '{key}' was removed")
        
        # Check for added parameters
        for key in current:
            if key not in original:
                changes.append(f"Parameter '{key}' was added with value {current[key]}")
        
        # Check for modified parameters
        for key in original:
            if key in current and original[key] != current[key]:
                changes.append(f"Parameter '{key}' changed from {original[key]} to {current[key]}")
        
        return changes
    
    def check_strategy_consistency(self, strategy_configs: List[Dict]) -> Dict:
        """
        Check consistency across multiple strategy configurations.
        
        Args:
            strategy_configs (List[Dict]): List of strategy configurations to compare
            
        Returns:
            Dict: Consistency check results
        """
        consistency_result = {
            'consistent': True,
            'total_configs': len(strategy_configs),
            'inconsistencies': [],
            'checked_at': datetime.now().isoformat()
        }
        
        if len(strategy_configs) < 2:
            consistency_result['inconsistencies'].append('Need at least 2 configurations to check consistency')
            consistency_result['consistent'] = False
            return consistency_result
        
        # Use first config as reference
        reference_config = strategy_configs[0]
        reference_keys = set(reference_config.keys())
        
        for i, config in enumerate(strategy_configs[1:], 1):
            config_keys = set(config.keys())
            
            # Check for missing keys
            missing_keys = reference_keys - config_keys
            if missing_keys:
                consistency_result['inconsistencies'].append(f"Config {i} missing keys: {list(missing_keys)}")
                consistency_result['consistent'] = False
            
            # Check for extra keys
            extra_keys = config_keys - reference_keys
            if extra_keys:
                consistency_result['inconsistencies'].append(f"Config {i} has extra keys: {list(extra_keys)}")
                consistency_result['consistent'] = False
            
            # Check for value differences
            for key in reference_keys.intersection(config_keys):
                if reference_config[key] != config[key]:
                    consistency_result['inconsistencies'].append(f"Config {i} key '{key}': {reference_config[key]} != {config[key]}")
                    consistency_result['consistent'] = False
        
        return consistency_result
    
    def verify_no_optimization_on_oos_data(self, parameter_history: List[Dict], oos_start_date: str) -> Dict:
        """
        Verify that no parameter optimization occurred on out-of-sample data.
        
        Args:
            parameter_history (List[Dict]): History of parameter changes with timestamps
            oos_start_date (str): Start date of out-of-sample period
            
        Returns:
            Dict: Verification results
        """
        verification_result = {
            'no_oos_optimization': True,
            'violations': [],
            'oos_start_date': oos_start_date,
            'parameter_changes_count': len(parameter_history),
            'verified_at': datetime.now().isoformat()
        }
        
        oos_start_dt = datetime.fromisoformat(oos_start_date.replace('Z', '+00:00')) if 'T' in oos_start_date else datetime.strptime(oos_start_date, '%Y-%m-%d')
        
        for i, param_change in enumerate(parameter_history):
            change_date_str = param_change.get('timestamp', param_change.get('date', ''))
            
            if not change_date_str:
                verification_result['violations'].append(f"Parameter change {i} has no timestamp")
                verification_result['no_oos_optimization'] = False
                continue
            
            try:
                # Handle different timestamp formats
                if 'T' in change_date_str:
                    change_date = datetime.fromisoformat(change_date_str.replace('Z', '+00:00'))
                else:
                    change_date = datetime.strptime(change_date_str, '%Y-%m-%d')
                
                if change_date >= oos_start_dt:
                    verification_result['violations'].append(f"Parameter optimization detected on {change_date_str} (after OOS start)")
                    verification_result['no_oos_optimization'] = False
            
            except ValueError as e:
                verification_result['violations'].append(f"Invalid timestamp format in parameter change {i}: {change_date_str}")
                verification_result['no_oos_optimization'] = False
        
        return verification_result
    
    def create_parameter_lock(self, strategy_name: str, parameters: Dict) -> Dict:
        """
        Create a parameter lock that can be used to ensure no changes during OOS testing.
        
        Args:
            strategy_name (str): Name of the strategy
            parameters (Dict): Parameters to lock
            
        Returns:
            Dict: Parameter lock information
        """
        param_hash = self.capture_strategy_parameters(strategy_name, parameters)
        
        lock_info = {
            'strategy_name': strategy_name,
            'locked_parameters': parameters.copy(),
            'lock_hash': param_hash,
            'locked_at': datetime.now().isoformat(),
            'lock_purpose': 'out_of_sample_validation'
        }
        
        return lock_info
    
    def validate_against_lock(self, lock_info: Dict, current_parameters: Dict) -> Dict:
        """
        Validate current parameters against a parameter lock.
        
        Args:
            lock_info (Dict): Parameter lock information
            current_parameters (Dict): Current parameters to validate
            
        Returns:
            Dict: Lock validation results
        """
        validation = {
            'lock_valid': False,
            'strategy_name': lock_info['strategy_name'],
            'violations': [],
            'validated_at': datetime.now().isoformat()
        }
        
        locked_params = lock_info['locked_parameters']
        
        # Compare parameters
        changes = self._compare_parameters(locked_params, current_parameters)
        
        if not changes:
            validation['lock_valid'] = True
        else:
            validation['violations'] = changes
        
        return validation
    
    def get_validation_summary(self) -> Dict:
        """
        Get summary of all validations performed.
        
        Returns:
            Dict: Validation summary
        """
        if not self.validation_log:
            return {
                'total_validations': 0,
                'passed_validations': 0,
                'failed_validations': 0,
                'failure_rate': 0.0
            }
        
        passed = sum(1 for v in self.validation_log if v['validation_passed'])
        failed = len(self.validation_log) - passed
        
        return {
            'total_validations': len(self.validation_log),
            'passed_validations': passed,
            'failed_validations': failed,
            'failure_rate': failed / len(self.validation_log) * 100,
            'strategies_validated': list(set(v['strategy_name'] for v in self.validation_log))
        }
    
    def print_validation_report(self):
        """Print detailed validation report."""
        print("\n=== OUT-OF-SAMPLE VALIDATION REPORT ===")
        
        summary = self.get_validation_summary()
        print(f"Total Validations: {summary['total_validations']}")
        print(f"Passed: {summary['passed_validations']}")
        print(f"Failed: {summary['failed_validations']}")
        print(f"Failure Rate: {summary['failure_rate']:.1f}%")
        
        if summary['strategies_validated']:
            print(f"Strategies: {', '.join(summary['strategies_validated'])}")
        
        # Show failed validations
        failed_validations = [v for v in self.validation_log if not v['validation_passed']]
        
        if failed_validations:
            print(f"\nFAILED VALIDATIONS:")
            for validation in failed_validations:
                print(f"  Strategy: {validation['strategy_name']}")
                print(f"  Time: {validation['validated_at']}")
                for change in validation['parameter_changes']:
                    print(f"    - {change}")


def test_oos_validator():
    """Test function to verify OOS validator works correctly."""
    
    print("Testing Out-of-Sample Validator...")
    
    # Initialize validator
    validator = OutOfSampleValidator()
    
    # Test 1: Capture momentum strategy parameters
    print(f"\n--- Test 1: Capture strategy parameters ---")
    momentum_params = {
        'periods': [30, 90, 180],
        'weights': [0.5, 0.3, 0.2],
        'transaction_cost_pct': 0.001,
        'rebalance_frequency': 'monthly',
        'etf_symbols': ['SPY', 'QQQ', 'IWM']
    }
    
    param_hash = validator.capture_strategy_parameters('momentum_strategy', momentum_params)
    print(f"Captured parameters with hash: {param_hash}")
    
    # Test 2: Validate unchanged parameters (should pass)
    print(f"\n--- Test 2: Validate unchanged parameters ---")
    validation_result = validator.validate_parameters_unchanged('momentum_strategy', momentum_params)
    print(f"Validation passed: {validation_result['validation_passed']}")
    
    # Test 3: Validate changed parameters (should fail)
    print(f"\n--- Test 3: Validate changed parameters ---")
    modified_params = momentum_params.copy()
    modified_params['transaction_cost_pct'] = 0.002  # Changed transaction cost
    modified_params['periods'] = [20, 60, 120]  # Changed periods
    
    validation_result = validator.validate_parameters_unchanged('momentum_strategy', modified_params)
    print(f"Validation passed: {validation_result['validation_passed']}")
    if not validation_result['validation_passed']:
        print("Parameter changes detected:")
        for change in validation_result['parameter_changes']:
            print(f"  - {change}")
    
    # Test 4: Strategy consistency check
    print(f"\n--- Test 4: Strategy consistency check ---")
    config1 = {'param_a': 1, 'param_b': 2}
    config2 = {'param_a': 1, 'param_b': 2}  # Same as config1
    config3 = {'param_a': 1, 'param_b': 3}  # Different param_b
    
    consistency = validator.check_strategy_consistency([config1, config2, config3])
    print(f"Consistency check passed: {consistency['consistent']}")
    if not consistency['consistent']:
        for inconsistency in consistency['inconsistencies']:
            print(f"  - {inconsistency}")
    
    # Test 5: Parameter lock
    print(f"\n--- Test 5: Parameter lock ---")
    lock_info = validator.create_parameter_lock('momentum_strategy', momentum_params)
    print(f"Created parameter lock at: {lock_info['locked_at']}")
    
    # Test lock validation
    lock_validation = validator.validate_against_lock(lock_info, momentum_params)
    print(f"Lock validation passed: {lock_validation['lock_valid']}")
    
    lock_validation_fail = validator.validate_against_lock(lock_info, modified_params)
    print(f"Lock validation with modified params passed: {lock_validation_fail['lock_valid']}")
    if not lock_validation_fail['lock_valid']:
        print("Lock violations:")
        for violation in lock_validation_fail['violations']:
            print(f"  - {violation}")
    
    # Test 6: OOS optimization check
    print(f"\n--- Test 6: OOS optimization verification ---")
    parameter_history = [
        {'timestamp': '2024-12-01T10:00:00', 'change': 'Initial parameters'},
        {'timestamp': '2025-01-15T14:30:00', 'change': 'Adjusted weights'},  # Before OOS
        {'timestamp': '2025-05-01T09:00:00', 'change': 'Modified periods'},   # After OOS starts
    ]
    
    oos_verification = validator.verify_no_optimization_on_oos_data(parameter_history, '2025-04-01')
    print(f"No OOS optimization: {oos_verification['no_oos_optimization']}")
    if not oos_verification['no_oos_optimization']:
        print("OOS optimization violations:")
        for violation in oos_verification['violations']:
            print(f"  - {violation}")
    
    # Print summary report
    validator.print_validation_report()
    
    return True


if __name__ == "__main__":
    # Run test when script is executed directly
    test_oos_validator()