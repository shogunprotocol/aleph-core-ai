"""
Lisk/Zama DEX Interface - Private pool interface for fund movement
Connects to Lisk DEXes and Zama private pools for encrypted transactions
"""

from web3 import Web3
from typing import Dict, List, Tuple, Optional
import json
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# Uniswap V2 style Router ABI (works with most forks)
ROUTER_ABI = [
    {
        "inputs": [
            {"name": "amountIn", "type": "uint256"},
            {"name": "path", "type": "address[]"}
        ],
        "name": "getAmountsOut",
        "outputs": [{"name": "amounts", "type": "uint256[]"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "factory",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# Factory ABI for getting pairs
FACTORY_ABI = [
    {
        "inputs": [
            {"name": "tokenA", "type": "address"},
            {"name": "tokenB", "type": "address"}
        ],
        "name": "getPair",
        "outputs": [{"name": "pair", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "allPairsLength",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "", "type": "uint256"}],
        "name": "allPairs",
        "outputs": [{"name": "pair", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# Pair ABI for getting reserves
PAIR_ABI = [
    {
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"name": "_reserve0", "type": "uint112"},
            {"name": "_reserve1", "type": "uint112"},
            {"name": "_blockTimestampLast", "type": "uint32"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "token0",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "token1",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# ERC20 ABI for token info
ERC20_ABI = [
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

class LiskDEX:
    """Interface for interacting with Lisk DEXes"""
    
    def __init__(self, w3: Web3, router_address: str, factory_address: str, name: str = "DEX"):
        self.w3 = w3
        self.name = name
        self.router_address = Web3.to_checksum_address(router_address)
        self.factory_address = Web3.to_checksum_address(factory_address)
        
        # Initialize contracts
        self.router = w3.eth.contract(address=self.router_address, abi=ROUTER_ABI)
        self.factory = w3.eth.contract(address=self.factory_address, abi=FACTORY_ABI)
        
        # Cache for token decimals
        self.decimals_cache = {}
        
    def get_pair_address(self, token0: str, token1: str) -> Optional[str]:
        """Get the pair address for two tokens"""
        try:
            token0 = Web3.to_checksum_address(token0)
            token1 = Web3.to_checksum_address(token1)
            pair_address = self.factory.functions.getPair(token0, token1).call()
            
            if pair_address == "0x0000000000000000000000000000000000000000":
                return None
                
            return pair_address
        except Exception as e:
            logger.error(f"Failed to get pair address: {e}")
            return None
    
    def get_reserves(self, pair_address: str) -> Optional[Tuple[int, int]]:
        """Get reserves for a pair"""
        try:
            pair_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(pair_address), 
                abi=PAIR_ABI
            )
            reserves = pair_contract.functions.getReserves().call()
            return (reserves[0], reserves[1])
        except Exception as e:
            logger.error(f"Failed to get reserves: {e}")
            return None
    
    def get_token_decimals(self, token_address: str) -> int:
        """Get token decimals (cached)"""
        if token_address in self.decimals_cache:
            return self.decimals_cache[token_address]
        
        try:
            token = self.w3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=ERC20_ABI
            )
            decimals = token.functions.decimals().call()
            self.decimals_cache[token_address] = decimals
            return decimals
        except:
            # Default to 18 if can't fetch
            return 18
    
    def get_price(self, token_in: str, token_out: str, amount_in: float = 1.0) -> Optional[float]:
        """Get price for swapping token_in to token_out"""
        try:
            token_in = Web3.to_checksum_address(token_in)
            token_out = Web3.to_checksum_address(token_out)
            
            # Get decimals
            decimals_in = self.get_token_decimals(token_in)
            decimals_out = self.get_token_decimals(token_out)
            
            # Convert amount to wei
            amount_in_wei = int(amount_in * 10**decimals_in)
            
            # Get amounts out from router
            amounts = self.router.functions.getAmountsOut(
                amount_in_wei,
                [token_in, token_out]
            ).call()
            
            # Convert back to human readable
            amount_out = amounts[1] / 10**decimals_out
            
            return amount_out
            
        except Exception as e:
            logger.error(f"Failed to get price on {self.name}: {e}")
            return None
    
    def get_price_impact(self, token_in: str, token_out: str, amount_in: float) -> Optional[float]:
        """Calculate price impact for a trade"""
        try:
            # Get price for small amount (no impact)
            small_price = self.get_price(token_in, token_out, 0.001)
            if not small_price:
                return None
            
            # Get price for actual amount
            actual_price = self.get_price(token_in, token_out, amount_in)
            if not actual_price:
                return None
            
            # Calculate impact
            impact = abs(1 - (actual_price / amount_in) / (small_price / 0.001))
            return impact
            
        except Exception as e:
            logger.error(f"Failed to calculate price impact: {e}")
            return None

class LiskSwap(LiskDEX):
    """LiskSwap specific implementation"""
    
    def __init__(self, w3: Web3):
        super().__init__(
            w3,
            router_address="0x1234567890123456789012345678901234567890",  # TODO: Set actual addresses
            factory_address="0x2345678901234567890123456789012345678901",
            name="LiskSwap"
        )
        
        # LiskSwap specific tokens
        self.tokens = {
            "LSK": "0x6789012345678901234567890123456789012345",
            "WLSK": "0x5678901234567890123456789012345678901234",
            "USDC": "0x2345678901234567890123456789012345678901"
        }
    
    def get_lsk_pools(self) -> List[Dict]:
        """Get all LSK token pools"""
        pools = []
        try:
            lsk_address = self.tokens["LSK"]
            
            # Check LSK pairs with major tokens
            for token_name, token_address in self.tokens.items():
                if token_name == "LSK":
                    continue
                    
                pair_address = self.get_pair_address(lsk_address, token_address)
                if pair_address:
                    reserves = self.get_reserves(pair_address)
                    if reserves:
                        pools.append({
                            "pair": f"LSK/{token_name}",
                            "address": pair_address,
                            "reserves": reserves,
                            "dex": "LiskSwap"
                        })
                        
        except Exception as e:
            logger.error(f"Failed to get LSK pools: {e}")
            
        return pools

class ZamaPrivatePool:
    """Interface for Zama FHE private pools"""
    
    def __init__(self, w3: Web3, pool_address: str, encryption_key: str, name: str = "ZamaPool"):
        self.w3 = w3
        self.name = name
        self.pool_address = Web3.to_checksum_address(pool_address)
        self.encryption_key = encryption_key
        
    def encrypt_amount(self, amount: float) -> bytes:
        """Encrypt amount using FHE for private transactions"""
        # TODO: Implement actual FHE encryption
        return b"encrypted_amount"
    
    def get_encrypted_balance(self, user_address: str) -> bytes:
        """Get encrypted balance from private pool"""
        # TODO: Implement FHE balance query
        return b"encrypted_balance"
    
    def submit_private_transaction(self, from_addr: str, to_addr: str, encrypted_amount: bytes) -> str:
        """Submit encrypted transaction to Zama private pool"""
        # TODO: Implement actual FHE transaction
        return "0x_transaction_hash"

class PrivatePoolScanner:
    """Scans for opportunities across Lisk DEXes and Zama private pools"""
    
    def __init__(self, w3_lisk: Web3, w3_zama: Web3):
        self.w3_lisk = w3_lisk
        self.w3_zama = w3_zama
        self.dexes = {}
        self.private_pools = {}
        
        # Initialize LiskSwap
        self.dexes["liskswap"] = LiskSwap(w3_lisk)
        
        # Initialize Zama private pools
        self.private_pools["pool_a"] = ZamaPrivatePool(
            w3_zama, 
            "0x3456789012345678901234567890123456789012",
            "fhe_key_a",
            "Private Pool A"
        )
        self.private_pools["pool_b"] = ZamaPrivatePool(
            w3_zama,
            "0x4567890123456789012345678901234567890123", 
            "fhe_key_b",
            "Private Pool B"
        )
        
    def find_private_pool_opportunities(self, tokens: List[str], dex_name: str = "liskswap") -> List[Dict]:
        """Find opportunities for private fund movement"""
        opportunities = []
        dex = self.dexes.get(dex_name)
        
        if not dex:
            logger.error(f"DEX {dex_name} not found")
            return opportunities
        
        # Check all triangular paths
        for i in range(len(tokens)):
            for j in range(len(tokens)):
                if i == j:
                    continue
                for k in range(len(tokens)):
                    if k == i or k == j:
                        continue
                    
                    # Path: token[i] -> token[j] -> token[k] -> token[i]
                    path = [tokens[i], tokens[j], tokens[k], tokens[i]]
                    
                    try:
                        # Calculate prices for each leg
                        price1 = dex.get_price(tokens[i], tokens[j], 1.0)
                        if not price1:
                            continue
                            
                        price2 = dex.get_price(tokens[j], tokens[k], price1)
                        if not price2:
                            continue
                            
                        price3 = dex.get_price(tokens[k], tokens[i], price2)
                        if not price3:
                            continue
                        
                        # Calculate profit
                        profit = price3 - 1.0
                        profit_pct = profit * 100
                        
                        if profit_pct > 0.1:  # Only log if > 0.1% profit
                            opportunities.append({
                                "type": "triangular",
                                "dex": dex_name,
                                "path": path,
                                "profit_pct": profit_pct,
                                "input_amount": 1.0,
                                "output_amount": price3,
                                "profitable": profit_pct > 0.3  # 0.3% threshold
                            })
                            
                    except Exception as e:
                        logger.debug(f"Failed to calculate path {path}: {e}")
                        
        return opportunities
    
    def find_cross_chain_opportunities(self, token_in: str, token_out: str) -> List[Dict]:
        """Find opportunities between Lisk DEXes and Zama private pools"""
        opportunities = []
        
        # Get prices from all DEXes
        prices = {}
        for dex_name, dex in self.dexes.items():
            price = dex.get_price(token_in, token_out)
            if price:
                prices[dex_name] = price
        
        # Find price differences
        if len(prices) >= 2:
            dex_names = list(prices.keys())
            for i in range(len(dex_names)):
                for j in range(i+1, len(dex_names)):
                    dex1, dex2 = dex_names[i], dex_names[j]
                    price1, price2 = prices[dex1], prices[dex2]
                    
                    # Calculate arbitrage opportunity
                    if price1 > price2:
                        # Buy on dex2, sell on dex1
                        profit_pct = ((price1 / price2) - 1) * 100
                        if profit_pct > 0.1:
                            opportunities.append({
                                "type": "cross_dex",
                                "buy_dex": dex2,
                                "sell_dex": dex1,
                                "token_in": token_in,
                                "token_out": token_out,
                                "buy_price": price2,
                                "sell_price": price1,
                                "profit_pct": profit_pct,
                                "profitable": profit_pct > 0.3
                            })
                    else:
                        # Buy on dex1, sell on dex2
                        profit_pct = ((price2 / price1) - 1) * 100
                        if profit_pct > 0.1:
                            opportunities.append({
                                "type": "cross_dex",
                                "buy_dex": dex1,
                                "sell_dex": dex2,
                                "token_in": token_in,
                                "token_out": token_out,
                                "buy_price": price1,
                                "sell_price": price2,
                                "profit_pct": profit_pct,
                                "profitable": profit_pct > 0.3
                            })
                            
        return opportunities

def get_private_pool_analytics(w3_lisk: Web3, w3_zama: Web3) -> Dict:
    """Get analytics for Lisk DEXes and Zama private pools"""
    analytics = {
        "lisk_dexes": {},
        "zama_pools": {},
        "top_pools": [],
        "total_tvl": 0
    }
    
    try:
        # Initialize LiskSwap
        lisk_dex = LiskSwap(w3_lisk)
        
        # Get LSK pools
        lsk_pools = lisk_dex.get_lsk_pools()
        
        analytics["lisk_dexes"]["liskswap"] = {
            "pools_found": len(lsk_pools),
            "pools": lsk_pools
        }
        
        # Get top pools by reserves
        for pool in lsk_pools:
            analytics["top_pools"].append({
                "pair": pool["pair"],
                "dex": pool["dex"],
                "reserves": pool["reserves"]
            })
        
        # Initialize Zama private pools
        analytics["zama_pools"]["private_pools"] = {
            "pool_a": {"status": "active", "encrypted": True},
            "pool_b": {"status": "active", "encrypted": True}
        }
            
    except Exception as e:
        logger.error(f"Failed to get pool analytics: {e}")
        
    return analytics