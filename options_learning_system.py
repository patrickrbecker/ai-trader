#!/usr/bin/env python3
"""
Options Learning System - Continuously improve selection algorithm
Learn from wins/losses to refine scoring weights and selection criteria
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict

@dataclass
class LearningMetrics:
    feature_name: str
    win_rate_high: float  # Win rate when feature is high
    win_rate_low: float   # Win rate when feature is low
    avg_return_high: float
    avg_return_low: float
    predictive_power: float  # How well this feature predicts success
    current_weight: float
    suggested_weight: float
    confidence: float

class OptionsLearningSystem:
    def __init__(self):
        """Initialize learning system"""
        
        # Current scoring weights (start with defaults, will be tuned)
        self.weights = {
            'liquidity_score': 0.25,
            'value_score': 0.25,
            'momentum_score': 0.20,
            'volatility_score': 0.15,
            'risk_score': -0.15,
            'technical_strength': 0.10,
            'moneyness': 0.05,
            'days_to_expiry': 0.05
        }
        
        # Learning parameters
        self.min_samples = 10  # Minimum trades needed to adjust weights
        self.learning_rate = 0.1  # How quickly to adjust weights
        self.confidence_threshold = 0.7  # Confidence needed for weight changes
        
        # Load existing learning data
        self.learning_data = self._load_learning_data()
        
        print("🧠 OPTIONS LEARNING SYSTEM INITIALIZED")
        print("   🔬 Adaptive weight optimization")
        print("   📊 Feature importance analysis")
        print("   🎯 Continuous model improvement")
        print(f"   📈 Learning from {len(self.learning_data)} historical trades")
    
    def _load_learning_data(self) -> List[Dict]:
        """Load historical learning data"""
        try:
            learning_file = "data/learning/options_learning_data.json"
            if os.path.exists(learning_file):
                with open(learning_file, 'r') as f:
                    data = json.load(f)
                    return data.get('trades', [])
        except Exception as e:
            print(f"   ⚠️ Could not load learning data: {e}")
        
        return []
    
    def record_trade_outcome(self, trade_data: Dict):
        """Record a completed trade for learning"""
        
        # Add timestamp
        trade_data['recorded_timestamp'] = datetime.now().isoformat()
        
        # Add to learning data
        self.learning_data.append(trade_data)
        
        # Save updated data
        self._save_learning_data()
        
        print(f"📝 Recorded trade outcome: {trade_data['symbol']} - {'WIN' if trade_data['win'] else 'LOSS'}")
        
        # Trigger learning if we have enough data
        if len(self.learning_data) >= self.min_samples:
            self.update_model()
    
    def _save_learning_data(self):
        """Save learning data to file"""
        try:
            os.makedirs("data/learning", exist_ok=True)
            learning_file = "data/learning/options_learning_data.json"
            
            with open(learning_file, 'w') as f:
                json.dump({
                    'last_updated': datetime.now().isoformat(),
                    'total_trades': len(self.learning_data),
                    'trades': self.learning_data
                }, f, indent=2, default=str)
                
        except Exception as e:
            print(f"   ❌ Could not save learning data: {e}")
    
    def analyze_feature_performance(self) -> Dict[str, LearningMetrics]:
        """Analyze how different features correlate with success"""
        
        if len(self.learning_data) < self.min_samples:
            print(f"   ⚠️ Need at least {self.min_samples} trades for analysis")
            return {}
        
        print(f"\n🔍 ANALYZING FEATURE PERFORMANCE ({len(self.learning_data)} trades)")
        print("=" * 60)
        
        metrics = {}
        
        # Features to analyze
        features = [
            'liquidity_score', 'value_score', 'momentum_score', 'volatility_score',
            'risk_score', 'technical_strength', 'moneyness', 'days_to_expiry',
            'implied_volatility', 'spread_pct', 'volume', 'open_interest'
        ]
        
        for feature in features:
            if not any(feature in trade for trade in self.learning_data):
                continue
            
            # Get feature values and outcomes
            feature_values = []
            outcomes = []
            returns = []
            
            for trade in self.learning_data:
                if feature in trade and 'win' in trade and 'pnl_percent' in trade:
                    feature_values.append(trade[feature])
                    outcomes.append(trade['win'])
                    returns.append(trade['pnl_percent'])
            
            if len(feature_values) < 5:  # Need minimum samples
                continue
            
            # Split into high/low groups
            median_value = np.median(feature_values)
            
            high_indices = [i for i, v in enumerate(feature_values) if v >= median_value]
            low_indices = [i for i, v in enumerate(feature_values) if v < median_value]
            
            if len(high_indices) < 3 or len(low_indices) < 3:
                continue
            
            # Calculate metrics
            high_outcomes = [outcomes[i] for i in high_indices]
            low_outcomes = [outcomes[i] for i in low_indices]
            high_returns = [returns[i] for i in high_indices]
            low_returns = [returns[i] for i in low_indices]
            
            win_rate_high = np.mean(high_outcomes) * 100
            win_rate_low = np.mean(low_outcomes) * 100
            avg_return_high = np.mean(high_returns)
            avg_return_low = np.mean(low_returns)
            
            # Calculate predictive power (difference in win rates)
            predictive_power = abs(win_rate_high - win_rate_low) / 100
            
            # Calculate confidence (based on sample size and effect size)
            sample_size_factor = min(len(feature_values) / 50, 1.0)  # Max confidence at 50+ samples
            effect_size_factor = min(predictive_power * 2, 1.0)  # Stronger effects = higher confidence
            confidence = (sample_size_factor + effect_size_factor) / 2
            
            # Suggest new weight
            current_weight = self.weights.get(feature, 0.1)
            
            if predictive_power > 0.1:  # Feature has predictive value
                # Increase weight if feature shows strong predictive power
                suggested_weight = current_weight * (1 + predictive_power)
            else:
                # Decrease weight if feature shows little predictive value
                suggested_weight = current_weight * 0.8
            
            # Cap weights
            suggested_weight = max(0.01, min(0.5, suggested_weight))
            
            metrics[feature] = LearningMetrics(
                feature_name=feature,
                win_rate_high=win_rate_high,
                win_rate_low=win_rate_low,
                avg_return_high=avg_return_high,
                avg_return_low=avg_return_low,
                predictive_power=predictive_power,
                current_weight=current_weight,
                suggested_weight=suggested_weight,
                confidence=confidence
            )
            
            print(f"📊 {feature.upper()}:")
            print(f"   Win Rate: High {win_rate_high:.1f}% vs Low {win_rate_low:.1f}%")
            print(f"   Avg Return: High {avg_return_high:+.1f}% vs Low {avg_return_low:+.1f}%")
            print(f"   Predictive Power: {predictive_power:.3f} | Confidence: {confidence:.2f}")
            print(f"   Weight: {current_weight:.3f} → {suggested_weight:.3f}")
            print()
        
        return metrics
    
    def update_model(self):
        """Update model weights based on learning"""
        
        print(f"\n🎯 UPDATING MODEL WEIGHTS")
        print("=" * 40)
        
        # Analyze feature performance
        metrics = self.analyze_feature_performance()
        
        if not metrics:
            print("   ⚠️ Not enough data for weight updates")
            return
        
        # Update weights for features with high confidence
        updates_made = 0
        
        for feature, metric in metrics.items():
            if (metric.confidence >= self.confidence_threshold and 
                feature in self.weights and 
                metric.predictive_power > 0.05):
                
                # Gradual weight adjustment
                old_weight = self.weights[feature]
                new_weight = old_weight + (metric.suggested_weight - old_weight) * self.learning_rate
                
                self.weights[feature] = new_weight
                updates_made += 1
                
                print(f"✅ Updated {feature}: {old_weight:.3f} → {new_weight:.3f}")
        
        if updates_made > 0:
            # Normalize weights to sum to 1.0 (excluding negative weights)
            positive_weights = {k: v for k, v in self.weights.items() if v > 0}
            total_positive = sum(positive_weights.values())
            
            if total_positive > 0:
                for feature in positive_weights:
                    self.weights[feature] = positive_weights[feature] / total_positive
            
            # Save updated weights
            self._save_model_weights()
            
            print(f"📊 Updated {updates_made} weights")
        else:
            print("   📊 No weight updates needed (low confidence)")
    
    def _save_model_weights(self):
        """Save updated model weights"""
        try:
            os.makedirs("data/learning", exist_ok=True)
            weights_file = "data/learning/model_weights.json"
            
            with open(weights_file, 'w') as f:
                json.dump({
                    'last_updated': datetime.now().isoformat(),
                    'weights': self.weights,
                    'total_trades_learned_from': len(self.learning_data)
                }, f, indent=2)
                
            print(f"💾 Model weights saved to {weights_file}")
            
        except Exception as e:
            print(f"   ❌ Could not save model weights: {e}")
    
    def get_optimized_weights(self) -> Dict[str, float]:
        """Get current optimized weights"""
        return self.weights.copy()
    
    def generate_learning_report(self) -> Dict:
        """Generate comprehensive learning report"""
        
        if len(self.learning_data) < 5:
            return {"error": "Insufficient data for learning report"}
        
        print(f"\n📊 LEARNING SYSTEM REPORT")
        print("=" * 50)
        
        # Overall performance metrics
        wins = sum(1 for trade in self.learning_data if trade.get('win', False))
        total_trades = len(self.learning_data)
        win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0
        
        avg_return = np.mean([trade.get('pnl_percent', 0) for trade in self.learning_data])
        
        print(f"📈 Overall Performance:")
        print(f"   Total Trades: {total_trades}")
        print(f"   Win Rate: {win_rate:.1f}%")
        print(f"   Average Return: {avg_return:+.1f}%")
        
        # Best and worst performing features
        metrics = self.analyze_feature_performance()
        
        if metrics:
            best_feature = max(metrics.values(), key=lambda x: x.predictive_power)
            worst_feature = min(metrics.values(), key=lambda x: x.predictive_power)
            
            print(f"\n🏆 Best Predictive Feature: {best_feature.feature_name}")
            print(f"   Predictive Power: {best_feature.predictive_power:.3f}")
            print(f"   Win Rate Difference: {abs(best_feature.win_rate_high - best_feature.win_rate_low):.1f}%")
            
            print(f"\n💔 Least Predictive Feature: {worst_feature.feature_name}")
            print(f"   Predictive Power: {worst_feature.predictive_power:.3f}")
        
        # Success patterns
        successful_trades = [trade for trade in self.learning_data if trade.get('win', False)]
        failed_trades = [trade for trade in self.learning_data if not trade.get('win', False)]
        
        if successful_trades and failed_trades:
            # Analyze patterns in successful trades
            success_patterns = self._analyze_success_patterns(successful_trades, failed_trades)
            
            print(f"\n🎯 SUCCESS PATTERNS:")
            for pattern, description in success_patterns.items():
                print(f"   {pattern}: {description}")
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'avg_return': avg_return,
            'best_feature': best_feature.feature_name if metrics else None,
            'model_weights': self.weights,
            'learning_confidence': len(self.learning_data) / 100  # Confidence improves with more data
        }
    
    def _analyze_success_patterns(self, wins: List[Dict], losses: List[Dict]) -> Dict[str, str]:
        """Identify patterns that separate winners from losers"""
        
        patterns = {}
        
        # Days to expiry pattern
        win_days = np.mean([trade.get('days_to_expiry', 30) for trade in wins])
        loss_days = np.mean([trade.get('days_to_expiry', 30) for trade in losses])
        
        if abs(win_days - loss_days) > 5:
            if win_days > loss_days:
                patterns['Timing'] = f"Longer-dated options perform better ({win_days:.0f} vs {loss_days:.0f} days)"
            else:
                patterns['Timing'] = f"Shorter-dated options perform better ({win_days:.0f} vs {loss_days:.0f} days)"
        
        # Option type pattern
        win_calls = sum(1 for trade in wins if trade.get('option_type') == 'CALL')
        win_puts = sum(1 for trade in wins if trade.get('option_type') == 'PUT')
        loss_calls = sum(1 for trade in losses if trade.get('option_type') == 'CALL')
        loss_puts = sum(1 for trade in losses if trade.get('option_type') == 'PUT')
        
        if win_calls + loss_calls > 0 and win_puts + loss_puts > 0:
            call_win_rate = win_calls / (win_calls + loss_calls) * 100
            put_win_rate = win_puts / (win_puts + loss_puts) * 100
            
            if abs(call_win_rate - put_win_rate) > 15:
                if call_win_rate > put_win_rate:
                    patterns['Direction'] = f"Calls outperform puts ({call_win_rate:.0f}% vs {put_win_rate:.0f}%)"
                else:
                    patterns['Direction'] = f"Puts outperform calls ({put_win_rate:.0f}% vs {call_win_rate:.0f}%)"
        
        # Volatility pattern
        win_iv = np.mean([trade.get('implied_volatility', 0.2) for trade in wins])
        loss_iv = np.mean([trade.get('implied_volatility', 0.2) for trade in losses])
        
        if abs(win_iv - loss_iv) > 0.05:
            if win_iv > loss_iv:
                patterns['Volatility'] = f"Higher IV options win more ({win_iv:.1%} vs {loss_iv:.1%})"
            else:
                patterns['Volatility'] = f"Lower IV options win more ({win_iv:.1%} vs {loss_iv:.1%})"
        
        return patterns

def main():
    """Test learning system"""
    learning_system = OptionsLearningSystem()
    
    # Simulate some trade outcomes for testing
    sample_trades = [
        {
            'symbol': 'SPY',
            'strike': 650,
            'option_type': 'CALL',
            'liquidity_score': 85,
            'value_score': 70,
            'momentum_score': 60,
            'volatility_score': 75,
            'risk_score': 25,
            'technical_strength': 80,
            'moneyness': 1.02,
            'days_to_expiry': 28,
            'implied_volatility': 0.18,
            'spread_pct': 8,
            'volume': 1500,
            'open_interest': 3000,
            'win': True,
            'pnl_percent': 45.2
        },
        {
            'symbol': 'AAPL',
            'strike': 180,
            'option_type': 'PUT',
            'liquidity_score': 60,
            'value_score': 45,
            'momentum_score': 30,
            'volatility_score': 40,
            'risk_score': 60,
            'technical_strength': 35,
            'moneyness': 0.95,
            'days_to_expiry': 14,
            'implied_volatility': 0.35,
            'spread_pct': 15,
            'volume': 200,
            'open_interest': 800,
            'win': False,
            'pnl_percent': -65.0
        }
    ]
    
    print("\n🧪 TESTING LEARNING SYSTEM")
    print("=" * 50)
    
    # Record sample trades
    for trade in sample_trades:
        learning_system.record_trade_outcome(trade)
    
    # Generate learning report
    report = learning_system.generate_learning_report()
    
    # Display optimized weights
    weights = learning_system.get_optimized_weights()
    print(f"\n🎯 Current Model Weights:")
    for feature, weight in weights.items():
        print(f"   {feature}: {weight:.3f}")

if __name__ == "__main__":
    main()