"""
BSD 2-Clause License

Copyright (c) 2021, Davide De Tommaso (dtmdvd@gmail.com)
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

import sys
sys.path.append('..')

from pykron.core import Pykron
from pykron.logging import PykronLogger
import time

logger = PykronLogger(save_csv=True)

if sys.version_info > (3,7):
    app = Pykron(profiling=True, pykron_logger=logger)
else:
    app = Pykron(pykron_logger=logger)

@app.AsyncRequest(timeout=120)
def fun1():
    app.logging.debug("Fun 1 reporting in")
    time.sleep(1)
    app.logging.debug("Fun 1 reporting out")
    time.sleep(1)
    return 1

@app.AsyncRequest(timeout=120)
def fun2():
    app.logging.debug("Fun 2 reporting in")
    time.sleep(1)
    fun1()
    app.logging.debug("Fun 2 reporting out")
    time.sleep(1)
    return 1

@app.AsyncRequest(timeout=120)
def fun3():
    app.logging.debug("Fun 3 reporting in")
    time.sleep(1)
    fun2()
    app.logging.debug("Fun 3 reporting out")
    time.sleep(1)
    return 1

@app.AsyncRequest(timeout=120)
def fun4():
    app.logging.debug("Fun 4 reporting in")
    time.sleep(1)
    fun3()
    app.logging.debug("Fun 4 reporting out")
    time.sleep(1)
    return 1


fun4()
time.sleep(12)

app.close()
