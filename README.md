# PyKron

PyKron is a open-source package that let you easily transform any Python
function in an asynchronous call.

# How it works

1. To make a def statement an asynchronous call

The original code contains two def statements as shown below. The execution will
take 4+2 seconds, since foo2 is executed right after foo2.

```
def foo1():
    time.sleep(4)
    print("foo1")

def foo2():
    time.sleep(2)
    print("foo2")

foo1()
foo2()
```

Now we want to make foo1 and foo2  asynchronous using PyKron. What we need to do
is basically wrap them with specific decorators of the AsyncRequest class. As
shown below, the execution will take now only 4 seconds cause foo1 and foo2 are
launched in parallel.

```
@AsyncRequest.decorator
def foo1():
    time.sleep(4)
    print("foo1")

@AsyncRequest.decorator
def foo2():
    time.sleep(2)
    print("foo2")

foo1()
foo2()
```
