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

import unittest
import time
from pykron.core import Pykron, PykronLogger, Task
from pykron.test import PykronTest

class TestBasic(PykronTest):

    def test_task_succeed(self):
        ''' tests storing a request and checking Task.SUCCEED status
        '''
        @Pykron.AsyncRequest()
        def inner_empty_fun():
            time.sleep(0.1)
            return 1

        request = inner_empty_fun()
        time.sleep(1)
        self.assertEqual(request.task.status, Task.SUCCEED)
        self.assertEqual(request.task.retval, 1)

    def test_task_failed(self):
        ''' tests if a Task.FAILED is properly displayed after division by zero
        '''

        @Pykron.AsyncRequest()
        def inner_empty_fun():
            return 1/0

        request = inner_empty_fun()
        time.sleep(0.5)
        self.assertEqual(request.task.status, Task.FAILED)

    def test_task_running(self):
        ''' tests if Task.RUNNING is properly used
        '''
        @Pykron.AsyncRequest()
        def level0_fun():
            time.sleep(2)

        request = level0_fun()
        time.sleep(0.1) # to avoid Task.IDLE
        self.assertEqual(request.task.status, Task.RUNNING)

    def test_task_cancelled(self):
        ''' tests if Task.CANCELLED is properly used
        this test is limited in functionality,
        .cancel( ) requires specific conditions
        '''

        @Pykron.AsyncRequest()
        def level0_fun():
            for i in range(0,90):
                time.sleep(0.1)

        request = level0_fun()
        time.sleep(0.1) # to avoid Task.IDLE
        request.cancel()
        time.sleep(0.1) # wait for it
        self.assertEqual(request.task.status, Task.CANCELLED)

    def test_task_wait_for_completed_and_callback(self):
        ''' test wait_for_completed together with a callback
        '''
        def on_completed(task):
            self.assertEqual(task.status, Task.SUCCEED)
            self.assertEqual(task.retval, 1)

        @Pykron.AsyncRequest(callback=on_completed)
        def inner_empty_fun():
            time.sleep(0.1)
            return 1

        inner_empty_fun().wait_for_completed()

    def test_return_value_through_future(self):
        ''' see if the future properly stores a returned value
        '''

        @Pykron.AsyncRequest()
        def inner_fun():
            time.sleep(0.1)
            return 'test'

        task = inner_fun()
        time.sleep(0.3)
        self.assertEqual(task.future.result(), 'test')

    def test_return_value_wait_for_completed(self):
        ''' test wait_for_completed together with a callback
        '''
        @Pykron.AsyncRequest()
        def inner_fun():
            time.sleep(0.1)
            return 'test'

        val = inner_fun().wait_for_completed()
        self.assertEqual(val, 'test')

    def test_same_time(self):
        ''' test if 5 functions can be run at the same time (without join)
        '''
        @Pykron.AsyncRequest()
        def fun1(arg):
            time.sleep(0.5)
            return arg

        args = ['a1','b2','c3','d4','e5']
        requests = list()
        for arg in args:
            requests.append( (fun1(arg),arg) )

        time.sleep(1) # to avoid Task.IDLE
        for (request,arg) in requests:
            self.assertEqual(request.future.result(), arg)

if __name__ == '__main__':
    unittest.main()
