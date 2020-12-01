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
from concurrent.futures import thread, ThreadPoolExecutor
from inspect import getframeinfo, stack
import concurrent.futures
import threading
import time
import os
import sys
import csv
import linecache
import traceback
import asyncio
import logging
import ctypes
import inspect

from pykron.logging import PykronLogger

import concurrent
import atexit

atexit.unregister(concurrent.futures.thread._python_exit)

class Task:

    FAILED     = 'FAILED'
    IDLE       = 'IDLE'
    CANCELLED  = 'CANCELLED'
    RUNNING    = 'RUNNING'
    SUCCEED    = 'SUCCEED'
    TIMEOUT    = 'TIMEOUT'

    def __init__(self, target, args, parent_id):
        self._target = target
        self._args = args
        self._retval = None
        self._status = Task.IDLE
        self._start_ts = None
        self._end_ts = None
        self._duration = None
        self._exception = None
        self._logger = PykronLogger.getInstance()
        self._parent_id = parent_id
        self._func_name = self._target.__name__
        self._task_id = threading.current_thread().ident
        caller = getframeinfo(stack()[2][0])
        self._name = "%s[%s:%d]" % (self._func_name, caller.filename, caller.lineno)
        self._arrival_ts = time.perf_counter()

    def __str__(self):
        return """>> Task '%s'
                Status: %s
                Duration:  %.2f (s)
                Idle time: %.2f (s)
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
        return self._end_ts - self._start_ts

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
        return self._start_ts - self._arrival_ts

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
    def task_id(self):
        return self._task_id

    def completed(self, future):
        self._end_ts = time.perf_counter()
        try:
            self._retval = future.result()
            self._status = Task.SUCCEED
        except TimeoutError:
            e = "%s(): Timeout occurred!" % (self.func_name)
            self._exception = e
            self._status = Task.TIMEOUT
        except asyncio.CancelledError:
            e = "%s(): Task Cancelled!" % (self.func_name)
            self._exception = e
            self._status = Task.CANCELLED
        except Exception as e:
            exc_type, exc_obj, tb = sys.exc_info()
            f = traceback.extract_tb(tb)[-1]
            lineno = f.lineno
            filename = f.filename
            e = "%s(): Generated an exception: '%s' Line: %s,  File: %s" % (self.func_name, e, lineno, filename)
            self._exception = e
            self._status = Task.FAILED
            self._logger.log.error("%s: %s" % (self.name, e))
        self._logger.log.debug("%s: Task completed! Status: %s, Duration: %.2f [Task id: T%d]" % (self.name, self.status, self.duration, self._task_id))

    def run(self):
        self._task_id = threading.current_thread().ident
        self._logger.log.debug("%s: Task starting ... [Task id: T%d, Parent id: T%d]" % (self.name, self._task_id, self.parent_id))
        self._status = Task.RUNNING
        self._start_ts = time.perf_counter()
        return self._target(*self._args)

class Pykron:

    _instance = None
    TIMEOUT_DEFAULT = 10.0

    @staticmethod
    def AsyncRequest(timeout=TIMEOUT_DEFAULT):
        def wrapper(foo):
            def f(*args, **kwargs):
                parent_id = threading.current_thread().ident
                task = Task(target=foo,
                            args=args,
                            parent_id=parent_id)

                return Pykron.getInstance().createRequest(task, timeout)
            return f
        return wrapper

    @staticmethod
    def getInstance():
        if Pykron._instance == None:
            Pykron()
        return Pykron._instance

    @staticmethod
    def join(requests):
        return_values = []
        executors = {}

        for req in requests:
            req.wait_for_completed()

        for req in requests:
            try:
                return_values.append(req.future.result())
            except:
                return_values.append(None)


        return return_values

    def __init__(self, logging_level=logging.DEBUG):
        if Pykron._instance != None:
            Pykron.getInstance()
        else:
            Pykron._instance = self
            self._logger = PykronLogger.getInstance()
            self._logger.LOGGING_LEVEL = logging_level

            self._requests = {}
            self._parents = {}
            self._futures = {}
            self._task_executions = {}
            self.loop = asyncio.get_event_loop()
            self._worker_thread = threading.Thread(target=self.worker)
            self._worker_thread.start()

    @property
    def logger(self):
        return self._logger

    def worker(self):
        self.loop.run_forever()

    def close(self):
        self.loop.call_soon_threadsafe(self.loop.stop)
        self._worker_thread.join()
        Pykron._instance = None

    def createRequest(self, task, timeout):
        req = AsyncRequest(self.loop, task, timeout)
        req_id = task.task_id
        self._requests[req_id] = req
        self._parents[req_id] = task.parent_id
        self._futures[req_id] = req.future
        if not task.name in self._task_executions.keys():
            self._task_executions[task.name] = []
        req.future.add_done_callback(self.on_completed)
        return req

    def on_completed(self, future):
        req_id = [k for k, v in self._futures.items() if v == future][0]
        task = self._requests[req_id].task
        task.completed(future)
        if task.status != Task.SUCCEED:
            if threading.main_thread().ident != task.parent_id:
                parent_req = Pykron.getInstance().getRequest(task._parent_id)
                parent_req.cancel()
        if task.status != Task.TIMEOUT:
            self._requests[req_id].stop_timeout_handler()
        task_exec = [str(time.ctime()), task.func_name, task.name, task.status, task.start_ts, task.end_ts, task.duration, task.idle_time, str(task.retval), str(task.exception), str(task.args)]
        self._task_executions[task.name].append(task_exec)
        self._logger.log_execution(task_exec)
        self._requests[req_id].set_completed()

    def getRequest(self, req_id):
        return self._requests[req_id]

class AsyncRequest:

    def __init__(self, loop, task, timeout):
        self._task = task
        self._timeout = timeout
        self._loop = loop
        self._callback = None
        self._timeout_handler_id = None
        self._logger = PykronLogger.getInstance()
        self._completed = threading.Event()
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._future = loop.run_in_executor(self._executor, task.run)
        self._future_timer = loop.run_in_executor(self._executor, loop.call_later, timeout, self.timeout_cb)

    @property
    def executor(self):
        return self._executor

    @property
    def future(self):
        return self._future

    @property
    def req_id(self):
        return self.task.task_id

    @property
    def task(self):
        return self._task

    @property
    def timeout(self):
        return self._timeout

    def _stop_thread(self, tid, exctype):
        """raises the exception, performs cleanup if needed"""
        if not inspect.isclass(exctype):
            raise TypeError("Only types can be raised (not instances)")
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), ctypes.py_object(exctype))
        if res == 0:
            raise ValueError("invalid thread id")
        elif res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, 0)
            raise SystemError("PyThreadState_SetAsyncExc failed")

    def cancel(self):
        self._logger.log.error("%s: Task cancelling ... [Task id: T%d, Parent id: T%d]" % (self.task.name, self.task.task_id, self.task.parent_id))
        self.executor.shutdown(wait=False)
        self.stop_timeout_handler()
        self._stop_thread(self.req_id, SystemExit)
        self._loop.call_soon_threadsafe(self.future.cancel)

    def on_completed(self, callback):
        self._callback = callback

    def set_completed(self):
        self._completed.set()

    def stop_timeout_handler(self):
        timeout_handler = self._future_timer.result()
        timeout_handler.cancel()

    def timeout_cb(self):
        if not self.future.done():
            self._logger.log.error("%s: Timeout occurred after %.2fs" % (self.task.name, self.timeout))
            self.future.set_exception(TimeoutError)

    def wait_for_completed(self, timeout=Pykron.TIMEOUT_DEFAULT, callback=None):
        if timeout is None:
            timeout = self._timeout
        self._task._timeout = timeout
        self.on_completed(callback)
        res = self._completed.wait(timeout=timeout)
        if res is True:
            if callback:
                callback(self._task)
            return self._task.retval
        else:
            self._logger.log.error("%s: Timeout occurred on wait_for_completed after %.2fs" % (self.task.name, timeout))
            return None
