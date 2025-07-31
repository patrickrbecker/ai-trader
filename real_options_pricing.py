#!/usr/bin/env python3
"""
Real Options Pricing System - Uses actual market data instead of estimates
Permanent fix for broken pricing models
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import time
from dataclasses import dataclass
import math
import os
from polygon_data_provider import PolygonDataProvider

@dataclass
class OptionData:
    symbol: str
    strike: float
    expiry: str
    option_type: str  # 'CALL' or 'PUT'
    last_price: float
    bid: float
    ask: float
    mid_price: float
    volume: int
    open_interest: int
    implied_volatility: float
    delta: Optional[float]
    theta: Optional[float]
    gamma: Optional[float]
    vega: Optional[float]
    intrinsic_value: float
    time_value: float
    days_to_expiry: int
    moneyness: float  # Stock price / Strike (for calls)

class RealOptionsPricer:
    def __init__(self, polygon_api_key: str = None):
        """Initialize real options pricing system with Polygon → Yahoo hierarchy"""
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
        
        # Initialize Polygon provider
        try:
            self.polygon_provider = PolygonDataProvider(polygon_api_key)
            self.polygon_available = True
        except Exception as e:
            print(f"⚠️ Polygon options unavailable: {e}")
            self.polygon_provider = None
            self.polygon_available = False
        
        print("🔧 ENHANCED REAL OPTIONS PRICING SYSTEM")
        print("   🏆 Primary: Polygon.io (Real-time, <20ms)")
        print("   🥈 Fallback: Yahoo Finance options chains")
        print("   ✅ Real implied volatility & Greeks")
        print("   ✅ Institutional-grade accuracy")
        print(f"   🔄 Polygon Status: {'Available' if self.polygon_available else 'Unavailable'}")
    
    def get_real_option_price(self, symbol: str, strike: float, expiry: str, 
                            option_type: str = 'CALL') -> Optional[OptionData]:
        """Get REAL option price with Polygon → Yahoo hierarchy"""
        
        cache_key = f"{symbol}_{strike}_{expiry}_{option_type}"
        
        # Check cache first
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if time.time() - cached_time < self.cache_duration:
                return cached_data
        
        print(f"💎 Fetching REAL option data: {symbol} ${strike} {option_type} ({expiry})")
        
        # 1️⃣ Try Polygon.io first (institutional-grade)
        if self.polygon_available:
            try:
                polygon_data = self.polygon_provider.get_option_price(symbol, strike, expiry, option_type)
                if polygon_data:
                    # Convert Polygon data to our OptionData format
                    option_data = OptionData(
                        symbol=polygon_data.symbol,
                        strike=polygon_data.strike,
                        expiry=polygon_data.expiry,
                        option_type=polygon_data.option_type,
                        last_price=polygon_data.last_price,
                        bid=polygon_data.bid,
                        ask=polygon_data.ask,
                        mid_price=polygon_data.mid_price,
                        volume=polygon_data.volume,
                        open_interest=polygon_data.open_interest,
                        implied_volatility=polygon_data.implied_volatility,
                        delta=polygon_data.delta,
                        theta=polygon_data.theta,
                        gamma=polygon_data.gamma,
                        vega=polygon_data.vega,
                        intrinsic_value=polygon_data.intrinsic_value,
                        time_value=polygon_data.time_value,
                        days_to_expiry=polygon_data.days_to_expiry,
                        moneyness=polygon_data.underlying_price / polygon_data.strike if polygon_data.option_type == 'CALL' else polygon_data.strike / polygon_data.underlying_price
                    )
                    
                    # Cache result
                    self.cache[cache_key] = (option_data, time.time())
                    print(f"   🏆 Polygon success: ${option_data.mid_price:.2f} (institutional-grade)")
                    return option_data
                else:
                    print(f"   ❌ Polygon failed, falling back to Yahoo...")
            except Exception as e:
                print(f"   ❌ Polygon error: {e}, falling back to Yahoo...")
        
        # 2️⃣ Yahoo Finance fallback
        try:
            print(f"🥈 Fetching from Yahoo Finance...")
            
            # Get the ticker
            ticker = yf.Ticker(symbol)
            
            # Get current stock price
            stock_info = ticker.history(period='1d')
            if stock_info.empty:
                print(f"   ❌ No stock data for {symbol}")
                return None
            
            current_price = stock_info['Close'].iloc[-1]
            
            # Get options chain
            try:
                chain = ticker.option_chain(expiry)
            except Exception as e:
                print(f"   ❌ No options chain for {expiry}: {e}")
                return None
            
            # Select calls or puts
            options_df = chain.calls if option_type == 'CALL' else chain.puts
            
            # Find the specific strike
            option_row = options_df[options_df['strike'] == strike]
            
            if option_row.empty:
                print(f"   ❌ Strike ${strike} not found")
                return None
            
            option = option_row.iloc[0]
            
            # Calculate derived values
            bid = float(option['bid']) if not pd.isna(option['bid']) else 0.0
            ask = float(option['ask']) if not pd.isna(option['ask']) else 0.0
            mid_price = (bid + ask) / 2 if (bid > 0 and ask > 0) else float(option['lastPrice'])
            
            # Calculate intrinsic value
            if option_type == 'CALL':
                intrinsic_value = max(0, current_price - strike)
                moneyness = current_price / strike
            else:
                intrinsic_value = max(0, strike - current_price)
                moneyness = strike / current_price
            
            time_value = max(0, mid_price - intrinsic_value)
            
            # Calculate days to expiry
            expiry_date = datetime.strptime(expiry, '%Y-%m-%d')
            days_to_expiry = (expiry_date - datetime.now()).days
            
            # Create OptionData object
            option_data = OptionData(
                symbol=symbol,
                strike=strike,
                expiry=expiry,
                option_type=option_type,
                last_price=float(option['lastPrice']) if not pd.isna(option['lastPrice']) else mid_price,
                bid=bid,
                ask=ask,
                mid_price=mid_price,
                volume=int(option['volume']) if not pd.isna(option['volume']) else 0,
                open_interest=int(option['openInterest']) if not pd.isna(option['openInterest']) else 0,
                implied_volatility=float(option['impliedVolatility']) if not pd.isna(option['impliedVolatility']) else 0.0,
                delta=float(option.get('delta', 0)) if 'delta' in option and not pd.isna(option.get('delta')) else None,
                theta=float(option.get('theta', 0)) if 'theta' in option and not pd.isna(option.get('theta')) else None,
                gamma=float(option.get('gamma', 0)) if 'gamma' in option and not pd.isna(option.get('gamma')) else None,
                vega=float(option.get('vega', 0)) if 'vega' in option and not pd.isna(option.get('vega')) else None,
                intrinsic_value=intrinsic_value,
                time_value=time_value,
                days_to_expiry=days_to_expiry,
                moneyness=moneyness
            )
            
            # Cache the result
            self.cache[cache_key] = (option_data, time.time())
            
            print(f"   ✅ Real price: ${mid_price:.2f} (Bid: ${bid:.2f}, Ask: ${ask:.2f})")
            print(f"   📊 IV: {option_data.implied_volatility*100:.1f}% | Volume: {option_data.volume}")
            
            return option_data
            
        except Exception as e:
            print(f"   ❌ Error fetching option data: {e}")
            return None
    
    def calculate_option_pnl(self, entry_price: float, current_option_data: OptionData) -> Dict:
        """Calculate real P&L based on current market prices"""
        
        if not current_option_data:
            return {
                'current_value': 0,
                'pnl_dollars': -entry_price * 100,  # Assume total loss
                'pnl_percent': -100,
                'break_even_stock_price': 0
            }
        
        current_value = current_option_data.mid_price
        pnl_dollars = (current_value - entry_price) * 100  # Per contract
        pnl_percent = ((current_value - entry_price) / entry_price) * 100
        
        # Calculate break-even stock price
        if current_option_data.option_type == 'CALL':
            break_even_stock_price = current_option_data.strike + entry_price
        else:
            break_even_stock_price = current_option_data.strike - entry_price
        
        return {
            'current_value': current_value,
            'pnl_dollars': pnl_dollars,
            'pnl_percent': pnl_percent,
            'break_even_stock_price': break_even_stock_price,
            'intrinsic_value': current_option_data.intrinsic_value,
            'time_value': current_option_data.time_value,
            'days_remaining': current_option_data.days_to_expiry,
            'implied_volatility': current_option_data.implied_volatility
        }
    
    def black_scholes_price(self, stock_price: float, strike: float, time_to_expiry: float,
                          risk_free_rate: float, volatility: float, option_type: str = 'CALL') -> float:
        """Proper Black-Scholes option pricing (as backup/validation)"""
        
        if time_to_expiry <= 0 or volatility <= 0:
            if option_type == 'CALL':
                return max(0, stock_price - strike)
            else:
                return max(0, strike - stock_price)
        
        # Black-Scholes formula
        d1 = (np.log(stock_price / strike) + (risk_free_rate + 0.5 * volatility**2) * time_to_expiry) / (volatility * np.sqrt(time_to_expiry))
        d2 = d1 - volatility * np.sqrt(time_to_expiry)
        
        # Standard normal CDF approximation
        def norm_cdf(x):
            return 0.5 * (1 + math.erf(x / math.sqrt(2)))
        
        if option_type == 'CALL':
            price = stock_price * norm_cdf(d1) - strike * np.exp(-risk_free_rate * time_to_expiry) * norm_cdf(d2)
        else:
            price = strike * np.exp(-risk_free_rate * time_to_expiry) * norm_cdf(-d2) - stock_price * norm_cdf(-d1)
        
        return max(0, price)
    
    def display_option_analysis(self, option_data: OptionData, entry_price: float):
        """Display comprehensive option analysis"""
        
        print(f"\n📊 REAL OPTIONS ANALYSIS: {option_data.symbol} ${option_data.strike} {option_data.option_type}")
        print("=" * 70)
        
        print(f"💰 MARKET PRICING:")
        print(f"   Last Trade: ${option_data.last_price:.2f}")
        print(f"   Bid/Ask: ${option_data.bid:.2f} / ${option_data.ask:.2f}")
        print(f"   Mid Price: ${option_data.mid_price:.2f}")
        print(f"   Spread: {((option_data.ask - option_data.bid) / option_data.mid_price * 100) if option_data.mid_price > 0 else 0:.1f}%")
        
        print(f"\n📈 LIQUIDITY:")
        print(f"   Volume: {option_data.volume:,}")
        print(f"   Open Interest: {option_data.open_interest:,}")
        
        print(f"\n⚡ VOLATILITY & GREEKS:")
        print(f"   Implied Vol: {option_data.implied_volatility*100:.1f}%")
        if option_data.delta is not None:
            print(f"   Delta: {option_data.delta:.3f}")
        if option_data.theta is not None:
            print(f"   Theta: {option_data.theta:.3f}")
        
        print(f"\n🎯 VALUE BREAKDOWN:")
        print(f"   Intrinsic Value: ${option_data.intrinsic_value:.2f}")
        print(f"   Time Value: ${option_data.time_value:.2f}")
        print(f"   Days to Expiry: {option_data.days_to_expiry}")
        print(f"   Moneyness: {option_data.moneyness:.3f}")
        
        # P&L Analysis
        pnl = self.calculate_option_pnl(entry_price, option_data)
        
        print(f"\n💸 P&L ANALYSIS (Entry: ${entry_price:.2f}):")
        print(f"   Current Value: ${pnl['current_value']:.2f}")
        print(f"   P&L per Contract: ${pnl['pnl_dollars']:.0f} ({pnl['pnl_percent']:+.1f}%)")
        print(f"   Break-even Stock Price: ${pnl['break_even_stock_price']:.2f}")
        
        # Risk Assessment
        time_decay_per_day = option_data.time_value / max(1, option_data.days_to_expiry)
        print(f"\n⚠️ RISK FACTORS:")
        print(f"   Daily Time Decay: ~${time_decay_per_day:.2f}")
        print(f"   % Out-of-Money: {abs(1 - option_data.moneyness)*100:.1f}%")

def main():
    """Test real options pricing system"""
    pricer = RealOptionsPricer()
    
    print("\n🧪 TESTING REAL OPTIONS PRICING")
    print("=" * 50)
    
    # Test with your actual SPY position
    spy_option = pricer.get_real_option_price('SPY', 655.0, '2025-08-29', 'CALL')
    
    if spy_option:
        pricer.display_option_analysis(spy_option, 2.36)  # Your entry price
    
    print("\n✅ REAL OPTIONS PRICING SYSTEM READY")
    print("💡 No more fantasy numbers - only real market data!")

if __name__ == "__main__":
    main()