"""
Portfolio Manager Module

Handles portfolio positions, rebalancing, and transaction cost calculations.
Independent module that can be tested separately.
"""

import pandas as pd
from datetime import datetime


class PortfolioManager:
    """Manages portfolio positions and rebalancing for momentum strategy."""
    
    def __init__(self, initial_capital=100000, transaction_cost_pct=0.001):
        """
        Initialize portfolio manager.
        
        Args:
            initial_capital (float): Starting capital in dollars
            transaction_cost_pct (float): Transaction cost as percentage (0.001 = 0.1%)
        """
        self.initial_capital = initial_capital
        self.transaction_cost_pct = transaction_cost_pct
        self.current_position = None  # ETF symbol currently held
        self.current_shares = 0
        self.current_cash = initial_capital
        self.portfolio_value = initial_capital
        self.transaction_log = []
        
    def get_current_position(self):
        """
        Get current portfolio position.
        
        Returns:
            dict: Current position details
        """
        return {
            "symbol": self.current_position,
            "shares": self.current_shares,
            "cash": self.current_cash,
            "portfolio_value": self.portfolio_value,
            "total_transactions": len(self.transaction_log)
        }
    
    def calculate_transaction_cost(self, trade_value):
        """
        Calculate transaction cost for a trade.
        
        Args:
            trade_value (float): Dollar value of the trade
            
        Returns:
            float: Transaction cost in dollars
        """
        return abs(trade_value) * self.transaction_cost_pct
    
    def update_portfolio_value(self, current_prices):
        """
        Update portfolio value based on current prices.
        
        Args:
            current_prices (dict): Dictionary with symbol: price pairs
            
        Returns:
            float: Updated portfolio value
        """
        if self.current_position is None:
            # All cash
            self.portfolio_value = self.current_cash
        else:
            # Cash + position value
            if self.current_position in current_prices:
                position_value = self.current_shares * current_prices[self.current_position]
                self.portfolio_value = self.current_cash + position_value
            else:
                # Price not available, keep previous value
                pass
        
        return self.portfolio_value
    
    def sell_current_position(self, current_price, date):
        """
        Sell current position if any.
        
        Args:
            current_price (float): Current price of the held ETF
            date (str): Date of the transaction
            
        Returns:
            dict: Transaction details
        """
        if self.current_position is None or self.current_shares == 0:
            return {"status": "no_position", "message": "No position to sell"}
        
        # Calculate proceeds from sale
        gross_proceeds = self.current_shares * current_price
        transaction_cost = self.calculate_transaction_cost(gross_proceeds)
        net_proceeds = gross_proceeds - transaction_cost
        
        # Record transaction
        transaction = {
            "date": date,
            "action": "SELL",
            "symbol": self.current_position,
            "shares": self.current_shares,
            "price": current_price,
            "gross_amount": gross_proceeds,
            "transaction_cost": transaction_cost,
            "net_amount": net_proceeds
        }
        
        self.transaction_log.append(transaction)
        
        # Update portfolio
        self.current_cash += net_proceeds
        previous_position = self.current_position
        self.current_position = None
        self.current_shares = 0
        
        return {
            "status": "success",
            "previous_position": previous_position,
            "proceeds": net_proceeds,
            "transaction_cost": transaction_cost,
            "new_cash": self.current_cash
        }
    
    def buy_etf_position(self, symbol, price, date):
        """
        Buy new ETF position with all available cash.
        
        Args:
            symbol (str): ETF symbol to buy
            price (float): Current price of the ETF
            date (str): Date of the transaction
            
        Returns:
            dict: Transaction details
        """
        if self.current_cash <= 0:
            return {"status": "error", "message": "No cash available"}
        
        # Calculate shares to buy (leave some cash for transaction costs)
        estimated_cost = self.current_cash * self.transaction_cost_pct
        available_for_shares = self.current_cash - estimated_cost
        
        if available_for_shares <= 0:
            return {"status": "error", "message": "Insufficient cash for transaction costs"}
        
        shares_to_buy = int(available_for_shares / price)  # Whole shares only
        
        if shares_to_buy <= 0:
            return {"status": "error", "message": f"Insufficient cash to buy 1 share at ${price:.2f}"}
        
        # Calculate actual costs
        gross_cost = shares_to_buy * price
        transaction_cost = self.calculate_transaction_cost(gross_cost)
        total_cost = gross_cost + transaction_cost
        
        if total_cost > self.current_cash:
            # Reduce shares by 1 and try again
            shares_to_buy -= 1
            if shares_to_buy <= 0:
                return {"status": "error", "message": "Cannot afford any shares after transaction costs"}
            
            gross_cost = shares_to_buy * price
            transaction_cost = self.calculate_transaction_cost(gross_cost)
            total_cost = gross_cost + transaction_cost
        
        # Record transaction
        transaction = {
            "date": date,
            "action": "BUY",
            "symbol": symbol,
            "shares": shares_to_buy,
            "price": price,
            "gross_amount": gross_cost,
            "transaction_cost": transaction_cost,
            "net_amount": total_cost
        }
        
        self.transaction_log.append(transaction)
        
        # Update portfolio
        self.current_cash -= total_cost
        self.current_position = symbol
        self.current_shares = shares_to_buy
        
        return {
            "status": "success",
            "symbol": symbol,
            "shares": shares_to_buy,
            "cost": total_cost,
            "transaction_cost": transaction_cost,
            "remaining_cash": self.current_cash
        }
    
    def rebalance_to_etf(self, target_symbol, current_prices, date):
        """
        Rebalance portfolio to target ETF.
        
        Args:
            target_symbol (str): ETF symbol to switch to
            current_prices (dict): Dictionary with current prices
            date (str): Date of rebalancing
            
        Returns:
            dict: Rebalancing results
        """
        rebalance_results = {
            "date": date,
            "target_symbol": target_symbol,
            "actions": [],
            "success": False
        }
        
        # Check if target price is available
        if target_symbol not in current_prices:
            rebalance_results["error"] = f"Price not available for {target_symbol}"
            return rebalance_results
        
        target_price = current_prices[target_symbol]
        
        # If already holding the target ETF, no action needed
        if self.current_position == target_symbol:
            rebalance_results["actions"].append("no_change")
            rebalance_results["success"] = True
            rebalance_results["message"] = f"Already holding {target_symbol}"
            return rebalance_results
        
        # Step 1: Sell current position if any
        if self.current_position is not None:
            current_price = current_prices.get(self.current_position)
            if current_price is None:
                rebalance_results["error"] = f"Price not available for current position {self.current_position}"
                return rebalance_results
            
            sell_result = self.sell_current_position(current_price, date)
            rebalance_results["actions"].append({"sell": sell_result})
            
            if sell_result["status"] != "success":
                rebalance_results["error"] = f"Failed to sell current position: {sell_result}"
                return rebalance_results
        
        # Step 2: Buy target ETF
        buy_result = self.buy_etf_position(target_symbol, target_price, date)
        rebalance_results["actions"].append({"buy": buy_result})
        
        if buy_result["status"] == "success":
            rebalance_results["success"] = True
            rebalance_results["new_position"] = {
                "symbol": target_symbol,
                "shares": buy_result["shares"],
                "cost": buy_result["cost"]
            }
        else:
            rebalance_results["error"] = f"Failed to buy {target_symbol}: {buy_result}"
        
        return rebalance_results
    
    def get_transaction_summary(self):
        """
        Get summary of all transactions.
        
        Returns:
            dict: Transaction summary
        """
        if not self.transaction_log:
            return {"total_transactions": 0, "total_costs": 0}
        
        total_cost = sum(t["transaction_cost"] for t in self.transaction_log)
        buy_transactions = len([t for t in self.transaction_log if t["action"] == "BUY"])
        sell_transactions = len([t for t in self.transaction_log if t["action"] == "SELL"])
        
        return {
            "total_transactions": len(self.transaction_log),
            "buy_transactions": buy_transactions,
            "sell_transactions": sell_transactions,
            "total_transaction_costs": total_cost,
            "average_cost_per_transaction": total_cost / len(self.transaction_log)
        }


