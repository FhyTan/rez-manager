"""Tests for the log viewer controller."""

from __future__ import annotations


def test_log_viewer_controller_reads_tail_of_log_file(tmp_path, monkeypatch):
    from rez_manager.ui.log_viewer import LogViewerController

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True)
    log_path = log_dir / "rez-manager.log"
    log_path.write_text("\n".join(f"line {index}" for index in range(120)), encoding="utf-8")

    controller = LogViewerController()

    assert controller.logPath == str(log_path)
    assert controller.logUrl == log_path.as_uri()
    assert controller.isTruncated
    assert controller.tailLineCount == 100
    assert controller.logText.splitlines()[0] == "line 20"
    assert controller.logText.splitlines()[-1] == "line 119"
    assert controller.loadError == ""


def test_log_viewer_controller_reports_missing_log_file(tmp_path, monkeypatch):
    from rez_manager.ui.log_viewer import LogViewerController

    monkeypatch.setenv("REZ_MANAGER_HOME", str(tmp_path))

    controller = LogViewerController()

    assert controller.logUrl == (tmp_path / "logs" / "rez-manager.log").as_uri()
    assert controller.logText == ""
    assert (
        controller.loadError == f"Log file does not exist: {tmp_path / 'logs' / 'rez-manager.log'}"
    )
    assert not controller.hasContent
