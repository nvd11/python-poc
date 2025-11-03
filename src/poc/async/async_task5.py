import asyncio

async def http_call(num):
    print(f"Starting HTTP call with parameter {num}")
    await asyncio.sleep(num)
    return {"status": "success", "data": num} 

# 错误！此时还没有事件循环在运行
task_list = [
    asyncio.create_task(http_call(3), name="t1"),
    asyncio.create_task(http_call(2), name="t2"),
]   

# 这行代码永远不会被执行到
asyncio.run(asyncio.gather(*task_list))