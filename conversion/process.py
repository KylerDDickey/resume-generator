from conversion import bounded_text, education, email, location, number, phone_number, profile, project, ranked_entity, resume, technical_knowledge, time, work_experience
from dataclasses import dataclass
from typing import Any, Dict, FrozenSet


@dataclass(frozen=True)
class Limits:
    short_bounded_text: bounded_text.BoundedTextLimits
    long_bounded_text: bounded_text.BoundedTextLimits


@dataclass(frozen=True)
class Parsers:
    date: time.DateParser
    email: email.EmailParser
    phone_number: phone_number.PhoneNumberParser


@dataclass(frozen=True)
class Converters:
    digits_to_phone_number: phone_number.DigitsToPhoneNumberConverter


@dataclass(frozen=True)
class Formatters:
    date: time.DateFormatter
    email: email.EmailFormatter
    location: location.LocationFormatter
    number: number.NumberFormatter
    phone_number: phone_number.PhoneNumberFormatter


@dataclass(frozen=True)
class Config:
    limits: Limits
    parsers: Parsers
    converters: Converters
    formatters: Formatters


class Process:

    def __init__(self, config: Config):
        self.__config = config

    def run_with(self, data: Dict[str, Any]) -> Dict[str, Any]:
        limits = self.__config.limits
        parsers = self.__config.parsers
        converters = self.__config.converters
        formatters = self.__config.formatters

        def iter(list_data, fn) -> FrozenSet[Any]:
            return frozenset([fn(d) for d in list_data])

        def get_short_text(text) -> bounded_text.BoundedText:
            return bounded_text.BoundedText(limits.short_bounded_text, text)

        def get_long_text(text) -> bounded_text.BoundedText:
            return bounded_text.BoundedText(limits.long_bounded_text, text)

        def get_ranked_text(
                ranked_text, text_fn
        ) -> ranked_entity.RankedEntity[bounded_text.BoundedText]:
            return ranked_entity.RankedEntity(
                number.Number(ranked_text['rank']),
                text_fn(ranked_text['text']))

        def get_short_ranked_text(
            ranked_text
        ) -> ranked_entity.RankedEntity[bounded_text.BoundedText]:
            return get_ranked_text(ranked_text, get_short_text)

        def get_long_ranked_text(
            ranked_text
        ) -> ranked_entity.RankedEntity[bounded_text.BoundedText]:
            return get_ranked_text(ranked_text, get_long_text)

        def get_location(location_data) -> location.Location:
            return location.FromStringsToCityAndStateLocation(
                location_data.get('city'),
                location_data.get('state')).create()

        def get_work_location(location_data) -> location.Location:
            loc = get_location(location_data)
            if location_data.get('remote') == True:
                return location.RemoteLocation(loc)
            return loc

        def get_degree(degree_data) -> education.Degree:
            program = get_short_text(degree_data.get('program'))
            major = get_short_text(degree_data.get('major'))

            degree_data_minor = degree_data.get('minor')
            minor = None if degree_data_minor is None else get_short_text(
                degree_data_minor)
            degree_data_emphasis = degree_data.get('emphasis')
            emphasis = None if degree_data_emphasis is None else get_short_text(
                degree_data_emphasis)

            return education.Degree(program, major, minor, emphasis)

        def get_involvement_level(
                involvement_leve_data) -> education.InvolvementLevel:
            title = get_short_text(involvement_leve_data.get('title'))
            start_date = time.FromStartDate(
                parsers.date, involvement_leve_data.get('startDate')).create()
            end_date = time.FromEndDate(
                parsers.date, involvement_leve_data.get('endDate')).create()
            return education.InvolvementLevel(title, start_date, end_date)

        def get_involvement(involvement_data) -> education.Involvement:
            organization = get_short_text(involvement_data.get('organization'))
            levels = iter(involvement_data.get('levels'),
                          get_involvement_level)
            return education.Involvement(organization, levels)

        def get_profile(profile_data) -> profile.Profile:
            applicant_name = get_short_text(profile_data.get('name'))
            applicant_phone_number = phone_number.FromDigitsStringToPhoneNumber(
                parsers.phone_number, converters.digits_to_phone_number,
                profile_data.get('phoneNumber')).create()
            applicant_email = email.FromEmailString(
                parsers.email, profile_data.get('email')).create()
            return profile.Profile(applicant_name, applicant_phone_number,
                                   applicant_email)

        def get_work_experience(
                work_experience_data) -> work_experience.WorkExperience:
            company_name = get_short_text(
                work_experience_data.get('companyName'))
            work_location = get_work_location(
                work_experience_data.get('location'))
            title = get_short_text(work_experience_data.get('title'))
            start_date = time.FromStartDate(
                parsers.date, work_experience_data.get('startDate')).create()
            end_date = time.FromEndDate(
                parsers.date, work_experience_data.get('endDate')).create()
            contributions = iter(work_experience_data.get('contributions'),
                                 get_long_ranked_text)
            return work_experience.WorkExperience(company_name, work_location,
                                                  title, start_date, end_date,
                                                  contributions)

        def get_education(education_data) -> education.Education:
            degree = get_degree(education_data.get('degree'))
            institution = get_short_text(education_data.get('institution'))
            institution_location = get_location(education_data.get('location'))
            start_date = time.FromStartDate(
                parsers.date, education_data.get('startDate')).create()
            end_date = time.FromEndDate(
                parsers.date, education_data.get('endDate')).create()
            notable_coursework = iter(education_data.get('notableCoursework'),
                                      get_short_text)
            involvement = iter(education_data.get('involvement'),
                               get_involvement)
            gpa = number.Number(education_data.get('gpa'))
            return education.Education(degree, institution,
                                       institution_location, start_date,
                                       end_date, notable_coursework,
                                       involvement, gpa)

        def get_technical_knowledge(
            technical_knowledge_data
        ) -> technical_knowledge.TechnicalKnowledge:
            category = get_short_text(technical_knowledge_data.get('category'))
            proficiencies = iter(technical_knowledge_data.get('proficiencies'),
                                 get_short_ranked_text)
            return technical_knowledge.TechnicalKnowledge(
                category, proficiencies)

        def get_ranked_technical_knowledge(
            ranked_technical_knowledge_data
        ) -> ranked_entity.RankedEntity[
                technical_knowledge.TechnicalKnowledge]:
            return ranked_entity.RankedEntity(
                number.Number(ranked_technical_knowledge_data['rank']),
                get_technical_knowledge(ranked_technical_knowledge_data))

        def get_project(project_data) -> project.Project:
            title = get_short_text(project_data.get('title'))
            description = get_long_text(project_data.get('description'))
            return project.Project(title, description)

        def get_ranked_project(
            ranked_project_data
        ) -> ranked_entity.RankedEntity[project.Project]:
            return ranked_entity.RankedEntity(
                number.Number(ranked_project_data['rank']),
                get_project(ranked_project_data))

        applicant_resume = resume.Resume(
            get_profile(data.get('profile')),
            iter(data.get('workExperience'), get_work_experience),
            iter(data.get('education'), get_education),
            iter(data.get('technicalKnowledge'),
                 get_ranked_technical_knowledge),
            iter(data.get('projects'), get_ranked_project))

        return {
            'profile': {
                'name':
                applicant_resume.applicant_profile.applicant_name.to_string(),
                'phone_number':
                applicant_resume.applicant_profile.applicant_phone_number.
                to_string(formatters.phone_number),
                'email':
                applicant_resume.applicant_profile.applicant_email.to_string(
                    formatters.email)
            },
            'work_experience': [{
                'company_name':
                we.company_name.to_string(),
                'location':
                we.work_location.to_string(formatters.location),
                'title':
                we.title.to_string(),
                'start_date':
                we.start_date.to_string(formatters.date),
                'end_date':
                we.end_date.to_string(formatters.date),
                'contributions': [
                    v.to_string()
                    for v in ranked_entity.RankedEntityCollection(
                        *[c for c in we.contributions]).to_sorted_values()
                ]
            } for we in sorted(applicant_resume.applicant_work_experience,
                               key=lambda v: v.start_date.value().timestamp(),
                               reverse=True)],
            'education': [{
                'degree': {
                    'program':
                    e.degree.program.to_string(),
                    'major':
                    e.degree.major.to_string(),
                    'minor':
                    None
                    if e.degree.minor is None else e.degree.minor.to_string(),
                    'emphasis':
                    None if e.degree.emphasis is None else
                    e.degree.emphasis.to_string()
                },
                'institution':
                e.institution.to_string(),
                'location':
                e.institution_location.to_string(formatters.location),
                'start_date':
                e.start_date.to_string(formatters.date),
                'end_date':
                e.end_date.to_string(formatters.date),
                'notable_coursework': [
                    nc.to_string()
                    for nc in sorted(e.notable_coursework,
                                     key=lambda v: v.to_string().upper())
                ],
                'involvement': [{
                    'organization':
                    i.organization.to_string(),
                    'levels': [{
                        'title':
                        l.title.to_string(),
                        'start_date':
                        l.start_date.to_string(formatters.date),
                        'end_date':
                        l.end_date.to_string(formatters.date)
                    } for l in sorted(
                        i.levels,
                        key=lambda v: v.start_date.value().timestamp(),
                        reverse=True)]
                } for i in sorted(
                    e.involvement,
                    key=lambda v: v.organization.to_string().upper())],
                'gpa':
                e.gpa.to_string(formatters.number)
            } for e in sorted(applicant_resume.applicant_education,
                              key=lambda v: v.start_date.value().timestamp(),
                              reverse=True)],
            'technical_knowledge': [{
                'category':
                v.category.to_string(),
                'proficiencies': [
                    t.to_string()
                    for t in ranked_entity.RankedEntityCollection(
                        *[p for p in v.proficiencies]).to_sorted_values()
                ]
            } for v in ranked_entity.RankedEntityCollection(
                *[tk for tk in applicant_resume.applicant_technical_knowledge
                  ]).to_sorted_values()],
            'projects': [{
                'title': v.title.to_string(),
                'description': v.description.to_string()
            } for v in ranked_entity.RankedEntityCollection(
                *[p for p in applicant_resume.applicant_projects
                  ]).to_sorted_values()]
        }
