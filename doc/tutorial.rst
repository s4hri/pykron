Tutorial
========

.. currentmodule:: pykron

This examples will help you to get started with Pykron functionality.

Creating an AsyncRequest function
---------------------------------

AsyncRequest decorator is used to launch a function in the background as a separate thread:

.. code-block:: python
   
   from pykron.core import AsyncRequest
   
   @AsyncRequest.decorator()
   def test():
       time.sleep(1)

   ...
   test() # this will be launched as a thread in the background
   something_else()

If you want to also have the ability to sometimes wait for the results, you can launch the function
with the .wait_for_completed():

.. code-block:: python

   test().wait_for_completed()

