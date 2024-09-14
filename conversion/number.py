from enum import Enum, Flag
from typing import Protocol
import locale


class Number:

    def __init__(self, input: float):
        self.__input = input

    def value(self) -> float:
        return self.__input

    def to_string(self, formatter) -> str:
        return formatter.format(self)


class NumberFormatter(Protocol):

    def format(self, number: Number) -> str:
        ...


class Scale(Enum):
    One = 1
    Two = 2
    Three = 3


class NumberFormattingFlags(Flag):
    NONE = 0
    GROUPING = 1
    MONETARY = 2


class ScaledNumberFormatter(NumberFormatter):

    def __init__(self, scale: Scale, flags: NumberFormattingFlags):
        self.__scale = scale
        self.__flags = flags

    def format(self, number: Number) -> str:
        scale = self.__scale.value
        value = number.value()

        grouping = NumberFormattingFlags.GROUPING in self.__flags
        monetary = NumberFormattingFlags.MONETARY in self.__flags

        return locale.format_string(f'%0.{scale}f',
                                    value,
                                    grouping=grouping,
                                    monetary=monetary)
