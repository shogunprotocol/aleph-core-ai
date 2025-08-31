"""
IWBTC Vault Integration for CoreDAO
Manages the IWBTC vault with AI-driven rebalancing
"""

from web3 import Web3
from eth_account import Account
import json
import os
from typing import Dict, List, Optional
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# Simplified Vault ABI for IWBTC operations
VAULT_ABI = [
    {
        "inputs": [{"name": "amount", "type": "uint256"}],
        "name": "deposit",
        "outputs": [{"name": "shares", "type": "uint256"}],
        "type": "function"
    },
    {
        "inputs": [{"name": "shares", "type": "uint256"}],
        "name": "withdraw",
        "outputs": [{"name": "amount", "type": "uint256"}],
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalAssets",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "inputs": [{"name": "strategies", "type": "address[]"}, {"name": "allocations", "type": "uint256[]"}],
        "name": "rebalance",
        "outputs": [],
        "type": "function"
    }
]

# ERC20 ABI for token operations
ERC20_ABI = [
    {
        "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    }
]

class IWBTCVault:
    """IWBTC Vault manager for CoreDAO"""
    
    def __init__(self, w3: Web3, vault_address: str, private_key: Optional[str] = None):
        self.w3 = w3
        self.vault_address = Web3.to_checksum_address(vault_address)
        self.vault = w3.eth.contract(address=self.vault_address, abi=VAULT_ABI)
        
        if private_key:
            self.account = Account.from_key(private_key)
        else:
            self.account = None
            
    def get_vault_stats(self) -> Dict:
        """Get current vault statistics"""
        try:
            total_assets = self.vault.functions.totalAssets().call()
            total_supply = self.vault.functions.totalSupply().call()
            
            # Calculate price per share
            if total_supply > 0:
                price_per_share = total_assets / total_supply
            else:
                price_per_share = 1.0
            
            return {
                "total_assets": total_assets / 10**8,  # Convert to BTC
                "total_supply": total_supply / 10**8,
                "price_per_share": price_per_share,
                "vault_address": self.vault_address
            }
        except Exception as e:
            logger.error(f"Failed to get vault stats: {e}")
            return {}
    
    def deposit_btc(self, amount: float) -> Optional[str]:
        """Deposit wBTC into the vault and receive IWBTC"""
        if not self.account:
            logger.error("No account configured for deposits")
            return None
            
        try:
            amount_wei = int(amount * 10**8)  # BTC has 8 decimals
            
            # Build transaction
            tx = self.vault.functions.deposit(amount_wei).build_transaction({
                'from': self.account.address,
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
            })
            
            # Sign and send
            signed_tx = self.account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            logger.info(f"Deposit tx sent: {tx_hash.hex()}")
            return tx_hash.hex()
            
        except Exception as e:
            logger.error(f"Deposit failed: {e}")
            return None
    
    def withdraw_btc(self, shares: float) -> Optional[str]:
        """Withdraw IWBTC shares to receive wBTC"""
        if not self.account:
            logger.error("No account configured for withdrawals")
            return None
            
        try:
            shares_wei = int(shares * 10**8)
            
            tx = self.vault.functions.withdraw(shares_wei).build_transaction({
                'from': self.account.address,
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
            })
            
            signed_tx = self.account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            logger.info(f"Withdraw tx sent: {tx_hash.hex()}")
            return tx_hash.hex()
            
        except Exception as e:
            logger.error(f"Withdraw failed: {e}")
            return None
    
    def rebalance_strategies(self, allocations: Dict[str, float]) -> Optional[str]:
        """Rebalance vault strategies based on AI recommendations"""
        if not self.account:
            logger.error("No account configured for rebalancing")
            return None
            
        try:
            # Convert allocations to arrays
            strategies = list(allocations.keys())
            weights = [int(w * 10000) for w in allocations.values()]  # Convert to basis points
            
            tx = self.vault.functions.rebalance(strategies, weights).build_transaction({
                'from': self.account.address,
                'gas': 500000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
            })
            
            signed_tx = self.account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            logger.info(f"Rebalance tx sent: {tx_hash.hex()}")
            return tx_hash.hex()
            
        except Exception as e:
            logger.error(f"Rebalance failed: {e}")
            return None

class IWBTCStrategy:
    """Strategy manager for IWBTC vault"""
    
    def __init__(self, vault: IWBTCVault):
        self.vault = vault
        self.strategies = {}
        
    def analyze_market_conditions(self) -> Dict:
        """Analyze current market conditions for strategy selection"""
        # This would integrate with real market data
        # For now, return mock analysis
        return {
            "btc_trend": "bullish",
            "volatility": "medium",
            "liquidity": "high",
            "recommended_strategy": "yield_farming"
        }
    
    def calculate_optimal_allocation(self, market_conditions: Dict) -> Dict[str, float]:
        """Calculate optimal strategy allocations based on market conditions"""
        allocations = {}
        
        if market_conditions["volatility"] == "high":
            # High volatility - focus on arbitrage
            allocations = {
                "arbitrage": 0.40,
                "yield_farming": 0.30,
                "liquidity_provision": 0.30
            }
        elif market_conditions["btc_trend"] == "bullish":
            # Bullish market - maximize yield
            allocations = {
                "yield_farming": 0.50,
                "liquidity_provision": 0.35,
                "arbitrage": 0.15
            }
        else:
            # Default balanced allocation
            allocations = {
                "yield_farming": 0.40,
                "liquidity_provision": 0.40,
                "arbitrage": 0.20
            }
        
        return allocations
    
    def execute_rebalance(self) -> Dict:
        """Execute a full rebalance cycle"""
        try:
            # 1. Get vault stats
            stats = self.vault.get_vault_stats()
            logger.info(f"Current vault TVL: {stats.get('total_assets', 0)} BTC")
            
            # 2. Analyze market
            market = self.analyze_market_conditions()
            logger.info(f"Market conditions: {market}")
            
            # 3. Calculate allocations
            allocations = self.calculate_optimal_allocation(market)
            logger.info(f"Target allocations: {allocations}")
            
            # 4. Execute rebalance
            # tx_hash = self.vault.rebalance_strategies(allocations)
            
            return {
                "status": "success",
                "stats": stats,
                "market": market,
                "allocations": allocations,
                # "tx_hash": tx_hash
            }
            
        except Exception as e:
            logger.error(f"Rebalance execution failed: {e}")
            return {"status": "failed", "error": str(e)}

# Integration with existing agents
def get_iwbtc_vault_interface(w3: Web3) -> IWBTCVault:
    """Get IWBTC vault interface for agents"""
    vault_address = "0x0000000000000000000000000000000000000000"  # TODO: Update with actual address
    private_key = os.getenv("PRIVATE_KEY")
    return IWBTCVault(w3, vault_address, private_key)

def perform_ai_rebalance(w3: Web3) -> Dict:
    """Perform AI-driven rebalance for IWBTC vault"""
    vault = get_iwbtc_vault_interface(w3)
    strategy = IWBTCStrategy(vault)
    return strategy.execute_rebalance()