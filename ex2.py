"""
BSD 2-Clause License

Copyright (c) 2020, Davide De Tommaso (dtmdvd@gmail.com)
                    Social Cognition in Human-Robot Interaction
                    Istituto Italiano di Tecnologia (IIT)
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

from pykron.core import AsyncRequest, Task
from pykron.logging import PykronLogger

import time
import logging


# You can assign to AsyncRequest.LOGGING_LEVEL any standard Python logging level
PykronLogger.LOGGING_LEVEL = logging.DEBUG

# 2-levels nested function foo1->foo2->foo3
@AsyncRequest.decorator()
def foo1():
    res = foo2().wait_for_completed()
    print('foo2 = ', res)
    time.sleep(5)
    return 1

# A never-ending function
@AsyncRequest.decorator()
def foo2():
    while True:
        print("foo2 I am alive!")
        time.sleep(1)
        foo3()
        time.sleep(2)
    return 2

# A bugged function
@AsyncRequest.decorator()
def foo3():
    return 1/0

# User-defined callback function running once the foo1 ends
def on_completed(task):
    if task.status == Task.SUCCEED:
        print("Everything's fine")
    else:
        print("Something goes wrong")

foo1().wait_for_completed(callback=on_completed)
print("FIN")
