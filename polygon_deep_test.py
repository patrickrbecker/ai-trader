#!/usr/bin/env python3
"""
DEFINITIVE POLYGON API TEST
Final verification - are we using their API correctly?
"""

import os
import requests
import json
from dotenv import load_dotenv
from datetime import datetime
import time

load_dotenv()

def test_polygon_api_endpoints():
    """Test multiple Polygon API endpoints to verify we're using it correctly"""
    
    api_key = os.getenv('POLYGON_API_KEY')
    base_url = "https://api.polygon.io"
    
    print("🔍 DEFINITIVE POLYGON API TEST")
    print("=" * 60)
    print(f"API Key: {api_key[:8]}...{api_key[-4:]}")
    print(f"Testing multiple endpoints and methods...")
    print("=" * 60)
    
    # Test 1: Check account/subscription status
    print("\n🔑 TEST 1: Account Status")
    print("-" * 30)
    
    try:
        response = requests.get(f"{base_url}/v1/marketstatus/now?apikey={api_key}")
        if response.status_code == 200:
            status = response.json()
            print(f"✅ API Access: Working")
            print(f"📊 Market Status: {status.get('market', 'Unknown')}")
        else:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"💥 Connection Error: {e}")
        return
    
    # Test 2: Stock price verification (should work)
    print("\n📈 TEST 2: Stock Price (Control Test)")
    print("-" * 30)
    
    try:
        # Get current SPY price
        response = requests.get(f"{base_url}/v2/aggs/ticker/SPY/prev?adjusted=true&apikey={api_key}")
        if response.status_code == 200:
            data = response.json()
            if data.get('results'):
                price = data['results'][0]['c']
                print(f"✅ SPY Price: ${price} (Stock data working)")
            else:
                print(f"⚠️ No stock data returned")
        else:
            print(f"❌ Stock API Error: {response.status_code}")
    except Exception as e:
        print(f"💥 Stock Error: {e}")
    
    # Test 3: Options contracts listing
    print("\n📋 TEST 3: Options Contracts Discovery")
    print("-" * 30)
    
    # Try to list available SPY options contracts
    try:
        response = requests.get(f"{base_url}/v3/reference/options/contracts?underlying_ticker=SPY&limit=10&apikey={api_key}")
        if response.status_code == 200:
            data = response.json()
            if data.get('results'):
                print(f"✅ Found {len(data['results'])} SPY option contracts")
                # Show first few contracts
                for i, contract in enumerate(data['results'][:3]):
                    print(f"   {i+1}. {contract.get('ticker', 'N/A')} - Strike: ${contract.get('strike_price', 'N/A')} - Exp: {contract.get('expiration_date', 'N/A')}")
                
                # Test specific contract we've been using
                target_contract = None
                for contract in data['results']:
                    if (contract.get('strike_price') == 655 and 
                        contract.get('expiration_date') == '2025-08-29' and
                        contract.get('contract_type') == 'call'):
                        target_contract = contract
                        break
                
                if target_contract:
                    print(f"🎯 Found target contract: {target_contract['ticker']}")
                    return target_contract['ticker']
                else:
                    print(f"❌ Target contract (SPY $655 CALL 8/29) not found")
            else:
                print(f"❌ No option contracts returned")
        else:
            print(f"❌ Options Contracts Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"💥 Contracts Error: {e}")
    
    return None

def test_options_pricing(contract_ticker):
    """Test different ways to get options pricing data"""
    
    api_key = os.getenv('POLYGON_API_KEY')
    base_url = "https://api.polygon.io"
    
    print(f"\n💰 TEST 4: Options Pricing Methods")
    print("-" * 30)
    print(f"Testing contract: {contract_ticker}")
    
    # Method 1: Last trade
    print(f"\n🔄 Method 1: Last Trade")
    try:
        response = requests.get(f"{base_url}/v2/last/trade/{contract_ticker}?apikey={api_key}")
        if response.status_code == 200:
            data = response.json()
            if data.get('results'):
                result = data['results']
                print(f"✅ Last Trade: ${result.get('p', 'N/A')} - Size: {result.get('s', 'N/A')} - Time: {result.get('t', 'N/A')}")
            else:
                print(f"❌ No last trade data")
        else:
            print(f"❌ Last Trade Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"💥 Last Trade Error: {e}")
    
    # Method 2: Last quote (bid/ask)
    print(f"\n📊 Method 2: Last Quote (Bid/Ask)")
    try:
        response = requests.get(f"{base_url}/v2/last/nbbo/{contract_ticker}?apikey={api_key}")
        if response.status_code == 200:
            data = response.json()
            if data.get('results'):
                result = data['results']
                print(f"✅ Bid/Ask: ${result.get('P', 'N/A')}/${result.get('p', 'N/A')} - Sizes: {result.get('S', 'N/A')}/{result.get('s', 'N/A')}")
            else:
                print(f"❌ No quote data")
        else:
            print(f"❌ Quote Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"💥 Quote Error: {e}")
    
    # Method 3: Daily bars (OHLC)
    print(f"\n📈 Method 3: Daily OHLC")
    try:
        # Get previous day's data
        response = requests.get(f"{base_url}/v2/aggs/ticker/{contract_ticker}/prev?adjusted=true&apikey={api_key}")
        if response.status_code == 200:
            data = response.json()
            if data.get('results'):
                result = data['results'][0]
                print(f"✅ OHLC: O:${result.get('o', 'N/A')} H:${result.get('h', 'N/A')} L:${result.get('l', 'N/A')} C:${result.get('c', 'N/A')}")
                print(f"✅ Volume: {result.get('v', 'N/A')}")
            else:
                print(f"❌ No OHLC data")
        else:
            print(f"❌ OHLC Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"💥 OHLC Error: {e}")
    
    # Method 4: Snapshot (comprehensive)
    print(f"\n📸 Method 4: Options Snapshot")
    try:
        response = requests.get(f"{base_url}/v3/snapshot/options/{contract_ticker}?apikey={api_key}")
        if response.status_code == 200:
            data = response.json()
            if data.get('results'):
                result = data['results']
                print(f"✅ Snapshot Data Found:")
                
                # Market data
                market = result.get('market_status', 'Unknown')
                print(f"   Market Status: {market}")
                
                # Last quote
                last_quote = result.get('last_quote', {})
                if last_quote:
                    print(f"   Last Quote: ${last_quote.get('bid', 'N/A')}/${last_quote.get('ask', 'N/A')}")
                    print(f"   Quote Sizes: {last_quote.get('bid_size', 'N/A')}/{last_quote.get('ask_size', 'N/A')}")
                
                # Last trade
                last_trade = result.get('last_trade', {})
                if last_trade:
                    print(f"   Last Trade: ${last_trade.get('price', 'N/A')} - Size: {last_trade.get('size', 'N/A')}")
                
                # Day summary
                day = result.get('day', {})
                if day:
                    print(f"   Day OHLC: ${day.get('open', 'N/A')}/${day.get('high', 'N/A')}/${day.get('low', 'N/A')}/${day.get('close', 'N/A')}")
                    print(f"   Day Volume: {day.get('volume', 'N/A')}")
                
                # Greeks and IV
                greeks = result.get('greeks', {})
                if greeks:
                    print(f"   Delta: {greeks.get('delta', 'N/A')}")
                    print(f"   Gamma: {greeks.get('gamma', 'N/A')}")
                    print(f"   Theta: {greeks.get('theta', 'N/A')}")
                    print(f"   Vega: {greeks.get('vega', 'N/A')}")
                
                implied_vol = result.get('implied_volatility', 'N/A')
                open_interest = result.get('open_interest', 'N/A')
                print(f"   IV: {implied_vol}")
                print(f"   OI: {open_interest}")
                
            else:
                print(f"❌ No snapshot data")
        else:
            print(f"❌ Snapshot Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"💥 Snapshot Error: {e}")

def test_subscription_level():
    """Check what subscription level we actually have"""
    
    print(f"\n🎫 TEST 5: Subscription Level Check")
    print("-" * 30)
    
    api_key = os.getenv('POLYGON_API_KEY')
    
    # Try to access premium endpoints
    premium_tests = [
        ("Real-time data", f"https://api.polygon.io/v2/last/trade/SPY?apikey={api_key}"),
        ("Options data", f"https://api.polygon.io/v3/reference/options/contracts?underlying_ticker=SPY&limit=1&apikey={api_key}"),
        ("Market status", f"https://api.polygon.io/v1/marketstatus/now?apikey={api_key}")
    ]
    
    for test_name, url in premium_tests:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print(f"✅ {test_name}: Accessible")
            elif response.status_code == 401:
                print(f"🔒 {test_name}: Unauthorized (subscription issue)")
            elif response.status_code == 429:
                print(f"⏰ {test_name}: Rate limited")
            else:
                print(f"❌ {test_name}: Error {response.status_code}")
        except Exception as e:
            print(f"💥 {test_name}: {e}")

def main():
    """Run comprehensive Polygon API test"""
    
    # Test account and find contract
    contract_ticker = test_polygon_api_endpoints()
    
    # Test subscription level
    test_subscription_level()
    
    # If we found a contract, test pricing methods
    if contract_ticker:
        test_options_pricing(contract_ticker)
    else:
        print(f"\n⚠️ Cannot test pricing without valid contract ticker")
        print(f"Trying with manually constructed ticker...")
        # Try standard format
        test_options_pricing("O:SPY250829C00655000")
    
    print(f"\n" + "=" * 60)
    print(f"🎯 CONCLUSION:")
    print(f"   If all methods above show limited/missing data,")
    print(f"   then Polygon's options coverage is genuinely poor.")
    print(f"   If some methods work, we need to fix our implementation.")
    print("=" * 60)

if __name__ == "__main__":
    main()