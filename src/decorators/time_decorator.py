
import src.configs.config
from loguru import logger
import time
import functools
import asyncio

from inspect import iscoroutinefunction


def log_execution_time(func):
    """
    A decorator that logs the start time, end time, and elapsed time of a function's execution
    using the logging module. Supports both synchronous and asynchronous functions.
    """
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        logger.info(f"Function '{func.__name__}' started with args: {args}, kwargs: {kwargs}")
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.info(f"Function '{func.__name__}' finished with args: {args}, kwargs: {kwargs}. Elapsed time: {elapsed_time:.4f} seconds")
        return result

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        logger.info(f"Function '{func.__name__}' started with args: {args}, kwargs: {kwargs}")
        result = await func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.info(f"Function '{func.__name__}' finished with args: {args}, kwargs: {kwargs}. Elapsed time: {elapsed_time:.4f} seconds")
        return result

    if iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
