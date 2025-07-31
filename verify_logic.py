#!/usr/bin/env python3
"""
Logic Verification - Check if calculations are accurate
Show raw data and step-by-step scoring
"""

import os
from dotenv import load_dotenv
from advanced_options_selector import AdvancedOptionsSelector
from real_options_pricing import RealOptionsPricer

load_dotenv()

def verify_spy_analysis():
    """Verify SPY $655 CALL analysis step by step"""
    
    print("🔍 LOGIC VERIFICATION: SPY $655 CALL")
    print("=" * 60)
    
    # Initialize components
    selector = AdvancedOptionsSelector(
        polygon_api_key=os.getenv('POLYGON_API_KEY'),
        tiingo_api_key=os.getenv('TIINGO_API_KEY')
    )
    
    pricer = RealOptionsPricer(polygon_api_key=os.getenv('POLYGON_API_KEY'))
    
    # Get raw option data
    symbol = "SPY"
    strike = 655.0
    expiry = "2025-08-29"
    option_type = "CALL"
    
    print(f"\n📊 RAW DATA COLLECTION:")
    print(f"Target: {symbol} ${strike} {option_type} exp {expiry}")
    
    # 1. Get option data
    option_data = pricer.get_real_option_price(symbol, strike, expiry, option_type)
    
    if not option_data:
        print("❌ No option data received")
        return
    
    print(f"\n💰 OPTION DATA:")
    print(f"   Last Price: ${option_data.last_price}")
    print(f"   Bid: ${option_data.bid}")
    print(f"   Ask: ${option_data.ask}")
    print(f"   Mid Price: ${option_data.mid_price}")
    print(f"   Volume: {option_data.volume}")
    print(f"   Open Interest: {option_data.open_interest}")
    print(f"   Implied Volatility: {option_data.implied_volatility:.3f}")
    print(f"   Days to Expiry: {option_data.days_to_expiry}")
    print(f"   Moneyness: {option_data.moneyness:.3f}")
    
    # 2. Calculate spread
    spread_pct = ((option_data.ask - option_data.bid) / option_data.mid_price * 100) if option_data.mid_price > 0 else 100
    print(f"\n📐 SPREAD CALCULATION:")
    print(f"   Bid-Ask Spread: ${option_data.ask:.2f} - ${option_data.bid:.2f} = ${option_data.ask - option_data.bid:.2f}")
    print(f"   Spread %: {spread_pct:.1f}%")
    
    # 3. Liquidity Score
    liquidity_score = selector.calculate_liquidity_score(option_data.volume, option_data.open_interest, spread_pct)
    print(f"\n🌊 LIQUIDITY SCORE BREAKDOWN:")
    print(f"   Volume: {option_data.volume} contracts")
    
    # Volume scoring logic
    volume_points = 0
    if option_data.volume >= 1000:
        volume_points = 40
    elif option_data.volume >= 500:
        volume_points = 30
    elif option_data.volume >= 100:
        volume_points = 20
    elif option_data.volume >= 50:
        volume_points = 10
    
    print(f"   Volume Points: {volume_points}/40")
    
    # Open Interest scoring
    oi_points = 0
    if option_data.open_interest >= 5000:
        oi_points = 40
    elif option_data.open_interest >= 1000:
        oi_points = 30
    elif option_data.open_interest >= 500:
        oi_points = 20
    elif option_data.open_interest >= 100:
        oi_points = 10
        
    print(f"   Open Interest: {option_data.open_interest} → {oi_points}/40 points")
    
    # Spread scoring
    spread_points = 0
    if spread_pct <= 5:
        spread_points = 20
    elif spread_pct <= 10:
        spread_points = 15
    elif spread_pct <= 15:
        spread_points = 10
    elif spread_pct <= 25:
        spread_points = 5
        
    print(f"   Spread: {spread_pct:.1f}% → {spread_points}/20 points")
    print(f"   TOTAL LIQUIDITY: {liquidity_score}/100")
    
    # 4. Get underlying data for value score
    stock_data = selector.data_manager.get_stock_data(symbol)
    if stock_data:
        df = stock_data['price_data']
        close_col = 'Close' if 'Close' in df.columns else 'close'
        
        # Calculate historical volatility
        returns = df[close_col].pct_change().dropna()
        if len(returns) > 30:
            historical_vol = returns.tail(30).std() * (252**0.5)  # Annualized
        else:
            historical_vol = 0.2  # Default
            
        print(f"\n📈 UNDERLYING DATA:")
        print(f"   Historical Vol (30d): {historical_vol:.3f}")
        print(f"   Implied Vol: {option_data.implied_volatility:.3f}")
        
        # 5. Value Score
        value_score = selector.calculate_value_score(option_data.implied_volatility, historical_vol, option_data.moneyness, option_data.days_to_expiry)
        
        print(f"\n💎 VALUE SCORE BREAKDOWN:")
        
        # IV vs HV comparison
        if historical_vol > 0:
            iv_premium = (option_data.implied_volatility - historical_vol) / historical_vol
            print(f"   IV Premium: {iv_premium:.3f} ({iv_premium*100:+.1f}%)")
            
            iv_points = 0
            if iv_premium < -0.2:
                iv_points = 30
                print("   IV Analysis: IV 20% below HV - CHEAP (+30 pts)")
            elif iv_premium < -0.1:
                iv_points = 20
                print("   IV Analysis: IV 10% below HV (+20 pts)")
            elif iv_premium < 0:
                iv_points = 10
                print("   IV Analysis: IV below HV (+10 pts)")
            elif iv_premium > 0.3:
                iv_points = -20
                print("   IV Analysis: IV 30% above HV - EXPENSIVE (-20 pts)")
            elif iv_premium > 0.1:
                iv_points = -10
                print("   IV Analysis: IV 10% above HV (-10 pts)")
            else:
                print("   IV Analysis: IV roughly fair (0 pts)")
        
        # Moneyness analysis
        moneyness_points = 0
        if 0.95 <= option_data.moneyness <= 1.05:
            moneyness_points = 15
            print(f"   Moneyness: {option_data.moneyness:.3f} - ATM sweet spot (+15 pts)")
        elif 0.90 <= option_data.moneyness <= 1.10:
            moneyness_points = 10
            print(f"   Moneyness: {option_data.moneyness:.3f} - Reasonable range (+10 pts)")
        elif option_data.moneyness < 0.80 or option_data.moneyness > 1.20:
            moneyness_points = -15
            print(f"   Moneyness: {option_data.moneyness:.3f} - Too far OTM/ITM (-15 pts)")
        else:
            print(f"   Moneyness: {option_data.moneyness:.3f} - Neutral (0 pts)")
            
        # Time to expiry
        dte_points = 0
        if 14 <= option_data.days_to_expiry <= 45:
            dte_points = 10
            print(f"   Days to Expiry: {option_data.days_to_expiry} - Sweet spot (+10 pts)")
        elif option_data.days_to_expiry < 7:
            dte_points = -20
            print(f"   Days to Expiry: {option_data.days_to_expiry} - Too risky (-20 pts)")
        elif option_data.days_to_expiry > 90:
            dte_points = -10
            print(f"   Days to Expiry: {option_data.days_to_expiry} - Too much decay (-10 pts)")
        else:
            print(f"   Days to Expiry: {option_data.days_to_expiry} - Neutral (0 pts)")
            
        print(f"   TOTAL VALUE: {value_score}/100")
        
        # 6. Final scoring weights
        print(f"\n⚖️ FINAL SCORING:")
        weights = {
            'liquidity': 0.25,
            'value': 0.25,
            'momentum': 0.20,
            'volatility': 0.15,
            'risk': -0.15  # Risk reduces score
        }
        
        # Get other scores
        technical_strength, _, _ = selector.analyze_underlying_strength(symbol)
        momentum_score = selector.calculate_momentum_score(technical_strength, "neutral")
        
        vol_score = 50
        if 0.15 <= option_data.implied_volatility <= 0.35:
            vol_score = 80
        elif option_data.implied_volatility < 0.10 or option_data.implied_volatility > 0.50:
            vol_score = 20
            
        risk_score = 0
        if option_data.days_to_expiry < 14:
            risk_score += 30
        if spread_pct > 20:
            risk_score += 20
        if option_data.volume < 50:
            risk_score += 25
        risk_score = min(100, risk_score)
        
        total_score = (
            liquidity_score * weights['liquidity'] +
            value_score * weights['value'] +
            momentum_score * weights['momentum'] +
            vol_score * weights['volatility'] +
            risk_score * weights['risk']
        )
        
        print(f"   Liquidity: {liquidity_score:.0f} × {weights['liquidity']} = {liquidity_score * weights['liquidity']:.1f}")
        print(f"   Value: {value_score:.0f} × {weights['value']} = {value_score * weights['value']:.1f}")
        print(f"   Momentum: {momentum_score:.0f} × {weights['momentum']} = {momentum_score * weights['momentum']:.1f}")
        print(f"   Volatility: {vol_score:.0f} × {weights['volatility']} = {vol_score * weights['volatility']:.1f}")
        print(f"   Risk: {risk_score:.0f} × {weights['risk']} = {risk_score * weights['risk']:.1f}")
        print(f"   TOTAL SCORE: {total_score:.1f}/100")
        
        # Verify against selector
        candidate = selector.score_options_candidate(symbol, strike, expiry, option_type)
        if candidate:
            print(f"\n✅ VERIFICATION:")
            print(f"   Calculated Score: {total_score:.1f}")
            print(f"   Selector Score: {candidate.total_score:.1f}")
            print(f"   Match: {'✅' if abs(total_score - candidate.total_score) < 1 else '❌'}")

if __name__ == "__main__":
    verify_spy_analysis()