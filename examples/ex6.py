import sys
sys.path.append('..')

from pykron.core import Pykron
from pykron.logging import PykronLogger
import time
import threading

app = Pykron()

@app.AsyncRequest()
def foo():
    time.sleep(1)

for _ in range(0,1000000):
    foo.asyn()

app.close()
