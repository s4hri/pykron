"""
BSD 2-Clause License

Copyright (c) 2021, Davide De Tommaso (davide.detommaso@iit.it),
                    Adam Lukomski (adam.lukomski@iit.it),
                    Social Cognition in Human-Robot Interaction
                    Istituto Italiano di Tecnologia, Genova
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
import concurrent

from pykron.logging import PykronLogger
from pykron.profiling import PykronProfiler

class Task:

    FAILED     = 'FAILED'
    IDLE       = 'IDLE'
    CANCELLED  = 'CANCELLED'
    RUNNING    = 'RUNNING'
    SUCCEED    = 'SUCCEED'
    TIMEOUT    = 'TIMEOUT'

    def __init__(self, task_id, target, args, kwargs, parent_id):
        self._target = target
        self._args = args
        self._kwargs = kwargs
        self._retval = None
        self._status = Task.IDLE
        self._start_ts = None
        self._end_ts = None
        self._duration = None
        self._exception = None
        self._arrival_ts = time.perf_counter()
        self._logger = Pykron.getInstance().logger
        self._parent_id = parent_id
        self._func_name = self._target.__name__
        self._task_id = task_id
        self._timeout = False
        self._profiler = None
        self._name = self._func_name
        self._caller_frame = stack()[2][0]
        caller_module = inspect.getmodule(self._caller_frame.f_code)
        caller_info = getframeinfo(self._caller_frame)
        caller_source = inspect.getsourcelines(caller_module)
        self._func_loc = "[%s:%d]" % (os.path.relpath(inspect.getsourcefile(self._target)), inspect.getsourcelines(self._target)[1]+1)
        self._caller_name = caller_info.function
        self._caller_loc = "[%s:%d]" % (os.path.relpath(caller_info.filename), caller_info.lineno)
        self._started = threading.Event()

    @property
    def args(self):
        return self._args

    @property
    def kwargs(self):
        return self._kwargs

    @property
    def arrival_ts(self):
        return self._arrival_ts

    @property
    def caller_loc(self):
        return self._caller_loc

    @property
    def caller_name(self):
        return self._caller_name

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
    def func_loc(self):
        return self._func_loc

    @property
    def idle_time(self):
        return self._start_ts - self._arrival_ts

    @property
    def logging(self):
        return self._logger.log

    @property
    def parent_id(self):
        return self._parent_id

    @property
    def profiler(self):
        return self._profiler

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
    def started(self):
        return self._started

    @property
    def task_id(self):
        return self._task_id

    @property
    def thread_id(self):
        return self._thread_id

    @property
    def current_thread(self):
        return threading.current_thread()

    def finalize(self, future):
        self._end_ts = time.perf_counter()
        try:
            self._retval = future.result()
            self._status = Task.SUCCEED
        except asyncio.CancelledError:
            if self._timeout:
                self.logging.error("T%d: TIMEOUT OCCURRED! %s(%s) <- %s(%s)" % (self.task_id, self.func_loc, self.func_name, self.caller_loc, self.caller_name))
                self._status = Task.TIMEOUT
            else:
                self._status = Task.CANCELLED
                self.logging.error("T%d: TASK CANCELLED! %s(%s) <- %s(%s)" % (self.task_id, self.func_loc, self.func_name, self.caller_loc, self.caller_name))
        except Exception as e:
            exc_type, exc_obj, tb = sys.exc_info()
            f = traceback.extract_tb(tb)[-1]
            lineno = f.lineno
            filename = f.filename
            self._exception = "%s Line: %s,  File: %s" % (e, lineno, filename)
            self._status = Task.FAILED
            self.logging.error("T%d: TASK FAILED! Exception: %s" % (self.task_id, self._exception))
        self.logging.debug("T%d: TASK COMPLETED! Status: %s, Duration: %.3f %s(%s) <- %s(%s)" % (self.task_id, self.status, self.duration, self.func_loc, self.func_name, self.caller_loc, self.caller_name))


    def run(self):
        self._thread_id = threading.current_thread().ident
        Pykron.getInstance().set_thread_id(self.thread_id, self.task_id)
        self.logging.debug("T%d: TASK STARTED! %s(%s) <- %s(%s)" % (self.task_id, self.func_loc, self.func_name, self.caller_loc, self.caller_name))
        self._start_ts = time.perf_counter()
        self.started.set()
        self._status = Task.RUNNING
        if self._profiler:
            res = self._profiler.runcall(self._target, *self._args, **self._kwargs)
        else:
            res = self._target(*self._args, **self._kwargs)
        return res

    def set_timeout(self):
        self._timeout = True

    def set_profiler(self, profiler):
        self._profiler = profiler

class Pykron:

    _instance = None
    TIMEOUT_DEFAULT = 30.0

    FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    FORMAT_VERBOSE = '%(asctime)s - %(levelname)s - %(module)s - %(process)d - %(thread)d - %(message)s'
    FORMAT_JSON = '{"asctime": "%(asctime)-15s", "created": %(created)f, "relativeCreated": %(relativeCreated)f, "levelname": "%(levelname)s", "module": "%(module)s", "process": %(process)d, "processName": "%(processName)s", "thread": %(thread)d, "threadName": "%(threadName)s", "message": "%(message)s"}'

    LOGGING_LEVEL = logging.DEBUG
    LOGGING_PATH = '.'

    @staticmethod
    def AsyncRequest(timeout=TIMEOUT_DEFAULT, callback=None, cancel_propagation=True):
        def wrapper(target):
                def f(*args, **kwargs):
                    parent_id = threading.current_thread().ident
                    task = Task(task_id=Pykron.getInstance().createTaskId(),
                            target=target,
                            args=args,
                            kwargs=kwargs,
                            parent_id=parent_id)
                    return Pykron.getInstance().createRequest(task, timeout, callback, cancel_propagation)
                return f
        return wrapper

    @staticmethod
    def close():
        app = Pykron.getInstance()
        app.wait_all_completed()
        app.save_csv()
        app.loop.call_soon_threadsafe(app.loop.stop)
        app._worker_thread.join()
        Pykron._instance = None

    @staticmethod
    def getInstance():
        if Pykron._instance == None:
            Pykron()
        return Pykron._instance

    @staticmethod
    def stop_thread(tid, exctype):
        """raises the exception, performs cleanup if needed"""
        if not inspect.isclass(exctype):
            raise TypeError("Only types can be raised (not instances)")
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), ctypes.py_object(exctype))
        if res == 0:
            raise ValueError("invalid thread id")
        elif res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, 0)
            raise SystemError("PyThreadState_SetAsyncExc failed")

    @staticmethod
    def join(requests):
        return_values = []

        for req in requests:
            req.wait_for_completed()

        for req in requests:
            try:
                return_values.append(req.future.result())
            except:
                return_values.append(None)
        return return_values

    def __init__(self, logging_level=LOGGING_LEVEL, logging_format=FORMAT, logging_file=False, logging_path=LOGGING_PATH, save_csv=False, profiling=False):
        if Pykron._instance != None:
            raise Exception("This class is a singleton!")
        else:
            Pykron._instance = self
            self._logger = PykronLogger(logging_level, logging_format, logging_file, logging_path, save_csv)
            self._requests = {}
            self._thread_ids = {}
            self._task_nr = 0
            if profiling:
                self._profiler = PykronProfiler()
            else:
                self._profiler = None
            self.loop = asyncio.get_event_loop()
            self._worker_thread = threading.Thread(target=self.worker, daemon=True)
            self._worker_thread.start()

    @property
    def logging(self):
        return self._logger.log

    @property
    def logger(self):
        return self._logger

    def worker(self):
        self.loop.run_forever()
        if self._profiler:
            self._profiler.saveStats()

    def createRequest(self, task, timeout, callback, cancel_propagation):
        if self._profiler:
            self._profiler.addTask(task)
        req_id = task.task_id
        req = AsyncRequest(self, task, timeout, callback, cancel_propagation)
        self._requests[req_id] = req
        return req

    def createTaskId(self):
        self._task_nr += 1
        return self._task_nr

    def set_thread_id(self, thread_id, task_id):
        self._thread_ids[thread_id] = task_id

    def future_completed(self, request):
        req_id = request.task.task_id
        task = request.task
        if not request.future.cancelled():
            task.finalize(request.future)
        request.stop_timeout_handler()
        if task.status != Task.SUCCEED:
            if threading.main_thread().ident != task.parent_id:
                parent_req = self.getRequest(self._thread_ids[task.parent_id])
                if parent_req.cancel_propagation:
                    parent_req.cancel()
        request.set_completed()
        request._retval = task.retval
        if request._callback:
            threading.Thread(target=request._callback, args=(request._task,)).start()
        if self._logger:
            threading.Thread(target=self._logger.log_execution, args=(task,)).start()
        if sys.version_info >= (3,9):
            request.executor.shutdown(wait=False, cancel_futures=True)
        else:
            request.executor.shutdown(wait=False)
        self._thread_ids.pop(task.thread_id)
        self._requests.pop(req_id)

    def getRequest(self, req_id):
        return self._requests[req_id]

    def save_csv(self):
        if self._logger:
            self._logger.save_csv()

    def wait_all_completed(self):
        while len(self._requests) > 0:
            pending_reqs = self._requests.copy()
            for req in pending_reqs.values():
                req.completed.wait()

class AsyncRequest:

    def __init__(self, app, task, timeout, callback=None, cancel_propagation=False):
        self._app = app
        self._task = task
        self._timeout = timeout
        self._loop = self._app.loop
        self._callback = callback
        self._retval = None
        self._cancel_propagation = cancel_propagation
        self._logger = app.logger
        self._completed = threading.Event()
        self._executor = ThreadPoolExecutor()
        self._future = self._loop.run_in_executor(self.executor, self.task.run)
        self._future.add_done_callback(self.on_completed)
        self._timeout_thread = threading.Timer(timeout, self.timeout_cb)
        self._timeout_thread.start()

    @property
    def cancel_propagation(self):
        return self._cancel_propagation

    @property
    def completed(self):
        return self._completed

    @property
    def executor(self):
        return self._executor

    @property
    def future(self):
        return self._future

    @property
    def logging(self):
        return self._logger.log

    @property
    def req_id(self):
        return self.task.task_id

    @property
    def task(self):
        return self._task

    @property
    def timeout(self):
        return self._timeout

    def cancel(self, error=SystemExit):
        self.future.cancel()
        self.task.finalize(self.future)
        Pykron.stop_thread(self.task.thread_id, error)

    def on_completed(self, future):
        self._app.future_completed(self)

    def set_completed(self):
        self._completed.set()

    def stop_timeout_handler(self):
        self._timeout_thread.cancel()

    def timeout_cb(self):
        if not self.future.done():
            self.task.set_timeout()
            self.cancel(TimeoutError)


    def wait_for_completed(self, timeout=Pykron.TIMEOUT_DEFAULT):
        if timeout is None:
            timeout = self._timeout
        res = self.completed.wait(timeout=timeout)
        if res is True:
            return self._retval
        else:
            self._completed.clear()
            self.task.set_timeout()
            self.cancel(TimeoutError)
            self.completed.wait()
            return None
