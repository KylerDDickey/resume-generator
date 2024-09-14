from conversion import bounded_text
from dataclasses import dataclass


@dataclass(frozen=True)
class Project:
    title: bounded_text.BoundedText
    description: bounded_text.BoundedText
