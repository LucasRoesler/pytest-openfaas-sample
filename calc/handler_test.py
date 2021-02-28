import calc.handler as h


class TestParsing:
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

    def test_operation_parsing_error_on_unknown_operation(self):
        req = '{"op": "foo", "var1": "1.0", "var2": 0}'
        resp, code = h.handle(req)
        assert code == 422

        # should be a list of error
        errors = resp.get("message", [])
        assert len(errors) == 1
        assert errors[0].get("loc") == ('op', )
        assert errors[0].get("msg") == (
            "value is not a valid enumeration member; permitted: "
            "'+', '-', '*', '/', '^'"
        )

    def test_operation_parsing_error_on_non_numeric_calue(self):
        req = '{"op": "+", "var1": "Karen", "var2": 0}'
        resp, code = h.handle(req)
        assert code == 422

        # should be a list of error
        errors = resp.get("message", [])
        assert len(errors) == 1
        assert errors[0].get("loc") == ('var1', )
        assert errors[0].get("msg") == "value is not a valid float"

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

    def test_operation_division(self):
        req = '{"op": "/", "var1": "3", "var2": 2}'
        resp, code = h.handle(req)
        assert code == 200
        assert resp["value"] == 1.5

    def test_operation_subtraction(self):
        req = '{"op": "-", "var1": "1", "var2": 2}'
        resp, code = h.handle(req)
        assert code == 200
        assert resp["value"] == -1

    def test_operation_power(self):
        req = '{"op": "^", "var1": "2", "var2": -2}'
        resp, code = h.handle(req)
        assert code == 200
        assert resp["value"] == 0.25
