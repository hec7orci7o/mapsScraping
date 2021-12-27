import random

def f(x: int, t: int) -> float:
    return t / (x + 1)

def g(x: int, m: int, k: int) -> float:
    return k*x / m + f(x, m) - k

def calc(x: int) -> float:
    m = 100
    k = 0.5
    t = random.uniform(0.4, 0.6)
    if x <= m:
        return f(x, t)
    else: 
        return g(x, m, k)