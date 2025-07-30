#!/usr/bin/env python3
"""
LEAP Capital Management - Multi-Agent Trading System
Inspired by AI Hedge Fund approach but focused on our strategy:
- Stocks for long-term holds (12-24+ months)
- Options for tactical plays (30-60 days)
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
from dataclasses import dataclass
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

@dataclass
class TradingRecommendation:
    """Standard recommendation format for all agents"""
    symbol: str
    action: str  # BUY, SELL, HOLD
    confidence: float  # 0-100
    target_price: Optional[float]
    reasoning: str
    risk_level: str  # LOW, MEDIUM, HIGH
    timeframe: str  # SHORT, MEDIUM, LONG
    agent_name: str

class BaseAgent:
    """Base class for all trading agents"""
    
    def __init__(self, name: str):
        self.name = name
        self.expertise = []
        
    def analyze(self, symbol: str) -> TradingRecommendation:
        """Override this method in each agent"""
        raise NotImplementedError
        
    def get_stock_data(self, symbol: str, period: str = "1y") -> pd.DataFrame:
        """Helper method to get stock data"""
        try:
            ticker = yf.Ticker(symbol)
            return ticker.history(period=period)
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()

class ValueAgent(BaseAgent):
    """Warren Buffett-style value analysis agent"""
    
    def __init__(self):
        super().__init__("Value Agent")
        self.expertise = ["fundamentals", "valuation", "long_term_growth"]
    
    def analyze(self, symbol: str) -> TradingRecommendation:
        """Analyze stock from value investing perspective"""
        print(f"🔍 {self.name} analyzing {symbol}...")
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = self.get_stock_data(symbol, "2y")
            
            if hist.empty:
                return self._default_recommendation(symbol, "Insufficient data")
            
            current_price = hist['Close'].iloc[-1]
            
            # Value metrics
            pe_ratio = info.get('trailingPE', None)
            pb_ratio = info.get('priceToBook', None)
            dividend_yield = info.get('dividendYield', 0) * 100 if info.get('dividendYield') and info.get('dividendYield') < 0.2 else 0
            debt_to_equity = info.get('debtToEquity', None)
            roe = info.get('returnOnEquity', None)
            
            # Price analysis
            week_52_low = info.get('fiftyTwoWeekLow', current_price)
            week_52_high = info.get('fiftyTwoWeekHigh', current_price)
            price_vs_low = ((current_price - week_52_low) / week_52_low) * 100
            
            # Generate recommendation
            bullish_signals = 0
            bearish_signals = 0
            reasoning_points = []
            
            # PE analysis
            if pe_ratio and pe_ratio < 15:
                bullish_signals += 2
                reasoning_points.append(f"Attractive P/E ratio of {pe_ratio:.1f}")
            elif pe_ratio and pe_ratio > 25:
                bearish_signals += 1
                reasoning_points.append(f"High P/E ratio of {pe_ratio:.1f}")
            
            # Dividend analysis
            if dividend_yield > 3:
                bullish_signals += 1
                reasoning_points.append(f"Strong dividend yield of {dividend_yield:.1f}%")
            
            # Price position analysis
            if price_vs_low < 30:
                bullish_signals += 2
                reasoning_points.append(f"Trading near 52-week low (only {price_vs_low:.0f}% above)")
            elif price_vs_low > 80:
                bearish_signals += 1
                reasoning_points.append("Trading near 52-week high - limited upside")
            
            # ROE analysis
            if roe and roe > 15:
                bullish_signals += 1
                reasoning_points.append(f"Strong ROE of {roe:.1f}%")
            
            # Generate final recommendation
            net_signal = bullish_signals - bearish_signals
            
            if net_signal >= 3:
                action = "BUY"
                confidence = min(85, 60 + net_signal * 5)
                risk_level = "LOW"
            elif net_signal >= 1:
                action = "HOLD"
                confidence = 65
                risk_level = "MEDIUM"
            else:
                action = "HOLD"
                confidence = 40
                risk_level = "MEDIUM"
            
            # Target price (simple multiple expansion)
            target_price = current_price * 1.25 if action == "BUY" else current_price
            
            reasoning = f"Value analysis: {' | '.join(reasoning_points)}"
            
            return TradingRecommendation(
                symbol=symbol,
                action=action,
                confidence=confidence,
                target_price=target_price,
                reasoning=reasoning,
                risk_level=risk_level,
                timeframe="LONG",
                agent_name=self.name
            )
            
        except Exception as e:
            return self._default_recommendation(symbol, f"Analysis error: {e}")
    
    def _default_recommendation(self, symbol: str, reason: str) -> TradingRecommendation:
        return TradingRecommendation(
            symbol=symbol,
            action="HOLD",
            confidence=50,
            target_price=None,
            reasoning=reason,
            risk_level="MEDIUM",
            timeframe="LONG",
            agent_name=self.name
        )

class TechnicalAgent(BaseAgent):
    """Technical analysis agent for timing and momentum"""
    
    def __init__(self):
        super().__init__("Technical Agent")
        self.expertise = ["charts", "momentum", "timing"]
    
    def analyze(self, symbol: str) -> TradingRecommendation:
        """Analyze stock from technical perspective"""
        print(f"📈 {self.name} analyzing {symbol}...")
        
        try:
            hist = self.get_stock_data(symbol, "6mo")
            if hist.empty or len(hist) < 50:
                return self._default_recommendation(symbol, "Insufficient price data for technical analysis")
            
            current_price = hist['Close'].iloc[-1]
            
            # Calculate technical indicators (with error handling)
            try:
                sma_20 = hist['Close'].rolling(20).mean().iloc[-1] if len(hist) >= 20 else hist['Close'].mean()
                sma_50 = hist['Close'].rolling(50).mean().iloc[-1] if len(hist) >= 50 else hist['Close'].mean()
            except:
                sma_20 = sma_50 = current_price
            volume_avg = hist['Volume'].rolling(20).mean().iloc[-1]
            recent_volume = hist['Volume'].iloc[-1]
            
            # RSI calculation (simplified)
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1] if not rsi.empty else 50
            
            # Price momentum (with bounds checking)
            try:
                price_change_5d = ((current_price - hist['Close'].iloc[-6]) / hist['Close'].iloc[-6]) * 100 if len(hist) >= 6 else 0
                price_change_20d = ((current_price - hist['Close'].iloc[-21]) / hist['Close'].iloc[-21]) * 100 if len(hist) >= 21 else 0
            except:
                price_change_5d = price_change_20d = 0
            
            # Generate signals
            bullish_signals = 0
            bearish_signals = 0
            reasoning_points = []
            
            # Moving average signals
            if current_price > sma_20 > sma_50:
                bullish_signals += 2
                reasoning_points.append("Price above rising moving averages")
            elif current_price < sma_20 < sma_50:
                bearish_signals += 2
                reasoning_points.append("Price below falling moving averages")
            
            # RSI signals
            if current_rsi < 30:
                bullish_signals += 2
                reasoning_points.append(f"Oversold RSI at {current_rsi:.0f}")
            elif current_rsi > 70:
                bearish_signals += 1
                reasoning_points.append(f"Overbought RSI at {current_rsi:.0f}")
            
            # Momentum signals
            if price_change_5d > 3:
                bullish_signals += 1
                reasoning_points.append(f"Strong 5-day momentum +{price_change_5d:.1f}%")
            elif price_change_5d < -3:
                bearish_signals += 1
                reasoning_points.append(f"Weak 5-day momentum {price_change_5d:.1f}%")
            
            # Volume confirmation
            if recent_volume > volume_avg * 1.5:
                reasoning_points.append("Above-average volume confirms move")
            
            # Final recommendation
            net_signal = bullish_signals - bearish_signals
            
            if net_signal >= 2:
                action = "BUY"
                confidence = min(80, 55 + net_signal * 8)
                risk_level = "MEDIUM"
            elif net_signal <= -2:
                action = "SELL"
                confidence = min(75, 55 + abs(net_signal) * 8)
                risk_level = "MEDIUM"
            else:
                action = "HOLD"
                confidence = 50
                risk_level = "MEDIUM"
            
            target_price = current_price * 1.15 if action == "BUY" else current_price * 0.90 if action == "SELL" else current_price
            
            reasoning = f"Technical analysis: {' | '.join(reasoning_points)}"
            
            return TradingRecommendation(
                symbol=symbol,
                action=action,
                confidence=confidence,
                target_price=target_price,
                reasoning=reasoning,
                risk_level=risk_level,
                timeframe="MEDIUM",
                agent_name=self.name
            )
            
        except Exception as e:
            return self._default_recommendation(symbol, f"Technical analysis error: {e}")
    
    def _default_recommendation(self, symbol: str, reason: str) -> TradingRecommendation:
        return TradingRecommendation(
            symbol=symbol,
            action="HOLD",
            confidence=50,
            target_price=None,
            reasoning=reason,
            risk_level="MEDIUM",
            timeframe="MEDIUM",
            agent_name=self.name
        )

class RiskAgent(BaseAgent):
    """Risk management and position sizing agent"""
    
    def __init__(self):
        super().__init__("Risk Manager")
        self.expertise = ["risk_management", "position_sizing", "volatility"]
    
    def analyze(self, symbol: str) -> TradingRecommendation:
        """Analyze risk characteristics"""
        print(f"⚠️ {self.name} analyzing {symbol}...")
        
        try:
            hist = self.get_stock_data(symbol, "1y")
            if hist.empty:
                return self._default_recommendation(symbol, "No data for risk analysis")
            
            # Calculate volatility metrics
            returns = hist['Close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252) * 100  # Annualized vol
            max_drawdown = self._calculate_max_drawdown(hist['Close'])
            
            # Recent volatility (30 days)
            recent_returns = returns.tail(30)
            recent_vol = recent_returns.std() * np.sqrt(252) * 100
            
            # Risk assessment
            risk_score = 0
            reasoning_points = []
            
            if volatility > 40:
                risk_score += 3
                reasoning_points.append(f"High volatility {volatility:.0f}%")
            elif volatility > 25:
                risk_score += 2
                reasoning_points.append(f"Moderate volatility {volatility:.0f}%")
            else:
                risk_score += 1
                reasoning_points.append(f"Low volatility {volatility:.0f}%")
            
            if max_drawdown > 30:
                risk_score += 2
                reasoning_points.append(f"Large historical drawdown {max_drawdown:.0f}%")
            
            if recent_vol > volatility * 1.5:
                risk_score += 1
                reasoning_points.append("Recent volatility spike")
            
            # Risk categorization
            if risk_score <= 2:
                risk_level = "LOW"
                action = "BUY"
                confidence = 75
            elif risk_score <= 4:
                risk_level = "MEDIUM" 
                action = "HOLD"
                confidence = 60
            else:
                risk_level = "HIGH"
                action = "HOLD"
                confidence = 40
            
            reasoning = f"Risk analysis: {' | '.join(reasoning_points)}"
            
            return TradingRecommendation(
                symbol=symbol,
                action=action,
                confidence=confidence,
                target_price=None,
                reasoning=reasoning,
                risk_level=risk_level,
                timeframe="LONG",
                agent_name=self.name
            )
            
        except Exception as e:
            return self._default_recommendation(symbol, f"Risk analysis error: {e}")
    
    def _calculate_max_drawdown(self, prices: pd.Series) -> float:
        """Calculate maximum drawdown percentage"""
        peak = prices.expanding().max()
        drawdown = ((prices - peak) / peak) * 100
        return abs(drawdown.min())
    
    def _default_recommendation(self, symbol: str, reason: str) -> TradingRecommendation:
        return TradingRecommendation(
            symbol=symbol,
            action="HOLD",
            confidence=50,
            target_price=None,
            reasoning=reason,
            risk_level="MEDIUM",
            timeframe="LONG",
            agent_name=self.name
        )

class PortfolioManager:
    """Combines agent recommendations into final decisions"""
    
    def __init__(self):
        self.agents = [
            ValueAgent(),
            TechnicalAgent(), 
            RiskAgent()
        ]
    
    def get_recommendation(self, symbol: str) -> Dict:
        """Get consensus recommendation from all agents"""
        print(f"\n🎯 LEAP CAPITAL MULTI-AGENT ANALYSIS: {symbol}")
        print("=" * 60)
        
        # Get recommendations from all agents
        recommendations = []
        for agent in self.agents:
            try:
                rec = agent.analyze(symbol)
                recommendations.append(rec)
                time.sleep(0.5)  # Be nice to APIs
            except Exception as e:
                print(f"Error with {agent.name}: {e}")
                continue
        
        if not recommendations:
            return {"error": "No agent recommendations available"}
        
        # Display individual agent views
        print("\n📊 INDIVIDUAL AGENT RECOMMENDATIONS:")
        print("-" * 40)
        
        for rec in recommendations:
            confidence_bar = "█" * int(rec.confidence / 10)
            print(f"{rec.agent_name}: {rec.action} ({rec.confidence:.0f}% confident)")
            print(f"   Risk: {rec.risk_level} | Timeframe: {rec.timeframe}")
            print(f"   Reasoning: {rec.reasoning}")
            print(f"   Confidence: [{confidence_bar:<10}] {rec.confidence:.0f}%")
            print()
        
        # Calculate consensus
        consensus = self._calculate_consensus(recommendations)
        
        print("🏆 CONSENSUS RECOMMENDATION:")
        print("=" * 40)
        print(f"Final Action: {consensus['action']}")
        print(f"Confidence: {consensus['confidence']:.0f}%")
        print(f"Risk Level: {consensus['risk_level']}")
        print(f"Target Price: ${consensus['target_price']:.2f}" if consensus['target_price'] else "Target Price: Not set")
        print(f"Reasoning: {consensus['reasoning']}")
        
        return consensus
    
    def _calculate_consensus(self, recommendations: List[TradingRecommendation]) -> Dict:
        """Calculate weighted consensus from agent recommendations"""
        if not recommendations:
            return {}
        
        # Weight agents by expertise relevance
        weights = {
            "Value Agent": 0.4,      # Primary for stock selection
            "Technical Agent": 0.35,  # Important for timing
            "Risk Manager": 0.25     # Risk overlay
        }
        
        # Calculate weighted scores
        buy_score = 0
        sell_score = 0 
        hold_score = 0
        
        total_confidence = 0
        risk_scores = []
        target_prices = []
        reasoning_parts = []
        
        for rec in recommendations:
            weight = weights.get(rec.agent_name, 0.33)
            confidence_weight = rec.confidence / 100 * weight
            
            if rec.action == "BUY":
                buy_score += confidence_weight
            elif rec.action == "SELL":
                sell_score += confidence_weight  
            else:
                hold_score += confidence_weight
            
            total_confidence += rec.confidence * weight
            
            if rec.target_price:
                target_prices.append(rec.target_price)
            
            risk_scores.append(rec.risk_level)
            reasoning_parts.append(f"{rec.agent_name}: {rec.reasoning}")
        
        # Determine final action
        if buy_score > max(sell_score, hold_score):
            final_action = "BUY"
        elif sell_score > max(buy_score, hold_score):
            final_action = "SELL"
        else:
            final_action = "HOLD"
        
        # Average confidence
        avg_confidence = total_confidence / len(recommendations)
        
        # Risk consensus (most conservative wins)
        if "HIGH" in risk_scores:
            risk_level = "HIGH"
        elif "MEDIUM" in risk_scores:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        # Average target price
        avg_target = np.mean(target_prices) if target_prices else None
        
        return {
            "action": final_action,
            "confidence": avg_confidence,
            "risk_level": risk_level,
            "target_price": avg_target,
            "reasoning": f"Consensus from {len(recommendations)} agents: " + " | ".join(reasoning_parts[:2])
        }

def main():
    """Test the multi-agent system"""
    portfolio_manager = PortfolioManager()
    
    # Test on Intel position
    print("Testing Multi-Agent System on Current Holdings")
    print("=" * 60)
    
    test_symbols = ["INTC", "AAPL", "SPY"]
    
    for symbol in test_symbols:
        try:
            recommendation = portfolio_manager.get_recommendation(symbol)
            print(f"\n✅ Analysis complete for {symbol}")
            print("-" * 60)
        except Exception as e:
            print(f"❌ Error analyzing {symbol}: {e}")
        
        time.sleep(2)  # Pause between symbols

if __name__ == "__main__":
    main()