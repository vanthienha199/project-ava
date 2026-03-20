"""
Live status reporter for Project Ava.
Pushes agent status updates to Supabase during execution so the
Live page can show real-time progress.

Usage:
    reporter = LiveReporter()  # auto-detects Supabase config
    run_id = reporter.start_run("07_dvfs_controller", "claude_cli")
    reporter.update_iteration(run_id, 2, "correct", passed=False, pass_count=8, fail_count=3)
    reporter.complete_run(run_id, passed=True, total_tests=11, pass_count=11, ...)

Set SUPABASE_LIVE=0 to disable (no-op).
"""

import json
import os
import urllib.request
import urllib.error


SUPABASE_URL = "https://yvpmoyzggbcfaldhsbkl.supabase.co"
SUPABASE_ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl2cG1veXpnZ2JjZmFsZGhzYmtsIiwi"
    "cm9sZSI6ImFub24iLCJpYXQiOjE3NzM5Njg5OTMsImV4cCI6MjA4OTU0NDk5M30."
    "qgpE7ayn57SMzeJVgp7mBu3VJ825gTTe8G6OmfTc1b0"
)


class LiveReporter:
    """Pushes live agent status to Supabase for the web dashboard."""

    def __init__(self, enabled=None):
        if enabled is None:
            enabled = os.environ.get("SUPABASE_LIVE", "1") != "0"
        self.enabled = enabled

    def _post(self, table, data, method="POST"):
        """POST/PATCH to Supabase REST API. Returns parsed JSON or None on failure."""
        if not self.enabled:
            return None
        url = f"{SUPABASE_URL}/rest/v1/{table}"
        body = json.dumps(data).encode("utf-8")
        headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw.strip() else []
        except Exception as e:
            # Never crash the agent for a reporting failure
            print(f"  [reporter] {method} {table} failed: {e}")
            return None

    def _patch(self, table, row_id, data):
        """PATCH a specific row by ID."""
        if not self.enabled:
            return None
        url = f"{SUPABASE_URL}/rest/v1/{table}?id=eq.{row_id}"
        body = json.dumps(data).encode("utf-8")
        headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }
        req = urllib.request.Request(url, data=body, headers=headers, method="PATCH")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw.strip() else []
        except Exception as e:
            print(f"  [reporter] PATCH {table}/{row_id} failed: {e}")
            return None

    def start_run(self, design_name, backend="claude_cli", model="claude-cli", design_id=None):
        """Insert a 'running' row into runs table. Returns run_id or None."""
        row = {
            "design_name": design_name,
            "backend": backend,
            "model": model,
            "passed": False,
            "total_tests": 0,
            "pass_count": 0,
            "fail_count": 0,
            "iterations": 0,
            "corrections": 0,
            "reboots": 0,
        }
        if design_id:
            row["design_id"] = design_id
        result = self._post("runs", row)
        if result and len(result) > 0:
            run_id = result[0].get("id")
            print(f"  [reporter] Live run started: {run_id}")
            return run_id
        return None

    def update_iteration(self, run_id, iteration_num, iteration_type,
                         passed=False, pass_count=0, fail_count=0,
                         corrections=0, reboots=0):
        """Update the run row with current iteration progress."""
        if not run_id:
            return
        self._patch("runs", run_id, {
            "iterations": iteration_num,
            "corrections": corrections,
            "reboots": reboots,
            "pass_count": pass_count,
            "fail_count": fail_count,
        })

    def complete_run(self, run_id, passed, total_tests, pass_count, fail_count,
                     iterations, corrections, reboots, total_latency_ms=None,
                     tokens_in=0, tokens_out=0, testbench_code=None):
        """Mark the run as completed with final results."""
        if not run_id:
            return
        data = {
            "passed": passed,
            "total_tests": total_tests,
            "pass_count": pass_count,
            "fail_count": fail_count,
            "iterations": iterations,
            "corrections": corrections,
            "reboots": reboots,
            "total_latency_ms": total_latency_ms,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
        }
        if testbench_code:
            data["testbench_code"] = testbench_code
        self._patch("runs", run_id, data)
        print(f"  [reporter] Run completed: {'PASS' if passed else 'FAIL'}")

    def report_test_result(self, run_id, test_name, status, sim_time_ns=None):
        """Insert an individual test result."""
        if not run_id:
            return
        self._post("test_results", {
            "run_id": run_id,
            "test_name": test_name,
            "status": status,
            "sim_time_ns": sim_time_ns,
        })
