from typing import Callable
import builtins


ret = {
    name:getattr(builtins, name) for name in dir(builtins)
    if isinstance(getattr(builtins, name), Callable)
}

for r in ret:
    print(f"'{r}' : None,")

"""
abs
aiter
all
anext
any
ascii
bin
bool
breakpoint
bytearray
bytes
callable
chr
classmethod
compile
complex
copyright
credits
delattr
dict
dir
divmod
enumerate
eval
exec
exit
filter
float
format
frozenset
getattr
globals
hasattr
hash
help
hex
id
input
int
isinstance
issubclass
iter
len
license
list
locals
map
max
memoryview
min
next
object
oct
open
ord
pow
print
property
quit
range
repr
reversed
round
set
setattr
slice
sorted
staticmethod
str
sum
super
tuple
type
vars
zip
"""