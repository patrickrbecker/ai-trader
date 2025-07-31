#!/usr/bin/env python3
"""
CRITICAL TIINGO API TEST
Ruthless analysis - is Tiingo worth paying for?
"""

import os
import requests
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta
import time
import yfinance as yf

load_dotenv()

def test_tiingo_api_endpoints():
    """Test Tiingo API endpoints thoroughly"""
    
    api_key = os.getenv('TIINGO_API_KEY')
    base_url = "https://api.tiingo.com"
    
    print("🔍 CRITICAL TIINGO API TEST")
    print("=" * 60)
    print(f"API Key: {api_key[:8]}...{api_key[-4:]}")
    print(f"Testing what you actually get for your money...")
    print("=" * 60)
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Token {api_key}'
    }
    
    # Test 1: Account info
    print("\n🔑 TEST 1: Account Status & Limits")
    print("-" * 40)
    
    try:
        # Try different account endpoint formats
        endpoints_to_try = [
            f"{base_url}/api/account",
            f"{base_url}/api/tiingo/utilities/search?query=SPY&token={api_key}",  # Test basic functionality
        ]
        
        working_endpoint = None
        for endpoint in endpoints_to_try:
            test_response = requests.get(endpoint, headers=headers)
            if test_response.status_code == 200:
                working_endpoint = endpoint
                break
        
        if working_endpoint:
            print(f"✅ API Access: Working (endpoint: {working_endpoint.split('/')[-1]})")
            
            # If account endpoint works, show details
            if 'account' in working_endpoint:
                response = requests.get(working_endpoint, headers=headers)
            else:
                response = test_response
                
        if response.status_code == 200:
            account = response.json()
            print(f"✅ Account Active: {account.get('email', 'Unknown')}")
            print(f"📊 Plan: {account.get('plan', 'Unknown')}")
            print(f"⏰ Rate Limits:")
            
            limits = account.get('api_requests_per_day', {})
            if isinstance(limits, dict):
                for key, value in limits.items():
                    print(f"   {key}: {value}")
            else:
                print(f"   Daily: {limits}")
                
            usage = account.get('usage', {})
            print(f"🎯 Current Usage:")
            for key, value in usage.items():
                print(f"   {key}: {value}")
                
        else:
            print(f"❌ Account Error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"💥 Account Error: {e}")
        return False
    
    return True

def test_stock_data_quality():
    """Compare Tiingo vs Yahoo stock data"""
    
    api_key = os.getenv('TIINGO_API_KEY')
    base_url = "https://api.tiingo.com"
    headers = {'Authorization': f'Token {api_key}'}
    
    print(f"\n📈 TEST 2: Stock Data Quality vs Yahoo")
    print("-" * 40)
    
    test_symbols = ['SPY', 'AAPL', 'TSLA']
    
    for symbol in test_symbols:
        print(f"\n🧪 Testing {symbol}:")
        
        # Tiingo current price
        tiingo_start = time.time()
        try:
            response = requests.get(f"{base_url}/api/tiingo/daily/{symbol}/prices?token={api_key}")
            tiingo_time = time.time() - tiingo_start
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    latest = data[0]  # Most recent data
                    tiingo_price = latest['close']
                    tiingo_date = latest['date'][:10]
                    print(f"   🔴 Tiingo: ${tiingo_price:.2f} ({tiingo_date}) - {tiingo_time:.2f}s")
                else:
                    print(f"   🔴 Tiingo: No data returned")
                    tiingo_price = None
            else:
                print(f"   🔴 Tiingo Error: {response.status_code}")
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
                
                # Compare prices
                if tiingo_price and yahoo_price:
                    diff = abs(tiingo_price - yahoo_price)
                    match = "✅ MATCH" if diff < 0.01 else f"❌ DIFF: ${diff:.2f}"
                    speed = "Tiingo" if tiingo_time < yahoo_time else "Yahoo"
                    print(f"   ⚖️ Price: {match} | Speed: {speed} faster")
            else:
                print(f"   🟡 Yahoo: No data")
        except Exception as e:
            print(f"   🟡 Yahoo Error: {e}")

def test_fundamentals_data():
    """Test Tiingo's key differentiator - fundamentals"""
    
    api_key = os.getenv('TIINGO_API_KEY')
    base_url = "https://api.tiingo.com"
    headers = {'Authorization': f'Token {api_key}'}
    
    print(f"\n📊 TEST 3: Fundamentals Data (Tiingo's Strength)")
    print("-" * 40)
    
    test_symbols = ['SPY', 'AAPL', 'MSFT']
    
    for symbol in test_symbols:
        print(f"\n📋 {symbol} Fundamentals:")
        
        try:
            # Try fundamentals endpoint
            response = requests.get(f"{base_url}/api/tiingo/fundamentals/{symbol}/daily?token={api_key}")
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    latest = data[0]
                    print(f"   ✅ Data Available:")
                    print(f"      Date: {latest.get('date', 'N/A')}")
                    
                    # Key metrics
                    key_metrics = ['marketCap', 'enterpriseVal', 'peRatio', 'pbRatio', 'revenue', 'netIncome']
                    for metric in key_metrics:
                        value = latest.get(metric, 'N/A')
                        if value != 'N/A' and value is not None:
                            if metric in ['marketCap', 'enterpriseVal', 'revenue', 'netIncome']:
                                if isinstance(value, (int, float)) and value > 1000000:
                                    value = f"${value/1000000000:.1f}B"
                            print(f"      {metric}: {value}")
                else:
                    print(f"   ❌ No fundamental data")
            elif response.status_code == 404:
                print(f"   ⚠️ Fundamentals not available for {symbol}")
            else:
                print(f"   ❌ Fundamentals Error: {response.status_code}")
        except Exception as e:
            print(f"   💥 Fundamentals Error: {e}")

def test_news_data():
    """Test Tiingo news vs free alternatives"""
    
    api_key = os.getenv('TIINGO_API_KEY')
    base_url = "https://api.tiingo.com"
    headers = {'Authorization': f'Token {api_key}'}
    
    print(f"\n📰 TEST 4: News Data Quality")
    print("-" * 40)
    
    try:
        # Get recent news for SPY
        response = requests.get(f"{base_url}/api/tiingo/news?tickers=SPY&token={api_key}")
        
        if response.status_code == 200:
            news = response.json()
            print(f"✅ Found {len(news)} news articles")
            
            if news:
                # Show latest article
                latest = news[0]
                print(f"📰 Latest: {latest.get('title', 'No title')[:60]}...")
                print(f"   Source: {latest.get('source', 'Unknown')}")
                print(f"   Date: {latest.get('publishedDate', 'Unknown')}")
                print(f"   Tags: {latest.get('tags', [])}")
        else:
            print(f"❌ News Error: {response.status_code}")
    except Exception as e:
        print(f"💥 News Error: {e}")

def test_crypto_forex():
    """Test Tiingo's crypto/forex capabilities"""
    
    api_key = os.getenv('TIINGO_API_KEY')
    base_url = "https://api.tiingo.com"
    headers = {'Authorization': f'Token {api_key}'}
    
    print(f"\n₿ TEST 5: Crypto & Forex Coverage")
    print("-" * 40)
    
    # Test crypto
    print("🪙 Crypto Data:")
    try:
        response = requests.get(f"{base_url}/api/tiingo/crypto/prices?tickers=btcusd&token={api_key}")
        if response.status_code == 200:
            data = response.json()
            if data:
                btc = data[0]
                price = btc.get('priceData', [{}])[0].get('close', 'N/A')
                print(f"   ✅ BTC: ${price}")
            else:
                print(f"   ❌ No crypto data")
        else:
            print(f"   ❌ Crypto Error: {response.status_code}")
    except Exception as e:
        print(f"   💥 Crypto Error: {e}")
    
    # Test forex
    print("💱 Forex Data:")
    try:
        response = requests.get(f"{base_url}/api/tiingo/fx/eurusd/prices?token={api_key}")
        if response.status_code == 200:
            data = response.json()
            if data:
                eur = data[0]
                price = eur.get('close', 'N/A')
                print(f"   ✅ EUR/USD: {price}")
            else:
                print(f"   ❌ No forex data")
        else:
            print(f"   ❌ Forex Error: {response.status_code}")
    except Exception as e:
        print(f"   💥 Forex Error: {e}")

def calculate_tiingo_value():
    """Calculate if Tiingo provides value over free alternatives"""
    
    print(f"\n💰 TIINGO VALUE ANALYSIS")
    print("=" * 60)
    
    # What you get with Tiingo
    tiingo_features = {
        "Stock prices": "✅ Available (but Yahoo is free)",
        "Historical data": "✅ Available (but Yahoo is free)", 
        "Fundamentals": "✅ Available (Yahoo has basic fundamentals)",
        "News": "✅ Available (but many free news sources exist)",
        "Crypto": "✅ Available (but CoinGecko is free)",
        "Forex": "✅ Available (but many free sources exist)",
        "API reliability": "✅ Professional SLA",
        "Rate limits": "✅ High limits (vs free alternatives)"
    }
    
    print("🎯 TIINGO FEATURES:")
    for feature, status in tiingo_features.items():
        print(f"   {feature}: {status}")
    
    # Cost analysis
    print(f"\n💸 COST ANALYSIS:")
    print(f"   Tiingo Cost: ~$10-50/month (estimated based on usage)")
    print(f"   Free Alternative: $0/month")
    print(f"   Annual Difference: $120-600/year")
    
    # ROI question
    print(f"\n❓ KEY QUESTIONS:")
    print(f"   1. Do you need professional-grade API reliability?")
    print(f"   2. Do you hit rate limits with free services?") 
    print(f"   3. Do you need comprehensive fundamentals data?")
    print(f"   4. Do you trade crypto/forex frequently?")
    print(f"   5. Is the cost justified by your trading profits?")

def main():
    """Run comprehensive Tiingo analysis"""
    
    if not test_tiingo_api_endpoints():
        print("❌ Cannot proceed - API access failed")
        return
    
    test_stock_data_quality()
    test_fundamentals_data()
    test_news_data()
    test_crypto_forex()
    calculate_tiingo_value()
    
    print(f"\n" + "=" * 60)
    print(f"🏛️ FINAL TIINGO VERDICT:")
    print(f"   Unlike Polygon, Tiingo actually works as advertised.")
    print(f"   The question is: Is it worth paying for vs free alternatives?")
    print(f"   Decision depends on your specific needs and trading volume.")
    print("=" * 60)

if __name__ == "__main__":
    main()