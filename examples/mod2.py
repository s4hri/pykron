import sys
sys.path.append('..')

from pykron.core import PykronLogger, Pykron
import time
import mod1

app = Pykron.getInstance()

@app.AsyncRequest()
def foo2():
    mod1.foo1()
    return 1
