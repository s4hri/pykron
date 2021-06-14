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


import unittest
import time
from pykron.core import Pykron, PykronLogger, Task
from pykron.test import PykronTest


class TestTaskTimeout(PykronTest):

    def test_task_timeout(self):
        ''' tests if Task.TIMEOUT is properly used
        '''

        @Pykron.AsyncRequest(timeout=0.2)
        def level0_fun():
            time.sleep(0.5)

        request = level0_fun()
        time.sleep(1) # this is not a wait_for_completed test, so brute-force it
        self.assertEqual(request.task.status, Task.TIMEOUT)
        self.assertLess(request.task.duration, 0.5)

    def test_wait_for_completed_timeout(self):
        ''' test wait_for_completed together with a callback
        '''

        @Pykron.AsyncRequest(timeout=2.0)
        def inner_fun():
            time.sleep(3.0)

        request = inner_fun()
        request.wait_for_completed(timeout=1.0)
        self.assertEqual(request.task.status, Task.TIMEOUT)
        self.assertLess(request.task.duration, 2.0)

    def test_timeout_cancel(self):
        ''' test that timeout causes task cancelation
        '''

        @Pykron.AsyncRequest(timeout=0.2)
        def foo1():
            time.sleep(0.5)

        @Pykron.AsyncRequest(timeout=2.0)
        def foo2():
            req = foo1()
            time.sleep(1.0)
            self.assertEqual(req.task.status, Task.TIMEOUT)
            self.assertLess(req.task.duration, 0.5)

        req = foo2()
        time.sleep(2.0)
        self.assertEqual(req.task.status, Task.CANCELLED)

    def test_timeout_nocancel(self):
        ''' test that timeout causes task cancelation
        '''

        @Pykron.AsyncRequest(timeout=0.2)
        def foo1():
            time.sleep(0.5)

        @Pykron.AsyncRequest(timeout=2.0, cancel_propagation=False)
        def foo2():
            req = foo1()
            time.sleep(1.0)
            self.assertEqual(req.task.status, Task.TIMEOUT)
            self.assertLess(req.task.duration, 0.5)

        req = foo2()
        time.sleep(2.0)
        self.assertEqual(req.task.status, Task.SUCCEED)
