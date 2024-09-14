from dataclasses import dataclass
from typing import Generic, List, TypeVar

from conversion import number

RankedEntityType = TypeVar("RankedEntityType")


class RankedEntity(Generic[RankedEntityType]):

    def __init__(self, rank: number.Number, value: RankedEntityType):
        self.__rank = rank
        self.__value = value

    def rank(self) -> number.Number:
        return self.__rank

    def value(self) -> RankedEntityType:
        return self.__value


@dataclass(frozen=True)
class RankedEntityCollectionSortOptions:
    reverse: bool

    @staticmethod
    def default():
        return RankedEntityCollectionSortOptions(reverse=False)


class RankedEntityCollection(Generic[RankedEntityType]):

    def __init__(self, *ranked_entities: RankedEntity[RankedEntityType]):
        self.__ranked_entities = ranked_entities

    def to_sorted_values(
        self,
        options: RankedEntityCollectionSortOptions | None = None
    ) -> List[RankedEntityType]:
        set_options = options if options is not None else RankedEntityCollectionSortOptions.default(
        )
        reverse = set_options.reverse

        return [
            v.value() for v in sorted(self.__ranked_entities,
                                      key=lambda v: v.rank().value(),
                                      reverse=reverse)
        ]
