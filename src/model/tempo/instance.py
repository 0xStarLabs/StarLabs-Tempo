import asyncio
import random
import secrets

import aiohttp
import primp
from eth_account import Account
from loguru import logger

from src.model.onchain.web3_custom import Web3Custom
from src.model.tempo.constants import TEMPO_TOKENS, ERC20_TRANSFER_ABI
from src.utils.config import Config
from src.utils.constants import EXPLORER_URL_TEMPO, CHAIN_ID
from src.utils.decorators import retry_async


class Tempo:
    def __init__(
        self,
        account_index: int,
        session: primp.AsyncClient,
        web3: Web3Custom,
        config: Config,
        wallet: Account,
        proxy: str,
    ):
        self.account_index = account_index
        self.session = session
        self.web3 = web3
        self.config = config
        self.wallet = wallet
        self.proxy = proxy

    async def _get_ws_connection(self):
        proxy_url = f"http://{self.proxy}"
        session = aiohttp.ClientSession()
        ws = await session.ws_connect(
            "wss://rpc.testnet.tempo.xyz/",
            proxy=proxy_url,
            headers={
                "Origin": "https://docs.tempo.xyz",
                "Cache-Control": "no-cache",
                "Accept-Language": "en-US,en;q=0.9,ru;q=0.8,zh-TW;q=0.7,zh;q=0.6,uk;q=0.5",
                "Pragma": "no-cache",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            },
        )
        return session, ws

    @retry_async(default_value=False)
    async def faucet(self) -> bool:
        session = None
        ws = None
        try:
            session, ws = await self._get_ws_connection()

            request_id = random.randint(1, 1000)
            await ws.send_json({
                "id": request_id,
                "jsonrpc": "2.0",
                "method": "tempo_fundAddress",
                "params": [self.wallet.address]
            })

            response = await ws.receive_json()

            if "result" in response:
                tx_hashes = response["result"]
                for tx_hash in tx_hashes:
                    logger.success(
                        f"{self.account_index} | Faucet TX: {EXPLORER_URL_TEMPO}{tx_hash[2:]}"
                    )
                await asyncio.sleep(3)
                await self.check_balances()
                return True
            else:
                raise Exception(f"Faucet failed: {response}")

        except Exception as e:
            random_pause = random.randint(
                self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(
                f"{self.account_index} | Faucet error: {e}"
            )
            await asyncio.sleep(random_pause)
            raise
        finally:
            if ws:
                await ws.close()
            if session:
                await session.close()

    async def check_balances(self) -> dict:
        balances = {}

        for token in TEMPO_TOKENS:
            balance = await self.web3.get_token_balance(
                wallet_address=self.wallet.address,
                token_address=token["address"],
                decimals=token["decimals"],
                symbol=token["symbol"],
            )
            balances[token["symbol"]] = balance
            amount = f"{balance.formatted:.6f}" if balance else "0"
            logger.info(f"{self.account_index} | {token['symbol']}: {amount}")

        return balances

    @retry_async(default_value=False)
    async def send_random_token(self) -> bool:
        try:
            token = random.choice(TEMPO_TOKENS)
            
            balance = await self.web3.get_token_balance(
                wallet_address=self.wallet.address,
                token_address=token["address"],
                decimals=token["decimals"],
                symbol=token["symbol"],
            )
            
            if not balance or balance.wei == 0:
                logger.warning(f"{self.account_index} | No {token['symbol']} balance to send")
                return False
            
            send_percent = random.uniform(
                self.config.TOKEN_SENDER.PERCENT_OF_BALANCE_TO_SEND[0] / 100,
                self.config.TOKEN_SENDER.PERCENT_OF_BALANCE_TO_SEND[1] / 100,
            )
            token_unit = 10 ** token["decimals"]
            amount_to_send = int(balance.wei * send_percent)
            amount_to_send = (amount_to_send // token_unit) * token_unit
            
            if amount_to_send == 0:
                logger.warning(f"{self.account_index} | Amount to send is too small")
                return False
            
            if self.config.TOKEN_SENDER.SEND_TOKENS_TO_MY_WALLETS:
                async with self.config.lock:
                    available_wallets = [
                        w for w in self.config.WALLETS.wallets 
                        if w.address.lower() != self.wallet.address.lower()
                    ]
                
                if not available_wallets:
                    logger.warning(f"{self.account_index} | No other wallets available to send to")
                    return False
                
                target_wallet = random.choice(available_wallets)
                to_address = target_wallet.address
                logger.info(f"{self.account_index} | Sending to own wallet #{target_wallet.account_index}")
            else:
                random_bytes = secrets.token_bytes(20)
                to_address = self.web3.web3.to_checksum_address("0x" + random_bytes.hex())
                logger.info(f"{self.account_index} | Sending to random address: {to_address}")
            
            token_contract = self.web3.web3.eth.contract(
                address=self.web3.web3.to_checksum_address(token["address"]),
                abi=ERC20_TRANSFER_ABI
            )
            
            formatted_amount = amount_to_send // token_unit
            logger.info(f"{self.account_index} | Sending {formatted_amount} {token['symbol']} to {to_address}")
            
            tx = await token_contract.functions.transfer(
                self.web3.web3.to_checksum_address(to_address),
                amount_to_send
            ).build_transaction({
                'chainId': CHAIN_ID,
                'from': self.wallet.address,
                'nonce': await self.web3.web3.eth.get_transaction_count(self.wallet.address),
                'gasPrice': await self.web3.web3.eth.gas_price,
            })
            tx['gas'] = await self.web3.web3.eth.estimate_gas(tx)
            
            signed_tx = self.web3.web3.eth.account.sign_transaction(tx, self.wallet.key)
            tx_hash = await self.web3.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            rcpt = await self.web3.web3.eth.wait_for_transaction_receipt(tx_hash, poll_latency=2)
            
            if rcpt['status'] != 1:
                raise Exception('Token transfer transaction failed')
            
            logger.success(f"{self.account_index} | Token sent! TX: {EXPLORER_URL_TEMPO}{rcpt['transactionHash'].hex()}")
            return True
            
        except Exception as e:
            random_pause = random.randint(
                self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                self.config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.error(f"{self.account_index} | Send token error: {e}")
            await asyncio.sleep(random_pause)
            raise
