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
import sys
import time
from collections import defaultdict
from pprint import pprint

import yaml

from .awsweeper import AwsweeperRunner
from .io_utils import ResourceIO


class AwsResourceCleaner:
    """
    Core logic for cleaning up AWS resources.

    This class manages the process of identifying and marking AWS resources
    for cleanup based on a threshold of how many times they have been seen.
    It integrates with external resource tracking and awsweeper to make
    decisions about which resources should be removed.

    :ivar THRESHOLD: How long after the resource was seen for the first time
                     before it's set to be deleted.
    :vartype THRESHOLD: int
    """

    THRESHOLD = 172800

    def __init__(
        self,
        resources_file,
        cleanup_file=None,
        dry_run=False,
        awsweeper_file=None,
        awsweeper_args=None,
    ):
        """
        Initialize the AwsResourceCleaner.

        :param resources_file: Path to the file containing current AWS resource data.
        :type resources_file: str
        :param cleanup_file: Path to the file where deletion list will be saved.
        :type cleanup_file: str, optional
        :param dry_run: If True, perform a dry run without actually modifying files.
        :type dry_run: bool
        :param awsweeper_file: Path to an awsweeper output file; if not provided,
                awsweeper is executed internally.
        :type awsweeper_file: str, optional
        :param awsweeper_args: Arguments for awsweeper runner when used internally.
        :type awsweeper_args: dict, optional
        """
        self.resources_file = resources_file
        self.cleanup_file = cleanup_file
        self.dry_run = dry_run
        self.awsweeper_file = awsweeper_file
        self.awsweeper_args = awsweeper_args

    def run(self):
        """
        Process the resources into to-be-cleaned list.

        Loads existing resources and awsweeper output, processes them to determine which
        should be marked for deletion based on seen count thresholds, then saves updated
        resource data and the cleanup list.

        :returns: None
        """
        resources = self._load_resources()
        awsweeper_resources = self._load_awsweeper_resources()

        updated_resources, deletion_list = self._process_resources(
            resources, awsweeper_resources
        )

        self._save_resources(updated_resources)
        self._save_cleanup(deletion_list)

    def _load_resources(self):
        """
        Load existing resources from file.

        :returns: A dictionary mapping resource keys (type, id) to their seen counts.
        :rtype: dict
        """
        resources = ResourceIO.load(self.resources_file)
        return {(r["type"], r["id"]): r.get("__seen__", 0) for r in resources}

    def _load_awsweeper_resources(self):
        """
        Load awsweeper resource data.

        If an awsweeper file is specified, load from that. Otherwise,
        execute the AwsweeperRunner to get current resource data.

        :returns: List of resource dictionaries from awsweeper.
        :rtype: list
        """
        if self.awsweeper_file:
            return ResourceIO.load(self.awsweeper_file)
        return AwsweeperRunner.run(self.awsweeper_args)

    def _process_resources(self, resources_dict, awsweeper_resources):
        """
        Process AWS resources to determine which should be deleted.

        Increments the seen count for each resource and marks it for deletion
        if the count exceeds the threshold. Also handles resources with a "createdat"
        field by immediately marking them for deletion.

        :param resources_dict: Dictionary of existing resources and their seen counts.
        :type resources_dict: dict
        :param awsweeper_resources: List of resources from awsweeper output.
        :type awsweeper_resources: list

        :returns: A tuple containing updated resource list and the deletion list.
        :rtype: tuple
        """
        updated_resources = {}
        deletion_list = []
        deadline = time.time() - self.THRESHOLD

        for r in awsweeper_resources:
            key = (r["type"], r["id"])

            if r.get("createdat") is not None:
                pprint(r, sys.stderr)
                deletion_list.append(r)
                continue

            seen = resources_dict.get(key, None)
            print(f"seen {seen}")
            if seen is None:
                print(f"Adding __seen__ to {r}")
                seen = time.time()
                r["__seen__"] = seen
            if seen < deadline:
                pprint(r, sys.stderr)
                deletion_list.append(r)
            r["__seen__"] = seen
            updated_resources[key] = r

        return list(updated_resources.values()), deletion_list

    def _save_resources(self, updated_resources):
        """
        Save the updated resource data to file.

        :param updated_resources: List of updated resource dictionaries.
        :type updated_resources: list
        """
        if self.dry_run:
            print(f"[DRY RUN] Not updating {self.resources_file}")
        else:
            ResourceIO.dump(self.resources_file, updated_resources)

    def _save_cleanup(self, deletion_list):
        """
        Save the cleanup list to file and print it in YAML format.

        Groups resources by type before saving. If a cleanup file is specified,
        writes the grouped data there as well.

        :param deletion_list: List of resource dictionaries marked for deletion.
        :type deletion_list: list
        """
        grouped = defaultdict(list)
        for r in deletion_list:
            grouped[r["type"]].append({"id": r["id"]})

        print(yaml.dump(dict(grouped)))

        if self.cleanup_file:
            if self.dry_run:
                print(f"[DRY RUN] Not writing {self.cleanup_file}")
            else:
                ResourceIO.dump(self.cleanup_file, dict(grouped))
