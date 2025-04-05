from abc import abstractmethod
from pytrait.enum import Enum, auto
from pytrait.impl import Impl
from pytrait.trait import Trait
from pytrait.runtime import requires_traits

class Adjustable(metaclass=Trait):
    @abstractmethod
    def lighter(self) -> str:
        pass

    @abstractmethod
    def darker(self) -> str:
        pass

class Sizeable(metaclass=Trait):
    def larger(self) -> str:
        pass
    def smaller(self) -> str:
        pass

class Paint(metaclass=Enum):
    RED = auto()
    BLUE = auto()

class ImplAdjustableforPaint(Adjustable, metaclass=Impl, target="Paint"):
    def lighter(self) -> str:
        match self:
            case Paint.RED: return "pink"
            case Paint.BLUE: return "teal"
            case _: return "lighter?"

    def darker(self) -> str:
        match self:
            case Paint.RED: return "maroon"
            case Paint.BLUE: return "navy"
            case _: return "darker?"


class ImplSizeableforPaint(Sizeable, metaclass=Impl, target="Paint"):
    def larger(self):
        return "64oz"
    def smaller(self):
        return "16oz"

@requires_traits(paint=(Adjustable, Sizeable))
def describe_paint(paint):
    print(f"Lighter version: {paint.lighter()}")
    print(f"Darker version: {paint.darker()}")
    print(f"Larger size: {paint.larger()}")
    print(f"Smaller size: {paint.smaller()}")

red_can = Paint.RED
blue_can = Paint.BLUE

describe_paint(red_can)