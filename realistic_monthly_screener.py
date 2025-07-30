#!/usr/bin/env python3
"""
Realistic Monthly Options Screener
Adjusted for actual monthly options market conditions
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

def find_realistic_monthly_options():
    print('🎯 REALISTIC MONTHLY OPTIONS SCREENER')
    print('Adjusted criteria for actual market conditions')
    print('=' * 60)
    
    # FOCUS ON ONLY THE MOST LIQUID NAMES for monthly options
    ultra_liquid = ['SPY', 'QQQ', 'AAPL', 'TSLA', 'NVDA', 'AMD', 'MSFT']
    
    # RELAXED CRITERIA for monthly reality
    max_premium = 2.50
    min_volume = 5        # Much lower - monthly options are illiquid
    min_oi = 20          # Much lower
    max_spread_pct = 25   # Much higher - monthly spreads suck
    
    opportunities = []
    
    print(f"Screening {len(ultra_liquid)} ultra-liquid symbols with REALISTIC criteria:")
    print(f"- Min Volume: {min_volume} (was 20)")
    print(f"- Min OI: {min_oi} (was 50)")  
    print(f"- Max Spread: {max_spread_pct}% (was 15%)")
    print()
    
    for symbol in ultra_liquid:
        print(f"Analyzing {symbol}...")
        try:
            ticker = yf.Ticker(symbol)
            current_price = ticker.history(period='1d')['Close'].iloc[-1]
            
            # Get expiries 25-45 days out
            expiries = ticker.options
            target_expiry = None
            
            for expiry in expiries:
                days = (datetime.strptime(expiry, '%Y-%m-%d') - datetime.now()).days
                if 25 <= days <= 45:
                    target_expiry = expiry
                    break
            
            if not target_expiry:
                print(f"   ❌ No suitable expiries")
                continue
            
            days_to_exp = (datetime.strptime(target_expiry, '%Y-%m-%d') - datetime.now()).days
            
            # Get options chain
            chain = ticker.option_chain(target_expiry)
            symbol_opportunities = []
            
            # Check calls
            for _, option in chain.calls.iterrows():
                opp = evaluate_realistic_option(
                    symbol, 'CALL', option, current_price, target_expiry, days_to_exp,
                    max_premium, min_volume, min_oi, max_spread_pct
                )
                if opp:
                    symbol_opportunities.append(opp)
            
            # Check puts  
            for _, option in chain.puts.iterrows():
                opp = evaluate_realistic_option(
                    symbol, 'PUT', option, current_price, target_expiry, days_to_exp,
                    max_premium, min_volume, min_oi, max_spread_pct
                )
                if opp:
                    symbol_opportunities.append(opp)
            
            if symbol_opportunities:
                opportunities.extend(symbol_opportunities)
                print(f"   ✅ Found {len(symbol_opportunities)} opportunities")
            else:
                print(f"   ❌ No opportunities")
                
        except Exception as e:
            print(f"   ⚠️ Error: {e}")
            
        time.sleep(0.5)
    
    if not opportunities:
        print(f"\n❌ Even with RELAXED criteria, no monthly opportunities found!")
        print("This confirms monthly options are largely untradeable for retail.")
        return
    
    # Sort by quality score
    opportunities.sort(key=lambda x: x['quality_score'], reverse=True)
    
    print(f"\n🎯 FOUND {len(opportunities)} REALISTIC MONTHLY OPPORTUNITIES")
    print("=" * 70)
    
    for i, opp in enumerate(opportunities[:5], 1):
        print(f"\n#{i} {opp['symbol']} ${opp['strike']:.0f} {opp['option_type']} ({opp['expiry']})")
        print(f"   💰 Cost: ${opp['premium']:.2f} (${opp['premium']*100:.0f} total)")
        print(f"   📅 Days: {opp['days_to_exp']} | Current: ${opp['current_price']:.2f}")
        print(f"   📊 Vol: {opp['volume']} | OI: {opp['open_interest']}")
        print(f"   💸 Spread: {opp['spread_pct']:.1f}% (Bid: ${opp['bid']:.2f}, Ask: ${opp['ask']:.2f})")
        print(f"   🎯 Need: {opp['move_needed']:.1f}% move to profit")
        print(f"   🏆 Quality Score: {opp['quality_score']:.1f}/100")
        print("-" * 50)

def evaluate_realistic_option(symbol, option_type, option, current_price, expiry, days_to_exp,
                             max_premium, min_volume, min_oi, max_spread_pct):
    """Evaluate with realistic monthly options criteria"""
    try:
        strike = option['strike']
        bid = option['bid'] if not pd.isna(option['bid']) else 0
        ask = option['ask'] if not pd.isna(option['ask']) else 0
        volume = option['volume'] if not pd.isna(option['volume']) else 0
        oi = option['openInterest'] if not pd.isna(option['openInterest']) else 0
        
        # Basic filters - MUCH more lenient
        if bid <= 0.02 or ask <= 0 or volume < min_volume or oi < min_oi:
            return None
        
        mid_price = (bid + ask) / 2
        spread_pct = ((ask - bid) / mid_price) * 100 if mid_price > 0 else 100
        
        if mid_price > max_premium or spread_pct > max_spread_pct:
            return None
        
        # Moneyness filters - reasonable strikes only
        if option_type == 'CALL':
            moneyness = current_price / strike
            move_needed = ((strike - current_price) / current_price) * 100
            if not (0.90 <= moneyness <= 1.10):  # Within 10%
                return None
        else:
            moneyness = strike / current_price  
            move_needed = ((current_price - strike) / current_price) * 100
            if not (0.90 <= moneyness <= 1.10):
                return None
        
        # Quality score
        quality_score = calculate_quality_score(volume, oi, spread_pct, abs(move_needed))
        
        return {
            'symbol': symbol,
            'option_type': option_type,
            'strike': strike,
            'expiry': expiry,
            'days_to_exp': days_to_exp,
            'current_price': current_price,
            'premium': round(mid_price, 2),
            'bid': bid,
            'ask': ask,
            'spread_pct': round(spread_pct, 1),
            'volume': int(volume),
            'open_interest': int(oi),
            'moneyness': round(moneyness, 3),
            'move_needed': round(abs(move_needed), 1),
            'quality_score': quality_score
        }
        
    except Exception:
        return None

def calculate_quality_score(volume, oi, spread_pct, move_needed):
    """Calculate option quality score"""
    score = 0
    
    # Volume score
    score += min(30, volume * 3)
    
    # Open interest score
    score += min(25, oi / 4)
    
    # Spread penalty
    score -= spread_pct
    
    # Move required penalty
    score -= move_needed
    
    return max(0, round(score, 1))

if __name__ == "__main__":
    find_realistic_monthly_options()