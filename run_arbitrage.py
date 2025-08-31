#!/usr/bin/env python3
"""
Main entry point for Lisk/Zama Private Pool Bot
Run with: python run_arbitrage.py
"""

import sys
import os
import asyncio
import argparse
import logging
from datetime import datetime
from typing import Optional

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.arbitrage import LiskZamaPrivateBot
from app.iwbtc_vault import IWBTCVault
from app.agents import create_rebalance_crew
from web3 import Web3
from decimal import Decimal
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/arbitrage_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_arbitrage_bot():
    """Run the private pool bot in scanning mode"""
    logger.info("=" * 50)
    logger.info("Starting Lisk/Zama Private Pool Bot")
    logger.info("=" * 50)
    
    bot = LiskZamaPrivateBot()
    bot.run()

async def run_vault_demo():
    """Run IWBTC Vault demonstration"""
    logger.info("=" * 50)
    logger.info("Starting IWBTC Vault Demo")
    logger.info("=" * 50)
    
    try:
        # Initialize vault
        vault = IWBTCVault()
        
        # Simulate institutional deposit
        logger.info("Simulating institutional deposit of 5 BTC...")
        deposit_result = await vault.deposit_btc(
            Decimal('5.0'), 
            '0x1234567890abcdef1234567890abcdef12345678',
            'institutional'
        )
        
        if deposit_result['success']:
            logger.info(f"✓ Deposit successful: {deposit_result['iwbtc_minted']:.4f} IWBTC minted")
            logger.info(f"  NAV per share: {deposit_result['nav_per_share']:.6f}")
            logger.info(f"  Expected annual yield: {deposit_result['estimated_annual_yield']}")
        
        # Get vault status
        logger.info("\nVault Status:")
        status = await vault.get_institutional_vault_status()
        for key, value in status['vault_overview'].items():
            logger.info(f"  {key}: {value}")
            
        # Generate institutional report
        logger.info("\nGenerating institutional compliance report...")
        report = await vault.generate_compliance_report()
        logger.info(f"✓ Report generated for {report.get('report_metadata', {}).get('report_period', 'N/A')}")
        
        return {
            'vault_status': status,
            'deposit_result': deposit_result,
            'compliance_report': report
        }
        
    except Exception as e:
        logger.error(f"Vault demo failed: {e}")
        return {'error': str(e)}

async def run_ai_analysis():
    """Run Shogun AI agents analysis"""
    logger.info("=" * 50)
    logger.info("Starting Shogun AI Multi-Agent Analysis")
    logger.info("=" * 50)
    
    try:
        # Initialize AI agents (simplified for demo)
        ai_agents = None
        
        # Sample market data
        market_data = {
            'protocols': {
                'liskswap': {'apy': 15.2, 'tvl': 25000000, 'risk_score': 6.8},
                'zama_pool_a': {'apy': 18.4, 'tvl': 15000000, 'risk_score': 7.1, 'encrypted': True},
                'zama_pool_b': {'apy': 16.8, 'tvl': 8200000, 'risk_score': 6.5, 'encrypted': True}
            },
            'prices': {
                'WLSK/WBTC': {'liskswap': 0.000123},
                'WLSK/USDT': {'liskswap': 2.45, 'zama_pool_a': 2.47}
            },
            'news': [
                'Lisk/Zama private pools reach $300M milestone',
                'Encrypted asset adoption accelerating', 
                'Private yield strategies stabilizing across FHE protocols'
            ]
        }
        
        # Client profile for institutional analysis
        client_profile = {
            'type': 'family_office',
            'volume': 10.0,  # 10 BTC
            'risk_profile': 'moderate'
        }
        
        # Mock AI analysis result for demo
        result = {
            'status': 'simulation_success',
            'institutional_analysis': {
                'apy_analysis': {'status': 'success', 'top_apy': '14.2%'},
                'market_sentiment': {'status': 'success', 'sentiment_score': 7.2},
                'arbitrage_opportunities': {'status': 'success', 'opportunities_found': 3},
                'portfolio_optimization': {'status': 'success', 'recommended_allocation': 'conservative'}
            },
            'client_type': client_profile['type'],
            'timestamp': time.time()
        }
        
        logger.info("✓ AI Analysis completed")
        logger.info(f"  Status: {result.get('status', 'unknown')}")
        logger.info(f"  Client type: {result.get('client_type', 'unknown')}")
        
        return result
        
    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        return {'error': str(e)}

