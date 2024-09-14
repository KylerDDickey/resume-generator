from conversion import education, profile, project, ranked_entity, technical_knowledge, work_experience
from dataclasses import dataclass
from typing import FrozenSet


@dataclass(frozen=True)
class Resume:
    applicant_profile: profile.Profile
    applicant_work_experience: FrozenSet[work_experience.WorkExperience]
    applicant_education: FrozenSet[education.Education]
    applicant_technical_knowledge: FrozenSet[ranked_entity.RankedEntity[
        technical_knowledge.TechnicalKnowledge]]
    applicant_projects: FrozenSet[ranked_entity.RankedEntity[project.Project]]
