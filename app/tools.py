import httpx
import yaml
from typing import Dict, List, Any
from web3 import Web3
from eth_account import Account
from langchain.tools import BaseTool
import os
import json
import numpy as np

class DefiLlamaTool(BaseTool):
    name = "defi_llama_apy"
    description = "Get APY data for DeFi protocols from DefiLlama"
    
    def _run(self, protocol: str) -> Dict[str, Any]:
        """Get APY data for a specific protocol"""
        try:
            # TODO: Implement actual DefiLlama API call
            # For now, return mocked data
            url = f"https://yields.llama.fi/pools"
            # response = httpx.get(url)
            # data = response.json()
            
            # Mock response for development
            mock_data = {
                "aave-v3": {"apy": 0.045, "tvl": 1000000},
                "compound-v3": {"apy": 0.052, "tvl": 800000},
                "morpho-aave": {"apy": 0.048, "tvl": 500000}
            }
            
            return mock_data.get(protocol, {"apy": 0.0, "tvl": 0})
            
        except Exception as e:
            return {"error": str(e), "apy": 0.0, "tvl": 0}

class CryptoNewsTool(BaseTool):
    name = "crypto_news_sentiment"
    description = "Get latest crypto news headlines and sentiment analysis"
    
    def _run(self, tokens: List[str]) -> Dict[str, Any]:
        """Get news sentiment for specified tokens"""
        try:
            # TODO: Implement actual news API call
            # For now, return mocked sentiment data
            
            mock_sentiment = {
                "USDC": {"sentiment": "neutral", "score": 0.0, "headlines": ["USDC maintains stability"]},
                "WETH": {"sentiment": "positive", "score": 0.2, "headlines": ["Ethereum upgrade successful"]},
                "default": {"sentiment": "neutral", "score": 0.0, "headlines": ["Market remains stable"]}
            }
            
            results = {}
            for token in tokens:
                results[token] = mock_sentiment.get(token, mock_sentiment["default"])
            
            return results
            
        except Exception as e:
            return {"error": str(e)}

class VaultTxTool(BaseTool):
    name = "vault_transaction"
    description = "Execute vault rebalance transactions on-chain"
    
    def __init__(self):
        super().__init__()
        self.w3 = None
        self.account = None
        self._setup_wallet()
    
    def _setup_wallet(self):
        """Setup Web3 connection and wallet"""
        try:
            rpc_url = os.getenv("RPC_URL")
            private_key = os.getenv("PRIVATE_KEY")
            
            if not rpc_url or not private_key:
                raise ValueError("RPC_URL and PRIVATE_KEY environment variables required")
            
            self.w3 = Web3(Web3.HTTPProvider(rpc_url))
            self.account = Account.from_key(private_key)
            
        except Exception as e:
            print(f"Wallet setup error: {e}")
    
    def _run(self, vault_addr: str, allocations: Dict[str, float]) -> Dict[str, Any]:
        """Set vault allocations via on-chain transaction"""
        try:
            if not self.w3 or not self.account:
                return {"error": "Wallet not properly configured"}
            
            # TODO: Implement actual vault contract interaction
            # This would typically involve:
            # 1. Loading vault ABI
            # 2. Creating contract instance
            # 3. Building transaction
            # 4. Signing and sending
            
            # Mock transaction for development
            mock_tx_hash = "0x" + "0" * 64
            mock_gas_used = 150000
            mock_gas_price = self.w3.eth.gas_price if self.w3 else 20000000000
            
            return {
                "success": True,
                "tx_hash": mock_tx_hash,
                "gas_used": mock_gas_used,
                "gas_price": mock_gas_price,
                "allocations": allocations,
                "vault_address": vault_addr
            }
            
        except Exception as e:
            return {"error": str(e), "success": False}

def load_config():
    """Load configuration files"""
    config = {}
    
    # Load pools config
    with open("config/pools.yaml", "r") as f:
        config["pools"] = yaml.safe_load(f)
    
    # Load addresses config
    with open("config/addresses.yaml", "r") as f:
        config["addresses"] = yaml.safe_load(f)
    
    return config

class VaultStateTool:
    def __init__(self, web3, vault_addr, abi):
        self.vault = web3.eth.contract(address=vault_addr, abi=abi)

    def get_allocations(self) -> dict:
        # example: mapping<string,uint256> allocations
        strategies, amounts = self.vault.functions.getAllocations().call()
        tvl = sum(amounts) or 1
        return {s.lower(): a / tvl for s, a in zip(strategies, amounts)}

__all__ = ["DefiLlamaTool", "CryptoNewsTool", "VaultTxTool", "VaultStateTool", "load_config"] 