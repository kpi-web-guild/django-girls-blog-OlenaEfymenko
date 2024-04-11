#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from contextlib import contextmanager, nullcontext, suppress

with suppress(ImportError):
    from coverage import Coverage


@contextmanager
def coverage_context():
    """Context manager to collect code coverage data.

    Uses coverage package to collect coverage, generate reports
    and print coverage percentage.
    """
    cov = Coverage()
    cov.erase()
    with cov.collect():
        yield
    cov.save()
    print(f'Coverage is {cov.report()}%')

    covered = cov.report()
    fail_under = cov.config.get_option('report:fail_under')
    if covered < fail_under:
        raise SystemExit(2)

    cov.html_report()
    cov.xml_report()


@contextmanager
def maybe_measure_coverage():
    """Check if command is 'test' and only then collect coverage."""
    try:
        command = sys.argv[1]
    except IndexError:
        command = 'help'

    running_tests = command == 'test'

    ctx = nullcontext() if not running_tests else coverage_context()
    with ctx:
        yield


@maybe_measure_coverage()
def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    try:
        # pylint: disable-next=import-outside-toplevel
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            'available on your PYTHONPATH environment variable? Did you '
            'forget to activate a virtual environment?',
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
