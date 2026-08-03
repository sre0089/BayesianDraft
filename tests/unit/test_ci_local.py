from scripts.ci_local import command_labels


def test_ci_local_lists_expected_checks() -> None:
    assert command_labels() == [
        "python-tests",
        "ruff",
        "mypy",
        "web-tests",
        "web-lint",
        "web-build",
    ]
