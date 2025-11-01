## 协程的意义
简单来讲， 协程能让程序在**单线程**的情况下， 如果遇到IO（只要是网络IO和磁盘IO）时能CPU自动去做别的事情而不会干等IO结束。

更简单地讲， 协程无非就是让多个IO同时执行！
这就是协程提高并发能力的机制， 而这个机制与多线程的注意区别是协程几乎无需额外的cpu资源开销！
## 网络IO的例子
下面会以一个实际的网络IO 体验协程对比同步函数的优势。


## 准备一个计算时间开销的注解（decorator）

src/decorators/time_decorator.py
```python

import src.configs.config
from loguru import logger
import time
import functools
import asyncio

from inspect import iscoroutinefunction


def log_execution_time(func):
    """
    A decorator that logs the start time, end time, and elapsed time of a function's execution
    using the logging module. Supports both synchronous and asynchronous functions.
    """
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        logger.info(f"Function '{func.__name__}' started with args: {args}, kwargs: {kwargs}")
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.info(f"Function '{func.__name__}' finished with args: {args}, kwargs: {kwargs}. Elapsed time: {elapsed_time:.4f} seconds")
        return result

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        logger.info(f"Function '{func.__name__}' started with args: {args}, kwargs: {kwargs}")
        result = await func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.info(f"Function '{func.__name__}' finished with args: {args}, kwargs: {kwargs}. Elapsed time: {elapsed_time:.4f} seconds")
        return result

    if iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

```

## 准备3个下载文件
由于我家里网络较好， 我准备了3个网络资源， 每个都在500mb以上，每个文件下载时间在50s左右

```python
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
```
## 编写同步方式的下载函数


其中 download_file就是核心函数， 而sync_files 会同步地（顺序地） 调用download_file 3次
```python
@log_execution_time
def download_file(url, save_path):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    file_name = os.path.basename(urlparse(url).path)
    save_path = os.path.join(save_path, file_name)
    
    with open(save_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    logger.info(f"Downloaded file from {url} to {save_path}")

@log_execution_time
def sync_files(urls, save_path):
   for url in urls:
         download_file(url, save_path)

sync_files(list_url, "/tmp/")
```
```
2025-11-01 21:15:28.366 | INFO     | src.decorators.time_decorator:sync_wrapper:19 - Function 'sync_files' started with args: (['https://download.microsoft.com/download/8/1/d/81d1f546-f951-45c5-964d-56bdbd758ba4/w2k3sp2_3959_usa_x64fre_spcd.iso', 'https://download.microsoft.com/download/5/9/7/59797dff-d8eb-4f46-9319-ea8326141ee9/w2k3sp2_3959_jpn_x64fre_spcd.iso', 'https://download.microsoft.com/download/8/8/0/880bca75-79dd-466a-927d-1abf1f5454b0/PBIDesktopSetup_x64.exe'], '/tmp/'), kwargs: {}
2025-11-01 21:15:28.367 | INFO     | src.decorators.time_decorator:sync_wrapper:19 - Function 'download_file' started with args: ('https://download.microsoft.com/download/8/1/d/81d1f546-f951-45c5-964d-56bdbd758ba4/w2k3sp2_3959_usa_x64fre_spcd.iso', '/tmp/'), kwargs: {}
2025-11-01 21:16:03.925 | INFO     | __main__:download_file:12 - Downloaded file from https://download.microsoft.com/download/8/1/d/81d1f546-f951-45c5-964d-56bdbd758ba4/w2k3sp2_3959_usa_x64fre_spcd.iso to /tmp/w2k3sp2_3959_usa_x64fre_spcd.iso
2025-11-01 21:16:03.927 | INFO     | src.decorators.time_decorator:sync_wrapper:23 - Function 'download_file' finished with args: ('https://download.microsoft.com/download/8/1/d/81d1f546-f951-45c5-964d-56bdbd758ba4/w2k3sp2_3959_usa_x64fre_spcd.iso', '/tmp/'), kwargs: {}. Elapsed time: 35.5595 seconds
2025-11-01 21:16:03.927 | INFO     | src.decorators.time_decorator:sync_wrapper:19 - Function 'download_file' started with args: ('https://download.microsoft.com/download/5/9/7/59797dff-d8eb-4f46-9319-ea8326141ee9/w2k3sp2_3959_jpn_x64fre_spcd.iso', '/tmp/'), kwargs: {}
2025-11-01 21:16:33.204 | INFO     | __main__:download_file:12 - Downloaded file from https://download.microsoft.com/download/5/9/7/59797dff-d8eb-4f46-9319-ea8326141ee9/w2k3sp2_3959_jpn_x64fre_spcd.iso to /tmp/w2k3sp2_3959_jpn_x64fre_spcd.iso
2025-11-01 21:16:33.206 | INFO     | src.decorators.time_decorator:sync_wrapper:23 - Function 'download_file' finished with args: ('https://download.microsoft.com/download/5/9/7/59797dff-d8eb-4f46-9319-ea8326141ee9/w2k3sp2_3959_jpn_x64fre_spcd.iso', '/tmp/'), kwargs: {}. Elapsed time: 29.2787 seconds
2025-11-01 21:16:33.207 | INFO     | src.decorators.time_decorator:sync_wrapper:19 - Function 'download_file' started with args: ('https://download.microsoft.com/download/8/8/0/880bca75-79dd-466a-927d-1abf1f5454b0/PBIDesktopSetup_x64.exe', '/tmp/'), kwargs: {}
2025-11-01 21:17:27.737 | INFO     | __main__:download_file:12 - Downloaded file from https://download.microsoft.com/download/8/8/0/880bca75-79dd-466a-927d-1abf1f5454b0/PBIDesktopSetup_x64.exe to /tmp/PBIDesktopSetup_x64.exe
2025-11-01 21:17:27.739 | INFO     | src.decorators.time_decorator:sync_wrapper:23 - Function 'download_file' finished with args: ('https://download.microsoft.com/download/8/8/0/880bca75-79dd-466a-927d-1abf1f5454b0/PBIDesktopSetup_x64.exe', '/tmp/'), kwargs: {}. Elapsed time: 54.5320 seconds
2025-11-01 21:17:27.739 | INFO     | src.decorators.time_decorator:sync_wrapper:23 - Function 'sync_files' finished with args: (['https://download.microsoft.com/download/8/1/d/81d1f546-f951-45c5-964d-56bdbd758ba4/w2k3sp2_3959_usa_x64fre_spcd.iso', 'https://download.microsoft.com/download/5/9/7/59797dff-d8eb-4f46-9319-ea8326141ee9/w2k3sp2_3959_jpn_x64fre_spcd.iso', 'https://download.microsoft.com/download/8/8/0/880bca75-79dd-466a-927d-1abf1f5454b0/PBIDesktopSetup_x64.exe'], '/tmp/'), kwargs: {}. Elapsed time: 119.3727 seconds
```
## 同步方法的效果
从日志看出 3个文件是顺序下载的， 所花费的时间分别是35s, 29s, 55s， 所以这个function 在网络IO的等待时间就是35+29+55 = 119s 总的开销也是119s
## 2. 编写异步并发下载

