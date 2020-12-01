#!/usr/bin/env python3
# how much time does it take to stop the loop?

import sys
sys.path.append('..')

from pykron.core import Pykron, PykronLogger

import time

app = Pykron()

@app.AsyncRequest(timeout=120)
def fun4():
    logger.log.debug("Fun 4 reporting in")
    time.sleep(1)
    #fun3()
    logger.log.debug("Fun 4 reporting out")
    time.sleep(1)


logger = PykronLogger.getInstance()
fun4()
time.sleep(2.5)

app.close()
a = time.time()

while app.loop.is_running():
    pass

print('time needed to stop:', time.time()-a )
