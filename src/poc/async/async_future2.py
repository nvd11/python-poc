

import asyncio


async def http_call(fut: asyncio.Future):
    print(f"Starting HTTP call with parameter {fut}")
    await asyncio.sleep(3)  # Simulating an I/O-bound operation with sleep
    fut.set_result("HTTP call result")
    print(f"Completed HTTP call")
    return {"status": "success", "data": fut.result}

async def func1():

    print("Started func1")
   
   
    # get the current event loop
    loop = asyncio.get_running_loop()


    # create a Future object, but it do nothing， this fut will never know when it could completed
    future = loop.create_future()

    # create a task which will set result to future after http_call is done
    # then the future will be marked as done, and func1 could continue
    await loop.create_task(http_call(future))  

    # then we could await the future obj
    rs = await future
    print(rs)


    # this line will never be reached, as future is never set with result or exception
    print("Done func1")


asyncio.run(func1()) # this will hang forever, as future is never set with result or exception