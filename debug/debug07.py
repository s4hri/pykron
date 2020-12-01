
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
import logging
import threading


app = Pykron(logging_level=logging.DEBUG)
logging = PykronLogger.getInstance()

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
