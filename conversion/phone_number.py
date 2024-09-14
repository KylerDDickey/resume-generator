from conversion.validation import ValidationException
from enum import Enum
from itertools import accumulate, zip_longest
from typing import Iterable, List, Protocol, Tuple
import re


class PhoneNumberDigit(Enum):
    ZERO = 0
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9

    def to_string(self) -> str:
        match self:
            case PhoneNumberDigit.ZERO:
                return '0'
            case PhoneNumberDigit.ONE:
                return '1'
            case PhoneNumberDigit.TWO:
                return '2'
            case PhoneNumberDigit.THREE:
                return '3'
            case PhoneNumberDigit.FOUR:
                return '4'
            case PhoneNumberDigit.FIVE:
                return '5'
            case PhoneNumberDigit.SIX:
                return '6'
            case PhoneNumberDigit.SEVEN:
                return '7'
            case PhoneNumberDigit.EIGHT:
                return '8'
            case PhoneNumberDigit.NINE:
                return '9'

    @classmethod
    def from_int(cls, value: int):
        match value:
            case 0:
                return cls.ZERO
            case 1:
                return cls.ONE
            case 2:
                return cls.TWO
            case 3:
                return cls.THREE
            case 4:
                return cls.FOUR
            case 5:
                return cls.FIVE
            case 6:
                return cls.SIX
            case 7:
                return cls.SEVEN
            case 8:
                return cls.EIGHT
            case 9:
                return cls.NINE
            case _:
                raise ValueError('Given input is not a valid single digit')

    @classmethod
    def many_to_string(cls, *digits) -> str:
        return ''.join(cls.to_string(d) for d in digits)


class Digits(Protocol):

    def count(self) -> int:
        ...

    def to_segmented_string(self) -> List[str]:
        ...


class OneDigit(Digits):

    def __init__(self, first: PhoneNumberDigit):
        self.__first = first

    def count(self) -> int:
        return 1

    def to_segmented_string(self) -> List[str]:
        return [PhoneNumberDigit.many_to_string(self.__first)]


class TwoDigits(Digits):

    def __init__(self, first: PhoneNumberDigit, second: PhoneNumberDigit):
        self.__first = first
        self.__second = second

    def count(self) -> int:
        return 2

    def to_segmented_string(self) -> List[str]:
        return [PhoneNumberDigit.many_to_string(self.__first, self.__second)]


class ThreeDigits(Digits):

    def __init__(self, first: PhoneNumberDigit, second: PhoneNumberDigit,
                 third: PhoneNumberDigit):
        self.__first = first
        self.__second = second
        self.__third = third

    def count(self) -> int:
        return 3

    def to_segmented_string(self) -> List[str]:
        return [
            PhoneNumberDigit.many_to_string(self.__first, self.__second,
                                            self.__third)
        ]


class FourDigits(Digits):

    def __init__(self, first: PhoneNumberDigit, second: PhoneNumberDigit,
                 third: PhoneNumberDigit, fourth: PhoneNumberDigit):
        self.__first = first
        self.__second = second
        self.__third = third
        self.__fourth = fourth

    def count(self) -> int:
        return 4

    def to_segmented_string(self) -> List[str]:
        return [
            PhoneNumberDigit.many_to_string(self.__first, self.__second,
                                            self.__third, self.__fourth)
        ]


class DigitsCollection(Digits):

    __create_key = object()

    def __init__(self, create_key, digit_sequences_acc: List[Tuple[int,
                                                                   Digits]]):
        assert create_key == DigitsCollection.__create_key, \
            "DigitsCollection objects must be created using DigitsCollection.create"

        self.__digit_sequences_acc = digit_sequences_acc

    @classmethod
    def create(cls, *digit_sequences: Digits):
        accumulation = accumulate(d.count() for d in digit_sequences)
        digit_count_accumulations = zip(accumulation, digit_sequences)
        return DigitsCollection(cls.__create_key, [*digit_count_accumulations])

    def count(self) -> int:
        return sum([acc[0] for acc in self.__digit_sequences_acc])

    def to_segmented_string(self) -> List[str]:
        return [
            d for ds in self.__digit_sequences_acc
            for d in ds[1].to_segmented_string()
        ]


class PhoneNumber(Protocol):

    def digits(self) -> Digits:
        ...

    def to_string(self, formatter) -> str:
        ...


class USPhoneNumber(PhoneNumber):

    def __init__(self, area_code: ThreeDigits, tele_prefix: ThreeDigits,
                 line_number: FourDigits):
        country_code = OneDigit(PhoneNumberDigit.from_int(1))
        self.__phone_number_digits = DigitsCollection.create(
            country_code, area_code, tele_prefix, line_number)

    def digits(self) -> Digits:
        return self.__phone_number_digits

    def to_string(self, formatter) -> str:
        return formatter.format(self)


