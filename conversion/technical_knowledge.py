from conversion import bounded_text, ranked_entity
from dataclasses import dataclass
from typing import FrozenSet


@dataclass(frozen=True)
class TechnicalKnowledge:
    category: bounded_text.BoundedText
    proficiencies: FrozenSet[ranked_entity.RankedEntity[
        bounded_text.BoundedText]]
