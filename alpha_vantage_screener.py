#!/usr/bin/env python3
"""
LEAP Screener using Alpha Vantage API
Free tier: 25 requests/day - use wisely
Get API key at: https://www.alphavantage.co/support/#api-key
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import time

class AlphaVantageScreener:
    def __init__(self, api_key=None):
        self.api_key = api_key or "demo"  # Demo key for testing
        self.base_url = "https://www.alphavantage.co/query"
        
    def get_stock_price(self, symbol):
        """Get current stock price"""
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            data = response.json()
            
            if 'Global Quote' in data:
                price = float(data['Global Quote']['05. price'])
                return price
            else:
                print(f"Error fetching price for {symbol}: {data}")
                return None
                
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def simulate_leap_opportunities(self, symbols):
        """
        Simulate LEAP opportunities using stock data only
        In production, you'd need options data from a proper provider
        """
        opportunities = []
        
        print("NOTE: This is a SIMULATION using stock prices only")
        print("Real LEAP analysis requires options chain data from a paid provider")
        print("-" * 60)
        
        for symbol in symbols:
            price = self.get_stock_price(symbol)
            if price is None:
                continue
                
            # Simulate potential LEAP strikes around current price
            strikes = [
                price * 0.8,   # 20% OTM
                price * 0.9,   # 10% OTM  
                price * 1.0,   # ATM
                price * 1.1,   # 10% ITM
                price * 1.2    # 20% ITM
            ]
            
            for strike in strikes:
                # Simulate basic LEAP metrics
                moneyness = price / strike
                simulated_premium = max(0, price - strike) + (price * 0.15)  # Rough estimate
                
                opportunities.append({
                    'symbol': symbol,
                    'current_price': price,
                    'strike': round(strike, 2),
                    'moneyness': round(moneyness, 3),
                    'estimated_premium': round(simulated_premium, 2),
                    'expiry': '2026-01-16',  # Typical LEAP expiry
                    'note': 'SIMULATED - NOT REAL OPTIONS DATA'
                })
            
            # Rate limiting
            time.sleep(12)  # Alpha Vantage allows 5 calls/minute
            
        return pd.DataFrame(opportunities)

def main():
    """Demo the concept"""
    
    print("ALPHA VANTAGE LEAP SCREENER DEMO")
    print("=" * 50)
    print("\nIMPORTANT: This uses FREE demo data with heavy limitations")
    print("For production use:")
    print("1. Get Alpha Vantage API key: https://www.alphavantage.co/support/#api-key")
    print("2. Use paid options data provider (Interactive Brokers, etc.)")
    print("3. This demo only shows stock prices + simulated options\n")
    
    screener = AlphaVantageScreener()
    
    # Test with just 2 symbols (free tier limited)
    test_symbols = ['IBM', 'MSFT']
    
    print(f"Testing with symbols: {test_symbols}")
    print("This will take ~30 seconds due to rate limits...\n")
    
    results = screener.simulate_leap_opportunities(test_symbols)
    
    print("\nSIMULATED LEAP OPPORTUNITIES:")
    print("=" * 50)
    
    for _, row in results.iterrows():
        print(f"{row['symbol']} - Strike: ${row['strike']:.2f}")
        print(f"  Current: ${row['current_price']:.2f} | Moneyness: {row['moneyness']:.3f}")
        print(f"  Est. Premium: ${row['estimated_premium']:.2f}")
        print(f"  NOTE: {row['note']}")
        print()
    
    print("TO GET REAL LEAP DATA:")
    print("1. Sign up for Interactive Brokers API")
    print("2. Use TastyTrade API") 
    print("3. Pay for professional options data feed")
    print("\nFree APIs don't provide reliable options chains.")

if __name__ == "__main__":
    main()