#!/usr/bin/env python3
"""
PROVE OPTIONS ANALYSIS LOGIC
Show every calculation step with raw data to verify no hallucinations
"""

import os
import yfinance as yf
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()

def prove_spy_analysis():
    """Prove every step of SPY $655 CALL analysis with raw data"""
    
    print("🔍 PROVING OPTIONS ANALYSIS - NO HALLUCINATIONS")
    print("=" * 70)
    print("Showing RAW DATA and EVERY CALCULATION STEP")
    print("=" * 70)
    
    # 1. GET RAW YAHOO DATA
    print("\n📊 STEP 1: RAW YAHOO FINANCE DATA")
    print("-" * 40)
    
    symbol = "SPY"
    strike = 655.0
    expiry = "2025-08-29"
    
    try:
        ticker = yf.Ticker(symbol)
        chain = ticker.option_chain(expiry)
        
        print(f"✅ Successfully fetched options chain for {symbol} exp {expiry}")
        print(f"   Calls available: {len(chain.calls)} contracts")
        print(f"   Puts available: {len(chain.puts)} contracts")
        
        # Find our specific contract
        calls_df = chain.calls
        target_call = calls_df[calls_df['strike'] == strike]
        
        if target_call.empty:
            print(f"❌ ${strike} strike not found")
            return
        
        option = target_call.iloc[0]
        
        print(f"\n📋 RAW OPTION DATA FOR SPY ${strike} CALL:")
        print("-" * 40)
        for col in option.index:
            value = option[col]
            print(f"   {col}: {value}")
        
        # Store raw values for calculation
        raw_data = {
            'last_price': float(option['lastPrice']),
            'bid': float(option['bid']),
            'ask': float(option['ask']),
            'volume': int(option['volume']),
            'open_interest': int(option['openInterest']),
            'implied_volatility': float(option['impliedVolatility'])
        }
        
        print(f"\n🔢 EXTRACTED VALUES FOR CALCULATIONS:")
        for key, value in raw_data.items():
            print(f"   {key}: {value}")
        
    except Exception as e:
        print(f"❌ Error getting Yahoo data: {e}")
        return None
    
    # 2. PROVE SPREAD CALCULATION
    print(f"\n🧮 STEP 2: SPREAD CALCULATION (PROVE MATH)")
    print("-" * 40)
    
    bid = raw_data['bid']
    ask = raw_data['ask']
    mid_price = (bid + ask) / 2
    spread_dollars = ask - bid
    spread_pct = (spread_dollars / mid_price) * 100 if mid_price > 0 else 100
    
    print(f"   Bid: ${bid}")
    print(f"   Ask: ${ask}")
    print(f"   Mid Price: (${bid} + ${ask}) / 2 = ${mid_price:.2f}")
    print(f"   Spread $: ${ask} - ${bid} = ${spread_dollars:.2f}")
    print(f"   Spread %: (${spread_dollars:.2f} / ${mid_price:.2f}) * 100 = {spread_pct:.1f}%")
    
    # 3. PROVE LIQUIDITY SCORING
    print(f"\n📊 STEP 3: LIQUIDITY SCORING (PROVE LOGIC)")
    print("-" * 40)
    
    volume = raw_data['volume']
    open_interest = raw_data['open_interest']
    
    print(f"   Volume: {volume:,} contracts")
    print(f"   Open Interest: {open_interest:,} contracts")
    print(f"   Spread: {spread_pct:.1f}%")
    
    # Volume points (show exact logic)
    print(f"\n   VOLUME SCORING:")
    volume_points = 0
    if volume >= 1000:
        volume_points = 40
        print(f"     {volume:,} >= 1000 → 40 points")
    elif volume >= 500:
        volume_points = 30
        print(f"     {volume:,} >= 500 → 30 points")
    elif volume >= 100:
        volume_points = 20
        print(f"     {volume:,} >= 100 → 20 points")
    elif volume >= 50:
        volume_points = 10
        print(f"     {volume:,} >= 50 → 10 points")
    else:
        volume_points = 0
        print(f"     {volume:,} < 50 → 0 points")
    
    # Open Interest points
    print(f"\n   OPEN INTEREST SCORING:")
    oi_points = 0
    if open_interest >= 5000:
        oi_points = 40
        print(f"     {open_interest:,} >= 5000 → 40 points")
    elif open_interest >= 1000:
        oi_points = 30
        print(f"     {open_interest:,} >= 1000 → 30 points")
    elif open_interest >= 500:
        oi_points = 20
        print(f"     {open_interest:,} >= 500 → 20 points")
    elif open_interest >= 100:
        oi_points = 10
        print(f"     {open_interest:,} >= 100 → 10 points")
    else:
        oi_points = 0
        print(f"     {open_interest:,} < 100 → 0 points")
    
    # Spread points
    print(f"\n   SPREAD SCORING:")
    spread_points = 0
    if spread_pct <= 5:
        spread_points = 20
        print(f"     {spread_pct:.1f}% <= 5% → 20 points")
    elif spread_pct <= 10:
        spread_points = 15
        print(f"     {spread_pct:.1f}% <= 10% → 15 points")
    elif spread_pct <= 15:
        spread_points = 10
        print(f"     {spread_pct:.1f}% <= 15% → 10 points")
    elif spread_pct <= 25:
        spread_points = 5
        print(f"     {spread_pct:.1f}% <= 25% → 5 points")
    else:
        spread_points = 0
        print(f"     {spread_pct:.1f}% > 25% → 0 points")
    
    liquidity_score = volume_points + oi_points + spread_points
    print(f"\n   TOTAL LIQUIDITY SCORE:")
    print(f"     Volume: {volume_points} + OI: {oi_points} + Spread: {spread_points} = {liquidity_score}/100")
    
    # 4. PROVE IMPLIED VOLATILITY ANALYSIS
    print(f"\n⚡ STEP 4: IMPLIED VOLATILITY ANALYSIS")
    print("-" * 40)
    
    iv = raw_data['implied_volatility']
    print(f"   Raw IV from Yahoo: {iv}")
    print(f"   IV as percentage: {iv*100:.1f}%")
    
    # Get historical volatility for comparison
    try:
        hist = ticker.history(period='30d')
        returns = hist['Close'].pct_change().dropna()
        historical_vol = returns.std() * (252**0.5)  # Annualized
        
        print(f"   Historical Vol (30d): {historical_vol:.3f} ({historical_vol*100:.1f}%)")
        
        iv_premium = (iv - historical_vol) / historical_vol if historical_vol > 0 else 0
        print(f"   IV Premium: ({iv:.3f} - {historical_vol:.3f}) / {historical_vol:.3f} = {iv_premium:.3f}")
        print(f"   IV Premium %: {iv_premium*100:+.1f}%")
        
    except Exception as e:
        print(f"   ❌ Could not calculate historical vol: {e}")
        historical_vol = 0.2  # Default
        iv_premium = (iv - historical_vol) / historical_vol
    
    # 5. PROVE DAYS TO EXPIRY
    print(f"\n📅 STEP 5: DAYS TO EXPIRY CALCULATION")
    print("-" * 40)
    
    expiry_date = datetime.strptime(expiry, '%Y-%m-%d')
    today = datetime.now()
    days_to_expiry = (expiry_date - today).days
    
    print(f"   Expiry Date: {expiry_date.strftime('%Y-%m-%d')}")
    print(f"   Today: {today.strftime('%Y-%m-%d')}")
    print(f"   Days to Expiry: ({expiry_date.strftime('%Y-%m-%d')} - {today.strftime('%Y-%m-%d')}) = {days_to_expiry} days")
    
    # 6. PROVE MONEYNESS CALCULATION
    print(f"\n🎯 STEP 6: MONEYNESS CALCULATION")
    print("-" * 40)
    
    try:
        current_stock_price = ticker.history(period='1d')['Close'].iloc[-1]
        moneyness = current_stock_price / strike
        
        print(f"   Current SPY Price: ${current_stock_price:.2f}")
        print(f"   Strike Price: ${strike}")
        print(f"   Moneyness: ${current_stock_price:.2f} / ${strike} = {moneyness:.3f}")
        
        if moneyness > 1:
            print(f"   Status: IN-THE-MONEY (stock > strike)")
        elif moneyness < 1:
            print(f"   Status: OUT-OF-THE-MONEY (stock < strike)")
            print(f"   Needs to move: {((strike/current_stock_price)-1)*100:.1f}% to reach strike")
        else:
            print(f"   Status: AT-THE-MONEY")
            
    except Exception as e:
        print(f"   ❌ Error getting current price: {e}")
        return None
    
    # 7. FINAL SUMMARY - NO HALLUCINATIONS
    print(f"\n" + "=" * 70)
    print(f"📋 VERIFIED ANALYSIS SUMMARY - ALL DATA PROVEN")
    print("=" * 70)
    
    print(f"✅ PROVEN METRICS:")
    print(f"   Contract: SPY ${strike} CALL exp {expiry}")
    print(f"   Current Price: ${mid_price:.2f} (Bid: ${bid}, Ask: ${ask})")
    print(f"   Volume: {volume:,} contracts")
    print(f"   Open Interest: {open_interest:,} contracts") 
    print(f"   Implied Volatility: {iv*100:.1f}%")
    print(f"   Days to Expiry: {days_to_expiry} days")
    print(f"   Moneyness: {moneyness:.3f}")
    print(f"   Liquidity Score: {liquidity_score}/100")
    
    print(f"\n✅ DATA SOURCES:")
    print(f"   All data from Yahoo Finance yfinance library")
    print(f"   No estimations or hallucinations")
    print(f"   Every calculation shown step-by-step")
    print(f"   Logic rules clearly defined and applied")
    
    return {
        'raw_yahoo_data': dict(option),
        'calculated_metrics': {
            'mid_price': mid_price,
            'spread_pct': spread_pct,
            'liquidity_score': liquidity_score,
            'days_to_expiry': days_to_expiry,
            'moneyness': moneyness,
            'iv_premium': iv_premium
        }
    }

def save_proof():
    """Save all proof data to file for verification"""
    
    print(f"\n💾 SAVING PROOF DATA")
    print("-" * 30)
    
    proof_data = prove_spy_analysis()
    
    if proof_data:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"data/options_analysis/proof_no_hallucinations_{timestamp}.json"
        
        os.makedirs("data/options_analysis", exist_ok=True)
        
        with open(filename, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'note': 'Complete proof of options analysis with raw data',
                'data': proof_data
            }, f, indent=2, default=str)
        
        print(f"✅ Proof saved to: {filename}")
        print(f"   You can verify every data point and calculation")

if __name__ == "__main__":
    prove_spy_analysis()
    save_proof()