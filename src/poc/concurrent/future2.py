import asyncio
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import time


# not async function
def func(value):
    print(f"Function called with value: {value}")
    time.sleep(2)
    print(f"Function ended with value: {value}")
    return value

async def main():
      loop = asyncio.get_running_loop()


      # run in  a thread pool
      with ThreadPoolExecutor(max_workers=5) as thread_pool:
          tasks = []
          for i in range(10):
              # here it's the Future object
              future = loop.run_in_executor(thread_pool, func, i)
              tasks.append(future)
              print(f"Submitted task {i}, future: {future}, type of future: {type(future)}")
          
          # await all tasks to complete
          results = await asyncio.gather(*tasks)
          print("All tasks completed, results:", results)

asyncio.run(main())