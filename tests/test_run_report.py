"""Tests for pipeline.run_report — RunReport tracking and saving."""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from pipeline.run_report import RunReport, StageEntry, time_stage


class TestStageEntry:
    """StageEntry dataclass."""

    def test_defaults(self):
        entry = StageEntry(name="test_stage")
        assert entry.name == "test_stage"
        assert entry.status == "running"
        assert entry.duration_s == 0.0
        assert entry.error is None

    def test_set_values(self):
        entry = StageEntry(name="s1", status="ok", duration_s=1.5, error=None)
        assert entry.name == "s1"
        assert entry.status == "ok"
        assert entry.duration_s == 1.5


class TestRunReport:
    """RunReport: track pipeline execution."""

    def test_defaults(self):
        report = RunReport()
        assert report.dry_run is False
        assert report.stages == []
        assert report.slug == ""
        assert report.author == ""
        assert report.image_generated is False
        assert report.msg_id is None
        assert report.failed_stage is None
        assert report.error is None
        assert report.status == "running"

    def test_begin(self):
        report = RunReport()
        report.begin()
        assert report.start_time > 0

    def test_finish(self):
        report = RunReport()
        report.begin()
        report.finish("ok")
        assert report.status == "ok"
        assert report.end_time > 0
        assert report.end_time >= report.start_time

    def test_add_stage(self):
        report = RunReport()
        entry = report.add_stage("test_stage")
        assert isinstance(entry, StageEntry)
        assert entry.name == "test_stage"
        assert len(report.stages) == 1

    def test_multiple_stages(self):
        report = RunReport()
        report.add_stage("s1")
        report.add_stage("s2")
        report.add_stage("s3")
        assert len(report.stages) == 3
        assert report.stages[0].name == "s1"
        assert report.stages[2].name == "s3"

    @patch("pipeline.run_report.STATE_DIR")
    def test_save(self, mock_state_dir, tmp_path):
        mock_state_dir.__truediv__ = lambda self, x: tmp_path / x

        report = RunReport()
        report.begin()
        report.slug = "test-slug"
        report.author = "Test Author"
        report.add_stage("s1")
        report.stages[0].status = "ok"
        report.stages[0].duration_s = 1.5
        report.finish("ok")

        path = report.save()
        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["status"] == "ok"
        assert data["slug"] == "test-slug"
        assert data["author"] == "Test Author"
        assert len(data["stages"]) == 1
        assert data["stages"][0]["name"] == "s1"
        assert data["stages"][0]["status"] == "ok"
        assert data["duration_s"] >= 0

    @patch("pipeline.run_report.STATE_DIR")
    def test_save_creates_runs_dir(self, mock_state_dir, tmp_path):
        mock_state_dir.__truediv__ = lambda self, x: tmp_path / x

        report = RunReport()
        report.begin()
        report.finish("ok")
        path = report.save()
        assert (tmp_path / "runs").is_dir()

    def test_dry_run_flag(self):
        report = RunReport(dry_run=True)
        assert report.dry_run is True


class TestTimeStage:
    """time_stage: context manager for tracking stage execution."""

    def test_successful_stage(self):
        report = RunReport()
        with time_stage(report, "test_stage") as entry:
            pass  # Simulating work
        assert entry.status == "ok"
        assert entry.duration_s >= 0
        assert entry.error is None
        assert len(report.stages) == 1

    def test_failed_stage(self):
        report = RunReport()
        with pytest.raises(ValueError, match="test error"):
            with time_stage(report, "fail_stage") as entry:
                raise ValueError("test error")
        assert entry.status == "failed"
        assert entry.error == "test error"
        assert entry.duration_s >= 0

    def test_error_truncated(self):
        report = RunReport()
        long_error = "x" * 500
        with pytest.raises(ValueError):
            with time_stage(report, "long_error_stage") as entry:
                raise ValueError(long_error)
        assert len(entry.error) <= 200

    def test_duration_measured(self):
        report = RunReport()
        with time_stage(report, "slow_stage") as entry:
            time.sleep(0.05)
        assert entry.duration_s >= 0.04  # Allow small timing variance

    def test_multiple_stages_tracked(self):
        report = RunReport()
        with time_stage(report, "s1"):
            pass
        with time_stage(report, "s2"):
            pass
        assert len(report.stages) == 2
        assert report.stages[0].name == "s1"
        assert report.stages[1].name == "s2"
