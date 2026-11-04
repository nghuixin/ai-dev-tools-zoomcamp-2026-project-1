#!/usr/bin/env python3
"""Poll Prometheus for firing alerts and hand each new one to a coding agent.

For every alert that starts firing, the poller:
  1. collects context: the alert's labels and annotations, recent error log lines
     from Loki (with their trace IDs), and links to Grafana;
  2. writes an incident brief to .alerts/<time>-<alertname>.md;
  3. if an agent command is configured, runs it with the brief on stdin and saves
     the agent's reply next to the brief (…-agent.md).

Each alert (name + labels + start time) is handled once; state lives in
.alerts/seen.json. Standard library only:

    python scripts/poll_alerts.py                     # loop, print briefs (dry run)
    python scripts/poll_alerts.py --once              # single check
    ALERT_AGENT_CMD="claude -p" python scripts/poll_alerts.py

Environment (flags override): PROMETHEUS_URL (http://127.0.0.1:9090),
LOKI_URL (http://127.0.0.1:3100), GRAFANA_URL (http://127.0.0.1:3000),
ALERT_AGENT_CMD (unset = dry run), ALERT_POLL_SECONDS (30).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_STATE_DIR = REPO_ROOT / ".alerts"
LOG_QUERY = '{service="api"} | json | status >= 500'


def http_json(url: str, timeout: float = 10.0) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def firing_alerts(prometheus_url: str) -> list[dict]:
    data = http_json(f"{prometheus_url.rstrip('/')}/api/v1/alerts")
    return [a for a in data.get("data", {}).get("alerts", []) if a.get("state") == "firing"]


def alert_key(alert: dict) -> str:
    """Stable ID for one firing episode: same labels + same start time."""
    labels = json.dumps(alert.get("labels", {}), sort_keys=True)
    raw = f"{labels}|{alert.get('activeAt', '')}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def recent_error_logs(loki_url: str, minutes: int = 15, limit: int = 20) -> list[dict]:
    """Recent 5xx request log lines from Loki, parsed from JSON. Empty if Loki is unreachable."""
    end = time.time_ns()
    params = urllib.parse.urlencode(
        {
            "query": LOG_QUERY,
            "start": end - minutes * 60 * 1_000_000_000,
            "end": end,
            "limit": limit,
            "direction": "backward",
        }
    )
    try:
        data = http_json(f"{loki_url.rstrip('/')}/loki/api/v1/query_range?{params}")
    except Exception as exc:  # noqa: BLE001 - context is best effort
        return [{"message": f"(could not query Loki: {exc})"}]
    lines: list[dict] = []
    for stream in data.get("data", {}).get("result", []):
        for _ts, line in stream.get("values", []):
            try:
                lines.append(json.loads(line))
            except json.JSONDecodeError:
                lines.append({"message": line})
    return lines[:limit]


def build_brief(alert: dict, logs: list[dict], grafana_url: str) -> str:
    labels = alert.get("labels", {})
    annotations = alert.get("annotations", {})
    name = labels.get("alertname", "unknown alert")
    trace_ids = sorted({line["trace_id"] for line in logs if line.get("trace_id")})
    explore = f"{grafana_url.rstrip('/')}/explore"

    out = [
        f"# Incident: {name}",
        "",
        "You are the on-call engineer for this repository (Site Issue Triage: FastAPI backend in",
        "`backend/`, React frontend in `frontend/`, contract in `openapi.yaml`, rules in `AGENTS.md`).",
        "A production alert is firing. Investigate it in this codebase:",
        "",
        "1. Explain the most likely cause, citing files and lines.",
        "2. Propose a minimal fix and a regression test (backend tests live in `backend/tests/`).",
        "3. If the failures are injected by `FAULT_CREATE_ISSUE_500_RATE`, say so; that is a demo, not a bug.",
        "Do not push, deploy or change infrastructure. Reply in Markdown.",
        "",
        "## Alert",
        "",
        f"- **Name:** {name}",
        f"- **Active since:** {alert.get('activeAt', 'unknown')}",
        f"- **Value:** {alert.get('value', 'unknown')}",
    ]
    for key in ("summary", "description", "runbook"):
        if annotations.get(key):
            out.append(f"- **{key.capitalize()}:** {annotations[key]}")
    out.append(f"- **Labels:** `{json.dumps(labels, sort_keys=True)}`")

    out += ["", f"## Recent 5xx log lines (Loki: `{LOG_QUERY}`)", ""]
    if logs:
        out += ["```json", *[json.dumps(line, sort_keys=True) for line in logs], "```"]
    else:
        out.append("No 5xx log lines found in the last 15 minutes.")

    out += ["", "## Trace IDs", ""]
    out += [f"- `{t}`" for t in trace_ids] or ["- none in the log sample"]
    out += ["", f"Grafana Explore: {explore} (Tempo for traces, Loki for logs)", ""]
    return "\n".join(out)


def run_agent(command: str, brief: str, timeout: int = 900) -> str:
    result = subprocess.run(
        shlex.split(command),
        input=brief,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=timeout,
    )
    output = result.stdout
    if result.returncode != 0:
        output += f"\n\n(agent exited with {result.returncode})\n{result.stderr}"
    return output


def load_seen(state_dir: Path) -> set[str]:
    path = state_dir / "seen.json"
    return set(json.loads(path.read_text())) if path.exists() else set()


def save_seen(state_dir: Path, seen: set[str]) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "seen.json").write_text(json.dumps(sorted(seen), indent=1))


def check_once(args: argparse.Namespace, seen: set[str]) -> int:
    try:
        alerts = firing_alerts(args.prometheus_url)
    except Exception as exc:  # noqa: BLE001
        print(f"[poll_alerts] Prometheus unreachable at {args.prometheus_url}: {exc}", file=sys.stderr)
        return 0
    handled = 0
    for alert in alerts:
        key = alert_key(alert)
        if key in seen:
            continue
        name = alert.get("labels", {}).get("alertname", "alert")
        brief = build_brief(alert, recent_error_logs(args.loki_url), args.grafana_url)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        args.state_dir.mkdir(parents=True, exist_ok=True)
        brief_path = args.state_dir / f"{stamp}-{name}.md"
        brief_path.write_text(brief, encoding="utf-8")
        print(f"[poll_alerts] firing: {name} -> {brief_path}")
        if args.agent_cmd:
            reply = run_agent(args.agent_cmd, brief)
            reply_path = brief_path.with_name(brief_path.stem + "-agent.md")
            reply_path.write_text(reply, encoding="utf-8")
            print(f"[poll_alerts] agent reply -> {reply_path}")
        else:
            print(brief)
        seen.add(key)
        save_seen(args.state_dir, seen)
        handled += 1
    return handled


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--prometheus-url", default=os.environ.get("PROMETHEUS_URL", "http://127.0.0.1:9090"))
    parser.add_argument("--loki-url", default=os.environ.get("LOKI_URL", "http://127.0.0.1:3100"))
    parser.add_argument("--grafana-url", default=os.environ.get("GRAFANA_URL", "http://127.0.0.1:3000"))
    parser.add_argument("--agent-cmd", default=os.environ.get("ALERT_AGENT_CMD"))
    parser.add_argument("--interval", type=int, default=int(os.environ.get("ALERT_POLL_SECONDS", "30")))
    parser.add_argument("--state-dir", type=Path, default=DEFAULT_STATE_DIR)
    parser.add_argument("--once", action="store_true", help="check once and exit")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    seen = load_seen(args.state_dir)
    mode = f"agent: {args.agent_cmd}" if args.agent_cmd else "dry run (set ALERT_AGENT_CMD)"
    print(f"[poll_alerts] watching {args.prometheus_url} every {args.interval}s; {mode}")
    while True:
        check_once(args, seen)
        if args.once:
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())
