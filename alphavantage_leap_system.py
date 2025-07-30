#!/usr/bin/env python3
"""
LEAP Capital Management - Historical LEAP Analysis System
Using Alpha Vantage API for backtesting optimal exit strategies
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
from scipy.stats import norm
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

class LEAPCapitalSystem:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.rate_limit_delay = 12  # 5 calls per minute
        
    def get_historical_options(self, symbol, date):
        """Get historical options chain for specific date"""
        params = {
            'function': 'HISTORICAL_OPTIONS',
            'symbol': symbol,
            'date': date,
            'apikey': self.api_key
        }
        
        try:
            print(f"Fetching options data for {symbol} on {date}...")
            response = requests.get(self.base_url, params=params)
            data = response.json()
            
            # Rate limiting
            time.sleep(self.rate_limit_delay)
            
            if 'data' in data:
                return pd.DataFrame(data['data'])
            else:
                print(f"No options data for {symbol} on {date}: {data}")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"Error fetching options: {e}")
            return pd.DataFrame()
    
    def get_stock_price_history(self, symbol, months_back=24):
        """Get stock price history for analysis"""
        params = {
            'function': 'TIME_SERIES_DAILY_ADJUSTED',
            'symbol': symbol,
            'outputsize': 'full',
            'apikey': self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            data = response.json()
            time.sleep(self.rate_limit_delay)
            
            if 'Time Series (Daily)' in data:
                df = pd.DataFrame(data['Time Series (Daily)']).T
                df.index = pd.to_datetime(df.index)
                df = df.astype(float)
                df.columns = ['open', 'high', 'low', 'close', 'adj_close', 'volume', 'dividend', 'split']
                return df.sort_index()
            else:
                print(f"Error fetching stock data: {data}")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"Error: {e}")
            return pd.DataFrame()
    
    def calculate_black_scholes(self, S, K, T, r, sigma, option_type='call'):
        """Calculate Black-Scholes option price"""
        try:
            if T <= 0 or sigma <= 0:
                return 0
                
            d1 = (np.log(S/K) + (r + sigma**2/2) * T) / (sigma * np.sqrt(T))
            d2 = d1 - sigma * np.sqrt(T)
            
            if option_type == 'call':
                price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
            else:
                price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
                
            return max(0, price)
        except:
            return 0
    
    def calculate_greeks(self, S, K, T, r, sigma):
        """Calculate option Greeks"""
        try:
            if T <= 0 or sigma <= 0:
                return 0, 0, 0, 0
                
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
    
    def analyze_leap_exit_timing(self, symbol, entry_date, strike, expiry_date, entry_price):
        """
        Analyze optimal exit timing for a LEAP position
        """
        print(f"\nAnalyzing LEAP: {symbol} ${strike} Call expiring {expiry_date}")
        print(f"Entry: {entry_date} at ${entry_price}")
        
        # Get stock price history from entry to expiry
        stock_data = self.get_stock_price_history(symbol)
        if stock_data.empty:
            return None
        
        # Filter data from entry to expiry
        entry_dt = pd.to_datetime(entry_date)
        expiry_dt = pd.to_datetime(expiry_date)
        
        relevant_data = stock_data[
            (stock_data.index >= entry_dt) & 
            (stock_data.index <= expiry_dt)
        ].copy()
        
        if relevant_data.empty:
            print("No stock data in date range")
            return None
        
        # Calculate theoretical option values over time
        results = []
        risk_free_rate = 0.05  # 5% assumption
        
        for date, row in relevant_data.iterrows():
            stock_price = row['close']
            days_to_expiry = (expiry_dt - date).days
            time_to_expiry = days_to_expiry / 365.0
            
            if time_to_expiry <= 0:
                # At expiry
                intrinsic_value = max(0, stock_price - strike)
                theoretical_price = intrinsic_value
                delta = 1 if stock_price > strike else 0
                theta = 0
                gamma = 0
                vega = 0
            else:
                # Estimate implied volatility (simplified)
                volatility = relevant_data['close'].pct_change().std() * np.sqrt(252)
                
                theoretical_price = self.calculate_black_scholes(
                    stock_price, strike, time_to_expiry, risk_free_rate, volatility
                )
                
                delta, theta, gamma, vega = self.calculate_greeks(
                    stock_price, strike, time_to_expiry, risk_free_rate, volatility
                )
            
            # Calculate P&L
            pnl = theoretical_price - entry_price
            pnl_pct = (pnl / entry_price) * 100 if entry_price > 0 else 0
            
            # Exit signals
            profit_target_25 = pnl_pct >= 25
            profit_target_50 = pnl_pct >= 50
            profit_target_100 = pnl_pct >= 100
            
            theta_acceleration = days_to_expiry <= 90 and theta < -0.05
            time_decay_warning = days_to_expiry <= 60
            
            results.append({
                'date': date,
                'stock_price': stock_price,
                'days_to_expiry': days_to_expiry,
                'theoretical_price': theoretical_price,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'delta': delta,
                'theta': theta,
                'gamma': gamma,
                'vega': vega,
                'profit_target_25': profit_target_25,
                'profit_target_50': profit_target_50,
                'profit_target_100': profit_target_100,
                'theta_acceleration': theta_acceleration,
                'time_decay_warning': time_decay_warning
            })
        
        return pd.DataFrame(results)
    
    def backtest_leap_strategy(self, symbol, test_cases):
        """
        Backtest LEAP exit strategies on historical data
        test_cases: list of dicts with entry_date, strike, expiry_date, entry_price
        """
        results = []
        
        for i, case in enumerate(test_cases):
            print(f"\n{'='*60}")
            print(f"BACKTEST {i+1}/{len(test_cases)}")
            
            analysis = self.analyze_leap_exit_timing(
                symbol, 
                case['entry_date'],
                case['strike'], 
                case['expiry_date'],
                case['entry_price']
            )
            
            if analysis is None or analysis.empty:
                continue
            
            # Find optimal exit points
            optimal_exits = self.find_optimal_exits(analysis)
            
            case_result = {
                'case': i+1,
                'symbol': symbol,
                'entry_date': case['entry_date'],
                'strike': case['strike'],
                'expiry_date': case['expiry_date'],
                'entry_price': case['entry_price'],
                'max_profit_pct': analysis['pnl_pct'].max(),
                'final_pnl_pct': analysis['pnl_pct'].iloc[-1],
                'optimal_exits': optimal_exits
            }
            
            results.append(case_result)
            
            # Save detailed analysis
            analysis.to_csv(f'leap_analysis_{symbol}_{i+1}.csv', index=False)
            
        return results
    
    def find_optimal_exits(self, analysis_df):
        """Find optimal exit points based on our criteria"""
        exits = []
        
        # 25% profit target
        profit_25_hits = analysis_df[analysis_df['profit_target_25']]
        if not profit_25_hits.empty:
            first_25 = profit_25_hits.iloc[0]
            exits.append({
                'trigger': '25% Profit Target',
                'date': first_25['date'],
                'pnl_pct': first_25['pnl_pct'],
                'days_held': len(analysis_df) - first_25.name
            })
        
        # 50% profit target
        profit_50_hits = analysis_df[analysis_df['profit_target_50']]
        if not profit_50_hits.empty:
            first_50 = profit_50_hits.iloc[0]
            exits.append({
                'trigger': '50% Profit Target', 
                'date': first_50['date'],
                'pnl_pct': first_50['pnl_pct'],
                'days_held': len(analysis_df) - first_50.name
            })
        
        # Theta acceleration warning
        theta_warnings = analysis_df[analysis_df['theta_acceleration']]
        if not theta_warnings.empty:
            first_theta = theta_warnings.iloc[0]
            exits.append({
                'trigger': 'Theta Acceleration',
                'date': first_theta['date'],
                'pnl_pct': first_theta['pnl_pct'],
                'days_held': len(analysis_df) - first_theta.name
            })
        
        return exits

def main():
    """Demo the LEAP analysis system"""
    
    print("LEAP CAPITAL MANAGEMENT - Historical Analysis System")
    print("="*60)
    
    api_key = "YOUR_API_KEY_HERE"  # Replace with your Alpha Vantage API key
    system = LEAPCapitalSystem(api_key)
    
    # Test cases - Historical LEAP positions
    test_symbol = "AAPL"
    
    test_cases = [
        {
            'entry_date': '2023-01-15',
            'strike': 150,
            'expiry_date': '2024-01-19', 
            'entry_price': 10.50
        },
        {
            'entry_date': '2023-06-15',
            'strike': 180,
            'expiry_date': '2024-06-21',
            'entry_price': 8.25
        }
    ]
    
    print(f"\nBacktesting LEAP strategies for {test_symbol}")
    print(f"Test cases: {len(test_cases)}")
    print("\nNOTE: This will take several minutes due to API rate limits...")
    
    # Run backtest
    results = system.backtest_leap_strategy(test_symbol, test_cases)
    
    # Summary
    print(f"\n{'='*60}")
    print("BACKTEST RESULTS SUMMARY")
    print(f"{'='*60}")
    
    for result in results:
        print(f"\nCase {result['case']}: {result['symbol']} ${result['strike']} Call")
        print(f"Entry: {result['entry_date']} @ ${result['entry_price']}")
        print(f"Max Profit: {result['max_profit_pct']:.1f}%")
        print(f"Final P&L: {result['final_pnl_pct']:.1f}%")
        
        print("Optimal Exit Points:")
        for exit in result['optimal_exits']:
            print(f"  - {exit['trigger']}: {exit['pnl_pct']:.1f}% on {exit['date'].strftime('%Y-%m-%d')}")
    
    print(f"\nDetailed analysis saved to CSV files.")
    print("Ready to build live system once historical performance is validated.")

if __name__ == "__main__":
    main()