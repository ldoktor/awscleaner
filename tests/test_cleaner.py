import datetime
import re

import pytest

from awscleaner.cleaner import AwsResourceCleaner


def sort_key(r):
    """Sort by type+id"""
    return (r["type"], r["id"])


def test_process_resources_marks_for_deletion(monkeypatch):
    cleaner = AwsResourceCleaner("resources.yaml", dry_run=True)
    monkeypatch.setattr("awscleaner.cleaner.time.time", lambda: 172802)

    resources_dict = {("ec2", "1"): 1}
    awsweeper_resources = [
        {"type": "ec2", "id": "1", "createdat": None},
        {"type": "s3", "id": "2", "createdat": "1970-01-01T00:00:00.000Z"},
    ]

    updated, deletion = cleaner._process_resources(
        resources_dict, awsweeper_resources
    )
    print(deletion)
    assert any(r["id"] == "1" for r in deletion)  # threshold exceeded
    assert any(r["id"] == "2" for r in deletion)  # createdat


def test_process_resources_complex(monkeypatch):
    cleaner = AwsResourceCleaner("resources.yaml", dry_run=True)
    monkeypatch.setattr("awscleaner.cleaner.time.time", lambda: 172803)

    # Simulated resources.yaml (previously tracked resources)
    resources_dict = {
        ("type1", "id_seen_5"): 5,
        ("type1", "id_seen_2"): 2,
        ("type1", "id_seen_1"): 1,
        ("type2", "id_seen_0"): 0,
        ("type3", "id_missing_in_awsweep"): 1000,
    }

    # Simulated awsweeper output
    awsweeper_resources = [
        {"type": "type1", "id": "id_seen_5", "key1": "value1", "__seen__": 5},
        {"type": "type1", "id": "id_seen_2", "key2": "value2", "__seen__": 2},
        {"type": "type1", "id": "id_seen_1", "key3": "value3", "__seen__": 1},
        {"type": "type2", "id": "id_seen_0", "key4": "value4", "__seen__": 0},
        {"type": "type1", "id": "extra_type1", "key5": "value5"},
        {"type": "awsweep_type", "id": "new_type", "key6": "value6"},
        {
            "type": "type2",
            "id": "createdat1",
            "key7": "value7",
            "createdat": "1970-01-01T00:00:02.000Z",
        },
        {
            "type": "type1",
            "id": "createdat2",
            "key7": "value8",
            "createdat": "1970-01-01T00:00:03.000Z",
        },
    ]

    updated, deletion = cleaner._process_resources(
        resources_dict, awsweeper_resources
    )

    # ---- Expected Updated Resources ----
    expected_updated = [
        {"type": "type1", "id": "id_seen_5", "key1": "value1", "__seen__": 5},
        {"type": "type1", "id": "id_seen_2", "key2": "value2", "__seen__": 2},
        {"type": "type1", "id": "id_seen_1", "key3": "value3", "__seen__": 1},
        {"type": "type2", "id": "id_seen_0", "key4": "value4", "__seen__": 0},
        {
            "type": "type1",
            "id": "extra_type1",
            "key5": "value5",
            "__seen__": 172803,
        },
        {
            "type": "awsweep_type",
            "id": "new_type",
            "key6": "value6",
            "__seen__": 172803,
        },
    ]

    # ---- Expected Deletions ----
    expected_deletion = [
        {"type": "type1", "id": "id_seen_2", "key2": "value2", "__seen__": 2},
        {"type": "type1", "id": "id_seen_1", "key3": "value3", "__seen__": 1},
        {"type": "type2", "id": "id_seen_0", "key4": "value4", "__seen__": 0},
        {
            "type": "type2",
            "id": "createdat1",
            "key7": "value7",
            "createdat": "1970-01-01T00:00:02.000Z",
        },
    ]

    assert sorted(updated, key=sort_key) == sorted(
        expected_updated, key=sort_key
    )
    assert sorted(deletion, key=sort_key) == sorted(
        expected_deletion, key=sort_key
    )


