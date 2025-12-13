import asyncio
import random

import primp
from eth_account import Account
from loguru import logger

from src.model.onchain.web3_custom import Web3Custom
from src.utils.config import Config
from src.utils.constants import EXPLORER_URL_TEMPO, CHAIN_ID
from src.utils.decorators import retry_async


ONCHAINGM_CONTRACT = "0x2d91014c9ab33821c4fa15806c63d2c053cdd10c"
ONCHAINGM_DEPLOY_CONTRACT = "0xa89E3e260C85d19c0b940245FDdb1e845C93dED8"
PATHUSD_CONTRACT = "0x20C0000000000000000000000000000000000000"
APPROVE_AMOUNT_GM = 15000000  # 15 pathUSD (6 decimals)
APPROVE_AMOUNT_DEPLOY = 20000000  # 20 pathUSD (6 decimals)


@retry_async(default_value=False)
async def onchaingm_gm(
    account_index: int,
    session: primp.AsyncClient,
    web3: Web3Custom,
    config: Config,
    wallet: Account,
):
    try:
        logger.info(f"{account_index} | Starting OnchainGM GM...")

        # Step 1: Approve pathUSD for OnchainGM contract
        approve_data = (
            "0x095ea7b3"
            "0000000000000000000000002d91014c9ab33821c4fa15806c63d2c053cdd10c"
            f"{APPROVE_AMOUNT_GM:064x}"
        )

        gas_params = await web3.get_gas_params()
        if gas_params is None:
            raise Exception("Failed to get gas parameters")

        approve_tx_params = {
            "from": wallet.address,
            "to": web3.web3.to_checksum_address(PATHUSD_CONTRACT),
            "value": 0,
            "data": approve_data,
            "nonce": await web3.web3.eth.get_transaction_count(wallet.address),
            "chainId": CHAIN_ID,
            **gas_params,
        }

        try:
            estimated_gas = await web3.estimate_gas(approve_tx_params)
            approve_tx_params["gas"] = estimated_gas
        except Exception as e:
            raise Exception(f"Error estimating gas for approve: {e}")

        logger.info(f"{account_index} | Approving pathUSD for OnchainGM contract...")

        tx_hash = await web3.execute_transaction(
            approve_tx_params,
            wallet=wallet,
            chain_id=CHAIN_ID,
            explorer_url=EXPLORER_URL_TEMPO,
        )

        if not tx_hash:
            raise Exception("Failed to approve pathUSD")

        logger.success(f"{account_index} | Successfully approved pathUSD")

        # Step 2: Call onChainGM
        mint_data = "0x84a3bb6b0000000000000000000000000000000000000000000000000000000000000000"

        gas_params = await web3.get_gas_params()
        if gas_params is None:
            raise Exception("Failed to get gas parameters")

        mint_tx_params = {
            "from": wallet.address,
            "to": web3.web3.to_checksum_address(ONCHAINGM_CONTRACT),
            "value": 0,
            "data": mint_data,
            "nonce": await web3.web3.eth.get_transaction_count(wallet.address),
            "chainId": CHAIN_ID,
            **gas_params,
        }

        try:
            estimated_gas = await web3.estimate_gas(mint_tx_params)
            mint_tx_params["gas"] = estimated_gas
        except Exception as e:
            raise Exception(f"Error estimating gas for mint: {e}")

        logger.info(f"{account_index} | Minting OnchainGM GM...")

        tx_hash = await web3.execute_transaction(
            mint_tx_params,
            wallet=wallet,
            chain_id=CHAIN_ID,
            explorer_url=EXPLORER_URL_TEMPO,
        )

        if tx_hash:
            logger.success(f"{account_index} | Successfully completed OnchainGM GM")
            return True

        raise Exception("Failed to complete OnchainGM GM")

    except Exception as e:
        random_pause = random.randint(
            config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
            config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
        )
        logger.error(
            f"{account_index} | Error in OnchainGM GM: {e}. Waiting {random_pause} seconds..."
        )
        await asyncio.sleep(random_pause)
        raise


@retry_async(default_value=False)
async def onchaingm_deploy(
    account_index: int,
    session: primp.AsyncClient,
    web3: Web3Custom,
    config: Config,
    wallet: Account,
):
    try:
        logger.info(f"{account_index} | Starting OnchainGM Deploy...")

        # Step 1: Approve pathUSD for OnchainGM Deploy contract
        approve_data = (
            "0x095ea7b3"
            "000000000000000000000000a89e3e260c85d19c0b940245fddb1e845c93ded8"
            f"{APPROVE_AMOUNT_DEPLOY:064x}"
        )

        gas_params = await web3.get_gas_params()
        if gas_params is None:
            raise Exception("Failed to get gas parameters")

        approve_tx_params = {
            "from": wallet.address,
            "to": web3.web3.to_checksum_address(PATHUSD_CONTRACT),
            "value": 0,
            "data": approve_data,
            "nonce": await web3.web3.eth.get_transaction_count(wallet.address),
            "chainId": CHAIN_ID,
            **gas_params,
        }

        try:
            estimated_gas = await web3.estimate_gas(approve_tx_params)
            approve_tx_params["gas"] = estimated_gas
        except Exception as e:
            raise Exception(f"Error estimating gas for approve: {e}")

        logger.info(f"{account_index} | Approving pathUSD for OnchainGM Deploy contract...")

        tx_hash = await web3.execute_transaction(
            approve_tx_params,
            wallet=wallet,
            chain_id=CHAIN_ID,
            explorer_url=EXPLORER_URL_TEMPO,
        )

        if not tx_hash:
            raise Exception("Failed to approve pathUSD")

        logger.success(f"{account_index} | Successfully approved pathUSD")

        # Step 2: Call deploy
        deploy_data = "0x775c300c"

        gas_params = await web3.get_gas_params()
        if gas_params is None:
            raise Exception("Failed to get gas parameters")

        deploy_tx_params = {
            "from": wallet.address,
            "to": web3.web3.to_checksum_address(ONCHAINGM_DEPLOY_CONTRACT),
            "value": 0,
            "data": deploy_data,
            "nonce": await web3.web3.eth.get_transaction_count(wallet.address),
            "chainId": CHAIN_ID,
            **gas_params,
        }

        try:
            estimated_gas = await web3.estimate_gas(deploy_tx_params)
            deploy_tx_params["gas"] = estimated_gas
        except Exception as e:
            raise Exception(f"Error estimating gas for deploy: {e}")

        logger.info(f"{account_index} | Deploying OnchainGM...")

        tx_hash = await web3.execute_transaction(
            deploy_tx_params,
            wallet=wallet,
            chain_id=CHAIN_ID,
            explorer_url=EXPLORER_URL_TEMPO,
        )

        if tx_hash:
            logger.success(f"{account_index} | Successfully completed OnchainGM Deploy")
            return True

        raise Exception("Failed to complete OnchainGM Deploy")

    except Exception as e:
        random_pause = random.randint(
            config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
            config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
        )
        logger.error(
            f"{account_index} | Error in OnchainGM Deploy: {e}. Waiting {random_pause} seconds..."
        )
        await asyncio.sleep(random_pause)
        raise
