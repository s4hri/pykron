import sys
sys.path.append('..')

from pykron.core import Pykron, Task
from pykron.logging import PykronLogger
import time
import threading

app = Pykron(logging_file=True, save_csv=True)

@Pykron.AsyncRequest()
def foo1():
    res = foo2().wait_for_completed()
    time.sleep(5)
    return 1

# A never-ending function
@Pykron.AsyncRequest()
def foo2():
    while True:
        print("I am alive! ")
        time.sleep(1)
        foo3()
        time.sleep(2)

# User-defined callback function running once the foo1 ends
def on_completed(task):
    if task.status == Task.SUCCEED:
        self.fail()

# A bugged function
@Pykron.AsyncRequest(callback=on_completed)
def foo3():
    time.sleep(1)
    return 1/0

req = foo1()
req.wait_for_completed()
time.sleep(5)
