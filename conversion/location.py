from conversion.validation import ValidationException
from itertools import zip_longest
from typing import Iterable, List, Protocol, Tuple


class PlaceIdentifier(Protocol):

    def to_segmented_string(self) -> List[str]:
        ...


class PlaceName(PlaceIdentifier):

    def __init__(self, value: str):
        self.__value = value

    def to_segmented_string(self) -> List[str]:
        return [self.__value]


class PlaceIdentifierCollection(PlaceIdentifier):

    def __init__(self, *place_identifiers: PlaceIdentifier):
        self.__place_identifiers = place_identifiers

    def to_segmented_string(self) -> List[str]:
        return [
            n for pn in self.__place_identifiers
            for n in pn.to_segmented_string()
        ]


class Location(Protocol):

    def value(self) -> PlaceIdentifierCollection:
        ...

    def to_string(self, formatter) -> str:
        ...


class CityAndStateLocation(Location):

    def __init__(self, city: PlaceName, state: PlaceName):
        self.__place = PlaceIdentifierCollection(city, state)

    def value(self) -> PlaceIdentifierCollection:
        return self.__place

    def to_string(self, formatter) -> str:
        return formatter.format(self)


class RemoteLocation(Location):

    def __init__(self, location: Location):
        self.__location = location

    def value(self) -> PlaceIdentifierCollection:
        return self.__location.value()

    def to_string(self, formatter) -> str:
        return formatter.format(self)


class LocationFactory(Protocol):

    def create(self) -> Location:
        ...


class FromStringsToCityAndStateLocation(LocationFactory):

    def __init__(self, city_name: str, state_name: str):
        self.__city_name = city_name
        self.__state_name = state_name

    def create(self) -> Location:

        def get_non_empty_or_none_str(input: str, error_message: str) -> str:
            name = input if input is not None else ''
            trimmed_name = name.strip()
            name_is_none_or_empty = trimmed_name == ''
            if name_is_none_or_empty:
                raise ValidationException(error_message)

            return trimmed_name

        valid_city_name = get_non_empty_or_none_str(
            self.__city_name,
            'Non-empty city name required for city and state location')
        city = PlaceName(valid_city_name)

        valid_state_name = get_non_empty_or_none_str(
            self.__state_name,
            'Non-empty state name required for city and state location')
        state = PlaceName(valid_state_name)

        return CityAndStateLocation(city, state)


class LocationSegmentFormatter(Protocol):

    def format(self, value: str) -> str:
        ...


class NoChangeLocationSegmentFormatter(LocationSegmentFormatter):

    def format(self, value: str) -> str:
        return value


class TrailingCommaSpaceLocationSegmentFormatter(LocationSegmentFormatter):

    def format(self, value: str) -> str:
        return f'{value}, '


class LocationFormatter(Protocol):

    def format(self, location: Location) -> str:
        ...


class OrdinalLocationFormatter(LocationFormatter):

    def __init__(self, *segment_formatters: LocationSegmentFormatter,
                 **options):

        def default_remote_location_post_formatter(input: str):
            return input

        self.__segment_formatters = segment_formatters
        self.__remote_formatter = options.get(
            'remote_location_post_formatter',
            default_remote_location_post_formatter)

    def format(self, location: Location) -> str:

        def zip_pad_with_no_change_formatter(
                *its) -> Iterable[Tuple[LocationSegmentFormatter, str]]:
            return zip_longest(*its,
                               fillvalue=NoChangeLocationSegmentFormatter())

        def zip_with_trunc(
                *its) -> Iterable[Tuple[LocationSegmentFormatter, str]]:
            return zip(*its)

        def apply_formatters(location: Location):
            segmented_string = location.value().to_segmented_string()

            len_segment_formatters = len(self.__segment_formatters)
            len_segmented_string = len(segmented_string)
            too_few_formatters = len_segment_formatters < len_segmented_string

            zip_fn = zip_pad_with_no_change_formatter if too_few_formatters else zip_with_trunc
            pairs = zip_fn(self.__segment_formatters, segmented_string)

            return ''.join(f.format(s) for (f, s) in pairs)

        match location:
            case CityAndStateLocation():
                return apply_formatters(location)
            case RemoteLocation():
                return self.__remote_formatter(apply_formatters(location))
            case other:
                raise ValueError(
                    f'Unrecognized Location implementation: {other}')
