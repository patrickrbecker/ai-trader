#!/usr/bin/env python3
"""
CRITICAL DATA QUALITY AUDIT: Polygon vs Yahoo
Ruthless analysis of what you're actually paying for
"""

import os
import yfinance as yf
import pandas as pd
from dotenv import load_dotenv
from polygon_data_provider import PolygonDataProvider
from real_options_pricing import RealOptionsPricer
import time
from datetime import datetime

load_dotenv()

def audit_options_data():
    """Compare Polygon vs Yahoo options data quality side by side"""
    
    print("🔍 CRITICAL AUDIT: POLYGON.IO vs YAHOO FINANCE")
    print("=" * 70)
    print("💰 POLYGON COST: $199/month (Premium plan)")
    print("💰 YAHOO COST: FREE")
    print("🎯 QUESTION: Is Polygon worth $2,388/year for options data?")
    print("=" * 70)
    
    # Test symbols with known liquid options
    test_cases = [
        ("SPY", 655, "2025-08-29", "CALL"),
        ("SPY", 630, "2025-08-29", "PUT"), 
        ("QQQ", 570, "2025-08-29", "CALL"),
        ("AAPL", 220, "2025-08-01", "CALL"),
        ("TSLA", 320, "2025-08-01", "PUT")
    ]
    
    polygon_provider = PolygonDataProvider(os.getenv('POLYGON_API_KEY'))
    
    results = []
    
    for symbol, strike, expiry, option_type in test_cases:
        print(f"\n🧪 TESTING: {symbol} ${strike} {option_type} exp {expiry}")
        print("-" * 50)
        
        # Time the requests
        start_polygon = time.time()
        
        # 1. POLYGON DATA
        print("🔴 POLYGON.IO DATA:")
        try:
            polygon_option = polygon_provider.get_option_price(symbol, strike, expiry, option_type)
            polygon_time = time.time() - start_polygon
            
            if polygon_option:
                print(f"   ⏱️ Speed: {polygon_time:.2f}s")
                print(f"   💰 Last: ${polygon_option.last_price:.2f}")
                print(f"   📊 Bid/Ask: ${polygon_option.bid:.2f}/${polygon_option.ask:.2f}")
                print(f"   📈 Volume: {polygon_option.volume:,}")
                print(f"   🏛️ Open Interest: {polygon_option.open_interest:,}")
                print(f"   ⚡ IV: {polygon_option.implied_volatility:.3f}")
                print(f"   🎯 Greeks: Δ{polygon_option.delta:.3f} Θ{polygon_option.theta:.3f}")
                
                # Data quality checks
                quality_issues = []
                if polygon_option.bid == 0 and polygon_option.ask == 0:
                    quality_issues.append("❌ No bid/ask data")
                if polygon_option.implied_volatility == 0:
                    quality_issues.append("❌ No IV data")
                if polygon_option.open_interest == 0:
                    quality_issues.append("❌ No OI data")
                if polygon_option.delta is None:
                    quality_issues.append("❌ No Greeks")
                    print(f"   🎯 Greeks: Not available")
                else:
                    print(f"   🎯 Greeks: Δ{polygon_option.delta:.3f} Θ{polygon_option.theta:.3f}")
                    
                if quality_issues:
                    print(f"   🚨 ISSUES: {', '.join(quality_issues)}")
                else:
                    print("   ✅ Complete data set")
                    
            else:
                print("   ❌ NO DATA RETURNED")
                polygon_time = None
                
        except Exception as e:
            print(f"   💥 ERROR: {e}")
            polygon_time = None
            polygon_option = None
        
        # 2. YAHOO DATA  
        print("\n🟡 YAHOO FINANCE DATA:")
        start_yahoo = time.time()
        
        try:
            ticker = yf.Ticker(symbol)
            chain = ticker.option_chain(expiry)
            yahoo_time = time.time() - start_yahoo
            
            options_df = chain.calls if option_type == 'CALL' else chain.puts
            option_row = options_df[options_df['strike'] == strike]
            
            if not option_row.empty:
                option = option_row.iloc[0]
                
                print(f"   ⏱️ Speed: {yahoo_time:.2f}s")
                print(f"   💰 Last: ${float(option['lastPrice']):.2f}")
                print(f"   📊 Bid/Ask: ${float(option['bid']):.2f}/${float(option['ask']):.2f}")
                print(f"   📈 Volume: {int(option['volume']):,}")
                print(f"   🏛️ Open Interest: {int(option['openInterest']):,}")
                print(f"   ⚡ IV: {float(option['impliedVolatility']):.3f}")
                
                # Check for Greeks
                has_greeks = 'delta' in option and not pd.isna(option.get('delta'))
                if has_greeks:
                    print(f"   🎯 Greeks: Available")
                else:
                    print(f"   🎯 Greeks: Not available")
                
                # Data quality
                quality_issues = []
                if float(option['bid']) == 0 and float(option['ask']) == 0:
                    quality_issues.append("❌ No bid/ask")
                if float(option['impliedVolatility']) == 0:
                    quality_issues.append("❌ No IV")
                if int(option['openInterest']) == 0:
                    quality_issues.append("❌ No OI")
                if not has_greeks:
                    quality_issues.append("❌ No Greeks")
                    
                if quality_issues:
                    print(f"   🚨 ISSUES: {', '.join(quality_issues)}")
                else:
                    print("   ✅ Complete data set")
                    
                yahoo_option = option
            else:
                print("   ❌ STRIKE NOT FOUND")
                yahoo_option = None
                
        except Exception as e:
            print(f"   💥 ERROR: {e}")
            yahoo_time = None
            yahoo_option = None
        
        # 3. CRITICAL COMPARISON
        print(f"\n⚖️ CRITICAL ANALYSIS:")
        
        if polygon_option and yahoo_option:
            # Price comparison
            price_diff = abs(polygon_option.last_price - float(yahoo_option['lastPrice']))
            print(f"   💰 Price Match: ${price_diff:.2f} difference")
            
            # Volume comparison
            vol_diff = abs(polygon_option.volume - int(yahoo_option['volume']))
            print(f"   📈 Volume Match: {vol_diff:,} difference")
            
            # IV comparison
            iv_diff = abs(polygon_option.implied_volatility - float(yahoo_option['impliedVolatility']))
            print(f"   ⚡ IV Match: {iv_diff:.3f} difference")
            
            # Speed comparison
            if polygon_time and yahoo_time:
                speed_advantage = "Polygon" if polygon_time < yahoo_time else "Yahoo"
                speed_diff = abs(polygon_time - yahoo_time)
                print(f"   ⏱️ Speed Winner: {speed_advantage} (by {speed_diff:.2f}s)")
            
            # Data completeness
            polygon_complete = (polygon_option.bid > 0 and polygon_option.ask > 0 and 
                              polygon_option.implied_volatility > 0 and 
                              polygon_option.open_interest > 0)
            
            yahoo_complete = (float(yahoo_option['bid']) > 0 and float(yahoo_option['ask']) > 0 and
                            float(yahoo_option['impliedVolatility']) > 0 and
                            int(yahoo_option['openInterest']) > 0)
            
            print(f"   📊 Data Quality: Polygon {'✅' if polygon_complete else '❌'} vs Yahoo {'✅' if yahoo_complete else '❌'}")
            
        elif polygon_option:
            print("   🏆 WINNER: Polygon (Yahoo failed)")
        elif yahoo_option is not None:
            print("   🏆 WINNER: Yahoo (Polygon failed)")
        else:
            print("   💀 BOTH FAILED")
        
        # Store results for summary
        results.append({
            'symbol': f"{symbol} ${strike} {option_type}",
            'polygon_success': polygon_option is not None,
            'yahoo_success': yahoo_option is not None,
            'polygon_time': polygon_time,
            'yahoo_time': yahoo_time,
            'polygon_complete': polygon_complete if polygon_option and yahoo_option else False,
            'yahoo_complete': yahoo_complete if polygon_option and yahoo_option else False
        })
        
        time.sleep(1)  # Rate limiting
    
    # FINAL VERDICT
    print(f"\n" + "=" * 70)
    print("🏛️ FINAL VERDICT: IS POLYGON WORTH $199/MONTH?")
    print("=" * 70)
    
    polygon_wins = sum(1 for r in results if r['polygon_success'] and not r['yahoo_success'])
    yahoo_wins = sum(1 for r in results if r['yahoo_success'] and not r['polygon_success'])
    both_work = sum(1 for r in results if r['polygon_success'] and r['yahoo_success'])
    both_fail = sum(1 for r in results if not r['polygon_success'] and not r['yahoo_success'])
    
    print(f"📊 RESULTS SUMMARY:")
    print(f"   Polygon Only: {polygon_wins}/{len(results)} tests")
    print(f"   Yahoo Only: {yahoo_wins}/{len(results)} tests") 
    print(f"   Both Work: {both_work}/{len(results)} tests")
    print(f"   Both Fail: {both_fail}/{len(results)} tests")
    
    if both_work > 0:
        avg_polygon_time = sum(r['polygon_time'] for r in results if r['polygon_time']) / len([r for r in results if r['polygon_time']])
        avg_yahoo_time = sum(r['yahoo_time'] for r in results if r['yahoo_time']) / len([r for r in results if r['yahoo_time']])
        
        polygon_better_quality = sum(1 for r in results if r['polygon_complete'] and not r['yahoo_complete'])
        yahoo_better_quality = sum(1 for r in results if r['yahoo_complete'] and not r['polygon_complete'])
        
        print(f"\n💎 QUALITY ANALYSIS:")
        print(f"   Avg Speed - Polygon: {avg_polygon_time:.2f}s vs Yahoo: {avg_yahoo_time:.2f}s")
        print(f"   Better Data - Polygon: {polygon_better_quality} vs Yahoo: {yahoo_better_quality}")
    
    # ROI Analysis
    print(f"\n💰 ROI ANALYSIS:")
    print(f"   Annual Cost: $2,388")
    print(f"   Success Rate: {(polygon_wins + both_work)/len(results)*100:.1f}%")
    
    if polygon_wins == 0 and yahoo_wins > 0:
        print(f"   🚨 VERDICT: CANCEL POLYGON - Yahoo is better AND free")
    elif polygon_wins > yahoo_wins:
        print(f"   ✅ VERDICT: Keep Polygon - Provides unique value")
    elif both_work == len(results) and avg_polygon_time < avg_yahoo_time * 0.5:
        print(f"   ⚡ VERDICT: Keep for speed advantage")
    else:
        print(f"   ❓ VERDICT: Questionable value - Consider canceling")

if __name__ == "__main__":
    audit_options_data()