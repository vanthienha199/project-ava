"""Test agent on the two new power-aware designs: power FSM and DVFS controller."""
from src.llm import LLM
from src.agent import Agent
import os, json

DESIGNS = [
    {
        "name": "06_power_fsm",
        "dir": "golden/06_power_fsm",
        "files": ["power_fsm.v"],
        "toplevel": "power_fsm",
    },
    {
        "name": "07_dvfs_controller",
        "dir": "golden/07_dvfs_controller",
        "files": ["dvfs_controller.v"],
        "toplevel": "dvfs_controller",
    },
]

llm = LLM(backend="claude_cli")
agent = Agent(llm)
os.makedirs("runs", exist_ok=True)

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
        print(f"  Tests: {result.sim_result.pass_count}/{result.sim_result.total}")
        for t in result.sim_result.tests:
            print(f"    {t.status}  {t.name}")

    log_path = f"runs/{design['name']}_run.json"
    with open(log_path, "w") as f:
        f.write(result.to_json())
