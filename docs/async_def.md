# python异步编程 -- 理解协程函数和协程对象


## 什么是协程函数

很简单， 用`async def` 定义的函数就是协程函数。
例如下面定义的func1()就是协程函数
```python

async def func1():
    print("This is async function 1")
    return "Result from async function 1"
```
<br><br><br><br>

## 什么是协程对象

调用一个协程函数并不会立即执行它，而是会返回一个**协程对象**。例如func1() 就是一个协程对象

又如 我们可以用一个变量来接收协程对象

```python
async def func1():
    print("This is async function 1")
    return "Result from async function 1"

def func2():
    print("This is sync function 2")
    return "Result from sync function 2"
coro = func1()
print(type(coro))   # <class 'coroutine'>

result = func2() # func2 will be executed immediately
print(type(result))    # <class 'str'> as return type of func2 is str
```

### 代码解释

上面的代码清晰地展示了异步函数和同步函数在调用时的本质区别：

1.  **调用异步函数 `func1()`**
    -   当执行 `coro = func1()` 时，`func1` 函数体内的代码（`print(...)`）**并不会被执行**。
    -   Python会立刻返回一个**协程对象（coroutine object）**，它像一个“待办事项”或“执行计划”。
    -   因此，`print(type(coro))` 的输出是 `<class 'coroutine'>`，证明了我们拿到的只是一个“计划”，而不是最终结果。

2.  **调用同步函数 `func2()`**
    -   当执行 `result = func2()` 时，Python会**立即进入并执行** `func2` 函数体内的所有代码。
    -   `print("This is sync function 2")` 会被立刻打印到控制台。
    -   函数执行完毕后，将其返回值（字符串 `"Result from sync function 2"`）赋给 `result` 变量。
    -   因此，`print(type(result))` 的输出是 `<class 'str'>`，即函数返回值的类型。

**核心结论：** 调用一个`async def`函数是创建并返回一个“计划”（协程对象），而调用一个`def`函数是立即执行并返回一个“结果”。这是理解`asyncio`编程的第一步。


<br><br><br><br>
## 如何执行协程函数里的代码

所以当未一个协程函数加上括号， 它只会返回一个协程对象， 并不会执行函数内的代码

如果要执行aysnc 函数， **则需要把协程对象放入到事件循环中**



<br><br><br><br>

## 如果要在同步环境中执行协程函数，则需要asyncio.run() 或 loop.run_until_complete()


例如：
```python

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

```
output:
```bash
This is async function 1
Result from asyncio.run(): Result from async function 1
This is async function 1
Result from asyncio.run(): Result from async function 1
```
可见func1里的代码被执行了

### 代码解释

这段代码展示了如何在同步代码中启动并执行一个协程。这是连接同步世界和异步世界的桥梁。

1.  **`trigger_event_loop()` (旧式方法)**
    *   `loop = asyncio.get_event_loop()`: 获取当前线程的事件循环。事件循环是`asyncio`应用的核心，负责调度和执行异步任务。
    *   `loop.run_until_complete(func1())`: 这是启动协程的关键。它会阻塞当前线程，将`func1()`协程对象放入事件循环中执行，直到它完成并返回结果。在`func1`执行期间，事件循环会接管控制权。

2.  **`trigger_event_loop2()` (新式方法, Python 3.7+ 推荐)**
    *   `asyncio.run(func1())`: 这是一个更高级、更简洁的接口。它会自动处理事件循环的创建、运行和关闭。当你调用`asyncio.run()`时，它会：
        1.  创建一个全新的事件循环。
        2.  将`func1()`协程提交给这个循环去执行。
        3.  等待协程执行完毕。
        4.  最后自动关闭事件循环。
    *   这是目前启动顶层异步程序的首选方式，因为它更安全、更简单，避免了手动管理事件循环的复杂性。

无论是旧式还是新式方法，核心思想都是通过一个入口函数（如`run_until_complete`或`run`）将协程“提交”给事件循环来执行。`asyncio.run()`是现代Python中更推荐的做法。


<br><br><br><br>
## 如果要异步环境中执行协程函数，直接用await就好

例如：

```python
async def func3():
    print("This is async function 3")
    rs = await func1()  # waiting for func1 to complete
    print(type(rs))
    print(rs)

asyncio.run(func3())

```

output:

```bash

This is async function 3
This is async function 1
<class 'str'>
Result from async function 1
```
可见func1里的代码被执行了， 而且我们还通过await拿到了返回值
因为func1被func3调用执行， 而func3也是一个异步环境， 所以直接用await就好

但是最终func3还是要被事件循环调用， 所以异步函数的最终入口肯定是事件循环，无论这个事件循环是显式创建还是由框架（如jupyter notebook,fastapi router）创建的

<br><br><br><br>
## 总结


*   **协程函数与协程对象**：用 `async def` 定义的是协程函数。调用它不会立即执行，而是返回一个“待办事项”——协程对象。这与立即执行并返回结果的普通函数形成鲜明对比。
*   **执行协程**：协程必须在**事件循环（Event Loop）**中才能执行。
*   **从同步代码启动协程**：在普通同步代码中，应使用 `asyncio.run(coroutine)` 来启动并执行一个协程。这个函数不仅会执行协程，还会返回其结果。
*   **在异步代码中调用协程**：在一个 `async def` 函数内部，应使用 `await` 关键字来调用另一个协程。`await` 会等待被调用的协程完成，并返回其结果。
*   **核心思想**：所有异步代码的执行起点最终都是一个事件循环。`asyncio.run()` 是顶层入口，而 `await` 是在异步世界中串联任务的工具。

---
