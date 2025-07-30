#!/usr/bin/env python3
"""
Analyze the top 3 monthly put options from our screening
"""

import yfinance as yf
from datetime import datetime

def analyze_put_options():
    print('🎯 ANALYZING TOP 3 MONTHLY PUT RECOMMENDATIONS')
    print('=' * 60)

    # The top 3 puts from our earlier screening
    puts = [
        {'symbol': 'QQQ', 'strike': 500, 'expiry': '2025-09-05', 'premium': 1.15, 'name': 'QQQ $500 PUT'},
        {'symbol': 'SPY', 'strike': 581, 'expiry': '2025-09-19', 'premium': 2.65, 'name': 'SPY $581 PUT'},
        {'symbol': 'SPY', 'strike': 575, 'expiry': '2025-09-19', 'premium': 2.30, 'name': 'SPY $575 PUT'}
    ]

    for i, put in enumerate(puts, 1):
        print(f'\n📊 OPTION #{i}: {put["name"]} ({put["expiry"]})')
        print('-' * 50)
        
        # Get current data
        ticker = yf.Ticker(put['symbol'])
        current_price = ticker.history(period='1d')['Close'].iloc[-1]
        
        # Calculate key metrics
        moneyness = put['strike'] / current_price
        otm_pct = ((current_price - put['strike']) / current_price) * 100
        days_to_exp = (datetime.strptime(put['expiry'], '%Y-%m-%d') - datetime.now()).days
        
        print(f'Current {put["symbol"]} Price: ${current_price:.2f}')
        print(f'Strike Price: ${put["strike"]}')
        print(f'Premium: ${put["premium"]}')
        print(f'Moneyness: {moneyness:.3f} ({otm_pct:.1f}% OTM)')
        print(f'Days to Expiry: {days_to_exp}')
        
        # Break-even analysis
        breakeven = put['strike'] - put['premium']
        move_needed = ((current_price - breakeven) / current_price) * 100
        
        print(f'Break-even: ${breakeven:.2f}')
        print(f'Move needed for profit: -{move_needed:.1f}%')
        
        # Profit scenarios
        moves = [0.05, 0.10, 0.15, 0.20]
        print('Profit scenarios:')
        for move in moves:
            new_price = current_price * (1 - move)
            if new_price < put['strike']:
                intrinsic = put['strike'] - new_price
                profit = intrinsic - put['premium']
                profit_pct = (profit / put['premium']) * 100
                print(f'  -{move*100:.0f}% move (${new_price:.2f}): +${profit:.2f} (+{profit_pct:.0f}%)')
            else:
                print(f'  -{move*100:.0f}% move (${new_price:.2f}): Expires worthless (-100%)')

if __name__ == "__main__":
    analyze_put_options()