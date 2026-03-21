#!/usr/bin/env python3
"""
Run mutation testing on all golden designs.
Outputs a summary table and saves detailed JSON reports.
"""
import json
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.mutation_runner import run_mutation_test, print_report


def main():
    golden_dir = Path("golden")
    runs_dir = Path("runs")
    os.makedirs("runs/mutations", exist_ok=True)

    designs = sorted(golden_dir.iterdir())
    all_reports = []

    for design_path in designs:
        if not design_path.is_dir():
            continue

        name = design_path.name
        tb_path = runs_dir / f"{name}_tb.py"

        if not tb_path.exists():
            print(f"SKIP {name}: no testbench at {tb_path}")
            continue

        # Read config
        config_file = design_path / "config.json"
        spec_file = design_path / "spec.txt"
        config = {}
        if config_file.exists():
            config = json.loads(config_file.read_text())

        verilog_files = config.get("files", [f.name for f in design_path.glob("*.v")])
        toplevel = config.get("toplevel", verilog_files[0].replace(".v", ""))

        testbench_code = tb_path.read_text()

        print(f"\n{'='*60}")
        print(f"  MUTATION TESTING: {name}")
        print(f"{'='*60}")

        report = run_mutation_test(
            design_dir=str(design_path),
            verilog_files=verilog_files,
            toplevel=toplevel,
            testbench_code=testbench_code,
        )

        print_report(report)

        # Save JSON
        report_path = f"runs/mutations/{name}_mutation.json"
        with open(report_path, "w") as f:
            json.dump(report.to_dict(), f, indent=2)

        all_reports.append(report)

    # Summary table
    print(f"\n\n{'='*70}")
    print(f"  MUTATION TESTING SUMMARY — ALL DESIGNS")
    print(f"{'='*70}")
    print(f"  {'Design':<25} {'Mutants':>8} {'Killed':>7} {'Survived':>9} {'Score':>7}")
    print(f"  {'-'*60}")

    total_mutants = 0
    total_killed = 0
    total_survived = 0
    total_errors = 0

    for r in all_reports:
        total_mutants += r.total_mutants
        total_killed += r.killed
        total_survived += r.survived
        total_errors += r.errors
        print(f"  {r.design_name:<25} {r.total_mutants:>8} {r.killed:>7} {r.survived:>9} {r.mutation_score:>6.1f}%")

    testable = total_mutants - total_errors
    overall_score = (total_killed / testable * 100) if testable > 0 else 0
    print(f"  {'-'*60}")
    print(f"  {'TOTAL':<25} {total_mutants:>8} {total_killed:>7} {total_survived:>9} {overall_score:>6.1f}%")

    # Save summary
    summary = {
        "total_designs": len(all_reports),
        "total_mutants": total_mutants,
        "total_killed": total_killed,
        "total_survived": total_survived,
        "total_errors": total_errors,
        "overall_mutation_score": round(overall_score, 1),
        "per_design": [r.to_dict() for r in all_reports],
    }
    with open("runs/mutations/summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n  Summary saved to runs/mutations/summary.json")


if __name__ == "__main__":
    main()
