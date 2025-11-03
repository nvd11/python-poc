# python 异步编程 -- 理解asyncio里的Future 对象

## 什么是asyncio里的Future

在 `asyncio` 中，`Future` 是一个非常底层的“可等待”对象，它代表一个**未来某个时刻才会有的结果**。

你可以把 `Future` 想象成一个“占位符”或者一个“空的承诺盒子”。当你创建一个 `Future` 时，你得到的是一个空的盒子。这个盒子本身并不知道如何去获取它应该装的东西，它只是在那里静静地等待。直到有**别的代码**（比如一个任务、一个回调函数，甚至是另一个线程）显式地把结果放进这个盒子里（通过调用 `set_result()`）或者告诉它操作失败了（通过调用 `set_exception()`），这个 `Future` 的状态才会变为“完成”。

任何 `await` 这个 `Future` 的代码都会被暂停，直到这个盒子被填满为止。

## 与coroutine、task 的关系与区别

为了通俗地理解这三者的关系，我们用一个“餐厅点餐”的比喻：

-   **`Coroutine` (协程)**:
    -   **比喻**：一张**菜谱**。
    -   **解释**：它详细描述了制作一道菜（完成一个异步操作）的所有步骤，比如“先切菜（`await step1()`），再炒菜（`await step2()`）”。它本身只是一个静态的指令集，放在那里什么也不会发生。

-   **`Task` (任务)**:
    -   **比喻**：一位**厨师**。
    -   **解释**：厨师拿到了菜谱（`Coroutine`），并且**知道如何按照菜谱一步步做菜**。你把菜谱交给厨师（`create_task(coro)`），厨师就会立即开始在厨房（事件循环）里忙活起来，直到把菜做完。`Task` 是 `Future` 的一个子类，所以它也是一个“承诺盒子”，但它是一个“聪明的盒子”，因为它自己就知道如何去完成承诺（通过执行它包装的协程）。

-   **`Future` (未来)**:
    -   **比喻**：一个**空盘子**。
    -   **解释**：这个盘子被放在出餐口，它只负责等待盛放最终的菜肴。盘子**自己完全不知道菜是怎么做的**，它只是等待别人（比如厨师 `Task`，或者服务员 `callback`）把做好的菜放上来。`Future` 是一个更被动的角色，它为不同部分的代码提供了一个同步点。

**总结区别**：
-   `Task` **知道如何完成自己**（通过运行协程）。
-   `Future` **不知道如何完成自己**，它依赖外部代码来设置其结果。
-   `Task` 是 `Future` 的一个更具体、更高级的应用。在纯 `asyncio` 代码中，你打交道的绝大部分都是 `Task`。`Future` 更多地用在需要桥接 `asyncio` 和其他异步模式（如回调、线程）的底层场景。

## 第一个代码例子

```python
import asyncio

async def func1():
    print("Started func1")
   
    # 获取当前事件循环
    loop = asyncio.get_running_loop()

    # 创建一个 Future 对象，它处于 "pending" 状态
    future = loop.create_future()

    # 等待 future 完成。但永远等不到...
    await future

    # 这行代码永远不会被执行
    print("Done func1")

# 程序会永远挂起
asyncio.run(func1())
```

**Output:**
```bash
Started func1
(程序在此处挂起，光标闪烁)
```

**代码解析：这个例子为何会hang住？**

这个程序会永远挂起，原因非常直接：

1.  我们创建了一个 `future` 对象，它就像一个空的“承诺盒子”。
2.  `await future` 这行代码的意思是：“暂停我当前的执行，直到这个 `future` 盒子被填满（即状态变为 'done'）再唤醒我。”
3.  然而，在这段代码中，**没有任何地方**去完成这个 `future`。没有代码调用 `future.set_result()` 或 `future.set_exception()`。
4.  因此，`await future` 的等待将是永恒的。`func1` 协程被永久地挂起了，程序也就卡在了那里，永远不会打印 "Done func1"。

---

## 第二个例子：用一个 task 去更新一个 future的状态

```python
import asyncio
import time

async def http_call(fut: asyncio.Future):
    print(f"Starting HTTP call, will complete the future: {fut}")
    await asyncio.sleep(3)
    # 3秒后，手动将结果设置到 future 对象中
    fut.set_result("HTTP call result")
    print(f"Completed HTTP call")

async def func1():
    print("Started func1")
    loop = asyncio.get_running_loop()

    # 1. 创建一个空的 Future
    future = loop.create_future()

    # 2. 创建一个 Task，这个 Task 的工作就是去完成上面的 future
    loop.create_task(http_call(future))  

    # 3. 等待 future 完成。此时我们不知道谁会完成它，但我们相信它会被完成
    print("Waiting for the future to be completed...")
    rs = await future
    print(f"Future is done! Result: {rs}")

    print("Done func1")

asyncio.run(func1())
```

**Output:**
```bash
Started func1
Waiting for the future to be completed...
Starting HTTP call, will complete the future: <Future pending>
Completed HTTP call
Future is done! Result: HTTP call result
Done func1
```

**代码解析:**

这个例子展示了 `Future` 和 `Task` 如何协作：