class PhoneNumberParser(Protocol):

    def parse(self, input: str) -> List[PhoneNumberDigit]:
        ...


class RegexPhoneNumberParser(PhoneNumberParser):

    __r_match = re.compile(
        r'^\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}$'
    )
    __r_sub = re.compile(r'[^0-9]')

    def parse(self, input: str) -> List[PhoneNumberDigit]:
        trimmed = input.strip()
        matching = RegexPhoneNumberParser.__r_match.match(trimmed)

        if matching is None:
            raise ValidationException(
                'Unable to extract phone number digits from input')

        sanitized = RegexPhoneNumberParser.__r_sub.sub('', matching.string)
        return [PhoneNumberDigit.from_int(int(d)) for d in sanitized]


class DigitsToPhoneNumberConverter(Protocol):

    def convert(self, digits: List[PhoneNumberDigit]) -> PhoneNumber:
        ...


class USDigitsToPhoneNumberConverter(DigitsToPhoneNumberConverter):

    def convert(self, digits: List[PhoneNumberDigit]) -> PhoneNumber:
        num_digits = len(digits)
        match num_digits:
            case 10 | 11:
                offset = 0 if num_digits == 10 else 1
                digits_iter = iter(digits[offset:num_digits])

                area_code = ThreeDigits(next(digits_iter), next(digits_iter),
                                        next(digits_iter))

                tele_prefix = ThreeDigits(next(digits_iter), next(digits_iter),
                                          next(digits_iter))

                line_number = FourDigits(next(digits_iter), next(digits_iter),
                                         next(digits_iter), next(digits_iter))

                return USPhoneNumber(area_code, tele_prefix, line_number)
            case 7:
                raise ValidationException(
                    'Unexpected length for US phone number. Are you missing the area code?'
                )
            case _:
                raise ValidationException(
                    f'Unexpected length for US phone number: {num_digits}.')


class PhoneNumberFactory(Protocol):

    def create(self) -> PhoneNumber:
        ...


class FromDigitsStringToPhoneNumber(PhoneNumberFactory):

    def __init__(self, parser: PhoneNumberParser,
                 converter: DigitsToPhoneNumberConverter, value: str):
        self.__parser = parser
        self.__converter = converter
        self.__value = value

    def create(self) -> PhoneNumber:
        digits = self.__parser.parse(self.__value)
        return self.__converter.convert(digits)


class PhoneNumberSegmentFormatter(Protocol):

    def format(self, value: str) -> str:
        ...


class NoChangePhoneNumberSegmentFormatter(PhoneNumberSegmentFormatter):

    def format(self, value: str) -> str:
        return value


class OmitSegmentFormatter(PhoneNumberSegmentFormatter):

    def format(self, value: str) -> str:
        _ = value  # Consume arg. Makes warning go away, but we don't need it
        return ''


class TrailingDotSegmentFormatter(PhoneNumberSegmentFormatter):

    def __init__(self,
                 nested_formatter: PhoneNumberSegmentFormatter | None = None):
        self.__nested_formatter = nested_formatter if nested_formatter is not None else NoChangePhoneNumberSegmentFormatter(
        )

    def format(self, value: str) -> str:
        s = self.__nested_formatter.format(value)
        return f'{s}.'


class PhoneNumberFormatter(Protocol):

    def format(self, phone_number: PhoneNumber) -> str:
        ...


class OrdinalPhoneNumberFormatter(PhoneNumberFormatter):

    def __init__(self, *segment_formatters: PhoneNumberSegmentFormatter):
        self.__segment_formatters = segment_formatters

    def format(self, phone_number: PhoneNumber) -> str:
        digits_collection = phone_number.digits()
        segmented_string = digits_collection.to_segmented_string()

        len_segment_formatters = len(self.__segment_formatters)
        len_segmented_string = len(segmented_string)
        too_few_formatters = len_segment_formatters < len_segmented_string

        zip_fn = self.__zip_pad_with_no_change_formatter if too_few_formatters else self.__zip_with_trunc
        pairs = zip_fn(self.__segment_formatters, segmented_string)

        return ''.join(f.format(s) for (f, s) in pairs)

    @staticmethod
    def __zip_pad_with_no_change_formatter(
            *its) -> Iterable[Tuple[PhoneNumberSegmentFormatter, str]]:
        return zip_longest(*its,
                           fillvalue=NoChangePhoneNumberSegmentFormatter())

    @staticmethod
    def __zip_with_trunc(
            *its) -> Iterable[Tuple[PhoneNumberSegmentFormatter, str]]:
        return zip(*its)
