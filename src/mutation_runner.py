"""
Mutation testing runner for Project Ava.
Takes a design + its generated testbench, creates mutants, and runs
the testbench against each mutant to measure test quality.

Usage:
    python3 -m src.mutation_runner --design-dir golden/01_adder --testbench runs/01_adder_tb.py
    python3 -m src.mutation_runner --design-dir golden/07_dvfs_controller

If no --testbench is specified, the agent generates one first.

Mutation Score = (Killed / (Total - CompileErrors)) * 100%
"""

import argparse
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

from .mutator import MutationEngine, MutationReport, MutationResult
from .simulator import Simulator


def run_mutation_test(design_dir: str, verilog_files: list, toplevel: str,
                      testbench_code: str, max_mutants: int = 0) -> MutationReport:
    """
    Run mutation testing on a design using an existing testbench.

    Args:
        design_dir: Directory containing original Verilog files
        verilog_files: List of Verilog filenames
        toplevel: Top-level module name
        testbench_code: The cocotb testbench Python source
        max_mutants: Max mutants to test (0 = all)

    Returns:
        MutationReport with kill/survive counts and details
    """
    design_path = Path(design_dir)
    engine = MutationEngine()
    simulator = Simulator()

    # Read all Verilog source
    verilog_source = ""
    for vf in verilog_files:
        verilog_source += (design_path / vf).read_text() + "\n"

    # Generate mutants
    mutants = engine.generate_mutants(verilog_source)
    if max_mutants > 0:
        mutants = mutants[:max_mutants]

    print(f"  Generated {len(mutants)} mutants")
    cat_summary = engine.summary(mutants)
    for cat, count in sorted(cat_summary.items()):
        print(f"    {cat}: {count}")

    # First: verify original design passes
    print(f"\n  Verifying original design passes...")
    orig_result = simulator.run(
        design_dir=str(design_path),
        verilog_files=verilog_files,
        toplevel=toplevel,
        test_module="test_generated",
        test_file_content=testbench_code,
    )
    if not orig_result.passed:
        print(f"  ERROR: Original design does not pass tests!")
        print(f"  Cannot run mutation testing on a failing testbench.")
        return MutationReport(
            design_name=design_path.name,
            total_mutants=len(mutants),
            killed=0, survived=0, errors=0,
            mutation_score=0.0,
            results=[],
            summary_by_category={},
        )

    orig_tests = orig_result.total
    print(f"  Original: PASS {orig_result.pass_count}/{orig_tests} tests")

    # Run each mutant
    results = []
    killed = 0
    survived = 0
    errors = 0

    for idx, mutant in enumerate(mutants):
        # Create temp dir with mutated Verilog
        with tempfile.TemporaryDirectory(prefix="ava_mut_") as tmpdir:
            # Write mutated Verilog
            for vf in verilog_files:
                # For single-file designs, replace the source
                # For multi-file, only mutate the first file (contains the logic)
                if vf == verilog_files[0]:
                    (Path(tmpdir) / vf).write_text(mutant.source)
                else:
                    shutil.copy(design_path / vf, Path(tmpdir) / vf)

            # Run tests against mutant
            try:
                sim_result = simulator.run(
                    design_dir=tmpdir,
                    verilog_files=verilog_files,
                    toplevel=toplevel,
                    test_module="test_generated",
                    test_file_content=testbench_code,
                )

                if sim_result.passed:
                    # Tests passed on mutant — mutation survived (bad)
                    survived += 1
                    result = MutationResult(
                        mutant=mutant, killed=False, survived=True,
                        tests_passed=sim_result.pass_count,
                        tests_total=sim_result.total,
                    )
                    status = "SURVIVED"
                else:
                    # Tests failed — mutation killed (good)
                    killed += 1
                    result = MutationResult(
                        mutant=mutant, killed=True, survived=False,
                        tests_passed=sim_result.pass_count,
                        tests_total=sim_result.total,
                    )
                    status = "KILLED"

            except Exception as e:
                # Compilation or runtime error — counts as killed
                errors += 1
                result = MutationResult(
                    mutant=mutant, killed=False, survived=False,
                    error=True, compile_error=True,
                    error_message=str(e),
                )
                status = "ERROR"

            results.append(result)

            # Progress output
            progress = f"[{idx+1}/{len(mutants)}]"
            print(f"  {progress} {status:>8} | {mutant.category:<22} | {mutant.description}")

    # Calculate mutation score
    # Compile errors are excluded from denominator (they're trivially detected)
    testable = len(mutants) - errors
    score = (killed / testable * 100) if testable > 0 else 0.0

    # Build category summary
    cat_results = {}
    for r in results:
        cat = r.mutant.category
        if cat not in cat_results:
            cat_results[cat] = {"total": 0, "killed": 0, "survived": 0, "errors": 0}
        cat_results[cat]["total"] += 1
        if r.killed:
            cat_results[cat]["killed"] += 1
        elif r.survived:
            cat_results[cat]["survived"] += 1
        elif r.error:
            cat_results[cat]["errors"] += 1

    report = MutationReport(
        design_name=design_path.name,
        total_mutants=len(mutants),
        killed=killed,
        survived=survived,
        errors=errors,
        mutation_score=score,
        results=results,
        summary_by_category=cat_results,
    )

    return report


