#!/usr/bin/env python3
"""
$40 Stock Screener - Find the best stock under $40
"""

import yfinance as yf
import pandas as pd
import time

def screen_stocks_under_40():
    print('🔍 SCREENING STOCKS UNDER $40 WITH UPSIDE POTENTIAL')
    print('=' * 60)

    # Candidate stocks under $40
    candidates = [
        'F',      # Ford - turnaround story
        'INTC',   # Intel - comeback play  
        'T',      # AT&T - dividend yield
        'VALE',   # Vale - commodity play
        'KMI',    # Kinder Morgan - pipeline
        'GOLD',   # Barrick Gold - gold play
        'NIO',    # Nio - Chinese EV
        'BB',     # BlackBerry - cybersecurity
        'NOK',    # Nokia - 5G infrastructure
        'PLTR',   # Palantir - data analytics
        'SOFI',   # SoFi - fintech
        'SIRI',   # SiriusXM
        'CCL',    # Carnival cruise
        'AAL',    # American Airlines
        'SNAP',   # Snapchat
        'PINS',   # Pinterest
    ]

    results = []

    for symbol in candidates:
        try:
            print(f'Checking {symbol}...')
            ticker = yf.Ticker(symbol)
            
            # Get current price
            hist = ticker.history(period='5d')
            if hist.empty:
                continue
                
            price = hist['Close'].iloc[-1]
            if price > 40:
                print(f'  {symbol}: ${price:.2f} - TOO EXPENSIVE')
                continue
                
            # Get company info
            info = ticker.info
            market_cap = info.get('marketCap', 0)
            market_cap_b = market_cap / 1e9 if market_cap else 0
            
            pe_ratio = info.get('trailingPE', None)
            dividend_yield = info.get('dividendYield', 0)
            div_yield_pct = dividend_yield * 100 if dividend_yield else 0
            
            # 52-week range
            week_52_high = info.get('fiftyTwoWeekHigh', 0)
            week_52_low = info.get('fiftyTwoWeekLow', 0)
            upside_to_high = ((week_52_high - price) / price) * 100 if week_52_high else 0
            
            # Recent performance
            price_30d_ago = hist['Close'].iloc[0] if len(hist) >= 5 else price
            recent_performance = ((price - price_30d_ago) / price_30d_ago) * 100
            
            results.append({
                'symbol': symbol,
                'price': price,
                'market_cap_b': market_cap_b,
                'pe_ratio': pe_ratio,
                'div_yield_pct': div_yield_pct,
                'week_52_high': week_52_high,
                'week_52_low': week_52_low,
                'upside_to_high': upside_to_high,
                'recent_perf': recent_performance,
                'company': info.get('longName', 'N/A'),
                'sector': info.get('sector', 'N/A'),
                'shares_you_can_buy': int(40 // price)
            })
            
            print(f'  ✅ {symbol}: ${price:.2f} - {upside_to_high:.1f}% upside to 52W high')
            time.sleep(0.5)
            
        except Exception as e:
            print(f'  ❌ Error with {symbol}: {e}')
            continue

    return results

def analyze_top_picks(results):
    print(f'\n🎯 TOP STOCK PICKS UNDER $40')
    print('=' * 80)
    
    # Sort by upside potential
    sorted_results = sorted(results, key=lambda x: x['upside_to_high'], reverse=True)
    
    for i, stock in enumerate(sorted_results[:5], 1):
        print(f'\n{i}. {stock["symbol"]} - ${stock["price"]:.2f}')
        print(f'   📊 {stock["company"][:40]}')
        print(f'   🏭 Sector: {stock["sector"]}')
        print(f'   📈 Market Cap: ${stock["market_cap_b"]:.1f}B')
        print(f'   💰 P/E: {stock["pe_ratio"]:.1f}' if stock["pe_ratio"] else '   💰 P/E: N/A')
        print(f'   💵 Dividend: {stock["div_yield_pct"]:.1f}%')
        print(f'   📊 52W Range: ${stock["week_52_low"]:.2f} - ${stock["week_52_high"]:.2f}')
        print(f'   🎯 UPSIDE TO 52W HIGH: {stock["upside_to_high"]:.1f}%')
        print(f'   📅 Recent 5-day: {stock["recent_perf"]:.1f}%')
        print(f'   🛒 YOU CAN BUY: {stock["shares_you_can_buy"]} shares')
        print('   ' + '-' * 60)
    
    return sorted_results

if __name__ == "__main__":
    results = screen_stocks_under_40()
    if results:
        top_picks = analyze_top_picks(results)
    else:
        print("No suitable stocks found under $40")