其中download_file_async 就是核心的异步下载函数， 而在async_files_concurrent 中构造了一个event loop， 交给其来管理协程
```python
import aiohttp
import asyncio

@log_execution_time
async def download_file_async(url, save_path):
    file_name = os.path.basename(urlparse(url).path)
    full_save_path = os.path.join(save_path, file_name)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                with open(full_save_path, 'wb') as f:
                    while True:
                        chunk = await response.content.read(8192) # even read() is not a async function, but it return a Future object, so it could be awaited
                        if not chunk:
                            break
                        f.write(chunk)
                logger.info(f"Downloaded file from {url} to {full_save_path}")
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")

@log_execution_time
async def async_files_concurrent(urls, save_path):
   tasks = [download_file_async(url, save_path) for url in urls]
   await asyncio.gather(*tasks)
```
```python
# 使用 asyncio.gather 实现并发下载
await async_files_concurrent(list_url, "/tmp/")
```
```
2025-11-01 21:18:57.848 | INFO     | src.decorators.time_decorator:async_wrapper:29 - Function 'async_files_concurrent' started with args: (['https://download.microsoft.com/download/8/1/d/81d1f546-f951-45c5-964d-56bdbd758ba4/w2k3sp2_3959_usa_x64fre_spcd.iso', 'https://download.microsoft.com/download/5/9/7/59797dff-d8eb-4f46-9319-ea8326141ee9/w2k3sp2_3959_jpn_x64fre_spcd.iso', 'https://download.microsoft.com/download/8/8/0/880bca75-79dd-466a-927d-1abf1f5454b0/PBIDesktopSetup_x64.exe'], '/tmp/'), kwargs: {}
2025-11-01 21:18:57.849 | INFO     | src.decorators.time_decorator:async_wrapper:29 - Function 'download_file_async_fixed' started with args: ('https://download.microsoft.com/download/8/1/d/81d1f546-f951-45c5-964d-56bdbd758ba4/w2k3sp2_3959_usa_x64fre_spcd.iso', '/tmp/'), kwargs: {}
2025-11-01 21:18:57.850 | INFO     | src.decorators.time_decorator:async_wrapper:29 - Function 'download_file_async_fixed' started with args: ('https://download.microsoft.com/download/5/9/7/59797dff-d8eb-4f46-9319-ea8326141ee9/w2k3sp2_3959_jpn_x64fre_spcd.iso', '/tmp/'), kwargs: {}
2025-11-01 21:18:57.850 | INFO     | src.decorators.time_decorator:async_wrapper:29 - Function 'download_file_async_fixed' started with args: ('https://download.microsoft.com/download/8/8/0/880bca75-79dd-466a-927d-1abf1f5454b0/PBIDesktopSetup_x64.exe', '/tmp/'), kwargs: {}
2025-11-01 21:20:00.100 | INFO     | __main__:download_file_async_fixed:19 - Downloaded file from https://download.microsoft.com/download/8/1/d/81d1f546-f951-45c5-964d-56bdbd758ba4/w2k3sp2_3959_usa_x64fre_spcd.iso to /tmp/w2k3sp2_3959_usa_x64fre_spcd.iso
2025-11-01 21:20:00.101 | INFO     | src.decorators.time_decorator:async_wrapper:33 - Function 'download_file_async_fixed' finished with args: ('https://download.microsoft.com/download/8/1/d/81d1f546-f951-45c5-964d-56bdbd758ba4/w2k3sp2_3959_usa_x64fre_spcd.iso', '/tmp/'), kwargs: {}. Elapsed time: 62.2524 seconds
2025-11-01 21:20:16.983 | INFO     | __main__:download_file_async_fixed:19 - Downloaded file from https://download.microsoft.com/download/5/9/7/59797dff-d8eb-4f46-9319-ea8326141ee9/w2k3sp2_3959_jpn_x64fre_spcd.iso to /tmp/w2k3sp2_3959_jpn_x64fre_spcd.iso
2025-11-01 21:20:16.985 | INFO     | src.decorators.time_decorator:async_wrapper:33 - Function 'download_file_async_fixed' finished with args: ('https://download.microsoft.com/download/5/9/7/59797dff-d8eb-4f46-9319-ea8326141ee9/w2k3sp2_3959_jpn_x64fre_spcd.iso', '/tmp/'), kwargs: {}. Elapsed time: 79.1353 seconds
2025-11-01 21:20:32.624 | INFO     | __main__:download_file_async_fixed:19 - Downloaded file from https://download.microsoft.com/download/8/8/0/880bca75-79dd-466a-927d-1abf1f5454b0/PBIDesktopSetup_x64.exe to /tmp/PBIDesktopSetup_x64.exe
2025-11-01 21:20:32.625 | INFO     | src.decorators.time_decorator:async_wrapper:33 - Function 'download_file_async_fixed' finished with args: ('https://download.microsoft.com/download/8/8/0/880bca75-79dd-466a-927d-1abf1f5454b0/PBIDesktopSetup_x64.exe', '/tmp/'), kwargs: {}. Elapsed time: 94.7745 seconds
2025-11-01 21:20:32.625 | INFO     | src.decorators.time_decorator:async_wrapper:33 - Function 'async_files_concurrent' finished with args: (['https://download.microsoft.com/download/8/1/d/81d1f546-f951-45c5-964d-56bdbd758ba4/w2k3sp2_3959_usa_x64fre_spcd.iso', 'https://download.microsoft.com/download/5/9/7/59797dff-d8eb-4f46-9319-ea8326141ee9/w2k3sp2_3959_jpn_x64fre_spcd.iso', 'https://download.microsoft.com/download/8/8/0/880bca75-79dd-466a-927d-1abf1f5454b0/PBIDesktopSetup_x64.exe'], '/tmp/'), kwargs: {}. Elapsed time: 94.7776 seconds
```
# 异步下载的效果
1. 首先，从日志看出，  3个文件几乎同时开始下载
2. 因为我的电脑总的带宽有限， 3个文件的下载时间都分别更长了， 是 62s ，79s, 95s
3. 但是程序是同时下载3个文件的， 所以总的网络IO 等待时间就是95s 最长的那个。
4. 程序的总时间开销就是95s 对比 同步下载的方法优势明显

