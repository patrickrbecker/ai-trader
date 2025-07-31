#!/usr/bin/env python3
"""
CORRECT TIINGO API TEST
Using proper endpoints and authentication from official documentation
"""

import os
import requests
import json
from dotenv import load_dotenv
import time
import yfinance as yf
from datetime import datetime, timedelta

load_dotenv()

def test_tiingo_proper():
    """Test Tiingo API using correct endpoints from documentation"""
    
    api_key = os.getenv('TIINGO_API_KEY')
    
    print("🔍 CORRECT TIINGO API TEST")
    print("=" * 50)
    print(f"API Key: {api_key[:8]}...{api_key[-4:]}")
    print("Using official Tiingo API endpoints...")
    print("=" * 50)
    
    # Test 1: End-of-day stock prices (correct endpoint)
    print("\n📈 TEST 1: End-of-Day Stock Prices")
    print("-" * 40)
    
    symbols = ['SPY', 'AAPL', 'TSLA']
    
    for symbol in symbols:
        print(f"\n🧪 {symbol}:")
        
        # Correct Tiingo endpoint format
        tiingo_start = time.time()
        try:
            # Official endpoint: https://api.tiingo.com/tiingo/daily/{ticker}
            url = f"https://api.tiingo.com/tiingo/daily/{symbol}?token={api_key}"
            response = requests.get(url)
            tiingo_time = time.time() - tiingo_start
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    # Tiingo returns metadata object
                    name = data.get('name', 'Unknown')
                    ticker = data.get('ticker', symbol)
                    print(f"   🔴 Tiingo Meta: {name} ({ticker}) - {tiingo_time:.2f}s")
                    
                    # Get latest price with prices endpoint
                    prices_url = f"https://api.tiingo.com/tiingo/daily/{symbol}/prices?token={api_key}"
                    prices_response = requests.get(prices_url)
                    
                    if prices_response.status_code == 200:
                        prices_data = prices_response.json()
                        if prices_data:
                            latest = prices_data[0]  # Most recent
                            tiingo_price = latest['close']
                            tiingo_date = latest['date'][:10]
                            print(f"   🔴 Tiingo Price: ${tiingo_price:.2f} ({tiingo_date})")
                        else:
                            print(f"   🔴 Tiingo: No price data")
                            tiingo_price = None
                    else:
                        print(f"   🔴 Tiingo Prices Error: {prices_response.status_code}")
                        tiingo_price = None
                else:
                    print(f"   🔴 Tiingo: No metadata")
                    tiingo_price = None
            else:
                print(f"   🔴 Tiingo Error: {response.status_code} - {response.text[:100]}")
                tiingo_price = None
        except Exception as e:
            print(f"   🔴 Tiingo Error: {e}")
            tiingo_price = None
        
        # Yahoo comparison
        yahoo_start = time.time()
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='1d')
            yahoo_time = time.time() - yahoo_start
            
            if not hist.empty:
                yahoo_price = hist['Close'].iloc[-1]
                yahoo_date = hist.index[-1].strftime('%Y-%m-%d')
                print(f"   🟡 Yahoo: ${yahoo_price:.2f} ({yahoo_date}) - {yahoo_time:.2f}s")
                
                # Compare if both worked
                if tiingo_price and yahoo_price:
                    diff = abs(tiingo_price - yahoo_price)
                    match = "✅ MATCH" if diff < 0.05 else f"❌ DIFF: ${diff:.2f}"
                    faster = "Tiingo" if tiingo_time < yahoo_time else "Yahoo"
                    print(f"   ⚖️ {match} | {faster} faster")
            else:
                print(f"   🟡 Yahoo: No data")
        except Exception as e:
            print(f"   🟡 Yahoo Error: {e}")
        
        time.sleep(0.5)  # Rate limiting
    
    # Test 2: Fundamentals (different endpoint)
    print(f"\n📊 TEST 2: Fundamentals Data")
    print("-" * 40)
    
    for symbol in ['AAPL', 'MSFT']:  # Skip ETFs
        print(f"\n📋 {symbol} Fundamentals:")
        try:
            # Correct fundamentals endpoint
            url = f"https://api.tiingo.com/tiingo/fundamentals/{symbol}/daily?token={api_key}"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    latest = data[0]
                    print(f"   ✅ Date: {latest.get('date', 'N/A')}")
                    
                    # Key fundamental metrics
                    metrics = {
                        'Market Cap': latest.get('marketCap'),
                        'Enterprise Value': latest.get('enterpriseVal'),
                        'P/E Ratio': latest.get('peRatio'),
                        'P/B Ratio': latest.get('pbRatio'),
                        'Revenue': latest.get('revenue'),
                        'Net Income': latest.get('netIncome'),
                        'Debt to Equity': latest.get('debtToEquity'),
                        'ROE': latest.get('roe')
                    }
                    
                    for name, value in metrics.items():
                        if value is not None:
                            if name in ['Market Cap', 'Enterprise Value', 'Revenue', 'Net Income'] and value > 1000000:
                                display_value = f"${value/1000000000:.1f}B"
                            elif isinstance(value, float):
                                display_value = f"{value:.2f}"
                            else:
                                display_value = str(value)
                            print(f"   {name}: {display_value}")
                else:
                    print(f"   ❌ No fundamental data")
            elif response.status_code == 404:
                print(f"   ⚠️ Fundamentals not available for {symbol}")
            elif response.status_code == 401:
                print(f"   🔒 Authentication error - check API key")
            elif response.status_code == 429:
                print(f"   ⏰ Rate limit exceeded")
            else:
                print(f"   ❌ Error: {response.status_code} - {response.text[:100]}")
        except Exception as e:
            print(f"   💥 Error: {e}")
        
        time.sleep(0.5)
    
    # Test 3: News (correct endpoint)
    print(f"\n📰 TEST 3: News Data")
    print("-" * 40)
    
    try:
        # Correct news endpoint
        url = f"https://api.tiingo.com/tiingo/news?tickers=SPY,AAPL&token={api_key}"
        response = requests.get(url)
        
        if response.status_code == 200:
            news = response.json()
            print(f"✅ Found {len(news)} news articles")
            
            if news and len(news) > 0:
                latest = news[0]
                print(f"   📰 Latest: {latest.get('title', 'No title')[:60]}...")
                print(f"   📅 Published: {latest.get('publishedDate', 'Unknown')}")
                print(f"   🏢 Source: {latest.get('source', 'Unknown')}")
                print(f"   🏷️ Tags: {latest.get('tags', [])[:3]}")  # First 3 tags
                print(f"   🔗 URL: {latest.get('url', 'No URL')[:50]}...")
        elif response.status_code == 401:
            print(f"🔒 Authentication error")
        elif response.status_code == 429:
            print(f"⏰ Rate limit exceeded")
        else:
            print(f"❌ News Error: {response.status_code} - {response.text[:100]}")
    except Exception as e:
        print(f"💥 News Error: {e}")
    
    # Test 4: Crypto (correct endpoint)
    print(f"\n₿ TEST 4: Crypto Data")
    print("-" * 40)
    
    try:
        # Correct crypto endpoint
        url = f"https://api.tiingo.com/tiingo/crypto/prices?tickers=btcusd&token={api_key}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                btc_info = data[0]
                ticker = btc_info.get('ticker', 'btcusd')
                
                price_data = btc_info.get('priceData', [])
                if price_data:
                    latest_price = price_data[0]
                    close_price = latest_price.get('close', 'N/A')
                    date = latest_price.get('date', 'N/A')
                    print(f"✅ {ticker.upper()}: ${close_price:,.2f} ({date})" if isinstance(close_price, (int, float)) else f"✅ {ticker.upper()}: {close_price}")
                else:
                    print(f"❌ No BTC price data in response")
            else:
                print(f"❌ No crypto data")
        elif response.status_code == 401:
            print(f"🔒 Authentication error")
        elif response.status_code == 429:
            print(f"⏰ Rate limit exceeded")
        else:
            print(f"❌ Crypto Error: {response.status_code} - {response.text[:100]}")
    except Exception as e:
        print(f"💥 Crypto Error: {e}")

