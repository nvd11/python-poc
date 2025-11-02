# asyncio.gather() vs asyncio.wait()：作用与区别

在 Python 的 `asyncio` 库中，`gather()` 和 `wait()` 都是用于并发运行多个异步任务的重要工具。然而，它们在设计目的、使用方式和返回值上存在显著差异。理解这些差异有助于在不同场景下选择最合适的工具。

## asyncio.gather()

`gather()` 是一个相对高层的 API，用于将多个可等待对象（如协程或任务）组合在一起并发执行，并收集它们的结果。

### 作用

1.  **并发执行**：同时运行多个异步任务。
2.  **收集结果**：等待所有任务完成后，将它们的结果按照输入时的顺序收集到一个列表中返回。
3.  **异常传播**：默认情况下，如果任何一个任务引发异常，`gather()` 会立即将该异常传播出去，并取消其他未完成的任务。如果设置 `return_exceptions=True`，它将不会传播异常，而是将异常对象作为结果之一返回。

### 使用场景

-   当你需要并发执行多个独立的异步操作，并且关心它们 **所有** 的返回结果时。
-   当你希望将一组任务视为一个整体，其中任何一个任务失败都意味着整个操作失败。
-   适用于简单、直接的并发执行需求。

### 代码示例

```python
import asyncio
import time

async def my_task(name, delay):
    print(f"任务 {name} 开始，将执行 {delay} 秒")
    await asyncio.sleep(delay)
    result = f"任务 {name} 完成"
    print(result)
    return result

async def main():
    start_time = time.time()
    
    # 使用 gather 并发运行任务
    results = await asyncio.gather(
        my_task("A", 2),
        my_task("B", 1),
        my_task("C", 3)
    )
    
    print("\n所有任务已完成。")
    print("返回结果:", results)
    
    end_time = time.time()
    print(f"总耗时: {end_time - start_time:.2f} 秒")

asyncio.run(main())

# 输出:
# 任务 A 开始，将执行 2 秒
# 任务 B 开始，将执行 1 秒
# 任务 C 开始，将执行 3 秒
# 任务 B 完成
# 任务 A 完成
# 任务 C 完成
#
# 所有任务已完成。
# 返回结果: ['任务 A 完成', '任务 B 完成', '任务 C 完成']
# 总耗时: 3.01 秒
```

---

## asyncio.wait()

`wait()` 是一个更底层的 API，它提供了对一组并发任务更精细的控制。它不会直接返回任务的结果，而是返回两组任务集合：已完成的（done）和待定的（pending）。

### 作用

1.  **并发执行**：与 `gather` 类似，同时运行多个异步任务。
2.  **精细控制**：通过 `return_when` 参数，可以指定 `wait()` 在何种条件下返回。
    -   `asyncio.ALL_COMPLETED` (默认): 等待所有任务完成。
    -   `asyncio.FIRST_COMPLETED`: 等待任意一个任务完成就返回。
    -   `asyncio.FIRST_EXCEPTION`: 等待任意一个任务抛出异常就返回（如果没有异常，则行为类似 `ALL_COMPLETED`）。
3.  **不直接返回结果**：它返回 `(done, pending)` 两个集合。你需要自己遍历 `done` 集合来获取任务的结果或检查异常。
4.  **不传播异常**：`wait()` 不会自动传播异常。你需要手动检查 `done` 集合中每个任务的状态。

### 使用场景

-   当你不需要等待所有任务都完成，只需要其中 **任意一个** 或 **第一个** 完成时。
-   当你需要对一组任务有更复杂的控制逻辑，例如设置超时或在某些任务失败后继续执行其他任务。
-   适用于需要底层、精细化控制的复杂并发场景。

### 代码示例

#### 场景1: 等待所有任务完成 (`ALL_COMPLETED`)

