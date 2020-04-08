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
import concurrent.futures
import threading
import time


class Task:

    IDLE    = 'IDLE',
    RUNNING = 'RUNNING',
    SUCCEED = 'SUCCEED',
    FAILED  = 'FAILED',
    TIMEOUT = 'TIMEOUT'

    def __init__(self, target, args, name=None):
        self._target = target
        self._args = args
        self._name = name
        self._retval = None
        self._status = Task.IDLE
        self._arrival_ts = time.perf_counter()
        self._start_ts = None
        self._end_ts = None
        self._duration = None
        self._exception = None

    def __str__(self):
        return """>> Task '%s'
                Status: %s
                Duration:  %.4f (s)
                Idle time: %.4f (s)
                Return value: %s
                """ % (self._name, self.status, self.duration, self.idle_time, str(self.retval))

    @property
    def duration(self):
        if not self._start_ts is None or self._end_ts is None:
            return self._end_ts - self._start_ts
        return None

    @property
    def idle_time(self):
        if not self._start_ts is None or self._arrival_ts is None:
            return self._start_ts - self._arrival_ts
        return None

    @property
    def status(self):
        return self._status

    @property
    def retval(self):
        return self._retval

    def run(self, timeout=10.0):
        self._start_ts = time.perf_counter()
        self._status = Task.RUNNING

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            try:
                future = executor.submit(self._target, *self._args)
                t = future.result(timeout=timeout)
                self._retval = t
                self._status = Task.SUCCEED
            except concurrent.futures.TimeoutError:
                self._status = Task.TIMEOUT
            except BaseException as e:
                self._status = Task.FAILED
                self._exception = e
                raise BaseException(e)
            finally:
                self._end_ts = time.perf_counter()


class AsyncRequest:

    @staticmethod
    def decorator(foo):

        def f(*args, **kwargs):
            #args = (self,) + args
            task = Task(foo, args, foo.__name__)
            req = AsyncRequest(task)
            return req

        return f

    @staticmethod
    def join(requests, timeout=None):
        futures = {}
        return_values = []
        idx = 0

        for req in requests:
            futures[req.future] = idx
            return_values.append(None)
            idx += 1

        for future in concurrent.futures.as_completed(futures):
            return_values[futures[future]] = future.result(timeout)

        return return_values


    def __init__(self, task):
        self._task = task
        self._completed = threading.Event()
        self._callback = None

        executor = concurrent.futures.ThreadPoolExecutor()
        self._future = executor.submit(self.run)

    @property
    def future(self):
        return self._future

    def wait_for_completed(self, callback=None, request_timeout=None):
        if not callback is None:
            self.on_completed(callback)
        res = self._future.result(request_timeout)
        return res.retval

    def on_completed(self, callback):
        self._callback = callback
        return self

    def run(self):
        self._task.run()
        self._completed.set()
        if self._callback is None:
            return self._task
        else:
            return self._callback(self._task)