1.  在 `func1` 中，我们创建了一个 `future`，它是一个等待结果的“占位符”。
2.  然后，我们创建了一个 `Task` 来运行 `http_call`。这个 `Task` 被“即发即忘”，它在后台开始运行。它的使命就是在3秒后调用 `future.set_result()`。
3.  `func1` 继续执行到 `await future`。此时，`func1` 暂停，等待 `future` 被完成。
4.  与此同时，`http_call` 任务在后台的 `asyncio.sleep(3)` 结束后，执行 `fut.set_result("HTTP call result")`。
5.  这个操作将 `future` 的状态从 `pending` 变为 `done`，并把结果存入其中。
6.  事件循环检测到 `future` 已完成，于是唤醒了正在 `await future` 的 `func1`。
7.  `func1` 从 `await` 处恢复执行，`rs` 变量得到了 `future` 的结果 "HTTP call result"，程序继续往下执行直到结束。

### 为什么这个例子要多此一举用task去配合future使用？

这是一个非常好的问题！在这个特定的、简化的例子中，确实是多此一举。我们完全可以像下面这样直接等待 `Task`：

```python
async def http_call():
    await asyncio.sleep(3)
    return "HTTP call result"

async def main():
    task = asyncio.create_task(http_call())
    result = await task
    print(result)
```

那么 `Future` 的真正价值在哪里？

**生动说明**：`Future` 扮演的是一个**“通用适配器”**或**“跨界桥梁”**的角色。

想象一下，你的 `asyncio` 世界是一个现代化的高科技厨房，所有的厨具（协程、任务）都用电，配合默契。但现在，你需要使用一个老式的、烧柴火的烤箱（比如一个运行在**另一个线程中的阻塞函数**，或者一个**基于回调的旧版库**）。

这个老式烤箱不认识你的高科技厨具。你怎么知道烤箱里的面包什么时候烤好呢？

`Future` 就是解决方案！你给操作烤箱的人（另一个线程）一个“对讲机”（`Future` 对象）。你告诉他：“面包烤好了就用这个对讲机通知我。” 然后你就可以在你的高科技厨房里 `await` 这个“对讲机”。当面包烤好后，那个人通过对讲机喊话（`future.set_result()`），你这边就能立刻收到信号，继续下一步操作。

所以，`Future` 的核心用途是**将不使用 `async/await` 语法的异步操作（如回调、线程、其他事件循环）集成到 `asyncio` 的世界中**。

---

## 再一个例子：更常用的Future使用场景

最常见、最实用的 `Future` 使用场景就是配合 `loop.run_in_executor()`，将阻塞的同步代码（如 CPU 密集型计算、不支持异步的 I/O 库）放到另一个线程中执行，以避免阻塞事件循环。

```python
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

# 这是一个阻塞的、同步的函数
def blocking_io_call(num):
    print(f"[Thread] Starting blocking call {num}, will take {num} seconds.")
    time.sleep(num)
    print(f"[Thread] Finished blocking call {num}.")
    return f"Result from blocking call {num}"

async def main():
    print("[Main] Starting main coroutine.")
    loop = asyncio.get_running_loop()

    # 1. 运行一个耗时3秒的阻塞函数
    # loop.run_in_executor() 会立即返回一个 Future 对象
    future1 = loop.run_in_executor(None, blocking_io_call, 3)

    # 2. 运行一个耗时2秒的阻塞函数
    future2 = loop.run_in_executor(None, blocking_io_call, 2)

    print("[Main] Blocking calls submitted. Waiting for futures.")
    
    # 使用 asyncio.gather 等待这两个 Future 完成
    results = await asyncio.gather(future1, future2)
    
    print(f"\n[Main] All futures completed. Results: {results}")

asyncio.run(main())
```

**Output:**
```bash
[Main] Starting main coroutine.
[Main] Blocking calls submitted. Waiting for futures.
[Thread] Starting blocking call 3, will take 3 seconds.
[Thread] Starting blocking call 2, will take 2 seconds.
[Thread] Finished blocking call 2.
[Thread] Finished blocking call 3.

[Main] All futures completed. Results: ['Result from blocking call 3', 'Result from blocking call 2']
```

**代码解析:**

1.  `blocking_io_call` 是一个普通的同步函数，它使用 `time.sleep()` 会阻塞当前线程。
2.  `loop.run_in_executor(None, blocking_io_call, 3)` 的作用是：
    -   `None`: 使用默认的 `ThreadPoolExecutor`（线程池）。
    -   它会从线程池中取一个线程去执行 `blocking_io_call(3)`。
    -   **关键**：它**立即返回一个 `Future` 对象**，而不会等待 `blocking_io_call` 执行完毕。
3.  `main` 协程拿到了两个 `Future` 对象，然后 `await asyncio.gather(...)` 来等待它们。
4.  当后台线程中的 `blocking_io_call` 函数执行完毕并返回结果时，事件循环会得到通知，并自动调用对应 `Future` 的 `set_result()` 方法。
5.  这样，`main` 协程就能在不阻塞事件循环的情况下，“等待”并获取在其他线程中运行的同步函数的结果。这正是 `Future` 作为“桥梁”的完美体现。

## 内容总结

-   `Future` 是一个底层的“占位符”，代表一个未来的结果。
-   `Future` **不知道**如何完成自己，必须由外部代码通过 `set_result()` 或 `set_exception()` 来手动完成。
-   `Task` 是 `Future` 的子类，它**知道**如何完成自己（通过运行它所包装的协程）。
-   在纯 `asyncio` 应用中，你应该优先使用 `Task` (`asyncio.create_task`)。
-   `Future` 的核心价值在于**充当桥梁**，用于将非 `async/await` 风格的异步操作（如线程、回调）集成到 `asyncio` 事件循环中。最典型的例子就是 `loop.run_in_executor()`。