```python
import asyncio

async def my_task(name, delay):
    await asyncio.sleep(delay)
    return f"任务 {name} 完成"

async def main():
    tasks = [
        asyncio.create_task(my_task("A", 2)),
        asyncio.create_task(my_task("B", 1))
    ]
    
    # 使用 wait 等待所有任务完成
    done, pending = await asyncio.wait(tasks)
    
    print(f"已完成的任务: {len(done)}")
    print(f"待定的任务: {len(pending)}")
    
    for task in done:
        # 需要调用 task.result() 来获取结果
        print("结果:", task.result())

asyncio.run(main())

# 输出:
# 已完成的任务: 2
# 待定的任务: 0
# 结果: 任务 B 完成
# 结果: 任务 A 完成
```

#### 场景2: 等待第一个任务完成 (`FIRST_COMPLETED`)

```python
import asyncio

async def my_task(name, delay):
    await asyncio.sleep(delay)
    return f"任务 {name} 完成"

async def main():
    tasks = [
        asyncio.create_task(my_task("A", 2)),
        asyncio.create_task(my_task("B", 1))
    ]
    
    # 使用 wait 等待第一个完成的任务
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    
    print(f"已完成的任务: {len(done)}")
    print(f"待定的任务: {len(pending)}")
    
    # 第一个完成的是任务B
    for task in done:
        print("结果:", task.result())
        
    # 注意：任务A仍在后台运行，需要手动取消以避免 "Task was destroyed but it is pending!" 警告
    for p_task in pending:
        p_task.cancel()

asyncio.run(main())

# 输出:
# 已完成的任务: 1
# 待定的任务: 1
# 结果: 任务 B 完成
```

---

## 参数类型的区别

您提出的这一点非常重要。虽然两个函数都接受“可等待对象”，但它们的常用模式和内部处理有所不同：

-   **`asyncio.gather(*aws)`**: `gather` 接受一系列（`*`）独立的可等待对象作为参数。你可以很方便地直接传入协程对象，`gather` 会自动将它们包装成 `Task` 来执行。这是它作为高层API便捷性的体现。
    ```python
    # 直接传入协程，非常方便
    await asyncio.gather(my_task("A"), my_task("B"))
    ```

-   **`asyncio.wait(aws)`**: `wait` 接受一个**单一的**可迭代对象（如列表或集合）作为参数，该对象包含了所有要等待的可等待对象。虽然它也可以接受包含协程的列表（内部也会包装成Task），但官方文档和最佳实践都**强烈推荐**传入一个 `Task` 对象的列表。这是因为 `wait` 返回的是 `Task` 对象的集合（`done` 和 `pending`），预先创建 `Task` 可以让你对这些对象有更明确的控制权。
    ```python
    # 推荐做法：先创建Task列表
    tasks = [asyncio.create_task(my_task("A")), asyncio.create_task(my_task("B"))]
    done, pending = await asyncio.wait(tasks)
    ```

总的来说，`gather` 的设计是为了“发射后不管”（fire and forget）并收集结果，所以直接接受协程很方便。而 `wait` 的设计是为了精细控制，所以与显式创建的 `Task` 对象配合使用效果最佳。

## 主要区别总结

| 特性 | `asyncio.gather()` | `asyncio.wait()` |
| :--- | :--- | :--- |
| **API 级别** | 高层 API | 底层 API |
| **参数形式** | 接受多个独立的可等待对象 (`*awaitables`) | 接受一个包含可等待对象的迭代器 (`Iterable[Awaitable]`) |
| **推荐参数** | 直接传入协程或Task | 传入 `Task` 对象列表 |
| **返回值** | 按顺序排列的结果列表 | `(done, pending)` 两个任务集合 |
| **异常处理** | 自动传播异常（可配置） | 需要手动检查任务异常 |
| **控制粒度** | 简单，要么全完成，要么失败 | 精细，可通过 `return_when` 控制返回时机 |
| **易用性** | 非常简单，适合大多数场景 | 相对复杂，需要更多手动处理 |

## 结论

-   **优先使用 `asyncio.gather()`**：在大多数情况下，`gather()` 更简单、更直接。当你需要并发运行一组任务并等待它们全部完成以获取结果时，它就是最佳选择。
-   **在需要精细控制时使用 `asyncio.wait()`**：当你需要处理更复杂的逻辑，例如“等待任意一个任务完成”、“设置超时后处理未完成的任务”或“即使有任务失败也要继续”等场景时，`wait()` 提供了必要的底层灵活性。
