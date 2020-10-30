"""
BSD 2-Clause License

Copyright (c) 2020, Davide De Tommaso (dtmdvd@gmail.com)
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

from threading import Thread
from concurrent.futures import thread
import concurrent.futures
import threading
import time
import pandas as pd
import os
import sys
import logging
import atexit
import linecache
import traceback

atexit.unregister(concurrent.futures.thread._python_exit)


class PykronLogger:
    FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    LOGGING_LEVEL = logging.DEBUG
    LOGGING_PATH = None
    _instance = None

    @staticmethod
    def getInstance():
        if PykronLogger._instance == None:
            PykronLogger()
        return PykronLogger._instance

    def __init__(self):
        if PykronLogger._instance != None:
            raise Exception("This class is a singleton!")
        else:
            PykronLogger._instance = self
            self._logger = logging.getLogger('pykron')
            self._logger.setLevel(PykronLogger.LOGGING_LEVEL)
            if not PykronLogger.LOGGING_PATH is None:
                filename = os.path.join(PykronLogger.LOGGING_PATH, 'pykron.log')
                ch = logging.FileHandler(filename)
            else:
                ch = logging.StreamHandler()
            ch.setLevel(PykronLogger.LOGGING_LEVEL)
            formatter = logging.Formatter(PykronLogger.FORMAT)
            ch.setFormatter(formatter)
            self._logger.addHandler(ch)

    @property
    def log(self):
       return self._logger

class Task:

    IDLE    = 'IDLE'
    RUNNING = 'RUNNING'
    SUCCEED = 'SUCCEED'
    FAILED  = 'FAILED'
    TIMEOUT = 'TIMEOUT'

    TIMEOUT_DEFAULT = 10.0

    EXECUTIONS = {}

    def __init__(self, target, args, timeout=TIMEOUT_DEFAULT, name=None):
        self._target = target
        self._args = args
        self._timeout = timeout
        self._retval = None
        self._status = Task.IDLE
        self._start_ts = None
        self._end_ts = None
        self._duration = None
        self._exception = None
        self._task_id = threading.get_native_id()
        self._logger = PykronLogger.getInstance()

        if name:
            self._name = name
        else:
            self._name = self._target.__name__

        if not self.name in Task.EXECUTIONS.keys():
            Task.EXECUTIONS[self.name] = []

        self._arrival_ts = time.perf_counter()

    def __str__(self):
        return """>> Task '%s'
                Status: %s
                Duration:  %.4f (s)
                Idle time: %.4f (s)
                Return value: %s
                Exception: %s
                """ % (self.name, self.status, self.duration, self.idle_time, str(self.retval), self.exception)

    @property
    def args(self):
        return self._args

    @property
    def arrival_ts(self):
        return self._arrival_ts

    @property
    def duration(self):
        if not self._start_ts is None or self._end_ts is None:
            return self._end_ts - self._start_ts
        return None

    @property
    def end_ts(self):
        return self._end_ts

    @property
    def exception(self):
        return self._exception

    @property
    def idle_time(self):
        if not self._start_ts is None or self._arrival_ts is None:
            return self._start_ts - self._arrival_ts
        return None

    @property
    def name(self):
        return self._name

    @property
    def retval(self):
        return self._retval

    @property
    def status(self):
        return self._status

    @property
    def start_ts(self):
        return self._start_ts

    @property
    def timeout(self):
        return self._timeout

    def run(self):
        self._start_ts = time.perf_counter()
        self._status = Task.RUNNING
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        waitForShutdown = True
        try:
            self._logger.log.debug("T%d: Starting task %s() " % (self._task_id, self._name))
            future = executor.submit(self._target, *self._args)
            t = future.result(timeout=self._timeout)
            self._retval = t
            self._status = Task.SUCCEED
        except concurrent.futures.TimeoutError:
            self._status = Task.TIMEOUT
            waitForShutdown = False
            self._logger.log.error("T%d: Timeout occurred after %.2fs for task %s()" % (self._task_id, self._timeout, self._name))
        except Exception as e:
            exc_type, exc_obj, tb = sys.exc_info()
            f = traceback.extract_tb(tb)[-1]
            lineno = f.lineno
            filename = f.filename
            self._logger.log.error('T%d: def %s(): generated an exception: %s - Line: %s,  File: %s' % (self._task_id, self.name, e, lineno, filename))
            self._status = Task.FAILED
            self._exception = e
        finally:
            self._end_ts = time.perf_counter()
            Task.EXECUTIONS[self.name].append([str(time.ctime()), self.status, self.start_ts, self.end_ts, self.duration, self.idle_time, str(self.retval), str(self.exception), str(self.args)])
            self._logger.log.debug("T%d: Task %s() completed! Status: %s, Duration: %.4f" % (self._task_id, self._name, self.status, self.duration))

        executor.shutdown(wait=waitForShutdown)

        return self._retval


class AsyncRequest:

    @staticmethod
    def decorator(timeout=Task.TIMEOUT_DEFAULT):
        def wrapper(foo):
            def f(*args, **kwargs):
                task = Task(target=foo,
                            args=args,
                            timeout=timeout)
                req = AsyncRequest(task)
                return req
            return f
        return wrapper

    @staticmethod
    def join(requests):
        futures = {}
        return_values = []
        idx = 0

        for req in requests:
            futures[req.future] = idx
            return_values.append(None)
            idx += 1

        for future in concurrent.futures.as_completed(futures):
            return_values[futures[future]] = future.result()

        return return_values

    @staticmethod
    def getExecutions():
        return Task.EXECUTIONS

    @staticmethod
    def getExecutionsByName(func_name):
        if func_name in Task.EXECUTIONS.keys():
            return Task.EXECUTIONS[func_name]
        return None

    @staticmethod
    def exportExecutions(filepath='.', mode='w'):
        for k,v in Task.EXECUTIONS.items():
            df = pd.DataFrame(v, columns=['Datetime', 'Status', 'Start_Ts', 'End_Ts', 'Duration', 'Idle_Time', 'Return_Value', 'Exception', 'Args'])
            df.to_csv(os.path.join(filepath, k + '.csv'), sep=',', encoding='utf-8', index=False, mode=mode)

    def __init__(self, task):
        self._task = task
        self._timeout = task.timeout
        self._callback = None
        self._logger = PykronLogger.getInstance()
        self._executor = concurrent.futures.ThreadPoolExecutor()
        self._future = self._executor.submit(self.run)

    @property
    def future(self):
        return self._future

    def wait_for_completed(self, timeout=Task.TIMEOUT_DEFAULT, callback=None):
        if callback:
            self._callback = callback
        try:
            self.future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            self._logger.log.error("Timeout occurred for wait_for_completed() after %.2fs for task %s() due to wait_for_completed timeout" % (timeout, self._task.name))
        return self

    def run(self):
        res = self._task.run()
        if self._callback:
            self._callback(self._task)
