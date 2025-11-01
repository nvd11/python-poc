## 什么事件循环
事件循环是python 异步开发的核心概念

这里不贴定义了，
通俗点讲， 事件循环就是一个能不断重复去处理内部多个任务的循环， 直到所有内部任务都完成处理。
它有个特性就是，当它处理一个任务遇到IO阻塞时，就会跳出来处理下个任务

<br><br><br><br>
## 伪代码解释

我们用一段伪代码来解释。

这段伪代码形象地模拟了一个事件循环的核心调度逻辑：

1.  **维护一个任务列表**：事件循环管理着所有需要执行的异步任务。
2.  **无限循环**：通过一个`while True`循环，调度器不断地检查和执行任务，直到所有任务完成。
3.  **智能调度**：
    *   当遇到一个**可处理**的任务，它会执行该任务，直到遇到IO操作（如网络请求）而阻塞。此时，它不会原地等待，而是立刻**挂起**该任务，并进入下一轮循环，去处理别的任务。
    *   当遇到一个处于**IO阻塞**状态的任务，它会直接**跳过**，避免浪费时间。
    *   当任务**已完成**，则将其从列表中移除。

这个“遇到阻塞就切换”的模型，正是`asyncio`事件循环在单线程中实现高并发IO操作的精髓所在。

```
#伪代码
   #构造一个可执行任务列表 （其中的任务有3中状态， 分别是可处理， IO阻塞和已完成）
   任务列表 = [task1, task2,task3....]

while True: # 不断循环直到达到某个条件
   如果列表中没有任务了(所有任务全部完成):
        break

   从任务列表中提取某个task

   如果这个task 状态是 可处理：
       处理这个task直到遇到IO阻塞就进入下一循环

   如果这个task 状态是 IO阻塞：
       continue

    如果这个task 状态是 已完成：
       从列表中移除（标记完成） 这个task
     
```

<br><br><br><br>
## 真实代码例子

下面会用一个可执行的代码例子来讲解

### 首先我们先构造两个函数
这两个函数都人为配置了IO阻塞, 而且这里我们也构造了一个相应的任务列表

```python
async def func1():
   logger.info("step 1")
   await asyncio.sleep(2)
   logger.info("step 2")

async def func2():
   logger.info("step 3")
   await asyncio.sleep(2)
   logger.info("step 4")

def get_event_loop_tasks():
   tasks = [
       func1(),
       func2(),
   ]
   return tasks
```


## 第一种触发事件循环的方式：syncio.get_event_loop().run_until_complete()

```python

def trigger_event_loop():
    loop = asyncio.get_event_loop()
    tasks = get_event_loop_tasks()
    loop.run_until_complete(asyncio.gather(*tasks))
```


可以看出， 这种方式的逻辑与上面的伪代码很类似

## 第二种触发事件循环的方式：asyncio.run（）

```python
async def run_tasks():
    tasks = get_event_loop_tasks()
    await asyncio.gather(*tasks)


def trigger_event_loop2():
     asyncio.run(run_tasks())
```

注意这里需要额外编写一层aysnc方法去await 任务列表
下面两种写法都是错误的

```python
"""
#ValueError: a coroutine was expected, got <_GatheringFuture pending>
sys:1: RuntimeWarning: coroutine 'func2' was never awaited
sys:1: RuntimeWarning: coroutine 'func1' was never awaited
"""
def trigger_event_loop2():
     tasks = get_event_loop_tasks()
     asyncio.run(asyncio.gather(*tasks))

"""    
asyncio.run(await asyncio.gather(*tasks))
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
SyntaxError: 'await' outside async functionw
"""
def trigger_event_loop2():
     tasks = get_event_loop_tasks()
     asyncio.run(await asyncio.gather(*tasks)) # asyncio.run only accept an async function

```

### 错误写法的代码解释

上面两种错误的写法非常典型，可以帮助我们更深入地理解`asyncio.run`和`await`的工作机制。

1.  **为什么 `asyncio.run(asyncio.gather(*tasks))` 是错的？**
    -   **错误原因**：`asyncio.run()` 函数期望接收的参数是一个**协程（Coroutine）**，也就是一个由`async def`函数调用后返回的对象（比如 `run_tasks()`）。
    -   然而，`asyncio.gather(*tasks)` 直接返回的是一个**Future对象**，它代表了未来将要完成的一组任务，但它本身不是一个协程。
    -   当你把一个Future而不是协程传给`asyncio.run()`时，它无法处理，因此会抛出 `ValueError: a coroutine was expected`。
    -   **正确做法**：必须将`await asyncio.gather(*tasks)`这行代码包装在一个`async def`函数内，然后将这个函数调用（即协程）传递给`asyncio.run()`。

