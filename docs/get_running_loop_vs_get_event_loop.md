# asyncio.get_running_loop() vs asyncio.get_event_loop()

在 `asyncio` 编程中，获取当前事件循环是一个常见的需求。Python 提供了两个主要的函数来做这件事：`asyncio.get_running_loop()` 和 `asyncio.get_event_loop()`。然而，它们的设计理念和行为有很大不同，理解这些差异对于编写健壮、可预测的异步代码至关重要。

**核心结论：在现代 Python (3.7+) 中，你应该始终优先使用 `asyncio.get_running_loop()`。**

---

## asyncio.get_running_loop()

这个函数是在 **Python 3.7** 中引入的，旨在提供一种更安全、更明确的方式来获取事件循环。

### 作用与行为

-   **意图明确**：它的名字清晰地表明了它的作用——获取**当前正在运行的**事件循环。
-   **上下文依赖**：它只能在由事件循环驱动的代码中被成功调用（例如，在一个 `async def` 函数内部，或者在一个被事件循环调度的回调中）。
-   **安全保证**：如果在没有事件循环运行的情况下调用它，它会立即抛出 `RuntimeError`。这是一个**特性而非缺陷**，因为它能有效防止一类常见的编程错误（例如，在循环启动前就尝试与之交互）。

### 代码示例

```python
import asyncio

def try_get_loop_outside():
    print("Trying to get loop outside async context...")
    try:
        loop = asyncio.get_running_loop()
        print(f"Success (outside): {loop}")
    except RuntimeError as e:
        print(f"Failed (outside): {e}")

async def main():
    print("Inside main coroutine...")
    try:
        loop = asyncio.get_running_loop()
        print(f"Success (inside): {loop}")
    except RuntimeError as e:
        print(f"Failed (inside): {e}")

# 在事件循环启动前调用
try_get_loop_outside()

# 启动事件循环并运行 main
asyncio.run(main())
```

**Output:**
```bash
Trying to get loop outside async context...
Failed (outside): no running event loop
Inside main coroutine...
Success (inside): <_UnixSelectorEventLoop running=True closed=False debug=False>
```
这个例子清晰地表明，`get_running_loop()` 只在 `asyncio.run()` 创建并运行了事件循环之后才能被成功调用。

---

## asyncio.get_event_loop()

这是 `asyncio` 中一个更早、更传统的函数。它的行为更复杂，也更容易导致意想不到的问题。

### 作用与行为

-   **复杂的策略**：它会获取当前上下文的事件循环。这个“上下文”通常指的是当前线程。
-   **可能会创建新循环**：如果在当前上下文中没有事件循环，调用 `get_event_loop()` **可能会自动创建一个新的事件循环**并将其设置为当前上下文的循环。
    -   **注意**：这个自动创建的行为在 Python 3.10 中已被弃用（Deprecrated），并计划在未来版本中移除，因为它常常是错误的根源。
-   **不保证循环在运行**：即使它返回了一个循环对象，也**不保证**这个循环当前正在运行。

这种“智能”的行为，尤其是在主线程中自动创建循环，很容易导致在不同模块中无意间创建了多个事件循环，或者在错误的线程中获取了循环，从而引发难以调试的bug。

### 代码示例

```python
import asyncio

# 在主线程、asyncio.run() 之外调用
print("Calling get_event_loop() in main thread...")
loop1 = asyncio.get_event_loop()
print(f"Loop 1: {loop1}, is running: {loop1.is_running()}")

async def main():
    print("Inside main coroutine...")
    loop2 = asyncio.get_event_loop()
    print(f"Loop 2: {loop2}, is running: {loop2.is_running()}")
    # 验证在 asyncio.run() 内外获取的是同一个循环对象
    print(f"Is loop1 the same as loop2? {loop1 is loop2}")

asyncio.run(main())
```

**Output (在 Python 3.9 及更早版本):**
```bash
Calling get_event_loop() in main thread...
Loop 1: <_UnixSelectorEventLoop running=False closed=False debug=False>, is running: False
Inside main coroutine...
Loop 2: <_UnixSelectorEventLoop running=True closed=False debug=False>, is running: True
Is loop1 the same as loop2? True
```
从输出可见，`get_event_loop()` 在循环运行之前就返回了一个循环对象（并且可能创建了它），这使得代码的意图变得模糊。

---

## 主要区别总结

| 特性 | `asyncio.get_running_loop()` (推荐) | `asyncio.get_event_loop()` (旧版) |
| :--- | :--- | :--- |
| **引入版本** | Python 3.7 | Python 3.4 |
| **核心行为** | 获取**正在运行的**循环 | 获取**当前上下文的**循环 |
| **无循环时** | 抛出 `RuntimeError` (安全) | 可能创建新循环 (危险, 已弃用) |
| **返回保证** | 返回的循环保证在运行中 | 不保证返回的循环在运行 |
| **主要用途** | 在异步代码内部安全地获取循环 | 兼容旧代码；从外部与循环交互 |
| **清晰性** | 非常清晰，意图明确 | 行为复杂，容易误用 |

## 结论与最佳实践

1.  **首选 `asyncio.get_running_loop()`**：在所有使用 Python 3.7+ 的新代码中，这应该是你获取事件循环的唯一方式。它更安全、更明确，能帮你避免很多潜在的错误。

2.  **谨慎使用 `asyncio.get_event_loop()`**：你只应该在少数特定场景下使用它：
    -   需要兼容 Python 3.6 或更早的版本。
    -   你需要从**非异步代码**（例如，另一个线程）中获取主线程的事件循环，以便使用 `loop.call_soon_threadsafe()` 等方法提交任务。即便如此，也需要非常小心地管理循环的生命周期。

3.  **你可能根本不需要它们**：随着 `asyncio.run()` 和 `asyncio.create_task()` 等高层 API 的普及，直接与事件循环对象交互的需求已经大大减少。在大多数应用代码中，你可能完全不需要手动获取事件循环。
