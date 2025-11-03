# python 异步编程 -- 理解concurrent.futures.Future 对象

在上一篇文章 [python 异步编程 -- 理解asyncio里的Future 对象](https://blog.csdn.net/nvd11/article/details/154315427?spm=1011.2415.3001.5331) 中，我们介绍了 `asyncio.Future` 对象。但在文章的最后一个例子里，我们其实引用了 `concurrent.futures` 这个包，它里面也有一个 `Future` 对象。

本文就将详细介绍 `concurrent.futures.Future` 对象，以及它如何在 `asyncio` 的世界中扮演关键的“桥梁”角色。

## 什么是python的concurrent.futures 框架

`concurrent.futures` 是 Python 标准库中一个用于异步执行可调用对象（callable）的高级模块。它提供了两种主要的执行器（Executor）：

1.  **`ThreadPoolExecutor`**：使用**多线程**来并发执行任务。它非常适合于 I/O 密集型任务（如网络请求、文件读写），因为在等待 I/O 时，线程可以释放 GIL（全局解释器锁），让其他线程运行。
2.  **`ProcessPoolExecutor`**：使用**多进程**来并行执行任务。它能够绕开 GIL 的限制，因此非常适合于 CPU 密集型任务（如大数据计算、图像处理），因为它可以在多个 CPU 核心上真正地并行运行。

这个框架的核心思想是：你将一个任务（一个函数和它的参数）提交给一个“池”（线程池或进程池），池会负责调度一个“工人”（线程或进程）去执行它。这个提交操作会**立即**返回一个 `concurrent.futures.Future` 对象，而任务则在后台异步执行。

### 简单例子

```python
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import time

def func(value):
    print(f"Function called with value: {value}")
    time.sleep(2)
    print(f"Function ended with value: {value}")
    return value

# 创建一个拥有5个工人的线程池
thread_pool = ThreadPoolExecutor(max_workers=5)

# 注意：我们提交了10个任务，但池中只有5个工人
for i in range(10):
    # submit() 会立即返回一个 concurrent.futures.Future 对象
    future = thread_pool.submit(func, i)
    print(f"Submitted task {i}, future: {future}, type of future: {type(future)}")

# 在程序结束前，确保所有任务都已完成
thread_pool.shutdown(wait=True)
```

**Output:**
```bash
Submitted task 0, future: <Future at 0x... state=running>, type of future: <class 'concurrent.futures._base.Future'>
Function called with value: 0
Submitted task 1, future: <Future at 0x... state=running>, type of future: <class 'concurrent.futures._base.Future'>
Function called with value: 1
Submitted task 2, future: <Future at 0x... state=running>, type of future: <class 'concurrent.futures._base.Future'>
Function called with value: 2
Submitted task 3, future: <Future at 0x... state=running>, type of future: <class 'concurrent.futures._base.Future'>
Function called with value: 3
Submitted task 4, future: <Future at 0x... state=running>, type of future: <class 'concurrent.futures._base.Future'>
Function called with value: 4
Submitted task 5, future: <Future at 0x... state=pending>, type of future: <class 'concurrent.futures._base.Future'>
Submitted task 6, future: <Future at 0x... state=pending>, type of future: <class 'concurrent.futures._base.Future'>
Submitted task 7, future: <Future at 0x... state=pending>, type of future: <class 'concurrent.futures._base.Future'>
Submitted task 8, future: <Future at 0x... state=pending>, type of future: <class 'concurrent.futures._base.Future'>
Submitted task 9, future: <Future at 0x... state=pending>, type of future: <class 'concurrent.futures._base.Future'>
Function ended with value: 0
Function called with value: 5
Function ended with value: 1
Function called with value: 6
Function ended with value: 2
Function called with value: 7
Function ended with value: 3
Function called with value: 8
Function ended with value: 4
Function called with value: 9
Function ended with value: 5
Function ended with value: 6
Function ended with value: 7
Function ended with value: 8
Function ended with value: 9
```

### 代码解析

1.  我们创建了一个最多有5个线程的 `ThreadPoolExecutor`。
2.  循环提交了10个任务。`submit()` 是非阻塞的，它把任务放进队列后立刻返回一个 `concurrent.futures.Future` 对象。
3.  从输出可以看到，前5个任务（0-4）的状态是 `running`，因为池里有5个可用的工人线程。
4.  从第6个任务（5）开始，状态是 `pending`，因为5个工人都被占用了，新任务需要在队列里排队。
5.  当一个正在运行的任务（如 `func(0)`）完成后，它占用的工人线程就被释放了。线程池会立刻从队列里取出下一个等待的任务（`func(5)`）并开始执行。这个过程会一直持续，直到所有任务都完成。

## 什么是concurrent.futures.Future 对象

`concurrent.futures.Future` 对象与 `asyncio.Future` 在概念上非常相似：它都是一个**未来结果的占位符**。

但它的上下文完全不同：
-   它代表的是一个在**线程池或进程池**中执行的任务的结果。
-   它**不是一个可等待对象（awaitable）**。你不能在 `async def` 函数中 `await` 一个 `concurrent.futures.Future`。
-   你需要使用它的 `.result()` 方法来**阻塞式地**获取结果，或者使用 `.add_done_callback()` 来注册一个在任务完成时触发的回调函数。

## 为何我们在异步编程里还需要了解concurrent.futures.Future 对象？

这是一个核心问题。`asyncio` 非常适合处理非阻塞的 I/O 操作，但在一个真实的项目中，我们经常会遇到一些无法避免的**阻塞操作**。例如：

-   一个老旧的、不支持 `asyncio` 的数据库驱动（如某些版本的 `MySQLdb`）。
-   一个需要进行大量计算的 CPU 密集型函数。
-   调用一个会阻塞的第三方库。

如果在 `async` 函数中直接调用这些阻塞代码，整个 `asyncio` 事件循环都会被卡住，所有其他的并发任务都会被暂停，从而失去异步的优势。

这时，`concurrent.futures` 就成了我们的救星。我们可以把这些阻塞代码扔到另一个线程或进程中去执行，从而让事件循环保持流畅。而 `asyncio` 提供了一个完美的桥梁——`loop.run_in_executor()`——来帮我们完成这件事。这个桥梁正是通过连接两种 `Future` 对象来工作的。

### 简单例子:

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time

# 一个普通的、阻塞的同步函数
def func(value):
    print(f"Function called with value: {value} in a separate thread")
    time.sleep(2)
    print(f"Function ended with value: {value}")
    return value

async def main():
    loop = asyncio.get_running_loop()
    print("Starting main coroutine in asyncio event loop.")

    with ThreadPoolExecutor(max_workers=5) as thread_pool:
        tasks = []
        for i in range(10):
            # loop.run_in_executor() 是这里的关键！
            # 它返回一个可以被 await 的 asyncio.Future 对象
            future = loop.run_in_executor(thread_pool, func, i)
            tasks.append(future)
            print(f"Submitted task {i}, future type: {type(future)}")
        
        print("\nWaiting for all asyncio.Future objects to complete...")
        results = await asyncio.gather(*tasks)
        print("\nAll tasks completed, results:", results)

asyncio.run(main())
```

**Output:**
```bash
Starting main coroutine in asyncio event loop.
Submitted task 0, future type: <class '_asyncio.Future'>
Submitted task 1, future type: <class '_asyncio.Future'>
Submitted task 2, future type: <class '_asyncio.Future'>
Submitted task 3, future type: <class '_asyncio.Future'>
Submitted task 4, future type: <class '_asyncio.Future'>
Submitted task 5, future type: <class '_asyncio.Future'>
Submitted task 6, future type: <class '_asyncio.Future'>
Submitted task 7, future type: <class '_asyncio.Future'>
Submitted task 8, future type: <class '_asyncio.Future'>
Submitted task 9, future type: <class '_asyncio.Future'>

Waiting for all asyncio.Future objects to complete...
Function called with value: 0 in a separate thread
Function called with value: 1 in a separate thread
Function called with value: 2 in a separate thread
Function called with value: 3 in a separate thread
Function called with value: 4 in a separate thread
Function ended with value: 0
Function called with value: 5 in a separate thread
Function ended with value: 1
Function called with value: 6 in a separate thread
Function ended with value: 2
Function called with value: 7 in a separate thread
Function ended with value: 3
Function called with value: 8 in a separate thread
Function ended with value: 4
Function called with value: 9 in a separate thread
Function ended with value: 5
Function ended with value: 6
Function ended with value: 7
Function ended with value: 8
Function ended with value: 9

All tasks completed, results: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
```

### 代码解析

这段代码完美地展示了 `asyncio` 和 `concurrent.futures` 的协作：

1.  `loop.run_in_executor(thread_pool, func, i)` 是魔法发生的地方。它做了几件事：
    -   它告诉 `thread_pool` 去执行阻塞函数 `func(i)`。
    -   它**立即返回一个 `asyncio.Future` 对象**，而不是 `concurrent.futures.Future`。
    -   在内部，它创建了一个 `concurrent.futures.Future` 来追踪线程中的任务，并将这个 `asyncio.Future` 与之关联。
2.  因为 `run_in_executor` 返回的是一个 `asyncio.Future`，所以我们可以在 `main` 协程中 `await` 它（通过 `asyncio.gather`）。
3.  当后台线程中的 `func(i)` 执行完毕并返回结果时，`concurrent.futures.Future` 完成。
4.  事件循环检测到这一点，并自动将结果复制到与之关联的 `asyncio.Future` 中，将其标记为完成。
5.  `asyncio.gather` 最终收集到所有 `asyncio.Future` 的结果，程序结束。

通过这个机制，我们成功地在不阻塞事件循环的前提下，并发地执行了10个阻塞函数。

## `asyncio.get_running_loop().run_in_executor()` 介绍

`run_in_executor(executor, func, *args)` 是事件循环的一个核心方法，用于将阻塞代码委托给执行器。

-   **`executor`**:
    -   可以是一个 `ThreadPoolExecutor` 或 `ProcessPoolExecutor` 实例。
    -   如果传入 `None`，`run_in_executor` 会使用事件循环**默认的 `ThreadPoolExecutor`**。这是一个非常方便的快捷方式，你甚至不需要自己创建线程池。
-   **`func`**: 要执行的阻塞函数。
-   **`*args`**: 传递给 `func` 的参数。

所以，如果你只是想简单地将一个阻塞调用扔到后台线程，可以这样写：
```python
# 无需手动创建 ThreadPoolExecutor
future = loop.run_in_executor(None, blocking_function, arg1, arg2)
result = await future
```



## 回归开始我们下载文件的例子

在python 异步编程文章的初期
在文章[python异步编程 -协程的实际意义](https://blog.csdn.net/nvd11/article/details/154257037?spm=1011.2415.3001.5331)

为了实现异步下载3个文件， 我们不得不切换http框架由requests 换成 aiohttp
因为requests 不支持 async..

现在 有了 concurrent.futures.Future 这个桥梁， 我们有机会在没有aiohttp的情形下，只用requests也能实现异步下载

例子：

```python
import asyncio
import os
import requests
from urllib.parse import urlparse
from loguru import logger
from src.decorators.time_decorator import log_execution_time

list_url = [
    "https://download.microsoft.com/download/8/1/d/81d1f546-f951-45c5-964d-56bdbd758ba4/w2k3sp2_3959_usa_x64fre_spcd.iso",
    "https://download.microsoft.com/download/5/9/7/59797dff-d8eb-4f46-9319-ea8326141ee9/w2k3sp2_3959_jpn_x64fre_spcd.iso",
    "https://download.microsoft.com/download/8/8/0/880bca75-79dd-466a-927d-1abf1f5454b0/PBIDesktopSetup_x64.exe"
]

@log_execution_time
async def download_file_with_requests(url, save_path):
    loop = asyncio.get_running_loop()

    # as lib requests does not supports async.. we need to run it in executor, 
    # to convert it to async Future(actually it will be run in a sepreated thread
    # the worker number of default thread pool is min(32, os.cpu_count() + 4)
    future = loop.run_in_executor(None, requests.get, url)

    response = await future
    file_name = os.path.basename(urlparse(url).path)
    save_path = os.path.join(save_path, file_name)
    
    with open(save_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    logger.info(f"Downloaded file from {url} to {save_path}")



@log_execution_time
async def async_files_concurrent(urls, save_path):
   tasks = [download_file_with_requests(url, save_path) for url in urls]
   await asyncio.gather(*tasks)


if __name__ == "__main__":
    save_path = "/tmp/"
    os.makedirs(save_path, exist_ok=True)
    asyncio.run(async_files_concurrent(list_url, save_path))
```
output

```bash

(.venv) gateman@MoreFine-S500: python-poc$ /home/gateman/projects/github/python-poc/.venv/bin/python /home/gateman/projects/github/python-poc/src/poc/concurrent/combine_async_concurrent.py
project_path is /home/gateman/projects/github/python-poc
2025-11-03 00:08:11.519 | INFO     | src.configs.config:<module>:21 - basic setup done
2025-11-03 00:08:11.520 | INFO     | src.configs.config:<module>:33 - Environment variable AIzaSxxxxxxx.... found, using value from environment.
2025-11-03 00:08:11.520 | INFO     | src.configs.config:<module>:37 - all configs loaded
2025-11-03 00:08:11.520 | INFO     | src.configs.proxy_config:set_proxy:5 - Setting up proxy configuration.
2025-11-03 00:08:11.520 | INFO     | src.configs.config:<module>:41 - proxy setup done
2025-11-03 00:08:11.521 | INFO     | src.decorators.time_decorator:async_wrapper:29 - Function 'async_files_concurrent' started with args: (['https://download.microsoft.com/download/8/1/d/81d1f546-f951-45c5-964d-56bdbd758ba4/w2k3sp2_3959_usa_x64fre_spcd.iso', 'https://download.microsoft.com/download/5/9/7/59797dff-d8eb-4f46-9319-ea8326141ee9/w2k3sp2_3959_jpn_x64fre_spcd.iso', 'https://download.microsoft.com/download/8/8/0/880bca75-79dd-466a-927d-1abf1f5454b0/PBIDesktopSetup_x64.exe'], '/tmp/'), kwargs: {}
2025-11-03 00:08:11.521 | INFO     | src.decorators.time_decorator:async_wrapper:29 - Function 'download_file_with_requests' started with args: ('https://download.microsoft.com/download/8/1/d/81d1f546-f951-45c5-964d-56bdbd758ba4/w2k3sp2_3959_usa_x64fre_spcd.iso', '/tmp/'), kwargs: {}
2025-11-03 00:08:11.522 | INFO     | src.decorators.time_decorator:async_wrapper:29 - Function 'download_file_with_requests' started with args: ('https://download.microsoft.com/download/5/9/7/59797dff-d8eb-4f46-9319-ea8326141ee9/w2k3sp2_3959_jpn_x64fre_spcd.iso', '/tmp/'), kwargs: {}
2025-11-03 00:08:11.522 | INFO     | src.decorators.time_decorator:async_wrapper:29 - Function 'download_file_with_requests' started with args: ('https://download.microsoft.com/download/8/8/0/880bca75-79dd-466a-927d-1abf1f5454b0/PBIDesktopSetup_x64.exe', '/tmp/'), kwargs: {}
2025-11-03 00:13:44.825 | INFO     | __main__:download_file_with_requests:33 - Downloaded file from https://download.microsoft.com/download/8/8/0/880bca75-79dd-466a-927d-1abf1f5454b0/PBIDesktopSetup_x64.exe to /tmp/PBIDesktopSetup_x64.exe
2025-11-03 00:13:44.825 | INFO     | src.decorators.time_decorator:async_wrapper:33 - Function 'download_file_with_requests' finished with args: ('https://download.microsoft.com/download/8/8/0/880bca75-79dd-466a-927d-1abf1f5454b0/PBIDesktopSetup_x64.exe', '/tmp/'), kwargs: {}. Elapsed time: 333.3032 seconds
2025-11-03 00:14:22.302 | INFO     | __main__:download_file_with_requests:33 - Downloaded file from https://download.microsoft.com/download/8/1/d/81d1f546-f951-45c5-964d-56bdbd758ba4/w2k3sp2_3959_usa_x64fre_spcd.iso to /tmp/w2k3sp2_3959_usa_x64fre_spcd.iso
2025-11-03 00:14:22.302 | INFO     | src.decorators.time_decorator:async_wrapper:33 - Function 'download_file_with_requests' finished with args: ('https://download.microsoft.com/download/8/1/d/81d1f546-f951-45c5-964d-56bdbd758ba4/w2k3sp2_3959_usa_x64fre_spcd.iso', '/tmp/'), kwargs: {}. Elapsed time: 370.7812 seconds
2025-11-03 00:14:39.506 | INFO     | __main__:download_file_with_requests:33 - Downloaded file from https://download.microsoft.com/download/5/9/7/59797dff-d8eb-4f46-9319-ea8326141ee9/w2k3sp2_3959_jpn_x64fre_spcd.iso to /tmp/w2k3sp2_3959_jpn_x64fre_spcd.iso
2025-11-03 00:14:39.507 | INFO     | src.decorators.time_decorator:async_wrapper:33 - Function 'download_file_with_requests' finished with args: ('https://download.microsoft.com/download/5/9/7/59797dff-d8eb-4f46-9319-ea8326141ee9/w2k3sp2_3959_jpn_x64fre_spcd.iso', '/tmp/'), kwargs: {}. Elapsed time: 387.9848 seconds
2025-11-03 00:14:39.527 | INFO     | src.decorators.time_decorator:async_wrapper:33 - Function 'async_files_concurrent' finished with args: (['https://download.microsoft.com/download/8/1/d/81d1f546-f951-45c5-964d-56bdbd758ba4/w2k3sp2_3959_usa_x64fre_spcd.iso', 'https://download.microsoft.com/download/5/9/7/59797dff-d8eb-4f46-9319-ea8326141ee9/w2k3sp2_3959_jpn_x64fre_spcd.iso', 'https://download.microsoft.com/download/8/8/0/880bca75-79dd-466a-927d-1abf1f5454b0/PBIDesktopSetup_x64.exe'], '/tmp/'), kwargs: {}. Elapsed time: 388.0062 seconds
```

<代码解析>
这段代码完美地展示了如何利用 `run_in_executor` 来包装一个不支持异步的库（`requests`），从而在 `asyncio` 程序中实现并发下载。

1.  **`download_file_with_requests` 函数**:
    -   这是一个 `async def` 函数，但它内部的核心操作 `requests.get(url)` 是一个**阻塞**的网络请求。
    -   关键的一行是 `future = loop.run_in_executor(None, requests.get, url)`。它将阻塞的 `requests.get` 操作扔到了后台的默认线程池中执行。
    -   函数立即获得一个可以 `await` 的 `asyncio.Future`。
    -   `response = await future` 会暂停 `download_file_with_requests` 的执行，但**不会阻塞事件循环**。事件循环此时可以去执行其他任务（比如启动另外两个文件的下载）。
    -   当后台线程中的 `requests.get` 完成后，`future` 得到结果（`response` 对象），`download_file_with_requests` 被唤醒并继续执行后续的文件写入操作。

2.  **`async_files_concurrent` 函数**:
    -   它创建了三个 `download_file_with_requests` 协程任务。
    -   `asyncio.gather(*tasks)` 会并发地启动这三个任务。由于每个任务内部的阻塞部分都被 `run_in_executor` 妥善处理了，这三个下载任务得以在不同的线程中**真正地并发进行**。

3.  **结果分析**:
    -   从日志的执行时间可以看出，三个下载任务的总耗时（388秒）约等于其中最长的那个任务的耗时（387秒），而不是三个任务耗时之和。这有力地证明了我们成功地将阻塞操作并发化了。
    -   这个例子展示了 `asyncio` 强大的整合能力：即使面对不支持异步的传统阻塞库，我们依然有办法将其无缝地集成到异步工作流中，而无需重写所有代码或替换整个技术栈。



## 本文总结

-   `concurrent.futures` 是 Python 用于**多线程和多进程**编程的高级框架，适合处理 I/O 密集型和 CPU 密集型任务。
-   `concurrent.futures.Future` 代表一个在线程/进程池中执行的任务的结果，它**不可被 `await`**。
-   `asyncio` 通过 `loop.run_in_executor()` 方法提供了与 `concurrent.futures` 框架的**桥梁**。
-   `run_in_executor()` 接收一个阻塞函数，在指定的执行器（线程或进程池）中运行它，并**返回一个可以被 `await` 的 `asyncio.Future`**。
-   这个机制是 `asyncio` 程序中处理**不可避免的阻塞代码**（如旧版库、CPU 密集计算）的标准和最佳实践，它能有效防止事件循环被阻塞。
