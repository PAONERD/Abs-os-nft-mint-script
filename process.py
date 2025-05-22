import asyncio
import random
import subprocess
import os

from loguru import logger

import src.utils
import src.model

async def start():
    async def launch_wrapper(index, proxy, private_key):
        async with semaphore:
            await account_flow(
                index,
                proxy,
                private_key,
                config,
                lock,
            )
    print("")

    print("Options:\n")
    print("[1] Start the bot")
    print("[2] Exit")
    
    try:
        choice = input("Enter: ").strip()
    except Exception as e:
        logger.error(f"Input error: {e}")
        return
    
    if choice == "2" or not choice:
        return
    
    elif choice == "1":
        pass

    else:
        logger.error(f"Invalid choice: {choice}")
        return

    config = src.utils.get_config()

    # Читаем все файлы
    proxies = src.utils.read_txt_file("proxies", "data/proxies.txt")
    if len(proxies) == 0:
        logger.error("No proxies found.")
        return
    proxies = src.utils.check_proxy_format(proxies)
    if proxies is False:
        return
    
    private_keys = src.utils.read_txt_file("private keys", "data/private_keys.txt")
    

    # Определяем диапазон аккаунтов
    start_index = config.SETTINGS.ACCOUNTS_RANGE[0]
    end_index = config.SETTINGS.ACCOUNTS_RANGE[1]

    # Если оба 0, проверяем EXACT_ACCOUNTS_TO_USE
    if start_index == 0 and end_index == 0:
        if config.SETTINGS.EXACT_ACCOUNTS_TO_USE:
            # Преобразуем номера аккаунтов в индексы (номер - 1)
            selected_indices = [i - 1 for i in config.SETTINGS.EXACT_ACCOUNTS_TO_USE]
            accounts_to_process = [private_keys[i] for i in selected_indices]
            logger.info(
                f"Using specific accounts: {config.SETTINGS.EXACT_ACCOUNTS_TO_USE}"
            )

            # Для совместимости с остальным кодом
            start_index = min(config.SETTINGS.EXACT_ACCOUNTS_TO_USE)
            end_index = max(config.SETTINGS.EXACT_ACCOUNTS_TO_USE)
        else:
            # Если список пустой, берем все аккаунты как раньше
            accounts_to_process = private_keys
            start_index = 1
            end_index = len(private_keys)
    else:
        # Python slice не включает последний элемент, поэтому +1
        accounts_to_process = private_keys[start_index - 1 : end_index]


    threads = config.SETTINGS.THREADS

    # Подготавливаем прокси для выбранных аккаунтов
    cycled_proxies = [
        proxies[i % len(proxies)] for i in range(len(accounts_to_process))
    ]

    # Создаем список индексов и перемешиваем его
    shuffled_indices = list(range(len(accounts_to_process)))
    random.shuffle(shuffled_indices)

    # Создаем строку с порядком аккаунтов
    account_order = " ".join(str(start_index + idx) for idx in shuffled_indices)
    logger.info(
        f"Starting with accounts {start_index} to {end_index} in random order..."
    )
    logger.info(f"Accounts order: {account_order}")

    lock = asyncio.Lock()
    semaphore = asyncio.Semaphore(value=threads)
    tasks = []

    # Используем перемешанные индексы для создания задач
    for shuffled_idx in shuffled_indices:
        tasks.append(
            asyncio.create_task(
                launch_wrapper(
                    start_index + shuffled_idx,
                    cycled_proxies[shuffled_idx],
                    accounts_to_process[shuffled_idx],
                )
            )
        )

    await asyncio.gather(*tasks)

    logger.success("Saved accounts and private keys to a file.")


async def account_flow(
    account_index: int,
    proxy: str,
    private_key: str,
    config: src.utils.config.Config,
    lock: asyncio.Lock,
):
    try:
        pause = random.randint(
            config.SETTINGS.RANDOM_INITIALIZATION_PAUSE[0],
            config.SETTINGS.RANDOM_INITIALIZATION_PAUSE[1],
        )
        logger.info(f"[{account_index}] Sleeping for {pause} seconds before start...")
        await asyncio.sleep(pause)

        report = False

        instance = src.model.Start(
            account_index, proxy, private_key, config
        )

        result = await wrapper(instance.initialize, config)
        if not result:
            report = True

        result = await wrapper(instance.flow, config, config)
        if not result:
            report = True

        pause = random.randint(
            config.SETTINGS.RANDOM_PAUSE_BETWEEN_ACCOUNTS[0],
            config.SETTINGS.RANDOM_PAUSE_BETWEEN_ACCOUNTS[1],
        )
        logger.info(f"Sleeping for {pause} seconds before next account...")
        await asyncio.sleep(pause)

    except Exception as err:
        logger.error(f"{account_index} | Account flow failed: {err}")


async def wrapper(function, config: src.utils.config.Config, *args, **kwargs):
    attempts = config.SETTINGS.ATTEMPTS
    for attempt in range(attempts):
        result = await function(*args, **kwargs)
        if isinstance(result, tuple) and result and isinstance(result[0], bool):
            if result[0]:
                return result
        elif isinstance(result, bool):
            if result:
                return True

        if attempt < attempts - 1:  # Don't sleep after the last attempt
            pause = random.randint(
                config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0],
                config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1],
            )
            logger.info(
                f"Sleeping for {pause} seconds before next attempt {attempt+1}/{config.SETTINGS.ATTEMPTS}..."
            )
            await asyncio.sleep(pause)

    return result


def task_exists_in_config(task_name: str, tasks_list: list) -> bool:
    """Рекурсивно проверяет наличие задачи в списке задач, включая вложенные списки"""
    for task in tasks_list:
        if isinstance(task, list):
            if task_exists_in_config(task_name, task):
                return True
        elif task == task_name:
            return True
    return False