def print_report(report: MutationReport):
    """Print a human-readable mutation testing report."""
    print(f"\n{'='*60}")
    print(f"  MUTATION TESTING REPORT: {report.design_name}")
    print(f"{'='*60}")
    print(f"  Total mutants:    {report.total_mutants}")
    print(f"  Killed:           {report.killed}")
    print(f"  Survived:         {report.survived}")
    print(f"  Compile errors:   {report.errors}")
    print(f"  MUTATION SCORE:   {report.mutation_score:.1f}%")
    print()

    # Category breakdown
    print(f"  {'Category':<25} {'Total':>6} {'Killed':>7} {'Survived':>9} {'Score':>7}")
    print(f"  {'-'*55}")
    for cat, stats in sorted(report.summary_by_category.items()):
        testable = stats["total"] - stats["errors"]
        cat_score = (stats["killed"] / testable * 100) if testable > 0 else 0
        print(f"  {cat:<25} {stats['total']:>6} {stats['killed']:>7} {stats['survived']:>9} {cat_score:>6.1f}%")

    # Surviving mutants (the gaps in test quality)
    survived_list = [r for r in report.results if r.survived]
    if survived_list:
        print(f"\n  SURVIVING MUTANTS (test gaps):")
        print(f"  {'-'*55}")
        for r in survived_list:
            print(f"  Line {r.mutant.line_num:>3}: {r.mutant.description}")
            print(f"         Original: {r.mutant.original}")
            print(f"         Mutated:  {r.mutant.mutated}")
            print()


def main():
    parser = argparse.ArgumentParser(description="Project Ava — Mutation Testing")
    parser.add_argument("--design-dir", required=True, help="Design directory")
    parser.add_argument("--testbench", help="Path to cocotb testbench file")
    parser.add_argument("--max-mutants", type=int, default=0, help="Max mutants (0=all)")
    parser.add_argument("--output", "-o", help="Save report as JSON")
    args = parser.parse_args()

    design_dir = Path(args.design_dir)
    config_file = design_dir / "config.json"
    config = json.loads(config_file.read_text()) if config_file.exists() else {}

    verilog_files = config.get("files", [f.name for f in design_dir.glob("*.v")])
    toplevel = config.get("toplevel", verilog_files[0].replace(".v", ""))

    # Get testbench code
    if args.testbench:
        testbench_code = Path(args.testbench).read_text()
    else:
        # Look for existing testbench in runs/
        run_log = Path(f"runs/{design_dir.name}_run.json")
        if run_log.exists():
            run_data = json.loads(run_log.read_text())
            # The testbench code is stored in the run result
            # For now, regenerate
            print(f"  No testbench specified. Use --testbench or generate one first.")
            print(f"  Run: python3 -m src run --design-dir {design_dir} --save-testbench tb.py")
            sys.exit(1)
        else:
            print(f"  No testbench found. Generate one first:")
            print(f"  python3 -m src run --design-dir {design_dir} --save-testbench runs/{design_dir.name}_tb.py")
            sys.exit(1)

    print(f"{'='*60}")
    print(f"  MUTATION TESTING: {design_dir.name}")
    print(f"  Files: {', '.join(verilog_files)}")
    print(f"  Toplevel: {toplevel}")
    print(f"{'='*60}")

    report = run_mutation_test(
        design_dir=str(design_dir),
        verilog_files=verilog_files,
        toplevel=toplevel,
        testbench_code=testbench_code,
        max_mutants=args.max_mutants,
    )

    print_report(report)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(report.to_dict(), f, indent=2)
        print(f"\n  Report saved to {args.output}")


if __name__ == "__main__":
    main()
