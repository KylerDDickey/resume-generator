from conversion import bounded_text, location, number, time
from dataclasses import dataclass
from typing import FrozenSet


@dataclass(eq=True, frozen=True)
class Degree:
    program: bounded_text.BoundedText
    major: bounded_text.BoundedText
    minor: bounded_text.BoundedText | None = None
    emphasis: bounded_text.BoundedText | None = None


@dataclass(eq=True, frozen=True)
class InvolvementLevel:
    title: bounded_text.BoundedText
    start_date: time.Date
    end_date: time.Date


@dataclass(eq=True, frozen=True)
class Involvement:
    organization: bounded_text.BoundedText
    levels: FrozenSet[InvolvementLevel]


@dataclass(eq=True, frozen=True)
class Education:
    degree: Degree
    institution: bounded_text.BoundedText
    institution_location: location.Location
    start_date: time.Date
    end_date: time.Date
    notable_coursework: FrozenSet[bounded_text.BoundedText]
    involvement: FrozenSet[Involvement]
    gpa: number.Number
