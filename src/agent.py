"""
Agent orchestrator for Project Ava.
The full pipeline: Verilog DUT + spec → generate → simulate → self-correct → result.

Implements the CorrectBench two-tier iteration strategy:
  - Correction: feed errors back to LLM, fix testbench (max IC_MAX attempts)
  - Reboot: regenerate from scratch (max IR_MAX attempts)

Usage:
    from src.llm import LLM
    from src.agent import Agent

    llm = LLM(backend="claude_cli")
    agent = Agent(llm)
    result = agent.run(
        design_dir="golden/02_alu",
        verilog_files=["alu.v"],
        toplevel="alu",
        spec="8-bit ALU with add, sub, and, or, xor operations and zero flag",
    )
    print(result.passed, result.iterations)
"""

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path

from .llm import LLM
from .generator import Generator, GenResult
from .corrector import Corrector
from .simulator import Simulator, SimResult
from .analyzer import analyze_failure, FailureAnalysis


IC_MAX = 3   # Max correction attempts before reboot
IR_MAX = 10  # Max reboot attempts before giving up


@dataclass
class Iteration:
    iteration_type: str  # "generate", "correct", or "reboot"
    ic: int  # correction counter
    ir: int  # reboot counter
    gen_result: GenResult = None
    sim_result: SimResult = None
    failures: list = field(default_factory=list)  # list of FailureAnalysis


@dataclass
class AgentResult:
    passed: bool
    testbench_code: str = ""
    iterations: int = 0
    corrections: int = 0
    reboots: int = 0
    history: list = field(default_factory=list)
    total_latency_ms: float = 0.0
    total_tokens_in: int = 0
    total_tokens_out: int = 0
    sim_result: SimResult = None

    def to_json(self) -> str:
        """Serialize to JSON for logging."""
        d = {
            "passed": self.passed,
            "iterations": self.iterations,
            "corrections": self.corrections,
            "reboots": self.reboots,
            "total_latency_ms": self.total_latency_ms,
            "total_tokens_in": self.total_tokens_in,
            "total_tokens_out": self.total_tokens_out,
        }
        if self.sim_result:
            d["tests"] = {
                "total": self.sim_result.total,
                "pass": self.sim_result.pass_count,
                "fail": self.sim_result.fail_count,
            }
            d["test_details"] = [
                {"name": t.name, "status": t.status, "sim_time_ns": t.sim_time_ns}
                for t in self.sim_result.tests
            ]
        d["history"] = [
            {
                "type": it.iteration_type,
                "ic": it.ic,
                "ir": it.ir,
                "passed": it.sim_result.passed if it.sim_result else None,
                "pass_count": it.sim_result.pass_count if it.sim_result else None,
                "fail_count": it.sim_result.fail_count if it.sim_result else None,
                "llm_latency_ms": it.gen_result.llm_response.latency_ms if it.gen_result else None,
                "sim_latency_ms": it.sim_result.latency_ms if it.sim_result else None,
                "failures": [
                    {"category": f.category.value, "summary": f.summary, "fixable": f.fixable_by_corrector}
                    for f in it.failures
                ] if it.failures else [],
            }
            for it in self.history
        ]
        return json.dumps(d, indent=2)


class Agent:
    def __init__(self, llm: LLM, prompt_version="v1"):
        self.generator = Generator(llm, prompt_version)
        self.corrector = Corrector(llm, prompt_version)
        self.simulator = Simulator()

    def run(self, design_dir: str, verilog_files: list, toplevel: str,
            spec: str, test_module: str = "test_generated") -> AgentResult:
        """
        Full agent pipeline: generate → simulate → correct/reboot → repeat.

        Args:
            design_dir: Directory containing Verilog source files
            verilog_files: List of Verilog filenames
            toplevel: Top-level module name
            spec: Natural language specification
            test_module: Name for the generated test module

        Returns:
            AgentResult with pass/fail, testbench code, and full history
        """
        design_dir = Path(design_dir)
        start = time.monotonic()

        # Read Verilog source for the prompt
        verilog_source = ""
        for vf in verilog_files:
            verilog_source += (design_dir / vf).read_text() + "\n"

        history = []
        ic = 0  # correction counter
        ir = 0  # reboot counter
        total_tokens_in = 0
        total_tokens_out = 0
        current_code = None

        # Initial generation
        gen_result = self.generator.generate(verilog_source, spec)
        current_code = gen_result.code
        total_tokens_in += gen_result.llm_response.tokens_in
        total_tokens_out += gen_result.llm_response.tokens_out

        while True:
            # Simulate
            sim_result = self.simulator.run(
                design_dir=str(design_dir),
                verilog_files=verilog_files,
                toplevel=toplevel,
                test_module=test_module,
                test_file_content=current_code,
            )

            # Analyze failures if any
            failures = []
            if not sim_result.passed:
                failures = analyze_failure(sim_result.raw_output, sim_result.errors)

            # Record iteration
            iter_type = "generate" if ic == 0 and len(history) == ir else "correct"
            iteration = Iteration(
                iteration_type=iter_type,
                ic=ic,
                ir=ir,
                gen_result=gen_result,
                sim_result=sim_result,
                failures=failures,
            )
            history.append(iteration)

            # Check if passed
            if sim_result.passed:
                total_ms = (time.monotonic() - start) * 1000
                return AgentResult(
                    passed=True,
                    testbench_code=current_code,
                    iterations=len(history),
                    corrections=sum(1 for h in history if h.iteration_type == "correct"),
                    reboots=ir,
                    history=history,
                    total_latency_ms=total_ms,
                    total_tokens_in=total_tokens_in,
                    total_tokens_out=total_tokens_out,
                    sim_result=sim_result,
                )

            # Failed — decide: correct or reboot
            errors = sim_result.errors or sim_result.fail_messages
            if not errors:
                errors = [f"Simulation failed with {sim_result.fail_count} test failures. "
                          "No specific error messages captured."]

            if ic < IC_MAX:
                # Correction attempt
                ic += 1
                try:
                    gen_result = self.corrector.correct(
                        verilog_source, spec, current_code, errors,
                    )
                    current_code = gen_result.code
                    total_tokens_in += gen_result.llm_response.tokens_in
                    total_tokens_out += gen_result.llm_response.tokens_out
                except Exception as e:
                    # LLM timeout or error during correction — force reboot
                    print(f"  [agent] Correction failed ({e.__class__.__name__}), forcing reboot")
                    ic = IC_MAX  # Skip remaining corrections
                    continue

            elif ir < IR_MAX:
                # Reboot — fresh generation
                ir += 1
                ic = 0
                try:
                    gen_result = self.generator.generate(verilog_source, spec)
                    current_code = gen_result.code
                    total_tokens_in += gen_result.llm_response.tokens_in
                    total_tokens_out += gen_result.llm_response.tokens_out
                except Exception as e:
                    print(f"  [agent] Generation failed ({e.__class__.__name__}), retrying")
                    continue

            else:
                # Max iterations reached — give up
                total_ms = (time.monotonic() - start) * 1000
                return AgentResult(
                    passed=False,
                    testbench_code=current_code,
                    iterations=len(history),
                    corrections=sum(1 for h in history if h.iteration_type == "correct"),
                    reboots=ir,
                    history=history,
                    total_latency_ms=total_ms,
                    total_tokens_in=total_tokens_in,
                    total_tokens_out=total_tokens_out,
                    sim_result=sim_result,
                )
