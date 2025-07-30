#!/usr/bin/env python3
"""
Professional LEAP Options Screener
Built for identifying profitable LEAP opportunities using Yahoo Finance data
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy.stats import norm
import math
import warnings
warnings.filterwarnings('ignore')

class LEAPScreener:
    def __init__(self):
        self.risk_free_rate = 0.05  # 5% risk-free rate assumption
        
    def get_options_chain(self, symbol):
        """Fetch options chain for a given symbol"""
        try:
            ticker = yf.Ticker(symbol)
            expiry_dates = ticker.options
            
            # Filter for LEAP expiries (>= 1 year out)
            leap_dates = []
            current_date = datetime.now()
            
            for date in expiry_dates:
                expiry = datetime.strptime(date, '%Y-%m-%d')
                days_to_expiry = (expiry - current_date).days
                if days_to_expiry >= 365:  # LEAP criteria
                    leap_dates.append(date)
            
            return ticker, leap_dates[:3]  # Limit to first 3 LEAP dates
            
        except Exception as e:
            print(f"Error fetching options for {symbol}: {e}")
            return None, []
    
    def calculate_black_scholes(self, S, K, T, r, sigma, option_type='call'):
        """Calculate Black-Scholes option price"""
        try:
            d1 = (np.log(S/K) + (r + sigma**2/2) * T) / (sigma * np.sqrt(T))
            d2 = d1 - sigma * np.sqrt(T)
            
            if option_type == 'call':
                price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
            else:
                price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
                
            return price
        except:
            return 0
    
    def calculate_greeks(self, S, K, T, r, sigma):
        """Calculate option Greeks"""
        try:
            d1 = (np.log(S/K) + (r + sigma**2/2) * T) / (sigma * np.sqrt(T))
            d2 = d1 - sigma * np.sqrt(T)
            
            # Delta
            delta = norm.cdf(d1)
            
            # Theta (daily)
            theta = -(S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) + 
                     r * K * np.exp(-r * T) * norm.cdf(d2)) / 365
            
            # Gamma
            gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
            
            # Vega (per 1% change in IV)
            vega = S * norm.pdf(d1) * np.sqrt(T) / 100
            
            return delta, theta, gamma, vega
        except:
            return 0, 0, 0, 0
    
    def analyze_leap(self, symbol, expiry_date):
        """Analyze LEAP options for a specific symbol and expiry"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get current stock price
            hist = ticker.history(period="5d")
            current_price = hist['Close'].iloc[-1]
            
            # Get options chain
            opt_chain = ticker.option_chain(expiry_date)
            calls = opt_chain.calls
            
            # Calculate time to expiry
            expiry = datetime.strptime(expiry_date, '%Y-%m-%d')
            days_to_expiry = (expiry - datetime.now()).days
            time_to_expiry = days_to_expiry / 365.0
            
            results = []
            
            for _, option in calls.iterrows():
                strike = option['strike']
                last_price = option['lastPrice']
                bid = option['bid']
                ask = option['ask']
                volume = option['volume']
                open_interest = option['openInterest']
                implied_vol = option['impliedVolatility']
                
                # Skip if no meaningful data
                if bid == 0 or ask == 0 or implied_vol == 0:
                    continue
                
                # Calculate mid price
                mid_price = (bid + ask) / 2
                
                # Calculate moneyness
                moneyness = current_price / strike
                
                # Calculate Greeks
                delta, theta, gamma, vega = self.calculate_greeks(
                    current_price, strike, time_to_expiry, self.risk_free_rate, implied_vol
                )
                
                # Calculate theoretical value
                theoretical_value = self.calculate_black_scholes(
                    current_price, strike, time_to_expiry, self.risk_free_rate, implied_vol
                )
                
                # Calculate edge (theoretical vs market price)
                edge = theoretical_value - mid_price
                edge_pct = (edge / mid_price) * 100 if mid_price > 0 else 0
                
                # Liquidity score (0-100)
                liquidity_score = min(100, (volume * 10 + open_interest) / 100)
                
                results.append({
                    'symbol': symbol,
                    'expiry': expiry_date,
                    'strike': strike,
                    'current_price': current_price,
                    'moneyness': moneyness,
                    'last_price': last_price,
                    'bid': bid,
                    'ask': ask,
                    'mid_price': mid_price,
                    'volume': volume,
                    'open_interest': open_interest,
                    'implied_vol': implied_vol,
                    'delta': delta,
                    'theta': theta,
                    'gamma': gamma,
                    'vega': vega,
                    'theoretical_value': theoretical_value,
                    'edge': edge,
                    'edge_pct': edge_pct,
                    'liquidity_score': liquidity_score,
                    'days_to_expiry': days_to_expiry
                })
            
            return results
            
        except Exception as e:
            print(f"Error analyzing LEAP for {symbol} {expiry_date}: {e}")
            return []
    
    def screen_symbols(self, symbols):
        """Screen multiple symbols for LEAP opportunities"""
        all_results = []
        
        print(f"Screening {len(symbols)} symbols for LEAP opportunities...")
        
        for i, symbol in enumerate(symbols):
            print(f"Processing {symbol} ({i+1}/{len(symbols)})")
            
            ticker, leap_dates = self.get_options_chain(symbol)
            if not leap_dates:
                continue
            
            for expiry_date in leap_dates:
                results = self.analyze_leap(symbol, expiry_date)
                all_results.extend(results)
        
        return pd.DataFrame(all_results)
    
    def apply_filters(self, df):
        """Apply LEAP screening filters"""
        if df.empty:
            return df
        
        # Filter criteria
        filtered = df[
            (df['moneyness'] >= 0.8) &      # Not too far OTM
            (df['moneyness'] <= 1.2) &      # Not too far ITM
            (df['delta'] >= 0.3) &          # Meaningful delta
            (df['delta'] <= 0.8) &          # Not too close to stock
            (df['liquidity_score'] >= 10) & # Minimum liquidity
            (df['implied_vol'] >= 0.15) &   # Minimum IV
            (df['implied_vol'] <= 0.6) &    # Maximum IV
            (df['bid'] > 0) &               # Valid bid
            (df['ask'] > 0)                 # Valid ask
        ].copy()
        
        return filtered
    
    def rank_opportunities(self, df):
        """Rank LEAP opportunities by attractiveness"""
        if df.empty:
            return df
        
        # Create composite score
        df['rank_score'] = (
            df['edge_pct'] * 0.3 +                    # Theoretical edge
            df['liquidity_score'] * 0.2 +            # Liquidity
            (1 - abs(df['moneyness'] - 1)) * 50 * 0.2 + # Close to ATM
            df['delta'] * 50 * 0.15 +                # Delta exposure
            (365 - df['days_to_expiry']) / 365 * 25 * 0.15  # Time preference
        )
        
        return df.sort_values('rank_score', ascending=False)

