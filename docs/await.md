# python 异步编程 -- 理解await

## 什么是await

`await` 是 Python 异步编程中的一个关键字，它用于暂停一个协程（coroutine）的执行，直到其等待的异步操作完成。`await` 表达式会交出程序的控制权，允许事件循环（event loop）去执行其他的任务。当等待的异步操作完成后，事件循环会恢复该协程的执行。

简单来说，`await` 就是告诉程序：“嘿，这个操作需要一些时间，你先去忙别的，等它好了再叫我回来继续。”

```python
import asyncio

async def say_after(delay, what):
    await asyncio.sleep(delay)
    print(what)

async def main():
    print("程序开始")
    # 暂停main()的执行，直到say_after(1, 'hello')完成
    await say_after(1, 'hello')
    # 暂停main()的执行，直到say_after(2, 'world')完成
    await say_after(2, 'world')
    print("程序结束")

asyncio.run(main())
# 输出:
# 程序开始
# (等待1秒)
# hello
# (等待2秒)
# world
# 程序结束
```

## await能够wait 什么对象

`await` 关键字后面可以跟多种可等待对象（awaitable objects），主要包括以下三种：

1.  **协程对象（Coroutine Object）**: 直接调用一个 `async def` 函数返回的对象。
2.  **Task 对象**: 通过 `asyncio.create_task()` 或 `loop.create_task()` 创建的任务，用于并发执行协程。
3.  **Future 对象**: 一个代表未来某个时刻会产生结果的底层抽象。Task 是 Future 的一个子类。

```python
import asyncio

# 1. 等待一个协程对象
async def my_coroutine():
    print("Coroutine is running")
    await asyncio.sleep(1)
    return "Coroutine finished"

async def main_coro():
    result = await my_coroutine() # 直接等待协程
    print(result)

# 2. 等待一个Task对象
async def main_task():
    task = asyncio.create_task(my_coroutine())
    result = await task # 等待Task
    print(result)

# asyncio.run(main_coro())
asyncio.run(main_task())
```

## await 只能在async方法内使用

这是一个语法规定。`await` 关键字只能在由 `async def` 定义的异步函数内部使用。如果在普通函数（`def`）中使用 `await`，Python 解释器会抛出 `SyntaxError`。

这是因为 `await` 的机制依赖于事件循环来管理协程的暂停和恢复，而只有 `async` 函数才能被事件循环所调度。

```python
import asyncio

async def async_func():
    await asyncio.sleep(1) # 正确

def sync_func():
    # await asyncio.sleep(1) # 错误: SyntaxError: 'await' outside async function
    pass
```

## await 的2大作用

### 1. 等待async 方法完成才执行后面的代码

在一个异步函数内部，`await` 确保了代码的执行顺序。当程序遇到 `await some_async_operation()` 时，它会暂停当前函数的执行，直到 `some_async_operation` 完成，然后才会继续执行 `await` 后面的代码。这使得异步代码的逻辑可以像同步代码一样顺序地编写。

```python
import asyncio
import time

async def step_1():
    print("第一步开始")
    await asyncio.sleep(2)
    print("第一步完成")

async def step_2():
    print("第二步开始")
    await asyncio.sleep(1)
    print("第二步完成")

async def main():
    start_time = time.time()
    await step_1() # 等待 step_1 完成
    await step_2() # 然后再执行和等待 step_2 完成
    end_time = time.time()
    print(f"总耗时: {end_time - start_time:.2f} 秒")

asyncio.run(main())
# 输出:
# 第一步开始
# (等待2秒)
# 第一步完成
# 第二步开始
# (等待1秒)
# 第二步完成
# 总耗时: 3.00 秒
```

### 2. 遇到aysnc 方法的IO阻塞时会切换去执行同级时间循环中别的任务

这是 `await` 最核心的功能。当 `await` 等待一个 I/O 密集型操作（如网络请求、文件读写、`asyncio.sleep()`）时，它并不会像 `time.sleep()` 那样阻塞整个线程。相反，它会将控制权交还给事件循环。事件循环此时可以去检查是否有其他已经就绪的任务，并执行它们。这就是所谓的“协作式多任务”。

```python
import asyncio
import time

async def task_a():
    print("任务A开始，准备等待2秒")
    await asyncio.sleep(2)
    print("任务A结束")

async def task_b():
    print("任务B开始，准备等待1秒")
    await asyncio.sleep(1)
    print("任务B结束")

async def main():
    start_time = time.time()
    # 使用 asyncio.gather 并发运行 task_a 和 task_b
    # 当 task_a await时，事件循环会切换到 task_b
    await asyncio.gather(task_a(), task_b())
    end_time = time.time()
    print(f"总耗时: {end_time - start_time:.2f} 秒")

asyncio.run(main())
# 输出:
# 任务A开始，准备等待2秒
# 任务B开始，准备等待1秒
# (等待1秒后)
# 任务B结束
# (再等待1秒后)
# 任务A结束
# 总耗时: 2.01 秒
```
在这个例子中，总耗时约等于最长的那个任务的耗时（2秒），而不是所有任务耗时之和（3秒），证明了任务是并发执行的。

## async 方法内可以有多个await 去等待多个asyns 方法

在一个 `async` 函数中，你可以串联多个 `await` 表达式。它们会按照代码的书写顺序依次执行。前一个 `await` 的异步操作必须完成后，后一个 `await` 才会开始。

这与使用 `asyncio.gather` 并发执行是不同的。串行 `await` 适用于有依赖关系的异步操作。

```python
import asyncio

async def get_data(source):
    print(f"开始从 {source} 获取数据...")
    await asyncio.sleep(1)
    print(f"完成从 {source} 获取数据")
    return f"Data from {source}"

async def process_data(data):
    print(f"开始处理数据: {data}...")
    await asyncio.sleep(0.5)
    print(f"完成处理数据: {data}")
    return f"Processed {data}"

async def main():
    # 串行执行：获取数据 -> 处理数据
    data = await get_data("API 1")
    processed_data = await process_data(data)
    print(f"最终结果: {processed_data}")

asyncio.run(main())
# 输出:
# 开始从 API 1 获取数据...
# (等待1秒)
# 完成从 API 1 获取数据
# 开始处理数据: Data from API 1...
# (等待0.5秒)
# 完成处理数据: Data from API 1
# 最终结果: Processed Data from API 1
```

## 总结

- `await` 是一个关键字，用于在 `async def` 函数中调用和等待可等待对象（协程、Task、Future）。
- `await` 的核心作用是暂停当前协程，将控制权交还给事件循环，以便执行其他任务，从而实现非阻塞的并发。
- `await` 保证了在同一个协程内部，代码是按顺序执行的，使得异步逻辑更易于理解和编写。
- `await` 只能在 `async` 函数中使用，这是其与事件循环协作的基础。
- 多个 `await` 串行执行，适用于有前后依赖的异步操作；若要并发执行无依赖的操作，应使用 `asyncio.gather` 或 `asyncio.create_task`。
