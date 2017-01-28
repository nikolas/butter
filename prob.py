import math
import random

def cumsum(l, t=0):
    """Return the cumulative sum of an iterable"""
    r = [None] * len(l)
    for i,v in enumerate(l):
        r[i] = t = t+v
    return r

def lookup(p, k):
    """Given a cumulative distribution of discrete values, return the value at
    k"""
    lo = 0
    hi = len(p)-1
    while True:
        if lo == hi: return lo
        mid = hi - (hi-lo)//2
        if p[mid] > k:
            hi = mid-1
        else:
            lo = mid

def weighted_sample(weights, k):
    """Return a list of k choices in the range [0, len(weights)) with the
    probabilities specified in weights"""
    cum = [0]+cumsum(weights)
    n = cum[-1]
    result = [None] * k
    selected = set()

    for i in range(k):
        j = random.randrange(n)
        while lookup(cum, j) in selected:
            j = random.randrange(n)
        result[i] = lookup(cum, j)
        selected.add(result[i])
    return result

def weighted_choice(weights):
    """Return an integer in the range [0, len(weights)) with the probabilities
    specified in weights"""
    cum = [0]+cumsum(weights)
    n = cum[-1]
    return lookup(cum, random.randrange(n))

def linspace(start, stop, num, endpoint=True):
    """Like range(), but takes a count for the number of samples; see also
    Numpy."""
    if num < 2:
        raise Exception('must have at least 2 steps!')

    if endpoint:
        num -= 1
    step = (stop - start) // num
    for i in range(num):
        yield start + step * i
    if endpoint:
        yield stop
