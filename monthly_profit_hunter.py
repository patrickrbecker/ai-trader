#!/usr/bin/env python3
"""
Find 3 monthly options (30-40 days out) with highest profit potential
Budget: $250 max per contract
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

def find_monthly_profit_options():
    print('🎯 MONTHLY PROFIT HUNTER - $250 MAX PER CONTRACT')
    print('Target: 30-40 days to expiry with maximum profit potential')
    print('=' * 70)
    
    # High-volume symbols for good options liquidity
    symbols = [
        'SPY', 'QQQ', 'IWM', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 
        'META', 'NFLX', 'AMD', 'JPM', 'BAC', 'XOM', 'XLF', 'XLE', 'GLD'
    ]
    
    target_dte_min = 25  # Minimum days
    target_dte_max = 45  # Maximum days
    max_premium = 2.50   # $250 max per contract
    
    all_options = []
    
    for symbol in symbols:
        print(f'Scanning {symbol}...')
        try:
            ticker = yf.Ticker(symbol)
            current_price = ticker.history(period='1d')['Close'].iloc[-1]
            
            # Get expiration dates
            expiries = ticker.options
            target_expiries = []
            
            for expiry in expiries:
                days_to_exp = (datetime.strptime(expiry, '%Y-%m-%d') - datetime.now()).days
                if target_dte_min <= days_to_exp <= target_dte_max:
                    target_expiries.append((expiry, days_to_exp))
            
            if not target_expiries:
                continue
            
            # Check first target expiry
            expiry, days_to_exp = target_expiries[0]
            
            try:
                chain = ticker.option_chain(expiry)
                
                # Analyze calls
                for _, option in chain.calls.iterrows():
                    if (option['bid'] > 0 and option['ask'] > 0 and 
                        option['volume'] > 50 and option['openInterest'] > 100):
                        
                        mid_price = (option['bid'] + option['ask']) / 2
                        if mid_price <= max_premium:
                            
                            strike = option['strike']
                            moneyness = current_price / strike
                            
                            # Calculate profit scenarios
                            profit_5pct = calculate_call_profit(current_price, strike, mid_price, 0.05)
                            profit_10pct = calculate_call_profit(current_price, strike, mid_price, 0.10)
                            profit_15pct = calculate_call_profit(current_price, strike, mid_price, 0.15)
                            
                            max_profit = max(profit_5pct, profit_10pct, profit_15pct)
                            
                            all_options.append({
                                'symbol': symbol,
                                'type': 'CALL',
                                'strike': strike,
                                'expiry': expiry,
                                'days_to_exp': days_to_exp,
                                'current_price': current_price,
                                'premium': mid_price,
                                'moneyness': moneyness,
                                'volume': option['volume'],
                                'open_interest': option['openInterest'],
                                'profit_5pct': profit_5pct,
                                'profit_10pct': profit_10pct,
                                'profit_15pct': profit_15pct,
                                'max_profit': max_profit
                            })
                
                # Analyze puts
                for _, option in chain.puts.iterrows():
                    if (option['bid'] > 0 and option['ask'] > 0 and 
                        option['volume'] > 50 and option['openInterest'] > 100):
                        
                        mid_price = (option['bid'] + option['ask']) / 2
                        if mid_price <= max_premium:
                            
                            strike = option['strike']
                            moneyness = strike / current_price
                            
                            # Calculate profit scenarios
                            profit_5pct = calculate_put_profit(current_price, strike, mid_price, 0.05)
                            profit_10pct = calculate_put_profit(current_price, strike, mid_price, 0.10)
                            profit_15pct = calculate_put_profit(current_price, strike, mid_price, 0.15)
                            
                            max_profit = max(profit_5pct, profit_10pct, profit_15pct)
                            
                            all_options.append({
                                'symbol': symbol,
                                'type': 'PUT',
                                'strike': strike,
                                'expiry': expiry,
                                'days_to_exp': days_to_exp,
                                'current_price': current_price,
                                'premium': mid_price,
                                'moneyness': moneyness,
                                'volume': option['volume'],
                                'open_interest': option['openInterest'],
                                'profit_5pct': profit_5pct,
                                'profit_10pct': profit_10pct,
                                'profit_15pct': profit_15pct,
                                'max_profit': max_profit
                            })
                            
            except Exception as e:
                print(f'  Error with {expiry}: {e}')
                continue
                
        except Exception as e:
            print(f'  Error with {symbol}: {e}')
            continue
        
        time.sleep(0.5)  # Rate limiting
    
    if not all_options:
        print('No options found matching criteria!')
        return
    
    # Sort by maximum profit potential
    sorted_options = sorted(all_options, key=lambda x: x['max_profit'], reverse=True)
    
    print(f'\n🏆 TOP 3 MONTHLY OPTIONS WITH HIGHEST PROFIT POTENTIAL')
    print('=' * 70)
    
    for i, option in enumerate(sorted_options[:3], 1):
        print(f'\n#{i} 🚀 {option["symbol"]} ${option["strike"]:.0f} {option["type"]} - {option["expiry"]}')
        print(f'   💰 Premium: ${option["premium"]:.2f} (${option["premium"]*100:.0f} total)')
        print(f'   📅 Days to Expiry: {option["days_to_exp"]}')
        print(f'   📊 Current Price: ${option["current_price"]:.2f} | Moneyness: {option["moneyness"]:.3f}')
        print(f'   📈 Volume: {option["volume"]:.0f} | OI: {option["open_interest"]:.0f}')
        print(f'   💎 PROFIT SCENARIOS:')
        
        if option['profit_5pct'] > 0:
            print(f'      5% move:  +{option["profit_5pct"]:.0f}% (${option["profit_5pct"]*option["premium"]:.0f})')
        if option['profit_10pct'] > 0:
            print(f'      10% move: +{option["profit_10pct"]:.0f}% (${option["profit_10pct"]*option["premium"]:.0f})')
        if option['profit_15pct'] > 0:
            print(f'      15% move: +{option["profit_15pct"]:.0f}% (${option["profit_15pct"]*option["premium"]:.0f})')
        
        print(f'   🎯 MAX PROFIT POTENTIAL: +{option["max_profit"]:.0f}%')
        print('-' * 60)

def calculate_call_profit(stock_price, strike, premium, move_pct):
    """Calculate call option profit for given stock move"""
    new_price = stock_price * (1 + move_pct)
    if new_price > strike:
        intrinsic = new_price - strike
        profit = intrinsic - premium
        return (profit / premium) * 100 if profit > 0 else -100
    else:
        return -100

def calculate_put_profit(stock_price, strike, premium, move_pct):
    """Calculate put option profit for given stock move"""
    new_price = stock_price * (1 - move_pct)
    if new_price < strike:
        intrinsic = strike - new_price
        profit = intrinsic - premium
        return (profit / premium) * 100 if profit > 0 else -100
    else:
        return -100

if __name__ == "__main__":
    find_monthly_profit_options()