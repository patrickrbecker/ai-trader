#!/usr/bin/env python3
"""
Automated Position Monitor - Real-time alerts for live trades
CEO-level position management with institutional discipline
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import yfinance as yf

from smart_data_manager import SmartDataManager
from position_tracker import PositionTracker
from real_options_pricing import RealOptionsPricer

@dataclass
class PositionAlert:
    timestamp: str
    symbol: str
    alert_type: str  # "PROFIT_TARGET", "STOP_LOSS", "TIME_WARNING", "VOLATILITY_SPIKE"
    current_price: float
    option_value: float
    pnl_dollars: float
    pnl_percent: float
    days_remaining: int
    message: str
    action_required: str
    urgency: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"

class AutomatedPositionMonitor:
    def __init__(self, polygon_api_key: str = None):
        """Initialize automated monitoring system with triple-source data"""
        self.data_manager = SmartDataManager(polygon_api_key=polygon_api_key)
        self.position_tracker = PositionTracker()
        self.options_pricer = RealOptionsPricer(polygon_api_key=polygon_api_key)  # Enhanced with Polygon!
        self.alerts_file = "data/position_alerts.json"
        self.monitoring_active = True
        
        # Load live positions
        self.live_positions = self._load_live_positions()
        
        print("🚨 AUTOMATED POSITION MONITOR INITIALIZED")
        print(f"   🎯 Monitoring {len(self.live_positions)} live positions")
        print("   ⏰ Real-time alerts enabled")
        print("   📊 Institutional-grade risk management")
        
    def _load_live_positions(self) -> List[Dict]:
        """Load positions that are NOT simulations"""
        positions = self.position_tracker.load_positions()
        live_positions = []
        
        for position in positions:
            if (position['status'] == 'ACTIVE' and 
                not position.get('is_simulation', False)):
                live_positions.append(position)
        
        return live_positions
    
    def monitor_spy_call_position(self) -> List[PositionAlert]:
        """Monitor the SPY $655 CALL position specifically"""
        print(f"\n🎯 MONITORING SPY $655 CALL POSITION")
        print("=" * 50)
        
        alerts = []
        
        # Find SPY call position
        spy_position = None
        for position in self.live_positions:
            if (position['symbol'] == 'SPY' and 
                position['position_type'] == 'CALL' and 
                position.get('strike') == 655):
                spy_position = position
                break
        
        if not spy_position:
            print("❌ SPY $655 CALL position not found")
            return []
        
        # Get current market data
        try:
            stock_data = self.data_manager.get_stock_data('SPY')
            if not stock_data:
                print("❌ Unable to fetch SPY data")
                return []
            
            current_spy_price = stock_data['price_data']['close'].iloc[-1] if 'close' in stock_data['price_data'].columns else stock_data['price_data']['Close'].iloc[-1]
            
            # Calculate days remaining
            expiry_date = datetime.strptime(spy_position['expiry'], '%Y-%m-%d')
            days_remaining = (expiry_date - datetime.now()).days
            
            # Get REAL option value from market data
            real_option_data = self.options_pricer.get_real_option_price(
                'SPY', 
                spy_position['strike'], 
                spy_position['expiry'], 
                'CALL'
            )
            
            if not real_option_data:
                print("   ❌ Unable to fetch real option data")
                return []
            
            option_value = real_option_data.mid_price
            
            # Calculate P&L
            entry_price = spy_position['entry_price']
            pnl_dollars = option_value - entry_price
            pnl_percent = (pnl_dollars / entry_price) * 100
            
            print(f"📊 SPY Current Price: ${current_spy_price:.2f}")
            print(f"📊 Option REAL Market Value: ${option_value:.2f} (Bid: ${real_option_data.bid:.2f}, Ask: ${real_option_data.ask:.2f})")
            print(f"💰 P&L: ${pnl_dollars*100:.0f} ({pnl_percent:+.1f}%)")
            print(f"⏰ Days Remaining: {days_remaining}")
            print(f"📊 Volume: {real_option_data.volume:,} | OI: {real_option_data.open_interest:,}")
            print(f"⚡ IV: {real_option_data.implied_volatility*100:.1f}% | Time Value: ${real_option_data.time_value:.2f}")
            
            # Generate alerts based on position status
            alerts.extend(self._check_profit_targets(
                spy_position, current_spy_price, option_value, pnl_percent, days_remaining
            ))
            
            alerts.extend(self._check_stop_losses(
                spy_position, current_spy_price, option_value, pnl_percent, days_remaining
            ))
            
            alerts.extend(self._check_time_warnings(
                spy_position, days_remaining, pnl_percent
            ))
            
            alerts.extend(self._check_volatility_conditions(
                stock_data, current_spy_price
            ))
            
        except Exception as e:
            print(f"❌ Error monitoring position: {e}")
        
        return alerts
    
    # REMOVED: Broken estimation method - now uses REAL market data only!
    
    def _check_profit_targets(self, position: Dict, stock_price: float, 
                            option_value: float, pnl_percent: float, 
                            days_remaining: int) -> List[PositionAlert]:
        """Check for profit-taking opportunities"""
        alerts = []
        
        # 25% profit target
        if pnl_percent >= 25 and pnl_percent < 50:
            alerts.append(PositionAlert(
                timestamp=datetime.now().isoformat(),
                symbol=position['symbol'],
                alert_type="PROFIT_TARGET",
                current_price=stock_price,
                option_value=option_value,
                pnl_dollars=(option_value - position['entry_price']) * 100,
                pnl_percent=pnl_percent,
                days_remaining=days_remaining,
                message=f"🎯 25% PROFIT TARGET HIT! Consider taking 25% position off table.",
                action_required="Consider partial profit taking (25% of position)",
                urgency="MEDIUM"
            ))
        
        # 50% profit target
        elif pnl_percent >= 50 and pnl_percent < 100:
            alerts.append(PositionAlert(
                timestamp=datetime.now().isoformat(),
                symbol=position['symbol'],
                alert_type="PROFIT_TARGET",
                current_price=stock_price,
                option_value=option_value,
                pnl_dollars=(option_value - position['entry_price']) * 100,
                pnl_percent=pnl_percent,
                days_remaining=days_remaining,
                message=f"🚀 50% PROFIT TARGET HIT! Strong recommendation to take 50% profits.",
                action_required="Take 50% profits, let remainder ride with trailing stop",
                urgency="HIGH"
            ))
        
        # 100% profit target (home run)
        elif pnl_percent >= 100:
            alerts.append(PositionAlert(
                timestamp=datetime.now().isoformat(),
                symbol=position['symbol'],
                alert_type="PROFIT_TARGET",
                current_price=stock_price,
                option_value=option_value,
                pnl_dollars=(option_value - position['entry_price']) * 100,
                pnl_percent=pnl_percent,
                days_remaining=days_remaining,
                message=f"💎 100% PROFIT HIT! HOME RUN TRADE! Consider full exit.",
                action_required="Take full profits - this is institutional success",
                urgency="CRITICAL"
            ))
        
        return alerts
    
    def _check_stop_losses(self, position: Dict, stock_price: float, 
                         option_value: float, pnl_percent: float, 
                         days_remaining: int) -> List[PositionAlert]:
        """Check for stop-loss triggers"""
        alerts = []
        
        # 30% stop loss
        if pnl_percent <= -30:
            alerts.append(PositionAlert(
                timestamp=datetime.now().isoformat(),
                symbol=position['symbol'],
                alert_type="STOP_LOSS",
                current_price=stock_price,
                option_value=option_value,
                pnl_dollars=(option_value - position['entry_price']) * 100,
                pnl_percent=pnl_percent,
                days_remaining=days_remaining,
                message=f"🚨 STOP LOSS TRIGGERED! Position down {pnl_percent:.1f}%",
                action_required="EXIT POSITION IMMEDIATELY - Cut losses",
                urgency="CRITICAL"
            ))
        
        # SPY technical stop (below $625)
        elif stock_price < 625:
            alerts.append(PositionAlert(
                timestamp=datetime.now().isoformat(),
                symbol=position['symbol'],
                alert_type="STOP_LOSS",
                current_price=stock_price,
                option_value=option_value,
                pnl_dollars=(option_value - position['entry_price']) * 100,
                pnl_percent=pnl_percent,
                days_remaining=days_remaining,
                message=f"🚨 SPY BROKE TECHNICAL SUPPORT! SPY at ${stock_price:.2f}",
                action_required="EXIT POSITION - Technical breakdown",
                urgency="CRITICAL"
            ))
        
        return alerts
    
    def _check_time_warnings(self, position: Dict, days_remaining: int, 
                           pnl_percent: float) -> List[PositionAlert]:
        """Check for time decay warnings"""
        alerts = []
        
        # 7 days or less warning
        if days_remaining <= 7 and pnl_percent < 25:
            alerts.append(PositionAlert(
                timestamp=datetime.now().isoformat(),
                symbol=position['symbol'],
                alert_type="TIME_WARNING",
                current_price=0,
                option_value=0,
                pnl_dollars=0,
                pnl_percent=pnl_percent,
                days_remaining=days_remaining,
                message=f"⏰ TIME DECAY CRITICAL! Only {days_remaining} days left",
                action_required="Consider exit if not profitable - time decay accelerating",
                urgency="HIGH"
            ))
        
        # 3 days or less - emergency
        elif days_remaining <= 3:
            alerts.append(PositionAlert(
                timestamp=datetime.now().isoformat(),
                symbol=position['symbol'],
                alert_type="TIME_WARNING",
                current_price=0,
                option_value=0,
                pnl_dollars=0,
                pnl_percent=pnl_percent,
                days_remaining=days_remaining,
                message=f"🚨 EXPIRATION IMMINENT! {days_remaining} days left",
                action_required="EXIT POSITION TODAY - Expiration risk",
                urgency="CRITICAL"
            ))
        
        return alerts
    
    def _check_volatility_conditions(self, stock_data: Dict, stock_price: float) -> List[PositionAlert]:
        """Check for volatility spikes or drops"""
        alerts = []
        
        try:
            # Get VIX data for volatility context
            vix_data = yf.Ticker("^VIX").history(period="5d")
            if not vix_data.empty:
                current_vix = vix_data['Close'].iloc[-1]
                
                if current_vix > 25:
                    alerts.append(PositionAlert(
                        timestamp=datetime.now().isoformat(),
                        symbol="SPY",
                        alert_type="VOLATILITY_SPIKE",
                        current_price=stock_price,
                        option_value=0,
                        pnl_dollars=0,
                        pnl_percent=0,
                        days_remaining=0,
                        message=f"⚡ VIX SPIKE! Current VIX: {current_vix:.1f}",
                        action_required="Monitor closely - high volatility environment",
                        urgency="MEDIUM"
                    ))
                
                elif current_vix < 12:
                    alerts.append(PositionAlert(
                        timestamp=datetime.now().isoformat(),
                        symbol="SPY",
                        alert_type="VOLATILITY_SPIKE",
                        current_price=stock_price,
                        option_value=0,
                        pnl_dollars=0,
                        pnl_percent=0,
                        days_remaining=0,
                        message=f"📉 LOW VOLATILITY! Current VIX: {current_vix:.1f}",
                        action_required="Consider exit - low vol kills option premiums",
                        urgency="MEDIUM"
                    ))
        
        except Exception:
            pass  # VIX data not critical
        
        return alerts
    
    def save_alerts(self, alerts: List[PositionAlert]):
        """Save alerts to file for tracking"""
        if not alerts:
            return
        
        # Load existing alerts
        existing_alerts = []
        if os.path.exists(self.alerts_file):
            try:
                with open(self.alerts_file, 'r') as f:
                    existing_alerts = json.load(f)
            except:
                existing_alerts = []
        
        # Add new alerts
        for alert in alerts:
            existing_alerts.append(asdict(alert))
        
        # Save updated alerts
        os.makedirs(os.path.dirname(self.alerts_file), exist_ok=True)
        with open(self.alerts_file, 'w') as f:
            json.dump(existing_alerts, f, indent=2, default=str)
    
    def display_active_alerts(self, alerts: List[PositionAlert]):
        """Display current alerts in order of urgency"""
        if not alerts:
            print("✅ No active alerts - position within normal parameters")
            return
        
        # Sort by urgency
        urgency_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        sorted_alerts = sorted(alerts, key=lambda x: urgency_order.get(x.urgency, 3))
        
        print(f"\n🚨 ACTIVE ALERTS ({len(alerts)} total)")
        print("=" * 60)
        
        for alert in sorted_alerts:
            urgency_emoji = "🚨" if alert.urgency == "CRITICAL" else "⚠️" if alert.urgency == "HIGH" else "💡"
            
            print(f"\n{urgency_emoji} {alert.urgency} - {alert.alert_type}")
            print(f"   📊 {alert.message}")
            print(f"   🎯 Action: {alert.action_required}")
            if alert.pnl_percent != 0:
                print(f"   💰 P&L: ${alert.pnl_dollars:.0f} ({alert.pnl_percent:+.1f}%)")
    
    def run_monitoring_cycle(self):
        """Run one complete monitoring cycle"""
        print(f"\n🔍 POSITION MONITORING CYCLE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Monitor SPY call position
        alerts = self.monitor_spy_call_position()
        
        # Save and display alerts
        self.save_alerts(alerts)
        self.display_active_alerts(alerts)
        
        return alerts

def main():
    """Run automated monitoring"""
    import os
    polygon_key = os.getenv('POLYGON_API_KEY')
    monitor = AutomatedPositionMonitor(polygon_api_key=polygon_key)
    
    print("\n🚨 AUTOMATED POSITION MONITORING")
    print("Running initial monitoring cycle...")
    print("=" * 50)
    
    # Run monitoring cycle
    alerts = monitor.run_monitoring_cycle()
    
    print(f"\n✅ Monitoring cycle complete")
    print(f"📊 Generated {len(alerts)} alerts")
    print("\n💡 Run this script regularly (every 30 minutes during market hours)")
    print("💡 Set up as cron job: */30 9-16 * * 1-5 python3 automated_position_monitor.py")

if __name__ == "__main__":
    main()