"""
Agent watcher — polls Supabase for pending designs submitted via the Upload page.
Picks up new submissions, runs the verification agent, and updates results live.

Usage:
    source venv/bin/activate
    python3 -m src.watcher                          # watch with Claude CLI
    python3 -m src.watcher --backend anthropic_api   # watch with Anthropic API
    python3 -m src.watcher --once                    # process one pending design and exit

The watcher:
1. Polls Supabase every 5 seconds for runs with backend='pending'
2. Downloads the Verilog source + spec from the designs table
3. Writes temp files and runs the agent
4. Updates the run row with results (live reporter handles iteration updates)
"""

import argparse
import json
import os
import sys
import tempfile
import time
import urllib.request
import urllib.error
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.llm import LLM
from src.agent import Agent


SUPABASE_URL = "https://yvpmoyzggbcfaldhsbkl.supabase.co"
SUPABASE_ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl2cG1veXpnZ2JjZmFsZGhzYmtsIiwi"
    "cm9sZSI6ImFub24iLCJpYXQiOjE3NzM5Njg5OTMsImV4cCI6MjA4OTU0NDk5M30."
    "qgpE7ayn57SMzeJVgp7mBu3VJ825gTTe8G6OmfTc1b0"
)


def supabase_get(table, params=""):
    url = f"{SUPABASE_URL}/rest/v1/{table}?{params}" if params else f"{SUPABASE_URL}/rest/v1/{table}"
    headers = {"apikey": SUPABASE_ANON_KEY, "Authorization": f"Bearer {SUPABASE_ANON_KEY}"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def supabase_patch(table, row_id, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}?id=eq.{row_id}"
    body = json.dumps(data).encode("utf-8")
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    req = urllib.request.Request(url, data=body, headers=headers, method="PATCH")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def process_pending_run(run, llm_backend, llm_model):
    """Process a single pending run."""
    design_name = run["design_name"]
    design_id = run.get("design_id")
    run_id = run["id"]

    print(f"\n{'='*60}")
    print(f"  PICKED UP: {design_name} (run {run_id[:8]}...)")
    print(f"{'='*60}")

    # Mark as running
    supabase_patch("runs", run_id, {"backend": llm_backend, "model": llm_model or llm_backend})

    # Fetch design details
    if design_id:
        designs = supabase_get("designs", f"id=eq.{design_id}")
    else:
        designs = supabase_get("designs", f"name=eq.{design_name}")

    if not designs:
        print(f"  ERROR: Design not found in database")
        supabase_patch("runs", run_id, {
            "backend": llm_backend, "model": "error",
            "passed": False, "fail_count": 1,
        })
        return False

    design = designs[0]
    verilog_source = design.get("verilog_source", "")
    spec = design.get("spec", "")
    toplevel = design.get("toplevel", design_name)

    if not verilog_source or not spec:
        print(f"  ERROR: Missing Verilog source or spec")
        supabase_patch("runs", run_id, {
            "backend": llm_backend, "model": "error",
            "passed": False, "fail_count": 1,
        })
        return False

    # Create temp directory with Verilog file
    with tempfile.TemporaryDirectory(prefix=f"ava_{design_name}_") as tmpdir:
        verilog_file = f"{toplevel}.v"
        verilog_path = Path(tmpdir) / verilog_file
        verilog_path.write_text(verilog_source)

        # Also write spec for reference
        (Path(tmpdir) / "spec.txt").write_text(spec)

        print(f"  Design: {design_name}")
        print(f"  Toplevel: {toplevel}")
        print(f"  Verilog: {len(verilog_source)} chars")
        print(f"  Spec: {len(spec)} chars")
        print(f"  Backend: {llm_backend}")
        print(f"  Temp dir: {tmpdir}")
        print("-" * 50)

        # Run the agent
        llm = LLM(backend=llm_backend, model=llm_model)
        agent = Agent(llm, live_report=False)  # We handle reporting via the existing run_id

        try:
            result = agent.run(
                design_dir=tmpdir,
                verilog_files=[verilog_file],
                toplevel=toplevel,
                spec=spec,
            )

            # Update the run with results
            update = {
                "backend": llm_backend,
                "model": llm_model or llm_backend,
                "passed": result.passed,
                "total_tests": result.sim_result.total if result.sim_result else 0,
                "pass_count": result.sim_result.pass_count if result.sim_result else 0,
                "fail_count": result.sim_result.fail_count if result.sim_result else 0,
                "iterations": result.iterations,
                "corrections": result.corrections,
                "reboots": result.reboots,
                "total_latency_ms": result.total_latency_ms,
                "tokens_in": result.total_tokens_in,
                "tokens_out": result.total_tokens_out,
            }
            if result.testbench_code:
                update["testbench_code"] = result.testbench_code
            supabase_patch("runs", run_id, update)

            # Upload test results
            if result.sim_result:
                for t in result.sim_result.tests:
                    try:
                        body = json.dumps({
                            "run_id": run_id,
                            "test_name": t.name,
                            "status": t.status,
                            "sim_time_ns": t.sim_time_ns,
                        }).encode("utf-8")
                        req = urllib.request.Request(
                            f"{SUPABASE_URL}/rest/v1/test_results",
                            data=body,
                            headers={
                                "apikey": SUPABASE_ANON_KEY,
                                "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
                                "Content-Type": "application/json",
                                "Prefer": "return=representation",
                            },
                        )
                        urllib.request.urlopen(req, timeout=10)
                    except Exception as e:
                        print(f"  Warning: Failed to upload test result: {e}")

            status = "PASS" if result.passed else "FAIL"
            print(f"  Result: {status}")
            print(f"  Iterations: {result.iterations}")
            if result.sim_result:
                print(f"  Tests: {result.sim_result.pass_count}/{result.sim_result.total}")
            return result.passed

        except Exception as e:
            print(f"  AGENT ERROR: {e}")
            supabase_patch("runs", run_id, {
                "backend": llm_backend, "model": llm_model or "error",
                "passed": False, "fail_count": 1,
            })
            return False


def watch(backend="claude_cli", model=None, once=False, poll_interval=5):
    """Main watch loop — polls for pending runs."""
    print("=" * 60)
    print("  PROJECT AVA — Agent Watcher")
    print(f"  Backend: {backend}")
    print(f"  Poll interval: {poll_interval}s")
    print(f"  Mode: {'single run' if once else 'continuous'}")
    print("=" * 60)
    print("\n  Watching for pending designs...\n")

    while True:
        try:
            # Find runs with backend='pending'
            pending = supabase_get("runs", "backend=eq.pending&order=created_at.asc&limit=1")

            if pending:
                run = pending[0]
                process_pending_run(run, backend, model)
                if once:
                    break
            else:
                if once:
                    print("  No pending designs found.")
                    break

        except KeyboardInterrupt:
            print("\n\n  Watcher stopped.")
            break
        except Exception as e:
            print(f"  Poll error: {e}")

        if not once:
            time.sleep(poll_interval)


def main():
    parser = argparse.ArgumentParser(description="Project Ava — Agent Watcher")
    parser.add_argument("--backend", default="claude_cli",
                        choices=["claude_cli", "anthropic_api", "ollama"])
    parser.add_argument("--model", default=None)
    parser.add_argument("--once", action="store_true", help="Process one pending design and exit")
    parser.add_argument("--poll-interval", type=int, default=5, help="Poll interval in seconds")
    args = parser.parse_args()

    watch(backend=args.backend, model=args.model, once=args.once, poll_interval=args.poll_interval)


if __name__ == "__main__":
    main()
