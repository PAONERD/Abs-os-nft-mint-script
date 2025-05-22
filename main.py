from loguru import logger
import urllib3
import sys
import asyncio
import platform

from process import start
import src


async def main():
    configuration()
    await start()


log_format = (
    "<light-blue>[</light-blue><yellow>{time:HH:mm:ss}</yellow><light-blue>]</light-blue> | "
    "<level>{level: <8}</level> | "
    "<cyan>{file}:{line}</cyan> | "
    "<level>{message}</level>"
)

def configuration():
    urllib3.disable_warnings()
    logger.remove()
    logger.add(
        sys.stdout,
        colorize=True,
        format=log_format,
    )
    logger.add(
        "logs/app.log",
        rotation="10 MB",
        retention="1 month",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{line} - {message}",
        level="INFO",
    )

if __name__ == "__main__":
    asyncio.run(main())