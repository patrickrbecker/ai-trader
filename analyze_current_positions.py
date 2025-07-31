#!/usr/bin/env python3
"""
Analyze Current Positions with Advanced Options Intelligence
Test new logic against live positions
"""

import json
from datetime import datetime
from advanced_options_selector import AdvancedOptionsSelector
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def main():
    """Analyze current positions with new intelligence system"""
    
    # Initialize the advanced selector
    selector = AdvancedOptionsSelector(
        polygon_api_key=os.getenv('POLYGON_API_KEY'),
        tiingo_api_key=os.getenv('TIINGO_API_KEY')
    )
    
    # Load current positions
    with open('data/positions.json', 'r') as f:
        positions = json.load(f)
    
    print("\n🔍 ANALYZING CURRENT POSITIONS WITH ADVANCED INTELLIGENCE")
    print("=" * 70)
    
    # Filter for active options positions
    options_positions = [
        p for p in positions 
        if p['status'] == 'ACTIVE' and p['position_type'] in ['CALL', 'PUT']
    ]
    
    print(f"Found {len(options_positions)} active options positions to analyze:\n")
    
    for i, position in enumerate(options_positions, 1):
        # Get stock name for display
        stock_names = {
            'SPY': 'SPDR S&P 500 ETF',
            'QQQ': 'Invesco QQQ Trust',
            'AAPL': 'Apple Inc.',
            'TSLA': 'Tesla Inc.',
            'NVDA': 'NVIDIA Corp.',
            'INTC': 'Intel Corp.'
        }
        stock_name = stock_names.get(position['symbol'], position['symbol'])
        
        print(f"📊 POSITION {i}: {stock_name} ({position['symbol']}) ${position['strike']} {position['position_type']}")
        print(f"   Entry: ${position['entry_price']} on {position['entry_date']}")
        print(f"   Expiry: {position['expiry']}")
        print(f"   Status: {'🔴 SIMULATION' if position.get('is_simulation', False) else '🟢 LIVE TRADE'}")
        print(f"   Notes: {position.get('notes', 'No notes')}")
        
        # Analyze with new system
        candidate = selector.score_options_candidate(
            symbol=position['symbol'],
            strike=position['strike'],
            expiry=position['expiry'],
            option_type=position['position_type']
        )
        
        if candidate:
            print(f"\n   🧠 ADVANCED INTELLIGENCE ANALYSIS:")
            print(f"      🎯 Current Score: {candidate.total_score:.1f}/100 ({candidate.recommendation})")
            print(f"      💰 Current Price: ${candidate.current_price:.2f} (Entry: ${position['entry_price']:.2f})")
            
            # Calculate P&L
            pnl_dollars = (candidate.current_price - position['entry_price']) * 100
            pnl_percent = ((candidate.current_price - position['entry_price']) / position['entry_price']) * 100
            
            pnl_color = "🟢" if pnl_dollars > 0 else "🔴" if pnl_dollars < 0 else "🟡"
            print(f"      📈 P&L: {pnl_color} ${pnl_dollars:.0f} ({pnl_percent:+.1f}%)")
            
            print(f"      ⏰ Days Remaining: {candidate.days_to_expiry}")
            print(f"      🎲 Probability of Profit: {candidate.probability_profit:.0f}%")
            print(f"      ⚖️ Risk/Reward Ratio: {candidate.risk_reward_ratio:.1f}:1")
            
            # Component scores breakdown
            print(f"      📊 Score Breakdown:")
            print(f"         Liquidity: {candidate.liquidity_score:.0f}/100")
            print(f"         Value: {candidate.value_score:.0f}/100") 
            print(f"         Momentum: {candidate.momentum_score:.0f}/100")
            print(f"         Volatility: {candidate.volatility_score:.0f}/100")
            print(f"         Risk: {candidate.risk_score:.0f}/100 (lower is better)")
            
            # Trading recommendation
            if candidate.total_score >= 60:
                if pnl_percent > 20:
                    action = "🎯 CONSIDER PROFIT TAKING"
                else:
                    action = "✅ HOLD - STRONG POSITION"
            elif candidate.total_score >= 40:
                if pnl_percent < -30:
                    action = "⚠️ CONSIDER STOP LOSS"
                else:
                    action = "👀 MONITOR CLOSELY"
            else:
                action = "🚨 CONSIDER CLOSING - WEAK FUNDAMENTALS"
            
            print(f"      🎯 RECOMMENDATION: {action}")
            
        else:
            print(f"   ❌ Could not analyze position (no current market data)")
        
        print("\n" + "─" * 70 + "\n")
    
    # Also analyze stock positions for context
    stock_positions = [
        p for p in positions 
        if p['status'] == 'ACTIVE' and p['position_type'] == 'STOCK'
    ]
    
    if stock_positions:
        print(f"📈 STOCK POSITIONS FOR CONTEXT ({len(stock_positions)} positions):")
        print("─" * 50)
        
        # Remove duplicates (same symbol, same entry date)
        unique_positions = {}
        for position in stock_positions:
            key = f"{position['symbol']}_{position['entry_date']}"
            if key not in unique_positions:
                unique_positions[key] = position
            else:
                # Add quantities if same position
                unique_positions[key]['quantity'] += position['quantity']
        
        for position in unique_positions.values():
            # Get current analysis
            technical_strength, fundamental_strength, reasoning = selector.analyze_underlying_strength(position['symbol'])
            
            stock_names = {
                'SPY': 'SPDR S&P 500 ETF',
                'QQQ': 'Invesco QQQ Trust', 
                'AAPL': 'Apple Inc.',
                'TSLA': 'Tesla Inc.',
                'NVDA': 'NVIDIA Corp.',
                'INTC': 'Intel Corp.'
            }
            stock_name = stock_names.get(position['symbol'], position['symbol'])
            
            print(f"📊 {stock_name} ({position['symbol']}): {position['quantity']} shares @ ${position['entry_price']}")
            print(f"   Technical Strength: {technical_strength:.0f}/100")
            print(f"   Fundamental Strength: {fundamental_strength:.0f}/100") 
            print(f"   Analysis: {reasoning}")
            print()

if __name__ == "__main__":
    main()