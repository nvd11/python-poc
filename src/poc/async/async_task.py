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
    task1 = asyncio.create_task(http_call(3))
    task2 = asyncio.create_task(http_call(2))

    print("Tasks created, awaiting their completion")
    result1 = ""
    result2 = ""

    result1 = await task1 # waiting for task1 to complete, but tasks is not triggered again
    print(f"Result from task1: {result1}")
    
    result2 = await task2 # waiting for task2 to complete, but tasks is not triggered again
    print(f"Result from task2: {result2}")
    print("All tasks completed")        

asyncio.run(main())