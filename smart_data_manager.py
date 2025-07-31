#!/usr/bin/env python3
"""
Smart Data Manager - Efficient caching + Tiingo/Yahoo fallback
Minimizes API calls while maintaining data quality
"""

import yfinance as yf
from tiingo_data_provider import TiingoDataProvider
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
import os
from typing import Dict, Optional, Any

class SmartDataManager:
    def __init__(self, tiingo_api_key='907ca772398b8f0249496b74ecea50e2e304ca00'):
        """Initialize with Tiingo primary, Yahoo fallback, and smart caching"""
        self.tiingo_provider = TiingoDataProvider(tiingo_api_key)
        self.cache = {}  # In-memory cache for session
        self.cache_dir = "data/smart_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # API usage tracking
        self.tiingo_requests_used = 0
        self.tiingo_hourly_limit = 50
        self.tiingo_daily_limit = 1000
        self.fallback_active = False
        
        print("🧠 Smart Data Manager initialized")
        print(f"   🥇 Primary: Tiingo (50/hour, 1000/day)")
        print(f"   🥈 Fallback: Yahoo Finance")
        print(f"   💾 Caching: Enabled")
    
    def _check_tiingo_limits(self) -> bool:
        """Check if we can use Tiingo or should fallback to Yahoo"""
        if self.tiingo_requests_used >= self.tiingo_hourly_limit:
            if not self.fallback_active:
                print(f"⚠️ Tiingo hourly limit reached ({self.tiingo_hourly_limit}). Switching to Yahoo fallback.")
                self.fallback_active = True
            return False
        return True
    
    def _get_cache_key(self, symbol: str, data_type: str, start_date: str, end_date: str) -> str:
        """Generate cache key for data"""
        return f"{symbol}_{data_type}_{start_date}_{end_date}"
    
    def _is_cache_valid(self, cache_key: str, max_age_minutes: int = 60) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache:
            return False
        
        cached_time = self.cache[cache_key].get('timestamp', 0)
        age_minutes = (time.time() - cached_time) / 60
        return age_minutes < max_age_minutes
    
    def get_stock_data(self, symbol: str, start_date: str = None, end_date: str = None, 
                      force_yahoo: bool = False) -> Optional[Dict]:
        """Get stock data with smart caching and fallback"""
        
        # Set default dates
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        # Check cache first
        cache_key = self._get_cache_key(symbol, 'stock', start_date, end_date)
        if self._is_cache_valid(cache_key):
            print(f"📦 Using cached data for {symbol}")
            return self.cache[cache_key]['data']
        
        # Determine data source
        use_tiingo = (not force_yahoo and 
                     self._check_tiingo_limits() and 
                     not self.fallback_active)
        
        if use_tiingo:
            # Try Tiingo first
            print(f"🥇 Fetching {symbol} from Tiingo...")
            try:
                data = self.tiingo_provider.get_stock_data(symbol, start_date, end_date)
                if data:
                    self.tiingo_requests_used += 1
                    # Cache the result
                    self.cache[cache_key] = {
                        'data': data,
                        'timestamp': time.time(),
                        'source': 'tiingo'
                    }
                    print(f"   ✅ Tiingo success ({self.tiingo_requests_used}/{self.tiingo_hourly_limit} used)")
                    return data
                else:
                    print(f"   ❌ Tiingo failed, falling back to Yahoo")
            except Exception as e:
                print(f"   ❌ Tiingo error: {e}, falling back to Yahoo")
        
        # Yahoo Finance fallback
        print(f"🥈 Fetching {symbol} from Yahoo...")
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date)
            
            if hist.empty:
                print(f"   ❌ No Yahoo data for {symbol}")
                return None
            
            # Convert to Tiingo-like format for consistency
            yahoo_data = {
                'price_data': hist,
                'metadata': {
                    'name': ticker.info.get('longName', 'Unknown'),
                    'exchangeCode': ticker.info.get('exchange', 'Unknown'),
                    'ticker': symbol
                },
                'symbol': symbol,
                'start_date': start_date,
                'end_date': end_date,
                'source': 'yahoo'
            }
            
            # Cache the result
            self.cache[cache_key] = {
                'data': yahoo_data,
                'timestamp': time.time(),
                'source': 'yahoo'
            }
            
            print(f"   ✅ Yahoo success (fallback mode)")
            return yahoo_data
            
        except Exception as e:
            print(f"   ❌ Yahoo error: {e}")
            return None
    
    def get_fundamentals(self, symbol: str, start_date: str = None, end_date: str = None) -> Optional[Dict]:
        """Get fundamentals with caching (Tiingo only - Yahoo doesn't have this)"""
        
        # Set default dates
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
        
        # Check cache first
        cache_key = self._get_cache_key(symbol, 'fundamentals', start_date, end_date)
        if self._is_cache_valid(cache_key, max_age_minutes=240):  # 4-hour cache for fundamentals
            print(f"📦 Using cached fundamentals for {symbol}")
            return self.cache[cache_key]['data']
        
        # Only available through Tiingo
        if not self._check_tiingo_limits() or self.fallback_active:
            print(f"   ⚠️ Fundamentals unavailable (Tiingo limit reached)")
            return None
        
        try:
            print(f"📋 Fetching fundamentals for {symbol} from Tiingo...")
            data = self.tiingo_provider.get_fundamentals(symbol, start_date, end_date)
            if data:
                self.tiingo_requests_used += 1
                # Cache the result
                self.cache[cache_key] = {
                    'data': data,
                    'timestamp': time.time(),
                    'source': 'tiingo'
                }
                print(f"   ✅ Fundamentals success ({self.tiingo_requests_used}/{self.tiingo_hourly_limit} used)")
                return data
            else:
                print(f"   ❌ No fundamental data available for {symbol}")
                return None
                
        except Exception as e:
            print(f"   ❌ Fundamentals error: {e}")
            return None
    
    def calculate_enhanced_metrics(self, stock_data: Dict) -> Dict:
        """Calculate enhanced metrics (works with both Tiingo and Yahoo data)"""
        if not stock_data or 'price_data' not in stock_data:
            return {}
        
        df = stock_data['price_data']
        source = stock_data.get('source', 'unknown')
        
        # Handle column name differences between Tiingo and Yahoo
        if 'Close' in df.columns:  # Yahoo format
            close_col = 'Close'
            volume_col = 'Volume'
        else:  # Tiingo format
            close_col = 'close'
            volume_col = 'volume'
        
        try:
            # Basic metrics
            current_price = df[close_col].iloc[-1]
            price_change_1d = ((df[close_col].iloc[-1] - df[close_col].iloc[-2]) / df[close_col].iloc[-2]) * 100
            
            # Volatility metrics
            returns = df[close_col].pct_change().dropna()
            volatility_30d = returns.tail(30).std() * np.sqrt(252) * 100
            
            # Volume analysis
            if volume_col in df.columns:
                avg_volume_30d = df[volume_col].tail(30).mean()
                current_volume = df[volume_col].iloc[-1]
                volume_ratio = current_volume / avg_volume_30d if avg_volume_30d > 0 else 1
            else:
                volume_ratio = 1.0
            
            # Price momentum
            sma_20 = df[close_col].tail(20).mean()
            sma_50 = df[close_col].tail(50).mean()
            price_vs_sma20 = ((current_price - sma_20) / sma_20) * 100
            price_vs_sma50 = ((current_price - sma_50) / sma_50) * 100
            
            return {
                'current_price': round(current_price, 2),
                'price_change_1d': round(price_change_1d, 2),
                'volatility_30d': round(volatility_30d, 1),
                'volume_ratio': round(volume_ratio, 2),
                'price_vs_sma20': round(price_vs_sma20, 1),
                'price_vs_sma50': round(price_vs_sma50, 1),
                'data_quality': f'Enhanced ({source.title()})'
            }
            
        except Exception as e:
            print(f"   ⚠️ Metrics calculation error: {e}")
            return {'data_quality': f'Error ({source.title()})'}
    
    def batch_analyze_symbols(self, symbols: list, include_fundamentals: bool = True) -> Dict:
        """Efficiently analyze multiple symbols with shared caching"""
        print(f"🚀 BATCH ANALYSIS: {len(symbols)} symbols")
        print(f"   Tiingo requests used: {self.tiingo_requests_used}/{self.tiingo_hourly_limit}")
        print(f"   Fundamentals: {'✅' if include_fundamentals else '❌'}")
        print("=" * 60)
        
        results = {}
        
        for i, symbol in enumerate(symbols, 1):
            print(f"\n[{i}/{len(symbols)}] Analyzing {symbol}...")
            
            # Get stock data (cached if available)
            stock_data = self.get_stock_data(symbol)
            if not stock_data:
                print(f"   ❌ No data available for {symbol}")
                continue
            
            # Calculate enhanced metrics
            enhanced_metrics = self.calculate_enhanced_metrics(stock_data)
            
            results[symbol] = {
                'stock_data': stock_data,
                'enhanced_metrics': enhanced_metrics,
                'fundamentals': None,
                'data_source': stock_data.get('source', 'unknown')
            }
            
            # Get fundamentals if requested and available
            if include_fundamentals and not self.fallback_active:
                fundamentals = self.get_fundamentals(symbol)
                if fundamentals:
                    results[symbol]['fundamentals'] = fundamentals
            
            print(f"   ✅ {symbol}: {enhanced_metrics.get('data_quality', 'Unknown quality')}")
            
            # Rate limiting check
            if self.tiingo_requests_used >= self.tiingo_hourly_limit - 2:
                print(f"   ⚠️ Approaching Tiingo limit, switching to Yahoo for remaining symbols")
                self.fallback_active = True
        
        print(f"\n📊 BATCH COMPLETE:")
        print(f"   Symbols analyzed: {len(results)}")
        print(f"   Tiingo requests used: {self.tiingo_requests_used}/{self.tiingo_hourly_limit}")
        print(f"   Cache hits: {len([r for r in self.cache.values() if time.time() - r['timestamp'] < 3600])}")
        
        return results
    
    def get_usage_stats(self) -> Dict:
        """Get current API usage statistics"""
        return {
            'tiingo_requests_used': self.tiingo_requests_used,
            'tiingo_hourly_limit': self.tiingo_hourly_limit,
            'tiingo_daily_limit': self.tiingo_daily_limit,
            'fallback_active': self.fallback_active,
            'cache_entries': len(self.cache),
            'requests_remaining': self.tiingo_hourly_limit - self.tiingo_requests_used
        }
    
    def reset_hourly_usage(self):
        """Reset hourly usage counter (call this manually or set up a timer)"""
        self.tiingo_requests_used = 0
        self.fallback_active = False
        print("🔄 Hourly Tiingo limit reset - back to premium data!")

def main():
    """Test smart data manager"""
    manager = SmartDataManager()
    
    # Test with a few symbols
    test_symbols = ['INTC', 'SPY', 'AAPL']
    
    print("🧪 TESTING SMART DATA MANAGER")
    print("=" * 50)
    
    # First run - should use Tiingo and cache
    results1 = manager.batch_analyze_symbols(test_symbols, include_fundamentals=True)
    
    print(f"\n" + "="*50)
    print("🔄 TESTING CACHE (immediate re-run)")
    
    # Second run - should use cache
    results2 = manager.batch_analyze_symbols(test_symbols, include_fundamentals=True)
    
    # Usage stats
    stats = manager.get_usage_stats()
    print(f"\n📊 USAGE STATISTICS:")
    for key, value in stats.items():
        print(f"   {key}: {value}")

if __name__ == "__main__":
    main()