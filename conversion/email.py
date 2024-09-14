from conversion.validation import ValidationException
from typing import Protocol, Tuple
import re


class Email():

    def __init__(self, user_name: str, domain_name: str):
        self.__user_name = user_name
        self.__domain_name = domain_name

    def parts(self) -> Tuple[str, str]:
        return (self.__user_name, self.__domain_name)

    def to_string(self, formatter) -> str:
        return formatter.format(self)


class EmailParser(Protocol):

    def parse(self, input: str) -> Tuple[str, str]:
        ...


class RegexEmailParser(EmailParser):

    __regex = re.compile(
        r"^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$"
    )

    def parse(self, input: str) -> Tuple[str, str]:
        trimmed = input.strip()
        matching = RegexEmailParser.__regex.match(trimmed)
        if matching is None:
            raise ValidationException('Unable to extract email from input')

        email_segments = matching.string.split('@')
        assert len(email_segments) == 2, \
            'Splitting an email string on the "@" symbol must produce two substrings'

        return (email_segments[0], email_segments[1])


class EmailFactory(Protocol):

    def create(self) -> Email:
        ...


class FromEmailString(EmailFactory):

    def __init__(self, parser: EmailParser, input: str):
        self.__parser = parser
        self.__input = input

    def create(self) -> Email:
        (user_name, domain_name) = self.__parser.parse(self.__input)
        return Email(user_name, domain_name)


class EmailFormatter:

    def format(self, email: Email) -> str:
        (user_name, domain_name) = email.parts()
        return f'{user_name}@{domain_name}'