def main():
    """Main execution function"""
    screener = LEAPScreener()
    
    # High-volume, liquid stocks suitable for LEAPs
    symbols = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA',
        'NVDA', 'META', 'NFLX', 'AMD', 'CRM',
        'JPM', 'BAC', 'XOM', 'JNJ', 'PG'
    ]
    
    # Screen for opportunities
    results_df = screener.screen_symbols(symbols)
    
    if results_df.empty:
        print("No LEAP opportunities found.")
        return
    
    # Apply filters
    filtered_df = screener.apply_filters(results_df)
    
    if filtered_df.empty:
        print("No LEAP opportunities passed filters.")
        return
    
    # Rank opportunities
    ranked_df = screener.rank_opportunities(filtered_df)
    
    # Display top opportunities
    print("\n" + "="*80)
    print("TOP LEAP OPPORTUNITIES")
    print("="*80)
    
    top_opportunities = ranked_df.head(10)
    
    for _, row in top_opportunities.iterrows():
        print(f"\n{row['symbol']} {row['expiry']} ${row['strike']:.0f} Call")
        print(f"Current Price: ${row['current_price']:.2f} | Strike: ${row['strike']:.0f} | Moneyness: {row['moneyness']:.2f}")
        print(f"Bid/Ask: ${row['bid']:.2f}/${row['ask']:.2f} | Mid: ${row['mid_price']:.2f}")
        print(f"Delta: {row['delta']:.3f} | Theta: ${row['theta']:.2f} | IV: {row['implied_vol']:.1%}")
        print(f"Theoretical Edge: {row['edge_pct']:.1f}% | Liquidity Score: {row['liquidity_score']:.0f}")
        print(f"Volume: {row['volume']:.0f} | Open Interest: {row['open_interest']:.0f}")
        print(f"Rank Score: {row['rank_score']:.1f}")
        print("-" * 60)
    
    # Save to CSV
    ranked_df.to_csv('leap_opportunities.csv', index=False)
    print(f"\nFull results saved to: leap_opportunities.csv")
    print(f"Total opportunities found: {len(ranked_df)}")

if __name__ == "__main__":
    main()