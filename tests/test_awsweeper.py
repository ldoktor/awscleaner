import subprocess

import pytest

from awscleaner.awsweeper import AwsweeperRunner


def test_run_returns_list(monkeypatch):
    def fake_run(*args, **kwargs):
        class Result:
            returncode = 0
            stdout = "- type: ec2\n  id: i-123"
            stderr = ""

        return Result()

    monkeypatch.setattr(subprocess, "run", fake_run)

    output = AwsweeperRunner.run(["dummy.yaml"])
    assert isinstance(output, list)
    assert output[0]["type"] == "ec2"
