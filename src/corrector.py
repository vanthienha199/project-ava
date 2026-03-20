"""
Corrector module for Project Ava.
Takes a failed testbench + error messages, sends to LLM for correction.
Uses the same cocotb 2.0 auto-fixes as the generator.

Usage:
    cor = Corrector(llm)
    result = cor.correct(verilog_source, spec, failed_code, errors)
    # Returns: GenResult(code, llm_response, prompt_used)
"""

from dataclasses import dataclass
from pathlib import Path

from .llm import LLM, LLMResponse
from .generator import GenResult, Generator


PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


class Corrector:
    def __init__(self, llm: LLM, prompt_version="v1"):
        self.llm = llm
        self.prompt_version = prompt_version
        # Reuse generator's cleaning/fixing logic
        self._gen = Generator(llm, prompt_version)

    def correct(self, verilog_source: str, spec: str,
                failed_code: str, errors: list) -> GenResult:
        """Attempt to fix a failed testbench using error feedback."""
        prompt = self._build_prompt(verilog_source, spec, failed_code, errors)
        response = self.llm.generate(prompt)
        code = self._gen._clean_code(response.text)
        code = self._gen._apply_cocotb2_fixes(code)

        return GenResult(
            code=code,
            llm_response=response,
            prompt_used=prompt,
            prompt_version=self.prompt_version,
        )

    def _build_prompt(self, verilog_source: str, spec: str,
                      failed_code: str, errors: list) -> str:
        """Load correction prompt template and fill in all fields."""
        template_path = PROMPTS_DIR / f"{self.prompt_version}_correct.txt"
        template = template_path.read_text()
        # Truncate errors to avoid massive correction prompts
        error_text = "\n".join(errors) if errors else "No specific error messages captured."
        if len(error_text) > 2000:
            error_text = error_text[:2000] + "\n... (truncated)"
        return template.format(
            verilog_source=verilog_source,
            spec=spec,
            testbench_code=failed_code,
            error_messages=error_text,
        )
