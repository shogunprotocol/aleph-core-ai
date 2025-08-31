#!/usr/bin/env python3
"""
Test script for Market Intelligence Engine
Run this to test real-time news, sentiment, and Polymarket data
"""

import asyncio
import json
import logging
from app.market_intelligence import MarketIntelligenceEngine, get_market_intelligence

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_market_intelligence():
    """Test the full market intelligence system"""
    
    print("🚀 Testing Shogun Core AI Market Intelligence Engine")
    print("=" * 60)
    
    try:
        # Test full intelligence gathering
        logger.info("Gathering comprehensive market intelligence...")
        intelligence = await get_market_intelligence()
        
        # Display results
        print(f"\n📊 MARKET INTELLIGENCE REPORT")
        print(f"Generated: {intelligence['timestamp']}")
        
        print(f"\n📰 NEWS ANALYSIS:")
        news = intelligence['news_analysis']
        print(f"  Articles analyzed: {news['total_articles']}")
        print(f"  Overall sentiment: {news['overall_sentiment']}")
        print(f"  Sentiment score: {news['sentiment_score']:.3f}")
        
        print(f"\n🗞️  RECENT HEADLINES:")
        for i, headline in enumerate(news['recent_headlines'][:5], 1):
            sentiment_emoji = "📈" if headline['sentiment'] > 0.1 else "📉" if headline['sentiment'] < -0.1 else "➡️"
            print(f"  {i}. {sentiment_emoji} {headline['title'][:80]}...")
            print(f"     Source: {headline['source']} | Sentiment: {headline['sentiment']:.2f}")
        
        print(f"\n🎯 PREDICTION MARKETS:")
        predictions = intelligence['prediction_markets']
        print(f"  Market confidence: {predictions['market_confidence']}")
        
        for i, pred in enumerate(predictions['bitcoin_predictions'][:3], 1):
            print(f"  {i}. {pred['question'][:60]}...")
            print(f"     Odds: {pred['odds']:.1%} | Volume: ${pred['volume_24h']:,.0f}")
        
        print(f"\n🧠 KEY INSIGHTS:")
        for insight in intelligence['key_insights']:
            print(f"  • {insight}")
        
        print(f"\n⚠️  RISK FACTORS:")
        for risk in intelligence['risk_factors']:
            print(f"  • {risk}")
        
        print(f"\n📈 TRADING SIGNALS:")
        signals = intelligence['trading_signals']
        print(f"  Short-term: {signals['short_term']}")
        print(f"  Medium-term: {signals['medium_term']}")
        print(f"  Confidence: {signals['confidence']}")
        
        print(f"\n✅ Market Intelligence Engine working successfully!")
        
        return intelligence
        
    except Exception as e:
        logger.error(f"Market intelligence test failed: {e}")
        print(f"\n❌ Test failed: {e}")
        return None

async def test_individual_components():
    """Test individual components of the market intelligence system"""
    
    print("\n🔧 TESTING INDIVIDUAL COMPONENTS")
    print("=" * 40)
    
    engine = MarketIntelligenceEngine()
    
    # Test news aggregation
    print("\n1. Testing News Aggregation...")
    try:
        news_items = await engine.news_aggregator.fetch_all_news(max_articles_per_feed=5)
        print(f"   ✅ Fetched {len(news_items)} news articles")
        
        if news_items:
            latest = news_items[0]
            print(f"   Latest: {latest.title[:60]}... (Sentiment: {latest.sentiment_score:.2f})")
    except Exception as e:
        print(f"   ❌ News aggregation failed: {e}")
    
    # Test Polymarket
    print("\n2. Testing Polymarket API...")
    try:
        predictions = await engine.polymarket.get_bitcoin_predictions()
        print(f"   ✅ Fetched {len(predictions)} prediction markets")
        
        if predictions:
            top_pred = predictions[0]
            print(f"   Top market: {top_pred.question[:60]}... (Odds: {top_pred.current_odds:.1%})")
    except Exception as e:
        print(f"   ❌ Polymarket failed: {e}")

if __name__ == "__main__":
    print("🤖 Shogun Core AI - Market Intelligence Test")
    print("Testing real-time news, sentiment, and prediction markets...")
    
    # Run the full test
    result = asyncio.run(test_market_intelligence())
    
    # Test individual components if needed
    if result:
        print("\n" + "=" * 60)
        asyncio.run(test_individual_components())
    
    print(f"\n🎯 Test completed!")