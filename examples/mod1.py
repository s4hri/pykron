import sys
sys.path.append('..')

from pykron.core import PykronLogger, Pykron

app = Pykron.getInstance()

@app.AsyncRequest()
def foo1():
    return 1
