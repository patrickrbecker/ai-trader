#!/usr/bin/env python3
"""
Simulation Position Tracker
Track paper trading positions to test strategy performance
"""

from position_tracker import PositionTracker
from datetime import datetime
import yfinance as yf

class SimulationTracker(PositionTracker):
    def __init__(self):
        super().__init__()
        
    def add_simulation_position(self, position_data):
        """Add a simulation position"""
        position_data['is_simulation'] = True
        return self.add_position(position_data)
    
    def track_spy_call_simulation(self):
        """Track the SPY $655 CALL as simulation"""
        
        # Get current SPY price for accurate entry
        spy = yf.Ticker('SPY')
        current_spy = spy.history(period='1d')['Close'].iloc[-1]
        
        spy_call_sim = {
            'symbol': 'SPY',
            'type': 'CALL',
            'quantity': 1,  # 1 contract = 100 shares
            'entry_price': 1.71,
            'strike': 655,
            'expiry': '2025-08-29',
            'entry_date': datetime.now().strftime('%Y-%m-%d'),
            'notes': f'Monthly screener top pick - SPY @ ${current_spy:.2f}, needs 3.4% move to ${655}',
            'is_simulation': True
        }
        
        position_id = self.add_simulation_position(spy_call_sim)
        
        print(f"\n🎯 SIMULATION POSITION DETAILS:")
        print(f"   Contract: SPY $655 CALL expiring 2025-08-29")
        print(f"   Entry Price: $1.71 per contract ($171 total cost)")
        print(f"   Current SPY Price: ${current_spy:.2f}")
        print(f"   Break-even: ${655 + 1.71:.2f} (SPY needs to reach)")
        print(f"   Move Required: {((655 - current_spy) / current_spy) * 100:.1f}%")
        print(f"   Days to Expiry: 29")
        print(f"   Time Decay: ~$0.06 per day (rough estimate)")
        print(f"\n📊 PROFIT SCENARIOS:")
        
        scenarios = [
            (660, "1.5% move"),
            (665, "5.0% move"), 
            (670, "5.8% move"),
            (680, "7.3% move")
        ]
        
        for target_price, move_desc in scenarios:
            if target_price > 655:
                intrinsic = target_price - 655
                # Rough estimate: 30% of time value remains
                estimated_value = intrinsic + (1.71 * 0.3)
                profit = estimated_value - 1.71
                profit_pct = (profit / 1.71) * 100
                profit_dollars = profit * 100  # Per contract
                
                print(f"   SPY @ ${target_price}: +${profit_dollars:.0f} ({profit_pct:+.0f}%) - {move_desc}")
        
        print(f"\n⚠️  RISK: Max loss is $171 (100%) if SPY stays below $655")
        
        return position_id

def main():
    """Demo simulation tracking"""
    sim_tracker = SimulationTracker()
    
    print("🎯 SIMULATION TRACKER")
    print("=" * 50)
    
    # Track the SPY call as simulation
    sim_tracker.track_spy_call_simulation()
    
    # Update all positions (real + simulation)
    sim_tracker.update_position_performance()
    
    # Show complete summary
    sim_tracker.get_position_summary()

if __name__ == "__main__":
    main()