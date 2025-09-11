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
import os
import subprocess
import sys

import yaml


class AwsweeperRunner:
    """Handles running awsweeper or loading its output from a file."""

    @staticmethod
    def run(args):
        """
        Run awsweeper with the specified configuration file and return parsed YAML output.

        :param args: Path to the configuration file
        :type args: list
        :return: Parsed YAML output from awsweeper or empty list if no output
        :rtype: list
        """
        if not args:
            args = []
        result = subprocess.run(
            ["awsweeper", "--dry-run", "--output", "yaml"] + args,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            print("Error running awsweeper:", result.stderr, file=sys.stderr)
            sys.exit(1)
        elif os.environ.get("DEBUG", "no").lower() == "yes":
            print(
                f"awsweeper stdout:\n{result.stdout}\nawsweeper stderr:\n"
                f"{result.stderr}",
                file=sys.stderr,
            )

        try:
            return yaml.safe_load(result.stdout) or []
        except yaml.YAMLError as e:
            print(f"Error parsing awsweeper output: {e}", file=sys.stderr)
            sys.exit(1)
