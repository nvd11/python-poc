# asyncio.create_task() vs asyncio.ensure_future()

在 `asyncio` 中，`create_task()` 和 `ensure_future()` 都可以用来安排一个协程（coroutine）的执行，并将其包装成一个任务（Task）。然而，它们之间存在一些关键的区别，了解这些区别有助于编写更清晰、更现代的异步代码。

简单来说：**在现代 Python (3.7+) 中，你应该优先使用 `asyncio.create_task()`。**

---

## asyncio.create_task()

`create_task()` 是在 **Python 3.7** 中引入的，作为创建和安排协程执行的推荐方式。

### 作用

-   **明确的意图**：其名称清晰地表明了它的作用——创建一个 `Task`。
-   **高层 API**：它是一个简单直接的高层函数。
-   **参数**：它只接受一个协程对象作为参数。
-   **返回值**：总是返回一个 `asyncio.Task` 对象。

### 使用场景

-   在任何需要将协程作为后台任务并发执行的应用代码中。这是现代 `asyncio` 编程的标准做法。

### 代码示例

```python
import asyncio

async def my_coroutine():
    print("Coroutine is running in the background")
    await asyncio.sleep(1)
    print("Coroutine has finished")

async def main():
    print("Main function started")
    # 使用 create_task 创建一个后台任务
    task = asyncio.create_task(my_coroutine())
    # main 函数可以继续执行其他工作，而不需要等待 task 完成
    print("Main function continues its work")
    await asyncio.sleep(2) # 等待足够长的时间以确保任务完成
    print("Main function finished")

asyncio.run(main())
```

---

## asyncio.ensure_future()

`ensure_future()` 是一个更早（从 **Python 3.4.4** 开始）且更底层的函数。

### 作用

-   **兼容性**：它的主要作用是确保你得到一个 `Future` 对象。
-   **参数**：它可以接受一个**协程**、一个 `Future` 对象或一个 `Task` 对象。
-   **返回值**：
    -   如果传入一个**协程**，它会调用 `loop.create_task()` 来创建一个 `Task` 并返回它（行为类似于 `create_task()`）。
    -   如果传入一个 `Future` 或 `Task` 对象，它会**原封不动地返回**该对象。

这个“确保”的特性使得它在编写需要同时处理协程和 `Future` 对象的库代码时非常有用。

### 使用场景

-   **兼容旧版本 Python**：在 Python 3.7 之前，这是创建任务的唯一官方推荐方式。
-   **编写库代码**：当你的函数需要接受一个“可等待”对象，但不确定它是一个协程还是一个已经存在的 `Task`/`Future` 时，`ensure_future()` 可以方便地进行统一处理。

### 代码示例

```python
import asyncio

async def my_coroutine():
    return "Done"

async def main():
    # 1. 传入协程
    task1 = asyncio.ensure_future(my_coroutine())
    print(f"Is task1 a Task? {isinstance(task1, asyncio.Task)}")

    # 2. 传入Task
    task2 = asyncio.create_task(my_coroutine())
    task3 = asyncio.ensure_future(task2)
    
    # task2 和 task3 是同一个对象
    print(f"Are task2 and task3 the same object? {task2 is task3}")

asyncio.run(main())

# 输出:
# Is task1 a Task? True
# Are task2 and task3 the same object? True
```

---

## 主要区别总结

| 特性 | `asyncio.create_task()` | `asyncio.ensure_future()` |
| :--- | :--- | :--- |
| **引入版本** | Python 3.7 | Python 3.4.4 |
| **API 级别** | 高层 | 底层 |
| **意图** | 清晰：创建新任务 | 确保得到一个 Future/Task |
| **参数类型** | 仅协程 (`Coroutine`) | 协程、Future 或 Task |
| **返回值** | 总是创建一个新的 `Task` | 如果参数是 Future/Task，则直接返回 |

## 结论与最佳实践

-   **对于应用开发者**：在你的项目中使用 Python 3.7 或更高版本时，**始终使用 `asyncio.create_task()`**。它的意图更明确，是社区推荐的最佳实践。

-   **对于库开发者**：只有在你需要兼容 Python 3.6 及更早版本，或者你需要编写一个能同时接受协程和 `Future` 对象的灵活函数时，才考虑使用 `asyncio.ensure_future()`。

简单来说，`create_task` 是为“做某事”而设计的，而 `ensure_future` 是为“确保某物是某种类型”而设计的。在日常开发中，我们绝大多数时候都属于前者。
