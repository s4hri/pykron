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


class TestTaskOrder(PykronTest):

    def test_1(self):

        @Pykron.AsyncRequest()
        def like(msg):
            print("I like " + msg)
            time.sleep(0.1)
            return 1

        a = like("strawberries")
        b = like("bananas")
        self.assertEqual(a.task.status, Task.RUNNING)
        self.assertEqual(b.task.status, Task.RUNNING)
        Pykron.join([a,b])
        self.assertEqual(a.task.status, Task.SUCCEED)
        self.assertEqual(b.task.status, Task.SUCCEED)
        c = like("mangos")
        res = c.wait_for_completed()
        self.assertEqual(c.task.status, Task.SUCCEED)
        self.assertEqual(res, 1)

    def test_2(self):
        # 2-levels nested function foo1->foo2->foo3
        @Pykron.AsyncRequest()
        def foo1():
            res = foo2().wait_for_completed()
            time.sleep(5)
            return 1

        # A never-ending function
        @Pykron.AsyncRequest()
        def foo2():
            while True:
                print("I am alive! ")
                time.sleep(1)
                foo3()
                time.sleep(2)
            return 2

        # User-defined callback function running once the foo1 ends
        def on_completed(task):
            if task.status == Task.SUCCEED:
                print("Everything's fine")
                self.fail()
            else:
                print("Something goes wrong")

        # A bugged function
        @Pykron.AsyncRequest(callback=on_completed)
        def foo3():
            return 1/0

        req = foo1()
        self.assertEqual(req.task.status, Task.RUNNING)
        req.wait_for_completed()
        self.assertEqual(req.task.status, Task.CANCELLED)
