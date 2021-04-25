from dataclasses import dataclass
from typing import Type, Any


def assertion_message(msg, expected, recieved):
    return f"{msg}\n\tExpected: '{expected}'\n\tRecieved: '{recieved}'"


@dataclass
class EnumDecodeError(Exception):
    type: Type
    value: Any
    expected: Any = None

    def __str__(self):
        if not self.expected:
            return f"{str(self.type)} cannot decode {repr(self.value)}."
        if isinstance(self.expected, list):
            return f"{str(self.type)} cannot decode {repr(self.value)}. Expected: [{', '.join([repr(p) for p in self.expected])}] "
        else:
            return f"{str(self.type)} cannot decode {repr(self.value)}. Expected: {repr(self.expected)}"


@dataclass
class ParsingError(Exception):
    index: int

    def __str__(self):
        if self.__cause__:
            return f"'{str(self.__cause__)}' @{self.index}"
        else:
            return f"@{self.index}"
