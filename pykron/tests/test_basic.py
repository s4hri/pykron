import pytest
from io import StringIO
import json
import time

from pykron.core import Pykron, PykronLogger, Task

# TODO try doing the same with function level fixture
@pytest.fixture(autouse=True)
def reset_all_singletons():
    Pykron._instance = None
    PykronLogger._instance = None

class TestBasic:
    def test_create_pykron(self):
        app = Pykron()
        logger = PykronLogger.getInstance()
        app.close()
        time.sleep(1) # it takes upwards of 25ms usually to stop the loop
        assert app.loop.is_running() == False

    def test_logger_singleton(self):
        logger = PykronLogger()
        with pytest.raises( Exception ):
            logger2 = PykronLogger()

    def test_pykron_singleton(self):
        app = Pykron()
        with pytest.raises( Exception ):
            app2 = Pykron()
        app.close()
        time.sleep(1) # it takes upwards of 25ms usually to stop the loop
        assert app.loop.is_running() == False

    def test_task_succeed(self):
        ''' tests storing a request and checking Task.SUCCEED status
        '''
        app = Pykron()
        @app.AsyncRequest(timeout=0.5)
        def inner_empty_fun():
            time.sleep(0.1)
            return 1
        request = inner_empty_fun()
        time.sleep(1)
        assert request.task.status == Task.SUCCEED
        #assert request.task.retval == 1 # TODO this fails !
        app.close()
        time.sleep(1)
        assert app.loop.is_running() == False

    def test_task_failed(self):
        ''' tests if a Task.FAILED is properly displayed after division by zero
        '''
        app = Pykron()
        @app.AsyncRequest(timeout=0.5)
        def inner_empty_fun():
            return 1/0
        request = inner_empty_fun()
        time.sleep(0.2)
        assert request.task.status == Task.FAILED
        app.close()
        time.sleep(1)
        assert app.loop.is_running() == False

    def test_task_running(self):
        ''' tests if Task.RUNNING is properly used
        '''
        app = Pykron()
        @app.AsyncRequest(timeout=3)
        def level0_fun():
            time.sleep(2)
        request = level0_fun()
        time.sleep(0.1) # to avoid Task.IDLE
        assert request.task.status == Task.RUNNING
        app.close()
        time.sleep(1)
        assert app.loop.is_running() == False


    def test_task_cancelled(self):
        ''' tests if Task.CANCELLED is properly used
        this test is limited in functionality,
        .cancel( ) requires specific conditions
        '''
        app = Pykron()
        @app.AsyncRequest(timeout=10)
        def level0_fun():
            for i in range(0,90):
                time.sleep(0.1)
        request = level0_fun()
        time.sleep(0.1) # to avoid Task.IDLE
        request.cancel()
        time.sleep(0.1) # wait for it
        assert request.task.status == Task.CANCELLED
        app.close()
        time.sleep(1)
        assert app.loop.is_running() == False

    def test_task_timeout(self):
        ''' tests if Task.TIMEOUT is properly used
        '''
        app = Pykron()
        @app.AsyncRequest(timeout=0.2)
        def level0_fun():
            time.sleep(2)
        request = level0_fun()
        time.sleep(0.3) # this is not a wait_for_completed test, so brute-force it
        assert request.task.status == Task.TIMEOUT
        app.close()
        time.sleep(1)
        assert app.loop.is_running() == False

    def test_task_wait_for_completed_and_callback(self):
        ''' test wait_for_completed together with a callback
        '''
        app = Pykron()
        @app.AsyncRequest(timeout=0.5)
        def inner_empty_fun():
            time.sleep(0.1)
            return 1
        def on_completed(task):
            assert task.status == Task.SUCCEED
            #assert task.retval == 1 # TODO this fails !
        inner_empty_fun().wait_for_completed(callback=on_completed)
        app.close()
        time.sleep(1)
        assert app.loop.is_running() == False

    def test_return_value_through_future(self):
        ''' see if the future properly stores a returned value
        '''
        app = Pykron()

        @app.AsyncRequest(timeout=0.5)
        def inner_fun():
            time.sleep(0.1)
            return 'test'
        task = inner_fun()
        time.sleep(0.3)
        assert task.future.result() == 'test'
        app.close()
        time.sleep(1)
        assert app.loop.is_running() == False

    def test_return_value_wait_for_completed(self):
        ''' test wait_for_completed together with a callback
        '''
        app = Pykron()
        @app.AsyncRequest(timeout=0.5)
        def inner_fun():
            time.sleep(0.1)
            return 'test'
        val = inner_fun().wait_for_completed()
        assert val == 'test'
        app.close()
        time.sleep(1)
        assert app.loop.is_running() == False
