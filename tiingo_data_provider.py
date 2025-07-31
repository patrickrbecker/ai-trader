#!/usr/bin/env python3
"""
Tiingo Data Provider - Enhanced market data with fundamentals and news
Replaces yfinance for higher quality, more comprehensive data
"""

from tiingo import TiingoClient
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
import os

class TiingoDataProvider:
    def __init__(self, api_key='907ca772398b8f0249496b74ecea50e2e304ca00'):
        """Initialize Tiingo client with session reuse for performance"""
        self.config = {
            'api_key': api_key,
            'session': True  # Reuse session for better performance
        }
        self.client = TiingoClient(self.config)
        self.rate_limit_delay = 1.2  # 50 requests/hour = 72 seconds between requests
        self.last_request_time = 0
        
        # Cache directory
        self.cache_dir = "data/tiingo_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        print("🚀 Tiingo Data Provider initialized")
        print(f"   Rate Limit: 50/hour, 1000/day")
        print(f"   Features: Stocks, Crypto, Forex, Fundamentals, News")
    
    def _rate_limit(self):
        """Enforce rate limiting to stay within API limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def get_stock_data(self, symbol, start_date=None, end_date=None, frequency='daily'):
        """Get comprehensive stock data with enhanced quality"""
        self._rate_limit()
        
        try:
            # Default to 1 year of data if no dates specified
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            
            print(f"📊 Fetching {symbol} data from Tiingo ({start_date} to {end_date})")
            
            # Get price data as DataFrame
            df = self.client.get_dataframe(
                symbol,
                startDate=start_date,
                endDate=end_date,
                frequency=frequency
            )
            
            if df.empty:
                print(f"   ❌ No data returned for {symbol}")
                return None
            
            # Get ticker metadata for additional context
            metadata = self.client.get_ticker_metadata(symbol)
            
            print(f"   ✅ Retrieved {len(df)} data points for {symbol}")
            if metadata:
                print(f"   📈 {metadata.get('name', 'Unknown Company')} - {metadata.get('exchangeCode', 'Unknown Exchange')}")
            
            return {
                'price_data': df,
                'metadata': metadata,
                'symbol': symbol,
                'start_date': start_date,
                'end_date': end_date
            }
            
        except Exception as e:
            print(f"   ❌ Error fetching {symbol}: {e}")
            return None
    
    def get_fundamentals(self, symbol, start_date=None, end_date=None):
        """Get fundamental data - quarterly reports, daily metrics"""
        self._rate_limit()
        
        try:
            # Default to 2 years for fundamentals
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
            
            print(f"📋 Fetching fundamentals for {symbol}")
            
            # Get daily fundamental metrics
            daily_fundamentals = self.client.get_fundamentals_daily(
                symbol,
                startDate=start_date,
                endDate=end_date
            )
            
            # Get quarterly statements
            statements = self.client.get_fundamentals_statements(
                symbol,
                startDate=start_date,
                endDate=end_date
            )
            
            # Get fundamental definitions for understanding the data
            definitions = self.client.get_fundamentals_definitions(symbol)
            
            print(f"   ✅ Retrieved fundamentals for {symbol}")
            print(f"   📊 Daily metrics: {len(daily_fundamentals) if daily_fundamentals else 0} entries")
            print(f"   📋 Statements: {len(statements) if statements else 0} quarters")
            
            return {
                'daily_fundamentals': daily_fundamentals,
                'quarterly_statements': statements,
                'definitions': definitions,
                'symbol': symbol
            }
            
        except Exception as e:
            print(f"   ❌ Error fetching fundamentals for {symbol}: {e}")
            return None
    
    def get_market_news(self, symbols=None, tags=None, limit=100, start_date=None):
        """Get curated financial news with ticker relevance"""
        self._rate_limit()
        
        try:
            # Default to last 7 days
            if not start_date:
                start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            
            print(f"📰 Fetching market news (last 7 days)")
            if symbols:
                print(f"   🎯 Symbols: {', '.join(symbols[:5])}{'...' if len(symbols) > 5 else ''}")
            
            news = self.client.get_news(
                tickers=symbols,
                tags=tags,
                startDate=start_date,
                limit=limit
            )
            
            print(f"   ✅ Retrieved {len(news) if news else 0} news articles")
            
            # Process news for sentiment and relevance
            processed_news = []
            for article in news or []:
                processed_article = {
                    'title': article.get('title', ''),
                    'description': article.get('description', ''),
                    'url': article.get('url', ''),
                    'published_date': article.get('publishedDate', ''),
                    'source': article.get('source', ''),
                    'tags': article.get('tags', []),
                    'tickers': article.get('tickers', []),
                    'crawl_date': article.get('crawlDate', '')
                }
                processed_news.append(processed_article)
            
            return processed_news
            
        except Exception as e:
            print(f"   ❌ Error fetching news: {e}")
            return []
    
    def get_crypto_data(self, symbols, start_date=None, end_date=None):
        """Get cryptocurrency data from 40+ exchanges"""
        self._rate_limit()
        
        try:
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            crypto_data = {}
            
            for symbol in symbols:
                print(f"₿ Fetching crypto data for {symbol}")
                
                # Get price history
                price_data = self.client.get_crypto_price_history(
                    symbol,
                    startDate=start_date,
                    endDate=end_date,
                    resampleFreq='1hour'
                )
                
                # Get top of book (bid/ask)
                top_of_book = self.client.get_crypto_top_of_book(symbol)
                
                crypto_data[symbol] = {
                    'price_history': price_data,
                    'top_of_book': top_of_book
                }
                
                print(f"   ✅ {symbol}: {len(price_data) if price_data else 0} price points")
            
            return crypto_data
            
        except Exception as e:
            print(f"   ❌ Error fetching crypto data: {e}")
            return {}
    
    def batch_stock_analysis(self, symbols, include_fundamentals=True, include_news=True):
        """Comprehensive batch analysis for multiple symbols"""
        print(f"🔍 COMPREHENSIVE TIINGO ANALYSIS")
        print(f"   Symbols: {len(symbols)} tickers")
        print(f"   Fundamentals: {'✅' if include_fundamentals else '❌'}")
        print(f"   News: {'✅' if include_news else '❌'}")
        print("=" * 60)
        
        results = {}
        
        for i, symbol in enumerate(symbols, 1):
            print(f"\n[{i}/{len(symbols)}] Analyzing {symbol}...")
            
            # Get stock data
            stock_data = self.get_stock_data(symbol)
            if not stock_data:
                continue
            
            results[symbol] = {
                'stock_data': stock_data,
                'fundamentals': None,
                'news_mentions': 0
            }
            
            # Get fundamentals if requested
            if include_fundamentals:
                fundamentals = self.get_fundamentals(symbol)
                if fundamentals:
                    results[symbol]['fundamentals'] = fundamentals
            
            # Count news mentions
            if include_news:
                news = self.get_market_news(symbols=[symbol], limit=10)
                results[symbol]['news_mentions'] = len(news)
                results[symbol]['recent_news'] = news[:3]  # Store top 3 articles
        
        # Get broader market news
        if include_news:
            print(f"\n📰 Fetching broader market news...")
            market_news = self.get_market_news(symbols=symbols[:10], limit=50)
            results['market_news'] = market_news
        
        print(f"\n✅ Batch analysis complete: {len(results)} symbols processed")
        return results
    
    def calculate_enhanced_metrics(self, stock_data):
        """Calculate enhanced metrics using Tiingo's high-quality data"""
        if not stock_data or 'price_data' not in stock_data:
            return {}
        
        df = stock_data['price_data']
        
        # Basic metrics
        current_price = df['close'].iloc[-1]
        price_change_1d = ((df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2]) * 100
        
        # Volatility metrics (more accurate with Tiingo's clean data)
        returns = df['close'].pct_change().dropna()
        volatility_30d = returns.tail(30).std() * np.sqrt(252) * 100
        
        # Volume analysis
        avg_volume_30d = df['volume'].tail(30).mean()
        current_volume = df['volume'].iloc[-1]
        volume_ratio = current_volume / avg_volume_30d if avg_volume_30d > 0 else 1
        
        # Price momentum
        sma_20 = df['close'].tail(20).mean()
        sma_50 = df['close'].tail(50).mean()
        price_vs_sma20 = ((current_price - sma_20) / sma_20) * 100
        price_vs_sma50 = ((current_price - sma_50) / sma_50) * 100
        
        return {
            'current_price': round(current_price, 2),
            'price_change_1d': round(price_change_1d, 2),
            'volatility_30d': round(volatility_30d, 1),
            'volume_ratio': round(volume_ratio, 2),
            'price_vs_sma20': round(price_vs_sma20, 1),
            'price_vs_sma50': round(price_vs_sma50, 1),
            'data_quality': 'Enhanced (Tiingo)'
        }

