#!/usr/bin/env python3
"""
Find ACTIONABLE monthly options - realistic profit opportunities
Focus: 30-40 days out, reasonable probability of success, $250 max
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

def find_actionable_monthly_options():
    print('🎯 ACTIONABLE MONTHLY OPTIONS - REALISTIC PROFIT OPPORTUNITIES')
    print('Criteria: 30-40 days, reasonable moves, good liquidity, $250 max')
    print('=' * 75)
    
    # Focus on liquid names with regular movement patterns
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'SPY', 'QQQ', 'IWM']
    
    target_dte_min = 25
    target_dte_max = 45
    max_premium = 2.50
    
    actionable_options = []
    
    for symbol in symbols:
        print(f'Analyzing {symbol}...')
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='3mo')
            current_price = hist['Close'].iloc[-1]
            
            # Calculate recent volatility for realistic expectations
            returns = hist['Close'].pct_change().dropna()
            avg_daily_move = returns.abs().mean()
            monthly_move_estimate = avg_daily_move * 22  # ~22 trading days per month
            
            # Get target expiries
            expiries = ticker.options
            target_expiry = None
            
            for expiry in expiries:
                days_to_exp = (datetime.strptime(expiry, '%Y-%m-%d') - datetime.now()).days
                if target_dte_min <= days_to_exp <= target_dte_max:
                    target_expiry = expiry
                    break
            
            if not target_expiry:
                continue
                
            days_to_exp = (datetime.strptime(target_expiry, '%Y-%m-%d') - datetime.now()).days
            
            try:
                chain = ticker.option_chain(target_expiry)
                
                # Look for REASONABLE call opportunities
                for _, option in chain.calls.iterrows():
                    if (option['bid'] > 0.05 and option['ask'] > 0 and 
                        option['volume'] >= 20 and option['openInterest'] >= 50):
                        
                        mid_price = (option['bid'] + option['ask']) / 2
                        spread_pct = ((option['ask'] - option['bid']) / mid_price) * 100
                        
                        if mid_price <= max_premium and spread_pct <= 20:  # Max 20% spread
                            
                            strike = option['strike']
                            moneyness = current_price / strike
                            
                            # Focus on REASONABLE strikes (within 10% of current price)
                            if 0.95 <= moneyness <= 1.15:  # ATM to slightly OTM
                                
                                move_to_profit = ((strike - current_price) / current_price) * 100
                                
                                # Calculate realistic profit (assume 5% and 10% moves)
                                profit_5pct = calculate_realistic_call_profit(current_price, strike, mid_price, 0.05)
                                profit_10pct = calculate_realistic_call_profit(current_price, strike, mid_price, 0.10)
                                
                                # Only include if profitable on reasonable moves
                                if profit_5pct > 0 or profit_10pct > 0:
                                    
                                    actionable_options.append({
                                        'symbol': symbol,
                                        'type': 'CALL',
                                        'strike': strike,
                                        'expiry': target_expiry,
                                        'days_to_exp': days_to_exp,
                                        'current_price': current_price,
                                        'premium': mid_price,
                                        'moneyness': moneyness,
                                        'volume': option['volume'],
                                        'open_interest': option['openInterest'],
                                        'spread_pct': spread_pct,
                                        'move_to_profit': move_to_profit,
                                        'monthly_vol_estimate': monthly_move_estimate * 100,
                                        'profit_5pct': profit_5pct,
                                        'profit_10pct': profit_10pct,
                                        'actionability_score': calculate_actionability_score(
                                            moneyness, spread_pct, option['volume'], 
                                            option['openInterest'], abs(move_to_profit), monthly_move_estimate * 100
                                        )
                                    })
                
                # Look for REASONABLE put opportunities  
                for _, option in chain.puts.iterrows():
                    if (option['bid'] > 0.05 and option['ask'] > 0 and 
                        option['volume'] >= 20 and option['openInterest'] >= 50):
                        
                        mid_price = (option['bid'] + option['ask']) / 2
                        spread_pct = ((option['ask'] - option['bid']) / mid_price) * 100
                        
                        if mid_price <= max_premium and spread_pct <= 20:
                            
                            strike = option['strike']
                            moneyness = strike / current_price
                            
                            # Focus on REASONABLE strikes
                            if 0.85 <= moneyness <= 1.05:
                                
                                move_to_profit = ((current_price - strike) / current_price) * 100
                                
                                profit_5pct = calculate_realistic_put_profit(current_price, strike, mid_price, 0.05)
                                profit_10pct = calculate_realistic_put_profit(current_price, strike, mid_price, 0.10)
                                
                                if profit_5pct > 0 or profit_10pct > 0:
                                    
                                    actionable_options.append({
                                        'symbol': symbol,
                                        'type': 'PUT',
                                        'strike': strike,
                                        'expiry': target_expiry,
                                        'days_to_exp': days_to_exp,
                                        'current_price': current_price,
                                        'premium': mid_price,
                                        'moneyness': moneyness,
                                        'volume': option['volume'],
                                        'open_interest': option['openInterest'],
                                        'spread_pct': spread_pct,
                                        'move_to_profit': abs(move_to_profit),
                                        'monthly_vol_estimate': monthly_move_estimate * 100,
                                        'profit_5pct': profit_5pct,
                                        'profit_10pct': profit_10pct,
                                        'actionability_score': calculate_actionability_score(
                                            moneyness, spread_pct, option['volume'], 
                                            option['openInterest'], abs(move_to_profit), monthly_move_estimate * 100
                                        )
                                    })
                            
            except Exception as e:
                print(f'  Error with {target_expiry}: {e}')
                continue
                
        except Exception as e:
            print(f'  Error with {symbol}: {e}')
            continue
        
        time.sleep(0.3)
    
    if not actionable_options:
        print('No actionable options found!')
        return
    
    # Sort by actionability score
    sorted_options = sorted(actionable_options, key=lambda x: x['actionability_score'], reverse=True)
    
    print(f'\n🎯 TOP 3 ACTIONABLE MONTHLY OPTIONS')
    print('=' * 60)
    
    for i, option in enumerate(sorted_options[:3], 1):
        print(f'\n#{i} ⚡ {option["symbol"]} ${option["strike"]:.0f} {option["type"]} - {option["expiry"]}')
        print(f'   💰 Cost: ${option["premium"]:.2f} (${option["premium"]*100:.0f} total)')
        print(f'   📅 Days: {option["days_to_exp"]} | Current: ${option["current_price"]:.2f}')
        print(f'   📊 Volume: {option["volume"]:.0f} | OI: {option["open_interest"]:.0f} | Spread: {option["spread_pct"]:.1f}%')
        print(f'   🎯 Need: {option["move_to_profit"]:.1f}% move to profit')
        print(f'   📈 Historical vol: {option["monthly_vol_estimate"]:.1f}% per month')
        
        print(f'   💎 REALISTIC PROFITS:')
        if option['profit_5pct'] > 0:
            profit_dollars = (option['profit_5pct'] / 100) * (option['premium'] * 100)
            print(f'      5% move:  +{option["profit_5pct"]:.0f}% (${profit_dollars:.0f})')
        if option['profit_10pct'] > 0:
            profit_dollars = (option['profit_10pct'] / 100) * (option['premium'] * 100)
            print(f'      10% move: +{option["profit_10pct"]:.0f}% (${profit_dollars:.0f})')
        
        print(f'   🏆 Actionability Score: {option["actionability_score"]:.1f}/100')
        print('-' * 50)

def calculate_realistic_call_profit(stock_price, strike, premium, move_pct):
    """Calculate call profit with realistic time decay"""
    new_price = stock_price * (1 + move_pct)
    if new_price > strike:
        intrinsic = new_price - strike
        # Rough estimate: assume 30% time decay over month
        estimated_option_value = intrinsic + (premium * 0.3)  
        profit = estimated_option_value - premium
        return (profit / premium) * 100 if profit > 0 else -100
    else:
        return -70  # Partial loss, not total

def calculate_realistic_put_profit(stock_price, strike, premium, move_pct):
    """Calculate put profit with realistic time decay"""
    new_price = stock_price * (1 - move_pct)
    if new_price < strike:
        intrinsic = strike - new_price
        estimated_option_value = intrinsic + (premium * 0.3)
        profit = estimated_option_value - premium
        return (profit / premium) * 100 if profit > 0 else -100
    else:
        return -70

def calculate_actionability_score(moneyness, spread_pct, volume, oi, move_needed, hist_vol):
    """Score how actionable/tradeable this option is"""
    score = 0
    
    # Moneyness score (prefer ATM to slightly OTM)
    if 0.98 <= moneyness <= 1.02:
        score += 30
    elif 0.95 <= moneyness <= 1.05:
        score += 25
    else:
        score += 15
    
    # Liquidity score
    score += min(25, volume / 2)  # Up to 25 points for volume
    score += min(20, oi / 50)     # Up to 20 points for OI
    
    # Spread penalty
    score -= spread_pct  # Subtract spread percentage
    
    # Realistic move score
    if move_needed <= hist_vol:
        score += 15  # Move is within historical range
    elif move_needed <= hist_vol * 1.5:
        score += 10
    else:
        score += 5
    
    return max(0, score)

if __name__ == "__main__":
    find_actionable_monthly_options()