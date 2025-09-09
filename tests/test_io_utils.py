import os
import tempfile

import yaml

from awscleaner.io_utils import ResourceIO


def test_local_file_load_and_dump():
    data = [{"type": "ec2", "id": "1"}]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".yaml")
    tmp.close()

    ResourceIO.dump(tmp.name, data)
    loaded = ResourceIO.load(tmp.name)

    assert loaded == data
    os.remove(tmp.name)