def test_tag_regexp(monkeypatch):
    cleaner = AwsResourceCleaner("resources.yaml", dry_run=True)
    cleaner.tag_regexps = [
        (-1, re.compile(r".*delete_5.*")),
        (9999999, re.compile(r"keep.*")),
        (9999998, re.compile(r".*-createdat1.*")),
        (-2, re.compile(r"^createdat-will-be.*")),
    ]
    monkeypatch.setattr("awscleaner.cleaner.time.time", lambda: 172803)

    # Simulated resources.yaml (previously tracked resources)
    resources_dict = {
        ("type1", "id_delete1"): 5,
        ("type1", "by_id_delete_5"): 5,
        ("type1", "id_default_delete1"): 2,
        ("type1", "id_keep1"): 1,
        ("type2", "id_default_delete2"): 0,
        ("type3", "id_missing_in_awsweep"): 1000,
    }

    # Simulated awsweeper output
    awsweeper_resources = [
        {
            "type": "type1",
            "id": "id_delete1",
            "key1": "value1",
            "__seen__": 5,
            "tags": {"foo/delete_5": True},
        },
        {
            "type": "type1",
            "id": "by_id_delete_5",
            "key1": "value1",
            "__seen__": 5,
        },
        {
            "type": "type1",
            "id": "id_default_delete1",
            "key2": "value2",
            "__seen__": 2,
        },
        {
            "type": "type1",
            "id": "id_keep1",
            "key3": "value3",
            "__seen__": 1,
            "tags": {"Name": "keep-mee"},
        },
        {
            "type": "type2",
            "id": "id_default_delete2",
            "key4": "value4",
            "__seen__": 0,
        },
        {"type": "type1", "id": "extra_type1", "key5": "value5"},
        {"type": "awsweep_type", "id": "new_type", "key6": "value6"},
        {
            "type": "type2",
            "id": "keep_createdat",
            "key7": "value7",
            "createdat": "1970-01-01T00:00:02.000Z",
            "tags": {"this-createdat1-should-be-kept": None},
        },
        {
            "type": "type1",
            "id": "delete_createdat",
            "key7": "value8",
            "createdat": "1970-01-01T00:00:03.000Z",
            "tags": {"some-random-attribute": "createdat-will-be-deleted"},
        },
    ]

    updated, deletion = cleaner._process_resources(
        resources_dict, awsweeper_resources
    )

    # ---- Expected Updated Resources ----
    expected_updated = [
        {
            "type": "type1",
            "id": "id_delete1",
            "key1": "value1",
            "__seen__": 5,
            "tags": {"foo/delete_5": True},
        },
        {
            "type": "type1",
            "id": "by_id_delete_5",
            "key1": "value1",
            "__seen__": 5,
        },
        {
            "type": "type1",
            "id": "id_default_delete1",
            "key2": "value2",
            "__seen__": 2,
        },
        {
            "type": "type1",
            "id": "id_keep1",
            "key3": "value3",
            "__seen__": 1,
            "tags": {"Name": "keep-mee"},
        },
        {
            "type": "type2",
            "id": "id_default_delete2",
            "key4": "value4",
            "__seen__": 0,
        },
        {
            "type": "type1",
            "id": "extra_type1",
            "key5": "value5",
            "__seen__": 172803,
        },
        {
            "type": "awsweep_type",
            "id": "new_type",
            "key6": "value6",
            "__seen__": 172803,
        },
    ]

    # ---- Expected Deletions ----
    expected_deletion = [
        {
            "type": "type1",
            "id": "id_delete1",
            "key1": "value1",
            "__seen__": 5,
            "tags": {"foo/delete_5": True},
        },
        {
            "type": "type1",
            "id": "by_id_delete_5",
            "key1": "value1",
            "__seen__": 5,
        },
        {
            "type": "type1",
            "id": "id_default_delete1",
            "key2": "value2",
            "__seen__": 2,
        },
        {
            "type": "type2",
            "id": "id_default_delete2",
            "key4": "value4",
            "__seen__": 0,
        },
        {
            "type": "type1",
            "id": "delete_createdat",
            "key7": "value8",
            "createdat": "1970-01-01T00:00:03.000Z",
            "tags": {"some-random-attribute": "createdat-will-be-deleted"},
        },
    ]

    # Sort for stable comparison
    assert sorted(updated, key=sort_key) == sorted(
        expected_updated, key=sort_key
    )
    assert sorted(deletion, key=sort_key) == sorted(
        expected_deletion, key=sort_key
    )


"""
def test_save_cleanup(monkeypatch):
    cleaner = AwsResourceCleaner(
        "resources.yaml", cleanup_file="cleanup.yaml", dry_run=False
    )

    # Deletion list provided in scenario
    deletion = [
        {"type": "type1", "id": "id_seen_2", "key2": "value2", "__seen__": 3},
        {"type": "type1", "id": "id_seen_3", "key3": "value3", "__seen__": 4},
        {"type": "type2", "id": "id_seen_5", "key4": "value4", "__seen__": 6},
        {
            "type": "type2",
            "id": "createdat1",
            "key7": "value7",
            "createdat": datetime.datetime(
                2025, 7, 25, 18, 52, 37, 922000, tzinfo=datetime.timezone.utc
            ),
        },
    ]

    captured = {}

    def fake_dump(filename, data):
        captured["filename"] = filename
        captured["data"] = data

    monkeypatch.setattr("awscleaner.cleaner.ResourceIO.dump", fake_dump)

    # Run save_cleanup
    cleaner._save_cleanup(deletion)

    # Expected grouped structure
    expected_grouped = {
        "type1": [{"id": "id_seen_2"}, {"id": "id_seen_3"}],
        "type2": [{"id": "id_seen_5"}, {"id": "createdat1"}],
    }

    assert captured["filename"] == "cleanup.yaml"
    assert captured["data"] == expected_grouped
"""
