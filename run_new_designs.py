"""Run agent on just the 3 new designs (08-10) to get their JSON logs."""
from src.llm import LLM
from src.agent import Agent
import os, json

DESIGNS = [
    {"name": "08_shift_register", "dir": "golden/08_shift_register", "files": ["shift_register.v"], "toplevel": "shift_register"},
    {"name": "09_fifo", "dir": "golden/09_fifo", "files": ["fifo.v"], "toplevel": "fifo"},
    {"name": "10_pwm", "dir": "golden/10_pwm", "files": ["pwm.v"], "toplevel": "pwm"},
]

llm = LLM(backend="anthropic_api")
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
