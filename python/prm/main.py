from library_1 import foo_1
import library_2
import os
from os import (
        getenv,
        environ,
        )

class Class():
    field = "this"

a = foo_1(1)
b = library_2.foo_2(2)
c = os.getcwd()
d = Class()
e = d.field
