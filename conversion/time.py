from conversion import validation
from datetime import datetime, timezone
from typing import Protocol


class Date(Protocol):

    def value(self) -> datetime:
        ...

    def to_string(self, formatter) -> str:
        ...


class ValidDate(Date):

    def __init__(self, value):
        self.__value = value

    def value(self) -> datetime:
        return self.__value

    def to_string(self, formatter) -> str:
        return formatter.format(self)


class PresentDate(Date):

    def value(self) -> datetime:
        return datetime.now(timezone.utc)

    def to_string(self, formatter) -> str:
        _ = formatter  # Consume arg. Makes warning go away, but we don't need it
        return "present"


class DateParser(Protocol):

    def parse(self, input: str) -> datetime:
        ...


class YearMonthParser(DateParser):

    __format = '%Y-%m'

    def parse(self, input: str) -> datetime:
        trimmed = input.strip()
        return datetime.strptime(trimmed, self.__format)


class DateFactory(Protocol):

    def create(self) -> Date:
        ...


class FromStartDate(DateFactory):

    def __init__(self, parser: DateParser, value: str):
        self.__parser = parser
        self.__value = value

    def create(self) -> Date:
        if self.__value is None:
            raise validation.ValidationException("Start date missing")

        parsed_date = self.__parser.parse(self.__value)
        return ValidDate(parsed_date)


class FromEndDate(DateFactory):

    def __init__(self, parser: DateParser, value: str):
        self.__parser = parser
        self.__value = value

    def create(self) -> Date:
        if self.__value is None:
            return PresentDate()

        parsed_date = self.__parser.parse(self.__value)
        return ValidDate(parsed_date)


class DateFormatter(Protocol):

    def format(self, date):
        ...


class FullMonthNameYearFormatter(DateFormatter):

    __format = '%B %Y'

    def format(self, date):
        value = date.value()
        assert value is not None, \
            "Cannot format classes implementing the Date protocol via the null-object pattern"

        return value.strftime(self.__format)
