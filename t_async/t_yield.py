def b():
    r = yield from c()
    print("b:", r)


def c():
    r = yield 1
    print("c:", r)
    return 4


gen = b()
c = c()
c.send(None)
c.send("haha")