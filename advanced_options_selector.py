#!/usr/bin/env python3
"""
Advanced Options Selector - Institutional-grade options picking algorithm
Uses real market data and quantitative analysis for optimal selection
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import json
import os

from smart_data_manager import SmartDataManager
from real_options_pricing import RealOptionsPricer

@dataclass
class OptionsCandidate:
    symbol: str
    strike: float
    expiry: str
    option_type: str
    current_price: float
    bid: float
    ask: float
    spread_pct: float
    volume: int
    open_interest: int
    implied_volatility: float
    delta: Optional[float]
    theta: Optional[float]
    gamma: Optional[float]
    vega: Optional[float]
    
    # Underlying metrics
    underlying_price: float
    moneyness: float
    days_to_expiry: int
    
    # Scoring components
    liquidity_score: float
    value_score: float
    momentum_score: float
    volatility_score: float
    risk_score: float
    
    # Final assessment
    total_score: float
    probability_profit: float
    max_profit_potential: float
    max_loss_potential: float
    risk_reward_ratio: float
    
    # Market context
    technical_strength: float
    fundamental_strength: float
    news_sentiment: Optional[float]
    
    reasoning: str
    recommendation: str

class AdvancedOptionsSelector:
    def __init__(self, polygon_api_key: str = None, tiingo_api_key: str = None):
        """Initialize advanced options selector with premium data sources"""
        self.data_manager = SmartDataManager(tiingo_api_key=tiingo_api_key, polygon_api_key=polygon_api_key)
        self.options_pricer = RealOptionsPricer(polygon_api_key=polygon_api_key)
        
        # Selection criteria (can be tuned)
        self.min_liquidity_score = 60  # 0-100 scale
        self.min_open_interest = 100
        self.min_volume = 50
        self.max_spread_pct = 15  # Max bid-ask spread %
        self.max_days_to_expiry = 60
        self.min_days_to_expiry = 7
        
        print("🧠 ADVANCED OPTIONS SELECTOR INITIALIZED")
        print("   🎯 Quantitative multi-factor analysis")
        print("   📊 Real market data integration")
        print("   🔬 Institutional-grade selection logic")
        print("   ⚡ Machine learning ready framework")
    
    def analyze_underlying_strength(self, symbol: str) -> Tuple[float, float, str]:
        """Analyze underlying stock strength - technical and fundamental"""
        
        try:
            stock_data = self.data_manager.get_stock_data(symbol)
            if not stock_data:
                return 50.0, 50.0, "No data available"
            
            df = stock_data['price_data']
            current_price = stock_data['metadata']['current_price']
            
            # Technical Analysis
            technical_score = 50  # Neutral baseline
            technical_factors = []
            
            if len(df) >= 50:
                close_col = 'Close' if 'Close' in df.columns else 'close'
                volume_col = 'Volume' if 'Volume' in df.columns else 'volume'
                
                # Moving averages
                sma_20 = df[close_col].tail(20).mean()
                sma_50 = df[close_col].tail(50).mean()
                
                if current_price > sma_20:
                    technical_score += 15
                    technical_factors.append("Above 20-day MA")
                
                if current_price > sma_50:
                    technical_score += 15
                    technical_factors.append("Above 50-day MA")
                
                if sma_20 > sma_50:
                    technical_score += 10
                    technical_factors.append("20MA > 50MA trend")
                
                # Price momentum
                returns_5d = df[close_col].pct_change().tail(5).sum()
                if returns_5d > 0.02:  # 2%+ in 5 days
                    technical_score += 15
                    technical_factors.append("Strong 5-day momentum")
                elif returns_5d < -0.02:
                    technical_score -= 15
                    technical_factors.append("Weak 5-day momentum")
                
                # Volume analysis
                if volume_col in df.columns:
                    avg_volume = df[volume_col].tail(20).mean()
                    recent_volume = df[volume_col].tail(5).mean()
                    
                    if recent_volume > avg_volume * 1.2:
                        technical_score += 10
                        technical_factors.append("Above-average volume")
                
                # Volatility analysis
                returns = df[close_col].pct_change().dropna()
                volatility = returns.tail(30).std() * np.sqrt(252)
                
                if 0.15 < volatility < 0.35:  # Sweet spot for options
                    technical_score += 10
                    technical_factors.append("Optimal volatility range")
            
            # Fundamental Analysis (basic - can be enhanced)
            fundamental_score = 50  # Neutral baseline
            fundamental_factors = []
            
            # Try to get fundamentals from Tiingo
            fundamentals = self.data_manager.get_fundamentals(symbol)
            if fundamentals:
                # Add fundamental analysis logic here
                fundamental_factors.append("Fundamental data available")
            else:
                fundamental_factors.append("Limited fundamental data")
            
            technical_score = max(0, min(100, technical_score))
            reasoning = f"Technical: {', '.join(technical_factors[:3])}. Fundamental: {', '.join(fundamental_factors[:2])}"
            
            return technical_score, fundamental_score, reasoning
            
        except Exception as e:
            return 50.0, 50.0, f"Analysis error: {str(e)}"
    
    def calculate_liquidity_score(self, volume: int, open_interest: int, spread_pct: float) -> float:
        """Calculate liquidity score (0-100)"""
        score = 0
        
        # Volume component (40 points max)
        if volume >= 1000:
            score += 40
        elif volume >= 500:
            score += 30
        elif volume >= 100:
            score += 20
        elif volume >= 50:
            score += 10
        
        # Open Interest component (40 points max)
        if open_interest >= 5000:
            score += 40
        elif open_interest >= 1000:
            score += 30
        elif open_interest >= 500:
            score += 20
        elif open_interest >= 100:
            score += 10
        
        # Spread component (20 points max)
        if spread_pct <= 5:
            score += 20
        elif spread_pct <= 10:
            score += 15
        elif spread_pct <= 15:
            score += 10
        elif spread_pct <= 25:
            score += 5
        
        return min(100, score)
    
    def calculate_value_score(self, iv: float, historical_vol: float, moneyness: float, days_to_expiry: int) -> float:
        """Calculate value score based on IV vs HV and other factors"""
        score = 50  # Neutral baseline
        
        # IV vs HV comparison (most important)
        if historical_vol > 0:
            iv_premium = (iv - historical_vol) / historical_vol
            
            if iv_premium < -0.2:  # IV 20% below HV - cheap
                score += 30
            elif iv_premium < -0.1:  # IV 10% below HV
                score += 20
            elif iv_premium < 0:  # IV below HV
                score += 10
            elif iv_premium > 0.3:  # IV 30% above HV - expensive
                score -= 20
            elif iv_premium > 0.1:  # IV 10% above HV
                score -= 10
        
        # Moneyness consideration
        if 0.95 <= moneyness <= 1.05:  # ATM sweet spot
            score += 15
        elif 0.90 <= moneyness <= 1.10:  # Reasonable range
            score += 10
        elif moneyness < 0.80 or moneyness > 1.20:  # Too far OTM/ITM
            score -= 15
        
        # Time to expiry optimization
        if 14 <= days_to_expiry <= 45:  # Sweet spot
            score += 10
        elif days_to_expiry < 7:  # Too risky
            score -= 20
        elif days_to_expiry > 90:  # Too much time decay
            score -= 10
        
        return max(0, min(100, score))
    
    def calculate_momentum_score(self, technical_strength: float, price_trend: str) -> float:
        """Calculate momentum score"""
        base_score = technical_strength * 0.8  # Base on technical analysis
        
        # Adjust for specific momentum indicators
        if "Strong momentum" in price_trend:
            base_score += 10
        elif "Weak momentum" in price_trend:
            base_score -= 10
        
        return max(0, min(100, base_score))
    
    def calculate_probability_profit(self, moneyness: float, days_to_expiry: int, iv: float, option_type: str) -> float:
        """Calculate probability of profit using simplified model"""
        
        # Distance from ATM
        distance = abs(1 - moneyness)
        
        # Base probability starts at 50% for ATM
        base_prob = 50
        
        # Adjust for moneyness
        if option_type == 'CALL':
            if moneyness > 1:  # ITM
                base_prob += 20
            else:  # OTM
                base_prob -= distance * 100  # Reduce prob for each % OTM
        
        # Adjust for time
        if days_to_expiry > 30:
            base_prob += 10
        elif days_to_expiry < 14:
            base_prob -= 15
        
        # Adjust for volatility
        if iv > 0.3:  # High volatility helps
            base_prob += 10
        elif iv < 0.15:  # Low volatility hurts
            base_prob -= 10
        
        return max(5, min(95, base_prob))
    
    def score_options_candidate(self, symbol: str, strike: float, expiry: str, option_type: str) -> Optional[OptionsCandidate]:
        """Score a single options candidate comprehensively"""
        
        try:
            # Get option data
            option_data = self.options_pricer.get_real_option_price(symbol, strike, expiry, option_type)
            if not option_data:
                return None
            
            # Get underlying analysis
            technical_strength, fundamental_strength, reasoning = self.analyze_underlying_strength(symbol)
            
            # Calculate spread
            spread_pct = ((option_data.ask - option_data.bid) / option_data.mid_price * 100) if option_data.mid_price > 0 else 100
            
            # Calculate component scores
            liquidity_score = self.calculate_liquidity_score(option_data.volume, option_data.open_interest, spread_pct)
            
            # For value score, we need historical volatility
            stock_data = self.data_manager.get_stock_data(symbol)
            historical_vol = 0.2  # Default
            if stock_data:
                df = stock_data['price_data']
                close_col = 'Close' if 'Close' in df.columns else 'close'
                returns = df[close_col].pct_change().dropna()
                if len(returns) > 30:
                    historical_vol = returns.tail(30).std() * np.sqrt(252)
            
            value_score = self.calculate_value_score(option_data.implied_volatility, historical_vol, option_data.moneyness, option_data.days_to_expiry)
            momentum_score = self.calculate_momentum_score(technical_strength, reasoning)
            
            # Volatility score (0-100)
            vol_score = 50
            if 0.15 <= option_data.implied_volatility <= 0.35:
                vol_score = 80
            elif option_data.implied_volatility < 0.10 or option_data.implied_volatility > 0.50:
                vol_score = 20
            
            # Risk score (lower is better)
            risk_score = 0
            if option_data.days_to_expiry < 14:
                risk_score += 30
            if spread_pct > 20:
                risk_score += 20
            if option_data.volume < 50:
                risk_score += 25
            risk_score = min(100, risk_score)
            
            # Calculate total score (weighted average)
            weights = {
                'liquidity': 0.25,
                'value': 0.25,
                'momentum': 0.20,
                'volatility': 0.15,
                'risk': -0.15  # Risk reduces score
            }
            
            total_score = (
                liquidity_score * weights['liquidity'] +
                value_score * weights['value'] +
                momentum_score * weights['momentum'] +
                vol_score * weights['volatility'] +
                risk_score * weights['risk']
            )
            
            # Calculate probability and risk/reward
            prob_profit = self.calculate_probability_profit(option_data.moneyness, option_data.days_to_expiry, option_data.implied_volatility, option_type)
            
            # Calculate underlying price from moneyness and strike
            if option_type == 'CALL':
                underlying_price = option_data.moneyness * strike
            else:  # PUT
                underlying_price = strike / option_data.moneyness if option_data.moneyness > 0 else strike
            
            # Max profit/loss estimates
            if option_type == 'CALL':
                max_profit = (underlying_price * 1.5 - strike - option_data.mid_price) * 100 if underlying_price * 1.5 > strike else 0
                max_loss = option_data.mid_price * 100
            else:  # PUT
                max_profit = (strike - underlying_price * 0.5 - option_data.mid_price) * 100 if strike > underlying_price * 0.5 else 0
                max_loss = option_data.mid_price * 100
            
            risk_reward_ratio = max_profit / max_loss if max_loss > 0 else 0
            
            # Generate recommendation
            if total_score >= 75:
                recommendation = "STRONG BUY"
            elif total_score >= 60:
                recommendation = "BUY"
            elif total_score >= 40:
                recommendation = "HOLD/WATCH"
            else:
                recommendation = "AVOID"
            
            # Detailed reasoning
            score_reasoning = f"Liquidity: {liquidity_score:.0f}, Value: {value_score:.0f}, Momentum: {momentum_score:.0f}, Vol: {vol_score:.0f}, Risk: {risk_score:.0f}. {reasoning}"
            
            return OptionsCandidate(
                symbol=symbol,
                strike=strike,
                expiry=expiry,
                option_type=option_type,
                current_price=option_data.mid_price,
                bid=option_data.bid,
                ask=option_data.ask,
                spread_pct=spread_pct,
                volume=option_data.volume,
                open_interest=option_data.open_interest,
                implied_volatility=option_data.implied_volatility,
                delta=option_data.delta,
                theta=option_data.theta,
                gamma=option_data.gamma,
                vega=option_data.vega,
                underlying_price=underlying_price,
                moneyness=option_data.moneyness,
                days_to_expiry=option_data.days_to_expiry,
                liquidity_score=liquidity_score,
                value_score=value_score,
                momentum_score=momentum_score,
                volatility_score=vol_score,
                risk_score=risk_score,
                total_score=total_score,
                probability_profit=prob_profit,
                max_profit_potential=max_profit,
                max_loss_potential=max_loss,
                risk_reward_ratio=risk_reward_ratio,
                technical_strength=technical_strength,
                fundamental_strength=fundamental_strength,
                news_sentiment=None,  # Can be enhanced with news pipeline
                reasoning=score_reasoning,
                recommendation=recommendation
            )
            
        except Exception as e:
            print(f"   ❌ Error scoring {symbol} {strike} {option_type}: {e}")
            return None
    
    def find_best_options(self, symbols: List[str], max_candidates: int = 10) -> List[OptionsCandidate]:
        """Find best options across multiple symbols and strikes"""
        
        print(f"\n🔍 SCANNING {len(symbols)} SYMBOLS FOR BEST OPTIONS")
        print("=" * 60)
        
        all_candidates = []
        
        for symbol in symbols:
            print(f"\n📊 Analyzing {symbol}...")
            
            # Get current stock price for strike selection
            stock_data = self.data_manager.get_stock_data(symbol)
            if not stock_data:
                continue
            
            # Extract current price from price data (works for all sources)
            df = stock_data['price_data']
            close_col = 'Close' if 'Close' in df.columns else 'close'
            current_price = df[close_col].iloc[-1]  # Most recent close price
            
            # Generate reasonable strike prices around current price
            strikes = [
                current_price * 0.95,  # 5% OTM Put / 5% ITM Call
                current_price * 0.98,  # 2% OTM Put / 2% ITM Call  
                current_price,         # ATM
                current_price * 1.02,  # 2% OTM Call / 2% ITM Put
                current_price * 1.05   # 5% OTM Call / 5% ITM Put
            ]
            
            # Round strikes to reasonable increments
            strikes = [round(s) if s > 100 else round(s, 1) for s in strikes]
            
            # Use available expiration dates (common ones for options)
            # Try next Friday, then next month end
            next_friday = datetime.now() + timedelta(days=(4 - datetime.now().weekday()) % 7)
            if next_friday <= datetime.now():
                next_friday += timedelta(days=7)
            
            expiry_date = next_friday.strftime('%Y-%m-%d')
            
            # Common backup dates if main one fails
            backup_dates = [
                '2025-08-29',  # Known working date
                '2025-09-05',
                '2025-09-19'
            ]
            
            # Test both calls and puts for each strike
            for strike in strikes:
                for option_type in ['CALL', 'PUT']:
                    # Try main expiry date first, then backups
                    candidate = None
                    for try_date in [expiry_date] + backup_dates:
                        candidate = self.score_options_candidate(symbol, strike, try_date, option_type)
                        if candidate:
                            break
                    
                    if candidate and candidate.total_score >= 40:  # Minimum threshold
                        all_candidates.append(candidate)
                        print(f"   ✅ {option_type} ${strike}: Score {candidate.total_score:.0f} ({candidate.recommendation})")
                    
                    time.sleep(0.1)  # Rate limiting
        
        # Sort by total score
        all_candidates.sort(key=lambda x: x.total_score, reverse=True)
        
        print(f"\n🏆 TOP {min(max_candidates, len(all_candidates))} OPTIONS CANDIDATES:")
        print("=" * 60)
        
        top_candidates = all_candidates[:max_candidates]
        
        for i, candidate in enumerate(top_candidates, 1):
            print(f"\n#{i} {candidate.symbol} ${candidate.strike} {candidate.option_type} (exp {candidate.expiry})")
            print(f"   💯 Score: {candidate.total_score:.1f} | {candidate.recommendation}")
            print(f"   💰 Price: ${candidate.current_price:.2f} | Spread: {candidate.spread_pct:.1f}%")
            print(f"   📊 Prob Profit: {candidate.probability_profit:.0f}% | R/R: {candidate.risk_reward_ratio:.1f}:1")
            print(f"   🎯 {candidate.reasoning[:100]}...")
        
        return top_candidates
    
    def save_analysis(self, candidates: List[OptionsCandidate], filename: str = None):
        """Save options analysis results"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"advanced_options_analysis_{timestamp}"
        
        os.makedirs("data/options_analysis", exist_ok=True)
        
        # Save as JSON
        json_file = f"data/options_analysis/{filename}.json"
        with open(json_file, 'w') as f:
            json.dump({
                'analysis_timestamp': datetime.now().isoformat(),
                'candidates': [asdict(candidate) for candidate in candidates]
            }, f, indent=2, default=str)
        
        print(f"\n💾 Analysis saved: {json_file}")

def main():
    """Test advanced options selector"""
    import os
    
    selector = AdvancedOptionsSelector(
        polygon_api_key=os.getenv('POLYGON_API_KEY'),
        tiingo_api_key=os.getenv('TIINGO_API_KEY')
    )
    
    # Test with popular, liquid symbols
    test_symbols = ['SPY', 'QQQ', 'AAPL', 'TSLA', 'NVDA']
    
    print("\n🧪 TESTING ADVANCED OPTIONS SELECTOR")
    print("=" * 50)
    
    # Find best options
    top_candidates = selector.find_best_options(test_symbols, max_candidates=5)
    
    # Save results
    if top_candidates:
        selector.save_analysis(top_candidates)

if __name__ == "__main__":
    main()