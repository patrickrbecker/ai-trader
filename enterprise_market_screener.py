#!/usr/bin/env python3
"""
Enterprise Market Screener - Full NYSE/NASDAQ scanning with 10,000/hour requests
Professional-grade market intelligence for options trading
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple
import threading
from dataclasses import dataclass, asdict

from smart_data_manager import SmartDataManager

@dataclass
class MarketOpportunity:
    symbol: str
    sector: str
    market_cap: str
    current_price: float
    price_change_1d: float
    volume_ratio: float
    volatility_30d: float
    rsi: float
    momentum_score: float
    value_score: float
    risk_score: float
    news_sentiment: Optional[float]  # -1 to +1
    opportunity_type: str  # "breakout", "oversold", "momentum", "value"
    confidence: float
    target_price: Optional[float]
    reasoning: str
    data_source: str

class EnterpriseMarketScreener:
    def __init__(self):
        """Initialize enterprise screener with unlimited API access"""
        self.data_manager = SmartDataManager()
        self.opportunities = []
        self.screening_stats = {
            'symbols_screened': 0,
            'opportunities_found': 0,
            'api_requests_used': 0,
            'processing_time': 0
        }
        
        # Market universe - all major exchanges
        self.market_universe = self._build_comprehensive_market_universe()
        
        print("🏢 ENTERPRISE MARKET SCREENER INITIALIZED")
        print(f"   🚀 API Power: 10,000/hour, 100,000/day")
        print(f"   📊 Universe: {len(self.market_universe)} symbols")
        print(f"   💪 Multi-threading: Enabled")
        print(f"   🎯 Target: Options trading opportunities")
    
    def _build_comprehensive_market_universe(self) -> Dict[str, List[str]]:
        """Build comprehensive market universe for screening"""
        
        # S&P 500 (Large Cap)
        sp500 = [
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'TSLA', 'META', 'UNH', 'JNJ',
            'JPM', 'V', 'PG', 'HD', 'CVX', 'MA', 'BAC', 'ABBV', 'PFE', 'AVGO',
            'KO', 'MRK', 'COST', 'PEP', 'TMO', 'WMT', 'ACN', 'MCD', 'ABT', 'CRM',
            'NFLX', 'ADBE', 'LLY', 'CSCO', 'XOM', 'NKE', 'QCOM', 'TXN', 'DHR', 'VZ',
            'AMD', 'INTC', 'ORCL', 'COP', 'NEE', 'UPS', 'T', 'CMCSA', 'RTX', 'PM'
        ]
        
        # High-volatility growth stocks (Options-friendly)
        growth_stocks = [
            'PLTR', 'SNOW', 'COIN', 'RBLX', 'UBER', 'LYFT', 'ABNB', 'SOFI', 'HOOD',
            'RIVN', 'LCID', 'NIO', 'XPEV', 'LI', 'BABA', 'JD', 'PDD', 'DIDI',
            'ZM', 'DOCU', 'ROKU', 'TWLO', 'SHOP', 'SQ', 'PYPL', 'SNAP', 'SPOT',
            'DASH', 'CRWD', 'OKTA', 'ZS', 'NET', 'DDOG', 'MDB', 'ESTC', 'PLAN'
        ]
        
        # Biotech/Healthcare (High volatility)
        biotech = [
            'MRNA', 'BNTX', 'GILD', 'REGN', 'VRTX', 'BIIB', 'ILMN', 'INCY',
            'AMGN', 'CELG', 'ISRG', 'MDLZ', 'ZTS', 'IDXX', 'DXCM', 'EW'
        ]
        
        # Financial services (Rate sensitive)
        financials = [
            'GS', 'MS', 'WFC', 'C', 'BLK', 'SCHW', 'AXP', 'SPGI', 'ICE',
            'CME', 'COF', 'USB', 'TFC', 'PNC', 'BK', 'STT', 'NTRS'
        ]
        
        # Energy (Commodity plays)
        energy = [
            'SLB', 'EOG', 'PXD', 'KMI', 'OKE', 'WMB', 'MPC', 'VLO', 'PSX',
            'HES', 'DVN', 'FANG', 'APA', 'HAL', 'BKR'
        ]
        
        # REITs (Dividend plays)
        reits = [
            'AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'WELL', 'DLR', 'SBAC',
            'EXR', 'AVB', 'EQR', 'MAA', 'UDR', 'CPT', 'ESS'
        ]
        
        # Retail/Consumer (Earnings sensitive)
        retail = [
            'AMZN', 'TGT', 'LOW', 'SBUX', 'DIS', 'BKNG', 'NKE', 'TJX',
            'ROST', 'ULTA', 'LULU', 'GPS', 'M', 'JWN', 'BBY', 'GME'
        ]
        
        # Semiconductor/Tech (High beta)
        semiconductors = [
            'TSM', 'ASML', 'MU', 'AMAT', 'LRCX', 'KLAC', 'MCHP', 'ADI',
            'MRVL', 'SWKS', 'QRVO', 'MPWR', 'TER', 'ENTG', 'RMBS'
        ]
        
        # Airlines/Travel (Recovery plays)
        travel = [
            'AAL', 'DAL', 'UAL', 'LUV', 'ALK', 'JBLU', 'SAVE',
            'CCL', 'RCL', 'NCLH', 'MAR', 'HLT', 'WYNN', 'LVS', 'MGM'
        ]
        
        # Popular meme/retail stocks
        meme_stocks = [
            'GME', 'AMC', 'BB', 'WISH', 'CLOV', 'SPCE', 'TLRY', 'SNDL',
            'MVIS', 'UWMC', 'RKT', 'PLBY', 'BBBY', 'EXPR', 'KOSS'
        ]
        
        return {
            'large_cap': sp500,
            'growth': growth_stocks,
            'biotech': biotech,
            'financials': financials,
            'energy': energy,
            'reits': reits,
            'retail': retail,
            'semiconductors': semiconductors,
            'travel': travel,
            'meme_stocks': meme_stocks
        }
    
    def get_all_symbols(self) -> List[str]:
        """Get flattened list of all symbols"""
        all_symbols = []
        for category, symbols in self.market_universe.items():
            all_symbols.extend(symbols)
        return list(set(all_symbols))  # Remove duplicates
    
    def analyze_single_symbol(self, symbol: str, sector: str) -> Optional[MarketOpportunity]:
        """Analyze single symbol for opportunities"""
        try:
            # Get comprehensive data
            stock_data = self.data_manager.get_stock_data(symbol)
            if not stock_data:
                return None
            
            enhanced_metrics = self.data_manager.calculate_enhanced_metrics(stock_data)
            if not enhanced_metrics or 'current_price' not in enhanced_metrics:
                return None
            
            # Calculate opportunity scores
            momentum_score = self._calculate_momentum_score(stock_data, enhanced_metrics)
            value_score = self._calculate_value_score(stock_data, enhanced_metrics)
            risk_score = self._calculate_risk_score(stock_data, enhanced_metrics)
            
            # Calculate RSI
            rsi = self._calculate_rsi(stock_data)
            
            # Determine opportunity type and confidence
            opportunity_type, confidence, target_price, reasoning = self._classify_opportunity(
                symbol, enhanced_metrics, momentum_score, value_score, risk_score, rsi
            )
            
            if confidence < 50:  # Filter low-confidence opportunities (lowered threshold)
                return None
            
            # Determine market cap category
            market_cap = self._estimate_market_cap(enhanced_metrics['current_price'])
            
            return MarketOpportunity(
                symbol=symbol,
                sector=sector,
                market_cap=market_cap,
                current_price=enhanced_metrics['current_price'],
                price_change_1d=enhanced_metrics['price_change_1d'],
                volume_ratio=enhanced_metrics['volume_ratio'],
                volatility_30d=enhanced_metrics['volatility_30d'],
                rsi=rsi,
                momentum_score=momentum_score,
                value_score=value_score,
                risk_score=risk_score,
                news_sentiment=None,  # Will be filled by news pipeline
                opportunity_type=opportunity_type,
                confidence=confidence,
                target_price=target_price,
                reasoning=reasoning,
                data_source=stock_data.get('source', 'unknown')
            )
            
        except Exception as e:
            print(f"   ⚠️ Error analyzing {symbol}: {e}")
            return None
    
    def _calculate_momentum_score(self, stock_data: Dict, enhanced_metrics: Dict) -> float:
        """Calculate momentum score (0-100)"""
        df = stock_data['price_data']
        close_col = 'Close' if 'Close' in df.columns else 'close'
        
        score = 50  # Neutral start
        
        # Price vs moving averages
        if enhanced_metrics['price_vs_sma20'] > 5:
            score += 20
        elif enhanced_metrics['price_vs_sma20'] < -5:
            score -= 20
        
        if enhanced_metrics['price_vs_sma50'] > 10:
            score += 15
        elif enhanced_metrics['price_vs_sma50'] < -10:
            score -= 15
        
        # Volume confirmation
        if enhanced_metrics['volume_ratio'] > 1.5:
            score += 10
        elif enhanced_metrics['volume_ratio'] < 0.7:
            score -= 10
        
        # Price momentum
        if enhanced_metrics['price_change_1d'] > 3:
            score += 10
        elif enhanced_metrics['price_change_1d'] < -3:
            score -= 10
        
        return max(0, min(100, score))
    
    def _calculate_value_score(self, stock_data: Dict, enhanced_metrics: Dict) -> float:
        """Calculate value score (0-100)"""
        score = 50  # Neutral start
        
        # Oversold conditions
        if enhanced_metrics['price_vs_sma50'] < -20:
            score += 25
        elif enhanced_metrics['price_vs_sma50'] < -10:
            score += 15
        
        # Volatility (lower is better for value)
        if enhanced_metrics['volatility_30d'] < 20:
            score += 10
        elif enhanced_metrics['volatility_30d'] > 50:
            score -= 15
        
        # Volume interest
        if enhanced_metrics['volume_ratio'] > 1.2:
            score += 5
        
        return max(0, min(100, score))
    
    def _calculate_risk_score(self, stock_data: Dict, enhanced_metrics: Dict) -> float:
        """Calculate risk score (0-100, higher = riskier)"""
        df = stock_data['price_data']
        close_col = 'Close' if 'Close' in df.columns else 'close'
        
        risk_score = 0
        
        # Volatility risk
        vol = enhanced_metrics['volatility_30d']
        if vol > 60:
            risk_score += 40
        elif vol > 40:
            risk_score += 25
        elif vol > 25:
            risk_score += 10
        
        # Drawdown risk
        if len(df) >= 30:
            rolling_max = df[close_col].rolling(window=30).max()
            drawdown = ((df[close_col] - rolling_max) / rolling_max) * 100
            max_drawdown = drawdown.min()
            
            if max_drawdown < -30:
                risk_score += 30
            elif max_drawdown < -20:
                risk_score += 20
            elif max_drawdown < -10:
                risk_score += 10
        
        # Price stability
        if abs(enhanced_metrics['price_change_1d']) > 5:
            risk_score += 10
        
        return min(100, risk_score)
    
    def _calculate_rsi(self, stock_data: Dict) -> float:
        """Calculate RSI indicator"""
        df = stock_data['price_data']
        close_col = 'Close' if 'Close' in df.columns else 'close'
        
        try:
            delta = df[close_col].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1] if not rsi.empty else 50.0
        except:
            return 50.0
    
    def _classify_opportunity(self, symbol: str, enhanced_metrics: Dict, momentum_score: float, 
                            value_score: float, risk_score: float, rsi: float) -> Tuple[str, float, Optional[float], str]:
        """Classify opportunity type and calculate confidence"""
        
        current_price = enhanced_metrics['current_price']
        reasoning_parts = []
        
        # Breakout opportunity
        if (momentum_score > 70 and enhanced_metrics['volume_ratio'] > 1.5 and 
            enhanced_metrics['price_vs_sma20'] > 5):
            opportunity_type = "breakout"
            confidence = min(95, momentum_score)
            target_price = current_price * 1.15  # 15% upside
            reasoning_parts.append(f"Strong momentum ({momentum_score:.0f}/100)")
            reasoning_parts.append(f"High volume ({enhanced_metrics['volume_ratio']:.1f}x)")
            
        # Oversold value opportunity  
        elif rsi < 30 and value_score > 65 and risk_score < 60:
            opportunity_type = "oversold"
            confidence = min(90, value_score)
            target_price = current_price * 1.20  # 20% recovery potential
            reasoning_parts.append(f"Oversold RSI ({rsi:.1f})")
            reasoning_parts.append(f"Strong value signals ({value_score:.0f}/100)")
            
        # Momentum continuation
        elif momentum_score > 65 and rsi < 70 and risk_score < 50:
            opportunity_type = "momentum" 
            confidence = min(85, momentum_score)
            target_price = current_price * 1.10  # 10% continuation
            reasoning_parts.append(f"Momentum continuation ({momentum_score:.0f}/100)")
            reasoning_parts.append(f"Manageable risk ({risk_score:.0f}/100)")
            
        # Value play
        elif value_score > 70 and risk_score < 40:
            opportunity_type = "value"
            confidence = min(80, value_score)
            target_price = current_price * 1.12  # 12% value unlock
            reasoning_parts.append(f"Undervalued ({value_score:.0f}/100)")
            reasoning_parts.append(f"Low risk ({risk_score:.0f}/100)")
            
        else:
            # No clear opportunity
            return "none", 0, None, "No clear trading opportunity"
        
        # Add volatility context
        vol = enhanced_metrics['volatility_30d']
        if vol > 40:
            reasoning_parts.append(f"High vol ({vol:.0f}% - options premium)")
        elif vol < 20:
            reasoning_parts.append(f"Low vol ({vol:.0f}% - stable)")
        
        reasoning = "; ".join(reasoning_parts)
        return opportunity_type, confidence, target_price, reasoning
    
    def _estimate_market_cap(self, price: float) -> str:
        """Rough market cap estimation"""
        if price > 200:
            return "Large Cap"
        elif price > 50:
            return "Mid Cap" 
        elif price > 10:
            return "Small Cap"
        else:
            return "Micro Cap"
    
    def screen_market_parallel(self, max_workers: int = 10) -> List[MarketOpportunity]:
        """Screen entire market using parallel processing"""
        start_time = time.time()
        all_symbols = self.get_all_symbols()
        
        print(f"\n🚀 ENTERPRISE MARKET SCREENING")
        print(f"   📊 Symbols: {len(all_symbols)}")
        print(f"   🔥 Workers: {max_workers} parallel threads")
        print(f"   ⚡ API Power: 10,000/hour available")
        print("=" * 70)
        
        opportunities = []
        completed = 0
        
        # Create symbol-sector mapping
        symbol_sectors = {}
        for sector, symbols in self.market_universe.items():
            for symbol in symbols:
                symbol_sectors[symbol] = sector
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all analysis tasks
            future_to_symbol = {
                executor.submit(self.analyze_single_symbol, symbol, symbol_sectors.get(symbol, 'unknown')): symbol
                for symbol in all_symbols
            }
            
            # Process completed tasks
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                completed += 1
                
                try:
                    opportunity = future.result()
                    if opportunity and opportunity.confidence >= 60:
                        opportunities.append(opportunity)
                        print(f"✅ {symbol}: {opportunity.opportunity_type.upper()} ({opportunity.confidence:.0f}%)")
                    else:
                        print(f"   {symbol}: No opportunity")
                        
                except Exception as e:
                    print(f"❌ {symbol}: Error - {e}")
                
                # Progress update
                if completed % 25 == 0:
                    elapsed = time.time() - start_time
                    rate = completed / elapsed if elapsed > 0 else 0
                    remaining = len(all_symbols) - completed
                    eta = remaining / rate if rate > 0 else 0
                    print(f"📊 Progress: {completed}/{len(all_symbols)} ({completed/len(all_symbols)*100:.1f}%) | ETA: {eta/60:.1f}min")
        
        # Final statistics
        elapsed_time = time.time() - start_time
        self.screening_stats = {
            'symbols_screened': len(all_symbols),
            'opportunities_found': len(opportunities),
            'api_requests_used': self.data_manager.tiingo_requests_used,
            'processing_time': elapsed_time
        }
        
        print(f"\n🏆 SCREENING COMPLETE")
        print(f"   ⏱️ Time: {elapsed_time/60:.1f} minutes")
        print(f"   📊 Screened: {len(all_symbols)} symbols")
        print(f"   🎯 Opportunities: {len(opportunities)}")
        print(f"   🔥 API Requests: {self.data_manager.tiingo_requests_used}")
        print(f"   ⚡ Rate: {len(all_symbols)/(elapsed_time/60):.1f} symbols/min")
        
        return sorted(opportunities, key=lambda x: x.confidence, reverse=True)
    
    def get_top_opportunities(self, opportunities: List[MarketOpportunity], 
                            limit: int = 20, opportunity_type: str = None) -> List[MarketOpportunity]:
        """Get top opportunities with optional filtering"""
        filtered = opportunities
        
        if opportunity_type:
            filtered = [opp for opp in opportunities if opp.opportunity_type == opportunity_type]
        
        return sorted(filtered, key=lambda x: x.confidence, reverse=True)[:limit]
    
    def display_opportunities(self, opportunities: List[MarketOpportunity], limit: int = 20):
        """Display opportunities in a professional format"""
        top_opportunities = opportunities[:limit]
        
        print(f"\n🎯 TOP {len(top_opportunities)} MARKET OPPORTUNITIES")
        print("=" * 90)
        
        for i, opp in enumerate(top_opportunities, 1):
            emoji = "🚀" if opp.opportunity_type == "breakout" else "💎" if opp.opportunity_type == "oversold" else "📈" if opp.opportunity_type == "momentum" else "💰"
            source_emoji = "🥇" if opp.data_source == "tiingo" else "🥈"
            
            print(f"\n#{i} {emoji} {opp.symbol} - {opp.opportunity_type.upper()} ({opp.confidence:.0f}%)")
            print(f"   {source_emoji} Price: ${opp.current_price:.2f} ({opp.price_change_1d:+.1f}%) | Sector: {opp.sector}")
            if opp.target_price:
                upside = ((opp.target_price - opp.current_price) / opp.current_price) * 100
                print(f"   🎯 Target: ${opp.target_price:.2f} (+{upside:.1f}% upside)")
            print(f"   📊 Vol: {opp.volatility_30d:.0f}% | RSI: {opp.rsi:.0f} | Risk: {opp.risk_score:.0f}/100")
            print(f"   🔥 Volume: {opp.volume_ratio:.1f}x | Cap: {opp.market_cap}")
            print(f"   💭 {opp.reasoning}")
        
        # Summary by opportunity type
        type_counts = {}
        for opp in opportunities:
            type_counts[opp.opportunity_type] = type_counts.get(opp.opportunity_type, 0) + 1
        
        print(f"\n📊 OPPORTUNITY BREAKDOWN:")
        for opp_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   {opp_type.upper()}: {count} opportunities")
    
    def save_opportunities(self, opportunities: List[MarketOpportunity], filename: str = None):
        """Save opportunities to JSON and CSV"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"enterprise_screening_{timestamp}"
        
        # Ensure data directory exists
        os.makedirs("data/enterprise_screening", exist_ok=True)
        
        # Save as JSON
        json_file = f"data/enterprise_screening/{filename}.json"
        with open(json_file, 'w') as f:
            json.dump({
                'screening_stats': self.screening_stats,
                'opportunities': [asdict(opp) for opp in opportunities],
                'timestamp': datetime.now().isoformat()
            }, f, indent=2, default=str)
        
        # Save as CSV for easy analysis
        csv_file = f"data/enterprise_screening/{filename}.csv"
        df = pd.DataFrame([asdict(opp) for opp in opportunities])
        df.to_csv(csv_file, index=False)
        
        print(f"\n💾 Results saved:")
        print(f"   📋 JSON: {json_file}")
        print(f"   📊 CSV: {csv_file}")

def main():
    """Run enterprise market screening"""
    screener = EnterpriseMarketScreener()
    
    print("\n🚀 ENTERPRISE MARKET SCREENING")
    print("Unleashing 10,000/hour API power!")
    print("=" * 70)
    
    # Screen the entire market
    opportunities = screener.screen_market_parallel(max_workers=15)
    
    # Display top opportunities
    screener.display_opportunities(opportunities, limit=25)
    
    # Save results
    screener.save_opportunities(opportunities)
    
    # Show different opportunity types
    for opp_type in ["breakout", "oversold", "momentum", "value"]:
        type_opportunities = screener.get_top_opportunities(opportunities, limit=5, opportunity_type=opp_type)
        if type_opportunities:
            print(f"\n🎯 TOP 5 {opp_type.upper()} OPPORTUNITIES:")
            for i, opp in enumerate(type_opportunities, 1):
                print(f"   {i}. {opp.symbol}: {opp.confidence:.0f}% confidence, ${opp.current_price:.2f}")

if __name__ == "__main__":
    main()