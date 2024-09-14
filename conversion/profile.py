from conversion import bounded_text, email, phone_number
from dataclasses import dataclass


@dataclass
class Profile:
    applicant_name: bounded_text.BoundedText
    applicant_phone_number: phone_number.PhoneNumber
    applicant_email: email.Email
