"""Quick test: verify Simulator module works against the proven ICG testbench."""
from src.simulator import Simulator

sim = Simulator()
result = sim.run(
    design_dir="research/icg_test",
    verilog_files=["dff.v", "iiitb_icg.v"],
    toplevel="iiitb_icg",
    test_module="test_icg",
    test_file_content=open("research/icg_test/test_icg.py").read(),
)

print(f"Passed: {result.passed}")
print(f"Total: {result.total}  Pass: {result.pass_count}  Fail: {result.fail_count}")
print(f"Latency: {result.latency_ms:.0f}ms")
print()
for t in result.tests:
    print(f"  {t.status}  {t.name}  ({t.sim_time_ns}ns)")
if result.errors:
    print(f"\nErrors: {result.errors}")
