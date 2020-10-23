import math, gzip
from contextlib import contextmanager


def round_sig(x, digits):
    if x == 0:
        return 0
    elif abs(x) == math.inf or math.isnan(x):
        raise ValueError("Cannot round infinity or NaN")
    else:
        log = math.log10(abs(x))
        digits_above_zero = int(math.floor(log))
        return round(x, digits - 1 - digits_above_zero)
assert round_sig(0.00123, 2) == 0.0012
assert round_sig(1.59e-10, 2) == 1.6e-10


@contextmanager
def read_maybe_gzip(filepath, mode=None):
    is_gzip = False
    with open(filepath, 'rb', buffering=0) as f: # no need for buffers
        if f.read(3) == b'\x1f\x8b\x08':
            is_gzip = True
    if is_gzip:
        with gzip.open(filepath, mode) as f:
            yield f
    else:
        with open(filepath, mode, buffering=2**18) as f: # 256KB buffer
            yield f
