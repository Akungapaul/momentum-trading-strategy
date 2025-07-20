/co# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a momentum-based algorithmic trading strategy that trades SPY, QQQ, and IWM ETFs using pure price momentum without technical analysis. The strategy achieved 13% returns in backtesting with monthly rebalancing.

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run full backtest
python backtesting/momentum_backtest.py

# Test individual components
python src/data_providers/etf_data_fetcher.py
python strategies/scenario_based/momentum_calculator.py
python src/portfolio/portfolio_manager.py

# Fetch latest ETF data
python -c "from src.data_providers.etf_data_fetcher import ETFDataFetcher; fetcher = ETFDataFetcher(); [fetcher.fetch_and_save_etf_data(s, '2024-01-01', '2025-12-31') for s in ['SPY', 'QQQ', 'IWM']]"
```

## Architecture

The momentum strategy is built with modular, independently testable components:

### Core Components
- **Data Layer** (`src/data_providers/`) - ETF data fetching and validation
- **Strategy Logic** (`strategies/scenario_based/`) - Momentum calculation without technical analysis
- **Portfolio Management** (`src/portfolio/`) - Position tracking and rebalancing
- **Backtesting Engine** (`backtesting/`) - Historical simulation and performance analysis
- **Utilities** (`utils/`) - Data validation and helper functions

### Strategy Performance
- **Backtest Period**: June 2024 - July 2025
- **Total Return**: 13.00%
- **Monthly Rebalancing**: 4 strategic position changes
- **Final Selection**: QQQ (highest momentum)

### Data Flow
1. **Fetch** ETF data (SPY, QQQ, IWM) via yfinance
2. **Validate** data quality and continuity
3. **Calculate** momentum scores (1M, 3M, 6M weighted returns)
4. **Rank** ETFs by momentum strength
5. **Rebalance** to highest momentum ETF monthly
6. **Track** performance and transaction costs

## Knowledge Management

This project includes a comprehensive knowledge base for prompt engineering and AI development best practices:

- **Framework Guide**: `/docs/prompt-engineering-framework.md` - Complete 6-step enterprise framework
- **Examples & Templates**: `/docs/prompt-examples.md` - Real-world examples and reusable templates
- **Quick Reference**: `/docs/knowledge-index.md` - Navigation and quick access guide

### Prompt Engineering Resources

The documentation provides:
- Enterprise-grade prompt engineering methodology
- Proven templates for customer support, code review, and documentation
- Performance metrics and optimization techniques
- A/B testing and validation frameworks
- Production deployment best practices

Access the knowledge base through `/docs/knowledge-index.md` for quick navigation and reference.

## Version Control

This project is now under Git version control:

```bash
# Repository status
git status

# View commit history  
git log --oneline

# Check differences
git diff

# Common workflow
git add .
git commit -m "Update strategy parameters"
git push origin main
```

### Git Configuration
- **Repository**: Initialized with comprehensive .gitignore
- **Documentation**: Complete README.md with usage examples
- **Data Protection**: Market data files excluded from version control
- **Structure**: All source code and documentation tracked

## Notes

- **Status**: Fully implemented momentum trading strategy
- **Components**: All modules tested and working
- **Performance**: 13% return in 1+ year backtest
- **Repository**: Ready for GitHub hosting