"""End-to-end test: Run the full agent pipeline on the ICG clock gating design."""
from src.llm import LLM
from src.agent import Agent

llm = LLM(backend="claude_cli")
agent = Agent(llm)

print("Running agent on ICG clock gating design...")
print("=" * 60)

result = agent.run(
    design_dir="golden/03_icg",
    verilog_files=["dff.v", "iiitb_icg.v"],
    toplevel="iiitb_icg",
    spec=open("golden/03_icg/spec.txt").read(),
)

print(f"PASSED: {result.passed}")
print(f"Iterations: {result.iterations}")
print(f"Corrections: {result.corrections}")
print(f"Reboots: {result.reboots}")
print(f"Total time: {result.total_latency_ms:.0f}ms")
print()

if result.sim_result:
    for t in result.sim_result.tests:
        print(f"  {t.status}  {t.name}")

print()
print("History:")
for i, h in enumerate(result.history):
    status = "PASS" if (h.sim_result and h.sim_result.passed) else "FAIL"
    print(f"  [{i}] {h.iteration_type} (ic={h.ic}, ir={h.ir}) → {status}")

# Save run log
log_path = "runs/icg_run.json"
import os
os.makedirs("runs", exist_ok=True)
with open(log_path, "w") as f:
    f.write(result.to_json())
print(f"\nRun log saved to {log_path}")
