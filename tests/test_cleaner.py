import datetime

import pytest

from awscleaner.cleaner import AwsResourceCleaner


def test_process_resources_marks_for_deletion(monkeypatch):
    cleaner = AwsResourceCleaner("resources.yaml", dry_run=True)
    monkeypatch.setattr("awscleaner.cleaner.time.time", lambda: 172802)

    resources_dict = {("ec2", "1"): 1}
    awsweeper_resources = [
        {"type": "ec2", "id": "1", "createdat": None},
        {"type": "s3", "id": "2", "createdat": "2021-01-01"},
    ]

    updated, deletion = cleaner._process_resources(
        resources_dict, awsweeper_resources
    )
    assert any(r["id"] == "1" for r in deletion)  # threshold exceeded
    assert any(r["id"] == "2" for r in deletion)  # createdat not null
    assert all("__seen__" in r for r in updated)


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
            "createdat": datetime.datetime(
                2025, 7, 25, 18, 52, 37, 922000, tzinfo=datetime.timezone.utc
            ),
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
            "createdat": datetime.datetime(
                2025, 7, 25, 18, 52, 37, 922000, tzinfo=datetime.timezone.utc
            ),
        },
    ]

    # Sort for stable comparison
    def sort_key(r):
        return (r["type"], r["id"])

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
