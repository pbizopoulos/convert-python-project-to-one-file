from os import getcwd

def foo_2(input_):
    return str(input_ + 1)

def foo_1(input_):
    return input_ + 1

class Class:
    field = 'this'
a = foo_1(1)
b = foo_2(2)
c = getcwd()
d = Class()
e = d.field