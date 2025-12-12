from typing import Protocol
from primp import AsyncClient
from eth_account import Account

from src.model.onchain.web3_custom import Web3Custom
from src.utils.config import Config


TEMPO_TOKENS = [
    {"symbol": "AlphaUSD", "address": "0x20c0000000000000000000000000000000000001", "decimals": 6},
    {"symbol": "BetaUSD", "address": "0x20c0000000000000000000000000000000000002", "decimals": 6},
    {"symbol": "ThetaUSD", "address": "0x20c0000000000000000000000000000000000003", "decimals": 6},
]


class TempoProtocol(Protocol):
    """Protocol class for Tempo type hints to avoid circular imports"""

    account_index: int
    session: AsyncClient
    web3: Web3Custom
    config: Config
    wallet: Account
    proxy: str



ERC20_TRANSFER_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"},
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
]
