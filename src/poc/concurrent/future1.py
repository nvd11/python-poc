from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import time


def func(value):
    print(f"Function called with value: {value}")
    time.sleep(2)
    print(f"Function ended with value: {value}")
    return value

# create a thread pool
thread_pool = ThreadPoolExecutor(max_workers=5)


# create a process pool
# process_pool = ProcessPoolExecutor(max_workers=5)


# pls note that we submitted 10 tasks but we just have 5 workers in the pool
for i in range(10):
    # here it's the Future object
    future = thread_pool.submit(func, i)
    print(f"Submitted task {i}, future: {future}, type of future: {type(future)}")