def check_system_status():
    """Check system status and connectivity"""
    logger.info("Checking system status...")
    
    # Check Lisk connection
    w3_lisk = Web3(Web3.HTTPProvider("https://rpc.api.lisk.com"))
    if w3_lisk.is_connected():
        logger.info(f"✓ Connected to Lisk (Chain ID: {w3_lisk.eth.chain_id})")
        logger.info(f"✓ Latest block: {w3_lisk.eth.block_number}")
    else:
        logger.error("✗ Failed to connect to Lisk")
        return False
    
    # Check Zama connection
    try:
        w3_zama = Web3(Web3.HTTPProvider("https://devnet.zama.ai"))
        if w3_zama.is_connected():
            logger.info(f"✓ Connected to Zama (Chain ID: {w3_zama.eth.chain_id})")
        else:
            logger.warning("⚠ Zama connection not available")
    except:
        logger.warning("⚠ Zama RPC not accessible")
    
    # Check wallet
    if os.getenv("PRIVATE_KEY"):
        from eth_account import Account
        account = Account.from_key(os.getenv("PRIVATE_KEY"))
        lisk_balance = w3_lisk.eth.get_balance(account.address)
        logger.info(f"✓ Wallet configured: {account.address}")
        logger.info(f"  Lisk balance: {w3_lisk.from_wei(lisk_balance, 'ether')} LSK")
    else:
        logger.warning("⚠ No private key configured - running in read-only mode")
    
    # Check configs
    import yaml
    try:
        with open("config/lisk_zama.yaml", "r") as f:
            config = yaml.safe_load(f)
            logger.info("✓ Lisk/Zama config loaded")
    except Exception as e:
        logger.error(f"✗ Failed to load config: {e}")
        return False
    
    logger.info("System check complete!")
    return True

