#!/usr/bin/env python3
"""
LEAP Capital Management - Monthly Options Profit Maximizer
Focus: High-probability, high-profit monthly options plays
Strategy: Regular puts/calls with 30-60 day expiries
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import random
from scipy.stats import norm
import warnings
warnings.filterwarnings('ignore')

class MonthlyOptionsScreener:
    def __init__(self):
        self.min_volume = 100          # Higher volume requirement for monthlies
        self.min_open_interest = 500   # Need liquidity for quick exits
        self.max_spread_pct = 8        # Tighter spreads for frequent trading
        self.min_iv_rank = 20          # Minimum IV for decent premiums
        self.target_dte = (30, 60)     # 30-60 days to expiry
        
    def get_monthly_chains(self, symbol):
        """Get options chains for monthly expiries (30-60 days out)"""
        try:
            print(f"🔍 Scanning {symbol} for monthly options...")
            time.sleep(random.uniform(0.5, 1.0))
            
            ticker = yf.Ticker(symbol)
            stock_data = ticker.history(period="30d")
            if stock_data.empty:
                return None, []
            
            current_price = stock_data['Close'].iloc[-1]
            
            # Calculate recent volatility for context
            returns = stock_data['Close'].pct_change().dropna()
            realized_vol = returns.std() * np.sqrt(252) * 100
            
            # Get all expiry dates
            all_expiries = ticker.options
            monthly_expiries = []
            current_date = datetime.now()
            
            # Filter for monthly timeframe (30-60 days)
            for expiry in all_expiries:
                exp_date = datetime.strptime(expiry, '%Y-%m-%d')
                days_to_exp = (exp_date - current_date).days
                if self.target_dte[0] <= days_to_exp <= self.target_dte[1]:
                    monthly_expiries.append(expiry)
            
            if not monthly_expiries:
                print(f"   ❌ No monthly expiries found for {symbol}")
                return None, []
            
            print(f"   ✅ Found {len(monthly_expiries)} monthly expiries")
            return ticker, monthly_expiries, current_price, realized_vol
            
        except Exception as e:
            print(f"   ❌ Error with {symbol}: {e}")
            return None, []
    
    def analyze_monthly_opportunities(self, ticker, expiries, current_price, realized_vol, symbol):
        """Analyze monthly options for profit opportunities"""
        opportunities = []
        
        for expiry in expiries[:2]:  # Check first 2 monthly expiries
            try:
                print(f"   📅 Analyzing {expiry}...")
                time.sleep(1)
                
                chain = ticker.option_chain(expiry)
                calls = chain.calls
                puts = chain.puts
                
                days_to_exp = (datetime.strptime(expiry, '%Y-%m-%d') - datetime.now()).days
                
                # Analyze calls
                for _, call in calls.iterrows():
                    opp = self.evaluate_option(call, 'call', symbol, expiry, current_price, 
                                             days_to_exp, realized_vol)
                    if opp:
                        opportunities.append(opp)
                
                # Analyze puts  
                for _, put in puts.iterrows():
                    opp = self.evaluate_option(put, 'put', symbol, expiry, current_price,
                                             days_to_exp, realized_vol)
                    if opp:
                        opportunities.append(opp)
                        
            except Exception as e:
                print(f"   ⚠️ Error with {expiry}: {e}")
                continue
        
        return opportunities
    
    def evaluate_option(self, option, option_type, symbol, expiry, stock_price, days_to_exp, realized_vol):
        """Evaluate individual option for profit potential"""
        try:
            strike = option['strike']
            bid = option['bid'] if not pd.isna(option['bid']) else 0
            ask = option['ask'] if not pd.isna(option['ask']) else 0
            volume = option['volume'] if not pd.isna(option['volume']) else 0
            oi = option['openInterest'] if not pd.isna(option['openInterest']) else 0
            iv = option['impliedVolatility'] if not pd.isna(option['impliedVolatility']) else 0
            last_price = option['lastPrice'] if not pd.isna(option['lastPrice']) else 0
            
            # Basic filters
            if bid <= 0 or ask <= 0 or volume < self.min_volume or oi < self.min_open_interest:
                return None
            
            mid_price = (bid + ask) / 2
            spread_pct = ((ask - bid) / mid_price) * 100 if mid_price > 0 else 100
            
            if spread_pct > self.max_spread_pct:
                return None
            
            # Calculate key metrics
            moneyness = stock_price / strike if option_type == 'call' else strike / stock_price
            iv_pct = iv * 100
            
            # IV filter - need some volatility for profits
            if iv_pct < self.min_iv_rank:
                return None
            
            # Calculate profit potential scenarios
            profit_scenarios = self.calculate_profit_scenarios(
                stock_price, strike, mid_price, days_to_exp, iv, option_type
            )
            
            # Position sizing for different budgets
            contracts_250 = int(250 / (mid_price * 100)) if mid_price > 0 else 0
            contracts_500 = int(500 / (mid_price * 100)) if mid_price > 0 else 0
            
            return {
                'symbol': symbol,
                'option_type': option_type.upper(),
                'expiry': expiry,
                'strike': strike,
                'stock_price': stock_price,
                'moneyness': round(moneyness, 3),
                'bid': bid,
                'ask': ask,
                'mid_price': round(mid_price, 2),
                'spread_pct': round(spread_pct, 1),
                'volume': int(volume),
                'open_interest': int(oi),
                'iv_pct': round(iv_pct, 1),
                'days_to_exp': days_to_exp,
                'last_price': last_price,
                'contracts_250': contracts_250,
                'contracts_500': contracts_500,
                'profit_scenarios': profit_scenarios,
                'profit_score': self.calculate_profit_score(profit_scenarios, spread_pct, volume, oi)
            }
            
        except Exception as e:
            return None
    
    def calculate_profit_scenarios(self, stock_price, strike, premium, days_to_exp, iv, option_type):
        """Calculate profit scenarios for different stock moves"""
        scenarios = {}
        
        # Stock movement scenarios (5%, 10%, 15%, 20%)
        moves = [0.05, 0.10, 0.15, 0.20]
        
        for move in moves:
            if option_type == 'call':
                new_stock_price = stock_price * (1 + move)
                intrinsic = max(0, new_stock_price - strike)
            else:  # put
                new_stock_price = stock_price * (1 - move)
                intrinsic = max(0, strike - new_stock_price)
            
            # Simplified profit calculation (intrinsic value at expiry)
            profit = intrinsic - premium
            profit_pct = (profit / premium) * 100 if premium > 0 else 0
            
            scenarios[f'{move*100:.0f}%_move'] = {
                'new_stock_price': round(new_stock_price, 2),
                'option_value': round(intrinsic, 2),
                'profit': round(profit, 2),
                'profit_pct': round(profit_pct, 1)
            }
        
        return scenarios
    
    def calculate_profit_score(self, scenarios, spread_pct, volume, oi):
        """Calculate overall profit potential score"""
        # Average profit potential across scenarios
        avg_profit_pct = np.mean([s['profit_pct'] for s in scenarios.values()])
        
        # Liquidity score
        liquidity_score = min(50, volume/10 + oi/100)
        
        # Spread penalty
        spread_penalty = max(0, 20 - spread_pct)
        
        # Combined score
        total_score = avg_profit_pct * 0.6 + liquidity_score * 0.3 + spread_penalty * 0.1
        
        return round(total_score, 1)
    
    def screen_monthly_options(self, symbols):
        """Screen multiple symbols for monthly options opportunities"""
        all_opportunities = []
        
        print("🎯 MONTHLY OPTIONS PROFIT MAXIMIZER")
        print("=" * 60)
        print("Scanning for high-profit monthly options (30-60 days)")
        print("=" * 60)
        
        for symbol in symbols:
            result = self.get_monthly_chains(symbol)
            if not result or len(result) < 4:
                continue
                
            ticker, expiries, current_price, realized_vol = result
            opportunities = self.analyze_monthly_opportunities(
                ticker, expiries, current_price, realized_vol, symbol
            )
            all_opportunities.extend(opportunities)
        
        return pd.DataFrame(all_opportunities)
    
    def rank_by_profit_potential(self, df):
        """Rank options by profit potential"""
        if df.empty:
            return df
        
        # Sort by profit score descending
        return df.sort_values('profit_score', ascending=False)

def main():
    """Main monthly options screening"""
    screener = MonthlyOptionsScreener()
    
    # Focus on high-volume, volatile stocks good for monthly options
    monthly_candidates = [
        # Tech volatility plays
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META',
        # High volume ETFs
        'SPY', 'QQQ', 'IWM', 'XLF', 'XLE',
        # Volatile individual names
        'AMD', 'NFLX', 'CRM', 'UBER', 'PLTR',
        # Earnings/event driven
        'JPM', 'BAC', 'XOM', 'WMT', 'TGT'
    ]
    
    print(f"Screening {len(monthly_candidates)} symbols for monthly options...")
    print("Focus: Maximum profit potential with 30-60 day expiries\n")
    
    results = screener.screen_monthly_options(monthly_candidates)
    
    if results.empty:
        print("❌ No monthly options opportunities found!")
        return
    
    # Rank by profit potential
    ranked = screener.rank_by_profit_potential(results)
    
    print(f"\n🚀 TOP MONTHLY OPTIONS PROFIT OPPORTUNITIES")
    print("=" * 80)
    
    # Show top 10 opportunities
    top_opportunities = ranked.head(10)
    
    for idx, row in top_opportunities.iterrows():
        print(f"\n🎯 {row['symbol']} ${row['strike']:.0f} {row['option_type']} ({row['expiry']})")
        print(f"   💰 Stock: ${row['stock_price']:.2f} | Moneyness: {row['moneyness']:.3f}")
        print(f"   💵 Entry: ${row['mid_price']:.2f} | Spread: {row['spread_pct']:.1f}%")
        print(f"   📊 Vol: {row['volume']} | OI: {row['open_interest']:,} | IV: {row['iv_pct']:.1f}%")
        print(f"   📅 Days to Expiry: {row['days_to_exp']}")
        print(f"   💼 Contracts for $250: {row['contracts_250']} | $500: {row['contracts_500']}")
        
        # Show profit scenarios
        scenarios = row['profit_scenarios']
        print(f"   📈 PROFIT SCENARIOS:")
        for move, data in scenarios.items():
            if data['profit_pct'] > 0:
                print(f"      {move}: +{data['profit_pct']:.0f}% (${data['profit']:.2f}/contract)")
        
        print(f"   🏆 Profit Score: {row['profit_score']:.1f}/100")
        print("   " + "-" * 60)
    
    # Save results
    ranked.to_csv('monthly_options_opportunities.csv', index=False)
    print(f"\n💾 Full results saved to: monthly_options_opportunities.csv")
    print(f"📊 Total opportunities found: {len(ranked)}")
    
    # Summary stats
    high_profit = len(ranked[ranked['profit_score'] >= 50])
    medium_profit = len(ranked[(ranked['profit_score'] >= 30) & (ranked['profit_score'] < 50)])
    
    print(f"\n📊 PROFIT POTENTIAL BREAKDOWN:")
    print(f"   🚀 High Profit (≥50 score): {high_profit}")
    print(f"   💚 Medium Profit (30-50 score): {medium_profit}")
    print(f"   💡 Focus on top 5-10 opportunities for best risk/reward")

if __name__ == "__main__":
    main()