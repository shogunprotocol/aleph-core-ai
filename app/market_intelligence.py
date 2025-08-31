"""
Market Intelligence Engine - Real-time news, sentiment, and prediction markets
Integrates RSS feeds, Polymarket, and social media sentiment for financial analysis
"""

import asyncio
import aiohttp
import feedparser
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import re
from dataclasses import dataclass
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

@dataclass
class NewsItem:
    title: str
    content: str
    url: str
    published: datetime
    source: str
    sentiment_score: Optional[float] = None
    keywords: List[str] = None

@dataclass
class MarketPrediction:
    question: str
    current_odds: float
    volume_24h: float
    outcome_tokens: Dict[str, float]
    end_date: Optional[datetime]
    category: str

class CryptoNewsAggregator:
    """Aggregates real-time crypto news from multiple RSS feeds"""
    
    def __init__(self):
        self.rss_feeds = {
            'cointelegraph_bitcoin': 'https://cointelegraph.com/rss/tag/bitcoin',
            'cointelegraph_ethereum': 'https://cointelegraph.com/rss/tag/ethereum',
            'cointelegraph_regulation': 'https://cointelegraph.com/rss/tag/regulation',
            'cointelegraph_analysis': 'https://cointelegraph.com/rss/category/price-analysis',
            'cointelegraph_defi': 'https://cointelegraph.com/rss/tag/defi',
            'coindesk_bitcoin': 'https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml',
            'decrypt_feed': 'https://decrypt.co/feed',
        }
        
        self.sentiment_keywords = {
            'bullish': ['bullish', 'rally', 'surge', 'pump', 'moon', 'breakthrough', 'adoption', 'institutional'],
            'bearish': ['bearish', 'crash', 'dump', 'correction', 'decline', 'regulatory', 'ban', 'hack'],
            'neutral': ['analysis', 'technical', 'support', 'resistance', 'consolidation']
        }
    
    async def fetch_all_news(self, max_articles_per_feed: int = 10) -> List[NewsItem]:
        """Fetch news from all RSS feeds"""
        all_news = []
        
        for source_name, feed_url in self.rss_feeds.items():
            try:
                news_items = await self._fetch_rss_feed(feed_url, source_name, max_articles_per_feed)
                all_news.extend(news_items)
                logger.info(f"Fetched {len(news_items)} articles from {source_name}")
            except Exception as e:
                logger.error(f"Failed to fetch news from {source_name}: {e}")
        
        # Sort by publish date (most recent first)
        all_news.sort(key=lambda x: x.published, reverse=True)
        return all_news[:50]  # Return top 50 most recent articles
    
    async def _fetch_rss_feed(self, feed_url: str, source_name: str, max_articles: int) -> List[NewsItem]:
        """Fetch and parse RSS feed"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(feed_url) as response:
                    if response.status == 200:
                        xml_content = await response.text()
                        return self._parse_rss_content(xml_content, source_name, max_articles)
                    else:
                        logger.warning(f"HTTP {response.status} for {feed_url}")
                        return []
        except Exception as e:
            # Fallback to synchronous feedparser
            logger.info(f"Async fetch failed for {feed_url}, trying sync: {e}")
            return self._parse_rss_sync(feed_url, source_name, max_articles)
    
    def _parse_rss_sync(self, feed_url: str, source_name: str, max_articles: int) -> List[NewsItem]:
        """Synchronous RSS parsing fallback"""
        try:
            feed = feedparser.parse(feed_url)
            news_items = []
            
            for entry in feed.entries[:max_articles]:
                try:
                    # Parse published date
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'published'):
                        published = datetime.now()  # Fallback to now
                    else:
                        published = datetime.now()
                    
                    # Extract content
                    content = ""
                    if hasattr(entry, 'summary'):
                        content = entry.summary
                    elif hasattr(entry, 'description'):
                        content = entry.description
                    
                    # Clean HTML tags from content
                    content = re.sub('<[^<]+?>', '', content)
                    
                    news_item = NewsItem(
                        title=entry.title,
                        content=content,
                        url=entry.link,
                        published=published,
                        source=source_name,
                        keywords=self._extract_keywords(entry.title + " " + content)
                    )
                    
                    # Add sentiment analysis
                    news_item.sentiment_score = self._analyze_sentiment(news_item.title + " " + news_item.content)
                    news_items.append(news_item)
                    
                except Exception as e:
                    logger.debug(f"Failed to parse article from {source_name}: {e}")
                    continue
            
            return news_items
            
        except Exception as e:
            logger.error(f"Failed to parse RSS feed {feed_url}: {e}")
            return []
    
    def _parse_rss_content(self, xml_content: str, source_name: str, max_articles: int) -> List[NewsItem]:
        """Parse RSS XML content"""
        feed = feedparser.parse(xml_content)
        return self._parse_rss_sync("", source_name, max_articles)  # Use sync parser
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract crypto-related keywords"""
        text_lower = text.lower()
        keywords = []
        
        crypto_terms = ['bitcoin', 'btc', 'ethereum', 'eth', 'crypto', 'blockchain', 'defi', 'nft', 'web3', 'core', 'coredao']
        for term in crypto_terms:
            if term in text_lower:
                keywords.append(term)
        
        return keywords
    
    def _analyze_sentiment(self, text: str) -> float:
        """Simple sentiment analysis based on keywords"""
        text_lower = text.lower()
        
        bullish_score = 0
        bearish_score = 0
        
        for word in self.sentiment_keywords['bullish']:
            bullish_score += text_lower.count(word)
        
        for word in self.sentiment_keywords['bearish']:
            bearish_score += text_lower.count(word)
        
        if bullish_score == 0 and bearish_score == 0:
            return 0.0  # Neutral
        
        total_sentiment_words = bullish_score + bearish_score
        sentiment_score = (bullish_score - bearish_score) / total_sentiment_words
        
        # Normalize to -1 to 1 range
        return max(-1.0, min(1.0, sentiment_score))

