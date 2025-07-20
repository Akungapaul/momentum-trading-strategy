# Momentum Trading Strategy

A systematic algorithmic trading strategy that uses price momentum to trade ETFs without relying on technical analysis indicators.

## 🎯 Strategy Overview

This momentum strategy:
- **Trades**: SPY, QQQ, IWM (major US equity ETFs)
- **Approach**: Pure price momentum without technical analysis
- **Rebalancing**: Monthly to highest momentum ETF
- **Capital**: 100% allocation to top performer
- **Tested**: 1+ year backtest with real market data

## 📊 Performance Results

**Backtest Period**: June 2024 - July 2025
- **Total Return**: 13.00%
- **Initial Capital**: $100,000
- **Final Value**: $112,998
- **Rebalances**: 4 strategic switches
- **Transaction Costs**: $309.57 (0.31%)

### Strategy Decisions
- **Mar 2025**: Selected SPY during market uncertainty
- **May 2025**: Switched to QQQ (+14.44% momentum)
- **Jun 2025**: Remained in QQQ (+7.14% momentum)
- **Final**: QQQ emerged as top performer

## 🏗️ Architecture

### Core Components

```
AlgoTrading1/
├── src/
│   ├── data_providers/        # ETF data fetching
│   └── portfolio/             # Position management
├── strategies/
│   └── scenario_based/        # Momentum calculations
├── backtesting/               # Historical simulation
├── utils/                     # Helper functions
├── data/                      # Market data storage
└── docs/                      # Documentation
```

### Key Modules

1. **ETF Data Fetcher** (`src/data_providers/etf_data_fetcher.py`)
   - Downloads ETF price data from Yahoo Finance
   - Handles data validation and storage

2. **Momentum Calculator** (`strategies/scenario_based/momentum_calculator.py`)
   - Calculates 1-month, 3-month, 6-month returns
   - Ranks ETFs by weighted momentum score
   - No technical indicators used

3. **Portfolio Manager** (`src/portfolio/portfolio_manager.py`)
   - Manages positions and rebalancing
   - Tracks transaction costs
   - Handles cash management

4. **Backtest Engine** (`backtesting/momentum_backtest.py`)
   - Orchestrates complete historical simulation
   - Monthly rebalancing logic
   - Performance reporting

## 🚀 Quick Start

### Prerequisites

```bash
pip install -r requirements.txt
```

Required packages:
- `pandas` - Data manipulation
- `numpy` - Numerical computing
- `yfinance` - Financial data
- `python-dateutil` - Date arithmetic

### Running the Strategy

1. **Fetch ETF Data**:
```python
from src.data_providers.etf_data_fetcher import ETFDataFetcher

fetcher = ETFDataFetcher()
start_date, end_date = fetcher.get_date_range_for_backtest(1)

# Download data for all ETFs
for symbol in ['SPY', 'QQQ', 'IWM']:
    fetcher.fetch_and_save_etf_data(symbol, start_date, end_date)
```

2. **Run Backtest**:
```python
from backtesting.momentum_backtest import MomentumBacktest

backtest = MomentumBacktest(
    etf_symbols=['SPY', 'QQQ', 'IWM'],
    initial_capital=100000,
    transaction_cost_pct=0.001
)

results = backtest.run_backtest('2024-06-20', '2025-07-18')
backtest.print_backtest_summary()
```

3. **Analyze Current Momentum**:
```python
from strategies.scenario_based.momentum_calculator import MomentumCalculator

calculator = MomentumCalculator()
# Load current data and calculate momentum scores
momentum_analysis = calculator.calculate_multi_etf_momentum(etf_data)
print(f"Top ETF: {momentum_analysis['top_etf']}")
```

## 📈 Strategy Logic

### Momentum Calculation

The strategy uses a weighted momentum score:

```python
# Period returns
1_month_return = (current_price / price_30_days_ago) - 1
3_month_return = (current_price / price_90_days_ago) - 1  
6_month_return = (current_price / price_180_days_ago) - 1

# Weighted momentum score
momentum_score = (1_month * 0.5) + (3_month * 0.3) + (6_month * 0.2)
```

### Rebalancing Rules

1. **Monthly Evaluation**: Calculate momentum scores for all ETFs
2. **Ranking**: Sort ETFs by momentum score (highest first)
3. **Position Switch**: If top ETF differs from current holding:
   - Sell current position
   - Buy new top ETF with proceeds
4. **Transaction Costs**: 0.1% per trade (realistic brokerage fees)

## 🔍 Testing Framework

Each component is independently testable:

### Run Individual Tests

```bash
# Test data fetcher
python src/data_providers/etf_data_fetcher.py

# Test momentum calculator  
python strategies/scenario_based/momentum_calculator.py

# Test portfolio manager
python src/portfolio/portfolio_manager.py

# Test full backtest
python backtesting/momentum_backtest.py
```

### Validation Checks

- **Data Quality**: Missing values, price ranges, continuity
- **Momentum Calculation**: Mathematical accuracy verification
- **Portfolio Logic**: Position tracking, transaction costs
- **Backtest Integrity**: Date handling, rebalancing logic

## 📋 Configuration

Strategy parameters in `momentum_calculator.py`:

```python
periods = [30, 90, 180]        # Lookback periods (days)
weights = [0.5, 0.3, 0.2]      # Period weights
transaction_cost = 0.001       # 0.1% per trade
rebalance_frequency = 'monthly' # Rebalancing schedule
```

## 📊 Performance Metrics

The backtest tracks:
- **Total Returns**: Portfolio growth over time
- **Volatility**: Risk measurement
- **Transaction Costs**: Trading expenses
- **Rebalancing History**: Strategy decisions
- **Position Tracking**: Holdings over time

## 🔧 Extending the Strategy

### Add New ETFs

```python
etf_symbols = ['SPY', 'QQQ', 'IWM', 'VTI', 'VOO']  # Add more ETFs
```

### Modify Momentum Periods

```python
calculator = MomentumCalculator(
    periods=[20, 60, 120],      # Different lookback periods
    weights=[0.6, 0.3, 0.1]     # Adjust weightings
)
```

### Change Rebalancing Frequency

```python
# Weekly rebalancing (higher transaction costs)
rebalance_dates = get_weekly_rebalance_dates(start_date, end_date)
```

## 📚 Documentation

- **Framework Guide**: `/docs/prompt-engineering-framework.md`
- **Examples**: `/docs/prompt-examples.md` 
- **Quick Reference**: `/docs/knowledge-index.md`
- **Project Notes**: `CLAUDE.md`

## ⚠️ Disclaimers

- **Backtesting Limitations**: Past performance doesn't guarantee future results
- **Transaction Costs**: Real-world costs may vary
- **Market Conditions**: Strategy performance depends on momentum persistence
- **Risk Management**: No stop-losses or risk limits implemented
- **Educational Purpose**: Not investment advice

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-strategy`)
3. Test your changes
4. Commit changes (`git commit -am 'Add new strategy'`)
5. Push to branch (`git push origin feature/new-strategy`)
6. Create Pull Request

## 📄 License

This project is for educational and research purposes. Use at your own risk.

## 🙋‍♂️ Support

For questions or issues:
1. Check the documentation in `/docs`
2. Review test examples in module files
3. Open an issue on GitHub

---

**Built with**: Python, pandas, yfinance  
**Strategy Type**: Momentum-based systematic trading  
**Last Updated**: 2025-07-20