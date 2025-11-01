
import src.configs.config
from loguru import logger
import time
import pytest
import asyncio

from src.decorators.time_decorator import log_execution_time



def test_log_execution_time_decorator_sync():
    """
    A demonstration of the log_execution_time decorator on a synchronous function.
    """
    @log_execution_time
    def decorated_sync_function(duration):
        """A simple function that sleeps for a given duration."""
        time.sleep(duration)
        logger.info("--- Sync function body execution ---")
        return "Function executed"

    logger.info("\nRunning sync test...")
    decorated_sync_function(0.1)
    logger.info("Sync test finished.")

@pytest.mark.asyncio
async def test_log_execution_time_decorator_async():
    """
    A demonstration of the log_execution_time decorator on an asynchronous function.
    """
    @log_execution_time
    async def decorated_async_function(duration):
        """A simple async function that sleeps for a given duration."""
        await asyncio.sleep(duration)
        logger.info("--- Async function body execution ---")
        return "Async function executed"

    logger.info("\nRunning async test...")
    await decorated_async_function(0.1)
    logger.info("Async test finished.")
