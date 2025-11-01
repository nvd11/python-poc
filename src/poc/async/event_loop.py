import src.configs.config
from loguru import logger
import asyncio

async def func1():
   logger.info("step 1")
   await asyncio.sleep(2)
   logger.info("step 2")

async def func2():
   logger.info("step 3")
   await asyncio.sleep(2)
   logger.info("step 4")

def get_event_loop_tasks():
   tasks = [
       func1(),
       func2(),
   ]
   return tasks


def trigger_event_loop():
    loop = asyncio.get_event_loop()
    tasks = get_event_loop_tasks()
    loop.run_until_complete(asyncio.gather(*tasks))

async def run_tasks():
    tasks = get_event_loop_tasks()
    await asyncio.gather(*tasks)


def trigger_event_loop2():
     tasks = get_event_loop_tasks()
     asyncio.run(await asyncio.gather(*tasks))
    

if __name__ == "__main__":
    trigger_event_loop2()