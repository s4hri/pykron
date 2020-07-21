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

from pykron.core import AsyncRequest
import random
import time

DEBUG = True

class Agent:

    def callback(self, arg):
        print(arg)

    @AsyncRequest.decorator(DEBUG=DEBUG)
    def like(self, msg):
        msg = "I like " + msg
        time.sleep(3)
        self.see()
        return 1

    @AsyncRequest.decorator(DEBUG=DEBUG)
    def see(self, msg):
        a = 1/0
        msg = "I see " + msg
        time.sleep(1)
        print(msg)
        return 2

    def bye(self):
        print("Bye bye")


jojo = Agent()
a = jojo.like("strawberries").on_completed(callback=jojo.callback)
b = jojo.like("bananas").on_completed(callback=jojo.callback)
#b = jojo.see("bananas").on_completed(callback=jojo.callback)
AsyncRequest.join([a,b])
jojo.bye()

def callback(task):
    print(task)


@AsyncRequest.decorator(DEBUG=DEBUG)
def foo1():
    time.sleep(3)
    print("foo1")
    return 1

@AsyncRequest.decorator(timeout=1.0, DEBUG=DEBUG)
def foo2():
    time.sleep(2)
    print("foo2")
    return 2


a = foo1().wait_for_completed(callback=callback)
print("foo1 completed")
b = foo2().wait_for_completed(callback=callback)
print("foo2 completed")

AsyncRequest.exportExecutions()
