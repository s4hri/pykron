#   Copyright (C) 2020  Davide De Tommaso, Adam Wojciech Lukomski
#
import unittest
import sys
import yarp
import time

sys.path.append('../..')

# this may be moved to inside each class to separate the test methods?
from pykron.core import AsyncRequest

class TestAsyncRequest(unittest.TestCase):

    def test_01_singleTestCase(self):
        @AsyncRequest.decorator(timeout=120)
        def innerFunction01():
            time.sleep(1)
            print("Done")
        innerFunction01().wait_for_completed()
        # self.assertEqual( fromFunction, msgToCompareTo)

if __name__ == '__main__':
    unittest.main()
