#!/usr/bin/env python3
"""
Upload Project Ava golden designs and run results to Supabase.

Usage:
    python3 scripts/upload_results.py                      # upload everything
    python3 scripts/upload_results.py --designs-only       # only upload golden designs
    python3 scripts/upload_results.py --runs-only          # only upload run results
    python3 scripts/upload_results.py --backend ollama --model llama3:33b  # tag runs

Requires: setup_db.sql tables already created in Supabase.
No pip dependencies -- uses only urllib from the standard library.
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error

# ── Supabase config ─────────────────────────────────────────
SUPABASE_URL = "https://yvpmoyzggbcfaldhsbkl.supabase.co"
SUPABASE_ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl2cG1veXpnZ2JjZmFsZGhzYmtsIiwi"
    "cm9sZSI6ImFub24iLCJpYXQiOjE3NzM5Njg5OTMsImV4cCI6MjA4OTU0NDk5M30."
    "qgpE7ayn57SMzeJVgp7mBu3VJ825gTTe8G6OmfTc1b0"
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLDEN_DIR = os.path.join(PROJECT_ROOT, "golden")
RUNS_DIR = os.path.join(PROJECT_ROOT, "runs")

# Design name -> category mapping
CATEGORIES = {
    "01_adder":           "combinational",
    "02_alu":             "combinational",
    "03_icg":             "power-aware",
    "04_counter":         "sequential",
    "05_freq_divider":    "power-aware",
    "06_power_fsm":       "power-aware",
    "07_dvfs_controller": "power-aware",
    "08_shift_register":  "sequential",
    "09_fifo":            "buffer",
    "10_pwm":             "sequential",
    "11_uart_tx":         "protocol",
}


# ── HTTP helpers ─────────────────────────────────────────────

def supabase_request(table, data, method="POST", prefer="return=representation"):
    """POST/GET to Supabase REST API. Returns parsed JSON response."""
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    body = json.dumps(data).encode("utf-8")
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
        "Prefer": prefer,
    }
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw.strip() else []
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            if e.code == 409:  # Duplicate — already exists
                return []
            print(f"  ERROR {e.code}: {error_body}", file=sys.stderr)
            raise
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if attempt < 2:
                print(f"    Retry {attempt+1}/2 ({e})")
                import time; time.sleep(2)
            else:
                raise


def supabase_get(table, params=""):
    """GET from Supabase REST API."""
    url = f"{SUPABASE_URL}/rest/v1/{table}?{params}" if params else f"{SUPABASE_URL}/rest/v1/{table}"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ── Upload designs ───────────────────────────────────────────

def upload_designs():
    """Read golden/<name>/ directories and upload to designs table."""
    print("=" * 60)
    print("UPLOADING GOLDEN DESIGNS")
    print("=" * 60)

    # Get existing designs to avoid duplicates
    existing = supabase_get("designs", "select=name")
    existing_names = {d["name"] for d in existing}

    if not os.path.isdir(GOLDEN_DIR):
        print(f"  Golden directory not found: {GOLDEN_DIR}")
        return {}

    design_map = {}  # name -> uuid

    for entry in sorted(os.listdir(GOLDEN_DIR)):
        design_dir = os.path.join(GOLDEN_DIR, entry)
        if not os.path.isdir(design_dir):
            continue

        config_path = os.path.join(design_dir, "config.json")
        spec_path = os.path.join(design_dir, "spec.txt")

        if not os.path.exists(config_path):
            print(f"  SKIP {entry}: no config.json")
            continue

        with open(config_path) as f:
            config = json.load(f)

        spec = ""
        if os.path.exists(spec_path):
            with open(spec_path) as f:
                spec = f.read()

        # Read all Verilog files and concatenate
        verilog_parts = []
        files = config.get("files", [])
        for vf in files:
            vpath = os.path.join(design_dir, vf)
            if os.path.exists(vpath):
                with open(vpath) as f:
                    verilog_parts.append(f"// --- {vf} ---\n{f.read()}")
        verilog_source = "\n\n".join(verilog_parts)

        category = CATEGORIES.get(entry, "unknown")
        toplevel = config.get("toplevel", entry)

        if entry in existing_names:
            print(f"  SKIP {entry}: already exists")
            # Fetch its ID
            rows = supabase_get("designs", f"select=id&name=eq.{entry}")
            if rows:
                design_map[entry] = rows[0]["id"]
            continue

        print(f"  Uploading {entry} ({category}, toplevel={toplevel})...")

        row = {
            "name": entry,
            "category": category,
            "toplevel": toplevel,
            "verilog_source": verilog_source,
            "spec": spec,
            "files": files,
        }

        result = supabase_request("designs", row)
        if result and len(result) > 0:
            design_map[entry] = result[0]["id"]
            print(f"    -> id={result[0]['id']}")

    # Also fetch any previously existing IDs we didn't upload
    all_designs = supabase_get("designs", "select=id,name")
    for d in all_designs:
        design_map[d["name"]] = d["id"]

    print(f"\n  Total designs in DB: {len(design_map)}")
    return design_map


# ── Upload runs ──────────────────────────────────────────────

def upload_runs(design_map, backend="claude_cli", model="claude-cli"):
    """Read runs/*_run.json and upload runs + iterations + failures + test_results."""
    print("\n" + "=" * 60)
    print(f"UPLOADING RUNS (backend={backend}, model={model})")
    print("=" * 60)

    if not os.path.isdir(RUNS_DIR):
        print(f"  Runs directory not found: {RUNS_DIR}")
        return

    run_files = sorted(
        f for f in os.listdir(RUNS_DIR)
        if f.endswith("_run.json") and f[0].isdigit()
    )

    if not run_files:
        print("  No run files found (expected NN_name_run.json)")
        return

    for rf in run_files:
        # Derive design name: "01_adder_run.json" -> "01_adder"
        design_name = rf.replace("_run.json", "")
        run_path = os.path.join(RUNS_DIR, rf)

        print(f"\n  Processing {rf} -> design={design_name}")

        with open(run_path) as f:
            data = json.load(f)

        design_id = design_map.get(design_name)

        # Build run row
        tests = data.get("tests", {})
        run_row = {
            "design_name": design_name,
            "backend": backend,
            "model": model,
            "passed": data["passed"],
            "total_tests": tests.get("total", 0),
            "pass_count": tests.get("pass", 0),
            "fail_count": tests.get("fail", 0),
            "iterations": data.get("iterations", 0),
            "corrections": data.get("corrections", 0),
            "reboots": data.get("reboots", 0),
            "total_latency_ms": data.get("total_latency_ms"),
            "tokens_in": data.get("total_tokens_in", 0),
            "tokens_out": data.get("total_tokens_out", 0),
        }
        if design_id:
            run_row["design_id"] = design_id

        # Try to read the generated testbench
        tb_path = os.path.join(PROJECT_ROOT, "golden", design_name, "test_generated.py")
        if os.path.exists(tb_path):
            with open(tb_path) as f:
                run_row["testbench_code"] = f.read()

        result = supabase_request("runs", run_row)
        if not result or len(result) == 0:
            print(f"    FAILED to insert run")
            continue

        run_id = result[0]["id"]
        print(f"    run_id={run_id}")

        # Upload iterations from history
        history = data.get("history", [])
        for idx, h in enumerate(history):
            iter_row = {
                "run_id": run_id,
                "iteration_number": idx + 1,
                "iteration_type": h.get("type", "unknown"),
                "ic": h.get("ic", 0),
                "ir": h.get("ir", 0),
                "passed": h.get("passed", False),
                "pass_count": h.get("pass_count", 0),
                "fail_count": h.get("fail_count", 0),
                "llm_latency_ms": h.get("llm_latency_ms"),
                "sim_latency_ms": h.get("sim_latency_ms"),
            }
            iter_result = supabase_request("iterations", iter_row)
            if not iter_result or len(iter_result) == 0:
                print(f"    FAILED to insert iteration {idx + 1}")
                continue

            iter_id = iter_result[0]["id"]

            # Upload failures for this iteration
            for fail in h.get("failures", []):
                fail_row = {
                    "iteration_id": iter_id,
                    "run_id": run_id,
                    "category": fail.get("category", "unknown"),
                    "summary": fail.get("summary"),
                    "fixable": fail.get("fixable"),
                }
                supabase_request("failures", fail_row)

        print(f"    {len(history)} iterations uploaded")

        # Upload test_details
        test_details = data.get("test_details", [])
        for td in test_details:
            tr_row = {
                "run_id": run_id,
                "test_name": td.get("name", ""),
                "status": td.get("status", "UNKNOWN"),
                "sim_time_ns": td.get("sim_time_ns"),
            }
            supabase_request("test_results", tr_row)

        print(f"    {len(test_details)} test results uploaded")

    print("\n  Done uploading runs.")


# ── Main ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Upload Project Ava data to Supabase")
    parser.add_argument("--designs-only", action="store_true", help="Only upload golden designs")
    parser.add_argument("--runs-only", action="store_true", help="Only upload run results")
    parser.add_argument("--backend", default="claude_cli", help="Backend tag (default: claude_cli)")
    parser.add_argument("--model", default="claude-cli", help="Model tag (default: claude-cli)")
    args = parser.parse_args()

    # Default: upload both
    do_designs = not args.runs_only
    do_runs = not args.designs_only

    design_map = {}

    if do_designs:
        design_map = upload_designs()

    if do_runs:
        if not design_map:
            # Fetch existing design IDs from DB
            print("\nFetching existing designs from Supabase...")
            rows = supabase_get("designs", "select=id,name")
            design_map = {r["name"]: r["id"] for r in rows}
            print(f"  Found {len(design_map)} designs")

        upload_runs(design_map, backend=args.backend, model=args.model)

    print("\n" + "=" * 60)
    print("ALL DONE")
    print("=" * 60)


if __name__ == "__main__":
    main()
