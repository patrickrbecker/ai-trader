#!/usr/bin/env python3
"""
Enhanced Multi-Agent Trading System with Tiingo Integration
Superior data quality, fundamentals analysis, and comprehensive market intelligence
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Optional
import time

from tiingo_data_provider import TiingoDataProvider

@dataclass
class EnhancedTradingRecommendation:
    symbol: str
    action: str  # BUY, SELL, HOLD
    confidence: float  # 0-100
    target_price: Optional[float]
    reasoning: str
    agent_votes: Dict[str, str]  # Which agents voted for what
    data_quality: str
    risk_score: float  # 0-100 (higher = riskier)
    fundamental_score: Optional[float]  # 0-100 if fundamentals available
    technical_score: float  # 0-100
    market_timing_score: float  # 0-100
    
class EnhancedValueAgent:
    """Value analysis with Tiingo's comprehensive fundamentals"""
    
    def __init__(self, tiingo_provider: TiingoDataProvider):
        self.provider = tiingo_provider
        self.name = "Enhanced Value Agent"
        
    def analyze(self, symbol: str) -> Dict:
        print(f"💎 {self.name} analyzing {symbol}...")
        
        # Get comprehensive data
        stock_data = self.provider.get_stock_data(symbol)
        fundamentals = self.provider.get_fundamentals(symbol)
        
        if not stock_data:
            return {
                'recommendation': 'HOLD',
                'confidence': 0,
                'reasoning': 'No stock data available',
                'score': 50
            }
        
        current_price = stock_data['price_data']['close'].iloc[-1]
        
        # Enhanced metrics with Tiingo's clean data
        enhanced_metrics = self.provider.calculate_enhanced_metrics(stock_data)
        
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
        
        # Fundamental analysis (if available)
        fundamental_score = None
        if fundamentals and fundamentals['daily_fundamentals']:
            try:
                # Analyze recent fundamental metrics
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
            'fundamental_score': fundamental_score,
            'current_price': current_price,
            'enhanced_metrics': enhanced_metrics
        }

class EnhancedTechnicalAgent:
    """Technical analysis with Tiingo's high-quality price data"""
    
    def __init__(self, tiingo_provider: TiingoDataProvider):
        self.provider = tiingo_provider
        self.name = "Enhanced Technical Agent"
        
    def analyze(self, symbol: str) -> Dict:
        print(f"📈 {self.name} analyzing {symbol}...")
        
        stock_data = self.provider.get_stock_data(symbol)
        if not stock_data:
            return {
                'recommendation': 'HOLD',
                'confidence': 0,
                'reasoning': 'No technical data available',
                'score': 50
            }
        
        df = stock_data['price_data']
        current_price = df['close'].iloc[-1]
        
        score = 50
        reasoning_parts = []
        
        # Moving average analysis (with Tiingo's clean data)
        sma_10 = df['close'].tail(10).mean()
        sma_20 = df['close'].tail(20).mean()
        sma_50 = df['close'].tail(50).mean()
        
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
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        if current_rsi < 30:
            score += 15
            reasoning_parts.append(f"Oversold RSI ({current_rsi:.1f})")
        elif current_rsi > 70:
            score -= 15
            reasoning_parts.append(f"Overbought RSI ({current_rsi:.1f})")
        
        # Volume confirmation (Tiingo's accurate volume data)
        avg_volume = df['volume'].tail(20).mean()
        recent_volume = df['volume'].tail(5).mean()
        volume_trend = recent_volume / avg_volume
        
        if volume_trend > 1.5:
            score += 8
            reasoning_parts.append(f"Strong volume ({volume_trend:.1f}x)")
        elif volume_trend < 0.7:
            score -= 5
            reasoning_parts.append(f"Weak volume ({volume_trend:.1f}x)")
        
        # Price momentum
        price_change_5d = ((current_price - df['close'].iloc[-6]) / df['close'].iloc[-6]) * 100
        if price_change_5d > 5:
            score += 10
            reasoning_parts.append(f"Strong 5-day momentum (+{price_change_5d:.1f}%)")
        elif price_change_5d < -5:
            score -= 10
            reasoning_parts.append(f"Weak 5-day momentum ({price_change_5d:.1f}%)")
        
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
            'price_change_5d': price_change_5d,
            'volume_trend': volume_trend
        }