class PolymarketAPI:
    """Polymarket prediction market data integration"""
    
    def __init__(self):
        self.base_url = "https://gamma-api.polymarket.com"
        self.clob_url = "https://clob.polymarket.com"
        self.session = None
    
    async def get_bitcoin_predictions(self) -> List[MarketPrediction]:
        """Get Bitcoin-related prediction markets"""
        try:
            async with aiohttp.ClientSession() as session:
                # Search for Bitcoin markets
                search_url = f"{self.base_url}/markets"
                params = {
                    'limit': 20,
                    'offset': 0,
                    'active': True,
                    'order': 'volume24hr',
                    'ascending': False
                }
                
                async with session.get(search_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        bitcoin_markets = []
                        
                        for market in data.get('data', []):
                            question = market.get('question', '').lower()
                            if 'bitcoin' in question or 'btc' in question:
                                prediction = MarketPrediction(
                                    question=market.get('question', ''),
                                    current_odds=float(market.get('outcomePrices', ['0.5', '0.5'])[0]),
                                    volume_24h=float(market.get('volume24hr', 0)),
                                    outcome_tokens={
                                        'yes': float(market.get('outcomePrices', ['0.5', '0.5'])[0]),
                                        'no': float(market.get('outcomePrices', ['0.5', '0.5'])[1])
                                    },
                                    end_date=None,  # Would parse from market data
                                    category='crypto'
                                )
                                bitcoin_markets.append(prediction)
                        
                        return bitcoin_markets[:10]  # Top 10 Bitcoin markets
                    else:
                        logger.warning(f"Polymarket API returned {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Failed to fetch Polymarket data: {e}")
            return self._get_mock_polymarket_data()
    
    def _get_mock_polymarket_data(self) -> List[MarketPrediction]:
        """Mock Polymarket data for development/fallback"""
        return [
            MarketPrediction(
                question="Bitcoin $1,000,000 by end of 2025?",
                current_odds=0.23,
                volume_24h=125000.0,
                outcome_tokens={'yes': 0.23, 'no': 0.77},
                end_date=datetime(2025, 12, 31),
                category='crypto'
            ),
            MarketPrediction(
                question="Bitcoin ETF approval affects CoreDAO adoption?",
                current_odds=0.67,
                volume_24h=45000.0,
                outcome_tokens={'yes': 0.67, 'no': 0.33},
                end_date=datetime(2024, 12, 31),
                category='crypto'
            ),
            MarketPrediction(
                question="Trump wins 2024 election (affects crypto regulation)?",
                current_odds=0.51,
                volume_24h=890000.0,
                outcome_tokens={'yes': 0.51, 'no': 0.49},
                end_date=datetime(2024, 11, 5),
                category='politics'
            )
        ]

class MarketIntelligenceEngine:
    """Main engine coordinating all market intelligence sources"""
    
    def __init__(self):
        self.news_aggregator = CryptoNewsAggregator()
        self.polymarket = PolymarketAPI()
        self.last_update = None
        self.cached_intelligence = None
        self.cache_duration = 300  # 5 minutes cache
    
    async def get_comprehensive_intelligence(self) -> Dict[str, Any]:
        """Get comprehensive market intelligence report"""
        
        # Check cache
        if (self.cached_intelligence and self.last_update and 
            (time.time() - self.last_update) < self.cache_duration):
            logger.info("Returning cached market intelligence")
            return self.cached_intelligence
        
        logger.info("Gathering fresh market intelligence...")
        
        try:
            # Gather data from all sources concurrently
            news_task = self.news_aggregator.fetch_all_news()
            predictions_task = self.polymarket.get_bitcoin_predictions()
            
            news_items, predictions = await asyncio.gather(news_task, predictions_task)
            
            # Analyze overall sentiment
            overall_sentiment = self._calculate_overall_sentiment(news_items)
            
            # Generate intelligence report
            intelligence = {
                'timestamp': datetime.now().isoformat(),
                'news_analysis': {
                    'total_articles': len(news_items),
                    'overall_sentiment': overall_sentiment,
                    'sentiment_score': sum(item.sentiment_score or 0 for item in news_items) / max(len(news_items), 1),
                    'recent_headlines': [
                        {
                            'title': item.title,
                            'source': item.source,
                            'sentiment': item.sentiment_score,
                            'published': item.published.isoformat(),
                            'url': item.url
                        }
                        for item in news_items[:10]  # Top 10 headlines
                    ]
                },
                'prediction_markets': {
                    'bitcoin_predictions': [
                        {
                            'question': pred.question,
                            'odds': pred.current_odds,
                            'volume_24h': pred.volume_24h,
                            'category': pred.category
                        }
                        for pred in predictions
                    ],
                    'market_confidence': self._analyze_prediction_confidence(predictions)
                },
                'key_insights': self._generate_key_insights(news_items, predictions),
                'risk_factors': self._identify_risk_factors(news_items, predictions),
                'trading_signals': self._generate_trading_signals(overall_sentiment, predictions)
            }
            
            # Cache results
            self.cached_intelligence = intelligence
            self.last_update = time.time()
            
            logger.info(f"Market intelligence updated with {len(news_items)} news items and {len(predictions)} predictions")
            return intelligence
            
        except Exception as e:
            logger.error(f"Failed to gather market intelligence: {e}")
            return self._get_fallback_intelligence()
    
    def _calculate_overall_sentiment(self, news_items: List[NewsItem]) -> str:
        """Calculate overall market sentiment from news"""
        if not news_items:
            return "neutral"
        
        avg_sentiment = sum(item.sentiment_score or 0 for item in news_items) / len(news_items)
        
        if avg_sentiment > 0.2:
            return "bullish"
        elif avg_sentiment < -0.2:
            return "bearish"
        else:
            return "neutral"
    
    def _analyze_prediction_confidence(self, predictions: List[MarketPrediction]) -> str:
        """Analyze confidence levels from prediction markets"""
        if not predictions:
            return "unknown"
        
        # Look for extreme odds as confidence indicators
        extreme_odds = [pred for pred in predictions if pred.current_odds > 0.8 or pred.current_odds < 0.2]
        
        if len(extreme_odds) > len(predictions) / 2:
            return "high_confidence"
        else:
            return "mixed_signals"
    
    def _generate_key_insights(self, news_items: List[NewsItem], predictions: List[MarketPrediction]) -> List[str]:
        """Generate key market insights"""
        insights = []
        
        # News-based insights
        if news_items:
            bitcoin_mentions = len([item for item in news_items if 'bitcoin' in item.title.lower()])
            if bitcoin_mentions > len(news_items) * 0.3:
                insights.append(f"High Bitcoin focus: {bitcoin_mentions}/{len(news_items)} articles mention Bitcoin")
        
        # Prediction-based insights
        if predictions:
            high_volume_predictions = [pred for pred in predictions if pred.volume_24h > 100000]
            if high_volume_predictions:
                insights.append(f"High trading volume in {len(high_volume_predictions)} prediction markets indicates strong market interest")
        
        return insights
    
    def _identify_risk_factors(self, news_items: List[NewsItem], predictions: List[MarketPrediction]) -> List[str]:
        """Identify potential risk factors"""
        risk_factors = []
        
        # Check for regulatory news
        regulatory_news = [item for item in news_items if 'regulat' in item.title.lower()]
        if len(regulatory_news) > 2:
            risk_factors.append(f"Increased regulatory attention: {len(regulatory_news)} recent articles")
        
        # Check for negative sentiment spikes
        negative_sentiment = [item for item in news_items if item.sentiment_score and item.sentiment_score < -0.5]
        if len(negative_sentiment) > len(news_items) * 0.3:
            risk_factors.append("Significant negative sentiment in recent news")
        
        return risk_factors
    
    def _generate_trading_signals(self, overall_sentiment: str, predictions: List[MarketPrediction]) -> Dict[str, str]:
        """Generate trading signals based on intelligence"""
        signals = {
            'short_term': 'neutral',
            'medium_term': 'neutral',
            'confidence': 'low'
        }
        
        # Simple signal generation based on sentiment and predictions
        if overall_sentiment == "bullish":
            signals['short_term'] = 'bullish'
            if predictions and any(pred.current_odds > 0.6 for pred in predictions):
                signals['medium_term'] = 'bullish'
                signals['confidence'] = 'medium'
        
        elif overall_sentiment == "bearish":
            signals['short_term'] = 'bearish'
            signals['confidence'] = 'medium'
        
        return signals
    
    def _get_fallback_intelligence(self) -> Dict[str, Any]:
        """Fallback intelligence data when APIs fail"""
        return {
            'timestamp': datetime.now().isoformat(),
            'news_analysis': {
                'total_articles': 0,
                'overall_sentiment': 'neutral',
                'sentiment_score': 0.0,
                'recent_headlines': []
            },
            'prediction_markets': {
                'bitcoin_predictions': [],
                'market_confidence': 'unknown'
            },
            'key_insights': ['Market intelligence temporarily unavailable'],
            'risk_factors': ['Data collection issues'],
            'trading_signals': {
                'short_term': 'neutral',
                'medium_term': 'neutral', 
                'confidence': 'low'
            }
        }

# Integration functions for the main system
async def get_market_intelligence() -> Dict[str, Any]:
    """Main function to get market intelligence for the IWBTC system"""
    engine = MarketIntelligenceEngine()
    return await engine.get_comprehensive_intelligence()

async def get_sentiment_score() -> float:
    """Get simple sentiment score for quick analysis"""
    try:
        intelligence = await get_market_intelligence()
        return intelligence['news_analysis']['sentiment_score']
    except Exception as e:
        logger.error(f"Failed to get sentiment score: {e}")
        return 0.0

if __name__ == "__main__":
    # Test the market intelligence engine
    async def test_engine():
        engine = MarketIntelligenceEngine()
        intelligence = await engine.get_comprehensive_intelligence()
        print(json.dumps(intelligence, indent=2))
    
    asyncio.run(test_engine())