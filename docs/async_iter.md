## 什么是异步迭代器
async iterator
实现了 _和 __anext__()方法的对象。__anext__()必须返回一个awaitable 对象。
async for 会处理异步迭代器的__anext__() 返回的awaitable 对象， 知道遇到一个stopAsyncIteration异常。

类似同步迭代器， aysnc iterator也可以实现__iter__()return 自己， 这样它又是一个aysnc iterable.


## 什么是异步可等待对象
aysnc iterable
可以被 aysnc for 使用的对象，  必须通过它的__aiter__() 返回一个async iterator.





