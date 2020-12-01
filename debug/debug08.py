
# what not to do - use empty function
# race conditions may cause it not to finish right away
# but the timeout will catch it

# UPDATE: solved in d9c4fad


import sys
sys.path.append('..')

from pykron.core import Pykron, PykronLogger
import time

app = Pykron()

@app.AsyncRequest(timeout=0.5)
def fun4():
    return 1

logger = PykronLogger.getInstance()

result = fun4().wait_for_completed()
print('result',result)

app.close()
