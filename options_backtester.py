#!/usr/bin/env python3
"""
Options Backtesting Framework - Test and validate options selection strategies
Learn from historical data to improve future picks
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

from smart_data_manager import SmartDataManager

@dataclass
class BacktestResult:
    symbol: str
    entry_date: str
    exit_date: str
    strike: float
    option_type: str
    entry_price: float
    exit_price: float
    pnl: float
    pnl_percent: float
    days_held: int
    max_profit: float
    max_loss: float
    win: bool
    underlying_move: float
    iv_change: float
    time_decay_cost: float

@dataclass 
class StrategyPerformance:
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    max_drawdown: float
    total_return: float
    sharpe_ratio: float
    best_trade: float
    worst_trade: float
    avg_days_held: float

class OptionsBacktester:
    def __init__(self):
        """Initialize backtesting framework"""
        self.data_manager = SmartDataManager()
        self.results = []
        
        print("📊 OPTIONS BACKTESTING FRAMEWORK INITIALIZED")
        print("   🔬 Historical strategy validation")
        print("   📈 Performance metrics calculation")
        print("   🧠 Machine learning data generation")
    
    def simulate_historical_option_performance(self, symbol: str, strike: float, 
                                             entry_date: str, expiry_date: str, 
                                             option_type: str, entry_price: float,
                                             hold_days: int = None) -> Optional[BacktestResult]:
        """Simulate how an option would have performed historically"""
        
        try:
            # Get historical stock data
            start_date = (datetime.strptime(entry_date, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d')
            end_date = (datetime.strptime(expiry_date, '%Y-%m-%d') + timedelta(days=5)).strftime('%Y-%m-%d')
            
            stock_data = self.data_manager.get_stock_data(symbol, start_date, end_date)
            if not stock_data:
                return None
            
            df = stock_data['price_data']
            close_col = 'Close' if 'Close' in df.columns else 'close'
            
            # Get entry price
            entry_idx = df.index.get_indexer([entry_date], method='nearest')[0]
            entry_stock_price = df.iloc[entry_idx][close_col]
            
            # Determine exit date
            if hold_days:
                exit_date = (datetime.strptime(entry_date, '%Y-%m-%d') + timedelta(days=hold_days)).strftime('%Y-%m-%d')
                exit_date = min(exit_date, expiry_date)  # Can't hold past expiry
            else:
                exit_date = expiry_date
            
            # Get exit price
            exit_idx = df.index.get_indexer([exit_date], method='nearest')[0]
            exit_stock_price = df.iloc[exit_idx][close_col]
            
            # Calculate option values (simplified Black-Scholes approximation)
            entry_days_to_expiry = (datetime.strptime(expiry_date, '%Y-%m-%d') - datetime.strptime(entry_date, '%Y-%m-%d')).days
            exit_days_to_expiry = (datetime.strptime(expiry_date, '%Y-%m-%d') - datetime.strptime(exit_date, '%Y-%m-%d')).days
            
            # Intrinsic values
            if option_type == 'CALL':
                entry_intrinsic = max(0, entry_stock_price - strike)
                exit_intrinsic = max(0, exit_stock_price - strike)
            else:  # PUT
                entry_intrinsic = max(0, strike - entry_stock_price)
                exit_intrinsic = max(0, strike - exit_stock_price)
            
            # Estimate time value decay (simplified)
            entry_time_value = entry_price - entry_intrinsic
            exit_time_value = entry_time_value * (exit_days_to_expiry / entry_days_to_expiry) if entry_days_to_expiry > 0 else 0
            
            # Exit option price
            exit_price = exit_intrinsic + exit_time_value
            
            # Calculate performance metrics
            pnl = exit_price - entry_price
            pnl_percent = (pnl / entry_price) * 100 if entry_price > 0 else 0
            days_held = (datetime.strptime(exit_date, '%Y-%m-%d') - datetime.strptime(entry_date, '%Y-%m-%d')).days
            
            # Track max profit/loss during holding period
            max_profit = pnl
            max_loss = pnl
            
            underlying_move = (exit_stock_price - entry_stock_price) / entry_stock_price * 100
            time_decay_cost = entry_time_value - exit_time_value
            
            return BacktestResult(
                symbol=symbol,
                entry_date=entry_date,
                exit_date=exit_date,
                strike=strike,
                option_type=option_type,
                entry_price=entry_price,
                exit_price=exit_price,
                pnl=pnl,
                pnl_percent=pnl_percent,
                days_held=days_held,
                max_profit=max_profit,
                max_loss=max_loss,
                win=pnl > 0,
                underlying_move=underlying_move,
                iv_change=0,  # Simplified - would need historical IV data
                time_decay_cost=time_decay_cost
            )
            
        except Exception as e:
            print(f"   ❌ Backtest error for {symbol}: {e}")
            return None
    
    def backtest_strategy(self, strategy_name: str, trades: List[Dict]) -> StrategyPerformance:
        """Backtest a complete strategy with multiple trades"""
        
        print(f"\n📊 BACKTESTING STRATEGY: {strategy_name}")
        print("=" * 50)
        
        results = []
        
        for i, trade in enumerate(trades, 1):
            print(f"[{i}/{len(trades)}] Testing {trade['symbol']} {trade['option_type']} ${trade['strike']}")
            
            result = self.simulate_historical_option_performance(
                symbol=trade['symbol'],
                strike=trade['strike'],
                entry_date=trade['entry_date'],
                expiry_date=trade['expiry_date'],
                option_type=trade['option_type'],
                entry_price=trade['entry_price'],
                hold_days=trade.get('hold_days')
            )
            
            if result:
                results.append(result)
                self.results.append(result)
                print(f"   📊 P&L: ${result.pnl:.2f} ({result.pnl_percent:+.1f}%) in {result.days_held} days")
        
        # Calculate strategy performance
        if not results:
            print("   ❌ No valid backtest results")
            return None
        
        return self._calculate_performance_metrics(results)
    
    def _calculate_performance_metrics(self, results: List[BacktestResult]) -> StrategyPerformance:
        """Calculate comprehensive performance metrics"""
        
        total_trades = len(results)
        winning_trades = sum(1 for r in results if r.win)
        losing_trades = total_trades - winning_trades
        
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        wins = [r.pnl for r in results if r.win]
        losses = [r.pnl for r in results if not r.win]
        
        avg_win = np.mean(wins) if wins else 0
        avg_loss = abs(np.mean(losses)) if losses else 0
        
        profit_factor = (sum(wins) / abs(sum(losses))) if losses else float('inf')
        
        # Calculate cumulative returns for drawdown
        cumulative_pnl = np.cumsum([r.pnl for r in results])
        running_max = np.maximum.accumulate(cumulative_pnl)
        drawdown = (cumulative_pnl - running_max)
        max_drawdown = abs(min(drawdown)) if len(drawdown) > 0 else 0
        
        total_return = sum(r.pnl for r in results)
        
        # Simplified Sharpe ratio
        returns = [r.pnl for r in results]
        sharpe_ratio = (np.mean(returns) / np.std(returns)) if np.std(returns) > 0 else 0
        
        best_trade = max(r.pnl for r in results)
        worst_trade = min(r.pnl for r in results)
        avg_days_held = np.mean([r.days_held for r in results])
        
        performance = StrategyPerformance(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            max_drawdown=max_drawdown,
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            best_trade=best_trade,
            worst_trade=worst_trade,
            avg_days_held=avg_days_held
        )
        
        self._display_performance(performance)
        return performance
    
    def _display_performance(self, perf: StrategyPerformance):
        """Display performance metrics"""
        
        print(f"\n📊 STRATEGY PERFORMANCE SUMMARY")
        print("=" * 40)
        print(f"📈 Total Trades: {perf.total_trades}")
        print(f"🎯 Win Rate: {perf.win_rate:.1f}% ({perf.winning_trades}W/{perf.losing_trades}L)")
        print(f"💰 Total Return: ${perf.total_return:.2f}")
        print(f"📊 Avg Win: ${perf.avg_win:.2f} | Avg Loss: ${perf.avg_loss:.2f}")
        print(f"⚡ Profit Factor: {perf.profit_factor:.2f}")
        print(f"📉 Max Drawdown: ${perf.max_drawdown:.2f}")
        print(f"🔢 Sharpe Ratio: {perf.sharpe_ratio:.2f}")
        print(f"🏆 Best Trade: ${perf.best_trade:.2f}")
        print(f"💔 Worst Trade: ${perf.worst_trade:.2f}")
        print(f"⏰ Avg Days Held: {perf.avg_days_held:.1f}")
        
        # Performance rating
        if perf.win_rate > 60 and perf.profit_factor > 1.5:
            rating = "🟢 EXCELLENT"
        elif perf.win_rate > 50 and perf.profit_factor > 1.2:
            rating = "🟡 GOOD"
        elif perf.win_rate > 40 and perf.profit_factor > 1.0:
            rating = "🟠 FAIR"
        else:
            rating = "🔴 POOR"
        
        print(f"\n🎯 Strategy Rating: {rating}")
    
    def analyze_what_works(self) -> Dict:
        """Analyze patterns in successful vs failed trades"""
        
        if not self.results:
            print("No backtest results to analyze")
            return {}
        
        print(f"\n🧠 ANALYZING SUCCESS PATTERNS")
        print("=" * 40)
        
        wins = [r for r in self.results if r.win]
        losses = [r for r in self.results if not r.win]
        
        analysis = {}
        
        if wins and losses:
            # Days held analysis
            avg_win_days = np.mean([w.days_held for w in wins])
            avg_loss_days = np.mean([l.days_held for l in losses])
            
            print(f"📊 Avg Days Held: Wins {avg_win_days:.1f} vs Losses {avg_loss_days:.1f}")
            
            # Underlying move analysis
            avg_win_move = np.mean([w.underlying_move for w in wins])
            avg_loss_move = np.mean([l.underlying_move for l in losses])
            
            print(f"📈 Avg Underlying Move: Wins {avg_win_move:+.1f}% vs Losses {avg_loss_move:+.1f}%")
            
            # Option type analysis
            call_wins = sum(1 for w in wins if w.option_type == 'CALL')
            call_total = sum(1 for r in self.results if r.option_type == 'CALL')
            put_wins = sum(1 for w in wins if w.option_type == 'PUT')
            put_total = sum(1 for r in self.results if r.option_type == 'PUT')
            
            call_win_rate = (call_wins / call_total * 100) if call_total > 0 else 0
            put_win_rate = (put_wins / put_total * 100) if put_total > 0 else 0
            
            print(f"🎯 Win Rates: Calls {call_win_rate:.1f}% vs Puts {put_win_rate:.1f}%")
            
            analysis = {
                'avg_win_days': avg_win_days,
                'avg_loss_days': avg_loss_days,
                'avg_win_move': avg_win_move,
                'avg_loss_move': avg_loss_move,
                'call_win_rate': call_win_rate,
                'put_win_rate': put_win_rate
            }
        
        return analysis
    
    def save_backtest_results(self, filename: str = None):
        """Save backtest results for further analysis"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"backtest_results_{timestamp}"
        
        os.makedirs("data/backtesting", exist_ok=True)
        
        json_file = f"data/backtesting/{filename}.json"
        with open(json_file, 'w') as f:
            json.dump({
                'backtest_timestamp': datetime.now().isoformat(),
                'total_trades': len(self.results),
                'results': [asdict(result) for result in self.results]
            }, f, indent=2, default=str)
        
        print(f"\n💾 Backtest results saved: {json_file}")

def main():
    """Test backtesting framework"""
    backtester = OptionsBacktester()
    
    # Example trades to backtest (would normally come from historical recommendations)
    sample_trades = [
        {
            'symbol': 'SPY',
            'strike': 640,
            'entry_date': '2025-07-01',
            'expiry_date': '2025-07-31',
            'option_type': 'CALL',
            'entry_price': 2.50,
            'hold_days': 14
        },
        {
            'symbol': 'SPY',
            'strike': 630,
            'entry_date': '2025-06-15',
            'expiry_date': '2025-07-15',
            'option_type': 'CALL',
            'entry_price': 3.00,
            'hold_days': 21
        }
    ]
    
    print("\n🧪 TESTING BACKTESTING FRAMEWORK")
    print("=" * 50)
    
    # Backtest the strategy
    performance = backtester.backtest_strategy("Test Strategy", sample_trades)
    
    # Analyze patterns
    analysis = backtester.analyze_what_works()
    
    # Save results
    backtester.save_backtest_results()

if __name__ == "__main__":
    main()