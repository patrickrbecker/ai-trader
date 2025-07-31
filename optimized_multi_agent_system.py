#!/usr/bin/env python3
"""
Optimized Multi-Agent Trading System
Efficient API usage with caching + Tiingo/Yahoo fallback
"""

import pandas as pd
import numpy as np
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Optional
import time

from smart_data_manager import SmartDataManager

@dataclass
class OptimizedTradingRecommendation:
    symbol: str
    action: str  # BUY, SELL, HOLD
    confidence: float  # 0-100
    target_price: Optional[float]
    reasoning: str
    agent_votes: Dict[str, str]  # Which agents voted for what
    data_quality: str
    data_source: str  # tiingo or yahoo
    risk_score: float  # 0-100 (higher = riskier)
    fundamental_score: Optional[float]  # 0-100 if fundamentals available
    technical_score: float  # 0-100
    market_timing_score: float  # 0-100

class OptimizedValueAgent:
    """Value analysis with shared data from SmartDataManager"""
    
    def __init__(self, name: str = "Optimized Value Agent"):
        self.name = name
        
    def analyze(self, symbol: str, stock_data: Dict, fundamentals: Dict = None, 
               enhanced_metrics: Dict = None) -> Dict:
        """Analyze using pre-fetched data (no API calls)"""
        print(f"💎 {self.name} analyzing {symbol} (using cached data)...")
        
        if not stock_data or not enhanced_metrics:
            return {
                'recommendation': 'HOLD',
                'confidence': 0,
                'reasoning': 'No data available',
                'score': 50
            }
        
        current_price = enhanced_metrics['current_price']
        score = 50  # Start neutral
        reasoning_parts = []
        
        # Price momentum analysis
        if enhanced_metrics['price_vs_sma50'] < -10:
            score += 15
            reasoning_parts.append(f"Oversold vs 50-day SMA ({enhanced_metrics['price_vs_sma50']:.1f}%)")
        elif enhanced_metrics['price_vs_sma50'] > 20:
            score -= 10
            reasoning_parts.append(f"Expensive vs 50-day SMA ({enhanced_metrics['price_vs_sma50']:.1f}%)")
        
        # Volatility assessment
        if enhanced_metrics['volatility_30d'] > 40:
            score -= 5
            reasoning_parts.append(f"High volatility ({enhanced_metrics['volatility_30d']:.1f}%)")
        elif enhanced_metrics['volatility_30d'] < 20:
            score += 5
            reasoning_parts.append(f"Stable volatility ({enhanced_metrics['volatility_30d']:.1f}%)")
        
        # Volume analysis
        if enhanced_metrics['volume_ratio'] > 1.5:
            score += 8
            reasoning_parts.append(f"High volume interest ({enhanced_metrics['volume_ratio']:.1f}x)")
        elif enhanced_metrics['volume_ratio'] < 0.5:
            score -= 3
            reasoning_parts.append(f"Low volume ({enhanced_metrics['volume_ratio']:.1f}x)")
        
        # Fundamental analysis (if available from Tiingo)
        fundamental_score = None
        if fundamentals and fundamentals.get('daily_fundamentals'):
            try:
                daily_fund = fundamentals['daily_fundamentals']
                if daily_fund and len(daily_fund) > 0:
                    recent_metrics = daily_fund[-1]  # Most recent data
                    
                    # P/E analysis
                    if 'trailingPE' in recent_metrics:
                        pe_ratio = recent_metrics['trailingPE']
                        if pe_ratio and 0 < pe_ratio < 15:
                            score += 10
                            reasoning_parts.append(f"Attractive P/E ({pe_ratio:.1f})")
                        elif pe_ratio and pe_ratio > 30:
                            score -= 8
                            reasoning_parts.append(f"High P/E ({pe_ratio:.1f})")
                    
                    # Dividend yield
                    if 'dividendYield' in recent_metrics:
                        div_yield = recent_metrics['dividendYield']
                        if div_yield and div_yield > 0.03:  # 3%+
                            score += 5
                            reasoning_parts.append(f"Strong dividend ({div_yield*100:.1f}%)")
                    
                    fundamental_score = min(100, max(0, score))
                    
            except Exception as e:
                print(f"   ⚠️ Fundamental analysis error: {e}")
        
        # Determine recommendation
        if score >= 70:
            recommendation = 'BUY'
            confidence = min(95, score)
        elif score <= 35:
            recommendation = 'SELL'
            confidence = min(95, 100 - score)
        else:
            recommendation = 'HOLD'
            confidence = 50
        
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Neutral signals"
        
        print(f"   📊 Score: {score}/100 | Recommendation: {recommendation}")
        
        return {
            'recommendation': recommendation,
            'confidence': confidence,
            'reasoning': reasoning,
            'score': score,
            'fundamental_score': fundamental_score
        }

