"""
Simulator module for Project Ava.
Runs cocotb testbenches via Icarus Verilog and parses the results.

Usage:
    sim = Simulator()
    result = sim.run(
        design_dir="/path/to/design",
        verilog_files=["dff.v", "iiitb_icg.v"],
        toplevel="iiitb_icg",
        test_module="test_icg",
    )
    # Returns: SimResult with pass/fail, test details, errors
"""

import os
import re
import subprocess
import tempfile
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TestResult:
    name: str
    status: str  # "PASS" or "FAIL"
    sim_time_ns: float = 0.0
    real_time_s: float = 0.0
    error_message: str = ""


@dataclass
class SimResult:
    passed: bool
    total: int = 0
    pass_count: int = 0
    fail_count: int = 0
    tests: list = field(default_factory=list)
    raw_output: str = ""
    errors: list = field(default_factory=list)
    latency_ms: float = 0.0
    vcd_path: str = ""

    @property
    def fail_messages(self) -> list:
        """Extract error messages from failed tests."""
        return [t.error_message for t in self.tests if t.status == "FAIL" and t.error_message]


class Simulator:
    def __init__(self, sim="icarus"):
        self.sim = sim

    def run(self, design_dir, verilog_files, toplevel, test_module,
            test_file_content=None, dump_vcd=False) -> SimResult:
        """
        Run a cocotb simulation.

        Args:
            design_dir: Directory containing Verilog source files
            verilog_files: List of Verilog filenames (relative to design_dir)
            toplevel: Top-level Verilog module name
            test_module: Python test module name (without .py)
            test_file_content: If provided, write this as the test module .py file

        Returns:
            SimResult with pass/fail status and parsed test details
        """
        design_dir = Path(design_dir)

        # Create a temp working directory for this run
        work_dir = Path(tempfile.mkdtemp(prefix="ava_sim_"))

        try:
            # Copy Verilog source files
            for vf in verilog_files:
                src = design_dir / vf
                if not src.exists():
                    return SimResult(
                        passed=False,
                        errors=[f"Verilog file not found: {src}"],
                        raw_output="",
                    )
                shutil.copy2(src, work_dir / vf)

            # Write test module if content provided
            if test_file_content is not None:
                (work_dir / f"{test_module}.py").write_text(test_file_content)

            # Write Makefile
            verilog_sources = " ".join(
                f"$(shell pwd)/{vf}" for vf in verilog_files
            )

            # VCD dump support
            if dump_vcd:
                vcd_wrapper = (
                    f"`timescale 1ns/1ps\n"
                    f"module vcd_dump;\n"
                    f"  initial begin\n"
                    f'    $dumpfile("dump.vcd");\n'
                    f"    $dumpvars(0);\n"
                    f"  end\n"
                    f"endmodule\n"
                )
                (work_dir / "vcd_dump.v").write_text(vcd_wrapper)
                verilog_sources += " $(shell pwd)/vcd_dump.v"

            makefile = (
                f"TOPLEVEL_LANG = verilog\n"
                f"VERILOG_SOURCES = {verilog_sources}\n"
                f"TOPLEVEL = {toplevel}\n"
                f"MODULE = {test_module}\n"
                f"SIM = {self.sim}\n"
                f"\ninclude $(shell cocotb-config --makefiles)/Makefile.sim\n"
            )
            (work_dir / "Makefile").write_text(makefile)

            # Run simulation
            start = time.monotonic()
            env = os.environ.copy()
            if dump_vcd:
                env["COMPILE_ARGS"] = "-s vcd_dump"
            result = subprocess.run(
                ["make", f"SIM={self.sim}"],
                capture_output=True,
                text=True,
                cwd=str(work_dir),
                timeout=120,
                env=env,
            )
            latency = (time.monotonic() - start) * 1000

            output = result.stdout + "\n" + result.stderr

            # Parse results
            sim_result = self._parse_output(output, latency)

            # Copy VCD file out if it was generated
            if dump_vcd:
                vcd_file = work_dir / "dump.vcd"
                if vcd_file.exists():
                    dest = Path(design_dir) / "dump.vcd"
                    shutil.copy2(vcd_file, dest)
                    sim_result.vcd_path = str(dest)

            return sim_result

        except subprocess.TimeoutExpired:
            return SimResult(
                passed=False,
                errors=["Simulation timed out (120s)"],
                raw_output="TIMEOUT",
            )
        except Exception as e:
            return SimResult(
                passed=False,
                errors=[str(e)],
                raw_output="",
            )
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

    def _parse_output(self, output: str, latency_ms: float) -> SimResult:
        """Parse cocotb simulation output into structured results."""
        tests = []
        errors = []

        # Parse individual test results
        # Format: ** test_module.test_name   PASS/FAIL   sim_time   real_time   ratio **
        test_pattern = re.compile(
            r"\*\*\s+(\S+)\s+(PASS|FAIL)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+\*\*"
        )
        for match in test_pattern.finditer(output):
            name = match.group(1)
            status = match.group(2)
            sim_time = float(match.group(3))
            real_time = float(match.group(4))
            tests.append(TestResult(
                name=name,
                status=status,
                sim_time_ns=sim_time,
                real_time_s=real_time,
            ))

        # Parse summary line: ** TESTS=5 PASS=5 FAIL=0 SKIP=0 **
        summary_pattern = re.compile(
            r"TESTS=(\d+)\s+PASS=(\d+)\s+FAIL=(\d+)"
        )
        summary_match = summary_pattern.search(output)

        total = int(summary_match.group(1)) if summary_match else len(tests)
        pass_count = int(summary_match.group(2)) if summary_match else sum(
            1 for t in tests if t.status == "PASS"
        )
        fail_count = int(summary_match.group(3)) if summary_match else sum(
            1 for t in tests if t.status == "FAIL"
        )

        # Extract error messages for failed tests
        # cocotb prints tracebacks with "Traceback" and "Error" / "Assert"
        error_blocks = re.findall(
            r"(Traceback.*?(?:Error|assert).*?)(?:\n\s*\d+\.\d+ns|\n\*\*)",
            output,
            re.DOTALL | re.IGNORECASE,
        )
        for i, err in enumerate(error_blocks):
            if i < len(tests) and tests[i].status == "FAIL":
                tests[i].error_message = err.strip()
            errors.append(err.strip())

        # Also catch single-line assertion errors
        assertion_errors = re.findall(
            r"(AssertionError:.*|AttributeError:.*|TypeError:.*|ValueError:.*)",
            output,
        )
        for ae in assertion_errors:
            if ae.strip() not in errors:
                errors.append(ae.strip())

        return SimResult(
            passed=(fail_count == 0 and total > 0),
            total=total,
            pass_count=pass_count,
            fail_count=fail_count,
            tests=tests,
            raw_output=output,
            errors=errors,
            latency_ms=latency_ms,
        )
