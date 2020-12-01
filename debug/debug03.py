
''' how much time does it take to spin up a task?

    for-loop test, first native, debug04 is with wait_for_completed

'''

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
    time.sleep(0.2)
    return a

storage = list()
for i in range(0,10):
    t0 = time.perf_counter()

    mytask = foo1(t0)
    time.sleep(1)
    storage.append(mytask.future.result())

for line in storage:
    print(line)


# I like to leave some time to see if the cleanup fails

time.sleep(1)
app.close()
time.sleep(1)
