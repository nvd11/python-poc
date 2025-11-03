import asyncio


async def http_call(num):
    print(f"Starting HTTP call with parameter {num}")
    await asyncio.sleep(num)  # Simulating an I/O-bound operation with sleep
    print(f"Completed HTTP call {num}")
    return {"status": "success", "data": num} 

async def main():
    print("Starting main coroutine")

    # !!!important,  2once task is created , it will be added to event loop automatically
    # and will start running in background!!!

    task_list = [
        asyncio.create_task(http_call(3),name="t1"),
        asyncio.create_task(http_call(2),name="t2"),
        asyncio.create_task(http_call(1),name="t3")
    ]
   
    print ("Tasks created, awaiting their start and completion")
    # Using asyncio.wait with timeout， will return two sets: done and pending
    done, pending = await asyncio.wait(task_list, timeout=2)  
    print(f"Done tasks: {done}")
    rs1 = done.pop().result()
    print(rs1)
    print(f"Pending tasks: {pending}")
    print("done main")
    # here will print "Completed HTTP call 2"

asyncio.run(main())