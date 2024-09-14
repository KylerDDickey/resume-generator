from typing import Any, Dict
from conversion import bounded_text, email, location, number, phone_number, process, time
import argparse
import jinja2 as jinja
import json


def configure_and_get_process() -> process.Process:

    def configure_and_get_short_bounded_text_limit(
    ) -> bounded_text.BoundedTextLimits:
        char_limit = 64
        bounded_text_limits = bounded_text.BoundedTextLimits(char_limit)

        return bounded_text_limits

    def configure_and_get_long_bounded_text_limit(
    ) -> bounded_text.BoundedTextLimits:
        char_limit = 1024
        bounded_text_limits = bounded_text.BoundedTextLimits(char_limit)

        return bounded_text_limits

    def configure_and_get_date_parser() -> time.DateParser:
        date_parser = time.YearMonthParser()

        return date_parser

    def configure_and_get_email_parser() -> email.EmailParser:
        email_parser = email.RegexEmailParser()

        return email_parser

    def configure_and_get_phone_number_parser(
    ) -> phone_number.PhoneNumberParser:
        phone_number_sanitizer = phone_number.RegexPhoneNumberParser()

        return phone_number_sanitizer

    def configure_and_get_digits_to_phone_number_converter(
    ) -> phone_number.DigitsToPhoneNumberConverter:
        phone_number_converter = phone_number.USDigitsToPhoneNumberConverter()

        return phone_number_converter

    def configure_and_get_date_formatter() -> time.DateFormatter:
        date_formatter = time.FullMonthNameYearFormatter()

        return date_formatter

    def configure_and_get_email_formatter() -> email.EmailFormatter:
        email_formatter = email.EmailFormatter()

        return email_formatter

    def configure_and_get_location_formatter() -> location.LocationFormatter:

        def remote_location_post_formatter(s: str) -> str:
            return f'Remote (Headquarters in {s})'

        city_name_formatter = location.TrailingCommaSpaceLocationSegmentFormatter(
        )
        city_and_state_formatter = location.OrdinalLocationFormatter(
            city_name_formatter,
            remote_location_post_formatter=remote_location_post_formatter)

        return city_and_state_formatter

    def configure_and_get_number_formatter() -> number.NumberFormatter:
        scale = number.Scale.Three
        number_formatting_flags = number.NumberFormattingFlags.GROUPING
        number_formatter = number.ScaledNumberFormatter(
            scale, number_formatting_flags)

        return number_formatter

    def configure_and_get_phone_number_formatter(
    ) -> phone_number.PhoneNumberFormatter:
        omit_segment_formatter = phone_number.OmitSegmentFormatter()
        trailing_dot_segment_formatter = phone_number.TrailingDotSegmentFormatter(
        )
        phone_number_formatter = phone_number.OrdinalPhoneNumberFormatter(
            omit_segment_formatter, trailing_dot_segment_formatter,
            trailing_dot_segment_formatter)

        return phone_number_formatter

    short_bounded_text_limit = configure_and_get_short_bounded_text_limit()
    long_bounded_text_limit = configure_and_get_long_bounded_text_limit()
    limits = process.Limits(short_bounded_text_limit, long_bounded_text_limit)

    date_parser = configure_and_get_date_parser()
    email_parser = configure_and_get_email_parser()
    phone_number_parser = configure_and_get_phone_number_parser()
    parsers = process.Parsers(date_parser, email_parser, phone_number_parser)

    digits_to_phone_number_converter = configure_and_get_digits_to_phone_number_converter(
    )
    converters = process.Converters(digits_to_phone_number_converter)

    date_formatter = configure_and_get_date_formatter()
    email_formatter = configure_and_get_email_formatter()
    location_formatter = configure_and_get_location_formatter()
    number_formatter = configure_and_get_number_formatter()
    phone_number_formatter = configure_and_get_phone_number_formatter()
    formatters = process.Formatters(date_formatter, email_formatter,
                                    location_formatter, number_formatter,
                                    phone_number_formatter)

    config = process.Config(limits, parsers, converters, formatters)
    return process.Process(config)


def get_template(location: str, name: str) -> jinja.Template:
    loader = jinja.FileSystemLoader(location.strip())
    env = jinja.Environment(loader=loader)
    template = env.get_template(f'{name.strip()}.md.jinja')
    return template


def read_in_file(file_name: str) -> Dict[str, Any]:
    with open(file_name.strip(), 'r') as file:
        return json.load(file)


def write_out_file(file_name: str, document: str) -> None:
    with open(file_name.strip(), 'w') as file:
        file.write(document)


def get_arg_parser() -> argparse.ArgumentParser:
    prog = "Resume Generator"
    description = "A data-driven program that generates resumes using templates."
    parser = argparse.ArgumentParser(prog=prog, description=description)

    template_name_help = '''
    The name of the template to use. Corresponds to the name of the file in the
    default or given templates directory without extensions, i.e., "pdf" in
    reference to "pdf.md.jinja".
    '''
    parser.add_argument('template_name',
                        metavar='TEMPLATE_NAME',
                        type=str,
                        help=template_name_help)

    template_location_help = '''
    The directory containing template files.
    '''
    parser.add_argument('-t',
                        '--template',
                        dest='template_location',
                        type=str,
                        required=False,
                        default='templates',
                        help=template_location_help)

    input_file_name_help = '''
    The name of the file containing the data to apply to the given template.
    '''
    parser.add_argument('-i',
                        '--input',
                        dest='input_file_name',
                        type=str,
                        required=True,
                        help=input_file_name_help)

    output_file_name_help = '''
    The name of the file to write the document contents to.
    '''
    parser.add_argument('-o',
                        '--output',
                        dest='output_file_name',
                        type=str,
                        required=True,
                        help=output_file_name_help)

    return parser


def main():
    argument_parser = get_arg_parser()
    args = argument_parser.parse_args()

    template = get_template(args.template_location, args.template_name)
    data = read_in_file(args.input_file_name)

    proc = configure_and_get_process()
    template_data = proc.run_with(data)
    document = template.render(template_data)

    write_out_file(args.output_file_name, document)


if __name__ == "__main__":
    main()
