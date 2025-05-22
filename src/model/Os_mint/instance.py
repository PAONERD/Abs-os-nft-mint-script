import asyncio
import random
from eth_account import Account
from primp import AsyncClient
from web3 import AsyncWeb3
from web3.contract import Contract

from src.utils.constants import EXPLORER_URL, RPC_URL
from src.utils.config import Config
from loguru import logger


ABI = [
    {
    "inputs":[
        {"internalType":"address","name":"nftContract","type":"address"},
        {"internalType":"address","name":"feeRecipient","type":"address"},
        {"internalType":"address","name":"minterIfNotPayer","type":"address"},
        {"internalType":"uint256","name":"quantity","type":"uint256"}
    ],
    "name":"mintPublic",
    "outputs":[],
    "stateMutability":"payable",
    "type":"function"
    }
]


class OsMint:
    def __init__(
        self,
        account_index: int,
        proxy: str,
        private_key: str,
        config: Config,
        session: AsyncClient,
    ):
        self.account_index = account_index
        self.proxy = proxy
        self.private_key = private_key
        self.config = config
        self.session = session

        self.account: Account = Account.from_key(private_key=private_key)
        self.web3 = AsyncWeb3(
             AsyncWeb3.AsyncHTTPProvider(
                RPC_URL,
                request_kwargs={"proxy": (f"http://{proxy}"), "ssl": False},
             )
        ) 
        self.contract_address = "0x00005EA00Ac477B1030CE78506496e8C2dE24bf5"
        self.nft_contract: Contract = self.web3.eth.contract(
            address=self.contract_address, abi=ABI
        )

    async def mint(self):
        for retry in range(self.config.SETTINGS.ATTEMPTS):
            try:
                logger.info(f"[{self.account_index}] Minting Os NFT")

                nft_contract_address = self.config.SETTINGS.CONTRACT_ADDRESS
                fee_recipient = "0x0000a26b00c1F0DF003000390027140000fAa719"
                minter_if_not_payer = self.account.address
                quantity = 1

                # Подготавливаем транзакцию минта
                mint_txn = await self.nft_contract.functions.mintPublic(
                    nft_contract_address,
                    fee_recipient,
                    minter_if_not_payer,
                    quantity
                ).build_transaction({
                    "from": self.account.address,
                    "value": 0,
                    "nonce": await self.web3.eth.get_transaction_count(self.account.address),
                    "maxFeePerGas": await self.web3.eth.gas_price,
                    "maxPriorityFeePerGas": await self.web3.eth.gas_price,
                })

                # Подписываем транзакцию
                signed_txn = self.web3.eth.account.sign_transaction(
                    mint_txn, self.private_key
                )

                # Отправляем транзакцию
                tx_hash = await self.web3.eth.send_raw_transaction(
                    signed_txn.raw_transaction
                )

                # Ждем подтверждения
                receipt = await self.web3.eth.wait_for_transaction_receipt(tx_hash)

                if receipt["status"] == 1:
                    logger.success(
                        f"[{self.account_index}] Successfully minted Os NFT. TX: {EXPLORER_URL}{tx_hash.hex()}"
                    )
                    return True
                else:
                    logger.error(
                        f"[{self.account_index}] Failed to mint Os NFT. TX: {EXPLORER_URL}{tx_hash.hex()}"
                    )
                    return False

            except Exception as e:
                random_pause = random.randint(
                    self.config.SETTINGS.RANDOM_PAUSE_BETWEEN_ACTIONS[0],
                    self.config.SETTINGS.RANDOM_PAUSE_BETWEEN_ACTIONS[1],
                )
                logger.error(
                    f"[{self.account_index}] Error in mint on Os: {e}. Sleeping for {random_pause} seconds"
                )
                await asyncio.sleep(random_pause)

        return False