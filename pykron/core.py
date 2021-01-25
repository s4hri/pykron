"""
BSD 2-Clause License

Copyright (c) 2020, Davide De Tommaso (davide.detommaso@iit.it),
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
import atexit

from pykron.logging import PykronLogger

if sys.version_info > (3,7):
    import cProfile, pstats, io
    from pstats import SortKey

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
        self._arrival_ts = time.perf_counter()
        self._logger = PykronLogger.getInstance()
        self._parent_id = parent_id
        self._func_name = self._target.__name__
        self._task_id = threading.current_thread().ident
        self._caller_frame = stack()[2][0]
        self._timeout = False
        caller_module = inspect.getmodule(self._caller_frame.f_code)
        caller_info = getframeinfo(self._caller_frame)
        caller_source = inspect.getsourcelines(caller_module)
        matching = [s for s in caller_source[0] if "def " + self._func_name in s]
        self._name = self._func_name
        self._func_loc = "[%s:%d]" % (caller_info.filename, caller_source[0].index(matching[0])+1)
        self._caller_name = caller_info.function
        self._caller_loc = "[%s:%d]" % (caller_info.filename, caller_info.lineno)

    @property
    def args(self):
        return self._args

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
        except asyncio.CancelledError:
            if self._timeout:
                e = "%s(): TIMEOUT OCCURRED!" % (self.func_name)
                self._exception = TimeoutError
                self._status = Task.TIMEOUT
            else:
                e = "%s(): TASK CANCELLED!" % (self.func_name)
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
            self.logging.error("%s: %s" % (self.name, e))
        self.logging.debug("%s%s: TASK COMPLETED! Status: %s, Duration: %.4f [Caller: %s%s]" % (self.func_name, self.func_loc, self.status, self.duration, self.caller_name, self.caller_loc))

    def run(self):
        self._task_id = threading.current_thread().ident
        self.logging.debug("%s%s: TASK STARTED! [Caller: %s%s]" % (self.func_name, self.func_loc, self.caller_name, self.caller_loc))
        self._start_ts = time.perf_counter()
        self._status = Task.RUNNING
        res = self._target(*self._args)
        return res

    def set_timeout(self):
        self._timeout = True

class Pykron:

    _instance = None
    TIMEOUT_DEFAULT = 10.0

    @staticmethod
    def AsyncRequest(timeout=TIMEOUT_DEFAULT, callback=None):
        def wrapper(target):
            def f(*args, **kwargs):
                parent_id = threading.current_thread().ident
                task = Task(target=target,
                            args=args,
                            parent_id=parent_id)
                return Pykron._instance.createRequest(task, timeout, callback)
            return f
        return wrapper

    @staticmethod
    def close():
        app = Pykron.getInstance()
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

    def __init__(self, pykron_logger=None, profiler=None):
        if Pykron._instance != None:
            raise Exception("This class is a singleton!")
        else:
            Pykron._instance = self
            if pykron_logger is None:
                self._logger = PykronLogger.getInstance()
            else:
                self._logger = pykron_logger
            self._requests = {}
            self._parents = {}
            self._futures = {}
            if profiler:
                self._profiler = cProfile.Profile()
            else:
                self._profiler = None
            self.loop = asyncio.get_event_loop()
            self._worker_thread = threading.Thread(target=self.worker)
            self._worker_thread.start()

    @property
    def logging(self):
        return self._logger.log

    def worker(self):
        if self._profiler:
            self._profiler = cProfile.Profile()
            self._profiler.enable()

        self.loop.run_forever()
        if self._profiler:
            self._profiler.disable()
            s = io.StringIO()
            sortby = SortKey.CUMULATIVE
            ps = pstats.Stats(self._profiler, stream=s).sort_stats(sortby)
            ps.print_stats()
            print(s.getvalue())
            ps.dump_stats("pykron.stats")


    def createRequest(self, task, timeout, callback):
        req = AsyncRequest(self.loop, task, timeout, callback)
        req_id = task.task_id
        self._requests[req_id] = req
        self._parents[req_id] = task.parent_id
        self._futures[req_id] = req.future
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
            threading.Thread(target=self._requests[req_id].stop_timeout_handler).start()
        self._requests[req_id].set_completed()
        self._requests[req_id]._retval = task.retval
        if self._requests[req_id]._callback:
            threading.Thread(target=self._requests[req_id]._callback, args=(self._requests[req_id]._task,)).start()
        self._requests[req_id].executor.shutdown(wait=False)
        if self._logger:
            threading.Thread(target=self._logger.log_execution, args=(task,)).start()
        del self._requests[req_id]


    def getRequest(self, req_id):
        return self._requests[req_id]

    def save_csv(self):
        if self._logger:
            self._logger.save_csv()

class AsyncRequest:

    def __init__(self, loop, task, timeout, callback=None):
        self._task = task
        self._timeout = timeout
        self._loop = loop
        self._callback = callback
        self._timeout_handler_id = None
        self._retval = None
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
        self.logging.error("%s%s: TASK CANCELLED [Caller: %s%s]" % (self.task.func_name, self.task.func_loc, self.task.caller_name, self.task.caller_loc))
        self.executor.shutdown(wait=False)
        self.stop_timeout_handler()
        Pykron.stop_thread(self.req_id, error)
        self._loop.call_soon_threadsafe(self.future.cancel)

    def set_completed(self):
        self._completed.set()

    def stop_timeout_handler(self):
        self._future_timer.cancel()

    def timeout_cb(self):
        if not self.future.done():
            self.logging.error("%s%s: TIMEOUT OCCURRED AFTER %.4fs! [Caller: %s%s]" % (self.task.func_name, self.task.func_loc, self.timeout, self.task.caller_name, self.task.caller_loc))
            self.task.set_timeout()
            self.cancel(TimeoutError)

    def wait_for_completed(self, timeout=Pykron.TIMEOUT_DEFAULT):
        if timeout is None:
            timeout = self._timeout
        res = self._completed.wait(timeout=timeout)
        if res is True:
            return self._retval
        else:
            self._completed.clear()
            self.task.set_timeout()
            self.cancel(TimeoutError)
            self._completed.wait()
            self.logging.error("%s%s: TIMEOUT OCCURRED ON wait_for_completed AFTER %.4fs! [Caller: %s%s]" % (self.task.func_name, self.task.func_loc, timeout, self.task.caller_name, self.task.caller_loc))
            return None
