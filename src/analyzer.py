"""
Failure analyzer for Project Ava.
Categorizes simulation errors into a taxonomy so we can understand
WHY the agent fails, not just that it failed.

Error categories:
  - SYNTAX: Python syntax error in generated code
  - COCOTB_API: cocotb 2.0 API misuse (units vs unit, fork vs start_soon, etc.)
  - SIGNAL_ACCESS: wrong signal name, missing attribute, Python keyword collision
  - TIMING: wrong number of wait cycles, race condition, clock setup issue
  - LOGIC: assertion failed because test logic is wrong (expected != actual)
  - COMPILE: Verilog compilation error (iverilog)
  - IMPORT: missing or wrong Python import
  - TIMEOUT: simulation hung or exceeded time limit
  - UNKNOWN: unclassified error
"""

import re
from dataclasses import dataclass
from enum import Enum


class ErrorCategory(str, Enum):
    SYNTAX = "syntax"
    COCOTB_API = "cocotb_api"
    SIGNAL_ACCESS = "signal_access"
    TIMING = "timing"
    LOGIC = "logic"
    COMPILE = "compile"
    IMPORT = "import"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


@dataclass
class FailureAnalysis:
    category: ErrorCategory
    summary: str
    details: str
    fixable_by_corrector: bool  # Can the LLM corrector likely fix this?


def analyze_failure(raw_output: str, errors: list) -> list:
    """Analyze simulation output and return categorized failures."""
    failures = []
    combined = raw_output + "\n" + "\n".join(errors)

    # Check each pattern in priority order
    if _check_compile_error(combined):
        failures.append(_check_compile_error(combined))
    if _check_syntax_error(combined):
        failures.append(_check_syntax_error(combined))
    if _check_import_error(combined):
        failures.append(_check_import_error(combined))
    if _check_signal_access(combined):
        failures.append(_check_signal_access(combined))
    if _check_cocotb_api(combined):
        failures.append(_check_cocotb_api(combined))
    if _check_timeout(combined):
        failures.append(_check_timeout(combined))
    if _check_logic_error(combined):
        failures.append(_check_logic_error(combined))

    # If nothing matched, mark as unknown
    if not failures and errors:
        failures.append(FailureAnalysis(
            category=ErrorCategory.UNKNOWN,
            summary="Unclassified failure",
            details="\n".join(errors)[:500],
            fixable_by_corrector=True,
        ))

    return failures


def _check_compile_error(text):
    patterns = [
        r"(error:.*syntax error)",
        r"(.*\.v:\d+:.*error)",
        r"(iverilog.*error)",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return FailureAnalysis(
                category=ErrorCategory.COMPILE,
                summary="Verilog compilation error",
                details=m.group(0)[:300],
                fixable_by_corrector=False,
            )
    return None


def _check_syntax_error(text):
    m = re.search(r"(SyntaxError:.*)", text)
    if m:
        return FailureAnalysis(
            category=ErrorCategory.SYNTAX,
            summary="Python syntax error in generated testbench",
            details=m.group(0),
            fixable_by_corrector=True,
        )
    return None


def _check_import_error(text):
    patterns = [
        r"(ImportError:.*)",
        r"(ModuleNotFoundError:.*)",
        r"(from cocotb\.result import.*TestFailure)",
        r"(from cocotb\.binary import.*BinaryValue)",
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return FailureAnalysis(
                category=ErrorCategory.IMPORT,
                summary="Import error (likely removed cocotb 2.0 class)",
                details=m.group(0),
                fixable_by_corrector=True,
            )
    return None


def _check_signal_access(text):
    patterns = [
        r"(AttributeError:.*contains no child object named\s+(\w+))",
        r"(AttributeError:.*has no attribute\s+['\"](\w+)['\"])",
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            signal = m.group(2) if m.lastindex >= 2 else "unknown"
            return FailureAnalysis(
                category=ErrorCategory.SIGNAL_ACCESS,
                summary=f"Wrong signal name: '{signal}'",
                details=m.group(0),
                fixable_by_corrector=True,
            )
    return None


def _check_cocotb_api(text):
    patterns = [
        (r"units\s*=", "Used units= instead of unit= (cocotb 2.0)"),
        (r"cocotb\.fork\s*\(", "Used cocotb.fork() instead of cocotb.start_soon()"),
        (r"\.value\.integer", "Used .value.integer instead of int(.value)"),
        (r"\.kill\s*\(\s*\)", "Used .kill() instead of .cancel()"),
        (r"TestFailure", "Used TestFailure (removed in cocotb 2.0)"),
        (r"BinaryValue", "Used BinaryValue (removed in cocotb 2.0)"),
        (r"\.value\.binstr", "Used .value.binstr instead of str(.value)"),
    ]
    for p, desc in patterns:
        if re.search(p, text):
            return FailureAnalysis(
                category=ErrorCategory.COCOTB_API,
                summary=desc,
                details=f"Pattern matched: {p}",
                fixable_by_corrector=True,
            )
    return None


def _check_timeout(text):
    if "TIMEOUT" in text or "timed out" in text.lower():
        return FailureAnalysis(
            category=ErrorCategory.TIMEOUT,
            summary="Simulation timed out",
            details="Possible infinite loop or missing clock",
            fixable_by_corrector=True,
        )
    return None


def _check_logic_error(text):
    patterns = [
        r"(AssertionError:.*)",
        r"(AssertionError\s*$)",
        r"(assert.*got\s+\d+)",
        r"(expected.*got\s+\d+)",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE | re.MULTILINE)
        if m:
            return FailureAnalysis(
                category=ErrorCategory.LOGIC,
                summary="Test assertion failed (wrong expected value or logic error)",
                details=m.group(0)[:300],
                fixable_by_corrector=True,
            )
    return None
