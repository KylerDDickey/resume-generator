from conversion import bounded_text, location, ranked_entity, time
from dataclasses import dataclass
from typing import FrozenSet


@dataclass(frozen=True)
class WorkExperience:
    company_name: bounded_text.BoundedText
    work_location: location.Location
    title: bounded_text.BoundedText
    start_date: time.Date
    end_date: time.Date
    contributions: FrozenSet[ranked_entity.RankedEntity[
        bounded_text.BoundedText]]
