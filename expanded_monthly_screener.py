#!/usr/bin/env python3
"""
Monthly Options Screener on Expanded Universe
87 symbols across 8 categories for maximum opportunities
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
import os
from expanded_universe_screener import UniverseManager

class ExpandedMonthlyScreener:
    def __init__(self):
        self.universe_manager = UniverseManager()
        self.target_dte_min = 25
        self.target_dte_max = 45
        self.max_premium = 2.50  # $250 max per contract
        self.min_volume = 20
        self.min_oi = 50
        self.max_spread_pct = 15
        
    def screen_expanded_universe(self):
        """Screen all 87 symbols for monthly options opportunities"""
        print('🎯 MONTHLY OPTIONS SCREENER - EXPANDED UNIVERSE (87 SYMBOLS)')
        print('Target: 25-45 days, $250 max, actionable opportunities')
        print('=' * 75)
        
        # Get our expanded universe
        all_symbols, categorized = self.universe_manager.get_comprehensive_universe()
        
        print(f"Screening {len(all_symbols)} symbols across 8 categories...")
        print("This will take 3-4 minutes due to API rate limits...\n")
        
        all_opportunities = []
        category_stats = {}
        
        # Screen by category for organized results
        for category, symbols in categorized.items():
            print(f"\n📊 SCREENING {category.upper()} ({len(symbols)} symbols)")
            print("-" * 50)
            
            category_opportunities = []
            
            for symbol in symbols:
                try:
                    opportunities = self.analyze_symbol_monthly_options(symbol, category)
                    if opportunities:
                        category_opportunities.extend(opportunities)
                        all_opportunities.extend(opportunities)
                        print(f"   ✅ {symbol}: {len(opportunities)} opportunities")
                    else:
                        print(f"   ❌ {symbol}: No suitable options")
                        
                except Exception as e:
                    print(f"   ⚠️ {symbol}: Error - {e}")
                    continue
                    
                time.sleep(0.3)  # Rate limiting
            
            category_stats[category] = {
                'symbols_screened': len(symbols),
                'opportunities_found': len(category_opportunities)
            }
            
            print(f"   📊 {category.upper()} TOTAL: {len(category_opportunities)} opportunities")
        
        return all_opportunities, category_stats
    
    def analyze_symbol_monthly_options(self, symbol, category):
        """Analyze monthly options for a single symbol"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get current price and recent volatility
            hist = ticker.history(period='3mo')
            if hist.empty or len(hist) < 30:
                return []
            
            current_price = hist['Close'].iloc[-1]
            
            # Calculate monthly volatility estimate
            returns = hist['Close'].pct_change().dropna()
            monthly_vol_estimate = returns.std() * np.sqrt(22) * 100  # 22 trading days
            
            # Get target expiry
            expiries = ticker.options
            target_expiry = None
            days_to_exp = 0
            
            for expiry in expiries:
                days = (datetime.strptime(expiry, '%Y-%m-%d') - datetime.now()).days
                if self.target_dte_min <= days <= self.target_dte_max:
                    target_expiry = expiry
                    days_to_exp = days
                    break
            
            if not target_expiry:
                return []
            
            # Get options chain
            chain = ticker.option_chain(target_expiry)
            opportunities = []
            
            # Analyze calls
            for _, option in chain.calls.iterrows():
                opp = self.evaluate_monthly_option(
                    symbol, 'CALL', option, current_price, days_to_exp, 
                    monthly_vol_estimate, category
                )
                if opp:
                    opportunities.append(opp)
            
            # Analyze puts
            for _, option in chain.puts.iterrows():
                opp = self.evaluate_monthly_option(
                    symbol, 'PUT', option, current_price, days_to_exp,
                    monthly_vol_estimate, category
                )
                if opp:
                    opportunities.append(opp)
            
            return opportunities
            
        except Exception as e:
            return []
    
    def evaluate_monthly_option(self, symbol, option_type, option, current_price, 
                               days_to_exp, monthly_vol, category):
        """Evaluate individual option for monthly trading"""
        try:
            # Basic data extraction
            strike = option['strike']
            bid = option['bid'] if not pd.isna(option['bid']) else 0
            ask = option['ask'] if not pd.isna(option['ask']) else 0
            volume = option['volume'] if not pd.isna(option['volume']) else 0
            oi = option['openInterest'] if not pd.isna(option['openInterest']) else 0
            iv = option['impliedVolatility'] if not pd.isna(option['impliedVolatility']) else 0
            
            # Filter out bad options
            if (bid <= 0.05 or ask <= 0 or volume < self.min_volume or 
                oi < self.min_oi or iv <= 0):
                return None
            
            mid_price = (bid + ask) / 2
            spread_pct = ((ask - bid) / mid_price) * 100
            
            if mid_price > self.max_premium or spread_pct > self.max_spread_pct:
                return None
            
            # Calculate key metrics
            if option_type == 'CALL':
                moneyness = current_price / strike
                move_to_profit = ((strike - current_price) / current_price) * 100
                
                # Reasonable call range
                if not (0.90 <= moneyness <= 1.10):
                    return None
                    
            else:  # PUT
                moneyness = strike / current_price
                move_to_profit = ((current_price - strike) / current_price) * 100
                
                # Reasonable put range
                if not (0.90 <= moneyness <= 1.10):
                    return None
            
            # Calculate profit scenarios
            profit_scenarios = self.calculate_monthly_profit_scenarios(
                current_price, strike, mid_price, option_type
            )
            
            # Actionability score
            actionability = self.calculate_actionability_score(
                moneyness, spread_pct, volume, oi, abs(move_to_profit), monthly_vol
            )
            
            return {
                'symbol': symbol,
                'category': category,
                'option_type': option_type,
                'strike': strike,
                'expiry': f"2025-{target_expiry.split('-')[1]}-{target_expiry.split('-')[2]}",
                'days_to_exp': days_to_exp,
                'current_price': current_price,
                'premium': round(mid_price, 2),
                'bid': bid,
                'ask': ask,
                'spread_pct': round(spread_pct, 1),
                'volume': int(volume),
                'open_interest': int(oi),
                'iv_pct': round(iv * 100, 1),
                'moneyness': round(moneyness, 3),
                'move_to_profit': round(abs(move_to_profit), 1),
                'monthly_vol_estimate': round(monthly_vol, 1),
                'profit_5pct': profit_scenarios.get('5pct', 0),
                'profit_10pct': profit_scenarios.get('10pct', 0),
                'actionability_score': actionability
            }
            
        except Exception:
            return None
    
    def calculate_monthly_profit_scenarios(self, stock_price, strike, premium, option_type):
        """Calculate realistic profit scenarios for monthly options"""
        scenarios = {}
        
        for move_pct in [0.05, 0.10]:
            if option_type == 'CALL':
                new_price = stock_price * (1 + move_pct)
                if new_price > strike:
                    intrinsic = new_price - strike
                    # Estimate remaining time value (30% decay assumption)
                    estimated_value = intrinsic + (premium * 0.3)
                    profit = estimated_value - premium
                    profit_pct = (profit / premium) * 100 if profit > 0 else -70
                else:
                    profit_pct = -70  # Time decay loss
            else:  # PUT
                new_price = stock_price * (1 - move_pct)
                if new_price < strike:
                    intrinsic = strike - new_price
                    estimated_value = intrinsic + (premium * 0.3)
                    profit = estimated_value - premium
                    profit_pct = (profit / premium) * 100 if profit > 0 else -70
                else:
                    profit_pct = -70
            
            scenarios[f'{int(move_pct*100)}pct'] = round(profit_pct, 0)
        
        return scenarios
    
    def calculate_actionability_score(self, moneyness, spread_pct, volume, oi, 
                                    move_needed, monthly_vol):
        """Calculate how actionable this trade is"""
        score = 0
        
        # Moneyness score (prefer close to ATM)
        if 0.98 <= moneyness <= 1.02:
            score += 25
        elif 0.95 <= moneyness <= 1.05:
            score += 20
        else:
            score += 10
        
        # Liquidity score
        score += min(20, volume / 5)
        score += min(15, oi / 20)
        
        # Spread penalty
        score -= spread_pct * 0.5
        
        # Realistic move probability
        if move_needed <= monthly_vol:
            score += 20
        elif move_needed <= monthly_vol * 1.5:
            score += 15
        else:
            score += 5
        
        return max(0, round(score, 1))
    
    def rank_and_display_results(self, opportunities, category_stats):
        """Rank and display the best opportunities"""
        if not opportunities:
            print("\n❌ No monthly opportunities found in expanded universe!")
            return
        
        # Sort by actionability score
        ranked = sorted(opportunities, key=lambda x: x['actionability_score'], reverse=True)
        
        print(f"\n🏆 TOP 10 MONTHLY OPTIONS FROM EXPANDED UNIVERSE")
        print("=" * 80)
        
        for i, opp in enumerate(ranked[:10], 1):
            cost = opp['premium'] * 100
            print(f"\n#{i} ⚡ {opp['symbol']} ${opp['strike']:.0f} {opp['option_type']} ({opp['expiry']})")
            print(f"   💰 Cost: ${opp['premium']:.2f} (${cost:.0f} total)")
            print(f"   📊 Category: {opp['category'].title()} | Days: {opp['days_to_exp']}")
            print(f"   📈 Current: ${opp['current_price']:.2f} | Need: {opp['move_to_profit']:.1f}% move")
            print(f"   📊 Vol: {opp['volume']} | OI: {opp['open_interest']} | Spread: {opp['spread_pct']:.1f}%")
            print(f"   📈 Monthly Vol: {opp['monthly_vol_estimate']:.1f}%")
            
            if opp['profit_5pct'] > 0:
                profit_5 = (opp['profit_5pct'] / 100) * cost
                print(f"   💎 5% move: +{opp['profit_5pct']:.0f}% (${profit_5:.0f})")
            if opp['profit_10pct'] > 0:
                profit_10 = (opp['profit_10pct'] / 100) * cost
                print(f"   💎 10% move: +{opp['profit_10pct']:.0f}% (${profit_10:.0f})")
            
            print(f"   🏆 Actionability: {opp['actionability_score']:.1f}/100")
            print("-" * 60)
        
        # Category breakdown
        print(f"\n📊 OPPORTUNITIES BY CATEGORY:")
        for category, stats in category_stats.items():
            print(f"   {category.upper()}: {stats['opportunities_found']} opportunities from {stats['symbols_screened']} symbols")
        
        # Save results
        self.save_results(ranked, category_stats)
        
        print(f"\n✅ Found {len(ranked)} total opportunities from expanded universe")
        print("💡 Much better selection than the 16-symbol limitation!")

    def save_results(self, opportunities, category_stats):
        """Save screening results"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'total_opportunities': len(opportunities),
            'category_stats': category_stats,
            'top_10': opportunities[:10]
        }
        
        filename = f"data/screening_results/monthly_expanded_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Also save CSV for easy analysis
        df = pd.DataFrame(opportunities)
        csv_filename = f"data/screening_results/monthly_expanded_{timestamp}.csv"
        df.to_csv(csv_filename, index=False)
        
        print(f"💾 Results saved to {filename} and {csv_filename}")

def main():
    """Run expanded monthly options screening"""
    screener = ExpandedMonthlyScreener()
    
    # Screen all opportunities
    opportunities, category_stats = screener.screen_expanded_universe()
    
    # Rank and display results
    screener.rank_and_display_results(opportunities, category_stats)

if __name__ == "__main__":
    main()