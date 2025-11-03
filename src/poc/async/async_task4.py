import asyncio


async def http_call(num):
    print(f"Starting HTTP call with parameter {num}")
    await asyncio.sleep(num)  # Simulating an I/O-bound operation with sleep
    print(f"Completed HTTP call {num}")
    return {"status": "success", "data": num} 






task_list = [
        asyncio.create_task(http_call(3),name="t1"),
        asyncio.create_task(http_call(2),name="t2"),
        asyncio.create_task(http_call(1),name="t3")
]   


# sys:1: RuntimeWarning: coroutine 'http_call' was never awaited
# because the event loop(created by function asyncio.run()) is not created yet when we are creating tasks and trying to add them to it.
rs =  asyncio.run(task_list)
print(rs)
                       