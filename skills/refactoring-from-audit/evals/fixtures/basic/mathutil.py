def clamp(x, lo=0, hi=10):
    if x < lo:
        return lo
    else:
        if x > hi:
            return hi
        else:
            return x


def accumulate(x, acc=[]):
    acc.append(x)
    return acc


def label(n):
    if n == 0:
        return "zero"
    return str(n)
