#!/usr/bin/env python3
"""
Expanded Universe Options Screener
Comprehensive market coverage for better opportunities
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
import os

class UniverseManager:
    """Manage our expanded trading universe"""
    
    def __init__(self):
        self.data_dir = "data"
        self.ensure_data_dirs()
        
    def ensure_data_dirs(self):
        """Create data storage directories"""
        dirs = ['data', 'data/daily_prices', 'data/options_chains', 'data/screening_results']
        for dir_name in dirs:
            os.makedirs(dir_name, exist_ok=True)
    
    def get_comprehensive_universe(self):
        """Build comprehensive trading universe"""
        
        # MEGA CAPS - Always liquid
        mega_caps = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX',
            'ORCL', 'CRM', 'ADBE', 'PYPL', 'INTC', 'AMD', 'MU', 'QCOM'
        ]
        
        # BROAD MARKET ETFS - Best liquidity
        market_etfs = [
            'SPY', 'QQQ', 'IWM', 'VTI', 'DIA', 'VEA', 'VWO', 'EEM'
        ]
        
        # SECTOR ETFS - Rotation plays
        sector_etfs = [
            'XLF', 'XLE', 'XLK', 'XLV', 'XLI', 'XLP', 'XLU', 'XLB',
            'XBI', 'XRT', 'XHB', 'XME', 'KRE', 'SMH', 'IBB', 'ARKK'
        ]
        
        # VOLATILITY/HEDGE - Market timing
        vol_plays = [
            'VIX', 'UVXY', 'SQQQ', 'SPXS', 'TLT', 'GLD', 'SLV'
        ]
        
        # HOT INDIVIDUAL NAMES - High options volume
        hot_names = [
            'UBER', 'LYFT', 'ABNB', 'COIN', 'RBLX', 'SNOW', 'PLTR', 'SOFI',
            'NIO', 'RIVN', 'LCID', 'F', 'GM', 'AAL', 'DAL', 'CCL', 'NCLH'
        ]
        
        # TRADITIONAL VALUE - Dividend/value plays  
        value_plays = [
            'JPM', 'BAC', 'WFC', 'GS', 'XOM', 'CVX', 'JNJ', 'PG', 'KO', 'PEP'
        ]
        
        # INTERNATIONAL - Geographic diversification
        international = [
            'FXI', 'EWJ', 'EWZ', 'EWY', 'EWG', 'INDA', 'RSX'
        ]
        
        # COMMODITIES - Inflation/commodity plays
        commodities = [
            'USO', 'UNG', 'GDX', 'GDXJ', 'SLV', 'PPLT', 'DBA'
        ]
        
        universe = {
            'mega_caps': mega_caps,
            'market_etfs': market_etfs, 
            'sector_etfs': sector_etfs,
            'vol_plays': vol_plays,
            'hot_names': hot_names,
            'value_plays': value_plays,
            'international': international,
            'commodities': commodities
        }
        
        # Flatten to single list
        all_symbols = []
        for category, symbols in universe.items():
            all_symbols.extend(symbols)
        
        # Remove duplicates
        all_symbols = list(set(all_symbols))
        
        print(f"📊 EXPANDED UNIVERSE: {len(all_symbols)} symbols across 8 categories")
        return all_symbols, universe
    
    def get_market_movers(self, min_volume=1000000):
        """Identify today's high-volume/volatile stocks"""
        print("🔥 Scanning for today's market movers...")
        
        # Sample of liquid names to check for unusual activity
        liquid_universe = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX',
            'AMD', 'CRM', 'UBER', 'PLTR', 'SOFI', 'SPY', 'QQQ', 'IWM'
        ]
        
        movers = []
        
        for symbol in liquid_universe:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='5d')
                
                if len(hist) >= 2:
                    today_vol = hist['Volume'].iloc[-1]
                    avg_vol = hist['Volume'].iloc[:-1].mean()
                    vol_ratio = today_vol / avg_vol if avg_vol > 0 else 1
                    
                    price_change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
                    
                    if vol_ratio > 1.5 or abs(price_change) > 3:  # High volume or big move
                        movers.append({
                            'symbol': symbol,
                            'price_change': price_change,
                            'volume_ratio': vol_ratio,
                            'current_volume': today_vol
                        })
                        
            except Exception:
                continue
                
            time.sleep(0.1)
        
        print(f"   Found {len(movers)} unusual movers today")
        return movers
    
    def save_universe_data(self, universe_data):
        """Save universe data for persistence"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"data/screening_results/universe_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(universe_data, f, indent=2, default=str)
        
        print(f"💾 Saved universe data to {filename}")

def main():
    """Test expanded universe"""
    manager = UniverseManager()
    
    # Get comprehensive universe
    all_symbols, categorized = manager.get_comprehensive_universe()
    
    print("\n📊 UNIVERSE BREAKDOWN:")
    for category, symbols in categorized.items():
        print(f"   {category.upper()}: {len(symbols)} symbols")
    
    print(f"\n🎯 TOTAL UNIVERSE: {len(all_symbols)} symbols")
    print("Sample symbols:", all_symbols[:10])
    
    # Get market movers
    movers = manager.get_market_movers()
    
    if movers:
        print(f"\n🔥 TODAY'S MARKET MOVERS:")
        for mover in movers[:5]:
            print(f"   {mover['symbol']}: {mover['price_change']:+.1f}% (Vol: {mover['volume_ratio']:.1f}x)")
    
    # Save data
    universe_data = {
        'timestamp': datetime.now().isoformat(),
        'total_symbols': len(all_symbols),
        'categories': categorized,
        'market_movers': movers
    }
    
    manager.save_universe_data(universe_data)
    
    print(f"\n✅ Expanded universe ready - {len(all_symbols)} symbols vs 16 previously")
    print("Ready to find much better opportunities!")

if __name__ == "__main__":
    main()