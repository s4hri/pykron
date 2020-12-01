
''' how much time does it take to spin up a task? '''

import sys
sys.path.append('..')

from pykron.core import Pykron, Task, PykronLogger

import time
import logging
import threading

app = Pykron(logging_level=logging.DEBUG)
logging = PykronLogger.getInstance()

@app.AsyncRequest()
def foo1(t0):
    a = time.perf_counter()-t0
    logging.log.debug(a)
    time.sleep(0.5)

t0 = time.perf_counter()
mytask = foo1(t0)
time.sleep(1)

app.close()