class OptimizedTechnicalAgent:
    """Technical analysis with shared data from SmartDataManager"""
    
    def __init__(self, name: str = "Optimized Technical Agent"):
        self.name = name
        
    def analyze(self, symbol: str, stock_data: Dict, enhanced_metrics: Dict = None) -> Dict:
        """Analyze using pre-fetched data (no API calls)"""
        print(f"📈 {self.name} analyzing {symbol} (using cached data)...")
        
        if not stock_data or not enhanced_metrics:
            return {
                'recommendation': 'HOLD',
                'confidence': 0,
                'reasoning': 'No technical data available',
                'score': 50
            }
        
        df = stock_data['price_data']
        current_price = enhanced_metrics['current_price']
        
        # Handle column name differences (Tiingo vs Yahoo)
        close_col = 'Close' if 'Close' in df.columns else 'close'
        volume_col = 'Volume' if 'Volume' in df.columns else 'volume'
        
        score = 50
        reasoning_parts = []
        
        # Moving average analysis
        sma_10 = df[close_col].tail(10).mean()
        sma_20 = df[close_col].tail(20).mean()
        sma_50 = df[close_col].tail(50).mean()
        
        # Trend analysis
        if current_price > sma_10 > sma_20 > sma_50:
            score += 20
            reasoning_parts.append("Strong uptrend (price > all MAs)")
        elif current_price < sma_10 < sma_20 < sma_50:
            score -= 20
            reasoning_parts.append("Strong downtrend (price < all MAs)")
        elif current_price > sma_20:
            score += 10
            reasoning_parts.append("Above 20-day MA")
        elif current_price < sma_20:
            score -= 10
            reasoning_parts.append("Below 20-day MA")
        
        # RSI calculation
        delta = df[close_col].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1] if not rsi.empty else 50
        
        if current_rsi < 30:
            score += 15
            reasoning_parts.append(f"Oversold RSI ({current_rsi:.1f})")
        elif current_rsi > 70:
            score -= 15
            reasoning_parts.append(f"Overbought RSI ({current_rsi:.1f})")
        
        # Volume confirmation
        if volume_col in df.columns:
            avg_volume = df[volume_col].tail(20).mean()
            recent_volume = df[volume_col].tail(5).mean()
            volume_trend = recent_volume / avg_volume if avg_volume > 0 else 1
            
            if volume_trend > 1.5:
                score += 8
                reasoning_parts.append(f"Strong volume ({volume_trend:.1f}x)")
            elif volume_trend < 0.7:
                score -= 5
                reasoning_parts.append(f"Weak volume ({volume_trend:.1f}x)")
        
        # Price momentum
        if len(df) >= 6:
            price_change_5d = ((current_price - df[close_col].iloc[-6]) / df[close_col].iloc[-6]) * 100
            if price_change_5d > 5:
                score += 10
                reasoning_parts.append(f"Strong 5-day momentum (+{price_change_5d:.1f}%)")
            elif price_change_5d < -5:
                score -= 10
                reasoning_parts.append(f"Weak 5-day momentum ({price_change_5d:.1f}%)")
        else:
            price_change_5d = 0
        
        # Determine recommendation
        if score >= 70:
            recommendation = 'BUY'
            confidence = min(95, score)
        elif score <= 35:
            recommendation = 'SELL'
            confidence = min(95, 100 - score)
        else:
            recommendation = 'HOLD'
            confidence = 50
        
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Neutral technical signals"
        
        print(f"   📊 Score: {score}/100 | RSI: {current_rsi:.1f} | Recommendation: {recommendation}")
        
        return {
            'recommendation': recommendation,
            'confidence': confidence,
            'reasoning': reasoning,
            'score': score,
            'rsi': current_rsi,
            'price_change_5d': price_change_5d
        }