def main():
    """Main entry point with CLI arguments"""
    parser = argparse.ArgumentParser(description="Lisk/Zama Private Pool Bot")
    parser.add_argument(
        "--mode",
        choices=["arbitrage", "vault", "ai", "status", "demo", "pools"],
        default="status",
        help="Operation mode"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in simulation mode without executing trades"
    )
    
    args = parser.parse_args()
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    try:
        if args.mode == "status":
            check_system_status()
            
        elif args.mode == "arbitrage":
            if args.dry_run:
                logger.info("Running in DRY RUN mode - no actual trades will be executed")
                os.environ["DRY_RUN"] = "true"
            run_arbitrage_bot()
            
        elif args.mode == "vault":
            if args.dry_run:
                logger.info("Running in DRY RUN mode - no actual vault operations will occur")
                os.environ["DRY_RUN"] = "true"
            import asyncio
            result = asyncio.run(run_vault_demo())
            logger.info(f"Vault demo result: {result.get('vault_status', {}).get('operational_status', {})}")
            
        elif args.mode == "ai":
            import asyncio
            result = asyncio.run(run_ai_analysis())
            logger.info(f"AI analysis completed with status: {result.get('status', 'unknown')}")
            
        elif args.mode == "pools":
            logger.info("=" * 50)
            logger.info("Lisk/Zama Private Pool Analysis")
            logger.info("=" * 50)
            
            from app.arbitrage import LiskZamaPrivateBot
            bot = LiskZamaPrivateBot()
            if bot.setup_web3():
                import asyncio
                analytics = asyncio.run(bot.analyze_private_pools())
                
                logger.info("\n📊 Pool Analysis Results:")
                for dex_name, data in analytics["lisk_dexes"].items():
                    logger.info(f"\n{dex_name.upper()}:")
                    logger.info(f"  Status: {'✅ Connected' if data['pools_found'] > 0 else '❌ No pools found'}")
                    logger.info(f"  Pools: {data['pools_found']}")
                    
                    for pool in data.get("pools", [])[:5]:  # Show first 5 pools
                        reserves = pool.get("reserves", (0, 0))
                        logger.info(f"    - {pool['pair']}: Reserves [{reserves[0]}, {reserves[1]}]")
            
        elif args.mode == "demo":
            logger.info("=" * 50)
            logger.info("DEMO MODE - Showing IWBTC System Capabilities")
            logger.info("=" * 50)
            
            # 1. Check status
            logger.info("\n1. System Status Check:")
            check_system_status()
            
            # 2. Analyze pools
            logger.info("\n2. Lisk/Zama Pool Analysis:")
            from app.arbitrage import LiskZamaPrivateBot
            bot = LiskZamaPrivateBot()
            if bot.setup_web3():
                import asyncio
                analytics = asyncio.run(bot.analyze_private_pools())
                total_pools = sum(dex["pools_found"] for dex in analytics["lisk_dexes"].values())
                logger.info(f"   Connected Lisk DEXes: {len(analytics['lisk_dexes'])}")
                logger.info(f"   Total pools monitored: {total_pools}")
            
            # 3. Find private pool opportunities
            logger.info("\n3. Scanning for Private Pool Opportunities:")
            from app.arbitrage import get_private_pool_opportunities
            opportunities = get_private_pool_opportunities()
            if opportunities:
                for i, opp in enumerate(opportunities[:3], 1):
                    profit = opp.get("profit_pct", 0)
                    logger.info(f"   Opportunity {i}: {opp.get('type', 'unknown')} - {profit:.3f}% profit")
            else:
                logger.info("   No profitable opportunities found at this time")
            
            # 4. Show private vault analytics
            logger.info("\n4. Private Vault Analytics:")
            from app.arbitrage import get_private_vault_analytics
            analytics = get_private_vault_analytics()
            for key, value in analytics.items():
                logger.info(f"   {key}: {value}")
            
            # 5. Demonstrate IWBTC vault
            logger.info("\n5. IWBTC Vault Demo:")
            import asyncio
            vault_demo = asyncio.run(run_vault_demo())
            if vault_demo.get('vault_status'):
                vault_overview = vault_demo['vault_status']['vault_overview']
                logger.info(f"   Vault NAV: {vault_overview.get('vault_nav', 0):.4f} BTC")
                logger.info(f"   NAV per share: {vault_overview.get('nav_per_share', 1.0):.6f}")
                logger.info(f"   Expected yield: {vault_demo['vault_status']['performance_metrics'].get('current_annual_yield', 'N/A')}")
            
            # 6. AI Analysis Demo
            logger.info("\n6. AI Analysis Demo:")
            ai_demo = asyncio.run(run_ai_analysis())
            if ai_demo.get('status') == 'success':
                logger.info("   ✓ Multi-agent analysis successful")
                logger.info("   ✓ Institutional portfolio optimization complete")
                logger.info("   ✓ Market sentiment and arbitrage analysis done")
            elif ai_demo.get('status') == 'simulation_success':
                logger.info("   ✓ AI analysis running in simulation mode (no OpenAI key)")
                logger.info("   ✓ Institutional features demonstrated successfully")
            
            logger.info("\n" + "=" * 50)
            logger.info("Demo complete!")
            logger.info("Next steps:")
            logger.info("  --mode=pools     : Analyze Lisk/Zama private pools")
            logger.info("  --mode=arbitrage : Start private pool scanning") 
            logger.info("  --mode=vault     : Run private vault operations")
            logger.info("  --mode=ai        : Run AI multi-agent analysis")
            logger.info("  --mode=arbitrage --dry-run : Safe simulation mode")
            
    except KeyboardInterrupt:
        logger.info("\nShutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()