# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright: Red Hat Inc. 2025
# Author: Lukas Doktor <ldoktor@redhat.com>
import argparse

from .cleaner import AwsResourceCleaner


def parse_age(value: str) -> float:
    """Parse age string with optional suffix (s/m/h/d/M/Y) into seconds as float."""
    # Define multipliers for each unit (in seconds)
    units = {
        "s": 1.0,  # second
        "m": 60.0,  # minute
        "h": 3600.0,  # hour
        "D": 86400.0,  # day
        "M": 2592000.0,  # month (approx 30 days)
        "Y": 31536000.0,  # year (approx 365 days)
    }

    # Extract last character as unit, if valid
    if len(value) > 1 and value[-1].lower() in units:
        num = float(value[:-1])  # all but last char
        unit = value[-1].lower()
    else:
        num = float(value)  # no suffix, assume seconds
        unit = "s"  # default to seconds

    return num * units[unit]


def main():
    """
    Main entry point for the AWS resource cleaner command-line tool.

    This function parses command-line arguments and executes the cleanup process
    based on the provided configuration files and options.
    """
    parser = argparse.ArgumentParser(
        description="Clean up unused AWS resources based on awsweeper and resource tracking."
    )
    parser.add_argument(
        "resources_file", help="Path to the resources.yaml file"
    )
    parser.add_argument(
        "cleanup_file",
        help="Path to the cleanup.yaml output file",
        default=None,
        nargs="?",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be cleaned without making changes",
    )
    parser.add_argument(
        "--awsweeper-file",
        help="Path to awsweeper output "
        "YAML file to be used directly rather than executing "
        "awsweeper",
    )
    parser.add_argument(
        "--awsweeper-args",
        help="Extra arguments used when '--awsweeper-file' is not used "
        "('--dry-run --output yaml' is always added)",
        nargs="+",
    )

    parser.add_argument(
        "--age",
        help="How old resources should be deleted, optional suffix smhDMY "
        f"({AwsResourceCleaner.THRESHOLD})",
        type=parse_age,
    )

    args = parser.parse_args()

    cleaner = AwsResourceCleaner(
        resources_file=args.resources_file,
        cleanup_file=args.cleanup_file,
        dry_run=args.dry_run,
        awsweeper_file=args.awsweeper_file,
        awsweeper_args=args.awsweeper_args,
    )
    if isinstance(args.age, float):
        cleaner.THRESHOLD = args.age
    cleaner.run()


if __name__ == "__main__":
    main()
