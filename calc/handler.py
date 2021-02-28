from pydantic import BaseModel, ValidationError
from enum import Enum, unique


@unique
class OperationType(Enum):
    ADD = "+"
    SUBTRACT = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    POWER = "^"


class Calculation(BaseModel):
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
        c = Calculation.parse_raw(req)
    except ValidationError as e:
        return {"message": e.errors()}, 422
    except Exception as e:
        return {"message": e}, 500

    return {"value": c.execute()}, 200