class EnhancedRiskManager:
    """Risk management with Tiingo's comprehensive market data"""
    
    def __init__(self, tiingo_provider: TiingoDataProvider):
        self.provider = tiingo_provider
        self.name = "Enhanced Risk Manager"
        
    def analyze(self, symbol: str) -> Dict:
        print(f"⚠️ {self.name} analyzing {symbol}...")
        
        stock_data = self.provider.get_stock_data(symbol)
        if not stock_data:
            return {
                'recommendation': 'HOLD',
                'confidence': 50,
                'reasoning': 'No risk data available',
                'risk_score': 50
            }
        
        df = stock_data['price_data']
        enhanced_metrics = self.provider.calculate_enhanced_metrics(stock_data)
        
        risk_score = 0  # Start at low risk
        reasoning_parts = []
        
        # Volatility risk (using Tiingo's clean data)
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
        rolling_max = df['close'].rolling(window=30).max()
        drawdown = ((df['close'] - rolling_max) / rolling_max) * 100
        max_drawdown_30d = drawdown.min()
        
        if max_drawdown_30d < -20:
            risk_score += 25
            reasoning_parts.append(f"Severe drawdown ({max_drawdown_30d:.1f}%)")
        elif max_drawdown_30d < -10:
            risk_score += 15
            reasoning_parts.append(f"Moderate drawdown ({max_drawdown_30d:.1f}%)")
        
        # Volume liquidity risk
        avg_dollar_volume = (df['close'] * df['volume']).tail(20).mean()
        if avg_dollar_volume < 1000000:  # $1M daily
            risk_score += 20
            reasoning_parts.append("Low liquidity risk")
        elif avg_dollar_volume > 100000000:  # $100M daily
            risk_score -= 5
            reasoning_parts.append("High liquidity (low risk)")
        
        # Price stability
        price_changes = df['close'].pct_change().tail(30)
        extreme_moves = (abs(price_changes) > 0.05).sum()  # Days with >5% moves
        if extreme_moves > 10:
            risk_score += 15
            reasoning_parts.append(f"{extreme_moves} extreme moves (30d)")
        
        # Market timing risk (current vs historical levels)
        current_price = df['close'].iloc[-1]
        price_52w_high = df['close'].tail(252).max()
        price_52w_low = df['close'].tail(252).min()
        
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

