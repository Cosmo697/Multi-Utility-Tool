from multi_utility_tool.utils.health_checks import (
    DependencyStatus,
    check_dependencies,
    summarize_failures,
)


def test_check_dependencies_detects_missing_and_present(monkeypatch):
    statuses = check_dependencies([("yaml", True), ("nonexistent_lib_xyz", False)])
    assert any(status.name == "yaml" and status.installed for status in statuses)
    assert any(status.name == "nonexistent_lib_xyz" and not status.installed for status in statuses)


def test_summarize_failures_filters_required_only():
    statuses = [
        DependencyStatus(name="present", required=True, installed=True, version="1.0", message="OK"),
        DependencyStatus(name="missing", required=True, installed=False, version=None, message="Not installed"),
        DependencyStatus(name="optional_missing", required=False, installed=False, version=None, message="Not installed"),
    ]
    failures = summarize_failures(statuses)
    assert failures == ["Missing required dependency: missing"]