2.  **为什么 `asyncio.run(await asyncio.gather(*tasks))` 是错的？**
    -   **错误原因**：这是一个纯粹的Python语法错误。`await`关键字**只能**在由`async def`声明的异步函数内部使用。
    -   在上面的例子中，`trigger_event_loop2`是一个普通的同步函数（由`def`定义），在同步函数中直接使用`await`是非法的。
    -   因此，Python解释器在解析代码时就会直接报`SyntaxError: 'await' outside async function`，甚至等不到代码运行。

<br><br><br><br>
## 深入对比：`asyncio.run()` vs `loop.run_until_complete()`

`loop.run_until_complete()` 是一个更低级的API，在`asyncio.run()`出现之前（Python 3.7以前），它是启动异步任务的主要方式。它们都能启动事件循环，但有本质区别。

| 特性 | `asyncio.run()` (高级API) | `loop.run_until_complete()` (低级API) |
| :--- | :--- | :--- |
| **API层级** | **高级 (High-level)** | **低级 (Low-level)** |
| **循环管理** | **全自动** (创建、运行、关闭) | **手动** (需要手动获取和关闭循环) |
| **推荐用法** | **现代首选**，简洁、安全 | **旧式**，或用于需要精细控制循环的复杂场景 |
| **简洁性** | 非常简洁，一行代码搞定 | 相对繁琐，需要多行代码来管理循环 |

### `loop.run_until_complete()` 的手动工作流

使用低级API，你必须像这样手动管理所有步骤：

```python
import asyncio

async def main():
    print("Hello")
    await asyncio.sleep(1)
    print("World")

# 1. 手动获取事件循环
loop = asyncio.get_event_loop()
try:
    # 2. 手动运行任务
    loop.run_until_complete(main())
finally:
    # 3. 手动关闭循环
    loop.close()
```

### 结论

-   **优先使用 `asyncio.run()`**：对于绝大多数应用，特别是启动主程序，`asyncio.run()` 更简单、更安全，能有效避免忘记关闭循环等资源泄露问题。
-   **何时使用 `loop.run_until_complete()`**：当你需要与一个长期运行的线程中的事件循环进行复杂的交互，或者在一些需要精细控制循环生命周期的库或框架中，这个低级API才有用武之地。对于普通应用程序开发，基本可以忘记它。

<br><br><br><br>

## 为什么要用解包 `asyncio.gather(*tasks)` 而不是直接`asyncio.gather(tasks)`?”


__原因分析__：

1. __`asyncio.gather`的函数签名__：首先，需要理解`asyncio.gather`期望接收什么样的参数。它的函数签名类似于 `asyncio.gather(*aws, loop=None, return_exceptions=False)`。这里的 `*aws` 是关键，它表示`gather`接收的&#x662F;__&#x4EFB;意数量的位置参数__（variable number of positional arguments），而不是一个单一的列表参数。

   - __正确调用__：`asyncio.gather(task1, task2, task3, ...)`
   - __错误调用__：`asyncio.gather([task1, task2, task3])`

2. __`*`（星号）的作用__：在函&#x6570;__&#x8C03;&#x7528;__&#x65F6;，`*`操作符的作用是**解包（unpacking）**一个可迭代对象（如列表或元组）。它会将列表中的每一个元素作为独立的参数传递给函数。

   - 假设 `tasks = [task1, task2, task3]`。
   - 调用 `asyncio.gather(*tasks)` 就等同于调用 `asyncio.gather(task1, task2, task3)`。这完全符合`gather`的函数签名。
   - 而如果直接调用 `asyncio.gather(tasks)`，则相当于调用 `asyncio.gather([task1, task2, task3])`。`gather`会把整个列表`[task1, task2, task3]`当&#x4F5C;__&#x4E00;&#x4E2A;__&#x53C2;数，而它期望的是多个独立的任务参数，这会导致`TypeError`或不符合预期的行为（它会尝试`await`一个列表，这是错误的）。


### 小结

- `asyncio.gather`需要的&#x662F;__&#x591A;个独立的任&#x52A1;__&#x4F5C;为参数。
- `tasks`是一&#x4E2A;__&#x5305;含多个任务的列表__。
- `*tasks`的作用就是把这个列表“打开”，将其中的每个任务作为独立的参数传给`gather`。