def test_portfolio_manager():
    """Test function to verify portfolio manager works correctly."""
    
    print("Testing Portfolio Manager...")
    
    # Initialize portfolio with $100,000
    portfolio = PortfolioManager(initial_capital=100000, transaction_cost_pct=0.001)
    
    print(f"Initial portfolio: {portfolio.get_current_position()}")
    
    # Test prices
    test_prices = {
        'SPY': 600.00,
        'QQQ': 550.00,
        'IWM': 220.00
    }
    
    # Test 1: Buy SPY
    print(f"\n--- Test 1: Buy SPY ---")
    buy_result = portfolio.buy_etf_position('SPY', test_prices['SPY'], '2024-01-01')
    print(f"Buy result: {buy_result}")
    print(f"Position after buy: {portfolio.get_current_position()}")
    
    # Test 2: Update portfolio value
    print(f"\n--- Test 2: Update portfolio value ---")
    new_prices = {'SPY': 620.00}  # SPY went up
    new_value = portfolio.update_portfolio_value(new_prices)
    print(f"New portfolio value: ${new_value:.2f}")
    
    # Test 3: Rebalance to QQQ
    print(f"\n--- Test 3: Rebalance to QQQ ---")
    rebalance_prices = {'SPY': 620.00, 'QQQ': 560.00}
    rebalance_result = portfolio.rebalance_to_etf('QQQ', rebalance_prices, '2024-02-01')
    print(f"Rebalance result: {rebalance_result['success']}")
    print(f"Position after rebalance: {portfolio.get_current_position()}")
    
    # Test 4: Transaction summary
    print(f"\n--- Test 4: Transaction summary ---")
    summary = portfolio.get_transaction_summary()
    print(f"Transaction summary: {summary}")
    
    # Test 5: Show all transactions
    print(f"\n--- Test 5: All transactions ---")
    for i, transaction in enumerate(portfolio.transaction_log, 1):
        print(f"  {i}. {transaction['date']} - {transaction['action']} {transaction['shares']} {transaction['symbol']} @ ${transaction['price']:.2f}")
        print(f"     Cost: ${transaction['transaction_cost']:.2f}")
    
    return True


if __name__ == "__main__":
    # Run test when script is executed directly
    test_portfolio_manager()