class EnhancedMultiAgentTradingSystem:
    """Enhanced multi-agent system with Tiingo's superior data"""
    
    def __init__(self):
        self.tiingo_provider = TiingoDataProvider()
        self.value_agent = EnhancedValueAgent(self.tiingo_provider)
        self.technical_agent = EnhancedTechnicalAgent(self.tiingo_provider)
        self.risk_manager = EnhancedRiskManager(self.tiingo_provider)
        
        print("🤖 Enhanced Multi-Agent Trading System Initialized")
        print("   🔋 Powered by Tiingo's institutional-grade data")
        print("   📊 Features: Fundamentals, Technical, Risk Management")
        
    def analyze_symbol(self, symbol: str) -> EnhancedTradingRecommendation:
        print(f"\n🎯 COMPREHENSIVE ANALYSIS: {symbol}")
        print("=" * 60)
        
        # Get analysis from all agents
        value_analysis = self.value_agent.analyze(symbol)
        technical_analysis = self.technical_agent.analyze(symbol)
        risk_analysis = self.risk_manager.analyze(symbol)
        
        # Collect agent votes
        agent_votes = {
            'Value Agent': value_analysis['recommendation'],
            'Technical Agent': technical_analysis['recommendation'],
            'Risk Manager': risk_analysis['recommendation']
        }
        
        # Weighted consensus (Risk Manager has veto power)
        if risk_analysis['risk_score'] > 70:
            # High risk - Risk Manager overrides
            final_recommendation = 'SELL'
            confidence = risk_analysis['confidence']
            reasoning = f"High risk override: {risk_analysis['reasoning']}"
        else:
            # Normal consensus with weights
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
            
            # Combine reasoning
            reasoning_parts = [
                f"Value: {value_analysis['reasoning']}",
                f"Technical: {technical_analysis['reasoning']}",
                f"Risk: {risk_analysis['reasoning']}"
            ]
            reasoning = " | ".join(reasoning_parts)
        
        # Calculate target price (if BUY)
        target_price = None
        if final_recommendation == 'BUY' and value_analysis.get('current_price'):
            current_price = value_analysis['current_price']
            # Conservative 10-15% upside target
            upside_potential = 0.10 if risk_analysis['risk_score'] > 30 else 0.15
            target_price = current_price * (1 + upside_potential)
        
        # Create comprehensive recommendation
        recommendation = EnhancedTradingRecommendation(
            symbol=symbol,
            action=final_recommendation,
            confidence=round(confidence, 1),
            target_price=round(target_price, 2) if target_price else None,
            reasoning=reasoning,
            agent_votes=agent_votes,
            data_quality="Enhanced (Tiingo)",
            risk_score=risk_analysis['risk_score'],
            fundamental_score=value_analysis.get('fundamental_score'),
            technical_score=technical_analysis['score'],
            market_timing_score=100 - risk_analysis['risk_score']  # Inverse of risk
        )
        
        return recommendation
        
    def display_recommendation(self, recommendation: EnhancedTradingRecommendation):
        """Display comprehensive recommendation"""
        print(f"\n🎯 FINAL RECOMMENDATION: {recommendation.symbol}")
        print("=" * 60)
        print(f"   🎪 Action: {recommendation.action}")
        print(f"   🎯 Confidence: {recommendation.confidence}%")
        if recommendation.target_price:
            print(f"   💰 Target Price: ${recommendation.target_price}")
        print(f"   📊 Data Quality: {recommendation.data_quality}")
        print(f"   ⚠️ Risk Score: {recommendation.risk_score}/100")
        
        print(f"\n📊 AGENT SCORES:")
        if recommendation.fundamental_score:
            print(f"   💎 Fundamental: {recommendation.fundamental_score}/100")
        print(f"   📈 Technical: {recommendation.technical_score}/100")
        print(f"   ⏰ Market Timing: {recommendation.market_timing_score}/100")
        
        print(f"\n🗳️ AGENT VOTES:")
        for agent, vote in recommendation.agent_votes.items():
            print(f"   {agent}: {vote}")
        
        print(f"\n💭 REASONING:")
        print(f"   {recommendation.reasoning}")

def main():
    """Test enhanced multi-agent system"""
    system = EnhancedMultiAgentTradingSystem()
    
    # Test with current positions
    test_symbols = ['INTC', 'SPY', 'AAPL']
    
    print("\n🚀 ENHANCED MULTI-AGENT ANALYSIS")
    print("Using Tiingo's institutional-grade data")
    print("=" * 70)
    
    recommendations = []
    
    for symbol in test_symbols:
        recommendation = system.analyze_symbol(symbol)
        system.display_recommendation(recommendation)
        recommendations.append(recommendation)
        
        print("\n" + "="*70)
        time.sleep(1)  # Rate limiting
    
    # Summary
    print(f"\n📋 PORTFOLIO SUMMARY")
    print("=" * 40)
    for rec in recommendations:
        action_emoji = "🟢" if rec.action == "BUY" else "🔴" if rec.action == "SELL" else "🟡"
        print(f"{action_emoji} {rec.symbol}: {rec.action} ({rec.confidence}% confidence)")

if __name__ == "__main__":
    main()