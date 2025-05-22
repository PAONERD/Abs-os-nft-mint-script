from loguru import logger
import primp
import random
import asyncio

from src.utils.config import Config
from src.utils.client import create_client
from src.model.Os_mint.instance import OsMint

class Start:
    def __init__(
        self,
        account_index: int,
        proxy: str,
        private_key: str,
        config: Config,
    ):
        self.account_index = account_index
        self.proxy = proxy
        self.private_key = private_key
        self.config = config

        self.session: primp.AsyncClient | None = None

    async def initialize(self):
        try:
            self.session = await create_client(self.proxy)

            return True
        except Exception as e:
            logger.error(f"[{self.account_index}] | Error: {e}")
            return False

    async def flow(self, config):
        try:
            if config.SETTINGS.OS_MINT == True:
                Os_mint = OsMint(
                    self.account_index,
                    self.proxy,
                    self.private_key,
                    self.config,
                    self.session,
                )
                Number_of_mintes = self.config.SETTINGS.NUMBER_OF_MINTES
                for i in range(Number_of_mintes):
                    logger.info(f"[{self.account_index}] Minting Os NFT {i + 1}/{Number_of_mintes}")
                    await Os_mint.mint()
                    await self.sleep()

            return True
        except Exception as e:
            logger.error(f"[{self.account_index}] | Error: {e}")
            return False

        
            
    async def sleep(self):
        """Делает рандомную паузу между действиями"""
        pause = random.randint(
            self.config.SETTINGS.RANDOM_PAUSE_BETWEEN_ACTIONS[0],
            self.config.SETTINGS.RANDOM_PAUSE_BETWEEN_ACTIONS[1],
        )
        logger.info(
            f"[{self.account_index}] Sleeping {pause} seconds"
        )
        await asyncio.sleep(pause)