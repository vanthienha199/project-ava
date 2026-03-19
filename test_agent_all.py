"""Run the agent on all golden designs and report results."""
from src.llm import LLM
from src.agent import Agent
import os
import json

DESIGNS = [
    {
        "name": "01_adder",
        "dir": "golden/01_adder",
        "files": ["adder.v"],
        "toplevel": "adder",
    },
    {
        "name": "02_alu",
        "dir": "golden/02_alu",
        "files": ["alu.v"],
        "toplevel": "alu",
    },
    {
        "name": "03_icg",
        "dir": "golden/03_icg",
        "files": ["dff.v", "iiitb_icg.v"],
        "toplevel": "iiitb_icg",
    },
]

llm = LLM(backend="claude_cli")
agent = Agent(llm)
os.makedirs("runs", exist_ok=True)

results = []

for design in DESIGNS:
    spec = open(os.path.join(design["dir"], "spec.txt")).read()
    print(f"\n{'='*60}")
    print(f"Running: {design['name']}")
    print(f"{'='*60}")

    result = agent.run(
        design_dir=design["dir"],
        verilog_files=design["files"],
        toplevel=design["toplevel"],
        spec=spec,
    )

    status = "PASS" if result.passed else "FAIL"
    print(f"  Result: {status}")
    print(f"  Iterations: {result.iterations} (corrections: {result.corrections}, reboots: {result.reboots})")
    print(f"  Time: {result.total_latency_ms:.0f}ms")
    if result.sim_result:
        print(f"  Tests: {result.sim_result.pass_count}/{result.sim_result.total} passed")
        for t in result.sim_result.tests:
            print(f"    {t.status}  {t.name}")

    # Save individual run log
    log_path = f"runs/{design['name']}_run.json"
    with open(log_path, "w") as f:
        f.write(result.to_json())

    results.append({
        "design": design["name"],
        "passed": result.passed,
        "iterations": result.iterations,
        "corrections": result.corrections,
        "reboots": result.reboots,
        "time_ms": round(result.total_latency_ms),
        "tests_pass": result.sim_result.pass_count if result.sim_result else 0,
        "tests_total": result.sim_result.total if result.sim_result else 0,
    })

# Print summary table
print(f"\n{'='*60}")
print("SUMMARY")
print(f"{'='*60}")
print(f"{'Design':<15} {'Status':<8} {'Tests':<10} {'Iters':<8} {'Time':<10}")
print("-" * 51)
for r in results:
    status = "PASS" if r["passed"] else "FAIL"
    tests = f"{r['tests_pass']}/{r['tests_total']}"
    print(f"{r['design']:<15} {status:<8} {tests:<10} {r['iterations']:<8} {r['time_ms']}ms")

total_pass = sum(1 for r in results if r["passed"])
print(f"\nOverall: {total_pass}/{len(results)} designs passed")

# Save summary
with open("runs/summary.json", "w") as f:
    json.dump(results, f, indent=2)
print("Summary saved to runs/summary.json")
