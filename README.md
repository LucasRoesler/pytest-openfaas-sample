# Using pytest with OpenFaaS


## Start the project
```sh
$ mkdir pytest-sample
$ cd pytest-sanmple
$ faas-cli template store pull python3-flask
$ mv calc.yml stack.yml
```

**Note** Don't forget to add this section to your stack file so that the `faas-cli` will know how to automatically pull the template

```yaml
configuration:
  templates:
    - name: python3-flask
      source: https://github.com/openfaas/python-flask-template

```

## Setup the local python environment

```sh
$ conda create -n pytest-sample pytest black pylint
$ conda activate pytest-sample
$ cat <<EOF >> requirements.txt
pydantic==1.7.3
flask==1.1.2
EOF
$ conda install --yes --file requirements.txt
```

Now we are ready to develop the calculator.

## Add the first tests
Let's start with some simple tests:

```sh
$ touch calc/handler_test.py
```

then add the following test cases for a couple of our happy paths

```py
import calc.handler as h


class TestParsing:
    def test_operation_addition(self):
        req = '{"op": "+", "var1": "1.0", "var2": 0}'
        resp, code = h.handle(req)
        assert code == 200
        assert resp["value"] == 1.0

    def test_operation_multiplication(self):
        req = '{"op": "*", "var1": "100.01", "var2": 1}'
        resp, code = h.handle(req)
        assert code == 200
        assert resp["value"] == 100.01
```

At this point, we have followed normal conventions for pytest, so we can run out test and see all of the errors in their wonderful glory

```sh
$ pytest
========================================= test session starts =========================================
platform linux -- Python 3.8.8, pytest-6.2.2, py-1.10.0, pluggy-0.13.1
rootdir: /home/lucas/code/openfaas/sandbox/pytest-sample
collected 2 items

calc/handler_test.py FF                                                                         [100%]

============================================== FAILURES ===============================================
_________________________________ TestParsing.test_operation_addition _________________________________

self = <calc.handler_test.TestParsing object at 0x7fc8029ad820>

    def test_operation_addition(self):
        req = '{"op": "+", "var1": "1.0", "var2": 0}'
>       resp, code = h.handle(req)
E       ValueError: too many values to unpack (expected 2)

calc/handler_test.py:49: ValueError
______________________________ TestParsing.test_operation_multiplication ______________________________

self = <calc.handler_test.TestParsing object at 0x7fc8029add30>

    def test_operation_multiplication(self):
        req = '{"op": "^", "var1": "2", "var2": -2}'
>       resp, code = h.handle(req)
E       ValueError: too many values to unpack (expected 2)

calc/handler_test.py:73: ValueError
======================================= short test summary info =======================================
FAILED calc/handler_test.py::TestParsing::test_operation_addition - ValueError: too many values to u...
FAILED calc/handler_test.py::TestParsing::test_operation_multiplication - ValueError: too many value...
========================================== 2 failed in 0.05s ==========================================
```

In this case we get a value error because our handler function only returns a string, not a dictionary  and a status code.  These tests are expecting that the handler returns something that looks like this

```py
return {"value": 1.1}, 200
```

This return value works with Flask, it will json serialize the dictionary and set the status code to 200 for us.


If we update the handler to look like

```py
def handle(req):
    return {"value": 1}, 200
```

and run pytest again, the we get a new error, a value error because we got the wrong calculation result

```sh
$ pytest
========================================= test session starts =========================================
platform linux -- Python 3.8.8, pytest-6.2.2, py-1.10.0, pluggy-0.13.1
rootdir: /home/lucas/code/openfaas/sandbox/pytest-sample
collected 2 items

calc/handler_test.py .F                                                                         [100%]

============================================== FAILURES ===============================================
______________________________ TestParsing.test_operation_multiplication ______________________________

self = <calc.handler_test.TestParsing object at 0x7f9f30ecbd30>

    def test_operation_multiplication(self):
        req = '{"op": "^", "var1": "2", "var2": -2}'
        resp, code = h.handle(req)
        assert code == 200
>       assert resp["value"] == 0.25
E       assert 1 == 0.25

calc/handler_test.py:75: AssertionError
======================================= short test summary info =======================================
FAILED calc/handler_test.py::TestParsing::test_operation_multiplication - assert 1 == 0.25
===================================== 1 failed, 1 passed in 0.06s =====================================
```

## The working implementation
Jumping forward a bit, here is the final implementation. I have used the `enum` package and `pydantic` to help simplify the validation and parsing of requests into my internal `Calculation` model

```py
from pydantic import BaseModel, ValidationError
from enum import Enum, unique
from typing import Callable


@unique
class OperationType(Enum):
    ADD = "+"
    SUBTRACT = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    POWER = "^"


class Caclucation(BaseModel):
    op: OperationType
    var1: float
    var2: float

    def execute(self) -> float:
        if self.op is OperationType.ADD:
            return self.var1 + self.var2

        if self.op is OperationType.SUBTRACT:
            return self.var1 - self.var2

        if self.op is OperationType.MULTIPLY:
            return self.var1 * self.var2

        if self.op is OperationType.DIVIDE:
            return self.var1 / self.var2

        if self.op is OperationType.POWER:
            return self.var1 ** self.var2

        raise ValueError("unknown operation")



def handle(req) -> (dict, int):
    """handle a request to the function
    Args:
        req (str): request body
    """

    try:
        c = Caclucation.parse_raw(req)
    except ValidationError as e:
        return {"message": e.errors()}, 422
    except Exception as e:
        return {"message": e}, 500

    return {"value": c.execute()}, 200
```

Now our tests will pass

```sh
$ pytest
========================================= test session starts =========================================
platform linux -- Python 3.8.8, pytest-6.2.2, py-1.10.0, pluggy-0.13.1
rootdir: /home/lucas/code/openfaas/sandbox/pytest-sample
collected 2 items

calc/handler_test.py ..                                                                         [100%]

========================================== 2 passed in 0.04s ==========================================
```


## Testing error cases
We can even extend our test cases to cover validation errors. Because we using `pydantic` and we are returning `{"message": e.errors()}`, these tests look like this

```py
def test_operation_parsing_error_on_empty_obj(self):
    req = '{}'

    resp, code = h.handle(req)
    assert code == 422
    # should be a list of error
    errors = resp.get("message", [])
    assert len(errors) == 3
    assert errors[0].get("loc") == ('op', )
    assert errors[0].get("msg") == "field required"

    assert errors[1].get("loc") == ('var1', )
    assert errors[1].get("msg") == "field required"

    assert errors[2].get("loc") == ('var2', )
    assert errors[2].get("msg") == "field required"
```

## Running this in CI

I've added a Github Action Workflow to my sample repo. It is based on the sample testing workflow that [Github provides for Python](https://docs.github.com/en/actions/guides/building-and-testing-python#starting-with-the-python-workflow-template) and the function workflow from [Serverless for Everyone](https://gumroad.com/l/serverless-for-everyone-else)

This workflow will test and build your function in parallel. The resulting Docker image is pushed to Docker Container Registry.

**NOTE** you need to configure the `DOCKER_PASSWORD` secret for your Github repo for this workflow to work correctly.


## Try the function

```sh
$ faas-cli deploy
$  echo '{"op":"+", "var1":1, "var2": 2}' | faas-cli invoke calc
{"value":3.0}
```