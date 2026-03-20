"""
CLI entry point for Project Ava.

Usage:
    python3 -m src --design path/to/design.v --spec "description" --toplevel module_name
    python3 -m src --design-dir golden/03_icg --spec-file golden/03_icg/spec.txt
    python3 -m src --benchmark                # Run all golden designs
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

from .llm import LLM
from .agent import Agent


def run_single(args):
    """Run agent on a single design."""
    llm = LLM(backend=args.backend, model=args.model, base_url=getattr(args, 'ollama_url', None))
    agent = Agent(llm, prompt_version=args.prompt_version)

    # Resolve design files
    if args.design_dir:
        design_dir = Path(args.design_dir)
        verilog_files = [f.name for f in design_dir.glob("*.v")]
        spec_file = design_dir / "spec.txt"
        config_file = design_dir / "config.json"
        config = json.loads(config_file.read_text()) if config_file.exists() else {}
        if spec_file.exists():
            spec = spec_file.read_text()
        elif config.get("spec"):
            spec = config["spec"]
        else:
            spec = args.spec
        toplevel = args.toplevel or config.get("toplevel") or verilog_files[0].replace(".v", "")
        verilog_files = config.get("files", verilog_files)
    else:
        design_dir = Path(args.design).parent
        verilog_files = [Path(args.design).name]
        spec = args.spec
        toplevel = args.toplevel or verilog_files[0].replace(".v", "")

    if not spec:
        print("Error: --spec or --spec-file required", file=sys.stderr)
        sys.exit(1)

    print(f"Design: {toplevel}")
    print(f"Files: {', '.join(verilog_files)}")
    print(f"Backend: {llm}")
    print("-" * 50)

    result = agent.run(
        design_dir=str(design_dir),
        verilog_files=verilog_files,
        toplevel=toplevel,
        spec=spec,
    )

    _print_result(toplevel, result)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w") as f:
            f.write(result.to_json())
        print(f"\nRun log: {args.output}")

    if args.save_testbench and result.testbench_code:
        with open(args.save_testbench, "w") as f:
            f.write(result.testbench_code)
        print(f"Testbench saved: {args.save_testbench}")

    return result.passed


def run_benchmark(args):
    """Run agent on all golden designs."""
    golden_dir = Path("golden")
    if not golden_dir.exists():
        print("Error: golden/ directory not found", file=sys.stderr)
        sys.exit(1)

    llm = LLM(backend=args.backend, model=args.model, base_url=getattr(args, 'ollama_url', None))
    agent = Agent(llm, prompt_version=args.prompt_version)
    os.makedirs("runs", exist_ok=True)

    designs = sorted(golden_dir.iterdir())
    results = []

    for design_path in designs:
        if not design_path.is_dir():
            continue

        verilog_files = [f.name for f in design_path.glob("*.v")]
        if not verilog_files:
            continue

        # Read config and spec
        config_file = design_path / "config.json"
        spec_file = design_path / "spec.txt"
        config = {}
        if config_file.exists():
            config = json.loads(config_file.read_text())

        if spec_file.exists():
            spec = spec_file.read_text()
        elif config.get("spec"):
            spec = config["spec"]
        else:
            continue

        toplevel = config.get("toplevel", verilog_files[0].replace(".v", ""))
        verilog_files = config.get("files", verilog_files)

        print(f"\n{'='*60}")
        print(f"Running: {design_path.name}")
        print(f"{'='*60}")

        result = agent.run(
            design_dir=str(design_path),
            verilog_files=verilog_files,
            toplevel=toplevel,
            spec=spec,
        )

        _print_result(design_path.name, result)

        # Save run log
        log_path = f"runs/{design_path.name}_run.json"
        with open(log_path, "w") as f:
            f.write(result.to_json())

        results.append({
            "design": design_path.name,
            "passed": result.passed,
            "iterations": result.iterations,
            "corrections": result.corrections,
            "reboots": result.reboots,
            "time_ms": round(result.total_latency_ms),
            "tests_pass": result.sim_result.pass_count if result.sim_result else 0,
            "tests_total": result.sim_result.total if result.sim_result else 0,
        })

    # Summary
    print(f"\n{'='*60}")
    print("BENCHMARK SUMMARY")
    print(f"{'='*60}")
    print(f"{'Design':<20} {'Status':<8} {'Tests':<10} {'Iters':<8} {'Time':<10}")
    print("-" * 56)
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        tests = f"{r['tests_pass']}/{r['tests_total']}"
        print(f"{r['design']:<20} {status:<8} {tests:<10} {r['iterations']:<8} {r['time_ms']}ms")

    total_pass = sum(1 for r in results if r["passed"])
    total_tests_pass = sum(r["tests_pass"] for r in results)
    total_tests = sum(r["tests_total"] for r in results)
    print(f"\nDesigns: {total_pass}/{len(results)} passed")
    print(f"Tests: {total_tests_pass}/{total_tests} passed")

    with open("runs/benchmark.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Benchmark saved to runs/benchmark.json")

    return all(r["passed"] for r in results)


def _print_result(name, result):
    """Print a single run result."""
    status = "PASS" if result.passed else "FAIL"
    print(f"  Result: {status}")
    print(f"  Iterations: {result.iterations} (corrections: {result.corrections}, reboots: {result.reboots})")
    print(f"  Time: {result.total_latency_ms:.0f}ms")
    if result.sim_result:
        print(f"  Tests: {result.sim_result.pass_count}/{result.sim_result.total}")
        for t in result.sim_result.tests:
            print(f"    {t.status}  {t.name}")


def main():
    parser = argparse.ArgumentParser(
        prog="ava",
        description="Project Ava — Agentic Hardware Verification",
    )
    subparsers = parser.add_subparsers(dest="command")

    # Single design
    run_parser = subparsers.add_parser("run", help="Run agent on a single design")
    run_parser.add_argument("--design", help="Path to Verilog file")
    run_parser.add_argument("--design-dir", help="Directory with Verilog files + spec.txt")
    run_parser.add_argument("--spec", help="Natural language specification")
    run_parser.add_argument("--toplevel", help="Top-level module name")
    run_parser.add_argument("--output", "-o", help="Save run log to JSON file")
    run_parser.add_argument("--save-testbench", help="Save generated testbench to file")
    run_parser.add_argument("--backend", default="claude_cli",
                            choices=["claude_cli", "anthropic_api", "ollama"])
    run_parser.add_argument("--model", default=None, help="LLM model override")
    run_parser.add_argument("--ollama-url", default=None, help="Ollama API URL (e.g. http://localhost:11435)")
    run_parser.add_argument("--prompt-version", default="v1")

    # Benchmark
    bench_parser = subparsers.add_parser("benchmark", help="Run on all golden designs")
    bench_parser.add_argument("--backend", default="claude_cli",
                              choices=["claude_cli", "anthropic_api", "ollama"])
    bench_parser.add_argument("--model", default=None)
    bench_parser.add_argument("--ollama-url", default=None, help="Ollama API URL")
    bench_parser.add_argument("--prompt-version", default="v1")

    args = parser.parse_args()

    if args.command == "run":
        success = run_single(args)
    elif args.command == "benchmark":
        success = run_benchmark(args)
    else:
        parser.print_help()
        sys.exit(1)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
