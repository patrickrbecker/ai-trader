#!/usr/bin/env python3
"""
Position Tracker - Store and monitor all trading positions
Track recommendations vs actual performance
"""

import json
import os
from datetime import datetime
import yfinance as yf
import pandas as pd

class PositionTracker:
    def __init__(self):
        self.data_dir = "data"
        self.positions_file = "data/positions.json"
        self.recommendations_file = "data/recommendations.json"
        self.performance_file = "data/performance_history.json"
        self.ensure_storage_structure()
        
    def ensure_storage_structure(self):
        """Create storage directories and files"""
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize empty files if they don't exist
        for file_path in [self.positions_file, self.recommendations_file, self.performance_file]:
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    json.dump([], f)
    
    def add_position(self, position_data):
        """Add a new position to tracking"""
        position = {
            'id': f"{position_data['symbol']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'timestamp': datetime.now().isoformat(),
            'symbol': position_data['symbol'],
            'position_type': position_data.get('type', 'STOCK'),  # STOCK, CALL, PUT
            'quantity': position_data['quantity'],
            'entry_price': position_data['entry_price'],
            'strike': position_data.get('strike', None),
            'expiry': position_data.get('expiry', None),
            'entry_date': position_data.get('entry_date', datetime.now().strftime('%Y-%m-%d')),
            'status': 'ACTIVE',
            'total_cost': position_data['quantity'] * position_data['entry_price'],
            'notes': position_data.get('notes', ''),
            'is_simulation': position_data.get('is_simulation', False)
        }
        
        # Load existing positions
        positions = self.load_positions()
        positions.append(position)
        
        # Save updated positions
        with open(self.positions_file, 'w') as f:
            json.dump(positions, f, indent=2)
        
        sim_label = " [SIMULATION]" if position.get('is_simulation') else ""
        print(f"✅ Added position: {position['symbol']} - {position['quantity']} shares/contracts @ ${position['entry_price']}{sim_label}")
        return position['id']
    
    def add_recommendation(self, recommendation_data):
        """Add a trading recommendation to track performance"""
        recommendation = {
            'id': f"rec_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'timestamp': datetime.now().isoformat(),
            'symbol': recommendation_data['symbol'],
            'recommendation_type': recommendation_data['type'],  # BUY, SELL, HOLD
            'position_type': recommendation_data.get('position_type', 'STOCK'),
            'target_price': recommendation_data.get('target_price', None),
            'strike': recommendation_data.get('strike', None),
            'expiry': recommendation_data.get('expiry', None),
            'confidence': recommendation_data.get('confidence', None),
            'reasoning': recommendation_data.get('reasoning', ''),
            'agent_source': recommendation_data.get('agent_source', 'Unknown'),
            'current_price': recommendation_data.get('current_price', None),
            'status': 'ACTIVE'
        }
        
        recommendations = self.load_recommendations()
        recommendations.append(recommendation)
        
        with open(self.recommendations_file, 'w') as f:
            json.dump(recommendations, f, indent=2)
        
        print(f"✅ Added recommendation: {recommendation['recommendation_type']} {recommendation['symbol']}")
        return recommendation['id']
    
    def update_position_performance(self):
        """Update all active positions with current market data"""
        positions = self.load_positions()
        performance_updates = []
        
        print("📊 UPDATING POSITION PERFORMANCE...")
        print("=" * 50)
        
        for position in positions:
            if position['status'] != 'ACTIVE':
                continue
                
            try:
                # Get current market data
                ticker = yf.Ticker(position['symbol'])
                
                if position['position_type'] == 'STOCK':
                    current_price = ticker.history(period='1d')['Close'].iloc[-1]
                    current_value = position['quantity'] * current_price
                    
                elif position['position_type'] in ['CALL', 'PUT']:
                    # For options, we'd need to fetch options chain
                    # Simplified for now - would need option_chain() call
                    current_price = 0  # Placeholder
                    current_value = 0   # Placeholder
                
                # Calculate P&L
                total_pnl = current_value - position['total_cost']
                pnl_pct = (total_pnl / position['total_cost']) * 100
                
                # Create performance record
                performance_record = {
                    'position_id': position['id'],
                    'timestamp': datetime.now().isoformat(),
                    'current_price': current_price,
                    'current_value': current_value,
                    'total_pnl': total_pnl,
                    'pnl_percentage': pnl_pct,
                    'days_held': (datetime.now() - datetime.fromisoformat(position['timestamp'])).days
                }
                
                performance_updates.append(performance_record)
                
                print(f"{position['symbol']}: ${total_pnl:+.2f} ({pnl_pct:+.1f}%)")
                
            except Exception as e:
                print(f"❌ Error updating {position.get('symbol', 'Unknown')}: {e}")
        
        # Save performance history
        if performance_updates:
            performance_history = self.load_performance_history()
            performance_history.extend(performance_updates)
            
            with open(self.performance_file, 'w') as f:
                json.dump(performance_history, f, indent=2)
        
        return performance_updates
    
    def get_position_summary(self):
        """Get summary of all positions"""
        positions = self.load_positions()
        performance_history = self.load_performance_history()
        
        # Get latest performance for each position
        latest_performance = {}
        for record in performance_history:
            pos_id = record['position_id']
            if pos_id not in latest_performance or record['timestamp'] > latest_performance[pos_id]['timestamp']:
                latest_performance[pos_id] = record
        
        print("\n💼 POSITION SUMMARY")
        print("=" * 50)
        
        total_cost = 0
        total_current = 0
        
        for position in positions:
            if position['status'] != 'ACTIVE':
                continue
                
            pos_id = position['id']
            perf = latest_performance.get(pos_id, {})
            
            sim_label = " [SIM]" if position.get('is_simulation') else ""
            print(f"\n{position['symbol']} ({position['position_type']}){sim_label}")
            print(f"   Quantity: {position['quantity']}")
            print(f"   Entry: ${position['entry_price']:.2f} on {position['entry_date']}")
            print(f"   Cost: ${position['total_cost']:.2f}")
            
            if perf:
                print(f"   Current: ${perf['current_price']:.2f}")
                print(f"   Value: ${perf['current_value']:.2f}")
                print(f"   P&L: ${perf['total_pnl']:+.2f} ({perf['pnl_percentage']:+.1f}%)")
                print(f"   Days Held: {perf['days_held']}")
                
                total_cost += position['total_cost']
                total_current += perf['current_value']
        
        if total_cost > 0:
            total_pnl = total_current - total_cost
            total_pnl_pct = (total_pnl / total_cost) * 100
            
            print(f"\n🏆 PORTFOLIO SUMMARY:")
            print(f"   Total Cost: ${total_cost:.2f}")
            print(f"   Current Value: ${total_current:.2f}")
            print(f"   Total P&L: ${total_pnl:+.2f} ({total_pnl_pct:+.1f}%)")
    
    def load_positions(self):
        """Load positions from file"""
        try:
            with open(self.positions_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def load_recommendations(self):
        """Load recommendations from file"""
        try:
            with open(self.recommendations_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def load_performance_history(self):
        """Load performance history from file"""
        try:
            with open(self.performance_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

def main():
    """Demo the position tracker"""
    tracker = PositionTracker()
    
    print("🎯 POSITION TRACKER DEMO")
    print("=" * 40)
    
    # Add your Intel position
    intel_position = {
        'symbol': 'INTC',
        'type': 'STOCK',
        'quantity': 2,
        'entry_price': 20.42,
        'entry_date': '2025-07-30',
        'notes': 'Turnaround value play - multi-agent recommendation'
    }
    
    tracker.add_position(intel_position)
    
    # Add a recommendation example
    spy_recommendation = {
        'symbol': 'SPY',
        'type': 'BUY',
        'position_type': 'CALL',
        'strike': 655,
        'expiry': '2025-08-29',
        'target_price': 1.85,
        'confidence': 49.7,
        'reasoning': 'Monthly options screener - 3.6% move needed',
        'agent_source': 'Monthly Options Screener',
        'current_price': 632.07
    }
    
    tracker.add_recommendation(spy_recommendation)
    
    # Update performance
    tracker.update_position_performance()
    
    # Show summary
    tracker.get_position_summary()

if __name__ == "__main__":
    main()