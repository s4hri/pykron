"""
BSD 2-Clause License

Copyright (c) 2020, Davide De Tommaso (davide.detommaso@iit.it),
                    Adam Lukomski (adam.lukomski@iit.it),
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


''' how much time does it take to spin up a task?

    for-loop test, with wait_for_completed

    the only difference is no time.sleep(), so the function is awfully quick

    in commit 3212db1 this gets stuck / freezes very frequently
    some iterations get a Timeout - why?

'''

import sys
sys.path.append('..')

from pykron.core import Pykron, Task, PykronLogger

import time
import threading

app = Pykron()

@app.AsyncRequest()
def foo1(t0):
    a = time.perf_counter()-t0
    app.logging.debug(a)
    return a


storage = list()
for i in range(0,10):
    t0 = time.perf_counter()
    val = foo1(t0).wait_for_completed()
    storage.append(val)

for line in storage:
    print(line)

# I like to leave some time to see if the cleanup fails

time.sleep(1)
app.close()
time.sleep(1)
