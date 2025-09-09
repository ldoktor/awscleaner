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
import sys
import tempfile

import yaml

try:
    import boto3
    from botocore.exceptions import ClientError

    S3_SUPPORT = True
except ImportError:
    S3_SUPPORT = False


class ResourceIO:
    """Handles loading and saving resources from/to YAML files and S3."""

    @staticmethod
    def load(filename: str):
        """
        Load data from a file or an S3 object.

        :param filename: The path to the file or the S3 URI (e.g., 's3://bucket/key')
        :type filename: str

        :returns: The loaded YAML data
        :rtype: dict or list or any
        """
        if filename.startswith("s3://"):
            return ResourceIO._load_from_s3(filename)
        with open(filename, "r") as f:
            return yaml.safe_load(f)

    @staticmethod
    def dump(filename: str, data):
        """
        Save data to a file or an S3 object.

        :param filename: The path to the file or the S3 URI (e.g., 's3://bucket/key')
        :type filename: str

        :param data: The data to be saved
        :type data: dict or list or any
        """
        if filename.startswith("s3://"):
            return ResourceIO._dump_to_s3(filename, data)
        with open(filename, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    @staticmethod
    def _load_from_s3(path: str):
        """
        Load YAML data from an S3 object.

        :param path: The S3 URI (e.g., 's3://bucket/key')
        :type path: str

        :returns: The loaded YAML data
        :rtype: dict or list or any

        :raises ValueError: If the S3 path format is invalid
        """
        if not S3_SUPPORT:
            print("For s3:// support install boto3 python libraries")
            sys.exit(1)

        s3_path = path[5:]
        if "/" not in s3_path:
            raise ValueError("Invalid S3 path format")

        bucket_name, key = s3_path.split("/", 1)

        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.close()
        try:
            s3_client = boto3.client("s3")
            s3_client.download_file(bucket_name, key, temp_file.name)
            with open(temp_file.name, "r") as f:
                return yaml.safe_load(f)
        except ClientError as e:
            print(f"Error downloading from S3: {e}")
            sys.exit(1)
        finally:
            os.remove(temp_file.name)

    @staticmethod
    def _dump_to_s3(path: str, data):
        """
        Save YAML data to an S3 object.

        :param path: The S3 URI (e.g., 's3://bucket/key')
        :type path: str

        :param data: The data to be saved
        :type data: dict or list or any
        """
        if not S3_SUPPORT:
            print("For s3:// support install boto3 python libraries")
            sys.exit(1)

        s3_path = path[5:]
        if "/" not in s3_path:
            raise ValueError("Invalid S3 path format")

        bucket_name, key = s3_path.split("/", 1)

        temp_file = tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".yaml"
        )
        try:
            temp_file.write(
                yaml.dump(data, default_flow_style=False, sort_keys=False)
            )
            temp_file.close()
            s3_client = boto3.client("s3")
            s3_client.upload_file(temp_file.name, bucket_name, key)
        finally:
            os.remove(temp_file.name)
