"""
Generator module for Project Ava.
Takes Verilog source + natural language spec, builds a prompt with cocotb 2.0 rules,
calls the LLM, and returns clean testbench Python code.

Usage:
    gen = Generator(llm)
    result = gen.generate(verilog_source, spec)
    # Returns: GenResult(code, llm_response, prompt_used)
"""

import re
from dataclasses import dataclass
from pathlib import Path

from .llm import LLM, LLMResponse


PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


@dataclass
class GenResult:
    code: str
    llm_response: LLMResponse
    prompt_used: str
    prompt_version: str


class Generator:
    def __init__(self, llm: LLM, prompt_version="v1"):
        self.llm = llm
        self.prompt_version = prompt_version

    def generate(self, verilog_source: str, spec: str) -> GenResult:
        """Generate a cocotb testbench from Verilog source and specification."""
        prompt = self._build_prompt(verilog_source, spec)
        response = self.llm.generate(prompt)
        code = self._clean_code(response.text)
        code = self._apply_cocotb2_fixes(code)

        return GenResult(
            code=code,
            llm_response=response,
            prompt_used=prompt,
            prompt_version=self.prompt_version,
        )

    def _build_prompt(self, verilog_source: str, spec: str) -> str:
        """Load prompt template and fill in design + spec."""
        template_path = PROMPTS_DIR / f"{self.prompt_version}_generate.txt"
        template = template_path.read_text()
        return template.format(
            verilog_source=verilog_source,
            spec=spec,
        )

    def _clean_code(self, text: str) -> str:
        """Strip markdown fences and leading/trailing whitespace."""
        text = text.strip()
        # Remove ```python ... ``` or ``` ... ```
        if text.startswith("```"):
            lines = text.split("\n")
            lines = lines[1:]  # Remove opening fence
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]  # Remove closing fence
            text = "\n".join(lines)
        return text.strip()

    def _apply_cocotb2_fixes(self, code: str) -> str:
        """Apply known cocotb 2.0 API fixes that LLMs consistently get wrong."""
        # Fix units="ns" → unit="ns" (most common LLM error)
        code = re.sub(r'units\s*=\s*"(ns|us|ms|s|ps|fs)"', r'unit="\1"', code)

        # Fix .value.integer → int(.value)
        code = re.sub(
            r'(\w+(?:\.\w+)*)\.value\.integer',
            r'int(\1.value)',
            code,
        )

        # Fix .value.signed_integer → .value.to_signed()
        code = re.sub(
            r'\.value\.signed_integer',
            r'.value.to_signed()',
            code,
        )

        # Fix cocotb.fork( → cocotb.start_soon(
        code = re.sub(r'cocotb\.fork\s*\(', 'cocotb.start_soon(', code)

        # Fix task.kill() → task.cancel()
        code = re.sub(r'\.kill\s*\(\s*\)', '.cancel()', code)

        # Fix raise TestFailure → assert False
        code = re.sub(
            r'raise\s+TestFailure\s*\(\s*(["\'].*?["\'])\s*\)',
            r'assert False, \1',
            code,
        )

        # Fix from cocotb.result import TestFailure → remove
        code = re.sub(
            r'from\s+cocotb\.result\s+import\s+.*TestFailure.*\n',
            '',
            code,
        )

        # Fix from cocotb.binary import BinaryValue → remove
        code = re.sub(
            r'from\s+cocotb\.binary\s+import\s+.*BinaryValue.*\n',
            '',
            code,
        )

        # Fix .value.binstr → str(.value)
        code = re.sub(
            r'(\w+(?:\.\w+)*)\.value\.binstr',
            r'str(\1.value)',
            code,
        )

        return code
