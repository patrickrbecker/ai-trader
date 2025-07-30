#!/usr/bin/env python3
"""
LEAP Capital Management - Liquidity-Focused LEAP Screener
Focuses on tradeable options with tight spreads and real volume
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import random
import warnings
warnings.filterwarnings('ignore')

class LiquidityScreener:
    def __init__(self):
        self.min_volume = 10           # Minimum daily volume
        self.min_open_interest = 100   # Minimum open interest
        self.max_spread_pct = 15       # Max bid/ask spread as % of mid
        self.min_bid = 0.10           # Minimum bid price (avoid zero bids)
        
    def analyze_liquidity(self, symbol, max_expiries=2):
        """Analyze options liquidity for a symbol"""
        try:
            print(f"\n🔍 Analyzing {symbol} for liquid LEAPs...")
            time.sleep(random.uniform(0.5, 1.5))
            
            ticker = yf.Ticker(symbol)
            stock_price = ticker.history(period="1d")['Close'].iloc[-1]
            
            # Get LEAP expiries (1+ years out)
            all_expiries = ticker.options
            current_date = datetime.now()
            
            leap_expiries = []
            for exp in all_expiries:
                exp_date = datetime.strptime(exp, '%Y-%m-%d')
                if (exp_date - current_date).days >= 365:
                    leap_expiries.append(exp)
            
            if not leap_expiries:
                print(f"❌ No LEAPs available for {symbol}")
                return []
            
            liquid_options = []
            
            # Check first few LEAP expiries
            for expiry in leap_expiries[:max_expiries]:
                print(f"   📅 Checking {expiry}...")
                time.sleep(1)
                
                try:
                    chain = ticker.option_chain(expiry)
                    calls = chain.calls
                    
                    # Filter for liquid calls
                    for _, option in calls.iterrows():
                        # Extract key metrics
                        strike = option['strike']
                        bid = option['bid'] if not pd.isna(option['bid']) else 0
                        ask = option['ask'] if not pd.isna(option['ask']) else 0
                        volume = option['volume'] if not pd.isna(option['volume']) else 0
                        oi = option['openInterest'] if not pd.isna(option['openInterest']) else 0
                        last_price = option['lastPrice'] if not pd.isna(option['lastPrice']) else 0
                        
                        # Skip if no meaningful data
                        if bid <= 0 or ask <= 0:
                            continue
                            
                        # Calculate metrics
                        mid_price = (bid + ask) / 2
                        spread_pct = ((ask - bid) / mid_price) * 100 if mid_price > 0 else 100
                        moneyness = stock_price / strike
                        days_to_exp = (datetime.strptime(expiry, '%Y-%m-%d') - current_date).days
                        
                        # Apply liquidity filters
                        if (bid >= self.min_bid and 
                            oi >= self.min_open_interest and
                            spread_pct <= self.max_spread_pct and
                            0.7 <= moneyness <= 1.3):  # Reasonable moneyness range
                            
                            liquid_options.append({
                                'symbol': symbol,
                                'expiry': expiry,
                                'strike': strike,
                                'stock_price': stock_price,
                                'moneyness': round(moneyness, 3),
                                'bid': bid,
                                'ask': ask,
                                'mid_price': round(mid_price, 2),
                                'spread_pct': round(spread_pct, 1),
                                'last_price': last_price,
                                'volume': int(volume),
                                'open_interest': int(oi),
                                'days_to_exp': days_to_exp,
                                'liquidity_score': self.calculate_liquidity_score(volume, oi, spread_pct)
                            })
                            
                except Exception as e:
                    print(f"   ⚠️  Error with {expiry}: {e}")
                    continue
            
            print(f"   ✅ Found {len(liquid_options)} liquid options")
            return liquid_options
            
        except Exception as e:
            print(f"❌ Error analyzing {symbol}: {e}")
            return []
    
    def calculate_liquidity_score(self, volume, oi, spread_pct):
        """Calculate liquidity score (0-100)"""
        # Volume component (0-40 points)
        volume_score = min(40, volume * 2)
        
        # Open interest component (0-40 points)  
        oi_score = min(40, oi / 100)
        
        # Spread component (0-20 points, lower spread = higher score)
        spread_score = max(0, 20 - spread_pct)
        
        return round(volume_score + oi_score + spread_score, 1)
    
    def screen_liquid_leaps(self, symbols):
        """Screen multiple symbols for liquid LEAPs"""
        all_liquid_options = []
        
        for symbol in symbols:
            options = self.analyze_liquidity(symbol)
            all_liquid_options.extend(options)
        
        return pd.DataFrame(all_liquid_options)
    
    def rank_by_tradability(self, df):
        """Rank options by tradability"""
        if df.empty:
            return df
            
        # Sort by liquidity score, then by spread
        df_sorted = df.sort_values(['liquidity_score', 'spread_pct'], 
                                 ascending=[False, True])
        
        return df_sorted

def main():
    """Main screening function"""
    print("🎯 LEAP CAPITAL MANAGEMENT - LIQUIDITY SCREENER")
    print("=" * 60)
    print("Screening for TRADEABLE LEAPs with tight spreads and real volume")
    print("=" * 60)
    
    screener = LiquidityScreener()
    
    # Focus on most liquid names first
    liquid_symbols = [
        'AAPL', 'MSFT', 'SPY', 'QQQ',  # High volume ETFs and mega caps
        'NVDA', 'TSLA', 'AMZN',        # High vol individual names  
        'XOM', 'JPM', 'BAC',           # Traditional value plays
        'IWM', 'GLD'                   # Additional liquid ETFs
    ]
    
    print(f"Screening {len(liquid_symbols)} highly liquid symbols...")
    
    results = screener.screen_liquid_leaps(liquid_symbols)
    
    if results.empty:
        print("\n❌ No liquid LEAP opportunities found!")
        return
    
    # Rank by tradability
    ranked = screener.rank_by_tradability(results)
    
    print(f"\n🎉 FOUND {len(ranked)} TRADEABLE LEAP OPPORTUNITIES")
    print("=" * 80)
    
    # Show top 15 most liquid options
    top_options = ranked.head(15)
    
    for idx, row in top_options.iterrows():
        print(f"\n📊 {row['symbol']} ${row['strike']:.0f} Call ({row['expiry']})")
        print(f"   💰 Stock: ${row['stock_price']:.2f} | Moneyness: {row['moneyness']:.3f}")
        print(f"   💵 Bid/Ask: ${row['bid']:.2f}/${row['ask']:.2f} | Mid: ${row['mid_price']:.2f}")
        print(f"   📈 Spread: {row['spread_pct']:.1f}% | Last: ${row['last_price']:.2f}")
        print(f"   📊 Volume: {row['volume']} | OI: {row['open_interest']:,}")
        print(f"   🏆 Liquidity Score: {row['liquidity_score']:.1f}/100")
        
        # Trade recommendation
        if row['spread_pct'] <= 5:
            print(f"   ✅ EXCELLENT tradability - tight spread")
        elif row['spread_pct'] <= 10:
            print(f"   🟡 GOOD tradability - reasonable spread")
        else:
            print(f"   🟠 FAIR tradability - wider spread")
            
        print("   " + "-" * 50)
    
    # Save results
    ranked.to_csv('liquid_leap_opportunities.csv', index=False)
    print(f"\n💾 Full results saved to: liquid_leap_opportunities.csv")
    print(f"📈 Total tradeable opportunities: {len(ranked)}")
    
    # Summary stats
    excellent = len(ranked[ranked['spread_pct'] <= 5])
    good = len(ranked[(ranked['spread_pct'] > 5) & (ranked['spread_pct'] <= 10)])
    fair = len(ranked[ranked['spread_pct'] > 10])
    
    print(f"\n📊 LIQUIDITY BREAKDOWN:")
    print(f"   ✅ Excellent (≤5% spread): {excellent}")  
    print(f"   🟡 Good (5-10% spread): {good}")
    print(f"   🟠 Fair (>10% spread): {fair}")

if __name__ == "__main__":
    main()