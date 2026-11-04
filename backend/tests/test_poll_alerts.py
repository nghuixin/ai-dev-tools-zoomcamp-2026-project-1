import importlib.util
import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "poll_alerts.py"
spec = importlib.util.spec_from_file_location("poll_alerts", SCRIPT)
poll_alerts = importlib.util.module_from_spec(spec)
sys.modules["poll_alerts"] = poll_alerts
spec.loader.exec_module(poll_alerts)

ALERT = {
    "state": "firing",
    "activeAt": "2026-11-03T10:00:00Z",
    "value": "0.5",
    "labels": {"alertname": "CreateIssue5xxRateHigh", "route": "POST /api/issues"},
    "annotations": {"summary": "Creating issues is failing"},
}


def test_alert_key_is_stable_and_changes_with_start_time():
    same = dict(ALERT, labels=dict(reversed(list(ALERT["labels"].items()))))
    assert poll_alerts.alert_key(ALERT) == poll_alerts.alert_key(same)
    assert poll_alerts.alert_key(ALERT) != poll_alerts.alert_key(dict(ALERT, activeAt="2026-11-03T11:00:00Z"))


def test_brief_includes_alert_logs_and_trace_ids():
    logs = [{"status": 500, "route": "/api/issues", "trace_id": "abc123"}]
    brief = poll_alerts.build_brief(ALERT, logs, "http://grafana:3000")
    assert "# Incident: CreateIssue5xxRateHigh" in brief
    assert "Creating issues is failing" in brief
    assert "`abc123`" in brief
    assert "Do not push, deploy" in brief


def test_new_alert_handled_once(tmp_path, monkeypatch):
    monkeypatch.setattr(poll_alerts, "firing_alerts", lambda _url: [ALERT])
    monkeypatch.setattr(poll_alerts, "recent_error_logs", lambda _url: [])
    calls = []
    monkeypatch.setattr(poll_alerts, "run_agent", lambda cmd, brief: calls.append(cmd) or "agent reply")
    args = poll_alerts.parse_args(["--once", "--state-dir", str(tmp_path), "--agent-cmd", "fake-agent"])
    seen: set[str] = set()

    assert poll_alerts.check_once(args, seen) == 1
    assert poll_alerts.check_once(args, seen) == 0
    assert calls == ["fake-agent"]
    assert len(list(tmp_path.glob("*-agent.md"))) == 1
    assert json.loads((tmp_path / "seen.json").read_text()) == [poll_alerts.alert_key(ALERT)]
