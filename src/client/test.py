# f o g o h == f(g(h(x)))
#
# implement chain(..) so we can do:
# F = chain(f, g, h)
# F(x) == f(g(h(x)))
#
# example:
from functools import reduce

f = lambda x: x + 1
g = lambda x: x * 2
h = lambda x: x - 3
#
# F(9) == ? # 13
#
# h(x) == 9-3
# g(..) == 12
# f(..) == 13


def chain(*funcs):
    def chained_call(arg):
        a = arg
        return reduce(lambda r, f: f(r), funcs, arg)
    return chained_call


@chain
def fn(param: int):
    return

F = chain(h, g, f)
print(F(9))

print(fn(9))

