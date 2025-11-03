

import asyncio

async def func1():

    print("Started func1")
   
   
    # get the current event loop
    loop = asyncio.get_running_loop()


    # create a Future object, but it do nothing
    future = loop.create_future()

    # wait for the return 
    await future

    # this line will never be reached, as future is never set with result or exception
    print("Done func1")


asyncio.run(func1()) # this will hang forever, as future is never set with result or exception