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


''' cancel a task that is running for 10 seconds

may crash because:
    time.sleep(10) does not want to be killed
    even when it allows to kill a thread (exception injection):
    there is nothing after time.sleep(10) so there is
    a race condition between natural ending and forced killing
    of a thread

'''

import sys
sys.path.append('..')

from pykron.core import Pykron, Task, PykronLogger

import time
import threading

app = Pykron.getInstance()

@app.AsyncRequest()
def foo1():
    time.sleep(10)


mytask = foo1()

time.sleep(1)
print("Trying to cancel")
mytask.cancel()
print("Cancel has been sent, waiting")
time.sleep(10)

app.close()
