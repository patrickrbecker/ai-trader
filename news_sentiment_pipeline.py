#!/usr/bin/env python3
"""
News Sentiment Pipeline - AI-powered market mood analysis
Premium Tiingo news API + sentiment analysis for trading signals
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
import os
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from smart_data_manager import SmartDataManager

@dataclass
class NewsArticle:
    title: str
    description: str
    url: str
    published_date: str
    source: str
    tickers: List[str]
    tags: List[str]
    sentiment_score: float  # -1 (very negative) to +1 (very positive)
    sentiment_magnitude: float  # 0 to 1 (how strong the sentiment is)
    relevance_score: float  # 0 to 1 (how relevant to trading)
    key_phrases: List[str]

@dataclass
class TickerSentiment:
    symbol: str
    overall_sentiment: float  # -1 to +1
    sentiment_strength: float  # 0 to 1
    article_count: int
    positive_articles: int
    negative_articles: int
    neutral_articles: int
    key_themes: List[str]
    recent_news: List[NewsArticle]
    sentiment_trend: str  # "improving", "declining", "stable"
    trading_signal: str  # "bullish", "bearish", "neutral"
    confidence: float  # 0 to 100

class NewsSentimentPipeline:
    def __init__(self):
        """Initialize news sentiment pipeline with premium Tiingo access"""
        self.data_manager = SmartDataManager()
        
        # Sentiment keywords for basic analysis (can be enhanced with ML models)
        self.positive_keywords = {
            'strong': 0.8, 'growth': 0.7, 'profit': 0.8, 'beat': 0.9, 'surge': 0.9,
            'rally': 0.8, 'breakthrough': 0.9, 'success': 0.7, 'expand': 0.6, 'gain': 0.7,
            'rise': 0.6, 'bullish': 0.9, 'optimistic': 0.7, 'upgrade': 0.8, 'outperform': 0.8,
            'record': 0.8, 'milestone': 0.7, 'partnership': 0.6, 'deal': 0.6, 'agreement': 0.5,
            'innovation': 0.7, 'breakthrough': 0.9, 'positive': 0.6, 'exceed': 0.8, 'robust': 0.7
        }
        
        self.negative_keywords = {
            'decline': -0.7, 'fall': -0.6, 'drop': -0.7, 'crash': -0.9, 'plunge': -0.9,
            'loss': -0.7, 'miss': -0.8, 'warning': -0.8, 'concern': -0.6, 'risk': -0.5,
            'bearish': -0.9, 'pessimistic': -0.7, 'downgrade': -0.8, 'underperform': -0.8,
            'crisis': -0.9, 'problem': -0.6, 'issue': -0.5, 'challenge': -0.5, 'struggle': -0.7,
            'bankruptcy': -1.0, 'lawsuit': -0.7, 'investigation': -0.7, 'scandal': -0.8,
            'disappointing': -0.7, 'weak': -0.6, 'poor': -0.7, 'negative': -0.6
        }
        
        # High-impact phrases that multiply sentiment
        self.impact_multipliers = {
            'earnings beat': 1.5, 'earnings miss': 1.5, 'guidance raised': 1.4, 'guidance lowered': 1.4,
            'merger': 1.3, 'acquisition': 1.3, 'fda approval': 1.6, 'fda rejection': 1.6,
            'product launch': 1.2, 'product recall': 1.4, 'ceo resigns': 1.3, 'new ceo': 1.1,
            'analyst upgrade': 1.2, 'analyst downgrade': 1.2, 'stock split': 1.1, 'dividend increase': 1.1
        }
        
        print("📰 NEWS SENTIMENT PIPELINE INITIALIZED")
        print("   🚀 Premium Tiingo News API access")
        print("   🧠 AI-powered sentiment analysis")
        print("   📊 Multi-symbol batch processing")
        print("   🎯 Trading signal generation")
    
    def get_news_for_symbols(self, symbols: List[str], days_back: int = 7, 
                           limit_per_symbol: int = 20) -> Dict[str, List[NewsArticle]]:
        """Get news articles for multiple symbols"""
        print(f"\n📰 FETCHING NEWS FOR {len(symbols)} SYMBOLS")
        print(f"   📅 Period: Last {days_back} days")
        print(f"   📊 Limit: {limit_per_symbol} articles per symbol")
        print("=" * 60)
        
        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        symbol_news = {}
        
        for i, symbol in enumerate(symbols, 1):
            print(f"[{i}/{len(symbols)}] Fetching news for {symbol}...")
            
            try:
                # Get news from Tiingo (premium feature)
                news_data = self.data_manager.tiingo_provider.get_market_news(
                    symbols=[symbol], 
                    limit=limit_per_symbol,
                    start_date=start_date
                )
                
                if news_data:
                    processed_articles = []
                    for article_data in news_data:
                        article = self._process_article(article_data, symbol)
                        if article:
                            processed_articles.append(article)
                    
                    symbol_news[symbol] = processed_articles
                    print(f"   ✅ {len(processed_articles)} articles processed")
                else:
                    print(f"   ❌ No news data available")
                    symbol_news[symbol] = []
                    
            except Exception as e:
                print(f"   ⚠️ Error fetching news for {symbol}: {e}")
                symbol_news[symbol] = []
            
            # Rate limiting for API calls
            time.sleep(0.1)
        
        total_articles = sum(len(articles) for articles in symbol_news.values())
        print(f"\n📊 NEWS COLLECTION COMPLETE")
        print(f"   📰 Total articles: {total_articles}")
        print(f"   📈 Symbols with news: {len([s for s, a in symbol_news.items() if a])}")
        
        return symbol_news
    
    def _process_article(self, article_data: Dict, primary_symbol: str) -> Optional[NewsArticle]:
        """Process raw article data into structured NewsArticle"""
        try:
            title = article_data.get('title', '')
            description = article_data.get('description', '')
            
            if not title and not description:
                return None
            
            # Calculate sentiment
            sentiment_score, sentiment_magnitude = self._analyze_sentiment(title, description)
            
            # Calculate relevance to trading
            relevance_score = self._calculate_relevance(title, description, article_data.get('tags', []))
            
            # Extract key phrases
            key_phrases = self._extract_key_phrases(title, description)
            
            return NewsArticle(
                title=title,
                description=description,
                url=article_data.get('url', ''),
                published_date=article_data.get('publishedDate', ''),
                source=article_data.get('source', ''),
                tickers=article_data.get('tickers', [primary_symbol]),
                tags=article_data.get('tags', []),
                sentiment_score=sentiment_score,
                sentiment_magnitude=sentiment_magnitude,
                relevance_score=relevance_score,
                key_phrases=key_phrases
            )
            
        except Exception as e:
            print(f"   ⚠️ Error processing article: {e}")
            return None
    
    def _analyze_sentiment(self, title: str, description: str) -> Tuple[float, float]:
        """Analyze sentiment of article text"""
        text = f"{title} {description}".lower()
        
        # Count positive and negative keywords
        positive_score = 0
        negative_score = 0
        word_count = 0
        
        words = re.findall(r'\b\w+\b', text)
        word_count = len(words)
        
        for word in words:
            if word in self.positive_keywords:
                positive_score += self.positive_keywords[word]
            elif word in self.negative_keywords:
                negative_score += abs(self.negative_keywords[word])
        
        # Check for high-impact phrases
        impact_multiplier = 1.0
        for phrase, multiplier in self.impact_multipliers.items():
            if phrase in text:
                impact_multiplier = max(impact_multiplier, multiplier)
        
        # Calculate overall sentiment (-1 to +1)
        if word_count == 0:
            return 0.0, 0.0
        
        pos_ratio = positive_score / word_count
        neg_ratio = negative_score / word_count
        
        sentiment = (pos_ratio - neg_ratio) * impact_multiplier
        magnitude = (pos_ratio + neg_ratio) * impact_multiplier
        
        # Normalize to [-1, 1] and [0, 1]
        sentiment = max(-1.0, min(1.0, sentiment * 5))  # Scale factor
        magnitude = min(1.0, magnitude * 3)
        
        return sentiment, magnitude
    
    def _calculate_relevance(self, title: str, description: str, tags: List[str]) -> float:
        """Calculate how relevant article is to trading decisions"""
        text = f"{title} {description}".lower()
        relevance = 0.5  # Base relevance
        
        # High relevance keywords
        trading_keywords = [
            'earnings', 'revenue', 'profit', 'loss', 'guidance', 'forecast',
            'analyst', 'rating', 'upgrade', 'downgrade', 'target', 'price',
            'merger', 'acquisition', 'partnership', 'deal', 'contract',
            'fda', 'approval', 'clinical', 'trial', 'product', 'launch',
            'ceo', 'management', 'restructuring', 'layoffs', 'hiring',
            'dividend', 'split', 'buyback', 'debt', 'financing', 'ipo'
        ]
        
        for keyword in trading_keywords:
            if keyword in text:
                relevance += 0.1
        
        # Tag-based relevance
        relevant_tags = ['earnings', 'mergers', 'management', 'products', 'financial']
        for tag in tags:
            if any(relevant_tag in tag.lower() for relevant_tag in relevant_tags):
                relevance += 0.15
        
        return min(1.0, relevance)
    
    def _extract_key_phrases(self, title: str, description: str) -> List[str]:
        """Extract key phrases from article text"""
        text = f"{title} {description}".lower()
        phrases = []
        
        # Common trading-relevant phrases
        key_patterns = [
            r'earnings\s+beat', r'earnings\s+miss', r'guidance\s+raised', r'guidance\s+lowered',
            r'analyst\s+upgrade', r'analyst\s+downgrade', r'price\s+target', r'revenue\s+up',
            r'revenue\s+down', r'profit\s+up', r'profit\s+down', r'new\s+product',
            r'product\s+launch', r'fda\s+approval', r'merger\s+announced', r'acquisition',
            r'ceo\s+resigns?', r'new\s+ceo', r'dividend\s+increase', r'stock\s+split'
        ]
        
        for pattern in key_patterns:
            matches = re.findall(pattern, text)
            phrases.extend(matches)
        
        return list(set(phrases))[:5]  # Return top 5 unique phrases
    
    def calculate_ticker_sentiment(self, symbol: str, articles: List[NewsArticle]) -> TickerSentiment:
        """Calculate overall sentiment for a ticker from its articles"""
        if not articles:
            return TickerSentiment(
                symbol=symbol,
                overall_sentiment=0.0,
                sentiment_strength=0.0,
                article_count=0,
                positive_articles=0,
                negative_articles=0,
                neutral_articles=0,
                key_themes=[],
                recent_news=[],
                sentiment_trend="stable",
                trading_signal="neutral",
                confidence=0.0
            )
        
        # Filter for high-relevance articles
        relevant_articles = [a for a in articles if a.relevance_score > 0.6]
        if not relevant_articles:
            relevant_articles = articles  # Fall back to all articles
        
        # Calculate weighted sentiment (recent articles matter more)
        total_sentiment = 0
        total_weight = 0
        
        for i, article in enumerate(relevant_articles):
            # Recent articles get higher weight
            recency_weight = 1.0 - (i / len(relevant_articles)) * 0.5
            weight = article.sentiment_magnitude * article.relevance_score * recency_weight
            
            total_sentiment += article.sentiment_score * weight
            total_weight += weight
        
        overall_sentiment = total_sentiment / total_weight if total_weight > 0 else 0.0
        
        # Count article types
        positive_articles = sum(1 for a in articles if a.sentiment_score > 0.2)
        negative_articles = sum(1 for a in articles if a.sentiment_score < -0.2)
        neutral_articles = len(articles) - positive_articles - negative_articles
        
        # Calculate sentiment strength
        sentiment_strength = np.mean([a.sentiment_magnitude for a in articles])
        
        # Extract key themes
        all_phrases = []
        for article in articles:
            all_phrases.extend(article.key_phrases)
        key_themes = list(set(all_phrases))[:5]
        
        # Determine sentiment trend (simplified)
        if len(articles) >= 3:
            recent_sentiment = np.mean([a.sentiment_score for a in articles[:len(articles)//2]])
            older_sentiment = np.mean([a.sentiment_score for a in articles[len(articles)//2:]])
            
            if recent_sentiment > older_sentiment + 0.1:
                sentiment_trend = "improving"
            elif recent_sentiment < older_sentiment - 0.1:
                sentiment_trend = "declining"
            else:
                sentiment_trend = "stable"
        else:
            sentiment_trend = "stable"
        
        # Determine trading signal
        if overall_sentiment > 0.3 and sentiment_strength > 0.5:
            trading_signal = "bullish"
            confidence = min(90, 50 + overall_sentiment * 40 + sentiment_strength * 20)
        elif overall_sentiment < -0.3 and sentiment_strength > 0.5:
            trading_signal = "bearish"
            confidence = min(90, 50 + abs(overall_sentiment) * 40 + sentiment_strength * 20)
        else:
            trading_signal = "neutral"
            confidence = 30 + sentiment_strength * 20
        
        return TickerSentiment(
            symbol=symbol,
            overall_sentiment=round(overall_sentiment, 3),
            sentiment_strength=round(sentiment_strength, 3),
            article_count=len(articles),
            positive_articles=positive_articles,
            negative_articles=negative_articles,
            neutral_articles=neutral_articles,
            key_themes=key_themes,
            recent_news=articles[:3],  # Top 3 most recent
            sentiment_trend=sentiment_trend,
            trading_signal=trading_signal,
            confidence=round(confidence, 1)
        )
    
    def analyze_market_sentiment(self, symbols: List[str], days_back: int = 7) -> Dict[str, TickerSentiment]:
        """Comprehensive sentiment analysis for multiple symbols"""
        print(f"\n🧠 MARKET SENTIMENT ANALYSIS")
        print(f"   📊 Symbols: {len(symbols)}")
        print(f"   📅 Period: {days_back} days")
        print("=" * 60)
        
        # Step 1: Collect news for all symbols
        symbol_news = self.get_news_for_symbols(symbols, days_back)
        
        # Step 2: Calculate sentiment for each symbol
        sentiment_results = {}
        
        for symbol, articles in symbol_news.items():
            sentiment = self.calculate_ticker_sentiment(symbol, articles)
            sentiment_results[symbol] = sentiment
            
            if articles:
                signal_emoji = "🟢" if sentiment.trading_signal == "bullish" else "🔴" if sentiment.trading_signal == "bearish" else "🟡"
                trend_emoji = "📈" if sentiment.sentiment_trend == "improving" else "📉" if sentiment.sentiment_trend == "declining" else "➡️"
                
                print(f"{signal_emoji} {symbol}: {sentiment.trading_signal.upper()} ({sentiment.confidence:.0f}%)")
                print(f"   {trend_emoji} Sentiment: {sentiment.overall_sentiment:+.2f} | Strength: {sentiment.sentiment_strength:.2f}")
                print(f"   📰 Articles: {sentiment.article_count} ({sentiment.positive_articles}+, {sentiment.negative_articles}-, {sentiment.neutral_articles}~)")
                if sentiment.key_themes:
                    print(f"   🏷️ Themes: {', '.join(sentiment.key_themes[:3])}")
        
        return sentiment_results
    
    def get_sentiment_leaders(self, sentiment_results: Dict[str, TickerSentiment], 
                            signal_type: str = "bullish", min_confidence: float = 60) -> List[TickerSentiment]:
        """Get top sentiment leaders by signal type"""
        filtered = [
            sentiment for sentiment in sentiment_results.values()
            if sentiment.trading_signal == signal_type and 
               sentiment.confidence >= min_confidence and
               sentiment.article_count >= 2
        ]
        
        return sorted(filtered, key=lambda x: x.confidence, reverse=True)
    
    def generate_sentiment_report(self, sentiment_results: Dict[str, TickerSentiment]):
        """Generate comprehensive sentiment report"""
        print(f"\n📊 MARKET SENTIMENT REPORT")
        print("=" * 70)
        
        # Overall market mood
        all_sentiments = [s.overall_sentiment for s in sentiment_results.values() if s.article_count > 0]
        if all_sentiments:
            market_sentiment = np.mean(all_sentiments)
            market_mood = "Bullish" if market_sentiment > 0.1 else "Bearish" if market_sentiment < -0.1 else "Neutral"
            print(f"📈 Overall Market Mood: {market_mood} ({market_sentiment:+.2f})")
        
        # Signal distribution
        signal_counts = {"bullish": 0, "bearish": 0, "neutral": 0}
        for sentiment in sentiment_results.values():
            if sentiment.article_count > 0:
                signal_counts[sentiment.trading_signal] += 1
        
        print(f"\n🎯 TRADING SIGNALS:")
        print(f"   🟢 Bullish: {signal_counts['bullish']} stocks")
        print(f"   🔴 Bearish: {signal_counts['bearish']} stocks")
        print(f"   🟡 Neutral: {signal_counts['neutral']} stocks")
        
        # Top bullish opportunities
        bullish_leaders = self.get_sentiment_leaders(sentiment_results, "bullish", 70)
        if bullish_leaders:
            print(f"\n🚀 TOP BULLISH OPPORTUNITIES:")
            for i, sentiment in enumerate(bullish_leaders[:5], 1):
                print(f"   {i}. {sentiment.symbol}: {sentiment.confidence:.0f}% confidence")
                print(f"      Sentiment: {sentiment.overall_sentiment:+.2f} | Trend: {sentiment.sentiment_trend}")
        
        # Top bearish opportunities (for puts)
        bearish_leaders = self.get_sentiment_leaders(sentiment_results, "bearish", 70)
        if bearish_leaders:
            print(f"\n🔻 TOP BEARISH OPPORTUNITIES (Put Options):")
            for i, sentiment in enumerate(bearish_leaders[:5], 1):
                print(f"   {i}. {sentiment.symbol}: {sentiment.confidence:.0f}% confidence")
                print(f"      Sentiment: {sentiment.overall_sentiment:+.2f} | Trend: {sentiment.sentiment_trend}")
    
    def save_sentiment_analysis(self, sentiment_results: Dict[str, TickerSentiment], 
                              filename: str = None):
        """Save sentiment analysis results"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"sentiment_analysis_{timestamp}"
        
        os.makedirs("data/sentiment_analysis", exist_ok=True)
        
        # Save as JSON
        json_file = f"data/sentiment_analysis/{filename}.json"
        with open(json_file, 'w') as f:
            json.dump({
                'analysis_timestamp': datetime.now().isoformat(),
                'sentiment_results': {k: asdict(v) for k, v in sentiment_results.items()}
            }, f, indent=2, default=str)
        
        # Save as CSV
        csv_file = f"data/sentiment_analysis/{filename}.csv"
        df_data = []
        for symbol, sentiment in sentiment_results.items():
            df_data.append({
                'symbol': symbol,
                'overall_sentiment': sentiment.overall_sentiment,
                'sentiment_strength': sentiment.sentiment_strength,
                'trading_signal': sentiment.trading_signal,
                'confidence': sentiment.confidence,
                'article_count': sentiment.article_count,
                'sentiment_trend': sentiment.sentiment_trend,
                'key_themes': '; '.join(sentiment.key_themes)
            })
        
        df = pd.DataFrame(df_data)
        df.to_csv(csv_file, index=False)
        
        print(f"\n💾 SENTIMENT ANALYSIS SAVED:")
        print(f"   📋 JSON: {json_file}")
        print(f"   📊 CSV: {csv_file}")

def main():
    """Test news sentiment pipeline"""
    pipeline = NewsSentimentPipeline()
    
    # Test with popular stocks
    test_symbols = ['AAPL', 'TSLA', 'NVDA', 'MSFT', 'GOOGL', 'META', 'AMZN', 'NFLX']
    
    print("\n🧪 TESTING NEWS SENTIMENT PIPELINE")
    print("=" * 50)
    
    # Run sentiment analysis
    sentiment_results = pipeline.analyze_market_sentiment(test_symbols, days_back=5)
    
    # Generate report
    pipeline.generate_sentiment_report(sentiment_results)
    
    # Save results
    pipeline.save_sentiment_analysis(sentiment_results)

if __name__ == "__main__":
    main()