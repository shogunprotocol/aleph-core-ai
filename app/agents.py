from crewai import Agent, Crew
from yaml import safe_load
import numpy as np
from typing import Dict, List, Any
from .tools import DefiLlamaTool, CryptoNewsTool, VaultTxTool, VaultStateTool, load_config
from .db import AllocationSnapshot
from .arbitrage import get_private_vault_analytics, get_private_pool_opportunities
from .iwbtc_vault import perform_ai_rebalance
from .market_intelligence import get_market_intelligence, get_sentiment_score
import json
from web3 import Web3

with open("config/pools.yaml") as f:
    CFG = safe_load(f)
    
# Load Lisk/Zama config
with open("config/lisk_zama.yaml") as f:
    LISK_ZAMA_CFG = safe_load(f)

class ApyScoutAgent(Agent):
    """Agent responsible for gathering APY data from DeFi protocols"""
    
    def __init__(self):
        super().__init__(
            role="APY Data Scout",
            goal="Gather accurate APY data from DeFi protocols to inform rebalancing decisions",
            backstory="""You are an expert DeFi analyst specializing in yield farming opportunities. 
            You have deep knowledge of various lending protocols and their risk profiles.""",
            verbose=True,
            allow_delegation=False,
            tools=[DefiLlamaTool()]
        )
    
    def scout_apy_data(self) -> Dict[str, Any]:
        """Scout APY data for configured strategies"""
        apy_data = {}
        
        # Get private vault analytics
        private_data = get_private_vault_analytics()
        
        # Add Lisk/Zama specific strategies
        apy_data["private_vault"] = private_data["apy"]
        apy_data["private_fund_movement"] = 0.15  # 15% APY from private operations
        apy_data["encrypted_yield"] = 0.085  # 8.5% from encrypted yield farming
        
        # Original strategies
        for strategy in CFG["strategies"]:
            strategy_id = strategy["id"]
            if strategy_id not in apy_data:
                apy_data[strategy_id] = np.random.uniform(0.03, 0.08)
        
        return apy_data

class NewsSentimentAgent(Agent):
    """Agent responsible for analyzing crypto news sentiment"""
    
    def __init__(self):
        super().__init__(
            role="Crypto News Analyst",
            goal="Analyze crypto news sentiment to assess market conditions",
            backstory="""You are a seasoned crypto market analyst with expertise in sentiment analysis. 
            You understand how news events impact DeFi protocols and market dynamics.""",
            verbose=True,
            allow_delegation=False,
            tools=[CryptoNewsTool()]
        )
    
    def analyze_sentiment(self, tokens: List[str] = None) -> Dict[str, Any]:
        """Analyze sentiment for specified tokens using real market intelligence"""
        try:
            import asyncio
            # Get real market intelligence
            intelligence = asyncio.run(get_market_intelligence())
            
            return {
                'overall_sentiment': intelligence['news_analysis']['overall_sentiment'],
                'sentiment_score': intelligence['news_analysis']['sentiment_score'],
                'total_articles': intelligence['news_analysis']['total_articles'],
                'recent_headlines': intelligence['news_analysis']['recent_headlines'][:5],
                'key_insights': intelligence['key_insights'],
                'trading_signals': intelligence['trading_signals']
            }
        except Exception as e:
            # Fallback to mock data
            return {
                'overall_sentiment': 'neutral',
                'sentiment_score': 0.1,
                'total_articles': 0,
                'error': str(e)
            }

class PortfolioOptimizerAgent(Agent):
    """Agent responsible for portfolio optimization decisions"""
    
    def __init__(self):
        super().__init__(
            role="Portfolio Optimizer",
            goal="Optimize portfolio allocations based on APY data and sentiment",
            backstory="""You are a quantitative portfolio manager specializing in DeFi yield optimization. 
            You use mathematical models to maximize risk-adjusted returns.""",
            verbose=True,
            allow_delegation=False
        )
    
    def run(self, apy_data: dict, sentiment: float, current_alloc: dict):
        """
        Return dict {strategy_id: new_weight}. Very dumb greedy for now.
        """
        deltas = {sid: apy_data[sid] - sum(
            apy_data[s]*current_alloc.get(s, 0) for s in apy_data)
                  for sid in apy_data}
        # sort by delta desc, cap by max_allocation
        target = current_alloc.copy()
        for sid, _ in sorted(deltas.items(), key=lambda x: x[1], reverse=True):
            cap = next(s['max_allocation'] for s in CFG['strategies'] if s['id']==sid)
            target[sid] = cap
        # normalize to 1.0
        total = sum(target.values()) or 1
        target = {k: round(v/total, 4) for k,v in target.items()}
        AllocationSnapshot.save(target)
        return {"action": "REBALANCE", "target_allocs": target}

class VaultManagerAgent(Agent):
    """Agent responsible for executing vault transactions"""
    
    def __init__(self):
        super().__init__(
            role="Vault Transaction Manager",
            goal="Execute vault rebalancing transactions safely and efficiently",
            backstory="""You are a blockchain transaction specialist with deep knowledge of DeFi vaults. 
            You ensure transactions are executed with proper gas optimization and security checks.""",
            verbose=True,
            allow_delegation=False,
            tools=[VaultTxTool()]
        )
    
    def run(self, allocs: dict):
        """Execute vault rebalance transaction"""
        # TODO: Implement actual vault contract interaction
        # This would typically involve:
        # 1. Loading vault ABI
        # 2. Creating contract instance
        # 3. Building transaction
        # 4. Signing and sending
        
        # Mock transaction for development
        mock_tx_hash = "0x" + "0" * 64
        
        return {"tx_hash": mock_tx_hash}

class PrivatePoolAgent(Agent):
    """Agent responsible for managing private pool operations on Lisk/Zama"""
    
    def __init__(self):
        super().__init__(
            role="Private Pool Manager",
            goal="Manage private fund movement and encrypted transactions",
            backstory="""You are a specialized private pool manager focusing on Lisk DEXes and Zama FHE pools. 
            You execute encrypted fund movements and optimize private liquidity operations.""",
            verbose=True,
            allow_delegation=False
        )
    
    def find_opportunities(self) -> Dict[str, Any]:
        """Find current private pool opportunities"""
        opportunities = get_private_pool_opportunities()
        
        # Filter for profitable opportunities
        profitable = [
            opp for opp in opportunities 
            if opp.get("profit_pct", 0) > 0.5 or opp.get("premium_pct", 0) > 0.3
        ]
        
        return {
            "total_opportunities": len(opportunities),
            "profitable": len(profitable),
            "best_opportunity": profitable[0] if profitable else None,
            "opportunities": profitable[:3]  # Top 3 opportunities
        }

def create_rebalance_crew():
    """Create the rebalance crew with all agents"""
    apy_agent = ApyScoutAgent()
    news_agent = NewsSentimentAgent()
    optimizer_agent = PortfolioOptimizerAgent()
    vault_agent = VaultManagerAgent()
    private_pool_agent = PrivatePoolAgent()  # New Lisk/Zama private pool agent
    
    crew = Crew(
        agents=[apy_agent, news_agent, optimizer_agent, vault_agent, private_pool_agent],
        verbose=True
    )
    
    return crew 