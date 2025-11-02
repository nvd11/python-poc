
async def func1():
    print("This is async function 1")
    return "Result from async function 1"

def func2():
    print("This is sync function 2")
    return "Result from sync function 2"
coro = func1() # This line creates a coroutine object but never awaits it, causing a RuntimeWarning.
print(type(coro))   # <class 'coroutine'>

result = func2() # func2 will be executed immediately
print(type(result))    # <class 'str'> as return type of func2 is str





import asyncio

def trigger_event_loop(): # old stype
    loop = asyncio.get_event_loop()
    result_from_run = loop.run_until_complete(func1())
    print(f"Result from asyncio.run(): {result_from_run}")

trigger_event_loop()
def trigger_event_loop2(): # after python 3.7
    # asyncio.run() not only executes the coroutine but also returns its result.
    result_from_run = asyncio.run(func1())
    print(f"Result from asyncio.run(): {result_from_run}")

trigger_event_loop2()

async def func3():
    print("This is async function 3")
    rs = await func1()  # waiting for func1 to complete
    print(type(rs))
    print(rs)

asyncio.run(func3())