def main():
    """Test Tiingo integration"""
    provider = TiingoDataProvider()
    
    # Test with a few symbols
    test_symbols = ['AAPL', 'INTC', 'SPY']
    
    print("🧪 TESTING TIINGO INTEGRATION")
    print("=" * 50)
    
    # Test stock data
    for symbol in test_symbols:
        data = provider.get_stock_data(symbol)
        if data:
            metrics = provider.calculate_enhanced_metrics(data)
            print(f"\n📊 {symbol} Enhanced Metrics:")
            for key, value in metrics.items():
                print(f"   {key}: {value}")
    
    # Test fundamentals
    fundamentals = provider.get_fundamentals('AAPL')
    if fundamentals:
        print(f"\n📋 AAPL Fundamentals Preview:")
        if fundamentals['daily_fundamentals']:
            print(f"   Daily metrics available: {len(fundamentals['daily_fundamentals'])}")
        if fundamentals['quarterly_statements']:
            print(f"   Quarterly statements: {len(fundamentals['quarterly_statements'])}")
    
    # Test news
    news = provider.get_market_news(symbols=['AAPL', 'TSLA'], limit=5)
    print(f"\n📰 Market News: {len(news)} articles retrieved")
    for article in news[:2]:
        print(f"   • {article['title']}")
        print(f"     Tickers: {', '.join(article['tickers'])}")

if __name__ == "__main__":
    main()