def test_tiingo_rate_limits():
    """Test rate limits and account status"""
    
    api_key = os.getenv('TIINGO_API_KEY')
    
    print(f"\n⏰ TEST 5: Rate Limits & Account")
    print("-" * 40)
    
    # Make multiple requests to test rate limiting
    print("Testing rate limits with multiple requests...")
    
    for i in range(5):
        try:
            url = f"https://api.tiingo.com/tiingo/daily/SPY?token={api_key}"
            start_time = time.time()
            response = requests.get(url)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                print(f"   Request {i+1}: ✅ Success ({elapsed:.2f}s)")
            elif response.status_code == 429:
                print(f"   Request {i+1}: ⏰ Rate Limited")
                break
            else:
                print(f"   Request {i+1}: ❌ Error {response.status_code}")
            
            time.sleep(0.1)  # Small delay
        except Exception as e:
            print(f"   Request {i+1}: 💥 Error: {e}")

def final_tiingo_verdict():
    """Final honest assessment of Tiingo value"""
    
    print(f"\n" + "=" * 60)
    print(f"🏛️ HONEST TIINGO ASSESSMENT")
    print("=" * 60)
    
    print(f"💡 WHAT I LEARNED:")
    print(f"   • My previous test used WRONG endpoints (404 errors)")
    print(f"   • Tiingo has specific API format requirements")
    print(f"   • Documentation matters - I should have read it first")
    
    print(f"\n🎯 TIINGO'S ACTUAL PERFORMANCE:")
    print(f"   • If endpoints work: Tiingo provides what it promises")
    print(f"   • If endpoints fail: I was using wrong API format")
    print(f"   • Either way: Yahoo remains free and comprehensive")
    
    print(f"\n💰 VALUE PROPOSITION:")
    print(f"   • Tiingo Cost: ~$120-600/year")
    print(f"   • Yahoo Cost: $0/year")
    print(f"   • Unique Tiingo Value: Fundamentals + News + Reliability")
    
    print(f"\n🎯 HONEST RECOMMENDATION:")
    print(f"   📊 Heavy fundamental analysis: Tiingo worth it")
    print(f"   📰 Need aggregated news: Tiingo worth it")
    print(f"   📈 Just stock/options trading: Yahoo sufficient")
    print(f"   🔬 Professional reliability: Tiingo worth premium")

if __name__ == "__main__":
    test_tiingo_proper()
    test_tiingo_rate_limits()
    final_tiingo_verdict()