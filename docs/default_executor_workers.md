# `run_in_executor` 的默认线程池有多少个 Worker？

这是一个在 `asyncio` 中混合使用阻塞代码时非常关键的问题。当我们调用 `loop.run_in_executor(None, ...)` 时，`asyncio` 会使用一个默认的 `ThreadPoolExecutor`。那么，这个默认的线程池到底有多大呢？

**简短的答案**：默认的 `max_workers` 数量是 **`min(32, os.cpu_count() + 4)`**。

---

## 公式详解

让我们来分解这个公式：`min(32, os.cpu_count() + 4)`

1.  **`os.cpu_count()`**:
    -   这个函数返回你的计算机上可用的 CPU 核心数。例如，在一台 8 核的机器上，它会返回 `8`。

2.  **`+ 4`**:
    -   这是一个为 **I/O 密集型任务** 设计的经验值。`ThreadPoolExecutor` 的主要应用场景是运行那些会因等待网络、磁盘等 I/O 操作而阻塞的任务。
    -   `+ 4` 的逻辑是，即使有与 CPU 核心数相等的线程正在忙于（理论上的）计算，也至少还有 4 个额外的线程可以用来处理那些正在等待 I/O 的任务，从而提高并发度。

3.  **`min(32, ...)`**:
    -   这是一个**保护性上限**。在拥有非常多核心的服务器（例如 64 核或 128 核）上，`os.cpu_count() + 4` 可能会得出一个非常大的数字。
    -   创建过多的线程本身会消耗内存资源，并且大量的线程切换（Context Switching）也会带来性能开销。因此，Python 设定了一个 `32` 的合理上限，以防止在默认情况下创建过多的线程。

**总结**：这个公式旨在提供一个在大多数常见场景下都表现良好的、无需手动配置的“明智默认值”。

---

## 代码验证

我们可以通过一个简单的例子来验证和观察这个行为。

```python
import asyncio
import os
import time
import threading

# 一个阻塞函数，用于模拟工作
def blocking_task(duration):
    thread_name = threading.current_thread().name
    print(f"[{thread_name}] - Task started, will run for {duration}s.")
    time.sleep(duration)
    print(f"[{thread_name}] - Task finished.")
    return duration

async def main():
    loop = asyncio.get_running_loop()
    
    # 计算并打印默认的 worker 数量
    cpu_cores = os.cpu_count() or 1 # os.cpu_count() 可能返回 None
    default_workers = min(32, cpu_cores + 4)
    print(f"Machine has {cpu_cores} CPU cores.")
    print(f"Default ThreadPoolExecutor workers: min(32, {cpu_cores} + 4) = {default_workers}\n")

    # 提交比 worker 数量更多的任务，以观察线程复用
    num_tasks = default_workers + 2
    print(f"Submitting {num_tasks} tasks to the default executor...")
    
    # 使用 loop.run_in_executor(None, ...)
    tasks = [loop.run_in_executor(None, blocking_task, 2) for _ in range(num_tasks)]
    
    results = await asyncio.gather(*tasks)
    print(f"\nAll tasks completed. Results: {results}")

# 运行主协程
asyncio.run(main())
```

### 预期输出

假设你的机器有 8 个 CPU 核心，那么默认的 worker 数将是 `min(32, 8 + 4) = 12`。

```bash
Machine has 8 CPU cores.
Default ThreadPoolExecutor workers: min(32, 8 + 4) = 12

Submitting 14 tasks to the default executor...
[ThreadPoolExecutor-0_0] - Task started, will run for 2s.
[ThreadPoolExecutor-0_1] - Task started, will run for 2s.
[ThreadPoolExecutor-0_2] - Task started, will run for 2s.
[ThreadPoolExecutor-0_3] - Task started, will run for 2s.
[ThreadPoolExecutor-0_4] - Task started, will run for 2s.
[ThreadPoolExecutor-0_5] - Task started, will run for 2s.
[ThreadPoolExecutor-0_6] - Task started, will run for 2s.
[ThreadPoolExecutor-0_7] - Task started, will run for 2s.
[ThreadPoolExecutor-0_8] - Task started, will run for 2s.
[ThreadPoolExecutor-0_9] - Task started, will run for 2s.
[ThreadPoolExecutor-0_10] - Task started, will run for 2s.
[ThreadPoolExecutor-0_11] - Task started, will run for 2s.
# --- 等待2秒后 ---
[ThreadPoolExecutor-0_0] - Task finished.
[ThreadPoolExecutor-0_0] - Task started, will run for 2s.  # 线程被复用
[ThreadPoolExecutor-0_1] - Task finished.
[ThreadPoolExecutor-0_1] - Task started, will run for 2s.  # 线程被复用
... (以此类推)

All tasks completed. Results: [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
```
从输出中可以看到，程序会立即启动 12 个任务，每个任务在一个独立的线程中运行。当这批任务中的任何一个完成后，它所占用的线程就会被释放并立即被用来执行队列中等待的下一个任务（第13个和第14个任务）。

---

## 何时需要覆盖默认值？

虽然默认值很方便，但在某些情况下你可能需要手动创建一个 `ThreadPoolExecutor` 实例来覆盖它：

1.  **大量高并发 I/O**：如果你的应用需要同时处理数百个网络连接，默认的 worker 数可能不够，导致请求排队。此时你可能需要一个更大的线程池。
2.  **资源限制**：在内存受限的环境中，你可能希望减小线程池的大小，因为每个线程都会消耗一定的内存。
3.  **共享线程池**：如果应用的不同部分都需要在后台执行阻塞任务，创建一个共享的、统一配置的线程池会是更好的做法。

在这种情况下，你可以这样做：

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

# ...

async def main():
    loop = asyncio.get_running_loop()
    
    # 手动创建一个线程池
    with ThreadPoolExecutor(max_workers=50) as custom_executor:
        await loop.run_in_executor(custom_executor, blocking_task, 5)
