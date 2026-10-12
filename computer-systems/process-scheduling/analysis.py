"""Paired bootstrap and explicitly normalized factorial contrasts."""
import random
from itertools import product

def mean(xs): return sum(xs)/len(xs)

def interval(values, resamples=2000, alpha=.05):
    rng=random.Random(20261012)
    n=len(values)
    samples=sorted(sum(values[rng.randrange(n)] for _ in range(n))/n for _ in range(resamples))
    def quantile(q):
        pos=(len(samples)-1)*q; i=int(pos)
        return samples[i]+(samples[min(i+1,len(samples)-1)]-samples[i])*(pos-i)
    return [quantile(alpha/2),quantile(1-alpha/2)]

def effect(cells, factors):
    # Average over omitted factors; differences over included factors.
    total=0.
    for bits in product((0,1), repeat=3):
        sign=1
        for i in factors: sign *= 1 if bits[i] else -1
        total+=sign*cells[bits]
    return total/(2**(3-len(factors)))
