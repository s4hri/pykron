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

    for-loop test, classic style

    very quick function, this time the measurements are before-during and during-after

    in commit 3212db1 works perfectly, but exhibits strange total time variability

'''

import sys
sys.path.append('..')

from pykron.core import Pykron, Task, PykronLogger

import time
import threading

if sys.version_info > (3,7):
    app = Pykron.getInstance(profiling=True)
else:
    app = Pykron.getInstance()

@app.AsyncRequest()
def foo1(t0):
    a = time.perf_counter()-t0
    app.logging.debug(a)
    return (a,time.perf_counter())


storage = list() # touple, contains both times
for i in range(0,100):
    t0 = time.perf_counter()

    mytask = foo1(t0)
    time.sleep(0.1)
    storage.append(mytask.future.result()[0])

for line in storage:
    print(line)


# I like to leave some time to see if the cleanup fails

time.sleep(1)
app.close()
time.sleep(1)
