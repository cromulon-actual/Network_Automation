from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import time
from functools import wraps


def timeit(method):
    @wraps(method)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = method(*args, **kwargs)
        end_time = time.time()
        print(f"{method.__name__} => {(end_time-start_time)*1000} ms")

        return result

    return wrapper


# @timeit
def process(fn, *args, **kwargs):
    def wrapper(*args, **kwargs):
        if args:
            with ProcessPoolExecutor() as executor:
                results = executor.submit(lambda p: fn(*p), args)

        elif kwargs:
            with ProcessPoolExecutor() as executor:
                results = executor.submit(lambda p: fn(*p), kwargs)
        return results.result()

    return wrapper


@timeit
def thread(fn, *args, **kwargs):
    def wrapper(*args, **kwargs):
        if args and not kwargs:
            with ThreadPoolExecutor() as executor:
                print(fn.__name__)
                results = executor.submit(lambda p: fn(*p), args)

                return results.result()

        elif kwargs and not args:
            print(fn.__name__)
            with ThreadPoolExecutor() as executor:
                results = executor.submit(lambda p: fn(*p), kwargs)

                return results.result()
        elif args and kwargs:
            print(type(args))

    return wrapper
