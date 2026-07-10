"""Tests for tools/system_resource_tool.py — local system resource snapshots."""

from tools import system_resource_tool


class TestResourceSnapshot:
    """resource_snapshot is pure local/read-only — always safe to call for real."""

    def test_resource_snapshot_returns_ok_with_expected_keys(self):
        # Act
        result = system_resource_tool.resource_snapshot()

        # Assert
        assert result["ok"] is True
        assert set(result.keys()) == {"ok", "disk", "load", "cpu_count", "memory", "uptime_s"}
        assert isinstance(result["disk"], dict)
        assert isinstance(result["load"], dict)
        assert isinstance(result["memory"], dict)

    def test_resource_snapshot_disk_has_percent_for_root(self):
        # Act
        result = system_resource_tool.resource_snapshot()

        # Assert
        assert result["disk"]["path"] == "/"
        assert isinstance(result["disk"]["percent"], float)
        assert 0 <= result["disk"]["percent"] <= 100

    def test_resource_snapshot_cpu_count_is_a_positive_int(self):
        # Act
        result = system_resource_tool.resource_snapshot()

        # Assert
        assert isinstance(result["cpu_count"], int)
        assert result["cpu_count"] > 0


class TestDiskUsage:
    """disk_usage wraps shutil.disk_usage with path validation."""

    def test_disk_usage_on_root_reports_real_numbers(self):
        # Act
        result = system_resource_tool.disk_usage("/")

        # Assert
        assert result["ok"] is True
        assert result["total"] > 0
        assert result["used"] >= 0
        assert result["free"] >= 0
        assert 0 <= result["percent"] <= 100

    def test_disk_usage_on_missing_path_is_an_error(self):
        # Act
        result = system_resource_tool.disk_usage("/no/such/path/should/exist")

        # Assert
        assert result["ok"] is False
        assert "no such path" in result["error"]


class TestCheckThresholds:
    """check_thresholds is pure logic — feed synthetic snapshots, no I/O."""

    def test_high_disk_usage_triggers_an_alert(self):
        # Arrange
        snapshot = {"disk": {"percent": 95}, "load": {"1m": None}}

        # Act
        result = system_resource_tool.check_thresholds(snapshot, disk_percent_max=90)

        # Assert
        assert result["ok"] is True
        assert len(result["alerts"]) == 1
        assert result["alerts"][0]["metric"] == "disk_percent"

    def test_low_disk_usage_triggers_no_alert(self):
        # Arrange
        snapshot = {"disk": {"percent": 50}, "load": {"1m": None}}

        # Act
        result = system_resource_tool.check_thresholds(snapshot, disk_percent_max=90)

        # Assert
        assert result["ok"] is True
        assert result["alerts"] == []

    def test_load_over_threshold_triggers_an_alert(self):
        # Arrange
        snapshot = {"disk": {"percent": 10}, "load": {"1m": 8.5}}

        # Act
        result = system_resource_tool.check_thresholds(snapshot, disk_percent_max=90, load1_max=4.0)

        # Assert
        assert result["ok"] is True
        assert len(result["alerts"]) == 1
        assert result["alerts"][0]["metric"] == "load1"

    def test_missing_load_metric_is_skipped_not_alerted(self):
        # Arrange
        snapshot = {"disk": {"percent": 10}, "load": {"1m": None}}

        # Act
        result = system_resource_tool.check_thresholds(snapshot, disk_percent_max=90, load1_max=4.0)

        # Assert
        assert result["alerts"] == []