---
## 内容总结

本文档通过一个下载文件的具体实例，深入浅出地展示了Python中**同步**与**异步并发**编程在处理IO密集型任务时的核心差异和性能表现。

**核心要点：**

1.  **同步执行**：
    *   采用传统的`requests`库进行文件下载，任务严格按照顺序执行，即一个文件下载完成后，下一个才能开始。
    *   **性能瓶颈**：总耗时是所有单个任务耗时的简单累加。在等待网络IO时，CPU处于闲置状态，资源利用率低。

2.  **异步并发执行**：
    *   采用`aiohttp`和`asyncio`库，通过`async/await`语法将下载任务定义为协程。
    *   关键在于使用`asyncio.gather()`将所有下载任务提交给事件循环，从而实现并发执行。所有下载任务几乎同时启动，CPU可以在等待一个任务的IO时，切换到另一个任务继续工作。
    *   **性能优势**：总耗时不再是时间的累加，而是取决于耗时最长的那个任务。从实验结果看，总时间从同步的**119秒**缩短到了异步的**95秒**，效率提升显著。

**结论：**

对于网络请求、文件读写等IO密集型场景，异步编程能够极大地提升程序的执行效率和资源利用率。它通过协程在单线程内实现了任务的并发调度，避免了无谓的等待，是构建高性能网络应用的关键技术。