class OptimizedRiskManager:
    """Risk management with shared data from SmartDataManager"""
    
    def __init__(self, name: str = "Optimized Risk Manager"):
        self.name = name
        
    def analyze(self, symbol: str, stock_data: Dict, enhanced_metrics: Dict = None) -> Dict:
        """Analyze using pre-fetched data (no API calls)"""
        print(f"⚠️ {self.name} analyzing {symbol} (using cached data)...")
        
        if not stock_data or not enhanced_metrics:
            return {
                'recommendation': 'HOLD',
                'confidence': 50,
                'reasoning': 'No risk data available',
                'risk_score': 50
            }
        
        df = stock_data['price_data']
        close_col = 'Close' if 'Close' in df.columns else 'close'
        volume_col = 'Volume' if 'Volume' in df.columns else 'volume'
        
        risk_score = 0
        reasoning_parts = []
        
        # Volatility risk
        volatility = enhanced_metrics['volatility_30d']
        if volatility > 50:
            risk_score += 30
            reasoning_parts.append(f"Very high volatility ({volatility:.1f}%)")
        elif volatility > 30:
            risk_score += 20
            reasoning_parts.append(f"High volatility ({volatility:.1f}%)")
        elif volatility < 15:
            risk_score += 5
            reasoning_parts.append(f"Low volatility ({volatility:.1f}%)")
        
        # Drawdown analysis
        rolling_max = df[close_col].rolling(window=30).max()
        drawdown = ((df[close_col] - rolling_max) / rolling_max) * 100
        max_drawdown_30d = drawdown.min()
        
        if max_drawdown_30d < -20:
            risk_score += 25
            reasoning_parts.append(f"Severe drawdown ({max_drawdown_30d:.1f}%)")
        elif max_drawdown_30d < -10:
            risk_score += 15
            reasoning_parts.append(f"Moderate drawdown ({max_drawdown_30d:.1f}%)")
        
        # Volume liquidity risk
        if volume_col in df.columns:
            avg_dollar_volume = (df[close_col] * df[volume_col]).tail(20).mean()
            if avg_dollar_volume < 1000000:  # $1M daily
                risk_score += 20
                reasoning_parts.append("Low liquidity risk")
            elif avg_dollar_volume > 100000000:  # $100M daily
                risk_score -= 5
                reasoning_parts.append("High liquidity (low risk)")
        
        # Price stability
        price_changes = df[close_col].pct_change().tail(30)
        extreme_moves = (abs(price_changes) > 0.05).sum()  # Days with >5% moves
        if extreme_moves > 10:
            risk_score += 15
            reasoning_parts.append(f"{extreme_moves} extreme moves (30d)")
        
        # Market timing risk
        current_price = enhanced_metrics['current_price']
        if len(df) >= 252:  # Full year of data
            price_52w_high = df[close_col].tail(252).max()
            price_52w_low = df[close_col].tail(252).min()
            
            price_position = (current_price - price_52w_low) / (price_52w_high - price_52w_low)
            if price_position > 0.9:  # Near 52-week high
                risk_score += 10
                reasoning_parts.append("Near 52-week high")
            elif price_position < 0.1:  # Near 52-week low
                risk_score += 5
                reasoning_parts.append("Near 52-week low (some risk)")
        
        # Determine risk-adjusted recommendation
        if risk_score > 60:
            recommendation = 'SELL'  # Too risky
            confidence = min(90, risk_score)
        elif risk_score > 40:
            recommendation = 'HOLD'  # Moderate risk
            confidence = 60
        else:
            recommendation = 'BUY'   # Low risk
            confidence = 70
        
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Normal risk levels"
        
        print(f"   📊 Risk Score: {risk_score}/100 | Recommendation: {recommendation}")
        
        return {
            'recommendation': recommendation,
            'confidence': confidence,
            'reasoning': reasoning,
            'risk_score': risk_score,
            'volatility': volatility,
            'max_drawdown_30d': max_drawdown_30d
        }

