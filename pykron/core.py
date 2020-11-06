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
from inspect import getframeinfo, stack
import concurrent.futures
import threading
import time
import os
import sys
import csv
import linecache
import traceback

from pykron.logging import PykronLogger

class Task:

    IDLE    = 'IDLE'
    RUNNING = 'RUNNING'
    SUCCEED = 'SUCCEED'
    FAILED  = 'FAILED'
    TIMEOUT = 'TIMEOUT'

    def __init__(self, target, args, timeout, parent_id):
        self._target = target
        self._args = args
        self._timeout = timeout
        self._retval = None
        self._status = Task.IDLE
        self._start_ts = None
        self._end_ts = None
        self._duration = None
        self._exception = None
        self._logger = PykronLogger.getInstance()
        self._parent_id = parent_id

        self._func_name = self._target.__name__

        caller = getframeinfo(stack()[2][0])
        self._name = "%s[%s:%d]" % (self._func_name, caller.filename, caller.lineno)

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
    def func_name(self):
        return self._func_name

    @property
    def idle_time(self):
        if not self._start_ts is None or self._arrival_ts is None:
            return self._start_ts - self._arrival_ts
        return None

    @property
    def parent_id(self):
        return self._parent_id

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
    def thread_id(self):
        return self._thread_id

    @property
    def timeout(self):
        return self._timeout

    def submit(self, timeout):
        self._timeout = timeout
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = self._executor.submit(self.run)
        return future

    def cancel(self):
        self._logger.log.debug("%s: Task cancelling %s() [Thread id: T%d, Parent id: T%d]" % (self.name, self.func_name, self._thread_id, self._parent_id))
        self._executor.shutdown(wait=False)

    def run(self):
        self._thread_id = threading.get_native_id() + 1
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = executor.submit(self._target, *self._args)
        self._logger.log.debug("%s: Task starting %s() [Thread id: T%d, Parent id: T%d]" % (self.name, self.func_name, self._thread_id, self._parent_id))
        self._start_ts = time.perf_counter()
        self._status = Task.RUNNING
        try:
            self._retval = future.result(timeout=self.timeout)
            self._status = Task.SUCCEED
        except concurrent.futures.TimeoutError:
            self._status = Task.TIMEOUT
            self._exception = concurrent.futures.TimeoutError
            self._logger.log.error("%s: Timeout occurred after %.2fs" % (self.name, self._timeout))
        except Exception as e:
            exc_type, exc_obj, tb = sys.exc_info()
            f = traceback.extract_tb(tb)[-1]
            lineno = f.lineno
            filename = f.filename
            self._logger.log.error('%s: def %s: generated an exception: %s - Line: %s,  File: %s' % (self.name, self.func_name, e, lineno, filename))
            self._status = Task.FAILED
            self._exception = e
        finally:
            self._end_ts = time.perf_counter()
            self._logger.log.debug("%s: Task completed! Status: %s, Duration: %.4f" % (self.name, self.status, self.duration))

class PykronManager:

    _instance = None
    TIMEOUT_DEFAULT = 10.0

    @staticmethod
    def getInstance():
        if PykronManager._instance == None:
            PykronManager()
        return PykronManager._instance

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

    def __init__(self):
        if PykronManager._instance != None:
            raise Exception("This class is a singleton!")
        else:
            PykronManager._instance = self
        self._logger = PykronLogger.getInstance()

        self._requests = {}
        self._parents = {}
        self._futures = {}
        self._task_executions = {}


    def createRequest(self, task, timeout):
        req = AsyncRequest(task, timeout)
        req_id = task.thread_id
        self._requests[req_id] = req
        self._parents[req_id] = task.parent_id
        self._futures[req_id] = req.future

        if not task.name in self._task_executions.keys():
            self._task_executions[task.name] = []
        self._futures[req_id].add_done_callback(self.completed)
        return req

    def completed(self, future):
        req_id = [k for k, v in self._futures.items() if v == future][0]
        task = self._requests[req_id].task
        task_exec = [str(time.ctime()), task.func_name, task.name, task.status, task.start_ts, task.end_ts, task.duration, task.idle_time, str(task.retval), str(task.exception), str(task.args)]
        self._task_executions[task.name].append(task_exec)
        if task.status != Task.SUCCEED:
            #req_id = [k for k, v in self._parents.items() if v == task.parent_id][0]
            #self._requests[self._parents[req_id]].task.cancel()
            pass
        self._logger.log_execution(task_exec)

class AsyncRequest:

    @staticmethod
    def decorator(timeout=PykronManager.TIMEOUT_DEFAULT):
        def wrapper(foo):
            def f(*args, **kwargs):
                task = Task(target=foo,
                            args=args,
                            timeout=timeout,
                            parent_id=threading.get_native_id())
                return PykronManager.getInstance().createRequest(task, timeout)
            return f
        return wrapper

    def __init__(self, task, timeout):
        self._task = task
        self._timeout = timeout
        self._callback = None
        self._logger = PykronLogger.getInstance()
        self._future = task.submit(timeout)

    @property
    def future(self):
        return self._future

    @property
    def task(self):
        return self._task

    def on_completed(self, callback):
        self._callback = callback

    def wait_for_completed(self, timeout=None, callback=None):
        if timeout is None:
            timeout = self._timeout
        self._task._timeout = timeout
        self.on_completed(callback)
        self.future.result()
        if self._callback:
            self._callback(self._task)
        return self._task.retval
