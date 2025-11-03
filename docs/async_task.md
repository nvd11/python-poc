# python 异步编程 -- 理解async中的Task 对象

## 什么是Task

在 `asyncio` 中，`Task` 是一个用来并发调度协程（Coroutine）的对象。你可以把它看作是对协程的一层“包装”，它负责在事件循环中管理协pre程的执行。

`Task` 对象是 `Future` 的一个子类，它封装了一个协程的运行过程，追踪其状态（如：待定、运行中、已完成），并保存其最终的返回结果或抛出的异常。

`Task` 的核心价值在于它允许程序“即发即忘”（fire and forget）。一旦你将一个协程包装成 `Task`，它就会被提交到事件循环中，并尽快得到执行，而你的主程序可以继续执行其他代码，不必立刻等待它完成。这正是实现并发的关键。

## Task 与 coroutine的关系和区别

理解 `Task` 和 `coroutine` 的关系是掌握 `asyncio` 的基础。

-   **Coroutine (协程)**:
    -   由 `async def` 定义的函数返回的对象。
    -   它本身只是一个“蓝图”或“配方”，定义了需要执行的一系列异步操作。
    -   仅仅调用一个协程函数并不会执行其中的代码，它只是返回一个可以被等待（await）或调度的协程对象。

-   **Task (任务)**:
    -   是协程的“执行者”或“运行实例”。
    -   当你用 `asyncio.create_task(my_coro)` 创建一个 `Task` 时，你实际上是在告诉事件循环：“请把这个协程（`my_coro`）安排上，尽快开始运行它。”
    -   `Task` 会立即被调度，并在事件循环的下一个迭代中开始执行，与程序中的其他任务并发运行。

**一个简单的比喻：**
-   `Coroutine` 就像一张菜谱，详细说明了做一道菜的步骤。
-   `Task` 就像一位厨师拿到了这张菜谱，并开始在厨房（事件循环）里实际动手做菜。你可以同时派多个厨师（Tasks）去做不同的菜（Coroutines）。

## 如何创建一个task对象

在现代 Python (3.7+) 中，创建 `Task` 的首选方法是使用高层 API `asyncio.create_task()`。

还有一个较早的函数 `asyncio.ensure_future()`，它更为底层，主要用于库的开发或兼容旧版本。对于应用开发，`create_task()` 的意图更清晰，是最佳选择。

### 代码例子

#### 例子1：串行等待并发任务

```python
import asyncio
import time

async def http_call(num):
    print(f"Starting HTTP call with parameter {num}")
    await asyncio.sleep(num)  # Simulating an I/O-bound operation with sleep
    print(f"Completed HTTP call {num}")
    return {"status": "success", "data": num} 

async def main():
    start_time = time.time()
    print("Starting main coroutine")

    # !!!important,  once task is created , it will be added to event loop automatically
    # and will start running in background!!!
    task1 = asyncio.create_task(http_call(3))
    task2 = asyncio.create_task(http_call(2))

    print("Tasks created, awaiting their completion")
    
    # 等待 task1 完成并获取结果。注意，此时 task1 和 task2 都已经在后台运行了。
    result1 = await task1 
    print(f"Result from task1: {result1}")
    
    # 等待 task2 完成。如果 task2 此时已经完成，await 会立刻返回结果。
    result2 = await task2 
    print(f"Result from task2: {result2}")
    
    print(f"All tasks completed in {time.time() - start_time:.2f} seconds")

asyncio.run(main())
```

**代码解析:**

这段代码最需要关注的是注释中提到的重点：**`Task` 一旦被创建，就会被自动提交到事件循环，并立即开始在后台运行。**

1.  当 `task1 = asyncio.create_task(http_call(3))` 执行时，`http_call(3)` 协程就被安排执行了。程序不会在此处停留。
2.  紧接着 `task2 = asyncio.create_task(http_call(2))` 也被安排执行。
3.  从输出可以看到，`Starting HTTP call...` 的打印发生在 `await task1` 之前，这证明了两个任务在被创建后就立刻并发启动了。
4.  `await task1` 的作用不是“启动”任务，而是“等待”一个**已经在运行的**任务完成，并获取其结果。
5.  虽然我们先 `await task1`，但因为 `task2` 的执行时间更短（2秒 vs 3秒），所以 `Completed HTTP call 2` 的输出会先于 `Completed HTTP call 3`。总耗时约等于最长的那个任务的耗时（3秒），而不是串行等待的总和（5秒）。

---

#### 另一个代码例子：使用 `asyncio.wait()` 控制任务

这个风格更常用于需要对一组任务进行精细控制的场景，比如设置超时。

```python
import asyncio
import time

async def http_call(num):
    print(f"Starting HTTP call with parameter {num}")
    await asyncio.sleep(num)
    print(f"Completed HTTP call {num}")
    return {"status": "success", "data": num} 

async def main():
    print("Starting main coroutine")

    task_list = [
        asyncio.create_task(http_call(3), name="t1"),
        asyncio.create_task(http_call(2), name="t2"),
        asyncio.create_task(http_call(1), name="t3")
    ]
    
    # 使用 asyncio.wait 并设置2秒超时
    done, pending = await asyncio.wait(task_list, timeout=2)  
    
    print(f"\nDone tasks ({len(done)}):")
    for task in done:
        # 任务完成后，可以通过 .result() 获取结果
        print(f"- {task.get_name()} result: {task.result()}")

    print(f"\nPending tasks ({len(pending)}):")
    for task in pending:
        print(f"- {task.get_name()} is still pending.")
        task.cancel() # 取消仍在运行的任务，避免资源泄露

asyncio.run(main())
```

