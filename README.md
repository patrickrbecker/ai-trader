# AI LEAP Options Screener

Professional-grade LEAP (Long-term Equity Anticipation Securities) screening tool built for identifying profitable long-term options opportunities.

## Features

- **Real-time options data** via Yahoo Finance
- **Black-Scholes pricing** with theoretical edge calculation
- **Full Greeks suite** (Delta, Theta, Gamma, Vega)
- **Liquidity scoring** to avoid illiquid positions
- **Multi-factor ranking** system for opportunity prioritization
- **Professional risk filters** based on institutional criteria

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python leap_screener.py
```

## Screening Criteria

- **Time to expiry**: ≥365 days (LEAP definition)
- **Moneyness**: 0.8-1.2 (reasonable strike range)
- **Delta**: 0.3-0.8 (meaningful exposure without excessive risk)
- **Implied Volatility**: 15%-60% (reasonable vol range)
- **Minimum liquidity requirements**

## Output

- Top 10 ranked opportunities displayed to terminal
- Full results exported to `leap_opportunities.csv`
- Detailed risk metrics for each position

## Risk Disclaimer

This tool is for educational and research purposes. Options trading involves substantial risk of loss. Past performance does not guarantee future results. Always conduct your own due diligence before making investment decisions.

## License

MIT License - Use at your own risk.