class OptimizedMultiAgentTradingSystem:
    """Optimized multi-agent system with efficient data usage"""
    
    def __init__(self):
        self.data_manager = SmartDataManager()
        self.value_agent = OptimizedValueAgent()
        self.technical_agent = OptimizedTechnicalAgent()
        self.risk_manager = OptimizedRiskManager()
        
        print("🚀 Optimized Multi-Agent Trading System Initialized")
        print("   💡 Smart caching: Minimize API calls")
        print("   🔄 Fallback: Tiingo → Yahoo when limits hit")
        print("   📊 Efficient: Shared data between agents")
        
    def analyze_symbols(self, symbols: List[str]) -> Dict[str, OptimizedTradingRecommendation]:
        """Analyze multiple symbols efficiently"""
        print(f"\n🎯 EFFICIENT MULTI-SYMBOL ANALYSIS")
        print("=" * 60)
        
        # Step 1: Batch fetch data once (smart caching + fallback)
        batch_data = self.data_manager.batch_analyze_symbols(symbols, include_fundamentals=True)
        
        # Step 2: Run all agents on cached data (no additional API calls)
        recommendations = {}
        
        for symbol in symbols:
            if symbol not in batch_data:
                print(f"⚠️ No data available for {symbol}, skipping...")
                continue
                
            print(f"\n🤖 Running agents for {symbol}...")
            
            symbol_data = batch_data[symbol]
            stock_data = symbol_data['stock_data']
            enhanced_metrics = symbol_data['enhanced_metrics']
            fundamentals = symbol_data.get('fundamentals')
            data_source = symbol_data['data_source']
            
            # All agents analyze the same cached data
            value_analysis = self.value_agent.analyze(symbol, stock_data, fundamentals, enhanced_metrics)
            technical_analysis = self.technical_agent.analyze(symbol, stock_data, enhanced_metrics)
            risk_analysis = self.risk_manager.analyze(symbol, stock_data, enhanced_metrics)
            
            # Create final recommendation
            recommendation = self._create_consensus_recommendation(
                symbol, value_analysis, technical_analysis, risk_analysis, 
                enhanced_metrics, data_source
            )
            
            recommendations[symbol] = recommendation
        
        # Usage statistics
        stats = self.data_manager.get_usage_stats()
        print(f"\n📊 API USAGE SUMMARY:")
        print(f"   Tiingo requests: {stats['tiingo_requests_used']}/{stats['tiingo_hourly_limit']}")
        print(f"   Cache efficiency: {stats['cache_entries']} entries")
        print(f"   Fallback active: {'Yes' if stats['fallback_active'] else 'No'}")
        
        return recommendations
    
    def _create_consensus_recommendation(self, symbol: str, value_analysis: Dict, 
                                       technical_analysis: Dict, risk_analysis: Dict,
                                       enhanced_metrics: Dict, data_source: str) -> OptimizedTradingRecommendation:
        """Create consensus recommendation from all agents"""
        
        # Collect agent votes
        agent_votes = {
            'Value Agent': value_analysis['recommendation'],
            'Technical Agent': technical_analysis['recommendation'],
            'Risk Manager': risk_analysis['recommendation']
        }
        
        # Weighted consensus (Risk Manager has veto power)
        if risk_analysis['risk_score'] > 70:
            final_recommendation = 'SELL'
            confidence = risk_analysis['confidence']
            reasoning = f"High risk override: {risk_analysis['reasoning']}"
        else:
            buy_votes = sum(1 for vote in agent_votes.values() if vote == 'BUY')
            sell_votes = sum(1 for vote in agent_votes.values() if vote == 'SELL')
            
            if buy_votes >= 2:
                final_recommendation = 'BUY'
                confidence = (value_analysis['confidence'] + technical_analysis['confidence']) / 2
            elif sell_votes >= 2:
                final_recommendation = 'SELL'
                confidence = (value_analysis['confidence'] + technical_analysis['confidence']) / 2
            else:
                final_recommendation = 'HOLD'
                confidence = 50
            
            reasoning_parts = [
                f"Value: {value_analysis['reasoning']}",
                f"Technical: {technical_analysis['reasoning']}",
                f"Risk: {risk_analysis['reasoning']}"
            ]
            reasoning = " | ".join(reasoning_parts)
        
        # Calculate target price
        target_price = None
        if final_recommendation == 'BUY':
            current_price = enhanced_metrics['current_price']
            upside_potential = 0.10 if risk_analysis['risk_score'] > 30 else 0.15
            target_price = current_price * (1 + upside_potential)
        
        return OptimizedTradingRecommendation(
            symbol=symbol,
            action=final_recommendation,
            confidence=round(confidence, 1),
            target_price=round(target_price, 2) if target_price else None,
            reasoning=reasoning,
            agent_votes=agent_votes,
            data_quality=enhanced_metrics.get('data_quality', 'Unknown'),
            data_source=data_source,
            risk_score=risk_analysis['risk_score'],
            fundamental_score=value_analysis.get('fundamental_score'),
            technical_score=technical_analysis['score'],
            market_timing_score=100 - risk_analysis['risk_score']
        )
    
    def display_recommendations(self, recommendations: Dict[str, OptimizedTradingRecommendation]):
        """Display all recommendations in a clean format"""
        print(f"\n🎯 FINAL RECOMMENDATIONS")
        print("=" * 70)
        
        for symbol, rec in recommendations.items():
            action_emoji = "🟢" if rec.action == "BUY" else "🔴" if rec.action == "SELL" else "🟡"
            source_emoji = "🥇" if rec.data_source == "tiingo" else "🥈"
            
            print(f"\n{action_emoji} {symbol} - {rec.action} ({rec.confidence}% confidence)")
            print(f"   {source_emoji} Data: {rec.data_quality}")
            if rec.target_price:
                print(f"   🎯 Target: ${rec.target_price}")
            print(f"   ⚠️ Risk: {rec.risk_score}/100")
            
            print(f"   🗳️ Votes: {' | '.join([f'{k}: {v}' for k, v in rec.agent_votes.items()])}")

def main():
    """Test optimized system"""
    system = OptimizedMultiAgentTradingSystem()
    
    # Test with current positions + a few more
    test_symbols = ['INTC', 'SPY', 'AAPL', 'MSFT']
    
    print("\n🚀 OPTIMIZED MULTI-AGENT ANALYSIS")
    print("Efficient API usage with smart caching")
    print("=" * 70)
    
    # Run analysis
    recommendations = system.analyze_symbols(test_symbols)
    
    # Display results
    system.display_recommendations(recommendations)

if __name__ == "__main__":
    main()