**代码解析:**

`asyncio.wait()` 是一个更底层的 API，它提供了强大的控制能力。

1.  `await asyncio.wait(task_list, timeout=2)` 会等待 `task_list` 中的任务，但最多只等2秒。
2.  2秒后，`wait` 函数会返回两个集合：`done`（已完成的任务）和 `pending`（仍在运行的任务）。
3.  在这个例子中，耗时1秒的 `t3` 和耗时2秒的 `t2` 会在2秒内完成，所以它们会出现在 `done` 集合中。
4.  耗时3秒的 `t1` 在2秒时还未完成，所以它会出现在 `pending` 集合中。
5.  这个模式非常适合处理那些“不必等待所有结果”或“需要对长时间运行的任务进行处理”的场景。

---

#### 再一个代码例子：使用 `asyncio.gather()` (最常用)

这个风格是并发执行一组任务并收集所有结果的最常用、最简洁的方式。

```python
import asyncio
import time

async def http_call(num):
    print(f"Starting HTTP call with parameter {num}")
    await asyncio.sleep(num)
    print(f"Completed HTTP call {num}")
    return {"status": "success", "data": num} 

async def main():
    start_time = time.time()
    print("Starting main coroutine")

    task_list = [
        http_call(3),
        http_call(2),
        http_call(1)
    ]
    
    print ("Tasks created, awaiting their start and completion")
    # 使用 asyncio.gather 运行任务并等待它们全部完成
    results = await asyncio.gather(*task_list)
    
    print(f"\nAll results: {results}")
    print(f"Total time: {time.time() - start_time:.2f} seconds")

asyncio.run(main())
```

**代码解析:**

`asyncio.gather()` 是一个高层 API，非常易于使用。

1.  `await asyncio.gather(*task_list)` 会并发运行 `task_list` 中的所有可等待对象，并等待它们全部完成。
2.  它会返回一个列表，其中包含了所有任务的返回结果，并且顺序与输入时保持一致。
3.  **值得注意的是**：`gather` 非常方便，你甚至不需要预先创建 `Task`。如例子所示，可以直接向它传递协程对象列表（`[http_call(3), http_call(2), ...]`)。`gather` 会在内部自动将它们包装成 `Task` 进行调度。这使得代码更加简洁。

---

## 一个常见的坑：在事件循环创建之前加入task

上面的例子中，`asyncio.create_task()` 都是在 `async` 函数内部调用的。此时，`asyncio.run()` 已经创建并启动了事件循环。但如果我们在事件循环创建之前就尝试创建 `Task`，就会出错。

**错误例子:**

```python
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
```

**错误输出:**
```bash
raceback (most recent call last):
  File "/home/gateman/projects/github/python-poc/notebooks/async/async_task5.py", line 10, in <module>
    asyncio.create_task(http_call(3), name="t1"),
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/gateman/.pyenv/versions/3.12.4/lib/python3.12/asyncio/tasks.py", line 417, in create_task
    loop = events.get_running_loop()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
RuntimeError: no running event loop
sys:1: RuntimeWarning: coroutine 'http_call' was never awaited
```

**代码解析:**

错误的原因非常直接：`asyncio.create_task()` 在执行时，需要一个正在运行的事件循环来注册和调度新创建的任务。它通过内部调用 `asyncio.get_running_loop()` 来获取这个循环。

在上面的错误例子中，`task_list` 的定义是在模块的顶层。当 
```

**代码解析:**

错误的原因非常直接：`asyncio.create_task()` 在执行时，需要一个正在运行的事件循环来注册和调度新创建的任务。它通过内部调用 `asyncio.get_running_loop()` 来获取这个循环。

在上面的错误例子中，`task_list` 的定义是在模块的顶层。当 Python 解释器执行到这里时，`asyncio.run()` 还没有被调用，因此没有任何事件循环在运行。`get_running_loop()` 自然会失败，并抛出 `RuntimeError`。

**正确做法**：始终在 `async` 函数内部，即在一个已经存在的异步上下文中创建 `Task`。

## 本文内容总结

-   **Task 是 Coroutine 的运行实例**。Coroutine 是定义，Task 是执行。
-   使用 `asyncio.create_task()` (Python 3.7+) 来创建和调度任务，这是现代 `asyncio` 的标准做法。
-   **Task 一旦创建，就会立即被调度**并在后台并发执行。
-   `await my_task` 用于等待一个**已经在运行的**任务完成并获取其结果。
-   `asyncio.gather()` 是并发运行多个任务并收集所有结果的最常用、最简单的方法。
-   `asyncio.wait()` 提供了更底层的控制，适用于超时处理等复杂场景。
-   **切记**：必须在有事件循环运行的上下文中（即 `async` 函数内）创建 `Task`，否则会引发 `RuntimeError`。
